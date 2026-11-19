import pytest

import deformable_mesh as dm


def mesh(positions, springs=(), masses=None, velocities=None,
         stiffness=1.0, damping=0.0, pinned=()):
    return dm.MassSpringMesh(
        positions,
        list(springs),
        masses=masses,
        velocities=velocities,
        stiffness=stiffness,
        damping=damping,
        pinned=pinned,
    )


def test_free_mass_without_force_stays_still():
    body = mesh([(0.0, 0.0)])
    body.step(0.5, (0.0, 0.0))
    assert body.positions() == [(0.0, 0.0)]


def test_gravity_accelerates_free_mass():
    body = mesh([(0.0, 0.0)])
    body.step(0.5, (0.0, -10.0))
    assert body.positions() == [(0.0, -2.5)]
    assert body.velocities() == [(0.0, -5.0)]


def test_mass_scales_spring_acceleration():
    light = mesh([(0.0, 0.0), (1.0, 0.0)], [(0, 1, 2.0)], stiffness=1.0, pinned=[0])
    light.step(1.0, (0.0, 0.0))
    heavy = mesh(
        [(0.0, 0.0), (1.0, 0.0)],
        [(0, 1, 2.0)],
        masses=[1.0, 2.0],
        stiffness=1.0,
        pinned=[0],
    )
    heavy.step(1.0, (0.0, 0.0))
    assert light.positions()[1] == (2.0, 0.0)
    assert heavy.positions()[1] == (1.5, 0.0)


def test_damping_reduces_velocity():
    body = mesh([(0.0, 0.0)], velocities=[(4.0, 0.0)], damping=0.5)
    body.step(1.0, (0.0, 0.0))
    assert body.velocities() == [(2.0, 0.0)]
    assert body.positions() == [(2.0, 0.0)]


def test_stretched_spring_pulls_inward():
    body = mesh([(0.0, 0.0), (4.0, 0.0)], [(0, 1, 2.0)], stiffness=2.0)
    body.step(0.5, (0.0, 0.0))
    assert body.positions() == [(1.0, 0.0), (3.0, 0.0)]


def test_compressed_spring_pushes_outward():
    body = mesh([(0.0, 0.0), (1.0, 0.0)], [(0, 1, 2.0)], stiffness=2.0)
    body.step(0.5, (0.0, 0.0))
    assert body.positions() == [(-0.5, 0.0), (1.5, 0.0)]


def test_spring_at_rest_exerts_no_force():
    body = mesh([(0.0, 0.0), (2.0, 0.0)], [(0, 1, 2.0)], stiffness=2.0)
    body.step(1.0, (0.0, 0.0))
    assert body.positions() == [(0.0, 0.0), (2.0, 0.0)]
    assert body.velocities() == [(0.0, 0.0), (0.0, 0.0)]


def test_pinned_vertex_ignores_gravity():
    body = mesh([(0.0, 0.0), (1.0, 0.0)], pinned=[0])
    body.step(0.5, (0.0, -10.0))
    assert body.positions()[0] == (0.0, 0.0)
    assert body.velocities()[0] == (0.0, 0.0)
    assert body.positions()[1] == (1.0, -2.5)


def test_pinned_vertex_holds_compressed_spring():
    body = mesh([(0.0, 0.0), (1.0, 0.0)], [(0, 1, 2.0)], stiffness=1.0, pinned=[0])
    body.step(1.0, (0.0, 0.0))
    assert body.positions()[0] == (0.0, 0.0)
    assert body.positions()[1] == (2.0, 0.0)


def test_invalid_spring_index_is_rejected():
    with pytest.raises(ValueError):
        mesh([(0.0, 0.0)], [(0, 3)])


def test_self_spring_is_rejected():
    with pytest.raises(ValueError):
        mesh([(0.0, 0.0)], [(0, 0)])


def test_duplicate_spring_is_rejected():
    with pytest.raises(ValueError):
        mesh([(0.0, 0.0), (1.0, 0.0)], [(0, 1), (1, 0)])


def test_damping_must_be_below_one():
    with pytest.raises(ValueError):
        mesh([(0.0, 0.0)], damping=1.0)


def test_step_rejects_non_positive_dt():
    body = mesh([(0.0, 0.0)])
    with pytest.raises(ValueError):
        body.step(0.0)


def test_state_snapshot_is_independent():
    body = mesh([(0.0, 0.0), (3.0, 0.0)], [(0, 1, 2.0)], stiffness=2.0)
    snapshot = body.state()
    snapshot["positions"][0] = (99.0, 99.0)
    snapshot["springs"][0] = (0, 1, 99.0)
    assert body.state()["positions"][0] == (0.0, 0.0)
    assert body.state()["springs"][0] == (0, 1, 2.0)
