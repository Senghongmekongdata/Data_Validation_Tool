import csv
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reconciliation.pipeline import reconcile, read_source

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.config = {
            'warehouse': {'path': 'warehouse.csv'},
            'finance': {'path': 'finance.csv'},
            'keys': ['id', 'currency'], 'amounts': ['amount'],
            'tolerances': {'amount': '0.01'},
        }

    def source(self, side, rows):
        with (self.base / f'{side}.csv').open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['id', 'currency', 'amount'])
            writer.writerows(rows)

    def test_tolerance_and_currency_totals(self):
        self.source('warehouse', [['1', 'USD', '0.30'], ['2', 'EUR', '12']])
        self.source('finance', [['1', 'USD', '0.31'], ['2', 'EUR', '12']])
        summary, rows, issues = reconcile(self.config, self.base)
        self.assertTrue(summary['passed'])
        self.assertEqual(summary['status_counts'], {'matched': 2})
        self.assertEqual(summary['totals_by_currency']['USD']['difference']['amount'], '-0.01')
        self.assertIsNone(summary['total_differences'])

    def test_missing_and_mismatching_records(self):
        self.source('warehouse', [['1', 'USD', '100'], ['2', 'USD', '20']])
        self.source('finance', [['1', 'USD', '90'], ['3', 'USD', '30']])
        summary, rows, issues = reconcile(self.config, self.base)
        self.assertFalse(summary['passed'])
        self.assertEqual(summary['status_counts'], {'amount_mismatch': 1, 'missing_in_finance': 1, 'missing_in_warehouse': 1})

    def test_duplicates_and_invalid_values(self):
        self.source('warehouse', [['1', 'USD', '10'], ['1', 'USD', '20'], ['2', 'USD', 'NaN'], ['', 'USD', '1']])
        self.source('finance', [['1', 'USD', '10']])
        summary, rows, issues = reconcile(self.config, self.base)
        self.assertFalse(summary['passed'])
        self.assertEqual(len(issues), 3)
        self.assertEqual(rows[0]['status'], 'duplicate_key')
        self.assertEqual(rows[0]['warehouse_amount'], '')
        self.assertFalse(summary['totals_complete'])

    def test_empty_sources_fail(self):
        self.source('warehouse', [])
        self.source('finance', [])
        summary, _, issues = reconcile(self.config, self.base)
        self.assertFalse(summary['passed'])
        self.assertEqual(len(issues), 2)

    def test_missing_column(self):
        self.source('warehouse', [])
        self.config['amounts'] = ['tax']
        with self.assertRaisesRegex(ValueError, 'missing columns'):
            reconcile(self.config, self.base)

    def test_reports_cli_and_overwrite_protection(self):
        self.source('warehouse', [['=1+1', 'USD', '10']])
        self.source('finance', [['=1+1', 'USD', '9']])
        config_path = self.base / 'config.json'
        config_path.write_text(json.dumps(self.config))
        output = self.base / 'reports'
        command = [sys.executable, '-m', 'reconciliation', '--config', str(config_path), '--output', str(output)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(list(output.iterdir())), 4)
        with (output / 'exceptions.csv').open() as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row['key_id'], "'=1+1")
        self.assertEqual(row['difference_amount'], '1')
        repeated = subprocess.run(command, cwd=ROOT, capture_output=True)
        self.assertEqual(repeated.returncode, 2)

    def test_parameterized_sql_adapter(self):
        db = self.base / 'warehouse.db'
        with sqlite3.connect(db) as connection:
            connection.execute('CREATE TABLE invoices (id TEXT, currency TEXT, amount TEXT)')
            connection.execute("INSERT INTO invoices VALUES ('1', 'USD', '12.25')")
        self.config['warehouse'] = {'type': 'sql', 'url_env': 'TEST_WAREHOUSE_URL', 'query': 'SELECT * FROM invoices WHERE id=:id', 'parameters': {'id': '1'}}
        self.source('finance', [['1', 'USD', '12.25']])
        with patch.dict(os.environ, {'TEST_WAREHOUSE_URL': f'sqlite:///{db}'}):
            summary, _, _ = reconcile(self.config, self.base)
        self.assertTrue(summary['passed'])

    def test_excel_mapping(self):
        from openpyxl import Workbook
        book = Workbook()
        sheet = book.active
        sheet.append(['Invoice', 'Currency', 'Total'])
        sheet.append(['001', 'USD', 12.25])
        book.save(self.base / 'finance.xlsx')
        book.close()
        self.source('warehouse', [['001', 'USD', '12.25']])
        self.config['finance'] = {'type': 'excel', 'path': 'finance.xlsx', 'columns': {'id': 'Invoice', 'currency': 'Currency', 'amount': 'Total'}}
        summary, _, _ = reconcile(self.config, self.base)
        self.assertTrue(summary['passed'])

    def test_database_drivers_and_missing_credentials(self):
        from sqlalchemy import create_engine
        for url in ('oracle+oracledb://', 'mysql+pymysql://'):
            engine = create_engine(url)
            engine.dispose()
        with patch.dict(os.environ, {}, clear=True):
            for kind in ('oracle', 'mysql'):
                with self.assertRaisesRegex(ValueError, 'missing database environment variables'):
                    read_source({'type': kind, 'query': 'SELECT 1'}, self.base)


if __name__ == '__main__':
    unittest.main()
