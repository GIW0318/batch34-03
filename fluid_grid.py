import math


class FluidGrid:
    """A small grid-based smoke solver.

    Density and velocity components are stored at integer grid points.
    Simulation uses implicit diffusion followed by semi-Lagrangian advection.
    """

    def __init__(self, width, height, diffusion=0.0, viscosity=0.0, iterations=10):
        self.width = self._positive_integer(width, "width")
        self.height = self._positive_integer(height, "height")
        self.diffusion = self._non_negative_float(diffusion, "diffusion")
        self.viscosity = self._non_negative_float(viscosity, "viscosity")
        self.iterations = self._positive_integer(iterations, "iterations")

        size = self.width * self.height
        self._density = [0.0] * size
        self._vx = [0.0] * size
        self._vy = [0.0] * size

    @staticmethod
    def _positive_integer(value, name):
        try:
            result = int(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"{name} must be a positive integer") from None
        if result != value or result <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return result

    @staticmethod
    def _non_negative_float(value, name):
        try:
            result = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"{name} must be a finite non-negative number") from None
        if not math.isfinite(result) or result < 0.0:
            raise ValueError(f"{name} must be a finite non-negative number")
        return result

    @staticmethod
    def _finite_float(value, name):
        try:
            result = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"{name} must be finite") from None
        if not math.isfinite(result):
            raise ValueError(f"{name} must be finite")
        return result

    def _index(self, x, y):
        try:
            ix = int(x)
            iy = int(y)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("grid coordinates must be integers") from None
        if ix != x or iy != y:
            raise ValueError("grid coordinates must be integers")
        if not (0 <= ix < self.width and 0 <= iy < self.height):
            raise ValueError("grid coordinate out of range")
        return iy * self.width + ix

    def add_density(self, x, y, amount):
        index = self._index(x, y)
        amount = self._finite_float(amount, "density amount")
        self._density[index] = max(0.0, self._density[index] + amount)

    def add_velocity(self, x, y, vx, vy):
        index = self._index(x, y)
        vx = self._finite_float(vx, "vx")
        vy = self._finite_float(vy, "vy")
        self._vx[index] += vx
        self._vy[index] += vy

    def density_at(self, x, y):
        return float(self._density[self._index(x, y)])

    def velocity_at(self, x, y):
        index = self._index(x, y)
        return (float(self._vx[index]), float(self._vy[index]))

    def step(self, dt):
        dt = self._finite_float(dt, "dt")
        if dt <= 0.0:
            raise ValueError("dt must be a positive number")

        if self.diffusion > 0.0:
            self._density = self._diffuse(
                self._density, self.diffusion * dt, preserve_total=True
            )

        if self.viscosity > 0.0:
            self._vx = self._diffuse(self._vx, self.viscosity * dt)
            self._vy = self._diffuse(self._vy, self.viscosity * dt)

        self._vx, self._vy = self._advect_velocity(dt)
        self._density = self._advect_density(dt)

    def _neighbour_average(self, field, x, y):
        width = self.width
        height = self.height
        left = field[y * width + max(x - 1, 0)]
        right = field[y * width + min(x + 1, width - 1)]
        above = field[max(y - 1, 0) * width + x]
        below = field[min(y + 1, height - 1) * width + x]
        return 0.25 * left + 0.25 * right + 0.25 * above + 0.25 * below

    def _diffuse(self, field, coefficient, preserve_total=False):
        """Apply stable implicit diffusion without changing the field total."""
        if coefficient <= 0.0:
            return list(field)

        if not math.isfinite(coefficient):
            self_weight = 0.0
        elif coefficient <= 1.0:
            self_weight = 1.0 / (1.0 + 4.0 * coefficient)
        else:
            inverse = 1.0 / coefficient
            self_weight = inverse / (4.0 + inverse)

        source = list(field)
        result = list(field)
        for _ in range(self.iterations):
            for y in range(self.height):
                row = y * self.width
                for x in range(self.width):
                    index = row + x
                    average = self._neighbour_average(result, x, y)
                    result[index] = (
                        self_weight * source[index]
                        + (1.0 - self_weight) * average
                    )

        if preserve_total:
            before = math.fsum(source)
            after = math.fsum(result)
            if before > 0.0 and after > 0.0 and math.isfinite(before / after):
                scale = before / after
                result = [value * scale for value in result]

        return [max(0.0, value) for value in result] if preserve_total else result

    def _sample(self, field, x, y):
        """Bilinearly sample a scalar field, clamping coordinates to its edge."""
        x = min(max(x, 0.0), float(self.width - 1))
        y = min(max(y, 0.0), float(self.height - 1))

        x0 = int(math.floor(x))
        y0 = int(math.floor(y))
        x1 = min(x0 + 1, self.width - 1)
        y1 = min(y0 + 1, self.height - 1)
        tx = x - x0
        ty = y - y0

        row0 = y0 * self.width
        row1 = y1 * self.width
        return (
            (1.0 - tx) * (1.0 - ty) * field[row0 + x0]
            + tx * (1.0 - ty) * field[row0 + x1]
            + (1.0 - tx) * ty * field[row1 + x0]
            + tx * ty * field[row1 + x1]
        )

    def _advect_velocity(self, dt):
        new_vx = [0.0] * len(self._vx)
        new_vy = [0.0] * len(self._vy)
        for y in range(self.height):
            row = y * self.width
            for x in range(self.width):
                index = row + x
                sample_x = x - dt * self._vx[index]
                sample_y = y - dt * self._vy[index]
                new_vx[index] = self._sample(self._vx, sample_x, sample_y)
                new_vy[index] = self._sample(self._vy, sample_x, sample_y)
        return new_vx, new_vy

    def _advect_density(self, dt):
        result = [0.0] * len(self._density)
        for y in range(self.height):
            row = y * self.width
            for x in range(self.width):
                index = row + x
                sample_x = x - dt * self._vx[index]
                sample_y = y - dt * self._vy[index]
                result[index] = max(
                    0.0, self._sample(self._density, sample_x, sample_y)
                )
        return result
