# -*- coding: utf-8 -*-
"""
Unit tests for Comparator.py.

Each test builds a fresh App on a hidden Tk window and points it at temporary
directories. Run with:  python -m unittest -v
"""

import os
import re
import shutil
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest import mock

import Comparator

# Strips the "[3][12:34:56] " prefix that output_text adds to every line
LOG_PREFIX = re.compile(r'^\[\d+\]\[\d\d:\d\d:\d\d\] ')


def make_files(root, files):
    """Create files under root from a {relative path: contents} dict."""
    for rel, contents in files.items():
        path = Path(root, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)


class ComparatorTestCase(unittest.TestCase):
    """Shared setup: a hidden Tk root, a fresh App and two temp directories."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as e:  # no display available
            raise unittest.SkipTest("Tk is not available: {}".format(e))
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.dir_a = tempfile.mkdtemp()
        self.dir_b = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir_a, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.dir_b, ignore_errors=True)
        self.app = Comparator.App(self.root)
        self.addCleanup(self.app.destroy)

    def log_lines(self):
        """Return the log window's lines without their number/time prefix."""
        text = self.app.textbox.get('1.0', 'end').strip()
        return [LOG_PREFIX.sub('', line) for line in text.splitlines()]

    def select_dirs(self, dir_a=None, dir_b=None):
        """Pick both directories through the Select buttons."""
        answers = [dir_a or self.dir_a, dir_b or self.dir_b]
        with mock.patch.object(Comparator.filedialog, 'askdirectory', side_effect=answers):
            self.app.dir_sel_btn_1()
            self.app.dir_sel_btn_2()

    def compare(self):
        """Clear the log, run a comparison and return the new log lines."""
        self.app.textbox.configure(state='normal')
        self.app.textbox.delete('1.0', 'end')
        self.app.textbox.configure(state='disabled')
        self.app.comp_files()
        return self.log_lines()


class TestListFiles(ComparatorTestCase):

    def setUp(self):
        super().setUp()
        make_files(self.dir_a, {'top.txt': '', 'sub/nested.txt': '', 'sub/deeper/deep.csv': ''})

    def test_top_level_only_by_default(self):
        self.assertEqual(self.app.list_files(self.dir_a), {'top.txt'})

    def test_full_directory_returns_relative_paths(self):
        self.app.chk1var.set(1)
        self.assertEqual(self.app.list_files(self.dir_a), {
            'top.txt',
            os.path.join('sub', 'nested.txt'),
            os.path.join('sub', 'deeper', 'deep.csv'),
        })

    def test_directories_are_not_listed(self):
        Path(self.dir_a, 'folder.txt').mkdir()
        self.assertNotIn('folder.txt', self.app.list_files(self.dir_a))


class TestCheckFiletypes(ComparatorTestCase):

    def test_sorted_lowercase_and_unique(self):
        make_files(self.dir_a, {'b.TXT': '', 'a.txt': '', 'c.Csv': ''})
        self.assertEqual(self.app.check_filetypes(self.dir_a), ['.csv', '.txt'])

    def test_files_without_extension_are_ignored(self):
        make_files(self.dir_a, {'README': '', 'a.txt': ''})
        self.assertEqual(self.app.check_filetypes(self.dir_a), ['.txt'])

    def test_full_directory_includes_subfolder_types(self):
        make_files(self.dir_a, {'a.txt': '', 'sub/b.csv': ''})
        self.assertEqual(self.app.check_filetypes(self.dir_a), ['.txt'])
        self.app.chk1var.set(1)
        self.assertEqual(self.app.check_filetypes(self.dir_a), ['.csv', '.txt'])


