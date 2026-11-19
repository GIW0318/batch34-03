import bisect
import math


def _validate_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a real number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


class FramePacer:
    def __init__(self, fps=60):
        _validate_number(fps, "fps")
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.fps = fps
        self._frames = []
        self._position = -1
        self._last_pts = None
        self._last_now = None
        self._presented = 0
        self._duplicated = 0
        self._dropped = 0

    def submit(self, pts):
        _validate_number(pts, "pts")
        if pts < 0:
            raise ValueError("pts must be non-negative")
        if self._last_pts is not None and pts <= self._last_pts:
            raise ValueError("pts must be strictly increasing")
        self._frames.append(pts)
        self._last_pts = pts

    def present(self, now):
        _validate_number(now, "now")
        if now < 0:
            raise ValueError("now must be non-negative")

        if self._last_now is not None and now == self._last_now:
            return self._duplicate_or_idle()
        self._last_now = now

        target = bisect.bisect_right(self._frames, now) - 1
        if target < 0:
            return {"action": "idle"}
        if target <= self._position:
            return self._duplicate_or_idle()

        dropped = list(range(self._position + 1, target))
        self._position = target
        self._presented += 1
        self._dropped += len(dropped)
        return {
            "action": "show",
            "index": target,
            "pts": self._frames[target],
            "dropped": dropped,
        }

    def _duplicate_or_idle(self):
        if self._position < 0:
            return {"action": "idle"}
        self._duplicated += 1
        return {
            "action": "duplicate",
            "index": self._position,
            "pts": self._frames[self._position],
            "dropped": [],
        }

    def stats(self):
        return {
            "presented": self._presented,
            "duplicated": self._duplicated,
            "dropped": self._dropped,
        }

    def reset(self):
        self._frames = []
        self._position = -1
        self._last_pts = None
        self._last_now = None
        self._presented = 0
        self._duplicated = 0
        self._dropped = 0

    def state(self):
        return {
            "fps": self.fps,
            "frames": list(self._frames),
            "position": self._position,
            "presented": self._presented,
            "duplicated": self._duplicated,
            "dropped": self._dropped,
        }
