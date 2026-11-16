"""Tao me cung co the tai tao. 0 = duong di, 1 = tuong."""
import json
import random
from pathlib import Path


def generate_maze(size, seed, loop_rate=0.13):
    if size < 7 or size % 2 == 0:
        raise ValueError("size phai la so le >= 7")
    rng = random.Random(seed)
    a = [[1] * size for _ in range(size)]
    start = (1, 1)
    stack = [start]
    a[1][1] = 0
    while stack:
        y, x = stack[-1]
        options = []
        for dy, dx in ((0, 2), (2, 0), (0, -2), (-2, 0)):
            ny, nx = y + dy, x + dx
            if 1 <= ny < size - 1 and 1 <= nx < size - 1 and a[ny][nx] == 1:
                options.append((ny, nx, dy, dx))
        if options:
            ny, nx, dy, dx = rng.choice(options)
            a[y + dy // 2][x + dx // 2] = 0
            a[ny][nx] = 0
            stack.append((ny, nx))
        else:
            stack.pop()
    # Them cac ngo di vong: cho phep nhieu loi di, khong chi co mot duong.
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            if a[y][x] == 1 and rng.random() < loop_rate:
                if (a[y - 1][x] == 0 and a[y + 1][x] == 0) or (a[y][x - 1] == 0 and a[y][x + 1] == 0):
                    a[y][x] = 0
    goal = (size - 2, size - 2)
    assert a[goal[0]][goal[1]] == 0
    return {'size': size, 'seed': seed, 'loop_rate': loop_rate, 'grid': a,
            'start': list(start), 'goal': list(goal)}


def generate_dataset(path, seed=2026):
    data = []
    for i in range(48):
        size = 21 if i % 2 == 0 else 31
        maze = generate_maze(size, seed + i * 101, loop_rate=(0.08, 0.14, 0.20)[i % 3])
        maze['id'] = f'M{i + 1:02d}'
        maze['split'] = 'development' if i < 36 else 'test'
        data.append(maze)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    return data


def load_dataset(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
