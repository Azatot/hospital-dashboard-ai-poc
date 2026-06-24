import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from db_connector import UnsafeQueryError, assert_read_only_query  # noqa: E402


class SqlValidationTests(unittest.TestCase):
    def test_accepts_select_and_cte_queries(self):
        assert_read_only_query("SELECT COUNT(*) AS total FROM urgencias")
        assert_read_only_query(
            "WITH diarios AS (SELECT fecha_entrada FROM urgencias) "
            "SELECT COUNT(*) AS total FROM diarios;"
        )

    def test_rejects_mutating_queries(self):
        with self.assertRaises(UnsafeQueryError):
            assert_read_only_query("UPDATE pacientes SET nombre = 'x'")

        with self.assertRaises(UnsafeQueryError):
            assert_read_only_query("SELECT * FROM pacientes; DROP TABLE pacientes;")

        with self.assertRaises(UnsafeQueryError):
            assert_read_only_query("SELECT * INTO copia_pacientes FROM pacientes")

    def test_ignores_keywords_inside_literals_and_comments(self):
        assert_read_only_query("SELECT 'drop table pacientes' AS nota")
        assert_read_only_query("SELECT 1 -- delete from pacientes")


if __name__ == "__main__":
    unittest.main()
