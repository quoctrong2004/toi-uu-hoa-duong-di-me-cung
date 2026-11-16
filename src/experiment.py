"""Thuc nghiem cong bang, khoa test; log CSV/JSON va do thi."""
import csv
import json
import random
import statistics as stats
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from .algorithms import solve_astar, solve_bfs, solve_dijkstra, validate_path
from .maze import generate_dataset, load_dataset

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / 'data' / 'mazes.json'
RES = BASE / 'results'
FIG = BASE / 'figures'
SEARCH_BUDGET = 24
SEEDS = (11, 22, 33, 44)
MAX_STRETCH = 1.15


def save_csv(path, rows):
    rows = list(rows)
    if not rows:
        return
    with Path(path).open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def ref_results(mazes):
    data = {}
    for maze in mazes:
        b = solve_bfs(maze)
        d = solve_dijkstra(maze)
        a = solve_astar(maze)
        assert b['found'] and d['found'] and a['found']
        assert b['steps'] == d['steps'] == a['steps']
        for r in (b, d, a):
            assert validate_path(maze, r['path'])
        data[maze['id']] = (b, a)
    return data


def evaluate_weight(mazes, refs, weight):
    stretch = []
    expanded = []
    ratios = []
    for maze in mazes:
        result = solve_astar(maze, weight)
        b = refs[maze['id']][0]
        if not result['found'] or not validate_path(maze, result['path']):
            raise AssertionError('Khong tim duoc duong hop le')
        stretch.append(result['steps'] / b['steps'])
        expanded.append(result['expanded'])
        ratios.append(result['expanded'] / b['expanded'])
    return {'weight': round(weight, 3), 'n_mazes': len(mazes),
            'mean_stretch': stats.mean(stretch), 'max_stretch': max(stretch),
            'mean_expanded': stats.mean(expanded), 'expanded_vs_bfs': stats.mean(ratios),
            'feasible': max(stretch) <= MAX_STRETCH + 1e-12,
            'optimal_rate': sum(v == 1.0 for v in stretch) / len(stretch)}


def winner(rows):
    eligible = [r for r in rows if r['feasible']]
    if not eligible:
        raise RuntimeError('Khong co cau hinh thoa rang buoc')
    return min(eligible, key=lambda r: (r['expanded_vs_bfs'], r['max_stretch'], r['weight']))


def pareto(rows):
    # Chi xet cac cap objective: mean_stretch (min), mean_expanded (min).
    unique = list({r['weight']: r for r in rows}.values())
    for a in unique:
        a['pareto'] = not any((b['mean_stretch'] <= a['mean_stretch'] + 1e-12 and
                                b['mean_expanded'] <= a['mean_expanded'] + 1e-12 and
                                (b['mean_stretch'] < a['mean_stretch'] - 1e-12 or
                                 b['mean_expanded'] < a['mean_expanded'] - 1e-12))
                               for b in unique if b is not a)
    return sorted(unique, key=lambda z: z['weight'])


def plot_maze(maze, paths, path):
    grid = maze['grid']
    fig, ax = plt.subplots(figsize=(6.6, 6.6))
    ax.imshow(grid, cmap=ListedColormap(['#f7fafc', '#233445']), vmin=0, vmax=1)
    for p, color, name in paths:
        xs = [v[1] for v in p]
        ys = [v[0] for v in p]
        ax.plot(xs, ys, color=color, lw=2.5, alpha=.88, label=name)
    sy, sx = maze['start']; gy, gx = maze['goal']
    ax.scatter([sx, gx], [sy, gy], c=['#219b78', '#cf594d'], s=75, zorder=4, edgecolors='white')
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"Maze {maze['id']} - {maze['size']} x {maze['size']}", fontsize=12)
    ax.legend(loc='lower center', bbox_to_anchor=(.5, -0.07), ncol=2, frameon=False)
    fig.tight_layout(); fig.savefig(path, dpi=170, bbox_inches='tight'); plt.close(fig)


