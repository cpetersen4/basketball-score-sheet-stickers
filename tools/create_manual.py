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
    text(94, 723, 'Windows 10/11 x64 | Version 1.0.0', 10)
    text(40, 682, title, 22, True)
    text(40, 660, subtitle, 11)
    c.setStrokeColor(HexColor('#E2E8F0'))
    c.line(40, 44, 572, 44)
    text(40, 28, 'Offline roster stickers | Print at actual size', 9)
    text(548, 28, f'{number} / 4', 9)

def screenshot(name):
    reader = ImageReader(str(ROOT / 'docs/screenshots' / name))
    w, h = reader.getSize()
    height = 532 * h / w
    c.drawImage(reader, 40, 637-height, 532, height)
    return 637-height-25

page(1, '1. Start with your roster', 'Extract the ZIP, then double-click Basketball-Score-Sheet-Stickers.exe.')
y = screenshot('load-roster.jpg')
for line in ['Choose CSV / TXT to load your roster, or skip CSV to enter names manually.',
             'No Python, Illustrator, administrator access, or internet connection is required.',
             'The EXE contains the template and libraries; it uses Windows Arial.',
             'Keep the included sample CSV as a fictional example.']:
    text(40, y, line, 10); y -= 20
c.showPage()
page(2, '2. Review your team', 'Enter the team name and check every player, number, and coach.')
y = screenshot('review-team.jpg')
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
for line in ['Browse for a new filename, then choose Create printable PDF.',
             'With a CSV import, Browse starts in the CSV folder. Existing files are protected.',
             'Open saved PDF launches your default PDF viewer. Print at 100% / actual size.',
             'Test on plain paper against the score sheet before printing adhesive sheets.',
             'Smaller rosters leave unused slots blank. Long names shrink to fit.']:
    text(40, y, line, 10); y -= 20
c.showPage()
page(4, 'CSV format and troubleshooting', 'Store each team roster and its generated PDFs together.')
y=620
for heading, lines in [
    ('A simple UTF-8 CSV or TXT', ['number,name,role', '7,Example Player,Player', 'na,Example Head Coach,Head Coach', 'na,Example Assistant,Assistant Coach']),
    ('Roster rules', ['Use the header above. Supported roles: Player, Head Coach, Assistant Coach.', 'Use 1-15 players and at most one head coach. Player order is preserved.', 'Quote names containing commas. Save as UTF-8 for accented names.']),
    ('If the app rejects a roster', ['Check missing names, duplicate numbers, extra CSV columns, and role spelling.', 'Shorten names that cannot fit legibly. Remove unsupported characters.', 'Existing output? Choose a new PDF filename rather than overwriting it.']),
    ('Printing and opening PDFs', ['Use actual size, not Fit to page. Confirm alignment with a plain-paper test.', 'If Open saved PDF fails, open the PDF directly in your preferred viewer.']),
    ('Compatibility and local files', ['Designed for Windows 10/11, 64-bit. Tested on Windows 11.', 'The app runs locally and makes no network requests. A PDF viewer is needed', 'to view or print the result. The executable is not digitally signed.', 'Changes remain in memory until you close the app; PDFs are saved to disk.', 'Free personal use. Redistributing or reselling the app requires written permission.'])]:
    text(40,y,heading,14,True); y-=26
    for line in lines:
        text(40,y,line,10); y-=18
    y-=20
c.save()
print(OUTPUT)