class TestFileTypeCombobox(ComparatorTestCase):

    def test_defaults_to_all(self):
        self.assertEqual(self.app.lst1.get(), 'All')

    def test_offers_only_types_in_both_directories(self):
        make_files(self.dir_a, {'a.txt': '', 'a.csv': '', 'a.log': ''})
        make_files(self.dir_b, {'b.txt': '', 'b.csv': '', 'b.ini': ''})
        self.select_dirs()
        self.assertEqual(self.app.lst1['values'], ('All', '.csv', '.txt'))

    def test_resets_to_all_when_choice_disappears(self):
        make_files(self.dir_a, {'a.txt': ''})
        make_files(self.dir_b, {'b.txt': ''})
        self.select_dirs()
        self.app.lst1.set('.txt')

        other = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, other, ignore_errors=True)
        make_files(other, {'c.csv': ''})
        with mock.patch.object(Comparator.filedialog, 'askdirectory', return_value=other):
            self.app.dir_sel_btn_2()
        self.assertEqual(self.app.lst1.get(), 'All')

    def test_toggling_full_directory_rescans(self):
        make_files(self.dir_a, {'sub/a.csv': ''})
        make_files(self.dir_b, {'sub/b.csv': ''})
        self.select_dirs()
        self.assertEqual(self.app.lst1['values'], ('All',))
        self.app.chk1var.set(1)
        self.app.check_box()
        self.assertEqual(self.app.lst1['values'], ('All', '.csv'))


class TestDirectorySelection(ComparatorTestCase):

    def test_selection_fills_text_box(self):
        self.select_dirs()
        self.assertEqual(self.app.box1.get(), self.dir_a)
        self.assertEqual(self.app.box2.get(), self.dir_b)
        self.assertEqual(self.app.dir1, self.dir_a)
        self.assertEqual(self.app.dir2, self.dir_b)

    def test_cancel_keeps_previous_selection(self):
        self.select_dirs()
        with mock.patch.object(Comparator.filedialog, 'askdirectory', return_value=''):
            self.app.dir_sel_btn_1()
            self.app.dir_sel_btn_2()
        self.assertEqual(self.app.dir1, self.dir_a)
        self.assertEqual(self.app.dir2, self.dir_b)
        self.assertEqual(self.app.box1.get(), self.dir_a)
        self.assertEqual(self.app.box2.get(), self.dir_b)


