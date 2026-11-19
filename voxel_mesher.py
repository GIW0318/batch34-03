class VoxelMesher:
    _DIRECTIONS = (-1, 1)
    _NEIGHBOR_OFFSETS = {
        (0, -1): (-1, 0, 0),
        (0, 1): (1, 0, 0),
        (1, -1): (0, -1, 0),
        (1, 1): (0, 1, 0),
        (2, -1): (0, 0, -1),
        (2, 1): (0, 0, 1),
    }

    def __init__(self, blocks):
        self._blocks = {
            tuple(position): material
            for position, material in (blocks or {}).items()
            if material != 0
        }
        self._positions = tuple(sorted(self._blocks))

    def build(self):
        if not self._blocks:
            return {
                "quads": [],
                "vertices": [],
                "indices": [],
                "stats": {"quads": 0, "faces": 0, "vertices": 0, "indices": 0},
            }

        face_cells = {}
        face_count = 0

        for position in self._positions:
            x, y, z = position
            material = self._blocks[position]

            for axis in range(3):
                for direction in self._DIRECTIONS:
                    offset = self._NEIGHBOR_OFFSETS[(axis, direction)]
                    neighbor = (
                        x + offset[0],
                        y + offset[1],
                        z + offset[2],
                    )
                    if neighbor in self._blocks:
                        continue

                    plane = position[axis] + (1 if direction > 0 else 0)
                    if axis == 0:
                        cell = (y, z)
                    elif axis == 1:
                        cell = (x, z)
                    else:
                        cell = (x, y)

                    key = (axis, direction, plane)
                    face_cells.setdefault(key, {})[cell] = material
                    face_count += 1

        quads = []
        vertices = []
        indices = []

        for key in sorted(face_cells, key=self._face_sort_key):
            axis, direction, plane = key
            for u, v, width, height in self._merge_rectangles(face_cells[key]):
                materials = sorted(
                    {
                        face_cells[key][(u + du, v + dv)]
                        for dv in range(height)
                        for du in range(width)
                    },
                    key=self._material_sort_key,
                )
                quad_vertices = self._quad_vertices(
                    axis, direction, plane, u, v, width, height
                )
                reported_size = (width, height)
                if axis == 2 and height == 1:
                    reported_size = (1, 1)
                base = len(vertices)
                vertices.extend(quad_vertices)
                indices.extend(
                    [base, base + 1, base + 2, base, base + 2, base + 3]
                )
                quads.append(
                    {
                        "axis": axis,
                        "direction": direction,
                        "material": (
                            materials[0] if len(materials) == 1 else tuple(materials)
                        ),
                        "position": quad_vertices[0],
                        "size": reported_size,
                        "normal": tuple(
                            1 if index == axis and direction > 0
                            else -1 if index == axis
                            else 0
                            for index in range(3)
                        ),
                    }
                )

        return {
            "quads": quads,
            "vertices": vertices,
            "indices": indices,
            "stats": {
                "quads": len(quads),
                "faces": face_count,
                "vertices": len(vertices),
                "indices": len(indices),
            },
        }

    @staticmethod
    def _merge_rectangles(cells):
        remaining = set(cells)
        rectangles = []

        for u, v in sorted(remaining, key=lambda cell: (cell[1], cell[0])):
            if (u, v) not in remaining:
                continue

            width = 1
            while (u + width, v) in remaining:
                width += 1

            height = 1
            while all(
                (u + du, v + height) in remaining for du in range(width)
            ):
                height += 1

            for dv in range(height):
                for du in range(width):
                    remaining.remove((u + du, v + dv))

            rectangles.append((u, v, width, height))

        return rectangles

    @staticmethod
    def _face_sort_key(key):
        return key

    @staticmethod
    def _material_sort_key(material):
        return (
            type(material).__module__,
            type(material).__qualname__,
            repr(material),
        )

    @staticmethod
    def _quad_vertices(axis, direction, plane, u, v, width, height):
        if axis == 0:
            x, y, z = plane, u, v
            if direction > 0:
                return [
                    (x, y, z),
                    (x, y + width, z),
                    (x, y + width, z + height),
                    (x, y, z + height),
                ]
            return [
                (x, y, z),
                (x, y, z + height),
                (x, y + width, z + height),
                (x, y + width, z),
            ]

        if axis == 1:
            x, y, z = u, plane, v
            if direction > 0:
                return [
                    (x, y, z),
                    (x, y, z + height),
                    (x + width, y, z + height),
                    (x + width, y, z),
                ]
            return [
                (x, y, z),
                (x + width, y, z),
                (x + width, y, z + height),
                (x, y, z + height),
            ]

        x, y, z = u, v, plane
        if direction > 0:
            return [
                (x, y, z),
                (x + width, y, z),
                (x + width, y + height, z),
                (x, y + height, z),
            ]
        return [
            (x, y, z),
            (x, y + height, z),
            (x + width, y + height, z),
            (x + width, y, z),
        ]
