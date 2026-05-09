from __future__ import annotations


def test_rolling_window_keeps_max_length_and_ready_state() -> None:
    from qts.indicators.rolling import RollingWindow

    window = RollingWindow[int](size=3)

    assert not window.ready
    window.append(1)
    window.append(2)
    assert tuple(window) == (1, 2)
    assert not window.ready
    window.append(3)
    assert window.ready
    window.append(4)

    assert tuple(window) == (2, 3, 4)
    assert window.snapshot() == (2, 3, 4)


def test_rolling_window_restore_preserves_values() -> None:
    from qts.indicators.rolling import RollingWindow

    window = RollingWindow[int](size=3)
    restored = window.restore((5, 6))

    assert tuple(restored) == (5, 6)
    assert not restored.ready
