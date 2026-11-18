import unittest

import pandas as pd

from etl.clean import add_iqr_outliers, clean_observations


class CleaningTests(unittest.TestCase):
    def frame(self, rows):
        return pd.DataFrame(
            rows,
            columns=["country_iso3", "indicator_code", "year", "sex", "value"],
        )

    def test_cleaning_rules_missing_sex_duplicates_and_year_window(self):
        frame = self.frame(
            [
                [" rou ", "SH.STA.DIAB.ZS", "2020", "", 8.1],
                ["ROU", "SH.STA.DIAB.ZS", "2020.0", "BOTH", 8.1],
                ["ROU", "SH.STA.DIAB.ZS", "2021", "X", 9.0],
                ["ROU", "SH.STA.DIAB.ZS", "2022.5", "MLE", 9.5],
                ["ROU", "SH.STA.DIAB.ZS", "1999", "MLE", 10.0],
                ["DEU", "SH.STA.DIAB.ZS", "2023", "MLE", "bad"],
                ["USA", "SH.STA.DIAB.ZS", "2024", "MLE", 101.0],
            ]
        )
        cleaned, logs = clean_observations(frame, {"ROU", "USA", "DEU"})

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["country_iso3"], "ROU")
        self.assertEqual(cleaned.iloc[0]["sex"], "BTSX")
        self.assertEqual(cleaned.iloc[0]["year"], 2020)
        self.assertTrue(any("duplicate" in log for log in logs))
        self.assertTrue(any("invalid sex" in log for log in logs))
        self.assertTrue(any("fractional year" in log for log in logs))
        self.assertTrue(any("year outside" in log for log in logs))
        self.assertTrue(any("missing value" in log or "non-numeric" in log for log in logs))
        self.assertTrue(any("plausible indicator bounds" in log for log in logs))

    def test_invalid_country_and_missing_year_are_removed(self):
        frame = self.frame(
            [
                ["GBR", "NY.GDP.PCAP.CD", "2020", "BTSX", 50000],
                ["XXX", "NY.GDP.PCAP.CD", "2020", "BTSX", 60000],
                ["GBR", "NY.GDP.PCAP.CD", None, "BTSX", 70000],
            ]
        )
        cleaned, logs = clean_observations(frame, {"GBR"})
        self.assertEqual(len(cleaned), 1)
        self.assertTrue(any("country not in country table" in log for log in logs))
        self.assertTrue(any("non-numeric or missing year" in log for log in logs))

    def test_iqr_flags_but_keeps_outliers(self):
        frame = self.frame(
            [
                ["ROU", "SH.STA.DIAB.ZS", 2020, "BTSX", 10],
                ["ROU", "SH.STA.DIAB.ZS", 2021, "BTSX", 11],
                ["ROU", "SH.STA.DIAB.ZS", 2022, "BTSX", 12],
                ["ROU", "SH.STA.DIAB.ZS", 2023, "BTSX", 13],
                ["ROU", "SH.STA.DIAB.ZS", 2024, "BTSX", 100],
            ]
        )
        flagged = add_iqr_outliers(frame)
        self.assertEqual(len(flagged), 5)
        self.assertTrue(flagged["is_outlier"].dtype == "bool")
        self.assertTrue(bool(flagged.iloc[-1]["is_outlier"]))

    def test_zero_iqr_is_safe_and_insufficient_data_is_not_flagged(self):
        zero_iqr = self.frame(
            [["ROU", "SH.STA.DIAB.ZS", year, "BTSX", 10] for year in range(2020, 2025)]
        )
        few = self.frame(
            [["ROU", "SH.STA.DIAB.ZS", year, "BTSX", value]
             for year, value in zip(range(2020, 2023), [10, 11, 12])]
        )
        self.assertFalse(add_iqr_outliers(zero_iqr)["is_outlier"].any())
        self.assertFalse(add_iqr_outliers(few)["is_outlier"].any())


if __name__ == "__main__":
    unittest.main()
