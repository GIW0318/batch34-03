import copy
import math
import random


class HydraulicErosion:
    # Fixed direction order so that equal-height neighbours are picked
    # deterministically regardless of the random seed / insertion order.
    _DIRECTIONS = ((0, -1), (1, 0), (0, 1), (-1, 0))

    def __init__(self, heightmap, erosion_rate=0.3, settle_rate=0.3,
                 carry_factor=4.0, evaporation=0.01):
        self._heightmap = self._validate_heightmap(heightmap)
        self._rows = len(self._heightmap)
        self._cols = len(self._heightmap[0])

        self._erosion_rate = self._validate_fraction(erosion_rate, "erosion_rate")
        self._settle_rate = self._validate_fraction(settle_rate, "settle_rate")
        if not self._is_number(carry_factor) or not math.isfinite(carry_factor) or carry_factor <= 0:
            raise ValueError("carry_factor must be a finite positive number")
        if (not self._is_number(evaporation) or not math.isfinite(evaporation)
                or evaporation < 0.0 or evaporation >= 1.0):
            raise ValueError("evaporation must be a finite number in [0, 1)")
        self._carry_factor = float(carry_factor)
        self._evaporation = float(evaporation)

        self._sediment_total = 0.0

    @staticmethod
    def _is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @classmethod
    def _validate_fraction(cls, value, name):
        if not cls._is_number(value) or not math.isfinite(value) or not (0.0 <= float(value) <= 1.0):
            raise ValueError(f"{name} must be a finite number in [0, 1]")
        return float(value)

    def _validate_heightmap(self, heightmap):
        if not isinstance(heightmap, (list, tuple)) or len(heightmap) == 0:
            raise ValueError("heightmap must be a non-empty 2D array")
        if not isinstance(heightmap[0], (list, tuple)) or len(heightmap[0]) == 0:
            raise ValueError("heightmap rows must be non-empty arrays")
        width = len(heightmap[0])
        validated = []
        for row in heightmap:
            if not isinstance(row, (list, tuple)) or len(row) != width:
                raise ValueError("heightmap must be rectangular (all rows the same length)")
            new_row = []
            for value in row:
                if not self._is_number(value) or not math.isfinite(value) or value < 0:
                    raise ValueError("heightmap values must be finite non-negative numbers")
                new_row.append(float(value))
            validated.append(new_row)
        return validated

    def _validate_start(self, start):
        if not isinstance(start, (list, tuple)) or len(start) != 2:
            raise ValueError("start must be a pair of (x, y) coordinates")
        x, y = start
        # bool is an int subclass but never a valid coordinate here
        if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("start coordinates must be integers")
        if not (0 <= x < self._cols and 0 <= y < self._rows):
            raise ValueError("start position is outside the heightmap")
        return x, y

    def erode(self, droplets=100, max_steps=30, seed=0, start=None):
        if isinstance(droplets, bool) or not isinstance(droplets, int) or droplets < 0:
            raise ValueError("droplets must be a non-negative integer")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError("max_steps must be a positive integer")
        fixed_start = self._validate_start(start) if start is not None else None

        rng = random.Random(seed)
        for _ in range(droplets):
            if fixed_start is not None:
                x, y = fixed_start
            else:
                x = rng.randrange(self._cols)
                y = rng.randrange(self._rows)
            self._simulate_droplet(x, y, max_steps)

        return {
            "droplets": droplets,
            "seed": seed,
            "moved": self._sediment_total,
        }

    def _simulate_droplet(self, x, y, max_steps):
        heightmap = self._heightmap
        water = 1.0
        sediment = 0.0

        for _ in range(max_steps):
            current_height = heightmap[y][x]

            # Pick the lowest in-map neighbour from the four cardinal cells.
            next_x = next_y = None
            lowest = current_height
            for dx, dy in self._DIRECTIONS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self._cols and 0 <= ny < self._rows:
                    neighbour_height = heightmap[ny][nx]
                    if neighbour_height < lowest:
                        lowest = neighbour_height
                        next_x, next_y = nx, ny

            # Local minimum (or no in-map neighbour): settle and stop.
            if next_x is None:
                break

            drop = current_height - lowest
            capacity = self._carry_factor * drop * water

            if sediment < capacity:
                # Erode the current cell, never below zero.
                amount = self._erosion_rate * (capacity - sediment)
                amount = min(amount, current_height)
                heightmap[y][x] = current_height - amount
                sediment += amount
                self._sediment_total += amount
            elif sediment > capacity:
                # Deposit the surplus onto the current cell.
                amount = self._settle_rate * (sediment - capacity)
                amount = min(amount, sediment)
                heightmap[y][x] += amount
                sediment -= amount
                self._sediment_total += amount

            x, y = next_x, next_y
            # Multiplicative evaporation keeps water positive while
            # evaporation < 1; evaporation == 1 is rejected up front.
            water *= 1.0 - self._evaporation
        else:
            # Step budget exhausted with sediment still carried.
            heightmap[y][x] += sediment
            self._sediment_total += sediment
            return

        # Stopped at a local minimum: dump every remaining grain here, so
        # material is never carried off the map and total height is conserved.
        if sediment > 0.0:
            heightmap[y][x] += sediment
            self._sediment_total += sediment

    def heights(self):
        return copy.deepcopy(self._heightmap)

    def sediment_total(self):
        return self._sediment_total
