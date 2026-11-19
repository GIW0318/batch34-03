import math


def _vector3(value, name):
    try:
        vector = tuple(float(component) for component in value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a three-dimensional vector") from exc

    if len(vector) != 3:
        raise ValueError(f"{name} must be a three-dimensional vector")
    if not all(math.isfinite(component) for component in vector):
        raise ValueError(f"{name} must contain finite values")
    return vector


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _scale(vector, scalar):
    return tuple(component * scalar for component in vector)


def _normalize(vector):
    length = math.sqrt(_dot(vector, vector))
    if length == 0.0:
        raise ValueError("direction must not be a zero vector")
    return tuple(component / length for component in vector)


def _ray_sphere_distance(origin, direction, center, radius):
    offset = tuple(origin[i] - center[i] for i in range(3))
    half_b = _dot(offset, direction)
    c = _dot(offset, offset) - radius * radius
    discriminant = half_b * half_b - c
    if discriminant < 0.0:
        return None

    root = math.sqrt(discriminant)
    near = -half_b - root
    far = -half_b + root
    if near > 0.0:
        return near
    if far > 0.0:
        return far
    return None


class CameraBoom:
    def __init__(self, target, max_distance, probe_radius=0.2, min_distance=0.1):
        self.target = _vector3(target, "target")

        try:
            self.max_distance = float(max_distance)
            self.probe_radius = float(probe_radius)
            self.min_distance = float(min_distance)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "camera distances and probe radius must be numbers"
            ) from exc

        if not all(
            math.isfinite(value)
            for value in (self.max_distance, self.probe_radius, self.min_distance)
        ):
            raise ValueError("camera distances and probe radius must be finite")
        if self.max_distance <= 0.0:
            raise ValueError("max_distance must be positive")
        if self.min_distance >= self.max_distance:
            raise ValueError("min_distance must be smaller than max_distance")
        if self.probe_radius <= 0.0:
            raise ValueError("probe_radius must be positive")

        self.obstacles = []

    def add_obstacle(self, center, radius):
        center = _vector3(center, "center")
        try:
            radius = float(radius)
        except (TypeError, ValueError) as exc:
            raise ValueError("obstacle radius must be a number") from exc
        if not math.isfinite(radius) or radius <= 0.0:
            raise ValueError("obstacle radius must be positive")

        self.obstacles.append((center, radius))
        return len(self.obstacles) - 1

    def solve(self, direction):
        direction = _normalize(_vector3(direction, "direction"))

        world_up = (0.0, 1.0, 0.0)
        if abs(direction[1]) > 1.0 - 1e-9:
            world_up = (1.0, 0.0, 0.0)
        right = _normalize(_cross(direction, world_up))
        up = _normalize(_cross(right, direction))

        offsets = (
            (0.0, 0.0, 0.0),
            _scale(right, self.probe_radius),
            _scale(right, -self.probe_radius),
            _scale(up, self.probe_radius),
            _scale(up, -self.probe_radius),
        )

        best_distance = None
        best_hit = None

        for index, (center, radius) in enumerate(self.obstacles):
            to_target = tuple(self.target[i] - center[i] for i in range(3))
            if _dot(to_target, to_target) <= radius * radius:
                best_distance = 0.0
                best_hit = index
                break

            for offset in offsets:
                origin = tuple(self.target[i] + offset[i] for i in range(3))
                distance = _ray_sphere_distance(origin, direction, center, radius)
                if distance is None:
                    continue
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_hit = index

        if best_hit is None:
            distance = self.max_distance
        else:
            distance = min(
                self.max_distance, max(self.min_distance, best_distance)
            )

        point = tuple(
            self.target[i] + direction[i] * distance for i in range(3)
        )
        return {"distance": distance, "hit": best_hit, "point": point}
