#!/usr/bin/env python3
"""ropebuf 固定验收程序（固定件）。**勿改本文件。**

用法（在仓库根目录）：
  python check/check.py              跑全部场景
  python check/check.py -list        列出全部 `组/名`
  python check/check.py --only <组>  只跑某一组（equivalence / cost / balance / persist / edge）

输出：逐场景 `PASS <组>/<名>` 或 `FAIL <组>/<名>  期望=… 实际=…`，
结尾 `结果：通过 x/N`；全过 exit 0，否则 exit 1；失败不早退。

判据只描述对外可见性质（结果字符串与 `Counter.visits`），不依赖墙钟 / 随机源之外的
非确定因素：随机操作序列使用固定种子。
"""

import math
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, os.pardir, "src"))

import counter as counter_mod  # noqa: E402
import ropebuf as lib  # noqa: E402

SINGLE_BOUND = 4000
MASS_BOUND = 2000000
DEPTH_C = 2.0


def show(value):
    text = repr(value)
    return text if len(text) <= 200 else text[:200] + "…"


def expect_equal(expected, actual, label):
    if expected != actual:
        raise AssertionError("%s：期望=%s 实际=%s" % (label, show(expected), show(actual)))


def expect_true(cond, label, actual):
    if not cond:
        raise AssertionError("%s：实际=%s" % (label, show(actual)))


# ------------------------------------------------------------------ scenarios

def sc_eq_random_ops():
    rng = random.Random(20240928)
    alphabet = "abcdefghij"
    model = "start-"
    rope = lib.Rope.from_str(model)
    for _ in range(300):
        op = rng.randrange(3)
        if op == 0:
            pos = rng.randrange(len(model) + 1)
            size = rng.randrange(0, 4)
            chunk = "".join(rng.choice(alphabet) for _ in range(size))
            model = model[:pos] + chunk + model[pos:]
            rope = rope.insert(pos, chunk)
        elif op == 1:
            if not model:
                continue
            pos = rng.randrange(len(model))
            size = rng.randrange(0, min(4, len(model) - pos) + 1)
            model = model[:pos] + model[pos + size:]
            rope = rope.delete(pos, size)
        else:
            low = rng.randrange(len(model) + 1)
            high = rng.randrange(low, len(model) + 1)
            model = model[low:high]
            rope = rope.slice(low, high)
        expect_equal(model, rope.to_str(), "随机操作序列 to_str")
        expect_equal(len(model), rope.length(), "随机操作序列 length")
    for index in range(len(model)):
        expect_equal(model[index], rope.char_at(index), "随机结果 char_at(%d)" % index)


def sc_eq_slice_concat():
    base = "0123456789abcdef"
    rope = lib.Rope.from_str(base)
    for low in range(len(base) + 1):
        for high in range(low, len(base) + 1):
            expect_equal(base[low:high], rope.slice(low, high).to_str(),
                         "slice(%d,%d)" % (low, high))
    joined = rope.slice(0, 4).concat(rope.slice(10, 16))
    expect_equal(base[0:4] + base[10:16], joined.to_str(), "concat 结果")
    expect_equal(base, rope.to_str(), "原 Rope 未被修改")


def sc_eq_char_index():
    text = "\u4e2da\u6587b\U0001f642c"
    rope = lib.Rope.from_str(text)
    expect_equal(len(text), rope.length(), "length 按字符")
    expect_equal(text, rope.to_str(), "to_str 往返")
    for index, char in enumerate(text):
        expect_equal(char, rope.char_at(index), "char_at(%d)" % index)
    expect_equal(text[:3], rope.slice(0, 3).to_str(), "slice 按字符")


def sc_cost_single_edit():
    rope = lib.Rope.from_str("a" * 100000)
    counter_mod.Counter.reset()
    grown = rope.insert(50000, "zz")
    expect_true(counter_mod.Counter.visits <= SINGLE_BOUND,
                "单次 insert 访问计数 ≤ %d" % SINGLE_BOUND, counter_mod.Counter.visits)
    expect_equal(100002, grown.length(), "插入后长度")
    counter_mod.Counter.reset()
    shrunk = rope.delete(10, 3)
    expect_true(counter_mod.Counter.visits <= SINGLE_BOUND,
                "单次 delete 访问计数 ≤ %d" % SINGLE_BOUND, counter_mod.Counter.visits)
    expect_equal(99997, shrunk.length(), "删除后长度")


def sc_cost_mass_insert():
    rope = lib.Rope.from_str("a" * 100000)
    counter_mod.Counter.reset()
    for _ in range(1000):
        rope = rope.insert(0, "x")
    expect_true(counter_mod.Counter.visits < MASS_BOUND,
                "1000 次前缀插入总访问计数 < %d" % MASS_BOUND, counter_mod.Counter.visits)
    expect_equal(101000, rope.length(), "前缀插入后长度")
    expect_true(rope.to_str().startswith("x" * 1000), "前缀插入内容", rope.to_str()[:20])


