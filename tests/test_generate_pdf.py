# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

from pypdf import PdfReader
from pypdf.generic import ContentStream
from reportlab.pdfgen import canvas

class Page:
    def __init__(self, page, reader):
        self.page, self.reader = page, reader
        self.rect = tuple(page.mediabox)
    def get_text(self, mode=None):
        text = self.page.extract_text()
        return [(0, 0, 0, 0, word) for word in text.split()] if mode == 'words' else text
    def get_drawings(self):
        return [op for _, op in ContentStream(self.page.get_contents(), self.reader).operations
                if op in (b'S', b's', b'f', b'F', b'f*', b'B', b'B*', b'b', b'b*')]

class PDF:
    def __init__(self, path):
        self.reader = PdfReader(path)
        self.pages = [Page(page, self.reader) for page in self.reader.pages]
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def __iter__(self): return iter(self.pages)
    def __len__(self): return len(self.pages)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('generate_pdf', ROOT / 'app/generate_pdf.py')
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def roster(self, rows):
        path = self.root / 'roster.txt'
        with path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['number', 'name', 'role'])
            writer.writerows(rows)
        return path

    def test_csv_quotes_accents_and_coach_roles(self):
        roster = generator.read_roster(self.roster([
            ['00', 'Ren\u00e9e, Sample', 'Player'],
            ['na', 'Example Coach', 'Head Coach'],
            ['na', 'Example Assistant', 'Assistant Coach'],
        ]))
        self.assertEqual(roster['players'], [('00', 'Ren\u00e9e, Sample')])
        self.assertEqual(roster['head_coach'], 'Example Coach')
        self.assertEqual(roster['assistants'], ['Example Assistant'])

    def test_manual_entry_clears_blank_rows_and_validates_partial_rows(self):
        result = generator.manual_roster([('00', 'Sample'), ('', '')], 'Coach', ['Assistant', ''])
        self.assertEqual(result, {'players': [('00', 'Sample')], 'head_coach': 'Coach', 'assistants': ['Assistant']})
        for rows in [[('', 'Name')], [('1', '')], [('1', 'One'), ('1', 'Two')]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                generator.manual_roster(rows, '', [])

    def test_manual_roster_generates_pdf_without_csv(self):
        roster = generator.manual_roster([('55', 'Manual Example')], 'Manual Coach', [])
        output = self.root / 'manual.pdf'
        generator.generate_pdf(None, output, 'Manual Team', roster=roster)
        with PDF(output) as doc:
            text = '\n'.join(page.get_text() for page in doc).replace('\u00a0', ' ')
            self.assertEqual(text.count('Manual Example'), 12)
            self.assertEqual(text.count('Manual Coach'), 12)
            self.assertNotIn('Asst Coach 01', text)

    def test_invalid_rosters_are_rejected(self):
        cases = [
            [['1', '', 'Player']],
            [['1', 'One', 'Player'], ['1', 'Two', 'Player']],
            [['x', 'One', 'Player']],
            [['1', 'One', 'Unknown']],
            [[str(i), 'Sample ' + str(i), 'Player'] for i in range(16)],
            [['na', 'One', 'Head Coach'], ['na', 'Two', 'Head Coach']],
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                generator.read_roster(self.roster(rows))

    def test_pdf_replaces_all_stickers_clears_unused_rows_preserves_geometry(self):
        roster = self.roster([
            ['00', 'Ren\u00e9e Example', 'Player'],
            ['99', 'Second Sample', 'Player'],
            ['na', 'Example Head', 'Head Coach'],
            ['na', 'Example Assistant', 'Assistant Coach'],
        ])
        output = self.root / 'filled.pdf'
        template = ROOT / 'templates' / 'score-sheet-stickers-2026.pdf'
        generator.generate_pdf(roster, output, 'Example Team', template)
        with PDF(template) as before, PDF(output) as after:
            self.assertEqual(len(after), 2)
            text = '\n'.join(page.get_text() for page in after).replace('\u00a0', ' ')
            for expected in ['Ren\u00e9e Example', 'Second Sample', 'Example Head',
                             'Example Assistant', 'Example Team']:
                self.assertEqual(text.count(expected), 12, expected)
            for absent in ['Player 01', 'Player 12', 'Player 15', 'Head Coach 01', 'Asst Coach 01', 'Sample Team']:
                self.assertNotIn(absent, text)
            for page in after:
                payload = page.page.get_contents().get_data()
                self.assertNotIn(b'Player 01', payload)
                self.assertNotIn(b'Head Coach 01', payload)
            for old, new in zip(before, after):
                self.assertEqual(old.rect, new.rect)
                self.assertEqual(len(old.get_drawings()), len(new.get_drawings()))
                words = [word[4] for word in new.get_text('words')]
                self.assertEqual(words.count('00'), 6)
                self.assertEqual(words.count('99'), 6)
                self.assertNotIn('44', words)

    def test_fifteen_players_fill_last_three_rows_on_every_sticker(self):
        rows = [[str(i), 'Example ' + chr(64 + i), 'Player'] for i in range(1, 16)]
        roster = self.roster(rows)
        self.assertEqual(len(generator.read_roster(roster)['players']), 15)
        output = self.root / 'fifteen.pdf'
        generator.generate_pdf(roster, output, 'Full Team')
        with PDF(output) as doc:
            self.assertEqual(len(doc), 2)
            for page in doc:
                text = page.get_text().replace('\u00a0', ' ')
                for i in range(1, 16):
                    self.assertEqual(text.count('Example ' + chr(64 + i)), 6)
                    self.assertEqual([w[4] for w in page.get_text('words')].count(str(i)), 6)
                self.assertNotIn('Player 15', text)

    def test_refuses_overwriting_template_or_existing_output(self):
        roster = self.roster([['1', 'Sample', 'Player']])
        output = self.root / 'existing.pdf'
        output.write_bytes(b'unchanged')
        with self.assertRaises(FileExistsError):
            generator.generate_pdf(roster, output, 'Sample')
        self.assertEqual(output.read_bytes(), b'unchanged')
        with self.assertRaises(ValueError):
            generator.generate_pdf(roster, ROOT / 'templates' / 'score-sheet-stickers-2026.pdf', 'Sample')

    def test_wrong_template_and_unprintably_long_names_fail_without_output(self):
        bad = self.root / 'blank.pdf'
        blank = canvas.Canvas(str(bad))
        blank.showPage()
        blank.save()
        roster = self.roster([['1', 'W' * 200, 'Player']])
        output = self.root / 'output.pdf'
        with self.assertRaises(ValueError):
            generator.generate_pdf(roster, output, 'Sample', bad)
        with self.assertRaises(ValueError):
            generator.generate_pdf(roster, output, 'Sample')
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
