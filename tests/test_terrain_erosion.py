import math

import pytest

import terrain_erosion as te

FLAT = [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]


def peak_map():
    m = [[0.5] * 5 for _ in range(5)]
    m[2][2] = 5.0
    return m


def test_empty_heightmap_is_rejected():
    with pytest.raises(ValueError):
        te.HydraulicErosion([])


def test_ragged_heightmap_is_rejected():
    with pytest.raises(ValueError):
        te.HydraulicErosion([[1.0, 2.0], [1.0]])


def test_non_numeric_height_is_rejected():
    with pytest.raises(ValueError):
        te.HydraulicErosion([[1.0, "2.0"]])


def test_erosion_rate_must_be_a_fraction():
    with pytest.raises(ValueError):
        te.HydraulicErosion(FLAT, erosion_rate=1.5)


def test_evaporation_must_be_below_one():
    with pytest.raises(ValueError):
        te.HydraulicErosion(FLAT, evaporation=1.0)


def test_carry_factor_must_be_positive():
    with pytest.raises(ValueError):
        te.HydraulicErosion(FLAT, carry_factor=0)


def test_negative_droplet_count_is_rejected():
    e = te.HydraulicErosion(FLAT)
    with pytest.raises(ValueError):
        e.erode(droplets=-1)


def test_zero_steps_is_rejected():
    e = te.HydraulicErosion(FLAT)
    with pytest.raises(ValueError):
        e.erode(droplets=1, max_steps=0)


def test_start_outside_heightmap_is_rejected():
    e = te.HydraulicErosion(FLAT)
    with pytest.raises(ValueError):
        e.erode(droplets=1, start=(3, 0))


def test_zero_droplets_leave_terrain_untouched():
    e = te.HydraulicErosion(FLAT)
    before = e.heights()
    stats = e.erode(droplets=0, seed=7)
    assert e.heights() == before
    assert stats["moved"] == 0.0


def test_stats_echo_droplets_and_seed():
    e = te.HydraulicErosion(peak_map())
    stats = e.erode(droplets=3, seed=11, start=(2, 2))
    assert stats["droplets"] == 3
    assert stats["seed"] == 11
    assert stats["moved"] > 0.0
    assert stats["moved"] == pytest.approx(e.sediment_total())


def test_fixed_start_is_reproducible_across_seeds():
    a = te.HydraulicErosion(peak_map())
    b = te.HydraulicErosion(peak_map())
    a.erode(droplets=5, max_steps=20, seed=1, start=(2, 2))
    b.erode(droplets=5, max_steps=20, seed=99, start=(2, 2))
    ha = a.heights()
    hb = b.heights()
    assert len(ha) == 5
    assert ha == hb


def test_summit_is_lowered_by_a_droplet():
    e = te.HydraulicErosion(peak_map())
    e.erode(droplets=1, max_steps=20, seed=0, start=(2, 2))
    assert e.heights()[2][2] < 5.0


def test_eroded_material_is_deposited_downstream():
    e = te.HydraulicErosion(peak_map())
    e.erode(droplets=1, max_steps=20, seed=0, start=(2, 2))
    h = e.heights()
    assert any(h[y][x] > 0.5 for y in range(5) for x in range(5) if (x, y) != (2, 2))


def test_invariants_hold_after_many_droplets():
    e = te.HydraulicErosion(peak_map(), evaporation=0.02)
    before = sum(sum(row) for row in e.heights())
    e.erode(droplets=40, max_steps=30, seed=3)
    h = e.heights()
    after = sum(sum(row) for row in h)
    assert math.isclose(before, after, rel_tol=1e-9, abs_tol=1e-9)
    assert all(math.isfinite(v) and v >= 0.0 for row in h for v in row)
    h[0][0] = 123.0
    assert e.heights()[0][0] != 123.0
