import math


class ClothSolver:
    def __init__(self, cols, rows, spacing=1.0, gravity=9.8, damping=0.99, rounds=3):
        if not isinstance(cols, int) or isinstance(cols, bool) or cols < 2:
            raise ValueError("cols must be an integer greater than or equal to 2")
        if not isinstance(rows, int) or isinstance(rows, bool) or rows < 2:
            raise ValueError("rows must be an integer greater than or equal to 2")
        if (
            not isinstance(spacing, (int, float))
            or isinstance(spacing, bool)
            or not math.isfinite(spacing)
            or spacing <= 0
        ):
            raise ValueError("spacing must be a positive finite number")
        if (
            not isinstance(damping, (int, float))
            or isinstance(damping, bool)
            or not 0 < damping <= 1
        ):
            raise ValueError("damping must be in the interval (0, 1]")
        if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 1:
            raise ValueError("rounds must be an integer greater than or equal to 1")

        self.cols = cols
        self.rows = rows
        self.spacing = float(spacing)
        self.gravity = float(gravity)
        self.damping = float(damping)
        self.rounds = rounds

        self._positions = [
            [col * self.spacing, -row * self.spacing]
            for row in range(rows)
            for col in range(cols)
        ]
        self._previous = [position[:] for position in self._positions]
        self._pinned = [False] * (cols * rows)

        self._horizontal_edges = [
            (row * cols + col, row * cols + col + 1)
            for row in range(rows)
            for col in range(cols - 1)
        ]
        self._vertical_edges = [
            (row * cols + col, (row + 1) * cols + col)
            for row in range(rows - 1)
            for col in range(cols)
        ]

    def pin(self, col, row):
        if (
            not isinstance(col, int)
            or isinstance(col, bool)
            or not isinstance(row, int)
            or isinstance(row, bool)
            or not 0 <= col < self.cols
            or not 0 <= row < self.rows
        ):
            raise ValueError("pinned point is outside the cloth grid")
        self._pinned[row * self.cols + col] = True

    def advance(self, dt):
        if (
            not isinstance(dt, (int, float))
            or isinstance(dt, bool)
            or not math.isfinite(dt)
            or dt <= 0
        ):
            raise ValueError("dt must be a positive finite number")
        dt = float(dt)

        gravity_step = self.gravity * dt * dt
        for index, position in enumerate(self._positions):
            if self._pinned[index]:
                continue

            previous = self._previous[index]
            velocity_x = (position[0] - previous[0]) * self.damping
            velocity_y = (position[1] - previous[1]) * self.damping

            self._previous[index] = [position[0], position[1]]
            self._positions[index] = [
                position[0] + velocity_x,
                position[1] + velocity_y - gravity_step,
            ]

        for _ in range(self.rounds):
            for first, second in self._horizontal_edges:
                self._solve_edge(first, second)
            for first, second in self._vertical_edges:
                self._solve_edge(first, second)

    def _solve_edge(self, first, second):
        first_pinned = self._pinned[first]
        second_pinned = self._pinned[second]
        if first_pinned and second_pinned:
            return

        first_position = self._positions[first]
        second_position = self._positions[second]
        delta_x = second_position[0] - first_position[0]
        delta_y = second_position[1] - first_position[1]
        distance_squared = delta_x * delta_x + delta_y * delta_y
        if distance_squared == 0:
            return

        distance = math.sqrt(distance_squared)
        correction = (distance - self.spacing) / distance

        if first_pinned:
            second_position[0] -= delta_x * correction
            second_position[1] -= delta_y * correction
        elif second_pinned:
            first_position[0] += delta_x * correction
            first_position[1] += delta_y * correction
        else:
            half_x = delta_x * correction * 0.5
            half_y = delta_y * correction * 0.5
            first_position[0] += half_x
            first_position[1] += half_y
            second_position[0] -= half_x
            second_position[1] -= half_y

    def positions(self):
        return [position[:] for position in self._positions]

    def max_stretch(self):
        maximum = 0.0
        for first, second in self._horizontal_edges + self._vertical_edges:
            first_position = self._positions[first]
            second_position = self._positions[second]
            distance = math.hypot(
                second_position[0] - first_position[0],
                second_position[1] - first_position[1],
            )
            maximum = max(maximum, abs(distance - self.spacing) / self.spacing)
        return maximum
