class AssetGraph:
    def __init__(self):
        self._deps = {}

    def add_asset(self, name, deps=()):
        if not isinstance(name, str) or not name:
            raise ValueError("asset name must be a non-empty string")
        if name in self._deps:
            raise ValueError("duplicate asset: %r" % name)
        deps = list(deps)
        seen = set()
        for dep in deps:
            if not isinstance(dep, str) or not dep:
                raise ValueError("dependency name must be a non-empty string")
            if dep in seen:
                raise ValueError("duplicate dependency: %r" % dep)
            seen.add(dep)
        self._deps[name] = deps

    def build_order(self):
        missing = self.missing_deps()
        if missing:
            raise ValueError("missing dependencies: %r" % missing)
        import heapq

        indegree = {name: 0 for name in self._deps}
        dependents = {name: [] for name in self._deps}
        for name, deps in self._deps.items():
            indegree[name] = len(deps)
            for dep in deps:
                dependents[dep].append(name)
        ready = [name for name, degree in indegree.items() if degree == 0]
        heapq.heapify(ready)
        order = []
        while ready:
            name = heapq.heappop(ready)
            order.append(name)
            for dependent in dependents[name]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    heapq.heappush(ready, dependent)
        if len(order) != len(self._deps):
            raise ValueError("dependency cycle detected: %r" % self.cycles())
        return order

    def missing_deps(self):
        missing = []
        for name in sorted(self._deps):
            for dep in sorted(self._deps[name]):
                if dep not in self._deps:
                    missing.append((name, dep))
        return missing

    def cycles(self):
        index_of = {}
        lowlink = {}
        on_stack = set()
        stack = []
        components = []
        for root in sorted(self._deps):
            if root in index_of:
                continue
            work = [(root, 0)]
            while work:
                node, child_idx = work[-1]
                if child_idx == 0:
                    index_of[node] = lowlink[node] = len(index_of)
                    stack.append(node)
                    on_stack.add(node)
                neighbors = sorted(
                    dep for dep in self._deps[node] if dep in self._deps
                )
                if child_idx < len(neighbors):
                    work[-1] = (node, child_idx + 1)
                    child = neighbors[child_idx]
                    if child not in index_of:
                        work.append((child, 0))
                    elif child in on_stack:
                        lowlink[node] = min(lowlink[node], index_of[child])
                else:
                    work.pop()
                    if work:
                        parent = work[-1][0]
                        lowlink[parent] = min(lowlink[parent], lowlink[node])
                    if lowlink[node] == index_of[node]:
                        component = []
                        while True:
                            member = stack.pop()
                            on_stack.discard(member)
                            component.append(member)
                            if member == node:
                                break
                        components.append(component)
        result = []
        for component in components:
            if len(component) > 1 or component[0] in self._deps[component[0]]:
                result.append(sorted(component))
        result.sort(key=lambda component: component[0])
        return result

    def state(self):
        return {
            "assets": {
                name: sorted(self._deps[name]) for name in sorted(self._deps)
            }
        }
