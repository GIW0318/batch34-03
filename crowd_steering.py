import math


def _validate(positions, velocities=None, radius=None, dt=None):
    if velocities is not None and len(positions) != len(velocities):
        raise ValueError("positions and velocities must have the same length")
    if radius is not None and radius <= 0:
        raise ValueError("radius must be positive")
    if dt is not None and dt <= 0:
        raise ValueError("dt must be positive")


def _clamp(vector, max_length):
    length = math.hypot(vector[0], vector[1])
    if length > max_length and length > 0.0:
        scale = max_length / length
        clamped = (vector[0] * scale, vector[1] * scale)
        clamped_length = math.hypot(clamped[0], clamped[1])
        if clamped_length > max_length:
            correction = math.nextafter(
                max_length / clamped_length, 0.0)
            clamped = (
                clamped[0] * correction,
                clamped[1] * correction,
            )
        return clamped
    return vector


def neighbor_grid(positions, radius, cell_size=None):
    _validate(positions, radius=radius)
    if cell_size is None:
        cell_size = radius
    if cell_size <= 0:
        raise ValueError("cell_size must be positive")

    cells = {}
    for index, (x, y) in enumerate(positions):
        key = (math.floor(x / cell_size), math.floor(y / cell_size))
        cells.setdefault(key, []).append(index)

    reach = int(math.ceil(radius / cell_size))
    neighbors = []
    for index, (x, y) in enumerate(positions):
        cell_x = math.floor(x / cell_size)
        cell_y = math.floor(y / cell_size)
        found = []
        for offset_x in range(-reach, reach + 1):
            for offset_y in range(-reach, reach + 1):
                for other in cells.get(
                        (cell_x + offset_x, cell_y + offset_y), ()):
                    if other == index:
                        continue
                    other_x, other_y = positions[other]
                    diff_x = other_x - x
                    diff_y = other_y - y
                    if math.hypot(diff_x, diff_y) <= radius:
                        found.append(other)
        neighbors.append(sorted(found))
    return neighbors


def boids_forces(positions, velocities, separation=1.0, alignment=1.0,
                 cohesion=1.0, radius=3.0, max_force=1.0, cell_size=None):
    _validate(positions, velocities, radius=radius)
    neighbors = neighbor_grid(positions, radius, cell_size=cell_size)

    forces = []
    for index, neighbor_ids in enumerate(neighbors):
        separation_x = 0.0
        separation_y = 0.0
        alignment_x = 0.0
        alignment_y = 0.0
        cohesion_x = 0.0
        cohesion_y = 0.0
        count = len(neighbor_ids)

        if count:
            position_x, position_y = positions[index]
            velocity_x, velocity_y = velocities[index]
            for other in neighbor_ids:
                other_x, other_y = positions[other]
                diff_x = position_x - other_x
                diff_y = position_y - other_y
                distance_sq = diff_x * diff_x + diff_y * diff_y
                if distance_sq > 0.0:
                    separation_x += diff_x / distance_sq
                    separation_y += diff_y / distance_sq

                other_velocity_x, other_velocity_y = velocities[other]
                alignment_x += other_velocity_x
                alignment_y += other_velocity_y
                cohesion_x += other_x
                cohesion_y += other_y

            alignment_x = alignment_x / count - velocity_x
            alignment_y = alignment_y / count - velocity_y
            cohesion_x = cohesion_x / count - position_x
            cohesion_y = cohesion_y / count - position_y

        force = (
            separation * separation_x
            + alignment * alignment_x
            + cohesion * cohesion_x,
            separation * separation_y
            + alignment * alignment_y
            + cohesion * cohesion_y,
        )
        forces.append(_clamp(force, max_force))
    return forces


def step(positions, velocities, dt=1.0, separation=1.0, alignment=1.0,
         cohesion=1.0, radius=3.0, max_force=1.0, max_speed=2.0,
         cell_size=None):
    _validate(positions, velocities, radius=radius, dt=dt)
    forces = boids_forces(
        positions,
        velocities,
        separation=separation,
        alignment=alignment,
        cohesion=cohesion,
        radius=radius,
        max_force=max_force,
        cell_size=cell_size,
    )

    new_positions = []
    new_velocities = []
    for (position_x, position_y), (velocity_x, velocity_y), (force_x, force_y) in zip(
            positions, velocities, forces):
        new_velocity_x, new_velocity_y = _clamp(
            (velocity_x + force_x * dt, velocity_y + force_y * dt),
            max_speed,
        )
        new_velocities.append((new_velocity_x, new_velocity_y))
        new_positions.append((
            position_x + new_velocity_x * dt,
            position_y + new_velocity_y * dt,
        ))
    return new_positions, new_velocities
