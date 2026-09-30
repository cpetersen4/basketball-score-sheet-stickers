# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
"""Fill the obfuscated basketball score sheet sticker PDF from a number,name,role CSV.

No arguments opens the Windows GUI; positional arguments provide the CLI.
"""
import argparse
import csv
import os
from pathlib import Path
import re
import sys

from io import BytesIO
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
DEFAULT_TEMPLATE = ROOT / 'templates' / 'score-sheet-stickers-2026.pdf'
CAPACITY = 15


def read_roster(path):
    players, assistants, head_coaches = [], [], []
    numbers = set()
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or set(reader.fieldnames) != {'number', 'name', 'role'}:
            raise ValueError('CSV header must contain number,name,role (in any order).')
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f'CSV row {reader.line_num} has missing or extra columns.')
            number, name, role = (row[key].strip() for key in ('number', 'name', 'role'))
            if not name or any(ord(c) < 32 for c in name):
                raise ValueError(f'CSV row {reader.line_num} needs a name without line breaks.')
            if role.lower() == 'player':
                if not re.fullmatch(r'[0-9]{1,3}', number):
                    raise ValueError(f'CSV row {reader.line_num}: player number must be 0-999.')
                if number in numbers:
                    raise ValueError(f'Duplicate jersey number: {number}.')
                numbers.add(number)
                players.append((number, name))
            elif role.lower() == 'head coach':
                head_coaches.append(name)
            elif role.lower() == 'assistant coach':
                assistants.append(name)
            else:
                raise ValueError(f'CSV row {reader.line_num}: unsupported role {role!r}.')
    if not 1 <= len(players) <= CAPACITY:
        raise ValueError(f'The template supports 1-{CAPACITY} players; found {len(players)}.')
    if len(head_coaches) > 1:
        raise ValueError('Only one Head Coach row is supported.')
    return {'players': players, 'head_coach': next(iter(head_coaches), ''), 'assistants': assistants}


def _template_pages(path):
    """Read character positions without changing the template artwork."""
    pages = []
    for layout in extract_pages(str(path)):
        chars = []
        def visit(item):
            if isinstance(item, LTChar):
                chars.append({'text': item.get_text(), 'x0': item.x0, 'x1': item.x1,
                              'top': layout.height - item.y1,
                              'bottom': layout.height - item.y0,
                              'size': item.size, 'matrix': item.matrix,
                              'color': item.graphicstate.ncolor})
            elif hasattr(item, '__iter__'):
                for child in item:
                    visit(child)
        visit(layout)
        for index, char in enumerate(chars):
            char['id'] = index
        pages.append({'width': layout.width, 'height': layout.height, 'chars': chars})
    return pages


def _spans(page):
    # Group text by baseline, then split columns at visible gaps. Match fields
    # inside a run so labels remain separate from the values being replaced.
    rows = []
    for char in sorted(page['chars'], key=lambda c: (-c['matrix'][5], c['x0'])):
        if not rows or abs(rows[-1][0]['matrix'][5] - char['matrix'][5]) > 0.2:
            rows.append([])
        rows[-1].append(char)
    spans = []
    pattern = r'Asst Coach 01, Asst Coach 02|Head Coach 01|Sample Team|Player \d{2}|(?<!\w)\d{1,3}(?!\w)'
    for row in rows:
        runs = []
        for char in sorted(row, key=lambda c: c['x0']):
            if not runs or char['x0'] - runs[-1][-1]['x1'] > 3:
                runs.append([])
            runs[-1].append(char)
        for run in runs:
            text = ''.join(c['text'] for c in run)
            # LTChar represents one glyph; reject ambiguous multi-character
            # glyphs instead of silently replacing the wrong field.
            if any(len(c['text']) != 1 for c in run):
                raise ValueError('Template contains unsupported combined glyphs.')
            for match in re.finditer(pattern, text):
                chars = run[match.start():match.end()]
                spans.append({'text': match.group(), 'size': chars[0]['size'],
                              'origin': (chars[0]['matrix'][4], page['height'] - chars[0]['matrix'][5]),
                              'bbox': (chars[0]['x0'], min(c['top'] for c in chars),
                                       chars[-1]['x1'], max(c['bottom'] for c in chars)),
                              'ids': {c['id'] for c in chars}})
    return spans


