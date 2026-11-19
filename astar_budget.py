import heapq


def _validate_point(point, grid, rows, cols, label):
    if not isinstance(point, (tuple, list)) or len(point) != 2:
        raise ValueError(f"{label} must be a (row, col) tuple")
    row, col = point
    if not isinstance(row, int) or not isinstance(col, int) or isinstance(row, bool) or isinstance(col, bool):
        raise ValueError(f"{label} coordinates must be integers")
    if not (0 <= row < rows and 0 <= col < cols):
        raise ValueError(f"{label} is outside the grid")
    if grid[row][col] == "#":
        raise ValueError(f"{label} must not be a wall")
    return (row, col)


def astar(grid, start, goal, max_expansions=1000, tie_break="h"):
    if not isinstance(grid, (list, tuple)) or len(grid) == 0:
        raise ValueError("grid must be a non-empty list of equal-length strings")
    cols = len(grid[0])
    if cols == 0 or not all(isinstance(row, str) and len(row) == cols for row in grid):
        raise ValueError("grid must be a non-empty list of equal-length strings")

    if not isinstance(max_expansions, int) or isinstance(max_expansions, bool) or max_expansions <= 0:
        raise ValueError("max_expansions must be a positive integer")
    if tie_break not in ("h", "fifo"):
        raise ValueError("tie_break must be 'h' or 'fifo'")

    rows = len(grid)
    start = _validate_point(start, grid, rows, cols, "start")
    goal = _validate_point(goal, grid, rows, cols, "goal")

    def heuristic(point):
        return abs(point[0] - goal[0]) + abs(point[1] - goal[1])

    if start == goal:
        return {"path": [start], "cost": 0, "expanded": 0, "complete": True}

    g_score = {start: 0}
    came_from = {}
    closed = set()
    open_heap = []
    sequence = 0

    if tie_break == "h":
        initial_key = (heuristic(start), heuristic(start), sequence)
    else:
        initial_key = (heuristic(start), sequence)
    heapq.heappush(open_heap, (initial_key, start))

    expanded = 0
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    while open_heap and expanded < max_expansions:
        _, current = heapq.heappop(open_heap)
        if current in closed:
            continue

        expanded += 1
        closed.add(current)
        current_g = g_score[current]

        if current == goal:
            path = [current]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return {
                "path": path,
                "cost": current_g,
                "expanded": expanded,
                "complete": True,
            }

        current_row, current_col = current

        for delta_row, delta_col in directions:
            neighbor = (current_row + delta_row, current_col + delta_col)
            n_row, n_col = neighbor
            if not (0 <= n_row < rows and 0 <= n_col < cols):
                continue
            if grid[n_row][n_col] == "#":
                continue

            tentative_g = current_g + 1
            if tentative_g >= g_score.get(neighbor, float("inf")):
                continue

            g_score[neighbor] = tentative_g
            came_from[neighbor] = current

            sequence += 1
            h_value = heuristic(neighbor)
            if tie_break == "h":
                key = (tentative_g + h_value, h_value, sequence)
            else:
                key = (tentative_g + h_value, sequence)
            heapq.heappush(open_heap, (key, neighbor))

    if open_heap:
        for _, queued_point in open_heap:
            if queued_point not in closed:
                return {"path": None, "cost": None, "expanded": expanded, "complete": False}

    return {"path": None, "cost": None, "expanded": expanded, "complete": True}
