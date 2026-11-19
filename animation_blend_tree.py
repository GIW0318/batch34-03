import math
import numbers


def _require_number(value):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError("value must be a number")
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    return value


class BlendTree:
    def __init__(self):
        self._nodes = {}

    def add_1d(self, name, param, points):
        if name in self._nodes:
            raise ValueError("node already exists")

        try:
            points = list(points)
        except TypeError:
            raise ValueError("points must be iterable") from None
        if not points:
            raise ValueError("a 1D node needs at least one clip")

        parsed = []
        clip_names = set()
        previous_threshold = None
        for point in points:
            try:
                threshold, clip = point
            except (TypeError, ValueError):
                raise ValueError("each point must be (threshold, clip)") from None

            threshold = _require_number(threshold)
            if previous_threshold is not None and threshold <= previous_threshold:
                raise ValueError("thresholds must strictly increase")
            if clip in clip_names:
                raise ValueError("clip names must be unique")

            clip_names.add(clip)
            parsed.append((threshold, clip))
            previous_threshold = threshold

        self._nodes[name] = ("1d", param, parsed)

    def add_2d(self, name, param_x, param_y, points):
        if name in self._nodes:
            raise ValueError("node already exists")

        try:
            points = list(points)
        except TypeError:
            raise ValueError("points must be iterable") from None
        if not points:
            raise ValueError("a 2D node needs at least one clip")

        parsed = []
        clip_names = set()
        coordinates = set()
        for point in points:
            try:
                x, y, clip = point
            except (TypeError, ValueError):
                raise ValueError("each point must be (x, y, clip)") from None

            x = _require_number(x)
            y = _require_number(y)
            coordinate = (x, y)
            if coordinate in coordinates:
                raise ValueError("coordinates must be unique")
            if clip in clip_names:
                raise ValueError("clip names must be unique")

            coordinates.add(coordinate)
            clip_names.add(clip)
            parsed.append((x, y, clip))

        self._nodes[name] = ("2d", param_x, param_y, parsed)

    def evaluate(self, name, params):
        if name not in self._nodes:
            raise ValueError("unknown node")
        if not isinstance(params, dict):
            raise ValueError("params must be a dictionary")

        node = self._nodes[name]
        if node[0] == "1d":
            return self._evaluate_1d(node, params)
        return self._evaluate_2d(node, params)

    @staticmethod
    def _parameter(params, name):
        if name not in params:
            raise ValueError("missing parameter")
        return _require_number(params[name])

    def _evaluate_1d(self, node, params):
        _, param, points = node
        value = self._parameter(params, param)

        if value <= points[0][0]:
            return {points[0][1]: 1.0}
        if value >= points[-1][0]:
            return {points[-1][1]: 1.0}

        for (lower_threshold, lower_clip), (upper_threshold, upper_clip) in zip(
            points, points[1:]
        ):
            if value == lower_threshold:
                return {lower_clip: 1.0}
            if lower_threshold < value < upper_threshold:
                upper_weight = (value - lower_threshold) / (
                    upper_threshold - lower_threshold
                )
                weights = {
                    lower_clip: 1.0 - upper_weight,
                    upper_clip: upper_weight,
                }
                return {clip: weight for clip, weight in weights.items() if weight > 0}

        return {points[-1][1]: 1.0}

    def _evaluate_2d(self, node, params):
        _, param_x, param_y, points = node
        x = self._parameter(params, param_x)
        y = self._parameter(params, param_y)

        distances = []
        for point_x, point_y, clip in points:
            distance_squared = (x - point_x) ** 2 + (y - point_y) ** 2
            if distance_squared == 0:
                return {clip: 1.0}
            distances.append((distance_squared, clip))

        inverse_distances = [
            (1.0 / distance_squared, clip)
            for distance_squared, clip in distances
        ]
        total = math.fsum(weight for weight, _ in inverse_distances)
        return {
            clip: weight / total
            for weight, clip in inverse_distances
            if weight > 0
        }
