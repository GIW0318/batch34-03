import pytest

import astar_budget as ab

OPEN3 = ["...", "...", "..."]


def test_empty_grid_is_rejected():
    with pytest.raises(ValueError):
        ab.astar([], (0, 0), (0, 0))


def test_ragged_grid_is_rejected():
    with pytest.raises(ValueError):
        ab.astar(["...", ".."], (0, 0), (1, 1))


def test_start_outside_grid_is_rejected():
    with pytest.raises(ValueError):
        ab.astar(OPEN3, (3, 0), (2, 2))


def test_goal_on_a_wall_is_rejected():
    with pytest.raises(ValueError):
        ab.astar(["..#"], (0, 0), (0, 2))


def test_zero_budget_is_rejected():
    with pytest.raises(ValueError):
        ab.astar(OPEN3, (0, 0), (2, 2), max_expansions=0)


def test_unknown_tie_break_is_rejected():
    with pytest.raises(ValueError):
        ab.astar(OPEN3, (0, 0), (2, 2), tie_break="random")


def test_start_equal_goal_returns_single_point():
    r = ab.astar(OPEN3, (1, 1), (1, 1))
    assert r["path"] == [(1, 1)]
    assert r["cost"] == 0
    assert r["complete"] is True


def test_straight_corridor_path():
    r = ab.astar(["....."], (0, 0), (0, 4))
    assert r["path"] == [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
    assert r["cost"] == 4


def test_path_detours_around_walls():
    grid = [".....", ".##..", "....."]
    r = ab.astar(grid, (0, 0), (2, 4))
    assert r["path"][0] == (0, 0)
    assert r["path"][-1] == (2, 4)
    assert r["cost"] == 6
    assert all(grid[r][c] != "#" for r, c in r["path"])


def test_path_steps_are_four_neighbour_moves():
    grid = [".....", ".##..", "....."]
    path = ab.astar(grid, (0, 0), (2, 4))["path"]
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        assert abs(x1 - x2) + abs(y1 - y2) == 1


def test_cost_matches_path_length():
    grid = [".....", ".##..", "....."]
    r = ab.astar(grid, (0, 0), (2, 4))
    assert r["cost"] == len(r["path"]) - 1


def test_unreachable_goal_reports_complete_without_path():
    grid = ["..#..", "..#..", "..#.."]
    r = ab.astar(grid, (0, 0), (0, 4))
    assert r["path"] is None
    assert r["complete"] is True
    assert r["expanded"] < 100


def test_budget_exhaustion_reports_incomplete():
    r = ab.astar(OPEN3, (0, 0), (2, 2), max_expansions=2)
    assert r["path"] is None
    assert r["complete"] is False
    assert r["expanded"] == 2


def test_h_tie_break_focuses_the_search():
    r = ab.astar(OPEN3, (0, 0), (2, 2), tie_break="h")
    assert r["expanded"] == 5


def test_fifo_tie_break_expands_more_than_h():
    h = ab.astar(OPEN3, (0, 0), (2, 2), tie_break="h")
    fifo = ab.astar(OPEN3, (0, 0), (2, 2), tie_break="fifo")
    assert fifo["expanded"] > h["expanded"]
