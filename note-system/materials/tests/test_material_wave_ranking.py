"""Synthetic tests for horizon-wave, effort-stratified material reranking."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from material_wave_ranking import plan_wave_rerank


class MaterialWaveRankingTests(unittest.TestCase):
    def test_wave_rerank_orders_quick_high_voi_ahead_of_unsliced_monographs(self):
        refs = [
            "material-protected-anchor",
            "material-monograph-course",
            "material-monograph-book",
            "material-quick-gate-slice",
            "material-quick-chapter-slice",
            "material-untouched-tail",
        ]
        reordered, summary = plan_wave_rerank(
            refs,
            [
                {
                    "material_ref": "material-monograph-course",
                    "horizon_wave": "active_sprint",
                    "effort_band": "deep_monograph",
                    "evidence_role": "foundational_reference",
                    "decision_gain_score": 88,
                    "scoped_slice_ready": False,
                },
                {
                    "material_ref": "material-monograph-book",
                    "horizon_wave": "imminent_gate",
                    "effort_band": "deep_monograph",
                    "evidence_role": "foundational_reference",
                    "decision_gain_score": 90,
                    "scoped_slice_ready": False,
                },
                {
                    "material_ref": "material-quick-gate-slice",
                    "horizon_wave": "imminent_gate",
                    "effort_band": "quick_slice",
                    "evidence_role": "load_bearing_primary",
                    "decision_gain_score": 92,
                    "blocks_active_deliverable": True,
                },
                {
                    "material_ref": "material-quick-chapter-slice",
                    "horizon_wave": "imminent_gate",
                    "effort_band": "quick_slice",
                    "evidence_role": "method_comparator",
                    "decision_gain_score": 85,
                    "scoped_slice_ready": True,
                },
            ],
            top_window_size=5,
            protected_material_refs=["material-protected-anchor"],
        )
        self.assertEqual(reordered[0], "material-protected-anchor")
        self.assertEqual(reordered[1:3], ["material-quick-gate-slice", "material-quick-chapter-slice"])
        self.assertEqual(
            set(summary["demoted_unsliced_monographs"]),
            {"material-monograph-course", "material-monograph-book"},
        )
        self.assertEqual(reordered[-1], "material-untouched-tail")
        self.assertEqual(sorted(reordered), sorted(refs))

    def test_primary_source_lineage_and_missing_load_bearing_gate(self):
        refs = ["material-generic-lecture", "material-primary-report", "material-cited-paper"]
        with self.assertRaisesRegex(ValueError, "settled via intake first"):
            plan_wave_rerank(
                refs,
                [],
                required_load_bearing_refs=["material-missing-primary"],
            )

        reordered, _ = plan_wave_rerank(
            refs,
            [
                {
                    "material_ref": "material-generic-lecture",
                    "horizon_wave": "imminent_gate",
                    "effort_band": "quick_slice",
                    "evidence_role": "secondary_or_commentary",
                    "decision_gain_score": 95,
                    "primary_source_refs": ["material-primary-report"],
                },
                {
                    "material_ref": "material-primary-report",
                    "horizon_wave": "active_sprint",
                    "effort_band": "focused_study",
                    "evidence_role": "load_bearing_primary",
                    "decision_gain_score": 90,
                    "blocks_active_deliverable": True,
                },
                {
                    "material_ref": "material-cited-paper",
                    "horizon_wave": "imminent_gate",
                    "effort_band": "focused_study",
                    "evidence_role": "load_bearing_primary",
                    "decision_gain_score": 94,
                    "blocks_active_deliverable": True,
                },
            ],
            top_window_size=3,
            required_load_bearing_refs=["material-primary-report", "material-cited-paper"],
        )
        self.assertLess(
            reordered.index("material-primary-report"),
            reordered.index("material-generic-lecture"),
        )
        self.assertEqual(reordered[0], "material-cited-paper")

    def test_orthogonal_signals_evicted_to_top_of_backlog_ahead_of_untouched_tail(self):
        refs = [f"material-item-{i:02d}" for i in range(1, 11)]
        reordered, summary = plan_wave_rerank(
            refs,
            [
                {
                    "material_ref": "material-item-01",
                    "horizon_wave": "imminent_gate",
                    "effort_band": "quick_slice",
                    "evidence_role": "orthogonal_signal",
                    "decision_gain_score": 88,
                },
                {
                    "material_ref": "material-item-02",
                    "horizon_wave": "active_sprint",
                    "effort_band": "quick_slice",
                    "evidence_role": "orthogonal_signal",
                    "decision_gain_score": 82,
                },
                {
                    "material_ref": "material-item-06",
                    "horizon_wave": "imminent_gate",
                    "effort_band": "focused_study",
                    "evidence_role": "load_bearing_primary",
                    "decision_gain_score": 95,
                    "blocks_active_deliverable": True,
                },
            ],
            top_window_size=4,
            max_orthogonal_in_top_window=0,
        )
        self.assertEqual(summary["orthogonal_in_top_window"], 0)
        self.assertNotIn("material-item-01", reordered[:4])
        self.assertNotIn("material-item-02", reordered[:4])
        # Immediately outside top_window_size=4 (ranks 5 and 6), ahead of remaining untouched tail:
        self.assertEqual(reordered[4:6], ["material-item-01", "material-item-02"])
        self.assertEqual(sorted(reordered), sorted(refs))


if __name__ == "__main__":
    unittest.main()
