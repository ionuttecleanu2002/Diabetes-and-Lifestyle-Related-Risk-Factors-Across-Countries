import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from etl import extract_owid, extract_who, extract_worldbank


class ExtractionTests(unittest.TestCase):
    def test_who_pagination_and_cache(self):
        first = Mock()
        first.raise_for_status = Mock()
        first.json.return_value = {
            "value": [{"SpatialDim": "ROU", "TimeDim": "2020"}],
            "@odata.nextLink": "https://who.example/page-2",
        }
        second = Mock()
        second.raise_for_status = Mock()
        second.json.return_value = {
            "value": [{"SpatialDim": "ROU", "TimeDim": "2021"}]
        }

        with tempfile.TemporaryDirectory() as directory:
            with patch("etl.extract_who.requests.get", side_effect=[first, second]) as get:
                path, url = extract_who.extract_who(
                    "WHOSIS_000001",
                    country_codes=["ROU"],
                    raw_dir=directory,
                )
                cached_path, _ = extract_who.extract_who(
                    "WHOSIS_000001",
                    raw_dir=directory,
                )

            self.assertEqual(get.call_count, 2)
            self.assertEqual(path, cached_path)
            self.assertEqual('WHOSIS_000001', path.stem)
            self.assertIn("SpatialDim", path.read_text(encoding="utf-8"))

    def test_worldbank_indicator_validation_and_cache(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = [
            {"page": 1, "pages": 1, "total": 1},
            [{
                "country": {"id": "RO", "value": "Romania"},
                "countryiso3code": "ROU",
                "date": "2020",
                "value": 7.5,
            }],
        ]

        with tempfile.TemporaryDirectory() as directory:
            with patch("etl.extract_worldbank.requests.get", return_value=response):
                path, url = extract_worldbank.extract_worldbank(
                    "SP.DYN.IMRT.IN",
                    country_codes=["ROU"],
                    raw_dir=directory,
                )
                cached_path, _ = extract_worldbank.extract_worldbank(
                    "SP.DYN.IMRT.IN",
                    raw_dir=directory,
                )

            self.assertEqual(path, cached_path)
            self.assertIn("SP.DYN.IMRT.IN", url)
            self.assertIn("ROU", path.read_text(encoding="utf-8"))

    def test_worldbank_rejects_unexpected_response_format(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {"unexpected": "format"}

        with tempfile.TemporaryDirectory() as directory:
            with patch("etl.extract_worldbank.requests.get", return_value=response):
                with self.assertRaisesRegex(
                    extract_worldbank.requests.RequestException,
                    "Unexpected World Bank",
                ):
                    extract_worldbank.extract_worldbank(
                        "NY.GDP.PCAP.CD",
                        raw_dir=directory,
                        force=True,
                    )

    def test_owid_download_validation_and_cache(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.headers = {"Content-Type": "text/csv"}
        response.content = (
            b"Entity,Code,Year,Life expectancy\n"
            b"Romania,ROU,2020,75.6\n"
        )

        with tempfile.TemporaryDirectory() as directory:
            with patch("etl.extract_owid.requests.get", return_value=response):
                path, url = extract_owid.extract_owid(
                    "life-expectancy",
                    raw_dir=directory,
                )
                cached_path, cached_url = extract_owid.extract_owid(
                    "life-expectancy",
                    raw_dir=directory,
                )

            self.assertEqual(path, cached_path)
            self.assertEqual(url, cached_url)
            self.assertIn("Romania", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
