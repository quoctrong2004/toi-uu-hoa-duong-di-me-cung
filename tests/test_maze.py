import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.maze import generate_maze, generate_dataset
from src.algorithms import solve_bfs, solve_dijkstra, solve_astar, validate_path
from src.experiment import evaluate_weight, pareto


class TestMazeAlgorithms(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(generate_maze(21, 9), generate_maze(21, 9))

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            generate_maze(10, 2)

    def test_bfs_and_dijkstra_agree(self):
        for i in range(15):
            m = generate_maze(21, 100+i)
            self.assertEqual(solve_bfs(m)['steps'], solve_dijkstra(m)['steps'])

    def test_astar_is_optimal(self):
        for i in range(20):
            m = generate_maze(31, 120+i)
            self.assertEqual(solve_astar(m, 1)['steps'], solve_bfs(m)['steps'])

    def test_path_validity(self):
        m = generate_maze(21, 7)
        for r in (solve_bfs(m), solve_dijkstra(m), solve_astar(m, 2)):
            self.assertTrue(validate_path(m, r['path']))

    def test_invalid_path_rejected(self):
        m = generate_maze(21, 7)
        self.assertFalse(validate_path(m, [(1, 1), (1, 20)]))

    def test_bad_weight(self):
        with self.assertRaises(ValueError):
            solve_astar(generate_maze(21, 10), .5)

    def test_dataset_split(self):
        with TemporaryDirectory() as tmp:
            data = generate_dataset(Path(tmp) / 'mazes.json')
            self.assertEqual(len(data), 48)
            self.assertEqual(sum(m['split'] == 'test' for m in data), 12)
            self.assertTrue(all(solve_bfs(m)['found'] for m in data))

    def test_weight_one_feasible(self):
        mazes = [generate_maze(21, i+11) for i in range(5)]
        for i,m in enumerate(mazes): m['id'] = str(i)
        refs = {m['id']: (solve_bfs(m), solve_astar(m)) for m in mazes}
        r = evaluate_weight(mazes, refs, 1.)
        self.assertTrue(r['feasible'])
        self.assertEqual(r['mean_stretch'], 1.)

    def test_pareto(self):
        rows = [{'weight': 1., 'mean_stretch': 1., 'mean_expanded': 80},
                {'weight': 2., 'mean_stretch': 1.1, 'mean_expanded': 40},
                {'weight': 3., 'mean_stretch': 1.2, 'mean_expanded': 100}]
        result = pareto(rows)
        self.assertEqual([r['pareto'] for r in result], [True, True, False])


if __name__ == '__main__':
    unittest.main()
