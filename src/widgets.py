"""Shared rounded surfaces and pixel-sized buttons for the desktop UI."""
import tkinter as tk
from tkinter import font as tkfont

RADIUS = 4
BORDER = '#D0DAE4'


def rounded(canvas, width, height, fill, border, line_width=1):
    width, height = max(1, width), max(1, height)
    background = canvas.cget('bg')
    key = width, height, fill, border, line_width, background
    if getattr(canvas, '_surface_key', None) != key:
        image = tk.PhotoImage(master=canvas, width=width, height=height)
        image.put(border or fill, to=(0, 0, width, height))
        edge = line_width if border else 0
        if width > edge * 2 and height > edge * 2:
            image.put(fill, to=(edge, edge, width-edge, height-edge))
        colors = [tuple(c // 257 for c in canvas.winfo_rgb(color))
                  for color in (background, border or fill, fill)]
        radius = min(RADIUS, width / 2, height / 2)
        for y in range(min(RADIUS, height)):
            for x in range(min(RADIUS, width)):
                samples = []
                for sy in range(4):
                    for sx in range(4):
                        distance = ((x+(sx+.5)/4-radius)**2 +
                                    (y+(sy+.5)/4-radius)**2)**.5
                        samples.append(colors[0 if distance > radius else
                                              1 if distance > radius-edge else 2])
                color = '#%02x%02x%02x' % tuple(round(sum(c[i] for c in samples)/16)
                                              for i in range(3))
                for px, py in ((x, y), (width-1-x, y),
                               (x, height-1-y), (width-1-x, height-1-y)):
                    image.put(color, to=(px, py))
        canvas._surface_image, canvas._surface_key = image, key
    return canvas.create_image(0, 0, anchor='nw', image=canvas._surface_image)


class RoundedPanel(tk.Canvas):
    def __init__(self, parent, fill='white', border=BORDER, line_width=1, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
        self.fill, self.border, self.line_width = fill, border, line_width
        self.bind('<Configure>', self.redraw)

    def redraw(self, event=None):
        self.delete('surface')
        item = rounded(self, self.winfo_width(), self.winfo_height(),
                       self.fill, self.border, self.line_width)
        self.itemconfigure(item, tags='surface')
        self.tag_lower(item)


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, font, height=34, primary=False, image=None):
        super().__init__(parent, height=height, bg=parent.cget('bg'), bd=0,
                         highlightthickness=0, takefocus=True, cursor='hand2')
        self.text, self.command, self.text_font = text, command, font
        self.primary, self.image, self.state, self.hover = primary, image, 'normal', False
        self.bind('<Configure>', self.redraw)
        self.bind('<Button-1>', self.invoke)
        self.bind('<Return>', self.invoke)
        self.bind('<space>', self.invoke)
        self.bind('<Enter>', lambda event: self.set_hover(True))
        self.bind('<Leave>', lambda event: self.set_hover(False))
        self.bind('<FocusIn>', self.redraw)
        self.bind('<FocusOut>', self.redraw)

    def configure(self, cnf=None, **kwargs):
        if 'state' in kwargs:
            self.state = kwargs.pop('state')
            super().configure(cursor='arrow' if self.state == 'disabled' else 'hand2')
        if 'text' in kwargs:
            self.text = kwargs.pop('text')
        result = super().configure(cnf, **kwargs)
        if hasattr(self, 'state'):
            self.redraw()
        return result

    config = configure

    def set_hover(self, value):
        self.hover = value
        self.redraw()

    def redraw(self, event=None):
        self.delete('all')
        width, height = self.winfo_width(), self.winfo_height()
        fill = '#427FDA' if self.primary else 'white'
        if self.hover and self.state != 'disabled':
            fill = '#3974CB' if self.primary else '#F5F8FC'
        border = fill if self.primary else BORDER
        if self.focus_get() == self and self.state != 'disabled':
            border = '#427FDA'
        rounded(self, width, height, fill, border)
        color = 'white' if self.primary else '#111111'
        if self.state == 'disabled':
            color = '#D6E3F8' if self.primary else '#777777'
        font = tkfont.Font(font=self.text_font)
        image_width = self.image.width() + 10 if self.image else 0
        group_width = font.measure(self.text) + image_width
        left = (width - group_width) / 2
        if self.image:
            self.create_image(left, height / 2, image=self.image, anchor='w')
        self.create_text(left + image_width, height / 2, text=self.text,
                         font=self.text_font, fill=color, anchor='w')

    def invoke(self, event=None):
        if self.state != 'disabled':
            self.focus_set()
            self.command()
            return 'break'
