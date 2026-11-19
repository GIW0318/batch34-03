import pytest

import cloth_solver as cs


def cloth(cols=3, rows=3, **kw):
    return cs.ClothSolver(cols, rows, **kw)


def test_columns_below_two_are_rejected():
    with pytest.raises(ValueError):
        cs.ClothSolver(1, 3)


def test_rows_below_two_are_rejected():
    with pytest.raises(ValueError):
        cs.ClothSolver(3, 0)


def test_spacing_must_be_positive():
    with pytest.raises(ValueError):
        cs.ClothSolver(3, 3, spacing=0)


def test_damping_must_be_in_unit_interval():
    with pytest.raises(ValueError):
        cs.ClothSolver(3, 3, damping=1.5)


def test_rounds_must_be_positive():
    with pytest.raises(ValueError):
        cs.ClothSolver(3, 3, rounds=0)


def test_initial_positions_form_grid():
    p = cs.ClothSolver(3, 2, spacing=2.0).positions()
    assert p[0] == [0.0, 0.0]
    assert p[1] == [2.0, 0.0]
    assert p[3] == [0.0, -2.0]
    assert p[5] == [4.0, -2.0]


def test_pinned_point_never_moves():
    c = cloth()
    c.pin(0, 0)
    for _ in range(100):
        c.advance(1.0 / 60.0)
    assert c.positions()[0] == [0.0, 0.0]


def test_free_point_falls_after_one_step():
    c = cloth()
    c.advance(1.0 / 60.0)
    assert c.positions()[4][1] < 0.0


def test_unpinned_cloth_keeps_grid_shape_while_falling():
    c = cloth(3, 2)
    c.advance(1.0 / 60.0)
    p = c.positions()
    assert p[0][1] == p[2][1]
    assert p[3][1] == p[5][1]
    assert [q[0] for q in p] == [0.0, 1.0, 2.0, 0.0, 1.0, 2.0]


def test_advance_with_zero_dt_is_rejected():
    c = cloth()
    with pytest.raises(ValueError):
        c.advance(0)


def test_pin_out_of_range_is_rejected():
    c = cloth()
    with pytest.raises(ValueError):
        c.pin(3, 0)


def test_hanging_middle_stays_centred():
    c = cloth()
    c.pin(0, 0)
    c.pin(2, 0)
    for _ in range(40):
        c.advance(1.0 / 60.0)
    p = c.positions()[7]
    assert abs(p[0] - 1.0) < 0.02
    assert p[1] < -2.0


def test_distance_constraints_stay_within_tolerance():
    c = cloth()
    for col in range(3):
        c.pin(col, 0)
    for _ in range(80):
        c.advance(1.0 / 60.0)
    assert c.max_stretch() < 0.1


def test_positions_returns_an_independent_copy():
    c = cloth()
    p = c.positions()
    p[0][0] = 99.0
    assert c.positions()[0][0] == 0.0


def test_max_stretch_is_zero_for_initial_grid():
    assert cloth().max_stretch() == 0.0
