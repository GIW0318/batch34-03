import math

import pytest

import water_waves as ww

G = 9.81


def wave(direction=(1.0, 0.0), amplitude=1.0, wavelength=8.0, steepness=0.5):
    return ww.GerstnerWave(direction, amplitude, wavelength, steepness)


def test_zero_amplitude_keeps_position():
    p = wave(amplitude=0.0).sample(3.0, 4.0, 1.7)
    assert p == pytest.approx((3.0, 0.0, 4.0))


def test_zero_amplitude_normal_points_up():
    n = wave(amplitude=0.0).normal(3.0, 4.0, 1.7)
    assert n == pytest.approx((0.0, 1.0, 0.0))


def test_crest_height_equals_amplitude():
    p = wave(amplitude=2.0, wavelength=8.0).sample(2.0, 0.0, 0.0)
    assert p[1] == pytest.approx(2.0)


def test_trough_height_is_negative_amplitude():
    p = wave(amplitude=2.0, wavelength=8.0).sample(6.0, 0.0, 0.0)
    assert p[1] == pytest.approx(-2.0)


def test_zero_crossing_has_horizontal_offset():
    p = wave(amplitude=2.0, steepness=0.5).sample(0.0, 0.0, 0.0)
    assert p[1] == pytest.approx(0.0)
    assert p[0] == pytest.approx(1.0)
    assert p[2] == pytest.approx(0.0)


def test_crest_moves_with_wave_speed():
    w = wave(amplitude=2.0, wavelength=8.0)
    k = 2 * math.pi / 8.0
    speed = math.sqrt(G / k)
    p = w.sample(2.0 + speed, 0.0, 1.0)
    assert p[1] == pytest.approx(2.0)


def test_direction_controls_displacement_axis():
    p = wave(direction=(0.0, 1.0), amplitude=2.0, steepness=0.5).sample(0.0, 0.0, 0.0)
    assert p[0] == pytest.approx(0.0)
    assert p[2] == pytest.approx(1.0)


def test_horizontal_offset_is_bounded():
    w = wave(amplitude=2.0, steepness=0.5)
    for x in [0.0, 0.7, 1.9, 3.3, 5.5, 7.8]:
        p = w.sample(x, 0.0, 0.3)
        assert abs(p[0] - x) <= 1.0 + 1e-9


def test_normal_is_unit_length():
    w = wave()
    for x in [0.0, 1.3, 2.8, 4.4]:
        n = w.normal(x, 0.5, 0.9)
        assert math.sqrt(sum(c * c for c in n)) == pytest.approx(1.0)


def test_normal_faces_upward():
    w = wave(amplitude=1.5, steepness=0.8)
    for x in [0.2, 1.7, 3.1, 5.9]:
        assert w.normal(x, 0.1, 0.4)[1] > 0.0


def test_normal_matches_finite_differences():
    w = wave(amplitude=1.2, wavelength=6.0, steepness=0.6)
    x, z, t = 1.1, 0.4, 0.7
    eps = 1e-4
    px1 = w.sample(x + eps, z, t)
    px0 = w.sample(x - eps, z, t)
    pz1 = w.sample(x, z + eps, t)
    pz0 = w.sample(x, z - eps, t)
    dx = [(px1[i] - px0[i]) / (2 * eps) for i in range(3)]
    dz = [(pz1[i] - pz0[i]) / (2 * eps) for i in range(3)]
    nx = dz[1] * dx[2] - dz[2] * dx[1]
    ny = dz[2] * dx[0] - dz[0] * dx[2]
    nz = dz[0] * dx[1] - dz[1] * dx[0]
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    expected = (nx / length, ny / length, nz / length)
    assert w.normal(x, z, t) == pytest.approx(expected, abs=1e-3)


def test_invalid_wave_parameters_raise():
    with pytest.raises(ValueError):
        ww.GerstnerWave((1.0, 0.0), 1.0, 0.0, 0.5)
    with pytest.raises(ValueError):
        ww.GerstnerWave((1.0, 0.0), -1.0, 8.0, 0.5)
    with pytest.raises(ValueError):
        ww.GerstnerWave((1.0, 0.0), 1.0, 8.0, -0.1)
    with pytest.raises(ValueError):
        ww.GerstnerWave((1.0, 0.0), 1.0, 8.0, 1.1)


def test_surface_sums_wave_offsets():
    a = wave(amplitude=0.8, wavelength=7.0, steepness=0.4)
    b = wave(direction=(0.6, -0.8), amplitude=0.5, wavelength=5.0, steepness=0.6)
    surface = ww.WaterSurface([a, b])
    x, z, t = 2.3, 1.4, 0.8
    pa = a.sample(x, z, t)
    pb = b.sample(x, z, t)
    expected = (pa[0] + pb[0] - x, pa[1] + pb[1], pa[2] + pb[2] - z)
    assert surface.sample(x, z, t) == pytest.approx(expected)


def test_surface_height_uses_vertical_component():
    a = wave(amplitude=0.8, wavelength=7.0, steepness=0.4)
    b = wave(direction=(0.6, -0.8), amplitude=0.5, wavelength=5.0, steepness=0.6)
    surface = ww.WaterSurface([a, b])
    p = surface.sample(0.5, 2.0, 1.2)
    assert surface.height(0.5, 2.0, 1.2) == pytest.approx(p[1])


def test_surface_normal_is_unit_and_up():
    surface = ww.WaterSurface([
        wave(amplitude=0.8, wavelength=7.0, steepness=0.4),
        wave(direction=(0.6, -0.8), amplitude=0.5, wavelength=5.0, steepness=0.6),
    ])
    n = surface.normal(1.3, 2.1, 0.4)
    assert math.sqrt(sum(c * c for c in n)) == pytest.approx(1.0)
    assert n[1] > 0.0
