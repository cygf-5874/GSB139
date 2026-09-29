"""ropebuf —— Rope 文本缓冲。

对外接口与语义见 README「对外契约」一节。

本实现是「整体字符串」版本：语义正确，但每次编辑都会重建整串，
节点访问计数随文本长度线性增长。
"""

import counter


class Rope:
    """不可变文本缓冲。所有编辑返回新的 ``Rope``，不修改自身。"""

    __slots__ = ("_text",)

    def __init__(self, text=""):
        if not isinstance(text, str):
            raise TypeError("text 必须是 str")
        self._text = text

    @classmethod
    def from_str(cls, text):
        return cls(text)

    def length(self):
        return len(self._text)

    def to_str(self):
        return self._text

    def char_at(self, index):
        if index < 0 or index >= len(self._text):
            raise IndexError("字符索引越界：%r" % (index,))
        counter.Counter.bump(1)
        return self._text[index]

    def insert(self, index, text):
        if index < 0 or index > len(self._text):
            raise IndexError("插入位置越界：%r" % (index,))
        counter.Counter.bump(len(self._text) + len(text))
        return Rope(self._text[:index] + text + self._text[index:])

    def delete(self, index, count):
        if index < 0 or count < 0 or index + count > len(self._text):
            raise IndexError("删除范围越界：%r,%r" % (index, count))
        counter.Counter.bump(len(self._text))
        return Rope(self._text[:index] + self._text[index + count:])

    def slice(self, start, end):
        if start < 0 or end < start or end > len(self._text):
            raise IndexError("切片范围越界：%r,%r" % (start, end))
        return Rope(self._text[start:end])

    def concat(self, other):
        if not isinstance(other, Rope):
            raise TypeError("concat 需要另一个 Rope")
        return Rope(self._text + other._text)

    def depth(self):
        return 0