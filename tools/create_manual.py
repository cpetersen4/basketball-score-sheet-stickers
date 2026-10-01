# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
"""Rebuild the illustrated manual: pip install reportlab, then run this script."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/Basketball-Score-Sheet-Stickers-Manual.pdf'
TEAL = HexColor('#00858C')
INK = HexColor('#12253A')
c = canvas.Canvas(str(OUTPUT), pagesize=(612, 792))
c.setTitle('Basketball Score Sheet Stickers - Windows Manual')
c.setAuthor('Basketball Score Sheet Stickers')

def text(x, y, value, size=11, bold=False):
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    c.drawString(x, y, value)

def page(number, title, subtitle):
    c.setFillColor(TEAL)
    c.rect(0, 776, 612, 16, fill=1, stroke=0)
    c.drawImage(str(ROOT / 'assets/basketball.png'), 40, 718, 40, 40, mask='auto')
    text(94, 740, 'BASKETBALL SCORE SHEET STICKERS', 12, True)
    text(94, 723, 'Windows 10/11 x64', 10)
    text(40, 682, title, 22, True)
    text(40, 660, subtitle, 11)
    c.setStrokeColor(HexColor('#E2E8F0'))
    c.line(40, 44, 572, 44)
    text(40, 28, 'Basketball Score Sheet Stickers', 9)
    text(548, 28, f'{number} / 4', 9)

def screenshot(name):
    reader = ImageReader(str(ROOT / 'docs/screenshots' / name))
    w, h = reader.getSize()
    height = 532 * h / w
    c.drawImage(reader, 40, 637-height, 532, height)
    return 637-height-25

page(1, '1. Load roster', 'Extract the ZIP, then double-click Basketball-Score-Sheet-Stickers.exe.')
y = screenshot('load-roster.png')
for line in ['Choose CSV / TXT to load your roster, or skip CSV to enter names manually.',
             'No Python, Illustrator, administrator access, or internet connection is required.',
             'The EXE contains the template and libraries; it uses Windows Arial.',
             'Keep the included sample CSV as a fictional example.']:
    text(40, y, line, 10); y -= 20
c.showPage()
page(2, '2. Review team', 'Enter the team name and check every player, number, and coach.')
y = screenshot('review-team.png')
for line in ['Use up to 15 player rows. Leave unused rows completely blank.',
             'On smaller screens, scroll the form; tabbing brings fields into view.',
             'Jersey numbers must be unique and contain 1-3 digits (0-999).',
             'Head coach is optional. Enter assistant coaches one per line.',
             'Click the top steps or Back to navigate. Edits stay in this open session.',
             'Close the app only after saving: edits are not saved as a roster file.']:
    text(40, y, line, 10); y -= 20
c.showPage()
page(3, '3. Save and print', 'Create a separate PDF with six home and six away roster stickers.')
y = screenshot('../sample-output.png')
for line in ['Open the generated PDF and select the home or away page.',
             'Use full-sheet 8.5 x 11-inch adhesive label paper suitable for your printer.',
             'Staples full-sheet shipping labels or similar full-sheet labels are suitable.',
             'Example label paper: https://a.co/d/0fz6G47o',
             'Select Letter paper and Actual size / 100%. Do not use Fit or Shrink.',
             'The PDF pages are landscape. Check a plain-paper test before using labels.',
             'Cut out the stickers with a straight paper cutter or scissors.',
             'Peel off the backing and attach each sticker to the team roster area.']:
    if line.startswith('Example label paper:'):
        c.linkURL('https://a.co/d/0fz6G47o', (40, y-2, 350, y+12), relative=0)
    text(40, y, line, 10); y -= 20
c.showPage()
page(4, 'CSV format and troubleshooting', 'Store each team roster and its generated PDFs together.')
y=620
for heading, lines in [
    ('UTF-8 CSV or TXT', ['number,name,role', '7,Example Player,Player', 'na,Example Head Coach,Head Coach', 'na,Example Assistant,Assistant Coach']),
    ('Roster rules', ['Use the header above. Supported roles: Player, Head Coach, Assistant Coach.', 'Use 1-15 players and at most one head coach. Player order is preserved.', 'Quote names containing commas. Save as UTF-8 for accented names.']),
    ('If the app rejects a roster', ['Check missing names, duplicate numbers, extra CSV columns, and role spelling.', 'Shorten names that cannot fit legibly. Remove unsupported characters.', 'Choose a new filename if the output PDF already exists.']),
    ('Printing and opening PDFs', ['Use actual size, not Fit to page. Confirm alignment with a plain-paper test.', 'If Open saved PDF fails, open the PDF directly in your preferred viewer.']),
    ('Compatibility and local files', ['Designed for Windows 10/11, 64-bit. Tested on Windows 11.', 'The app runs locally and makes no network requests. A PDF viewer is needed', 'to view or print the result. The executable is not digitally signed.', 'Changes remain in memory until you close the app; PDFs are saved to disk.', 'Free personal use. Redistributing or reselling the app requires written permission.'])]:
    text(40,y,heading,14,True); y-=26
    for line in lines:
        text(40,y,line,10); y-=18
    y-=20
c.save()
print(OUTPUT)
