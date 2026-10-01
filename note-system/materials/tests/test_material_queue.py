import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "material_queue", Path(__file__).resolve().parents[1] / "material_queue.py"
)
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def catalog():
    return {
        "schema_version": queue.SCHEMA,
        "queue_id": "external",
        "top_window_size": 30,
        "entries": [
            {
                "material_ref": "material-demo",
                "title": "A public source",
                "sources": ["https://example.org/paper"],
                "tier": "A",
                "lifecycle": "candidate",
                "read_scope": "recorded_review",
                "note": "",
                "queue_rank": 1,
            }
        ],
    }


class PublicQueueBoundary(unittest.TestCase):
    def test_ranked_and_unranked_remain_distinct(self):
        data = catalog()
        second = copy.deepcopy(data["entries"][0])
        second.update(
            material_ref="material-next", title="Another source", queue_rank=None
        )
        data["entries"].append(second)
        pages, counts = queue.render(data)
        self.assertEqual(
            counts, {"materials": 2, "ranked": 1, "unranked": 1, "top_window": 1}
        )
        self.assertNotIn("Another source", pages["QUEUE.md"])
        self.assertIn("Another source", pages["CANDIDATES.md"])

    def test_duplicate_urls_do_not_delete_stable_records(self):
        data = catalog()
        second = copy.deepcopy(data["entries"][0])
        second.update(material_ref="material-other", queue_rank=2)
        data["entries"].append(second)
        self.assertEqual(queue.validate(data)["ranked"], 2)

    def test_duplicate_ids_and_gapped_ranks_are_rejected(self):
        for modification in ("duplicate", "gap", "bool"):
            with self.subTest(modification=modification):
                data = catalog()
                if modification == "duplicate":
                    data["entries"].append(copy.deepcopy(data["entries"][0]))
                else:
                    data["entries"][0]["queue_rank"] = (
                        3 if modification == "gap" else True
                    )
                with self.assertRaises(ValueError):
                    queue.validate(data)

    def test_raw_private_fields_cannot_be_carried_through(self):
        data = catalog()
        data["entries"][0]["raw_body"] = "not part of the public card contract"
        with self.assertRaises(ValueError):
            queue.validate(data)

    def test_archived_record_cannot_enter_current_public_queue(self):
        data = catalog()
        data["entries"][0]["lifecycle"] = "archived"
        with self.assertRaises(ValueError):
            queue.validate(data)

    def test_local_paths_credentials_and_share_queries_are_rejected(self):
        sources = [
            "/home/example/private.md",
            "file:///private/example.md",
            "https://name:pass@example.org/paper",
            "https://localhost/paper",
            "https://127.0.0.1/paper",
            "https://service.internal/paper",
            "https://example.org/paper?access_token=value",
            "https://example.org/paper#login-secret",
            "./distributed-systems-for-loopx/../../private.md",
            "./distributed-systems-for-loopx/%2e%2e/private.md",
        ]
        for source in sources:
            with self.subTest(source=source), self.assertRaises(ValueError):
                queue.validate_source(source)

    def test_legitimate_url_paths_and_resource_ids_survive(self):
        for source in [
            "https://example.org/news/home/article",
            "https://openreview.net/forum?id=paper-id",
            "https://www.youtube.com/watch?v=video-id",
            "./distributed-systems-for-loopx/recovery_lab.py",
        ]:
            queue.validate_source(source)

    def test_table_delimiters_and_arrows_do_not_break_rendering(self):
        data = catalog()
        data["entries"][0]["title"] = "A | B -> C [example]"
        pages, _ = queue.render(data)
        self.assertIn(r"A \| B -> C \[example\]", pages["QUEUE.md"])


if __name__ == "__main__":
    unittest.main()
