# Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
"""Guided, editable roster workflow for the standalone Windows app."""
import os
from pathlib import Path
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

BG = '#F5F7FA'
INK = '#12253A'
MUTED = '#64748B'
TEAL = '#00858C'
PALE = '#E4F4F4'
LINE = '#E2E8F0'


class StickerApp:
    def __init__(self, read_roster, manual_roster, generate_pdf, generate_cricut=None):
        self.read_roster = read_roster
        self.manual_roster = manual_roster
        self.generate_pdf = generate_pdf
        self.generate_cricut = generate_cricut
        self.cricut_saved_path = None
        self.window = tk.Tk()
        self.window.title('Basketball Score Sheet Stickers')
        asset_root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
        self.window.iconbitmap(str(asset_root / 'assets' / 'basketball.ico'))
        width = min(1060, max(840, self.window.winfo_screenwidth() - 80))
        height = min(880, max(420, self.window.winfo_screenheight() - 100))
        self.window.geometry(f'{width}x{height}')
        self.window.minsize(840, 420)
        self.window.configure(bg=BG)
        self.window.option_add('*Font', ('Segoe UI', 10))
        style = ttk.Style(self.window)
        style.theme_use('clam')
        style.configure('Roster.TEntry', padding=3, fieldbackground='white', foreground=INK,
                        bordercolor=LINE, lightcolor=LINE, darkcolor=LINE)
        style.map('Roster.TEntry', bordercolor=[('focus', TEAL)])
        self.team = tk.StringVar()
        self.head = tk.StringVar()
        self.assistants = tk.StringVar()
        self.players = [(tk.StringVar(), tk.StringVar()) for _ in range(15)]
        self.output = tk.StringVar()
        self.source = None
        self.saved_path = None
        self.step = 1
        self.assistant_editor = None
        for variable in [self.head, self.assistants] + [v for row in self.players for v in row]:
            variable.trace_add('write', self.update_summary)
        self.summary_labels = None
        self.window.bind('<MouseWheel>', self.scroll_body)
        self.window.bind('<FocusIn>', self.reveal_field)
        self.show(1)

    def label(self, parent, text, size=10, color=INK, bold=False, **kwargs):
        label = tk.Label(parent, text=text, bg=parent['bg'], fg=color,
                         font=('Segoe UI', size, 'bold' if bold else 'normal'), **kwargs)
        if 'wraplength' in kwargs:
            maximum = kwargs['wraplength']
            def fit_text(event):
                padding = 2 * parent.winfo_pixels(parent.cget('padx'))
                label.configure(wraplength=max(120, min(maximum, event.width - padding - 2)))
            parent.bind('<Configure>', fit_text, add='+')
        return label

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, relief='flat', bd=0,
                         bg=TEAL if primary else '#EDF1F5', fg='white' if primary else INK,
                         activebackground='#006A70' if primary else LINE,
                         activeforeground='white' if primary else INK, cursor='hand2',
                         font=('Segoe UI', 10, 'bold'), padx=18, pady=10)

    def card(self, parent, **kwargs):
        return tk.Frame(parent, bg='white', highlightbackground=LINE, highlightthickness=1, **kwargs)

    def entry(self, parent, variable, width=None):
        return ttk.Entry(parent, textvariable=variable, style='Roster.TEntry', width=width)

    def show(self, step):
        if self.assistant_editor is not None and self.assistant_editor.winfo_exists():
            self.assistants.set(self.assistant_editor.get('1.0', 'end-1c'))
        self.assistant_editor = None
        self.step = step
        self.summary_labels = None
        for child in self.window.winfo_children():
            child.destroy()
        sidebar = tk.Frame(self.window, bg='#EDF2F7', width=190)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        self.label(sidebar, 'BASKETBALL', size=17, color=TEAL, bold=True).pack(anchor='w', padx=22, pady=(30, 0))
        self.label(sidebar, 'SCORE SHEET STICKERS', size=9, color=MUTED, bold=True).pack(anchor='w', padx=22)
        tk.Frame(sidebar, bg=sidebar['bg'], height=30).pack(fill='x')
        titles = ['Load roster', 'Review team', 'Save PDF']
        for index, title in enumerate(titles, 1):
            frame = tk.Frame(sidebar, bg=PALE if index == step else sidebar['bg'])
            frame.pack(fill='x', padx=12, pady=5)
            self.label(frame, f'{index}   {title}', color=TEAL if index == step else MUTED,
                       bold=index == step).pack(anchor='w', padx=14, pady=13)
        self.label(sidebar, 'No internet connection required.', size=9, color=MUTED, wraplength=150,
                   justify='left').pack(side='bottom', anchor='w', padx=20, pady=25)
        main = tk.Frame(self.window, bg=BG)
        main.pack(side='left', fill='both', expand=True, padx=28, pady=22)
        progress = tk.Frame(main, bg=BG)
        progress.pack(fill='x', pady=(0, 20))
        for index, title in enumerate(titles, 1):
            color = TEAL if index == step else MUTED
            tk.Button(progress, text=f'{index}  {title}', command=lambda destination=index: self.navigate(destination),
                      bg=PALE if index == step else BG, fg=color, activebackground=PALE,
                      activeforeground=TEAL, relief='flat', bd=0, cursor='hand2',
                      font=('Segoe UI', 10, 'bold' if index == step else 'normal'),
                      padx=14, pady=7).pack(side='left', expand=True)
        headings = ['Load roster', 'Review team', 'Save PDF']
        descriptions = ['Import a CSV, or start with a blank roster and enter your team manually.',
                        'Edit player names, jersey numbers and coaches before printing.',
                        'Create a print-ready PDF with six home and six away roster stickers.']
        self.label(main, headings[step-1], size=23, bold=True).pack(anchor='w')
        self.label(main, descriptions[step-1], color=MUTED, wraplength=730,
                   justify='left').pack(anchor='w', pady=(6, 20))
        # Reserve navigation space before the scrolling content takes the rest.
        footer = tk.Frame(main, bg=BG)
        footer.pack(side='bottom', fill='x', pady=(18, 0))
        viewport = tk.Frame(main, bg=BG)
        viewport.pack(fill='both', expand=True)
        self.body_canvas = tk.Canvas(viewport, bg=BG, highlightthickness=0, width=1, height=1)
        self.body_canvas.pack(side='left', fill='both', expand=True)
        self.body_scrollbar = ttk.Scrollbar(viewport, orient='vertical', command=self.body_canvas.yview)
        self.body_canvas.configure(yscrollcommand=self.body_scrollbar.set)
        self.body_frame = body = tk.Frame(self.body_canvas, bg=BG)
        self.body_window = self.body_canvas.create_window((0, 0), window=body, anchor='nw')
        self.body_canvas.bind('<Configure>', self.resize_body)
        body.bind('<Configure>', self.resize_body)
        if step > 1:
            self.button(footer, 'Back', lambda: self.show(step-1)).pack(side='left')
        if step == 1:
            self.load_screen(body)
        elif step == 2:
            self.review_screen(body)
            self.button(footer, 'Continue to save  >', self.continue_to_save, True).pack(side='right')
        else:
            self.save_screen(body)

    def resize_body(self, event=None):
        canvas = self.body_canvas
        height = max(canvas.winfo_height(), self.body_frame.winfo_reqheight())
        canvas.itemconfigure(self.body_window, width=canvas.winfo_width(), height=height)
        canvas.configure(scrollregion=(0, 0, canvas.winfo_width(), height))
        if height > canvas.winfo_height() + 1:
            if not self.body_scrollbar.winfo_manager():
                self.body_scrollbar.pack(side='right', fill='y')
        else:
            self.body_scrollbar.pack_forget()

    def is_body_widget(self, widget):
        while widget is not None:
            if widget == self.body_canvas:
                return True
            widget = widget.master
        return False

    def scroll_body(self, event):
        if self.is_body_widget(event.widget) and self.body_scrollbar.winfo_manager():
            self.body_canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
            return 'break'

    def reveal_field(self, event):
        if not self.is_body_widget(event.widget):
            return
        canvas = self.body_canvas
        top = event.widget.winfo_rooty() - self.body_frame.winfo_rooty()
        bottom = top + event.widget.winfo_height()
        visible_top = canvas.canvasy(0)
        height = self.body_frame.winfo_height()
        if top < visible_top:
            canvas.yview_moveto(top / max(height, 1))
        elif bottom > visible_top + canvas.winfo_height():
            canvas.yview_moveto((bottom - canvas.winfo_height()) / max(height, 1))

    def load_screen(self, body):
        for title, caption, button, action, primary in [
            ('Import CSV', 'Use a CSV or TXT with number, name and role columns.\nReview and edit the imported roster on the next screen.',
             'Choose CSV / TXT', self.import_csv, True),
            ('Enter manually', 'Enter player names, jersey numbers and coaches without a CSV.',
             'Skip CSV / Enter manually', lambda: self.show(2), False)]:
            card = self.card(body, padx=25, pady=25)
            card.pack(fill='x', pady=(0, 18))
            self.label(card, title, size=15, bold=True).pack(anchor='w')
            self.label(card, caption, color=MUTED, justify='left', wraplength=680).pack(anchor='w', pady=(8, 18))
            self.button(card, button, action, primary).pack(anchor='w')
        self.label(body, 'Up to 15 players. Coaches are optional. No internet connection needed.',
                   color=MUTED, size=9).pack(anchor='w', pady=4)

    def import_csv(self):
        path = filedialog.askopenfilename(parent=self.window, title='Choose roster',
                                         filetypes=[('Roster CSV / TXT', '*.csv *.txt')])
        if not path:
            return
        try:
            roster = self.read_roster(path)
        except Exception as error:
            messagebox.showerror('Could not load roster', str(error), parent=self.window)
            return
        self.source = path
        for index, (number, name) in enumerate(self.players):
            values = roster['players'][index] if index < len(roster['players']) else ('', '')
            number.set(values[0]); name.set(values[1])
        self.head.set(roster['head_coach'])
        self.assistants.set('\n'.join(roster['assistants']))
        self.show(2)

    def review_screen(self, body):
        top = tk.Frame(body, bg=BG)
        top.pack(fill='x', pady=(0, 16))
        self.label(top, 'Team name', bold=True).pack(side='left', padx=(0, 12))
        self.entry(top, self.team).pack(side='left', fill='x', expand=True)
        self.label(top, 'CSV imported' if self.source else 'Manual entry', color=TEAL,
                   size=9).pack(side='right', padx=(12, 0))
        columns = tk.Frame(body, bg=BG)
        columns.pack(fill='both', expand=True)
        left = self.card(columns, padx=16, pady=14)
        left.pack(side='left', fill='both', expand=True, padx=(0, 16))
        self.label(left, 'Players', size=13, bold=True).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))
        for col, text in enumerate(['', 'Jersey #', 'Player name']):
            self.label(left, text, color=MUTED, size=9, bold=True).grid(row=1, column=col, sticky='w', pady=(0, 5))
        left.columnconfigure(2, weight=1)
        for index, (number, name) in enumerate(self.players, 1):
            self.label(left, str(index).zfill(2), size=9, color=MUTED).grid(row=index+1, column=0, padx=(0, 8))
            self.entry(left, number, width=6).grid(row=index+1, column=1, padx=(0, 10), pady=1)
            self.entry(left, name).grid(row=index+1, column=2, sticky='ew', pady=1)
        self.label(left, 'Leave unused rows completely blank.', size=9, color=MUTED).grid(
            row=17, column=0, columnspan=3, sticky='w', pady=(10, 0))
        right = tk.Frame(columns, bg=BG, width=245)
        right.pack(side='right', fill='y')
        coaches = self.card(right, padx=16, pady=16)
        coaches.pack(fill='x')
        self.label(coaches, 'Coaches', size=13, bold=True).pack(anchor='w', pady=(0, 12))
        self.label(coaches, 'Head coach', size=9, color=MUTED).pack(anchor='w')
        self.entry(coaches, self.head, width=24).pack(fill='x', pady=(5, 14))
        self.label(coaches, 'Assistants (one per line)', size=9, color=MUTED).pack(anchor='w')
        editor = tk.Text(coaches, height=4, width=24, font=('Segoe UI', 10), relief='flat',
                         highlightthickness=1, highlightbackground=LINE, highlightcolor=TEAL,
                         padx=7, pady=6, undo=True, wrap='word')
        editor.pack(fill='x', pady=(5, 0))
        self.assistant_editor = editor
        editor.insert('1.0', self.assistants.get())
        editor.edit_modified(False)
        def sync_assistants(event):
            if editor.edit_modified():
                self.assistants.set(editor.get('1.0', 'end-1c'))
                editor.edit_modified(False)
        editor.bind('<<Modified>>', sync_assistants)
        summary = tk.Frame(right, bg=PALE, padx=18, pady=18)
        summary.pack(fill='x', pady=16)
        self.label(summary, 'Team summary', color=TEAL, bold=True).pack(anchor='w', pady=(0, 12))
        self.summary_labels = [self.label(summary, '', size=11) for _ in range(3)]
        for label in self.summary_labels:
            label.pack(anchor='w', pady=5)
        self.label(summary, '12 roster stickers\n6 home + 6 away', color=TEAL,
                   justify='left', size=9).pack(anchor='w', pady=(12, 0))
        self.update_summary()

    def update_summary(self, *args):
        if not self.summary_labels:
            return
        players = sum(bool(name.get().strip() or number.get().strip()) for number, name in self.players)
        assistants = sum(bool(line.strip()) for line in self.assistants.get().splitlines())
        for label, text in zip(self.summary_labels, [f'{players} player' + ('' if players == 1 else 's'),
                              f'{int(bool(self.head.get().strip()))} head coach',
                              f'{assistants} assistant' + ('' if assistants == 1 else 's')]):
            label.configure(text=text)

    def collect_roster(self):
        if not self.team.get().strip():
            raise ValueError('Enter your team name.')
        return self.manual_roster([(number.get(), name.get()) for number, name in self.players],
                                  self.head.get(), self.assistants.get().splitlines())

    def continue_to_save(self):
        self.navigate(3)

    def navigate(self, step):
        if step == self.step:
            return
        if self.assistant_editor is not None and self.assistant_editor.winfo_exists():
            self.assistants.set(self.assistant_editor.get('1.0', 'end-1c'))
        if step != 3:
            self.show(step)
            return
        try:
            self.collect_roster()
        except ValueError as error:
            messagebox.showerror('Check your roster', str(error), parent=self.window)
            return
        self.show(3)

    def save_screen(self, body):
        card = self.card(body, padx=24, pady=24)
        card.pack(fill='x')
        self.label(card, self.team.get(), size=17, bold=True).pack(anchor='w')
        roster = self.collect_roster()
        count = len(roster['players'])
        self.label(card, f"{count} player" + ('' if count == 1 else 's') + '  |  Home + away  |  2 pages', color=MUTED).pack(
            anchor='w', pady=(6, 24))
        self.label(card, 'Save PDF to', bold=True).pack(anchor='w')
        path_row = tk.Frame(card, bg='white')
        path_row.pack(fill='x', pady=(8, 20))
        self.entry(path_row, self.output).pack(side='left', fill='x', expand=True, padx=(0, 12))
        self.button(path_row, 'Browse...', self.choose_output).pack(side='right')
        self.button(card, 'Create printable PDF', self.create_pdf, True).pack(anchor='w')
        self.status = self.label(card, '', color=TEAL, wraplength=650, justify='left')
        self.status.pack(anchor='w', pady=(14, 0))
        self.open_button = self.button(card, 'Open saved PDF', self.open_pdf)
        if self.saved_path and self.saved_path.exists():
            self.status.configure(text=f'Previously saved PDF:\n{self.saved_path}')
            self.open_button.pack(anchor='w', pady=(12, 0))
        hint = tk.Frame(body, bg=PALE, padx=20, pady=18)
        hint.pack(fill='x', pady=20)
        self.label(hint, 'Print at actual size', color=TEAL, size=12, bold=True).pack(anchor='w')
        self.label(hint, 'Choose 100% / actual size in your PDF viewer. Test on plain paper first.',
                   color=INK, wraplength=650, justify='left').pack(anchor='w', pady=(6, 0))
        if self.generate_cricut is not None:
            cricut = self.card(body, padx=20, pady=18)
            cricut.pack(fill='x')
            self.label(cricut, 'Cricut Print Then Cut', size=12, bold=True).pack(anchor='w')
            self.label(cricut, 'Export individual home and away sticker images for Design Space.\n'
                       'The ZIP includes a PDF with sizing, printing, and cutting instructions.',
                       color=MUTED, wraplength=650, justify='left').pack(anchor='w', pady=(6, 12))
            self.button(cricut, 'Export Cricut ZIP...', self.export_cricut).pack(anchor='w')
            self.cricut_status = self.label(cricut, '', color=TEAL, wraplength=650, justify='left')
            self.cricut_status.pack(anchor='w', pady=(10, 0))
            if self.cricut_saved_path:
                self.cricut_status.configure(text=f'Cricut ZIP saved:\n{self.cricut_saved_path}')

    def export_cricut(self):
        try:
            roster = self.collect_roster()
            name = re.sub(r'[^\w-]+', '-', self.team.get().strip()).strip('-') or 'team'
            path = filedialog.asksaveasfilename(parent=self.window, title='Export Cricut stickers',
                                               initialfile=name + '-cricut.zip', defaultextension='.zip',
                                               initialdir=str(Path(self.source).resolve().parent) if self.source else None,
                                               filetypes=[('ZIP', '*.zip')], confirmoverwrite=False)
            if not path:
                return
            result = self.generate_cricut(self.source, path, self.team.get(), roster=roster)
            self.cricut_saved_path = Path(result).resolve()
            self.cricut_status.configure(text=f'Cricut ZIP saved:\n{self.cricut_saved_path}')
        except Exception as error:
            messagebox.showerror('Could not export Cricut stickers', str(error), parent=self.window)

    def choose_output(self):
        name = re.sub(r'[^\w-]+', '-', self.team.get().strip()).strip('-') or 'team'
        path = filedialog.asksaveasfilename(parent=self.window, title='Save sticker sheets',
                                           initialfile=name + '-stickers.pdf',
                                           initialdir=str(Path(self.source).resolve().parent) if self.source else None,
                                           defaultextension='.pdf',
                                           filetypes=[('PDF', '*.pdf')], confirmoverwrite=False)
        if path:
            self.output.set(path)

    def create_pdf(self):
        try:
            if not self.output.get().strip():
                self.choose_output()
                if not self.output.get().strip():
                    return
            result = self.generate_pdf(self.source, self.output.get(), self.team.get(), roster=self.collect_roster())
        except Exception as error:
            messagebox.showerror('Could not create PDF', str(error), parent=self.window)
            return
        self.saved_path = Path(result).resolve()
        self.status.configure(text=f'PDF saved:\n{self.saved_path}')
        self.open_button.pack(anchor='w', pady=(12, 0))

    def open_pdf(self):
        try:
            os.startfile(self.saved_path)
        except OSError as error:
            messagebox.showerror('Could not open PDF', str(error), parent=self.window)

    def run(self):
        self.window.mainloop()
