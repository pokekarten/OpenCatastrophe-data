from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "research-scripts" / "pcold_ingarch_prequential.py"
SPEC = importlib.util.spec_from_file_location("pcold_ingarch_prequential", SCRIPT)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


class PCOLDIngarchPrequentialTests(unittest.TestCase):
    def test_ingarch_recursion_hand_values(self) -> None:
        hist = np.array([2.0, 5.0, 1.0])
        lam = m.ingarch_lambda(hist, omega=1.0, a=0.2, b=0.3)
        np.testing.assert_allclose(lam, np.array([2.0, 2.0, 2.6]), rtol=0.0, atol=1e-15)
        self.assertAlmostEqual(m.ingarch_forecast(hist, 1.0, 0.2, 0.3), 1.98, places=14)

    def test_transform_obeys_frozen_domain(self) -> None:
        for z in [
            np.array([0.0, 0.0, 0.0]),
            np.array([-5.0, 12.0, -12.0]),
            np.array([5.0, -12.0, 12.0]),
        ]:
            omega, a, b = m.ingarch_transform(z)
            self.assertGreater(omega, 0.0)
            self.assertGreaterEqual(a, 0.0)
            self.assertGreaterEqual(b, 0.0)
            self.assertLessEqual(a + b, m.PERSISTENCE_CAP)

    def test_zero_dynamics_is_constant_poisson_mean(self) -> None:
        hist = np.array([0.0, 3.0, 7.0, 1.0])
        lam = m.ingarch_lambda(hist, omega=2.5, a=0.0, b=0.0)
        np.testing.assert_array_equal(lam, np.full(len(hist), 2.5))
        self.assertEqual(m.ingarch_forecast(hist, 2.5, 0.0, 0.0), 2.5)

    def test_nb2_tiny_dispersion_matches_poisson(self) -> None:
        y = np.array([0.0, 1.0, 4.0, 9.0])
        mu = np.array([0.25, 1.2, 3.5, 8.0])
        np.testing.assert_allclose(
            m.nb2_logpmf(y, mu, 1e-12),
            m.poisson_logpmf(y, mu),
            rtol=0.0,
            atol=0.0,
        )

    def test_prequential_history_firewall(self) -> None:
        y = np.arange(20.0)
        origin = 11
        idx = m.history_indices_for_origin(origin)
        np.testing.assert_array_equal(idx, np.arange(origin))
        baseline = y[idx].copy()
        changed = y.copy()
        changed[origin:] += 10000.0
        np.testing.assert_array_equal(baseline, changed[idx])
        self.assertNotIn(origin, idx)

    def test_score_start_index_is_199_month_warmup(self) -> None:
        lo = m.month_key(*m.EXPECTED_MIN_MONTH)
        hi = m.month_key(*m.EXPECTED_MAX_MONTH)
        pairs = [m.month_pair(k) for k in range(lo, hi + 1)]
        start = m.score_start_index(pairs)
        self.assertEqual(start, 199)
        self.assertEqual(len(pairs) - start, 215)
        self.assertEqual(pairs[start], (2005, 1))
        self.assertEqual(pairs[-1], (2022, 11))

    def test_stable_nb2_is_finite_at_zero_tiny_nonboundary(self) -> None:
        y = np.array([0.0, 0.0, 1.0])
        mu = np.array([0.1, 10.0, 2.0])
        ll = m.nb2_logpmf(y, mu, 1e-9)
        self.assertTrue(np.all(np.isfinite(ll)))

    def test_bootstrap_is_deterministic(self) -> None:
        x = np.linspace(-1.0, 2.0, 48)
        a = m.moving_block_bootstrap(x, block=12, reps=500, seed=m.SEED)
        b = m.moving_block_bootstrap(x, block=12, reps=500, seed=m.SEED)
        self.assertEqual(a, b)
        self.assertAlmostEqual(a["mean_improvement"], float(x.mean()), places=15)


if __name__ == "__main__":
    unittest.main()
