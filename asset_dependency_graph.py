class AssetGraph:
    def __init__(self):
        self._deps = {}

    def add_asset(self, name, deps=()):
        return None

    def build_order(self):
        return None

    def missing_deps(self):
        return None

    def cycles(self):
        return None

    def state(self):
        return {}
