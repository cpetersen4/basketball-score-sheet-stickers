# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, DecodedStreamObject, DictionaryObject, NameObject
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

    def test_duplicate_csv_headers_are_rejected(self):
        path = self.root / 'duplicate-header.csv'
        path.write_text('number,name,role,name\n1,Original,Player,Overwritten\n')
        with self.assertRaises(ValueError):
            generator.read_roster(path)

    def test_invisible_names_and_team_names_are_rejected_without_output(self):
        for name, team in [('\u200b', 'Team'), ('Player', '\u200d')]:
            with self.subTest(name=name, team=team):
                output = self.root / 'invisible.pdf'
                roster = generator.manual_roster([('1', name)], '', [])
                with self.assertRaisesRegex(ValueError, 'visible'):
                    generator.generate_pdf(None, output, team, roster=roster)
                self.assertFalse(output.exists())

    def test_repeated_template_player_slot_is_rejected(self):
        page = generator._template_pages(generator.DEFAULT_TEMPLATE)[0]
        spans = generator._spans(page)
        next(span for span in spans if span['text'] == 'Player 15')['text'] = 'Player 14'
        roster = generator.manual_roster([('1', 'Example')], '', [])
        with patch.object(generator, '_spans', return_value=spans):
            with self.assertRaisesRegex(ValueError, 'once'):
                generator._plan(page, roster, 'Team')

    def test_serialization_failure_does_not_leave_an_output_file(self):
        output = self.root / 'failed.pdf'
        roster = generator.manual_roster([('1', 'Example')], '', [])
        with patch.object(generator.PdfWriter, 'write', side_effect=RuntimeError('Failed writer')):
            with self.assertRaises(RuntimeError):
                generator.generate_pdf(None, output, 'Team', roster=roster)
        self.assertFalse(output.exists())

    def test_file_created_during_generation_is_not_removed_or_overwritten(self):
        output = self.root / 'racing.pdf'
        roster = generator.manual_roster([('1', 'Example')], '', [])
        original_write = generator.PdfWriter.write
        def racing_write(writer, buffer):
            original_write(writer, buffer)
            output.write_bytes(b'Created by another process')
        with patch.object(generator.PdfWriter, 'write', racing_write):
            with self.assertRaises(FileExistsError):
                generator.generate_pdf(None, output, 'Team', roster=roster)
        self.assertEqual(output.read_bytes(), b'Created by another process')

    def test_failed_disk_write_removes_partial_file(self):
        output = self.root / 'partial.pdf'
        roster = generator.manual_roster([('1', 'Example')], '', [])
        original_open = Path.open
        class PartialWriter:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): self.stream.close()
            def write(self, data):
                self.stream.write(data[:10])
                raise OSError('Simulated full disk')
        def open_file(path, mode='r', *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            return PartialWriter(stream) if path == output and mode == 'xb' else stream
        with patch.object(Path, 'open', open_file):
            with self.assertRaises(OSError):
                generator.generate_pdf(None, output, 'Team', roster=roster)
        self.assertFalse(output.exists())

    def test_template_text_inside_form_objects_is_removed(self):
        writer = PdfWriter()
        for source in PdfReader(generator.DEFAULT_TEMPLATE).pages:
            page = writer.add_page(source)
            form = DecodedStreamObject()
            form.set_data(page.get_contents().get_data())
            form.update({NameObject('/Type'): NameObject('/XObject'),
                         NameObject('/Subtype'): NameObject('/Form'),
                         NameObject('/BBox'): page.mediabox,
                         NameObject('/Resources'): page['/Resources']})
            stream = DecodedStreamObject()
            stream.set_data(b'q /Sticker Do Q')
            page[NameObject('/Contents')] = writer._add_object(stream)
            page[NameObject('/Resources')] = DictionaryObject({
                NameObject('/XObject'): DictionaryObject({NameObject('/Sticker'): writer._add_object(form)})})
        template = self.root / 'form-template.pdf'
        writer.write(template)
        output = self.root / 'form-filled.pdf'
        roster = generator.manual_roster([('77', 'Fresh Player')], '', [])
        generator.generate_pdf(None, output, 'Fresh Team', template, roster=roster)
        text = '\n'.join(page.extract_text() for page in PdfReader(output).pages)
        self.assertEqual(text.count('Fresh Player'), 12)
        self.assertNotIn('Player 01', text)
        self.assertNotIn('Sample Team', text)

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
