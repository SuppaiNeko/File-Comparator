# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 09:27:59 2022

@author: Colem
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog

from datetime import datetime as dt
from pathlib import Path

import filecmp


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__()

        self.master.title("File Comparator")

        self.dir1 = None
        self.dir2 = None

        self.dir1_types = []
        self.dir2_types = []

        self.widgets = []
        self.add_widgets()

        self.line_number = 0

    def add_widgets(self):
        self.pack()

        self.b1 = tk.Button(self, text='Select', width=20, command=self.dir_sel_btn_1)
        self.b1.grid(row=0, column=13, pady=10)

        self.box1 = tk.Entry(self, text='', width=70)
        self.box1.grid(row=0, column=1, columnspan=10, padx=5, sticky=tk.W)

        self.lbl1 = tk.Label(self, text='Directory A:')
        self.lbl1.grid(row=0, column=0)

        # lower
        self.b2 = tk.Button(self, text='Select', width=20, command=self.dir_sel_btn_2)
        self.b2.grid(row=1, column=13, pady=10)

        self.box2 = tk.Entry(self, text='', width=70)
        self.box2.grid(row=1, column=1, columnspan=10, padx=5, sticky=tk.W)

        self.lbl2 = tk.Label(self, text='Directory B:')
        self.lbl2.grid(row=1, column=0)

        # start
        self.b3 = tk.Button(self, text="Compare Dirs", command=self.comp_files)
        self.b3.grid(row=2, column=10, pady=10)

        self.lbl3 = tk.Label(self, text="File Type:")
        self.lbl3.grid(row=2, column=3)

        self.lst1 = ttk.Combobox(self, values=["All"], width=10)
        self.lst1.grid(row=2, column=4, columnspan=1)

        self.chk1var = tk.IntVar()
        self.chk1 = tk.Checkbutton(self, text="Full Directory", variable=self.chk1var, onvalue=True, offvalue=False, command=self.check_box)
        self.chk1.grid(row=2, column=5)

        # console output
        self.textbox = scrolledtext.ScrolledText(self, height=15, state='disabled')
        self.textbox.grid(row=3, column=0, columnspan=15, pady=15, padx=15)

    def output_text(self, text):
        header = '[{}]'.format(self.line_number) + '[' + dt.now().strftime("%H:%M:%S") + '] '
        self.textbox.configure(state='normal')
        self.textbox.insert("end", header + text + "\n")
        self.textbox.configure(state='disabled')
        self.line_number += 1
        self.textbox.see(tk.END)

    def dir_sel_btn_1(self):
        self.dir1 = filedialog.askdirectory()
        # set text box to selection
        self.box1.delete(0, tk.END)
        self.box1.insert(0, self.dir1)
        self.output_text("Directory A: " + self.dir1)
        self.dir1_types = self.check_filetypes(self.dir1)
        self.output_text("Directory A types: " + str(self.dir1_types))
        self.update_combobox()

    def dir_sel_btn_2(self):
        self.dir2 = filedialog.askdirectory()
        # set text box to selection
        self.box2.delete(0, tk.END)
        self.box2.insert(0, self.dir2)
        self.output_text("Directory B: " + self.dir2)
        self.dir2_types = self.check_filetypes(self.dir2)
        self.output_text("Directory B types: " + str(self.dir2_types))
        self.update_combobox()

    def check_filetypes(self, directory):
        path = Path(directory)
        #Check is we need all files in subdirectorys
        if self.chk1var.get():
            files = [file.suffix.lower() for file in path.rglob('*')]
        else:
            files = [file.suffix.lower() for file in path.iterdir()]
        types = []
        for file in files:
            if file not in types and file != '':
                types.append(file)
        return types

    def update_combobox(self):
        values = ['All']
        for t in self.dir1_types:
            if t in self.dir2_types:
                values.append(t)
        self.lst1['values'] = values

    def check_box(self):
        if not self.dir1 or not self.dir2:
            return None
        self.dir1_types = self.check_filetypes(self.dir1)
        self.output_text("Directory A types: " + str(self.dir1_types))
        self.dir2_types = self.check_filetypes(self.dir2)
        self.output_text("Directory B types: " + str(self.dir2_types))
        self.update_combobox()


    def comp_files(self):
        self.output_text("Starting file comparison.")
        self.dir1 = self.box1.get()
        self.dir2 = self.box2.get()
        file_type = self.lst1.get()
        p1 = Path(self.dir1)
        p2 = Path(self.dir2)
        files = []
        if file_type == 'All':
            if self.chk1var.get():
                files = [i.name for i in p1.rglob('*') if i.is_file()] + [j.name for j in p2.rglob('*') if j.is_file()]
            else:
                files = [i.name for i in p1.iterdir() if i.is_file()] + [j.name for j in p2.iterdir() if j.is_file()]
        else:
            if self.chk1var.get():
                for file in [i for i in p1.rglob('*')] + [j for j in p2.rglob('*')]:
                    if file_type == file.suffix.lower() and file.name not in files:
                        files.append(file.name)
            else:
                for file in [i for i in p1.iterdir()] + [j for j in p2.iterdir()]:
                    if file_type == file.suffix.lower() and file.name not in files:
                        files.append(file.name)
        match, mismatch, errors = filecmp.cmpfiles(p1, p2, files)
        self.output_text("{} {} files in total".format(len(files), file_type))
        if mismatch:
            self.output_text("============== NON MATCHING FILES ==============")
            for file in mismatch:
                self.output_text(file)
        if errors:
            self.output_text("================ MISSING FILES =================")
            for file in errors:
                if file in [i.name for i in p1.iterdir() if i.is_file()]:
                    self.output_text(file + '---------> Not in Directory B')
                if file in [i.name for i in p2.iterdir() if i.is_file()]:
                    self.output_text(file + '---------> Not in Directory A')
        if not mismatch and not errors:
            self.output_text("No File discrepancies")

        self.output_text("Comparison Complete")


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry()
    root.resizable(width=False, height=False)
    gui = App()
    root.mainloop()