def _plan(page, roster, team):
    spans = _spans(page)
    plans = []
    slots = [s for s in spans if re.fullmatch(r'Player \d{2}', s['text'].strip())]
    if len(slots) != 6 * CAPACITY:
        raise ValueError(f'Template must have six stickers per page, each with Player 01-{CAPACITY}.')
    for slot in slots:
        index = int(slot['text'].strip()[-2:]) - 1
        if not 0 <= index < CAPACITY:
            raise ValueError('Invalid player slot in PDF template.')
        x, y = slot['origin']
        candidates = [s for s in spans if re.fullmatch(r'[0-9]{1,3}', s['text'].strip())
                      and abs(s['origin'][1] - y) < 0.2 and x + 150 < s['origin'][0] < x + 215]
        if len(candidates) != 1:
            raise ValueError('Cannot locate the jersey number for a player slot.')
        number_span = candidates[0]
        number, name = roster['players'][index] if index < len(roster['players']) else ('', '')
        plans.append((slot, name, 150, False))
        plans.append((number_span, number, 32, True))
    anchors = [s for s in slots if s['text'].strip() == 'Player 01']
    for pattern, value in [(r'Sample Team', team), (r'Head Coach 01', roster['head_coach']),
                           (r'Asst Coach 01, Asst Coach 02', ', '.join(roster['assistants']))]:
        matches = [s for s in spans if re.fullmatch(pattern, s['text'].strip())]
        if len(matches) != 6:
            raise ValueError(f'Template is missing repeated placeholder {pattern!r}.')
        for span in matches:
            x, y = span['origin']
            # Associate a field with its sticker to keep text inside the right border.
            nearby = [a for a in anchors if a['origin'][0] - 5 <= x <= a['origin'][0] + 210
                      and a['origin'][1] - 40 <= y <= a['origin'][1] + 210]
            if len(nearby) != 1:
                raise ValueError('Cannot determine the sticker boundary for a PDF field.')
            plans.append((span, value, nearby[0]['origin'][0] + 207 - x, False))
    return plans


def manual_roster(rows, head_coach, assistants):
    players = [(str(number).strip(), name.strip()) for number, name in rows
               if str(number).strip() or name.strip()]
    if not 1 <= len(players) <= CAPACITY:
        raise ValueError(f'Enter 1-{CAPACITY} players.')
    numbers = set()
    for number, name in players:
        if not name or any(ord(c) < 32 for c in name):
            raise ValueError('Each player needs a name without line breaks.')
        if not re.fullmatch(r'[0-9]{1,3}', number):
            raise ValueError('Each player needs a jersey number from 0 to 999.')
        if number in numbers:
            raise ValueError(f'Duplicate jersey number: {number}.')
        numbers.add(number)
    coaches = [head_coach.strip()] + [name.strip() for name in assistants if name.strip()]
    if any(any(ord(c) < 32 for c in name) for name in coaches):
        raise ValueError('Coach names cannot contain line breaks.')
    return {'players': players, 'head_coach': coaches[0], 'assistants': coaches[1:]}


