import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from engine import Downloader, normalize_url

ROOT = Path(__file__).resolve().parent
BG, CARD, INK, MUTED, ACCENT = '#F3F5F9', '#ffffff', '#111111', '#777777', '#427FDA'
SECONDARY, BORDER = '#E7EDF4', '#D9D9D9'
TEXT_FONT = ('맑은 고딕', 10)
DOWNLOAD_FONT = ('맑은 고딕', 11, 'bold')


class FlatProgress(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, height=15, bg=BG, bd=0, highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=BORDER)
        self.value = 0
        self.fill = self.create_rectangle(0, 0, 0, 0, fill=ACCENT, outline='', width=0)
        self.bind('<Configure>', lambda event: self.set(self.value))

    def set(self, value):
        self.value = max(0, min(100, float(value)))
        self.coords(self.fill, 0, 0, max(0, self.winfo_width() - 2) * self.value / 100,
                    self.winfo_height())

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('YouTube to MP3')
        self.geometry('690x590')
        self.minsize(690, 590)
        self.configure(bg=BG)
        self.app_icon = tk.PhotoImage(file=str(ROOT / 'icon.png'))
        self.iconphoto(True, self.app_icon)
        self.option_add('*Font', TEXT_FONT)
        self.events = queue.Queue()
        self.worker = None
        self.busy = False
        self.closing = False
        self.url = tk.StringVar()
        self.mode = tk.StringVar(value='single')
        self.folder = tk.StringVar(value=str(Path.home() / 'Downloads'))
        self.status = tk.StringVar(value='주소를 붙여넣고 다운로드를 시작하세요.')
        self.count = tk.StringVar(value='저장 확인 0곡')
        outer = tk.Frame(self, bg=BG, padx=30, pady=28)
        outer.pack(fill='both', expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(6, weight=1)
        self.label(outer, '유튜브주소', INK).grid(row=0, column=0, sticky='w', pady=(0, 10))
        row = tk.Frame(outer, bg=ACCENT, padx=2, pady=2, height=50)
        row.grid(row=1, column=0, sticky='ew')
        row.pack_propagate(False)
        input_area = tk.Frame(row, bg=CARD, padx=12)
        self.entry = tk.Entry(input_area, textvariable=self.url, bg=CARD, fg=INK, relief='flat', bd=0,
                              highlightthickness=0, insertbackground=INK, font=TEXT_FONT)
        self.paste_button = self.button(row, '붙여넣기', self.paste, True)
        self.paste_button.pack(side='right', fill='y', ipadx=12)
        input_area.pack(side='left', fill='both', expand=True)
        self.entry.pack(fill='both', expand=True)
        modes = tk.Frame(outer, bg=BG)
        modes.grid(row=2, column=0, sticky='w', pady=(22, 24), padx=10)
        self.radio_off = self.radio_image(False)
        self.radio_on = self.radio_image(True)
        self.radios = []
        for text, value in [('한곡만 다운로드', 'single'), ('재생목록 전체 다운로드', 'playlist')]:
            radio = tk.Radiobutton(modes, text='  ' + text, variable=self.mode, value=value, bg=BG,
                                  activebackground=BG, activeforeground=INK, selectcolor=BG, fg=INK,
                                  image=self.radio_off, selectimage=self.radio_on, compound='left',
                                  indicatoron=False, relief='flat', offrelief='flat', overrelief='flat',
                                  bd=0, highlightthickness=0, padx=0, pady=0,
                                  font=TEXT_FONT, cursor='hand2')
            radio.pack(side='left', padx=(0, 24))
            self.radios.append(radio)
        actions = tk.Frame(outer, bg=BG)
        actions.grid(row=3, column=0, sticky='ew')
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, minsize=76)
        actions.columnconfigure(2, minsize=126)
        actions.rowconfigure(0, minsize=48)
        self.start_button = self.button(actions, 'MP3 다운로드', self.start, True, emphasis=True)
        self.start_button.grid(row=0, column=0, sticky='nsew')
        self.stop_button = self.button(actions, '중지', self.stop)
        self.stop_button.grid(row=0, column=1, sticky='nsew', padx=(6, 6))
        self.stop_button.configure(state='disabled')
        self.button(actions, '저장 폴더 열기', self.open_folder).grid(row=0, column=2, sticky='nsew')
        status_row = tk.Frame(outer, bg=BG)
        status_row.grid(row=4, column=0, sticky='ew', pady=(18, 8))
        status_row.columnconfigure(1, weight=1)
        self.status_label = self.label(status_row, '', MUTED, textvariable=self.status, anchor='w',
                                       justify='left', wraplength=490)
        self.status_label.grid(row=0, column=0, sticky='w')
        self.label(status_row, '', MUTED, textvariable=self.count).grid(row=0, column=1, sticky='w', padx=(12, 0))
        self.progress = FlatProgress(outer)
        self.progress.grid(row=5, column=0, sticky='ew')
        self.log = tk.Text(outer, height=1, bg=SECONDARY, fg=INK, relief='flat', bd=0,
                           highlightthickness=0, padx=12, pady=10,
                           font=TEXT_FONT, state='disabled', wrap='word')
        self.log.grid(row=6, column=0, sticky='nsew', pady=(16, 22))
        details = tk.Frame(outer, bg=BG)
        details.grid(row=7, column=0, sticky='ew')
        details.columnconfigure(1, weight=1)
        self.label(details, 'MP3 · 320 kbps', ACCENT).grid(row=0, column=0, sticky='w', padx=(0, 18))
        self.label(details, '원본 이상의 음질로 복원되지는 않습니다.',
                   MUTED).grid(row=0, column=1, sticky='w')
        self.label(details, '저장폴더', ACCENT).grid(row=1, column=0, sticky='w', pady=(4, 0))
        self.label(details, '', MUTED, textvariable=self.folder, anchor='w', wraplength=500).grid(
            row=1, column=1, sticky='ew', pady=(4, 0))
        footer = tk.Frame(outer, bg=BG)
        footer.grid(row=8, column=0, sticky='ew', pady=(22, 0))
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, minsize=146)
        footer.columnconfigure(2, minsize=160)
        self.label(footer, '최초 실행 시 필요한 도구를 자동으로 준비합니다.', MUTED).grid(row=0, column=0, sticky='w')
        self.choose_button = self.button(footer, '저장폴더 변경', self.choose)
        self.choose_button.grid(row=0, column=1, sticky='nsew', padx=(0, 10))
        self.update_button = self.button(footer, '다운로드 도구 업데이트', self.update_tools)
        self.update_button.configure(padx=7)
        self.update_button.grid(row=0, column=2, sticky='nsew')
        footer.rowconfigure(0, minsize=42)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.poll)
        self.entry.focus_set()

    def label(self, parent, text, color, **kwargs):
        return tk.Label(parent, text=text, bg=parent['bg'], fg=color,
                        font=TEXT_FONT, **kwargs)

    def radio_image(self, selected):
        image = tk.PhotoImage(width=20, height=20)
        colors = {name: tuple(component // 257 for component in self.winfo_rgb(color))
                  for name, color in {'bg': BG, 'ring': '#919191', 'white': CARD, 'blue': ACCENT}.items()}
        for y in range(20):
            row = []
            for x in range(20):
                samples = []
                for sy in range(4):
                    for sx in range(4):
                        distance = ((x + (sx + .5) / 4 - 10) ** 2 + (y + (sy + .5) / 4 - 10) ** 2) ** .5
                        key = 'bg' if distance > 8 else 'ring' if distance > 6.8 else 'blue' if selected and distance < 4.8 else 'white'
                        samples.append(colors[key])
                rgb = tuple(round(sum(s[i] for s in samples) / 16) for i in range(3))
                row.append('#%02x%02x%02x' % rgb)
            image.put('{' + ' '.join(row) + '}', to=(0, y))
        return image

    def button(self, parent, text, callback, primary=False, emphasis=False):
        return tk.Button(parent, text=text, command=callback, bg=ACCENT if primary else SECONDARY,
                         fg='white' if primary else INK, relief='flat', bd=0, highlightthickness=0,
                         font=DOWNLOAD_FONT if emphasis else TEXT_FONT, padx=10, pady=9,
                         cursor='hand2', activebackground='#3974CB' if primary else '#DCE5F0',
                         activeforeground='white' if primary else INK,
                         disabledforeground='#D6E3F8' if primary else '#999999')

    def paste(self):
        try:
            self.url.set(self.clipboard_get().strip())
        except tk.TclError:
            messagebox.showinfo('주소 붙여넣기', '클립보드에 복사된 텍스트가 없습니다.')

    def choose(self):
        folder = filedialog.askdirectory(initialdir=self.folder.get(), title='MP3 저장 폴더')
        if folder:
            self.folder.set(folder)

    def open_folder(self):
        try:
            path = Path(self.folder.get())
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(path)
        except OSError as error:
            messagebox.showerror('저장 폴더', str(error))

    def set_busy(self, value):
        self.busy = value
        for widget in [self.start_button, self.choose_button, self.update_button, self.paste_button, self.entry, *self.radios]:
            widget.configure(state='disabled' if value else 'normal')
        self.stop_button.configure(state='normal' if value else 'disabled')

    def start(self, update=False):
        if self.busy:
            return
        url, folder, playlist = self.url.get(), self.folder.get(), self.mode.get() == 'playlist'
        if not update:
            try:
                normalize_url(url, playlist)
            except ValueError as error:
                messagebox.showerror('주소 확인', str(error))
                return
        self.set_busy(True)
        self.progress.set(0)
        self.count.set('저장 확인 0곡')
        self.status.set('다운로드 도구 준비 중…' if not update else '다운로드 도구 업데이트 중…')
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')
        self.worker = Downloader(lambda kind, value: self.events.put((kind, value)))
        threading.Thread(target=self.worker.run, args=(url, folder, playlist, update), daemon=True).start()

    def update_tools(self):
        self.start(update=True)

    def stop(self):
        if self.worker:
            self.status.set('중지 중…')
            self.stop_button.configure(state='disabled')
            threading.Thread(target=self.worker.stop, daemon=True).start()

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get_nowait()
            if kind == 'log':
                self.log.configure(state='normal')
                self.log.insert('end', value + '\n')
                if int(self.log.index('end-1c').split('.')[0]) > 700:
                    self.log.delete('1.0', '100.0')
                self.log.see('end')
                self.log.configure(state='disabled')
                if not self.worker.cancelled.is_set():
                    self.status.set(value[:100])
            elif kind == 'progress':
                self.progress.set(value)
                self.status.set(f'현재 곡 다운로드 · {value:.1f}% · 다운로드 후 MP3로 변환합니다.')
            elif kind == 'count':
                self.count.set(f'저장 확인 {value}곡')
            elif kind == 'done':
                self.status.set(value)
            elif kind == 'idle':
                self.set_busy(False)
                if self.closing:
                    self.destroy()
                    return
        self.after(100, self.poll)

    def close(self):
        if self.busy:
            if not messagebox.askyesno('YouTube to MP3 종료', '진행 중인 작업을 중지하고 닫을까요?'):
                return
            self.closing = True
            self.stop()
        else:
            self.destroy()

if __name__ == '__main__':
    App().mainloop()
