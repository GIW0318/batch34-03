from bisect import bisect_right
from copy import deepcopy


class ReplayBuffer:
    def __init__(self, keyframe_interval=10):
        if (
            isinstance(keyframe_interval, bool)
            or not isinstance(keyframe_interval, int)
            or keyframe_interval < 1
        ):
            raise ValueError("keyframe_interval must be a positive integer")

        self.keyframe_interval = keyframe_interval
        self._frames = []
        self._keyframes = []
        self._last_state = None
        self._cache = {}
        self._hits = 0
        self._misses = 0

    def append(self, state):
        if not isinstance(state, dict):
            raise ValueError("state must be a dict")

        frame_index = len(self._frames)
        snapshot = deepcopy(state)

        if frame_index % self.keyframe_interval == 0:
            self._frames.append(("keyframe", snapshot))
            self._keyframes.append(frame_index)
        else:
            changes = {}
            for key, value in snapshot.items():
                if key not in self._last_state or self._last_state[key] != value:
                    changes[key] = value

            removed = set(self._last_state) - set(snapshot)
            self._frames.append(("delta", changes, removed))

        self._last_state = snapshot
        return frame_index

    def seek(self, index):
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index >= len(self._frames)
        ):
            raise IndexError("frame index out of range")

        if index in self._cache:
            self._hits += 1
            return deepcopy(self._cache[index])

        self._misses += 1
        keyframe_index = self._keyframes[bisect_right(self._keyframes, index) - 1]
        kind, *payload = self._frames[keyframe_index]
        if kind == "keyframe":
            state = deepcopy(payload[0])
        else:
            raise RuntimeError("invalid keyframe entry")

        for frame_index in range(keyframe_index + 1, index + 1):
            kind, *delta_payload = self._frames[frame_index]
            if kind != "delta":
                raise RuntimeError("invalid delta entry")

            changes, removed = delta_payload
            for key in removed:
                state.pop(key, None)
            for key, value in changes.items():
                state[key] = deepcopy(value)

        self._cache[index] = state
        return deepcopy(state)

    def cache_info(self):
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
        }

    def stats(self):
        return {
            "frames": len(self._frames),
            "keyframes": list(self._keyframes),
            "cache_entries": len(self._cache),
        }