class TestCompareFiles(ComparatorTestCase):

    def test_identical_directories(self):
        make_files(self.dir_a, {'a.txt': 'same', 'b.csv': 'same'})
        make_files(self.dir_b, {'a.txt': 'same', 'b.csv': 'same'})
        self.select_dirs()
        lines = self.compare()
        self.assertIn('2 All files in total', lines)
        self.assertIn('No File discrepancies', lines)
        self.assertEqual(lines[-1], 'Comparison Complete')

    def test_reports_mismatch_once(self):
        make_files(self.dir_a, {'a.txt': 'one'})
        make_files(self.dir_b, {'a.txt': 'two!'})
        self.select_dirs()
        lines = self.compare()
        self.assertIn('1 All files in total', lines)
        self.assertEqual(lines.count('a.txt'), 1)
        self.assertNotIn('No File discrepancies', lines)

    def test_reports_missing_files_on_each_side(self):
        make_files(self.dir_a, {'shared.txt': 'x', 'only_a.txt': 'x'})
        make_files(self.dir_b, {'shared.txt': 'x', 'only_b.txt': 'x'})
        self.select_dirs()
        lines = self.compare()
        self.assertIn('3 All files in total', lines)
        self.assertIn('only_a.txt---------> Not in Directory B', lines)
        self.assertIn('only_b.txt---------> Not in Directory A', lines)

    def test_subfolders_ignored_without_full_directory(self):
        make_files(self.dir_a, {'sub/a.txt': 'one'})
        make_files(self.dir_b, {'sub/a.txt': 'two!'})
        self.select_dirs()
        lines = self.compare()
        self.assertIn('0 All files in total', lines)
        self.assertIn('No File discrepancies', lines)

    def test_full_directory_compares_nested_files(self):
        make_files(self.dir_a, {'sub/same.txt': 'x', 'sub/diff.txt': 'one', 'sub/only_a.txt': 'x'})
        make_files(self.dir_b, {'sub/same.txt': 'x', 'sub/diff.txt': 'two!'})
        self.app.chk1var.set(1)
        self.select_dirs()
        lines = self.compare()
        self.assertIn('3 All files in total', lines)
        self.assertIn(os.path.join('sub', 'diff.txt'), lines)
        self.assertIn(os.path.join('sub', 'only_a.txt') + '---------> Not in Directory B', lines)
        self.assertNotIn(os.path.join('sub', 'same.txt'), lines)

    def test_same_name_in_different_subfolders_is_not_merged(self):
        # x/f.txt only exists in A and y/f.txt only in B: two missing files, not one match
        make_files(self.dir_a, {'x/f.txt': 'same'})
        make_files(self.dir_b, {'y/f.txt': 'same'})
        self.app.chk1var.set(1)
        self.select_dirs()
        lines = self.compare()
        self.assertIn('2 All files in total', lines)
        self.assertIn(os.path.join('x', 'f.txt') + '---------> Not in Directory B', lines)
        self.assertIn(os.path.join('y', 'f.txt') + '---------> Not in Directory A', lines)

    def test_file_type_filter(self):
        make_files(self.dir_a, {'a.txt': 'one', 'a.csv': 'one'})
        make_files(self.dir_b, {'a.txt': 'one', 'a.csv': 'two!'})
        self.select_dirs()
        self.app.lst1.set('.txt')
        lines = self.compare()
        self.assertIn('1 .txt files in total', lines)
        self.assertIn('No File discrepancies', lines)

    def test_file_type_filter_ignores_case(self):
        make_files(self.dir_a, {'a.TXT': 'one'})
        make_files(self.dir_b, {'a.TXT': 'two!'})
        self.select_dirs()
        self.app.lst1.set('.txt')
        lines = self.compare()
        self.assertIn('1 .txt files in total', lines)
        self.assertIn('a.TXT', lines)

    def test_blank_file_type_means_all(self):
        make_files(self.dir_a, {'a.txt': 'x', 'noext': 'x'})
        make_files(self.dir_b, {'a.txt': 'x', 'noext': 'x'})
        self.select_dirs()
        self.app.lst1.set('')
        lines = self.compare()
        self.assertIn('2 All files in total', lines)

    def test_typed_paths_are_used(self):
        make_files(self.dir_a, {'a.txt': 'one'})
        make_files(self.dir_b, {'a.txt': 'two!'})
        self.app.box1.insert(0, self.dir_a)
        self.app.box2.insert(0, self.dir_b)
        lines = self.compare()
        self.assertIn('a.txt', lines)

    def test_unreadable_files_get_own_section(self):
        make_files(self.dir_a, {'locked.txt': 'x'})
        make_files(self.dir_b, {'locked.txt': 'x'})
        self.select_dirs()
        with mock.patch.object(Comparator.filecmp, 'cmpfiles', return_value=([], [], ['locked.txt'])):
            lines = self.compare()
        self.assertIn('=============== UNREADABLE FILES ===============', lines)
        self.assertIn('locked.txt', lines)
        self.assertNotIn('No File discrepancies', lines)


class TestInvalidInput(ComparatorTestCase):

    def test_empty_path_is_rejected(self):
        self.app.box2.insert(0, self.dir_b)
        lines = self.compare()
        self.assertEqual(lines, ["Directory A is not a valid directory: ''"])

    def test_missing_path_is_rejected(self):
        missing = os.path.join(self.dir_b, 'does-not-exist')
        self.app.box1.insert(0, self.dir_a)
        self.app.box2.insert(0, missing)
        lines = self.compare()
        self.assertEqual(lines, ["Directory B is not a valid directory: '{}'".format(missing)])

    def test_file_path_is_rejected(self):
        make_files(self.dir_a, {'a.txt': ''})
        file_path = os.path.join(self.dir_a, 'a.txt')
        self.app.box1.insert(0, file_path)
        self.app.box2.insert(0, self.dir_b)
        lines = self.compare()
        self.assertEqual(lines, ["Directory A is not a valid directory: '{}'".format(file_path)])

    def test_unexpected_errors_are_logged(self):
        self.assertEqual(self.root.report_callback_exception, self.app.report_error)
        self.app.report_error(PermissionError, PermissionError('access denied'), None)
        self.assertEqual(self.log_lines(), ['ERROR: PermissionError: access denied'])


if __name__ == '__main__':
    unittest.main()
