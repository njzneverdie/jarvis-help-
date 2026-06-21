"""
One-Euro Filter — 低速高平滑、高速低延遲，適合手部追蹤。
參考：https://cristal.univ-lille.fr/~casiez/1euro/
"""

import math
import time


class _LowPassFilter:
    def __init__(self):
        self._y = None
        self._dy = 0.0

    def filter(self, x: float, alpha: float) -> float:
        if self._y is None:
            self._y = x
        result = alpha * x + (1.0 - alpha) * self._y
        self._dy = result - self._y
        self._y = result
        return result

    @property
    def dy(self) -> float:
        return self._dy


class OneEuroFilter:
    """
    params:
        min_cutoff  — 最小截止頻率（越小越平滑，預設 1.0 Hz）
        beta        — 速度係數（越大高速越靈敏，預設 0.007）
        d_cutoff    — 速度低通截止（通常固定 1.0 Hz）
    """

    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_filter = _LowPassFilter()
        self._dx_filter = _LowPassFilter()
        self._last_t = None

    def _alpha(self, cutoff: float, dt: float) -> float:
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, x: float, timestamp: float | None = None) -> float:
        now = timestamp if timestamp is not None else time.monotonic()
        dt = (now - self._last_t) if self._last_t is not None else 1e-3
        dt = max(dt, 1e-6)
        self._last_t = now

        # 速度估計
        dx = (x - (self._x_filter._y or x)) / dt
        edx = self._dx_filter.filter(dx, self._alpha(self._d_cutoff, dt))

        # 自適應截止頻率
        cutoff = self._min_cutoff + self._beta * abs(edx)
        return self._x_filter.filter(x, self._alpha(cutoff, dt))


class SmoothXY:
    """對 (x, y) 各自套 One-Euro Filter。"""

    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007):
        self._fx = OneEuroFilter(min_cutoff, beta)
        self._fy = OneEuroFilter(min_cutoff, beta)

    def filter(self, x: float, y: float) -> tuple[float, float]:
        t = time.monotonic()
        return self._fx.filter(x, t), self._fy.filter(y, t)
