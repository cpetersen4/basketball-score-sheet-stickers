import unittest, tempfile, zipfile, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from unittest.mock import patch
from PIL import Image
from test_generate_pdf import generator, PDF

class CricutTests(unittest.TestCase):
    def test_export_contains_two_solid_rectangles_and_printed_roster(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'cricut.zip'
            roster=generator.manual_roster([(str(i),f'New Player {i:02}') for i in range(1,16)],'New Coach',['New Assistant'])
            generator.generate_cricut(None,output,'New Team',roster=roster)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(set(z.namelist()),{'home-sticker.png','away-sticker.png','Cricut-Instructions.pdf','dimensions.json'})
                sizes=json.loads(z.read('dimensions.json'))
                import io
                for name in ('home-sticker.png','away-sticker.png'):
                    image=Image.open(io.BytesIO(z.read(name))).convert('RGBA')
                    self.assertEqual(image.getpixel((0,0))[3],255)
                    alpha=image.getchannel('A'); box=alpha.getbbox()
                    self.assertEqual(alpha.crop(box).getextrema(),(255,255))
                    self.assertEqual(box,(0,0,image.width,image.height))
                    self.assertAlmostEqual(sizes[name]['width_inches'],sizes[name]['cut_width_inches'])
                    self.assertGreaterEqual(image.width,1800)
                    self.assertEqual(sizes[name]['dpi'],600)
                    self.assertAlmostEqual(sizes[name]['width_inches'],image.width/600,places=5)
                doc=PDF(io.BytesIO(z.read('Cricut-Instructions.pdf')))
                self.assertIn('Print Then Cut',doc.pages[0].get_text())
                self.assertIn('Do not remove',doc.pages[0].get_text())
            original=output.read_bytes()
            with self.assertRaises(FileExistsError):generator.generate_cricut(None,output,'New Team',roster=roster)
            self.assertEqual(output.read_bytes(),original)

    def test_bad_roster_leaves_no_export(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'bad.zip'
            with self.assertRaises(ValueError):generator.generate_cricut(None,output,'',roster={'players':[], 'head_coach':'','assistants':[]})
            self.assertFalse(output.exists())

    def test_failed_zip_write_cleans_partial_file(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'failed.zip'
            original_open = Path.open
            class BrokenFile:
                def __enter__(self):
                    self.stream = original_open(output, 'xb')
                    return self
                def write(self, data):
                    self.stream.write(data[:20])
                    raise OSError('Simulated full disk')
                def __exit__(self, *args):
                    self.stream.close()
            def open_file(path, *args, **kwargs):
                return BrokenFile() if path == output else original_open(path, *args, **kwargs)
            with patch.object(Path, 'open', open_file), self.assertRaises(OSError):
                generator.generate_cricut(None, output, 'Team',
                                          roster=generator.manual_roster([('1','Player')],'',[]))
            self.assertFalse(output.exists())
