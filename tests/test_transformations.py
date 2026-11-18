import json
import tempfile
import unittest
from pathlib import Path

from etl.transform_owid import transform_owid
from etl.transform_who import transform_who
from etl.transform_worldbank import transform_worldbank


class TransformationTests(unittest.TestCase):
    def test_who_sex_and_normalized_columns(self):
        payload = {
            "value": [
                {
                    "SpatialDim": "ROU",
                    "TimeDim": "2020",
                    "NumericValue": 75.5,
                    "IndicatorCode": "WHOSIS_000001",
                    "Dim1Type": "SEX",
                    "Dim1": "Male",
                },
                {
                    "SpatialDim": "ROU",
                    "TimeDim": "2020",
                    "NumericValue": 16.0,
                    "IndicatorCode": "WHOSIS_000001",
                    "Dim1Type": "SEX",
                    "Dim1": "Both sexes",
                },
                {
                    "SpatialDim": "ROU",
                    "TimeDim": "2020",
                    "NumericValue": 99.0,
                    "IndicatorCode": "WHOSIS_000001",
                    "Dim1Type": "Age",
                    "Dim1": "18+",
                },
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "who.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            frame = transform_who(path)

        self.assertEqual(
            list(frame.columns),
            ["country_iso3", "indicator_code", "year", "sex", "value"],
        )
        self.assertEqual(len(frame), 2)
        self.assertEqual(frame["sex"].tolist(), ["MLE", "BTSX"])

    def test_worldbank_uses_country_list_and_excludes_regions(self):
        countries = [
            {"page": 1, "pages": 1},
            [
                {
                    "iso2Code": "RO",
                    "iso3Code": "ROU",
                    "region": {"id": "ECS", "value": "Europe"},
                },
                {
                    "iso2Code": "1W",
                    "iso3Code": "WLD",
                    "region": {"id": "NA", "value": "Aggregates"},
                },
            ],
        ]
        observations = [
            {"page": 1, "pages": 1},
            [
                {
                    "countryiso3code": "ROU",
                    "indicator": {"id": "SP.DYN.IMRT.IN"},
                    "date": "2020",
                    "value": 6.1,
                },
                {
                    "countryiso3code": "WLD",
                    "indicator": {"id": "SP.DYN.IMRT.IN"},
                    "date": "2020",
                    "value": 27.0,
                },
            ],
        ]
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            countries_path = directory / "countries.json"
            observations_path = directory / "indicator.json"
            countries_path.write_text(json.dumps(countries), encoding="utf-8")
            observations_path.write_text(json.dumps(observations), encoding="utf-8")
            frame = transform_worldbank(observations_path, countries_path)

        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["country_iso3"], "ROU")
        self.assertEqual(frame.iloc[0]["indicator_code"], "SP.DYN.IMRT.IN")
        self.assertEqual(frame.iloc[0]["sex"], "BTSX")

    def test_owid_valid_csv_and_exactly_one_value_column(self):
        csv_text = (
            "Entity,Code,Year,Life expectancy at birth\n"
            "Romania,ROU,2020,75.6\n"
            "World,WLD,2020,72.8\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "life-expectancy.csv"
            path.write_text(csv_text, encoding="utf-8")
            frame = transform_owid(path, "OWID_LIFE_EXPECTANCY")

        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["country_iso3"], "ROU")
        self.assertEqual(frame.iloc[0]["indicator_code"], "OWID_LIFE_EXPECTANCY")
        self.assertEqual(frame.iloc[0]["year"], "2020")

    def test_owid_rejects_missing_and_extra_value_columns(self):
        missing = "Entity,Year,Value\nRomania,2020,75\n"
        extra = "Entity,Code,Year,First,Second\nRomania,ROU,2020,1,2\n"
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            missing_path = directory / "missing.csv"
            extra_path = directory / "extra.csv"
            missing_path.write_text(missing, encoding="utf-8")
            extra_path.write_text(extra, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required"):
                transform_owid(missing_path)
            with self.assertRaisesRegex(ValueError, "exactly one value"):
                transform_owid(extra_path)


if __name__ == "__main__":
    unittest.main()
