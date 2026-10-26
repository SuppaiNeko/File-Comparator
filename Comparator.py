# -*- coding: utf-8 -*-
"""
File Comparator: a small Tkinter GUI that compares the files in two directories.

Pick Directory A and Directory B, optionally narrow the comparison to a single
file extension, and optionally include subdirectories ("Full Directory").
Files are paired up by their path relative to each directory and compared with
filecmp. Files whose contents differ, and files that exist on only one side,
are listed in the log window.

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
    """Main window: two directory pickers, a file type filter and a log."""

    def __init__(self, master=None):
        super().__init__(master)

        self.master.title("File Comparator")
        # Built with --noconsole there is no stderr, so show unexpected errors in the log instead
        self.master.report_callback_exception = self.report_error

        self.dir1 = None
        self.dir2 = None

        # File extensions found in each directory, e.g. ['.txt', '.csv']
        self.dir1_types = []
        self.dir2_types = []

        self.widgets = []
        self.add_widgets()

        self.line_number = 0

    def add_widgets(self):
        """Create and lay out all widgets on the grid."""
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

        # Only offers extensions present in both directories (see update_combobox)
        self.lst1 = ttk.Combobox(self, values=["All"], width=10)
        self.lst1.grid(row=2, column=4, columnspan=1)
        self.lst1.current(0)

        self.chk1var = tk.IntVar()
        self.chk1 = tk.Checkbutton(self, text="Full Directory", variable=self.chk1var, onvalue=True, offvalue=False, command=self.check_box)
        self.chk1.grid(row=2, column=5)

        # console output
        self.textbox = scrolledtext.ScrolledText(self, height=15, state='disabled')
        self.textbox.grid(row=3, column=0, columnspan=15, pady=15, padx=15)

    def output_text(self, text):
        """Append a numbered, timestamped line to the log window."""
        header = '[{}]'.format(self.line_number) + '[' + dt.now().strftime("%H:%M:%S") + '] '
        self.textbox.configure(state='normal')
        self.textbox.insert("end", header + text + "\n")
        self.textbox.configure(state='disabled')
        self.line_number += 1
        self.textbox.see(tk.END)

    def report_error(self, exc, val, tb):
        """Log an unhandled exception raised by a button or checkbox handler."""
        self.output_text("ERROR: {}: {}".format(exc.__name__, val))

    def dir_sel_btn_1(self):
        """Ask for Directory A, then refresh its file types and the filter list."""
        directory = filedialog.askdirectory()
        if not directory:  # dialog was cancelled
            return
        self.dir1 = directory
        # set text box to selection
        self.box1.delete(0, tk.END)
        self.box1.insert(0, self.dir1)
        self.output_text("Directory A: " + self.dir1)
        self.dir1_types = self.check_filetypes(self.dir1)
        self.output_text("Directory A types: " + str(self.dir1_types))
        self.update_combobox()

    def dir_sel_btn_2(self):
        """Ask for Directory B, then refresh its file types and the filter list."""
        directory = filedialog.askdirectory()
        if not directory:  # dialog was cancelled
            return
        self.dir2 = directory
        # set text box to selection
        self.box2.delete(0, tk.END)
        self.box2.insert(0, self.dir2)
        self.output_text("Directory B: " + self.dir2)
        self.dir2_types = self.check_filetypes(self.dir2)
        self.output_text("Directory B types: " + str(self.dir2_types))
        self.update_combobox()

    def list_files(self, directory):
        """Return the set of files in directory, as paths relative to it.

        Subdirectories are searched too when "Full Directory" is ticked.
        Relative paths let files in matching subfolders be paired up.
        """
        path = Path(directory)
        found = path.rglob('*') if self.chk1var.get() else path.iterdir()
        return {str(file.relative_to(path)) for file in found if file.is_file()}

    def check_filetypes(self, directory):
        """Return the sorted, lowercased file extensions found in directory."""
        types = {Path(file).suffix.lower() for file in self.list_files(directory)}
        types.discard('')  # files with no extension
        return sorted(types)

    def update_combobox(self):
        """Offer "All" plus every extension present in both directories."""
        values = ['All']
        for t in self.dir1_types:
            if t in self.dir2_types:
                values.append(t)
        self.lst1['values'] = values
        # Fall back to "All" if the previous choice is no longer offered
        if self.lst1.get() not in values:
            self.lst1.current(0)

    def check_box(self):
        """Rescan both directories when "Full Directory" is toggled."""
        if not self.dir1 or not self.dir2:
            return None
        self.dir1_types = self.check_filetypes(self.dir1)
        self.output_text("Directory A types: " + str(self.dir1_types))
        self.dir2_types = self.check_filetypes(self.dir2)
        self.output_text("Directory B types: " + str(self.dir2_types))
        self.update_combobox()

    def comp_files(self):
        """Compare the two directories and log differing and missing files.

        The directories are read from the text boxes, so typed paths work too.
        Files present in both are compared with filecmp.cmpfiles, which treats
        files with identical size and modification time as equal without
        reading their contents.
        """
        self.dir1 = self.box1.get()
        self.dir2 = self.box2.get()
        for label, directory in (('A', self.dir1), ('B', self.dir2)):
            if not directory or not Path(directory).is_dir():
                self.output_text("Directory {} is not a valid directory: '{}'".format(label, directory))
                return
        self.output_text("Starting file comparison.")
        file_type = self.lst1.get().lower() or 'all'

        files1 = self.list_files(self.dir1)
        files2 = self.list_files(self.dir2)
        if file_type != 'all':
            files1 = {f for f in files1 if Path(f).suffix.lower() == file_type}
            files2 = {f for f in files2 if Path(f).suffix.lower() == file_type}

        only1 = sorted(files1 - files2)
        only2 = sorted(files2 - files1)
        match, mismatch, errors = filecmp.cmpfiles(self.dir1, self.dir2, sorted(files1 & files2))

        self.output_text("{} {} files in total".format(len(files1 | files2), self.lst1.get() or 'All'))
        if mismatch:
            self.output_text("============== NON MATCHING FILES ==============")
            for file in mismatch:
                self.output_text(file)
        if only1 or only2:
            self.output_text("================ MISSING FILES =================")
            for file in only1:
                self.output_text(file + '---------> Not in Directory B')
            for file in only2:
                self.output_text(file + '---------> Not in Directory A')
        if errors:
            # In both directories but could not be read (e.g. permissions)
            self.output_text("=============== UNREADABLE FILES ===============")
            for file in errors:
                self.output_text(file)
        if not mismatch and not only1 and not only2 and not errors:
            self.output_text("No File discrepancies")

        self.output_text("Comparison Complete")


if __name__ == '__main__':
    root = tk.Tk()
    root.resizable(width=False, height=False)
    gui = App(root)
    root.mainloop()
