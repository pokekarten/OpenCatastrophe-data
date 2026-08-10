# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
import unittest

from scripts.hydrology_metrics import MetricInputError, modified_kge_prime


class ModifiedKgePrimeTests(unittest.TestCase):
    def test_perfect_agreement_is_one(self) -> None:
        values = [1.0, 2.0, 4.0, 8.0]
        self.assertAlmostEqual(modified_kge_prime(values, values), 1.0)

    def test_uses_coefficient_of_variation_not_standard_deviation_ratio(self) -> None:
        observed = [1.0, 2.0, 3.0]
        simulated = [2.0, 3.0, 4.0]

        expected = 1.0 - math.sqrt((0.5) ** 2 + (1.0 / 3.0) ** 2)
        self.assertAlmostEqual(modified_kge_prime(simulated, observed), expected)
        self.assertNotAlmostEqual(modified_kge_prime(simulated, observed), 0.5)

    def test_multiplicative_bias_preserves_variability_component(self) -> None:
        observed = [1.0, 2.0, 4.0, 8.0]
        simulated = [2.0, 4.0, 8.0, 16.0]
        self.assertAlmostEqual(modified_kge_prime(simulated, observed), 0.0)

    def test_rejects_unequal_lengths(self) -> None:
        with self.assertRaisesRegex(MetricInputError, "equal length"):
            modified_kge_prime([1.0, 2.0], [1.0])

    def test_rejects_non_finite_values(self) -> None:
        with self.assertRaisesRegex(MetricInputError, "finite numeric"):
            modified_kge_prime([1.0, math.nan], [1.0, 2.0])
        with self.assertRaisesRegex(MetricInputError, "finite numeric"):
            modified_kge_prime([1.0, 2.0], [1.0, math.inf])

    def test_rejects_zero_mean(self) -> None:
        with self.assertRaisesRegex(MetricInputError, "non-zero means"):
            modified_kge_prime([-1.0, 1.0], [1.0, 2.0])

    def test_rejects_zero_variance(self) -> None:
        with self.assertRaisesRegex(MetricInputError, "non-zero variance"):
            modified_kge_prime([2.0, 2.0], [1.0, 2.0])

    def test_rejects_single_pair(self) -> None:
        with self.assertRaisesRegex(MetricInputError, "at least two"):
            modified_kge_prime([1.0], [1.0])


if __name__ == "__main__":
    unittest.main()
