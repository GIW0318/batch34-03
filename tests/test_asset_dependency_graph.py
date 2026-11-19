import pytest

import asset_dependency_graph as ad


def test_empty_graph_has_empty_order():
    assert ad.AssetGraph().build_order() == []


def test_single_asset_order():
    graph = ad.AssetGraph()
    graph.add_asset("core")
    assert graph.build_order() == ["core"]


def test_dependency_comes_first():
    graph = ad.AssetGraph()
    graph.add_asset("ui", ["core"])
    graph.add_asset("core")
    assert graph.build_order() == ["core", "ui"]


def test_lexicographic_tie_break():
    graph = ad.AssetGraph()
    graph.add_asset("zeta")
    graph.add_asset("alpha")
    graph.add_asset("mid", ["zeta"])
    assert graph.build_order() == ["alpha", "zeta", "mid"]


def test_diamond_dependency_order():
    graph = ad.AssetGraph()
    graph.add_asset("top", ["left", "right"])
    graph.add_asset("left", ["base"])
    graph.add_asset("right", ["base"])
    graph.add_asset("base")
    assert graph.build_order() == ["base", "left", "right", "top"]


def test_missing_dependency_is_reported():
    graph = ad.AssetGraph()
    graph.add_asset("ui", ["core"])
    assert graph.missing_deps() == [("ui", "core")]


def test_missing_dependency_blocks_build():
    graph = ad.AssetGraph()
    graph.add_asset("ui", ["core"])
    with pytest.raises(ValueError):
        graph.build_order()


def test_two_node_cycle_is_normalized():
    graph = ad.AssetGraph()
    graph.add_asset("b", ["a"])
    graph.add_asset("a", ["b"])
    assert graph.cycles() == [["a", "b"]]


def test_self_cycle_is_reported():
    graph = ad.AssetGraph()
    graph.add_asset("self", ["self"])
    assert graph.cycles() == [["self"]]


def test_cycle_blocks_build():
    graph = ad.AssetGraph()
    graph.add_asset("a", ["b"])
    graph.add_asset("b", ["a"])
    with pytest.raises(ValueError):
        graph.build_order()


def test_duplicate_asset_is_rejected():
    graph = ad.AssetGraph()
    graph.add_asset("core")
    with pytest.raises(ValueError):
        graph.add_asset("core")


def test_empty_asset_name_is_rejected():
    with pytest.raises(ValueError):
        ad.AssetGraph().add_asset("")


def test_duplicate_dependency_is_rejected():
    with pytest.raises(ValueError):
        ad.AssetGraph().add_asset("ui", ["core", "core"])


def test_non_string_dependency_is_rejected():
    with pytest.raises(ValueError):
        ad.AssetGraph().add_asset("ui", [3])


def test_state_snapshot_is_independent():
    graph = ad.AssetGraph()
    graph.add_asset("ui", ["core", "audio"])
    graph.add_asset("core")
    graph.add_asset("audio")
    snapshot = graph.state()
    assert snapshot["assets"]["ui"] == ["audio", "core"]
    snapshot["assets"]["ui"].append("hack")
    assert graph.state()["assets"]["ui"] == ["audio", "core"]
