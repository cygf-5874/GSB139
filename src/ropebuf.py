"""ropebuf —— 持久化 Rope 文本缓冲。"""

import counter


LEAF_LIMIT = 64


class _Node:
    __slots__ = ()


class _Leaf(_Node):
    __slots__ = ("text", "length", "height")

    def __init__(self, text):
        self.text = text
        self.length = len(text)
        self.height = 1


class _Branch(_Node):
    __slots__ = ("left", "right", "length", "height")

    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.length = left.length + right.length
        self.height = max(left.height, right.height) + 1


def _from_text(text, start, end):
    length = end - start
    if length <= LEAF_LIMIT:
        return _Leaf(text[start:end])

    middle = start + (length // 2)
    return _Branch(_from_text(text, start, middle),
                   _from_text(text, middle, end))


def _rotate_right(node):
    left = node.left
    if left.right.height > left.left.height:
        new_left = _Branch(left.left, left.right.left)
        new_right = _Branch(left.right.right, node.right)
        return _Branch(new_left, new_right)

    new_right = _Branch(left.right, node.right)
    return _Branch(left.left, new_right)


def _rotate_left(node):
    right = node.right
    if right.left.height > right.right.height:
        new_left = _Branch(node.left, right.left.left)
        new_right = _Branch(right.left.right, right.right)
        return _Branch(new_left, new_right)

    new_left = _Branch(node.left, right.left)
    return _Branch(new_left, right.right)


def _rebalance(left, right):
    left_height = left.height
    right_height = right.height

    if left_height > right_height + 1:
        counter.Counter.bump(1)
        return _rotate_right(_Branch(left, right))

    if right_height > left_height + 1:
        counter.Counter.bump(1)
        return _rotate_left(_Branch(left, right))

    return _Branch(left, right)


def _join(left, right):
    if left is None:
        return right
    if right is None:
        return left

    counter.Counter.bump(1)
    if left.height > right.height + 2:
        joined = _join(left.right, right)
        return _rebalance(left.left, joined)

    if right.height > left.height + 2:
        joined = _join(left, right.left)
        return _rebalance(joined, right.right)

    return _rebalance(left, right)


def _split(node, index):
    if index == 0:
        return None, node
    if index == node.length:
        return node, None

    counter.Counter.bump(1)

    if isinstance(node, _Leaf):
        return _Leaf(node.text[:index]), _Leaf(node.text[index:])

    left_length = node.left.length
    if index < left_length:
        first, second = _split(node.left, index)
        return first, _join(second, node.right)

    if index > left_length:
        first, second = _split(node.right, index - left_length)
        return _join(node.left, first), second

    return node.left, node.right


class Rope:
    """不可变文本缓冲。所有编辑返回新的 ``Rope``，不修改自身。"""

    __slots__ = ("_root",)

    def __init__(self, text=""):
        if not isinstance(text, str):
            raise TypeError("text 必须是 str")
        self._root = _from_text(text, 0, len(text)) if text else None

    @classmethod
    def _from_root(cls, root):
        rope = object.__new__(cls)
        rope._root = root
        return rope

    @classmethod
    def from_str(cls, text):
        return cls(text)

    def length(self):
        return 0 if self._root is None else self._root.length

    def to_str(self):
        if self._root is None:
            return ""

        parts = []
        stack = [self._root]
        while stack:
            node = stack.pop()
            if isinstance(node, _Leaf):
                parts.append(node.text)
            else:
                stack.append(node.right)
                stack.append(node.left)
        return "".join(parts)

    def char_at(self, index):
        if index < 0 or index >= self.length():
            raise IndexError("字符索引越界：%r" % (index,))

        node = self._root
        while isinstance(node, _Branch):
            counter.Counter.bump(1)
            if index < node.left.length:
                node = node.left
            else:
                index -= node.left.length
                node = node.right

        counter.Counter.bump(1)
        return node.text[index]

    def insert(self, index, text):
        if not isinstance(text, str):
            raise TypeError("text 必须是 str")
        if index < 0 or index > self.length():
            raise IndexError("插入位置越界：%r" % (index,))
        if text == "":
            return self

        first, second = _split(self._root, index)
        inserted = _from_text(text, 0, len(text))
        return Rope._from_root(_join(_join(first, inserted), second))

    def delete(self, index, count):
        if index < 0 or count < 0 or index + count > self.length():
            raise IndexError("删除范围越界：%r,%r" % (index, count))
        if count == 0:
            return self

        first, rest = _split(self._root, index)
        _, remaining = _split(rest, count)
        return Rope._from_root(_join(first, remaining))

    def slice(self, start, end):
        if start < 0 or end < start or end > self.length():
            raise IndexError("切片范围越界：%r,%r" % (start, end))
        if start == end:
            return Rope()
        if start == 0 and end == self.length():
            return self

        _, rest = _split(self._root, start)
        result, _ = _split(rest, end - start)
        return Rope._from_root(result)

    def concat(self, other):
        if not isinstance(other, Rope):
            raise TypeError("concat 需要另一个 Rope")
        return Rope._from_root(_join(self._root, other._root))

    def depth(self):
        return 0 if self._root is None else self._root.height
