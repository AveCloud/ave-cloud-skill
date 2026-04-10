"""Kline formatting, sparklines, number/USD display, and label utilities."""

import math
from collections import deque


def interval_label(interval: str) -> str:
    if interval == "s1":
        return "1s"
    if interval.startswith("k"):
        minutes = int(interval[1:])
        if minutes == 1440:
            return "1d"
        if minutes == 10080:
            return "1w"
        if minutes % 60 == 0:
            return f"{minutes // 60}h"
        return f"{minutes}m"
    return interval


def short_label(value) -> str:
    if not isinstance(value, str):
        return str(value)
    if len(value) <= 18:
        return value
    return f"{value[:8]}...{value[-6:]}"


def format_small_number(value) -> str:
    if value is None:
        return "n/a"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == 0:
        return "0"
    abs_number = abs(number)
    if abs_number >= 1:
        return f"{number:,.6f}".rstrip("0").rstrip(".")
    if abs_number >= 0.001:
        return f"{number:.8f}".rstrip("0").rstrip(".")
    raw = f"{abs_number:.12f}".split(".")[1]
    zero_count = 0
    for ch in raw:
        if ch == "0":
            zero_count += 1
        else:
            break
    significant = raw[zero_count:zero_count + 4] or "0"
    prefix = "-" if number < 0 else ""
    return f"{prefix}0.0{{{zero_count}}}{significant}"


def format_usd(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    abs_number = abs(number)
    if abs_number >= 1_000_000_000:
        return f"${number / 1_000_000_000:.2f}B"
    if abs_number >= 1_000_000:
        return f"${number / 1_000_000:.2f}M"
    if abs_number >= 1_000:
        return f"${number / 1_000:.2f}K"
    return f"${number:.2f}"


def sparkline_rows(values: list, rows: int = 5, width: int = 20) -> list[str]:
    clean = [float(v) for v in values if v is not None and _is_numeric(v)]
    if not clean:
        return []
    if len(clean) > width:
        clean = clean[-width:]
    low, high = min(clean), max(clean)
    if math.isclose(high, low):
        return [f"{format_small_number(high):>12} | {'---' * len(clean)}"]
    levels = [high - (high - low) * idx / (rows - 1) for idx in range(rows)]
    return [
        f"{format_small_number(level):>12} | {''.join(chr(9608) if v >= level else ' ' for v in clean).rstrip()}"
        for level in levels
    ]


def _is_numeric(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


class KlineFormatter:
    def __init__(self, history: int = 20) -> None:
        self.closes: deque = deque(maxlen=history)

    def render(self, event: dict) -> str:
        close = event.get("close")
        self.closes.append(close)
        o, h, l, vol = event.get("open"), event.get("high"), event.get("low"), event.get("volume")
        pair = event.get("pair", "pair")
        chain = event.get("chain", "?")
        pair_label = event.get("pair_label") or short_label(pair)
        iv = interval_label(event.get("interval", "?"))
        pct = None
        try:
            of, cf = float(o), float(close)
            if of:
                pct = (cf - of) / of * 100
        except (TypeError, ValueError, ZeroDivisionError):
            pass
        direction = "flat" if pct is None else ("up candle" if pct > 0 else "down candle" if pct < 0 else "flat")
        lines = [
            f"[{chain}] {pair_label} {iv}",
            f"O: {format_small_number(o)}  H: {format_small_number(h)}  L: {format_small_number(l)}  C: {format_small_number(close)}",
        ]
        if pct is not None:
            lines.append(f"Move: {pct:+.2f}%   Vol: {format_usd(vol)}   Trend: {direction}")
        else:
            lines.append(f"Vol: {format_usd(vol)}   Trend: {direction}")
        lines.append("")
        lines.extend(sparkline_rows(self.closes))
        return "\n".join(lines)