def generate_pdf(csv_path, output_path, team_name, template_path=DEFAULT_TEMPLATE, *, roster=None):
    output, template = Path(output_path), Path(template_path)
    if output.resolve() == template.resolve() or (csv_path and output.resolve() == Path(csv_path).resolve()):
        raise ValueError('Output must be a separate file from the template and roster.')
    if output.exists():
        raise FileExistsError('Output already exists. Choose a new filename.')
    if output.suffix.lower() != '.pdf':
        raise ValueError('Output filename must end in .pdf.')
    team = team_name.strip()
    if not team or any(ord(c) < 32 for c in team):
        raise ValueError('Enter a team name without line breaks.')
    if roster is None:
        roster = read_roster(csv_path)
    else:
        roster = manual_roster(roster['players'], roster['head_coach'], roster['assistants'])
    font_path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/arial.ttf'
    if not font_path.is_file():
        raise ValueError('Windows Arial font was not found.')
    font = TTFont('RosterArial', str(font_path))
    pdfmetrics.registerFont(font)
    reader = PdfReader(template)
    pages = _template_pages(template)
    if len(reader.pages) != 2 or len(pages) != 2:
        raise ValueError('Use the two-page obfuscated home/away sticker template.')
    page_plans = [_plan(page, roster, team) for page in pages]
    # Validate all values before creating an output file.
    for plans in page_plans:
        for span, value, width, centered in plans:
            if any(ord(c) not in font.face.charToGlyph for c in value):
                raise ValueError('A roster or team name contains a character Arial cannot print.')
            if value and pdfmetrics.stringWidth(value, 'RosterArial', 5.5) > width:
                raise ValueError(f'Text is too long to print legibly: {value!r}. Shorten it.')
    writer = PdfWriter()
    for source, page, plans in zip(reader.pages, pages, page_plans):
        # Strip every text-showing operation before cloning the page. This
        # physically removes placeholders; graphics and table paths stay intact.
        stream = ContentStream(source.get_contents(), reader)
        stream.operations = [(args, op) for args, op in stream.operations
                             if op not in (b'Tj', b'TJ', b"'", b'"')]
        source[NameObject('/Contents')] = stream
        source.pop('/Metadata', None)
        overlay = BytesIO()
        drawing = canvas.Canvas(overlay, pagesize=(page['width'], page['height']))
        removed = set().union(*(span['ids'] for span, *_ in plans))
        # Recreate untouched labels at their original glyph positions, preserving
        # kerning, colour, baseline, and font size rather than reflowing labels.
        for char in page['chars']:
            if char['id'] in removed:
                continue
            color = char['color']
            if isinstance(color, (tuple, list)) and len(color) == 4:
                drawing.setFillColorCMYK(*color)
            elif isinstance(color, (tuple, list)) and len(color) == 3:
                drawing.setFillColorRGB(*color)
            else:
                drawing.setFillGray(color[0] if isinstance(color, (tuple, list)) else color or 0)
            drawing.setFont('RosterArial', char['size'])
            drawing.drawString(char['matrix'][4], char['matrix'][5], char['text'])
        drawing.setFillColorRGB(0, 0, 0)
        for span, value, width, centered in plans:
            if not value:
                continue
            size = min(span['size'], width / pdfmetrics.stringWidth(value, 'RosterArial', 1))
            x, y = span['origin']
            if centered:
                x = (span['bbox'][0] + span['bbox'][2] - pdfmetrics.stringWidth(value, 'RosterArial', size)) / 2
            drawing.setFont('RosterArial', size)
            drawing.drawString(x, page['height'] - y, value)
        drawing.save()
        target = writer.add_page(source)
        target.merge_page(PdfReader(overlay).pages[0])
        target.compress_content_streams()
    writer.add_metadata({'/Title': team + ' - Basketball Score Sheet Stickers',
                         '/Creator': 'Basketball Score Sheet Stickers'})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as destination:
        writer.write(destination)
    return output


def gui():
    from sticker_app import StickerApp
    StickerApp(read_roster, manual_roster, generate_pdf).run()


def main():
    if len(sys.argv) == 1:
        gui()
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path, help='Roster CSV or TXT with number,name,role columns')
    parser.add_argument('output', type=Path, help='New printable PDF filename')
    parser.add_argument('--team', required=True, help='Team name for home and away stickers')
    parser.add_argument('--template', type=Path, default=DEFAULT_TEMPLATE)
    args = parser.parse_args()
    try:
        generate_pdf(args.csv, args.output, args.team, args.template)
    except Exception as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Created {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
