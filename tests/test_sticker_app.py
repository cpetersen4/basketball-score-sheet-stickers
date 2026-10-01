# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
import sys
from pathlib import Path
import tempfile
import unittest

from test_generate_pdf import PDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from generate_pdf import read_roster, manual_roster, generate_pdf
from sticker_app import StickerApp


class WizardTests(unittest.TestCase):
    def test_small_window_keeps_navigation_visible_and_last_row_reachable(self):
        app = StickerApp(read_roster, manual_roster, generate_pdf)
        try:
            self.assertLessEqual(app.window.minsize()[1], 650)
            app.window.geometry('1000x480')
            app.show(2)
            app.window.update()
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            button = next(widget for widget in descendants(app.window)
                          if widget.winfo_class() == 'Button' and widget.cget('text') == 'Continue to save  >')
            self.assertTrue(button.winfo_ismapped())
            self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                                 app.window.winfo_rooty() + app.window.winfo_height())
            final_entry = next(widget for widget in descendants(app.window)
                               if widget.winfo_class() == 'TEntry'
                               and widget.cget('textvariable') == str(app.players[14][1]))
            self.assertEqual(app.body_scrollbar.winfo_manager(), 'pack')
            app.body_canvas.yview_moveto(1)
            app.window.update()
            self.assertGreaterEqual(final_entry.winfo_rooty(), app.body_canvas.winfo_rooty())
            self.assertLessEqual(final_entry.winfo_rooty() + final_entry.winfo_height(),
                                 app.body_canvas.winfo_rooty() + app.body_canvas.winfo_height())
            app.body_canvas.yview_moveto(0)
            final_entry.focus_force()
            app.window.update()
            self.assertLessEqual(final_entry.winfo_rooty() + final_entry.winfo_height(),
                                 app.body_canvas.winfo_rooty() + app.body_canvas.winfo_height())
            app.players[14][1].set('Last Player')
            app.navigate(1)
            app.navigate(2)
            self.assertEqual(app.players[14][1].get(), 'Last Player')
        finally:
            app.window.destroy()

    def test_manual_workflow_and_back_navigation_preserve_roster(self):
        app = StickerApp(read_roster, manual_roster, generate_pdf)
        app.window.update_idletasks()
        app.window.withdraw()
        try:
            self.assertEqual(app.step, 1)
            self.assertIsNone(app.source)
            self.assertEqual(len(app.players), 15)
            app.show(2)
            app.team.set('Manual Team')
            app.players[0][0].set('00')
            app.players[0][1].set('Manual Player')
            app.players[14][0].set('99')
            app.players[14][1].set('Last Player')
            app.head.set('Manual Coach')
            app.assistant_editor.insert('1.0', 'Assistant One\nAssistant Two')
            app.navigate(1)
            app.navigate(2)
            self.assertEqual(app.players[14][1].get(), 'Last Player')
            self.assertEqual(app.team.get(), 'Manual Team')
            app.window.deiconify()
            app.window.update()
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            button = next(widget for widget in descendants(app.window)
                          if widget.winfo_class() == 'Button' and widget.cget('text') == 'Continue to save  >')
            self.assertTrue(button.winfo_ismapped())
            self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                                 app.window.winfo_rooty() + app.window.winfo_height())
            app.window.withdraw()
            self.assertEqual([label.cget('text') for label in app.summary_labels],
                             ['2 players', '1 head coach', '2 assistants'])
            app.navigate(3)
            self.assertEqual(app.step, 3)
            with tempfile.TemporaryDirectory() as folder:
                output = Path(folder) / 'manual.pdf'
                app.output.set(str(output))
                app.create_pdf()
                self.assertEqual(app.saved_path, output.resolve())
                top_load = next(widget for widget in descendants(app.window)
                                if widget.winfo_class() == 'Button' and widget.cget('text') == '1  Load roster')
                top_load.invoke()
                self.assertEqual(app.step, 1)
                top_save = next(widget for widget in descendants(app.window)
                                if widget.winfo_class() == 'Button' and widget.cget('text') == '3  Save PDF')
                top_save.invoke()
                self.assertEqual(app.step, 3)
                self.assertEqual(app.output.get(), str(output))
                self.assertEqual(app.open_button.winfo_manager(), 'pack')
                with PDF(output) as doc:
                    text = '\n'.join(page.get_text() for page in doc).replace('\u00a0', ' ')
                    self.assertEqual(text.count('Manual Player'), 12)
                    self.assertEqual(text.count('Last Player'), 12)
                    self.assertEqual(text.count('Assistant Two'), 12)
            app.show(2)
            app.window.update()
            self.assertEqual(app.players[0][1].get(), 'Manual Player')
            self.assertEqual(app.assistants.get(), 'Assistant One\nAssistant Two')
        finally:
            app.window.destroy()


if __name__ == '__main__':
    unittest.main()