def plot_search(trials, path):
    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    for method, seed, color in [('Grid', 0, '#0d7377'), ('Random', SEEDS[0], '#d47a39')]:
        xs, ys = [], []
        best = float('inf')
        for r in [r for r in trials if r['method'] == method and r['seed'] == seed]:
            if r['feasible']:
                best = min(best, r['expanded_vs_bfs'])
            xs.append(r['trial']); ys.append(best if best < float('inf') else float('nan'))
        ax.step(xs, ys, where='post', lw=2, label=f'{method} (seed {seed})', color=color)
    ax.set(xlabel='So lan thu (trial)', ylabel='So o mo rong / BFS (trung binh)',
           title='Search history: cau hinh kha thi tot nhat den hien tai')
    ax.grid(alpha=.2); ax.legend(); fig.tight_layout(); fig.savefig(path, dpi=165); plt.close(fig)


def plot_pareto(front, path):
    fig, ax = plt.subplots(figsize=(8.1, 4.5))
    bad = [r for r in front if not r['pareto']]
    good = [r for r in front if r['pareto']]
    ax.scatter([r['mean_stretch'] for r in bad], [r['mean_expanded'] for r in bad],
               s=43, c='#b6c1cc', alpha=.72, label='Dominated')
    ax.scatter([r['mean_stretch'] for r in good], [r['mean_expanded'] for r in good],
               s=64, c='#057e79', label='Non-dominated')
    for r in good:
        ax.annotate(f"w={r['weight']:.2f}", (r['mean_stretch'], r['mean_expanded']),
                    xytext=(4,4), textcoords='offset points', fontsize=7)
    ax.set(xlabel='Do dai duong di / toi uu (mean; thap hon tot hon)',
           ylabel='So o mo rong trung binh (thap hon tot hon)', title='Pareto: do dai va cong suc tim kiem')
    ax.grid(alpha=.2); ax.legend(); fig.tight_layout(); fig.savefig(path, dpi=165); plt.close(fig)


def plot_sensitivity(agg, path):
    fig, ax = plt.subplots(figsize=(7.9, 4.3))
    ax.plot([r['weight'] for r in agg], [r['max_stretch'] for r in agg], color='#d47a39', lw=2)
    ax.set(xlabel='Trong so heuristic w', ylabel='Ty le duong dai nhat / toi uu (max tren dev)',
           title='Do nhay: w va he so do dai toi da tren development')
    ax.axhline(MAX_STRETCH, ls='--', lw=1, color='#b95b52', label='Nguong kha thi tren tung maze: 1.15')
    ax.grid(alpha=.2); ax.legend(); fig.tight_layout(); fig.savefig(path, dpi=165); plt.close(fig)