def sc_balance_height_and_cache():
    n = 4096
    rope = lib.Rope.from_str("a" * n)
    limit = math.ceil(DEPTH_C * math.log2(n + 1))
    depth = rope.depth()
    expect_true(1 <= depth <= limit, "深度 ∈ [1,%d]" % limit, depth)
    counter_mod.Counter.reset()
    for _ in range(200):
        rope.length()
    expect_true(counter_mod.Counter.visits == 0,
                "length() 读缓存、不增加访问计数", counter_mod.Counter.visits)


def sc_persist_immutable():
    base = lib.Rope.from_str("hello world")
    inserted = base.insert(5, ",")
    deleted = base.delete(0, 1)
    sliced = base.slice(0, 5)
    merged = inserted.concat(sliced)
    edited = merged.insert(0, ">")
    expect_equal("hello world", base.to_str(), "base 未被 insert/delete/slice 修改")
    expect_equal("hello, world", inserted.to_str(), "insert 结果")
    expect_equal("ello world", deleted.to_str(), "delete 结果")
    expect_equal("hello", sliced.to_str(), "slice 结果")
    expect_equal("hello, worldhello", merged.to_str(), "concat 结果")
    expect_equal(">hello, worldhello", edited.to_str(), "concat 后再编辑")
    expect_equal("hello world", base.to_str(), "base 始终未被修改")


def sc_edge_boundaries():
    empty = lib.Rope.from_str("")
    expect_equal("", empty.to_str(), "空串 to_str")
    expect_equal(0, empty.length(), "空串 length")
    one = empty.insert(0, "a")
    expect_equal("a", one.to_str(), "空串插入")
    appended = one.insert(one.length(), "z")
    expect_equal("az", appended.to_str(), "末尾追加")

    out_of_range = [
        (lambda: one.char_at(-1), "char_at(-1)"),
        (lambda: one.char_at(1), "char_at(1)"),
        (lambda: one.delete(1, 1), "delete 越界"),
        (lambda: one.insert(2, "x"), "insert 越界"),
        (lambda: one.slice(0, 2), "slice 越界"),
    ]
    for call, label in out_of_range:
        try:
            call()
        except IndexError:
            continue
        raise AssertionError("%s 应抛 IndexError" % label)


SCENARIOS = [
    ("equivalence", "random-ops", "随机操作序列与朴素字符串逐字符等价", sc_eq_random_ops),
    ("equivalence", "slice-concat", "slice / concat 与朴素字符串等价", sc_eq_slice_concat),
    ("equivalence", "char-index", "按字符索引与切片", sc_eq_char_index),
    ("cost", "single-edit", "单次编辑访问计数 ≤ %d" % SINGLE_BOUND, sc_cost_single_edit),
    ("cost", "mass-insert", "1000 次前缀插入总计数 < %d" % MASS_BOUND, sc_cost_mass_insert),
    ("balance", "height-and-cache", "深度 ∈ [1, ceil(2·log2(n+1))] 且 length() 不计数", sc_balance_height_and_cache),
    ("persist", "immutable", "编辑返回新 Rope、不改原 Rope", sc_persist_immutable),
    ("edge", "boundaries", "空串 / 末尾追加 / 越界 IndexError", sc_edge_boundaries),
]


def main(argv):
    list_only = "-list" in argv or "--list" in argv
    only = None
    if "--only" in argv:
        idx = argv.index("--only")
        if idx + 1 >= len(argv):
            sys.stderr.write("--only 缺少取值\n")
            return 2
        only = argv[idx + 1]

    if list_only:
        for group, name, _expect, _run in SCENARIOS:
            sys.stdout.write("%s/%s\n" % (group, name))
        return 0

    passed = 0
    ran = 0
    for group, name, expect, run in SCENARIOS:
        if only is not None and group != only:
            continue
        ran += 1
        label = "%s/%s" % (group, name)
        try:
            run()
            passed += 1
            sys.stdout.write("PASS %s\n" % label)
        except Exception as exc:  # noqa: BLE001
            detail = "%s: %s" % (type(exc).__name__, exc)
            sys.stdout.write("FAIL %s  期望=%s 实际=%s\n" % (label, expect, show(detail)))

    if ran == 0:
        sys.stdout.write("结果：通过 0/0（没有匹配的场景：--only %s）\n" % only)
        return 1

    sys.stdout.write("结果：通过 %d/%d\n" % (passed, ran))
    return 0 if passed == ran else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))