import unittest
from contextlib import contextmanager

import pandas as pd
from sqlalchemy.dialects import postgresql

from etl.load import (
    OBSERVATION_CONSTRAINT,
    _observation_upsert,
    _records_from_frame,
    load_observations,
)


class _Result:
    def __init__(self, value=None, rows=()):
        self.value = value
        self.rows = list(rows)

    def scalar_one(self):
        return self.value

    def mappings(self):
        return iter(self.rows)


class _FakeSession:
    def __init__(self, fail_on_observation=False):
        self.fail_on_observation = fail_on_observation
        self.added = []
        self.executed_tables = []
        self.committed = False
        self.rolled_back = False

    @contextmanager
    def begin(self):
        try:
            yield
        except Exception:
            self.rolled_back = True
            raise
        else:
            self.committed = True

    def execute(self, statement):
        table_name = statement.table.name
        self.executed_tables.append(table_name)
        if table_name == "source":
            return _Result(value=7)
        if table_name == "indicator":
            compiled = statement.compile(dialect=postgresql.dialect())
            codes = sorted({
                value for key, value in compiled.params.items()
                if key.startswith("indicator_code")
            })
            return _Result(
                rows=[
                    {"indicator_code": code, "indicator_id": index + 10}
                    for index, code in enumerate(codes)
                ]
            )
        if table_name == "observation" and self.fail_on_observation:
            raise RuntimeError("simulated database failure")
        return _Result()

    def add(self, item):
        self.added.append(item)


class LoadTests(unittest.TestCase):
    def test_observation_upsert_targets_existing_natural_key(self):
        statement = _observation_upsert(
            [{
                "country_iso3": "ROU",
                "indicator_id": 10,
                "year": 2020,
                "sex": "BTSX",
                "age_group": "All ages",
                "value": 10.2,
                "is_outlier": True,
            }]
        )
        sql = str(statement.compile(dialect=postgresql.dialect()))
        self.assertIn(f"ON CONSTRAINT {OBSERVATION_CONSTRAINT}", sql)
        self.assertIn("DO UPDATE SET", sql)
        self.assertIn("is_outlier = excluded.is_outlier", sql)
        self.assertIn("imported_at = now()", sql)

    def test_records_are_deduplicated_and_default_optional_fields(self):
        frame = pd.DataFrame(
            [
                ["ROU", "CODE", 2020, "BTSX", 1.0],
                ["ROU", "CODE", 2020, "BTSX", 2.0],
            ],
            columns=[
                "country_iso3",
                "indicator_code",
                "year",
                "sex",
                "value",
            ],
        )
        records = _records_from_frame(frame)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["value"], 2.0)
        self.assertFalse(records[0]["is_outlier"])
        self.assertEqual(records[0]["age_group"], "All ages")

    def test_load_commits_upserts_and_success_log_in_chunks(self):
        session = _FakeSession()
        frame = pd.DataFrame(
            [
                ["ROU", "CODE", 2020, "BTSX", 1.0, False],
                ["ROU", "CODE", 2021, "BTSX", 2.0, True],
            ],
            columns=[
                "country_iso3",
                "indicator_code",
                "year",
                "sex",
                "value",
                "is_outlier",
            ],
        )
        count = load_observations(
            session,
            frame,
            source_name="Test source",
            countries=[{
                "country_iso3": "ROU",
                "country_name": "Romania",
                "region": "Europe",
            }],
            chunk_size=1,
        )

        self.assertEqual(count, 2)
        self.assertTrue(session.committed)
        self.assertFalse(session.rolled_back)
        self.assertEqual(session.executed_tables.count("observation"), 2)
        self.assertEqual(len(session.added), 1)
        self.assertEqual(session.added[0].status, "success")
        self.assertEqual(session.added[0].records_imported, 2)

    def test_failed_load_rolls_back_without_success_log(self):
        session = _FakeSession(fail_on_observation=True)
        frame = pd.DataFrame(
            [["ROU", "CODE", 2020, "BTSX", 1.0]],
            columns=[
                "country_iso3",
                "indicator_code",
                "year",
                "sex",
                "value",
            ],
        )
        with self.assertRaisesRegex(RuntimeError, "simulated database failure"):
            load_observations(
                session,
                frame,
                source_name="Test source",
                countries=[{
                    "country_iso3": "ROU",
                    "country_name": "Romania",
                    "region": "Europe",
                }],
            )
        self.assertTrue(session.rolled_back)
        self.assertFalse(session.committed)
        self.assertEqual(session.added, [])


if __name__ == "__main__":
    unittest.main()