def run():
    for folder in (RES, FIG): folder.mkdir(exist_ok=True, parents=True)
    mazes = generate_dataset(DATA)
    dev = [m for m in mazes if m['split'] == 'development']
    test = [m for m in mazes if m['split'] == 'test']
    refs = ref_results(mazes)
    # Khoa test: khong tham gia vao viec tim weight hay xet Pareto.
    weights_grid = [round(1.0 + i * .1, 2) for i in range(SEARCH_BUDGET)]
    universe = [round(1.0 + i * .05, 2) for i in range(47)]
    trials = []
    for method, seed, choices in ([('Grid', 0, weights_grid)] + [
            ('Random', s, random.Random(s).sample(universe, SEARCH_BUDGET)) for s in SEEDS]):
        best_feasible = float('inf')
        for i, w in enumerate(choices, 1):
            tic = time.perf_counter()
            result = evaluate_weight(dev, refs, w)
            runtime = (time.perf_counter() - tic) * 1000
            if result['feasible']:
                best_feasible = min(best_feasible, result['expanded_vs_bfs'])
            trials.append({'method': method, 'seed': seed, 'trial': i, **result,
                           'search_ms': round(runtime, 3),
                           'best_so_far': round(best_feasible, 5) if best_feasible < float('inf') else ''})
    save_csv(RES / 'trial_history.csv', trials)
    grid = [r for r in trials if r['method'] == 'Grid']
    rando = [r for r in trials if r['method'] == 'Random']
    grid_best, random_best = winner(grid), winner([r for r in rando if r['seed'] == SEEDS[0]])
    candidates = [grid_best, random_best]
    # So sanh Grid 24 trial voi Random seed chinh 24 trial. 3 seed con lai chi do do on dinh.
    # Chon tren development, khong nhin tap test.
    selected = min(candidates, key=lambda r: (r['expanded_vs_bfs'], r['max_stretch'], r['weight']))
    front = pareto(trials)
    save_csv(RES / 'pareto_candidates.csv', front)
    # Thuat toan A* w=1 bao dam ngan nhat, Weighted A* co nguy co duong dai hon.
    test_rows = []
    for maze in test:
        bfs = refs[maze['id']][0]
        for method, w in [('BFS', None), ('A*', 1.0), ('Weighted A*', selected['weight'])]:
            durations = []
            for _ in range(25):
                tic = time.perf_counter()
                sol = solve_bfs(maze) if method == 'BFS' else solve_astar(maze, w)
                durations.append((time.perf_counter() - tic) * 1000)
            elapsed_ms = stats.median(durations)
            assert validate_path(maze, sol['path'])
            test_rows.append({'maze_id': maze['id'], 'size': maze['size'], 'method': method,
                              'weight': w if w is not None else '', 'steps': sol['steps'],
                              'optimal_steps': bfs['steps'], 'stretch': round(sol['steps']/bfs['steps'], 5),
                              'expanded': sol['expanded'], 'runtime_ms': round(elapsed_ms, 5),
                              'feasible': sol['steps']/bfs['steps'] <= MAX_STRETCH + 1e-12})
    save_csv(RES / 'test_results.csv', test_rows)
    methods = ['BFS', 'A*', 'Weighted A*']
    summary = {}
    for method in methods:
        group = [r for r in test_rows if r['method'] == method]
        summary[method] = {
            'n': len(group), 'mean_steps': round(stats.mean(r['steps'] for r in group), 3),
            'mean_stretch': round(stats.mean(r['stretch'] for r in group), 5),
            'max_stretch': round(max(r['stretch'] for r in group), 5),
            'optimal_rate': round(sum(r['stretch'] == 1 for r in group)/len(group), 5),
            'mean_expanded': round(stats.mean(r['expanded'] for r in group), 3),
            'mean_runtime_ms': round(stats.mean(r['runtime_ms'] for r in group), 5),
            'feasible_rate': round(sum(r['feasible'] for r in group)/len(group), 5)
        }
    random_by_seed = [winner([r for r in rando if r['seed'] == seed]) for seed in SEEDS]
    stability = [{'seed': r['seed'], 'best_weight': r['weight'],
                  'best_expanded_vs_bfs': r['expanded_vs_bfs'],
                  'max_stretch': r['max_stretch']} for r in random_by_seed]
    save_csv(RES / 'random_stability.csv', stability)
    import platform, sys
    summary_json = {
        'title': 'Shortest path in maze: BFS, A* and Weighted A*', 'seed_dataset': 2026,
        'python_version': sys.version.split()[0], 'platform': platform.platform(),
        'development_mazes': len(dev), 'test_mazes': len(test),
        'search_budget_per_run': SEARCH_BUDGET, 'random_seeds': SEEDS, 'primary_random_seed': SEEDS[0],
        'max_allowed_stretch_per_maze': MAX_STRETCH,
        'best_grid': {k: grid_best[k] for k in ('weight','expanded_vs_bfs','mean_stretch','max_stretch')},
        'best_random': {k: random_best[k] for k in ('seed','weight','expanded_vs_bfs','mean_stretch','max_stretch')},
        'selected_from_development': {k: selected[k] for k in ('method','seed','weight','expanded_vs_bfs','mean_stretch','max_stretch')},
        'pareto_count': sum(r['pareto'] for r in front),
        'random_stability_expanded_ratio_mean': stats.mean(r['best_expanded_vs_bfs'] for r in stability),
        'random_stability_expanded_ratio_std': stats.stdev(r['best_expanded_vs_bfs'] for r in stability),
        'test': summary,
        'note': 'BFS va A* (w=1, Manhattan) dam bao duong di ngan nhat; Weighted A* khong dam bao.'
    }
    (RES / 'summary.json').write_text(json.dumps(summary_json, indent=2, ensure_ascii=False), encoding='utf-8')
    example = test[0]
    paths = [(solve_bfs(example)['path'], '#e1a246', 'BFS shortest path'),
             (solve_astar(example, selected['weight'])['path'], '#148781', 'Weighted A*')]
    plot_maze(example, paths, FIG / '01_maze_paths.png')
    plot_search(trials, FIG / '02_search_history.png')
    plot_pareto(front, FIG / '03_pareto.png')
    plot_sensitivity(front, FIG / '04_sensitivity.png')
    print(json.dumps(summary_json, indent=2, ensure_ascii=False))
    return summary_json

if __name__ == '__main__':
    run()
