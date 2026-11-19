import pytest

import video_frame_pacer as vf


def pacer(fps=4):
    return vf.FramePacer(fps)


def test_fps_must_be_positive():
    with pytest.raises(ValueError):
        vf.FramePacer(0)


def test_negative_pts_is_rejected():
    with pytest.raises(ValueError):
        pacer().submit(-0.25)


def test_string_pts_is_rejected():
    with pytest.raises(ValueError):
        pacer().submit("0.25")


def test_pts_must_strictly_increase():
    unit = pacer()
    unit.submit(0.0)
    with pytest.raises(ValueError):
        unit.submit(0.0)


def test_empty_queue_is_idle():
    assert pacer().present(1.0)["action"] == "idle"


def test_show_frame_due_now():
    unit = pacer()
    unit.submit(0.0)
    result = unit.present(0.0)
    assert result == {"action": "show", "index": 0, "pts": 0.0, "dropped": []}


def test_before_first_frame_is_idle():
    unit = pacer()
    unit.submit(0.5)
    assert unit.present(0.25)["action"] == "idle"


def test_same_frame_twice_is_duplicate():
    unit = pacer()
    unit.submit(0.0)
    unit.present(0.0)
    result = unit.present(0.1)
    assert result["action"] == "duplicate"
    assert result["index"] == 0


def test_advance_to_next_frame():
    unit = pacer()
    unit.submit(0.0)
    unit.submit(0.25)
    unit.present(0.0)
    result = unit.present(0.25)
    assert result["action"] == "show"
    assert result["index"] == 1
    assert result["dropped"] == []


def test_skip_records_all_dropped_indices():
    unit = pacer()
    for pts in (0.0, 0.25, 0.5, 0.75):
        unit.submit(pts)
    unit.present(0.0)
    result = unit.present(0.75)
    assert result["index"] == 3
    assert result["dropped"] == [1, 2]


def test_drop_counter_accumulates():
    unit = pacer()
    for pts in (0.0, 0.25, 0.5, 0.75):
        unit.submit(pts)
    unit.present(0.0)
    unit.present(0.75)
    assert unit.stats()["dropped"] == 2


def test_duplicate_counter_accumulates():
    unit = pacer()
    unit.submit(0.0)
    unit.present(0.0)
    unit.present(0.1)
    assert unit.stats()["duplicated"] == 1
    assert unit.stats()["presented"] == 1


def test_present_uses_audio_clock_not_latest_frame():
    unit = pacer()
    for pts in (0.0, 0.25, 0.5):
        unit.submit(pts)
    unit.present(0.0)
    assert unit.present(0.4)["index"] == 1


def test_reset_clears_queue_and_counters():
    unit = pacer()
    unit.submit(0.0)
    unit.present(0.0)
    unit.reset()
    assert unit.state()["frames"] == []
    assert unit.state()["presented"] == 0
    assert unit.present(1.0)["action"] == "idle"


def test_state_snapshot_is_independent():
    unit = pacer()
    unit.submit(0.0)
    unit.present(0.0)
    snapshot = unit.state()
    snapshot["frames"].append(9.0)
    snapshot["presented"] = 99
    assert unit.state()["frames"] == [0.0]
    assert unit.state()["presented"] == 1
