import math

import pytest

import camera_occlusion as co


def boom(**kw):
    return co.CameraBoom((0.0, 0.0, 0.0), 10.0, **kw)


def test_target_must_be_three_dimensional():
    with pytest.raises(ValueError):
        co.CameraBoom((0.0, 1.0), 10.0)


def test_max_distance_must_be_positive():
    with pytest.raises(ValueError):
        co.CameraBoom((0.0, 0.0, 0.0), 0.0)


def test_min_distance_must_be_smaller_than_max():
    with pytest.raises(ValueError):
        co.CameraBoom((0.0, 0.0, 0.0), 5.0, min_distance=5.0)


def test_probe_radius_must_not_be_negative():
    with pytest.raises(ValueError):
        co.CameraBoom((0.0, 0.0, 0.0), 10.0, probe_radius=-0.1)


def test_obstacle_radius_must_be_positive():
    b = boom()
    with pytest.raises(ValueError):
        b.add_obstacle((2.0, 0.0, 0.0), 0.0)


def test_zero_direction_is_rejected():
    with pytest.raises(ValueError):
        boom().solve((0.0, 0.0, 0.0))


def test_open_space_keeps_full_boom():
    r = boom().solve((1.0, 0.0, 0.0))
    assert r["distance"] == 10.0
    assert r["hit"] is None
    assert r["point"] == (10.0, 0.0, 0.0)


def test_sphere_directly_ahead_shortens_boom():
    b = boom()
    b.add_obstacle((5.0, 0.0, 0.0), 1.0)
    r = b.solve((1.0, 0.0, 0.0))
    assert r["distance"] == pytest.approx(4.0)
    assert r["hit"] == 0


def test_sphere_behind_target_is_ignored():
    b = boom()
    b.add_obstacle((-5.0, 0.0, 0.0), 1.0)
    r = b.solve((1.0, 0.0, 0.0))
    assert r["distance"] == 10.0
    assert r["hit"] is None


def test_sphere_off_the_axis_is_ignored():
    b = boom()
    b.add_obstacle((5.0, 3.0, 0.0), 1.0)
    r = b.solve((1.0, 0.0, 0.0))
    assert r["distance"] == 10.0
    assert r["hit"] is None


def test_nearest_sphere_wins():
    b = boom()
    b.add_obstacle((7.0, 0.0, 0.0), 1.0)
    b.add_obstacle((3.0, 0.0, 0.0), 1.0)
    r = b.solve((1.0, 0.0, 0.0))
    assert r["distance"] == pytest.approx(2.0)
    assert r["hit"] == 1


def test_target_inside_sphere_clamps_to_minimum():
    b = boom(min_distance=0.25)
    b.add_obstacle((0.1, 0.0, 0.0), 1.0)
    r = b.solve((1.0, 0.0, 0.0))
    assert r["distance"] == pytest.approx(0.25)
    assert r["hit"] == 0


def test_offset_ray_catches_a_glancing_sphere():
    b = boom()
    b.add_obstacle((5.0, 0.9, 0.0), 1.0)
    r = b.solve((1.0, 0.0, 0.0))
    assert r["distance"] == pytest.approx(5.0 - math.sqrt(0.51), abs=1e-6)
    assert r["hit"] == 0


def test_hit_point_lies_on_the_boom_axis():
    b = boom()
    b.add_obstacle((5.0, 0.0, 0.0), 1.0)
    r = b.solve((2.0, 0.0, 0.0))
    assert r["point"] == pytest.approx((4.0, 0.0, 0.0))


def test_hit_reports_the_second_obstacle_index():
    b = boom()
    b.add_obstacle((5.0, 3.0, 0.0), 1.0)
    b.add_obstacle((6.0, 0.0, 0.0), 1.0)
    r = b.solve((1.0, 0.0, 0.0))
    assert r["hit"] == 1
    assert r["distance"] == pytest.approx(5.0)
