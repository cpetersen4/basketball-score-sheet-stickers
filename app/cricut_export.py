# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
"""Export individual, opaque rectangular stickers for Cricut Print Then Cut."""
from io import BytesIO
import json
import math
from pathlib import Path
import tempfile
import zipfile

from PIL import Image
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTCurve
import pypdfium2 as pdfium
from reportlab.pdfgen import canvas

DPI = 600


def sticker_bounds(template):
    """Locate the first sticker's complete artwork, including the coach rows."""
    from generate_pdf import _template_pages, _spans
    text_pages = _template_pages(template)
    bounds = []
    for index, page in enumerate(extract_pages(str(template))):
        curves = []
        def visit(item):
            if isinstance(item, LTCurve):
                curves.append(item)
            elif hasattr(item, '__iter__'):
                for child in item:
                    visit(child)
        visit(page)
        # Top-left player field is below the team and column heading rows.
        players = sorted((s for s in _spans(text_pages[index]) if s['text'] == 'Player 01'),
                         key=lambda s: (s['origin'][1], s['origin'][0]))
        if not players:
            raise ValueError('Cannot locate the Cricut sticker artwork.')
        x, origin_y = players[0]['origin']
        y = page.height - origin_y
        lines = [c for c in curves if c.width > 200 and c.width < 225
                 and x - 10 <= c.x0 <= x + 1
                 and y - 200 <= c.y0 <= y + 40]
        if len(lines) < 18:
            raise ValueError('Cannot determine the full Cricut sticker boundary.')
        left = min(c.x0 for c in lines)
        right = max(c.x1 for c in lines)
        bottom = min(c.y0 for c in lines)
        top = max(c.y1 for c in lines)
        artwork = [c for c in curves if left-2 <= c.x0 and c.x1 <= right+2
                   and bottom-2 <= c.y0 and c.y1 <= top+2]
        left = min(c.x0 for c in artwork)
        right = max(c.x1 for c in artwork)
        bottom = min(c.y0 for c in artwork)
        top = max(c.y1 for c in artwork)
        bounds.append((left, bottom, right, top))
    if len(bounds) != 2:
        raise ValueError('Cricut export requires the two-page home/away template.')
    return bounds


def instructions(dimensions):
    buffer = BytesIO()
    drawing = canvas.Canvas(buffer, pagesize=(612, 792))
    drawing.setTitle('Cricut Print Then Cut instructions')
    drawing.setFont('Helvetica-Bold', 18)
    drawing.drawString(40, 744, 'Cricut Print Then Cut')
    drawing.setFont('Helvetica', 11)
    lines = [
        '1. Extract this ZIP. Upload home-sticker.png or away-sticker.png to Design Space.',
        '2. Choose the flat, full-color image option and save as Print Then Cut.',
        'Do not remove the white background inside the sticker or isolate its text.',
        '3. Lock the size proportions and set the image width shown below:',
    ]
    for name, size in dimensions.items():
        lines.append(f"   {name}: width {size['width_inches']:.6f} in; height {size['height_inches']:.6f} in.")
    lines += [
        'The images are cropped to the sticker edges; these are the finished sticker sizes.',
        '4. Duplicate the sticker for the number of copies you need.',
        '5. Choose Make and print through Design Space so it adds its sensor marks.',
        'Use Letter label paper. Do not fit, shrink, or scale the printed page.',
        'Let Design Space arrange the copies within its Print Then Cut area.',
        '6. Load the printed sheet on your mat and follow the cut instructions.',
        'Check the cut preview: it should show one outside rectangle, not letters or lines.',
        'Use a Print Then Cut-compatible machine and calibrate it before testing.',
        'For a kiss cut, select a material setting that cuts the label, not the backing.',
        'Test one sticker first to check size, alignment, and cutting pressure.',
        'The ordinary PDF is for manual cutting; do not use it for this workflow.',
    ]
    for index, line in enumerate(lines):
        drawing.drawString(40, 704-index*25, line)
    drawing.save()
    return buffer.getvalue()


def export_cricut(generate_pdf, csv_path, output_path, team_name, template_path, *, roster=None):
    output = Path(output_path)
    if output.suffix.lower() != '.zip':
        raise ValueError('Cricut output filename must end in .zip.')
    if output.exists():
        raise FileExistsError('Output already exists. Choose a new filename.')
    if csv_path and output.resolve() == Path(csv_path).resolve():
        raise ValueError('Output must be separate from the roster.')
    with tempfile.TemporaryDirectory(prefix='score-sheet-cricut-') as folder:
        filled = Path(folder) / 'filled.pdf'
        generate_pdf(csv_path, filled, team_name, template_path, roster=roster)
        bounds = sticker_bounds(template_path)
        payload = BytesIO()
        dimensions = {}
        with pdfium.PdfDocument(str(filled)) as document, zipfile.ZipFile(payload, 'w', zipfile.ZIP_DEFLATED) as archive:
            for index, (left, bottom, right, top) in enumerate(bounds):
                name = ('home-sticker.png', 'away-sticker.png')[index]
                page = document[index]
                try:
                    bitmap = page.render(scale=DPI/72)
                    try:
                        rendered = bitmap.to_pil().convert('RGB')
                        crop = rendered.crop((math.floor(left*DPI/72), math.floor((page.get_height()-top)*DPI/72),
                                              math.ceil(right*DPI/72), math.ceil((page.get_height()-bottom)*DPI/72)))
                    finally:
                        bitmap.close()
                finally:
                    page.close()
                image = crop.convert('RGBA')
                stream = BytesIO()
                image.save(stream, format='PNG', dpi=(DPI, DPI))
                archive.writestr(name, stream.getvalue())
                dimensions[name] = {'width_inches': image.width/DPI, 'height_inches': image.height/DPI,
                                    'dpi': DPI, 'cut_width_inches': crop.width/DPI, 'cut_height_inches': crop.height/DPI}
            archive.writestr('dimensions.json', json.dumps(dimensions, indent=2))
            archive.writestr('Cricut-Instructions.pdf', instructions(dimensions))
        output.parent.mkdir(parents=True, exist_ok=True)
        destination = output.open('xb')
        try:
            with destination:
                data = payload.getvalue()
                if destination.write(data) != len(data):
                    raise OSError('The Cricut ZIP could not be written completely.')
        except BaseException:
            output.unlink()
            raise
    return output
