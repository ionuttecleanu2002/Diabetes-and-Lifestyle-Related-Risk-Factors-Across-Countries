import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from etl.import_owid import import_owid
from etl.import_who import import_who
from etl.import_worldbank import import_worldbank


class ImporterTests(unittest.TestCase):
    def test_worldbank_imports_saved_files_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "countries.json").write_text(
                json.dumps([
                    {"page": 1, "pages": 1},
                    [{
                        "id": "ROU",
                        "name": "Romania",
                        "region": {"id": "ECS", "value": "Europe"},
                    }],
                ]),
                encoding="utf-8",
            )
            (path / "SP.DYN.IMRT.IN.json").write_text(
                json.dumps([
                    {"page": 1, "pages": 1},
                    [{
                        "countryiso3code": "ROU",
                        "indicator": {
                            "id": "SP.DYN.IMRT.IN",
                            "value": "Mortality rate, infant",
                        },
                        "date": "2020",
                        "value": 6.1,
                    }],
                ]),
                encoding="utf-8",
            )
            calls = []

            def fake_load(frame, **kwargs):
                calls.append((frame, kwargs))
                return len(frame)

            with patch("etl.import_worldbank.extract_worldbank") as extract:
                result = import_worldbank(
                    path,
                    indicators=["SP.DYN.IMRT.IN"],
                    load_function=fake_load,
                )

        extract.assert_not_called()
        self.assertEqual(result["imported"]["SP.DYN.IMRT.IN"], 1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][1]["countries"][0]["country_iso3"], "ROU")
        self.assertEqual(
            calls[1][1]["indicator_metadata"]["SP.DYN.IMRT.IN"]["indicator_name"],
            "Mortality rate, infant",
        )

    def test_worldbank_continues_after_indicator_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "countries.json").write_text(
                json.dumps([
                    {"page": 1, "pages": 1},
                    [{
                        "id": "ROU",
                        "name": "Romania",
                        "region": {"id": "ECS", "value": "Europe"},
                    }],
                ]),
                encoding="utf-8",
            )
            (path / "GOOD.json").write_text(
                json.dumps([
                    {"page": 1, "pages": 1},
                    [{
                        "countryiso3code": "ROU",
                        "indicator": {"id": "GOOD", "value": "Good indicator"},
                        "date": "2020",
                        "value": 3,
                    }],
                ]),
                encoding="utf-8",
            )
            with patch(
                "etl.import_worldbank.extract_worldbank",
                side_effect=RuntimeError("simulated download failure"),
            ):
                result = import_worldbank(
                    path,
                    indicators=["MISSING", "GOOD"],
                    load_function=lambda frame, **kwargs: len(frame),
                )

        self.assertIn("MISSING", result["failures"])
        self.assertEqual(result["imported"]["GOOD"], 1)

    def test_who_import_uses_saved_raw_file(self):
        with tempfile.TemporaryDirectory() as directory:
            raw_file = Path(directory) / "WHOSIS_000001.json"
            raw_file.write_text(
                json.dumps({
                    "value": [{
                        "SpatialDim": "ROU",
                        "TimeDim": "2020",
                        "NumericValue": 75.5,
                        "IndicatorCode": "WHOSIS_000001",
                        "IndicatorName": "Life expectancy",
                    }]
                }),
                encoding="utf-8",
            )
            captured = []
            with patch("etl.import_who.extract_who") as extract:
                count = import_who(
                    directory,
                    load_function=lambda frame, **kwargs: (
                        captured.append((frame, kwargs)) or len(frame)
                    ),
                    country_codes={"ROU"},
                )

        extract.assert_not_called()
        self.assertEqual(count, 1)
        self.assertEqual(captured[0][1]["source_name"], "WHO GHO")
        self.assertEqual(
            captured[0][1]["indicator_metadata"]["WHOSIS_000001"][
                "indicator_name"
            ],
            "Life expectancy",
        )

    def test_owid_import_uses_saved_chart_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "life-expectancy.csv").write_text(
                "Entity,Code,Year,Life expectancy at birth\n"
                "Romania,ROU,2020,75.6\n"
                "World,WLD,2020,72.8\n",
                encoding="utf-8",
            )
            captured = []
            with patch("etl.import_owid.extract_owid") as extract:
                result = import_owid(
                    path,
                    charts=[("life-expectancy", "LIFE-EXPECTANCY")],
                    country_codes={"ROU"},
                    load_function=lambda frame, **kwargs: (
                        captured.append((frame, kwargs)) or len(frame)
                    ),
                )

        extract.assert_not_called()
        self.assertEqual(result["imported"]["LIFE-EXPECTANCY"], 1)
        self.assertEqual(len(captured[0][0]), 1)
        self.assertEqual(
            captured[0][1]["indicator_metadata"]["LIFE-EXPECTANCY"][
                "indicator_name"
            ],
            "Life expectancy at birth",
        )


if __name__ == "__main__":
    unittest.main()
