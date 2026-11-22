import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from search_index import build, open_index, search


class SearchIndexTest(unittest.TestCase):
    def test_keyword_search_fills_limit_across_grouped_batches(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cases = root / "in_delhi_judgments.parquet"
            pq.write_table(pa.Table.from_pylist(
                [{"case_id": "case-a", "title": "Termination notice", "text": "termination notice"}] * 110
                + [{"case_id": "case-b", "title": "Second case", "text": "termination notice"}]
            ), cases)
            build([cases], root / "index", threads=1)
            matches = search(open_index(root / "index"), "termination notice", limit=2)
            self.assertEqual([match["group"][0] for match in matches],
                             ["judgment:case-a", "judgment:case-b"])

    def test_exact_lookup_preserves_numeric_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            acts = root / "in_central_legislation.parquet"
            pq.write_table(pa.Table.from_pylist([
                {"act_id": "act-a", "title": "Example Act", "section_number": section, "text": section}
                for section in ("2(1)", "21")
            ]), acts)
            build([acts], root / "index", threads=1)
            index = open_index(root / "index")
            for section in ("2(1)", "21"):
                matches = search(index, "Example Act Section " + section, exact=True)
                self.assertEqual([match["section"][0] for match in matches], [section])

    def test_resume_filters_and_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cases = root / "in_delhi_judgments.parquet"
            acts = root / "in_central_legislation.parquet"
            matters = root / "in_cat_tribunal_matters.parquet"
            pq.write_table(pa.Table.from_pylist([{
                "case_id": "case-a", "title": "An Example Case",
                "citation": "[1979] 3 S.C.R. 453", "court_code": "DHC",
                "text": "Context: termination notice", "text_original": "termination notice",
                "decision_date": "1979-03-06", "page_start": 4,
            }]), cases)
            pq.write_table(pa.Table.from_pylist([{
                "act_id": "act-a", "title": "Example Act", "section_number": "2(q)",
                "text": "termination notice", "jurisdiction": "central", "year": 2005.0,
            }]), acts)
            pq.write_table(pa.Table.from_pylist([{
                "case_id": "matter-a", "title": "Example termination notice",
                "case_number": "OA/1/2024", "tribunal": "cat", "year": 2024,
            }]), matters)
            sources = [cases, acts, matters]
            destination = root / "index"
            self.assertEqual(build(sources, destination, threads=1), 3)
            self.assertEqual(build(sources, destination, threads=1), 0)
            index = open_index(destination)
            hits = search(index, "termination notice")
            self.assertEqual({h["group"][0] for h in hits}, {"judgment:case-a", "legislation:act-a", "tribunal:matter-a"})
            self.assertEqual(search(index, "[1979] 3 SCR 453", exact=True)[0]["body"], ["termination notice"])
            self.assertEqual(search(index, "Example Act Section 2(q)", exact=True)[0]["section"], ["2(q)"])
            self.assertEqual(search(index, "Example Act Section 999", exact=True), [])
            result = search(index, "termination", court="DHC", from_year=1979, to_year=1979)
            self.assertEqual(result[0]["page_start"], [4])
            self.assertEqual(search(index, "termination", from_year=2025), [])
            self.assertEqual(search(index, "checkpoint:in_delhi_judgments.parquet"), [])
            self.assertEqual(len(search(index, "*", limit=10)), 3)
            with self.assertRaisesRegex(ValueError, "limit"):
                search(index, "termination", limit=0)


if __name__ == "__main__":
    unittest.main()
