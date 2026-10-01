# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
"""Smoke-test the extracted release with no external Python on PATH."""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import zipfile
from pypdf import PdfReader
from PIL import Image
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='score-sheet-portable-') as folder:
    portable = Path(folder)
    with zipfile.ZipFile(ROOT / 'dist/Basketball-Score-Sheet-Stickers-Windows-x64.zip') as archive:
        assert {name for name in archive.namelist() if not name.startswith('licenses/')} == {
            'Basketball-Score-Sheet-Stickers.exe', 'team-names_sample.csv',
            'Basketball-Score-Sheet-Stickers-Manual.pdf', 'LICENSE', 'THIRD-PARTY-NOTICES.md'}
        archive.extractall(portable)
    environment = dict(os.environ)
    environment['PATH'] = str(Path(environment['WINDIR']) / 'System32')
    for key in ('PYTHONHOME', 'PYTHONPATH', 'VIRTUAL_ENV'):
        environment.pop(key, None)
    output = portable / 'verified-stickers.pdf'
    subprocess.run([str(portable / 'Basketball-Score-Sheet-Stickers.exe'),
                    str(portable / 'team-names_sample.csv'), str(output),
                    '--team', 'Portable Sample'], cwd=portable, env=environment,
                   check=True, timeout=30)
    document = PdfReader(output)
    assert len(document.pages) == 2
    text = '\n'.join(page.extract_text() for page in document.pages).replace('\u00a0', ' ')
    assert text.count('Player 15') == 12
    assert text.count('Portable Sample') == 12
    cricut = portable / 'verified-cricut.zip'
    subprocess.run([str(portable / 'Basketball-Score-Sheet-Stickers.exe'),
                    str(portable / 'team-names_sample.csv'), str(cricut),
                    '--team', 'Portable Cricut', '--cricut'], cwd=portable, env=environment,
                   check=True, timeout=30)
    with zipfile.ZipFile(cricut) as archive:
        dimensions = json.loads(archive.read('dimensions.json'))
        for name in ('home-sticker.png', 'away-sticker.png'):
            image = Image.open(BytesIO(archive.read(name)))
            assert image.width >= 1800
            assert dimensions[name]['dpi'] == 600
            alpha = image.getchannel('A')
            assert image.getpixel((0, 0))[3] == 255
            assert alpha.getbbox() == (0, 0, image.width, image.height)
            assert alpha.crop(alpha.getbbox()).getextrema() == (255, 255)
        assert len(PdfReader(BytesIO(archive.read('Cricut-Instructions.pdf'))).pages) == 1
print('Portable package verified: PDF and Cricut export, all 15 players, no external Python.')
