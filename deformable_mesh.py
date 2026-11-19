import math
import operator


class MassSpringMesh:
    def __init__(self, positions, springs, masses=None, velocities=None,
                 stiffness=1.0, damping=0.0, pinned=()):
        try:
            initial_positions = [
                tuple(float(coordinate) for coordinate in position)
                for position in positions
            ]
        except (TypeError, ValueError) as exc:
            raise ValueError("positions must contain numeric vectors") from exc

        self._dimension = len(initial_positions[0]) if initial_positions else 0
        if any(len(position) != self._dimension
               for position in initial_positions):
            raise ValueError("all positions must have the same dimension")

        self._initial_positions = initial_positions
        self._positions = list(initial_positions)
        vertex_count = len(self._positions)

        self._masses = self._normalize_masses(masses, vertex_count)

        if velocities is None:
            initial_velocities = [
                (0.0,) * self._dimension for _ in range(vertex_count)
            ]
        else:
            try:
                initial_velocities = [
                    tuple(float(coordinate) for coordinate in velocity)
                    for velocity in velocities
                ]
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "velocities must contain numeric vectors"
                ) from exc
            if len(initial_velocities) != vertex_count:
                raise ValueError(
                    "velocities must have one entry per vertex"
                )
            if any(len(velocity) != self._dimension
                   for velocity in initial_velocities):
                raise ValueError(
                    "velocities must have the same dimension as positions"
                )

        self._initial_velocities = initial_velocities
        self._velocities = list(initial_velocities)

        try:
            self._stiffness = float(stiffness)
            self._damping = float(damping)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "stiffness and damping must be numeric"
            ) from exc
        if not math.isfinite(self._stiffness):
            raise ValueError("stiffness must be finite")
        if not 0.0 <= self._damping < 1.0:
            raise ValueError("damping must be in the range [0, 1)")

        self._springs = self._normalize_springs(springs, vertex_count)
        self._pinned = self._normalize_pinned(pinned, vertex_count)

    @staticmethod
    def _normalize_masses(masses, vertex_count):
        if masses is None:
            return [1.0] * vertex_count

        try:
            normalized = [float(mass) for mass in masses]
        except (TypeError, ValueError) as exc:
            raise ValueError("masses must contain numeric values") from exc

        if len(normalized) != vertex_count:
            raise ValueError("masses must have one entry per vertex")
        if any(not math.isfinite(mass) or mass <= 0.0
               for mass in normalized):
            raise ValueError("masses must be positive and finite")
        return normalized

    @staticmethod
    def _as_index(value, vertex_count, description):
        if isinstance(value, bool):
            raise ValueError(f"{description} must be an integer")
        try:
            index = operator.index(value)
        except TypeError as exc:
            raise ValueError(f"{description} must be an integer") from exc
        if not 0 <= index < vertex_count:
            raise ValueError(f"{description} is out of range")
        return index

    def _normalize_springs(self, springs, vertex_count):
        normalized = []
        seen_edges = set()

        try:
            spring_list = list(springs)
        except TypeError as exc:
            raise ValueError("springs must be an iterable") from exc

        for spring in spring_list:
            try:
                values = list(spring)
            except TypeError as exc:
                raise ValueError(
                    "each spring must contain two indices and an optional "
                    "rest length"
                ) from exc
            if len(values) not in (2, 3):
                raise ValueError(
                    "each spring must contain two indices and an optional "
                    "rest length"
                )

            first = self._as_index(values[0], vertex_count, "spring index")
            second = self._as_index(values[1], vertex_count, "spring index")
            if first == second:
                raise ValueError("a spring cannot connect a vertex to itself")

            edge = (min(first, second), max(first, second))
            if edge in seen_edges:
                raise ValueError("duplicate springs are not allowed")
            seen_edges.add(edge)

            if len(values) == 3:
                try:
                    rest_length = float(values[2])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "spring rest length must be numeric"
                    ) from exc
            else:
                start = self._positions[first]
                end = self._positions[second]
                rest_length = math.sqrt(sum(
                    (end[axis] - start[axis]) ** 2
                    for axis in range(self._dimension)
                ))

            if not math.isfinite(rest_length) or rest_length <= 0.0:
                raise ValueError(
                    "spring rest length must be positive and finite"
                )
            normalized.append((first, second, rest_length))

        return normalized

    @staticmethod
    def _normalize_pinned(pinned, vertex_count):
        if pinned is None:
            pinned = ()
        elif isinstance(pinned, (str, bytes)):
            raise ValueError("pinned must contain integer indices")
        else:
            try:
                iter(pinned)
            except TypeError:
                pinned = (pinned,)

        return {
            MassSpringMesh._as_index(index, vertex_count, "pinned index")
            for index in pinned
        }

    def step(self, dt, gravity=(0.0, 0.0)):
        try:
            dt = float(dt)
        except (TypeError, ValueError) as exc:
            raise ValueError("dt must be a positive number") from exc
        if not math.isfinite(dt) or dt <= 0.0:
            raise ValueError("dt must be a positive finite number")

        try:
            gravity_vector = tuple(float(value) for value in gravity)
        except (TypeError, ValueError) as exc:
            raise ValueError("gravity must be a numeric vector") from exc
        if len(gravity_vector) != self._dimension:
            raise ValueError(
                "gravity must have the same dimension as positions"
            )
        if not all(math.isfinite(value) for value in gravity_vector):
            raise ValueError("gravity must contain finite values")

        vertex_count = len(self._positions)
        forces = [[0.0] * self._dimension for _ in range(vertex_count)]

        for first, second, rest_length in self._springs:
            start = self._positions[first]
            end = self._positions[second]
            delta = [
                end[axis] - start[axis] for axis in range(self._dimension)
            ]
            length_squared = sum(value * value for value in delta)
            if length_squared == 0.0:
                continue

            length = math.sqrt(length_squared)
            magnitude = (
                self._stiffness * (length - rest_length) / length
            )
            for axis in range(self._dimension):
                force = magnitude * delta[axis]
                forces[first][axis] += force
                forces[second][axis] -= force

        damping_factor = 1.0 - self._damping
        new_positions = []
        new_velocities = []
        for index in range(vertex_count):
            if index in self._pinned:
                new_positions.append(self._initial_positions[index])
                new_velocities.append(self._initial_velocities[index])
                continue

            mass = self._masses[index]
            velocity = []
            for axis in range(self._dimension):
                acceleration = (
                    forces[index][axis] / mass + gravity_vector[axis]
                )
                component = (
                    self._velocities[index][axis] + acceleration * dt
                ) * damping_factor
                velocity.append(component)

            position = tuple(
                self._positions[index][axis] + velocity[axis] * dt
                for axis in range(self._dimension)
            )
            new_positions.append(position)
            new_velocities.append(tuple(velocity))

        self._positions = new_positions
        self._velocities = new_velocities

    def positions(self):
        return list(self._positions)

    def velocities(self):
        return list(self._velocities)

    def state(self):
        return {
            "positions": self.positions(),
            "velocities": self.velocities(),
            "springs": list(self._springs),
            "masses": list(self._masses),
            "stiffness": self._stiffness,
            "damping": self._damping,
            "pinned": sorted(self._pinned),
        }
