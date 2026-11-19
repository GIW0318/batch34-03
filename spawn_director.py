import random


class SpawnDirector:
    def __init__(self, seed):
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError("seed must be an integer")
        self._seed = seed

    def plan_wave(self, wave_id, entries, budget, count, duration):
        if budget < 0:
            raise ValueError("budget must not be negative")
        if not entries:
            raise ValueError("entries must not be empty")
        for entry in entries:
            if entry["cost"] <= 0:
                raise ValueError("entry cost must be positive")
            if entry["weight"] <= 0:
                raise ValueError("entry weight must be positive")
        if count <= 0:
            raise ValueError("count must be positive")
        if duration <= 0:
            raise ValueError("duration must be positive")

        rng = random.Random(f"{self._seed}:{wave_id}")
        remaining = budget
        spawns = []

        for slot in range(count):
            affordable = [e for e in entries if e["cost"] <= remaining]
            if not affordable:
                break
            chosen = rng.choices(
                affordable, weights=[e["weight"] for e in affordable], k=1
            )[0]
            remaining -= chosen["cost"]
            spawns.append(
                {
                    "type": chosen["type"],
                    "cost": chosen["cost"],
                    "at": slot * duration / count,
                }
            )

        spent = budget - remaining
        return {
            "wave": wave_id,
            "spawns": spawns,
            "spent": spent,
            "remaining": remaining,
            "finished": True,
        }
