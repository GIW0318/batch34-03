import pytest

import animation_blend_tree as abt


def tree_1d():
    t = abt.BlendTree()
    t.add_1d("locomotion", "speed", [(0.0, "idle"), (5.0, "walk"), (10.0, "run")])
    return t


def tree_2d():
    t = abt.BlendTree()
    t.add_2d("strafe", "x", "y", [(0.0, 0.0, "center"), (10.0, 0.0, "right"), (0.0, 10.0, "forward")])
    return t


def tree_2d_pair():
    t = abt.BlendTree()
    t.add_2d("strafe", "x", "y", [(0.0, 0.0, "left"), (10.0, 0.0, "right")])
    return t


def test_duplicate_node_name_is_rejected():
    t = tree_1d()
    with pytest.raises(ValueError):
        t.add_1d("locomotion", "speed", [(0.0, "idle")])


def test_thresholds_must_increase():
    t = abt.BlendTree()
    with pytest.raises(ValueError):
        t.add_1d("locomotion", "speed", [(5.0, "walk"), (0.0, "idle")])


def test_one_dimensional_clip_names_must_be_unique():
    t = abt.BlendTree()
    with pytest.raises(ValueError):
        t.add_1d("locomotion", "speed", [(0.0, "walk"), (5.0, "walk")])


def test_one_dimensional_node_needs_a_clip():
    t = abt.BlendTree()
    with pytest.raises(ValueError):
        t.add_1d("locomotion", "speed", [])


def test_two_dimensional_coordinates_must_be_unique():
    t = abt.BlendTree()
    with pytest.raises(ValueError):
        t.add_2d("strafe", "x", "y", [(0.0, 0.0, "a"), (0.0, 0.0, "b")])


def test_unknown_node_is_rejected():
    with pytest.raises(ValueError):
        tree_1d().evaluate("jump", {"speed": 0.0})


def test_missing_parameter_is_rejected():
    with pytest.raises(ValueError):
        tree_1d().evaluate("locomotion", {})


def test_non_numeric_parameter_is_rejected():
    with pytest.raises(ValueError):
        tree_1d().evaluate("locomotion", {"speed": "fast"})


def test_exact_threshold_gives_full_weight():
    assert tree_1d().evaluate("locomotion", {"speed": 5.0}) == {"walk": 1.0}


def test_midpoint_splits_weight_evenly():
    w = tree_1d().evaluate("locomotion", {"speed": 2.5})
    assert w == pytest.approx({"idle": 0.5, "walk": 0.5})


def test_out_of_range_parameters_clamp_to_end_clips():
    t = tree_1d()
    assert t.evaluate("locomotion", {"speed": -3.0}) == {"idle": 1.0}
    assert t.evaluate("locomotion", {"speed": 99.0}) == {"run": 1.0}


def test_only_the_bracketing_clips_are_used():
    w = tree_1d().evaluate("locomotion", {"speed": 7.5})
    assert set(w) == {"walk", "run"}
    assert w["walk"] == pytest.approx(0.5)
    assert w["run"] == pytest.approx(0.5)


def test_two_dimensional_exact_point_wins():
    assert tree_2d().evaluate("strafe", {"x": 10.0, "y": 0.0}) == {"right": 1.0}


def test_two_dimensional_midpoint_splits_weight():
    w = tree_2d_pair().evaluate("strafe", {"x": 5.0, "y": 0.0})
    assert w == pytest.approx({"left": 0.5, "right": 0.5})


def test_closer_clip_gets_more_weight():
    w = tree_2d().evaluate("strafe", {"x": 2.0, "y": 0.0})
    assert w["center"] > w["right"] > w["forward"]
    assert sum(w.values()) == pytest.approx(1.0)
    assert all(v > 0.0 for v in w.values())
