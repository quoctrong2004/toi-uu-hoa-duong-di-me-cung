"""BFS, Dijkstra va (Weighted) A*. Don vi chi phi: so buoc."""
from collections import deque
from heapq import heappush, heappop
from itertools import count
from math import inf

DIRECTIONS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def neighbors(grid, pos):
    y, x = pos
    for dy, dx in DIRECTIONS:
        ny, nx = y + dy, x + dx
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == 0:
            yield ny, nx


def make_path(previous, goal):
    path = [goal]
    while previous[path[-1]] is not None:
        path.append(previous[path[-1]])
    path.reverse()
    return path


def solve_bfs(maze):
    grid = maze['grid']
    start, goal = tuple(maze['start']), tuple(maze['goal'])
    queue = deque([start])
    prev = {start: None}
    expanded = 0
    while queue:
        u = queue.popleft()
        expanded += 1
        if u == goal:
            path = make_path(prev, goal)
            return {'path': path, 'steps': len(path) - 1, 'expanded': expanded,
                    'found': True}
        for v in neighbors(grid, u):
            if v not in prev:
                prev[v] = u
                queue.append(v)
    return {'path': [], 'steps': None, 'expanded': expanded, 'found': False}


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def solve_astar(maze, weight=1.0):
    if weight < 1.0:
        raise ValueError('weight can >= 1')
    grid = maze['grid']
    start, goal = tuple(maze['start']), tuple(maze['goal'])
    tickets = count()
    # f = g + w*h; tie-break on larger g for determinism.
    queue = [(weight * manhattan(start, goal), 0, next(tickets), start)]
    distance = {start: 0}
    prev = {start: None}
    expanded = 0
    expanded_history = []
    while queue:
        _, neg_g, _, u = heappop(queue)
        g = -neg_g
        if g != distance[u]:
            continue
        expanded += 1
        expanded_history.append((expanded, g, manhattan(u, goal)))
        if u == goal:
            path = make_path(prev, goal)
            return {'path': path, 'steps': len(path) - 1, 'expanded': expanded,
                    'found': True, 'history': expanded_history}
        for v in neighbors(grid, u):
            ng = g + 1
            if ng < distance.get(v, inf):
                distance[v] = ng
                prev[v] = u
                f = ng + weight * manhattan(v, goal)
                heappush(queue, (f, -ng, next(tickets), v))
    return {'path': [], 'steps': None, 'expanded': expanded, 'found': False,
            'history': expanded_history}


def solve_dijkstra(maze):
    start, goal = tuple(maze['start']), tuple(maze['goal'])
    grid = maze['grid']
    heap = [(0, start)]
    dist = {start: 0}
    previous = {start: None}
    expanded = 0
    while heap:
        d, u = heappop(heap)
        if d != dist[u]:
            continue
        expanded += 1
        if u == goal:
            p = make_path(previous, goal)
            return {'path': p, 'steps': d, 'expanded': expanded, 'found': True}
        for v in neighbors(grid, u):
            nd = d + 1
            if nd < dist.get(v, inf):
                dist[v] = nd
                previous[v] = u
                heappush(heap, (nd, v))
    return {'path': [], 'steps': None, 'expanded': expanded, 'found': False}


def validate_path(maze, path):
    if not path or tuple(path[0]) != tuple(maze['start']) or tuple(path[-1]) != tuple(maze['goal']):
        return False
    grid = maze['grid']
    for p in path:
        y, x = p
        if not (0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] == 0):
            return False
    return all(manhattan(a, b) == 1 for a, b in zip(path, path[1:]))
