import unittest

from sqlalchemy import Boolean

from app.models import Observation


class DatabaseModelTests(unittest.TestCase):
    def test_observation_is_outlier_column(self):
        column = Observation.__table__.c.is_outlier
        self.assertFalse(column.nullable)
        self.assertFalse(column.server_default is None)
        self.assertIsInstance(column.type, Boolean)

    def test_observation_natural_key_is_preserved(self):
        names = {
            constraint.name
            for constraint in Observation.__table__.constraints
            if hasattr(constraint, "name")
        }
        self.assertIn(
            "uq_observation_country_indicator_year_sex_age",
            names,
        )


if __name__ == "__main__":
    unittest.main()
