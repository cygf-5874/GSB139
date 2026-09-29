# ropebuf

Python 3 的 **Rope 文本缓冲**库：把大文本上的插入 / 删除 / 切片从「整串重建」换成「按树组织、按路径复制」。

- 语言 / 依赖：Python 3（标准库，`unittest`），**无第三方依赖**。
- 入口：`src/ropebuf.py`（库代码）；节点访问计数固定入口 `src/counter.py`（**勿改**）。
- 自检：`bash scripts/check.sh`（`check/` 是固定验收程序，**勿改**）。
- 既有用例：`python tests/run.py`（unittest，当前全绿）。

## 用法

```bash
python tests/run.py
bash scripts/check.sh                 # 加 -list / --only <组名> 可过滤
```

对外接口（`src/ropebuf.py`，签名已定死）：

- `Rope(text="")`、`Rope.from_str(text) -> Rope`：构造。
- `length() -> int`、`to_str() -> str`、`char_at(index) -> str`。
- `insert(index, text) -> Rope`、`delete(index, count) -> Rope`、`slice(start, end) -> Rope`、`concat(other) -> Rope`。
- `depth() -> int`：当前树的深度。

节点访问计数：`src/counter.py` 的 `Counter`（`Counter.reset()` 复位、`Counter.bump(n)` 累加、`Counter.visits` 读取）。
实现应在每次编辑里按**访问到的节点数**调用 `Counter.bump(...)`；判据只看这个计数，**不看墙钟**。

## 对外契约

1. **等价性**：`insert` / `delete` / `slice` / `char_at` / `length` / `to_str` 与等价的朴素字符串操作**逐字符等价**。
2. **单次编辑代价**：对长度 `n = 100000` 的 Rope 做一次 `insert` / `delete`，`Counter.visits` 增量 ≤ `4000`。
3. **规模判据**：在长度 `100000` 的 Rope 上连续做 `1000` 次**前缀插入**，`Counter.visits` 总量必须 `< 2000000`。
4. **树高约束**：`depth()` 返回树的深度，对长度 `n ≥ 2` 满足 `1 ≤ depth() ≤ ceil(2·log2(n+1))`（树保持平衡）。
5. **长度缓存**：`length()` 读缓存、`O(1)`；重复调用 `length()` **不得**增加 `Counter.visits`（不得整树重算）。
6. **持久化**：`insert` / `delete` / `slice` / `concat` 返回**新** Rope，**不修改**原 Rope；结果与原 Rope 共享子树。
7. **按字符索引**：`char_at` / `slice` / `insert` / `delete` 的下标都按 `str` 的**字符**计，不按字节。
8. **边界**：空串合法；`insert(length, s)` 是末尾追加；`char_at` / `delete` / `slice` / `insert` 越界抛 `IndexError`。
9. **确定性**：同一操作序列产出的字符串逐字符相同；不依赖墙钟、随机源、容器迭代顺序。

## 本次重构的目标

`src/ropebuf.py` 现在的实现语义正确，但每次编辑都重建整串（访问计数随长度线性增长）。
请在**不改变对外语义**的前提下，把它重构成按树组织、按路径复制的实现，使第 2~6 条成立。

## 目录

```
src/ropebuf.py      库代码（本次要重构）
src/counter.py      节点访问计数（已给全，勿改）
tests/run.py        既有用例（unittest，当前全绿）
check/check.py      固定验收程序（8 个场景，勿改）
scripts/check.sh    自检入口
```