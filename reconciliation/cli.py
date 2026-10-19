import argparse
import json
import sys
from pathlib import Path

from .pipeline import reconcile, write_reports


def main():
    parser = argparse.ArgumentParser(description="Compare warehouse records with Finance records")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New directory for this run")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        summary, rows, issues = reconcile(config, args.config.resolve().parent)
        write_reports(args.output, summary, rows, issues, config["keys"], config["amounts"])
    except Exception as exc:
        # SQL errors may contain credentials, SQL literals, or sensitive record values.
        if type(exc).__module__.startswith(("sqlalchemy", "psycopg", "pymysql", "snowflake")):
            print("Database operation failed; check connectivity, driver, permissions, and query.", file=sys.stderr)
        else:
            print(f"Reconciliation failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1
