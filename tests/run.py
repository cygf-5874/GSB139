"""ropebuf 既有用例（unittest）。

起点：`src/ropebuf.py` 的实现语义正确但每次编辑重建整串，本文件当前**全绿**。
本文件只覆盖少量基本形状，不对固定件的全部场景下断言。**勿改本文件。**
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "src"))

from ropebuf import Rope  # noqa: E402


class RopeTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(Rope.from_str("").to_str(), "")

    def test_length(self):
        self.assertEqual(Rope.from_str("hello").length(), 5)

    def test_insert_middle(self):
        self.assertEqual(Rope.from_str("helo").insert(3, "l").to_str(), "hello")

    def test_delete_middle(self):
        self.assertEqual(Rope.from_str("heallo").delete(2, 1).to_str(), "hello")

    def test_slice(self):
        self.assertEqual(Rope.from_str("hello world").slice(0, 5).to_str(), "hello")

    def test_concat(self):
        self.assertEqual(Rope.from_str("foo").concat(Rope.from_str("bar")).to_str(), "foobar")

    def test_char_at(self):
        self.assertEqual(Rope.from_str("abc").char_at(1), "b")

    def test_immutable(self):
        base = Rope.from_str("abc")
        base.insert(1, "X")
        self.assertEqual(base.to_str(), "abc")

    def test_index_error(self):
        with self.assertRaises(IndexError):
            Rope.from_str("abc").char_at(3)

    def test_unicode_by_char(self):
        self.assertEqual(Rope.from_str("中文a").char_at(1), "文")


if __name__ == "__main__":
    unittest.main(verbosity=2)