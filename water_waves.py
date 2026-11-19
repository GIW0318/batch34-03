import math

GRAVITY = 9.81


class GerstnerWave:
    def __init__(self, direction, amplitude, wavelength, steepness):
        if wavelength <= 0:
            raise ValueError("wavelength must be positive")
        if amplitude < 0:
            raise ValueError("amplitude must be non-negative")
        if not 0.0 <= steepness <= 1.0:
            raise ValueError("steepness must be within [0, 1]")
        dx, dz = direction
        length = math.hypot(dx, dz)
        if length == 0.0:
            raise ValueError("direction must be a non-zero vector")
        self.direction = (dx / length, dz / length)
        self.amplitude = amplitude
        self.wavelength = wavelength
        self.steepness = steepness
        self.wave_number = 2.0 * math.pi / wavelength
        self.angular_frequency = math.sqrt(GRAVITY * self.wave_number)

    def _phase(self, x, z, t):
        dx, dz = self.direction
        return self.wave_number * (dx * x + dz * z) - self.angular_frequency * t

    def _displacement(self, x, z, t):
        phase = self._phase(x, z, t)
        dx, dz = self.direction
        horizontal = self.steepness * self.amplitude * math.cos(phase)
        return (horizontal * dx, self.amplitude * math.sin(phase), horizontal * dz)

    def _derivatives(self, x, z, t):
        phase = self._phase(x, z, t)
        dx, dz = self.direction
        k = self.wave_number
        qa = self.steepness * self.amplitude
        sin_p = math.sin(phase)
        cos_p = math.cos(phase)
        d_x = (-qa * k * dx * dx * sin_p, self.amplitude * k * dx * cos_p,
               -qa * k * dx * dz * sin_p)
        d_z = (-qa * k * dx * dz * sin_p, self.amplitude * k * dz * cos_p,
               -qa * k * dz * dz * sin_p)
        return d_x, d_z

    def sample(self, x, z, t):
        ox, oy, oz = self._displacement(x, z, t)
        return (x + ox, oy, z + oz)

    def normal(self, x, z, t):
        d_x, d_z = self._derivatives(x, z, t)
        tangent_x = (1.0 + d_x[0], d_x[1], d_x[2])
        tangent_z = (d_z[0], d_z[1], 1.0 + d_z[2])
        return _up_normal(tangent_x, tangent_z)


class WaterSurface:
    def __init__(self, waves):
        self.waves = list(waves)

    def sample(self, x, z, t):
        px, py, pz = x, 0.0, z
        for wave in self.waves:
            ox, oy, oz = wave._displacement(x, z, t)
            px += ox
            py += oy
            pz += oz
        return (px, py, pz)

    def height(self, x, z, t):
        return self.sample(x, z, t)[1]

    def normal(self, x, z, t):
        tangent_x = [1.0, 0.0, 0.0]
        tangent_z = [0.0, 0.0, 1.0]
        for wave in self.waves:
            d_x, d_z = wave._derivatives(x, z, t)
            for i in range(3):
                tangent_x[i] += d_x[i]
                tangent_z[i] += d_z[i]
        return _up_normal(tuple(tangent_x), tuple(tangent_z))


def _up_normal(tangent_x, tangent_z):
    nx = tangent_z[1] * tangent_x[2] - tangent_z[2] * tangent_x[1]
    ny = tangent_z[2] * tangent_x[0] - tangent_z[0] * tangent_x[2]
    nz = tangent_z[0] * tangent_x[1] - tangent_z[1] * tangent_x[0]
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0.0:
        return (0.0, 1.0, 0.0)
    normal = (nx / length, ny / length, nz / length)
    if normal[1] < 0.0:
        normal = (-normal[0], -normal[1], -normal[2])
    return normal
