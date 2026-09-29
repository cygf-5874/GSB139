"""节点访问计数（固定入口，勿改）。

`Rope` 的每次编辑按**访问到的节点数**调用 :meth:`Counter.bump`；固定件只看这个
计数，不看墙钟。调用方（或固定件）可用 :meth:`Counter.reset` 复位后再测量。
"""


class Counter:
    """全局节点访问计数器（可注入 / 可复位）。"""

    visits = 0

    @classmethod
    def reset(cls):
        """把计数复位为 0。"""
        cls.visits = 0

    @classmethod
    def bump(cls, n=1):
        """累加 `n` 次节点访问。"""
        cls.visits += n