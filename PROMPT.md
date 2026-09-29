大文本上的插入删除开销与长度成正比。ropebuf 是 Python 3 的 Rope 文本缓冲库（仅标准库，unittest），自检走 `scripts/check.sh`（`check/` 是固定验收程序，别改），既有用例走 `python tests/run.py`。

`src/ropebuf.py` 现在的实现语义是对的，但每次编辑都重建整串；判据不看墙钟，只看 `src/counter.py` 里那个 `Counter` 的节点访问计数。

任务：把它重构成按树组织、按路径复制的实现，满足 README「对外契约」的全部 9 条；既有用例要继续全绿。

验收：
- python -m py_compile src/ropebuf.py 退出码 0；
- python tests/run.py 全绿；
- bash scripts/check.sh 退出码 0，8 个场景全过（equivalence 3 + cost 2 + balance 1 + persist 1 + edge 1）。

约束：
1. 不改 `check/`、不改 `src/counter.py`；可以新增模块。
2. 对外方法名与签名已定死，不要改；`tests/run.py` 里的用例一条都不许删或改。
3. 只许用 Python 标准库，不许引入任何第三方依赖。
4. 不许依赖墙钟、随机源或容器迭代顺序。