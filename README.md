# Data Validation Tool

Python reconciliation pipeline for comparing warehouse data against Finance data.
Supports CSV, MySQL, Oracle, and Excel on either side. Reports matched records,
missing records, amount differences, duplicates, invalid data, and totals by currency.
Requires Python 3.11+. Source records are never updated.

## Install and run

Run from the repository root:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[mysql,oracle,excel]'
.venv/bin/python -m reconciliation --config examples/config.json --output reports/demo
.venv/bin/python -m unittest discover -s tests -v
```

The demonstration intentionally exits **1**: one match, one amount mismatch,
one record missing in Finance, and one missing in the warehouse. Exit **0** means
all records match within tolerance with no quality issues. Exit **2** means an
input, configuration, connection, or output error prevented completion.
Use a new output directory each run: existing reports are never overwritten.

## Your current CSV and MySQL workflow

Copy `examples/mysql-config.json` to a local configuration directory. Replace
`finance_invoice_extract`, column names, period, and Finance CSV location with
actual values. Paths resolve relative to the configuration file. Both sources can
independently be CSV, MySQL, Oracle, Excel, or generic SQL; switch their `type`
and associated fields as needed.

Supply these variables through your secure runtime environment, never in source
control, JSON, or chat:

| MySQL | Oracle |
| --- | --- |
| MYSQL_USER | ORACLE_USER |
| MYSQL_PASSWORD | ORACLE_PASSWORD |
| MYSQL_HOST | ORACLE_HOST |
| MYSQL_DATABASE | ORACLE_SERVICE |
| MYSQL_PORT (default 3306) | ORACLE_PORT (default 1521) |

`examples/oracle-config.json` shows an Oracle warehouse comparison. Oracle uses
python-oracledb thin mode; ordinary connections need no Instant Client. Use
SELECT-only database accounts: configuration queries are trusted SQL and database
permissions enforce read-only access. Bind filter values through `parameters`.
Use quoted Oracle column aliases as shown to preserve header case.

Connections require direct database network access. Follow your organization's
TLS requirements; `connect_args` passes supported driver options to SQLAlchemy,
for example MySQL `{"ssl_ca": "/path/to/ca.pem", "ssl_verify_cert": true,
"ssl_verify_identity": true}`. Do not put credentials in `connect_args`.
Override variable names with `user_env`, `password_env`, `host_env`, `port_env`,
and `database_env` or `service_env` to configure independent connections.
Generic `type: sql` uses `url_env` (default `WAREHOUSE_URL`) for a SQLAlchemy URL,
plus `query` and optional `parameters`; install the relevant driver.

```bash
.venv/bin/python -m reconciliation --config /path/to/local-config.json --output reports/period-run-001
```

For Excel use `{"type": "excel", "path": "finance.xlsx", "sheet": "Invoices"}`.
`sheet` defaults to the active worksheet. Formula cells need cached calculated
values; this tool does not calculate formulas.

## Agree the comparison rules

- `keys`: unique business identifiers such as invoice ID, company, currency, and
  period. `columns` maps canonical names to each source's column headers. Keys
  are whitespace-trimmed, case-sensitive strings. Preserve leading zeroes as text
  in Excel and warehouse queries.
- `amounts`: numeric fields such as net, tax, and gross amount. Each field accepts
  an absolute `tolerances` value, default zero. Decimal arithmetic avoids binary
  floating-point comparison errors. A tolerance of `0.01` accepts exactly one cent.
- `currency_key`: include currency in the keys to separate totals. Defaults to
  `currency` when present. Without it, ensure a single currency/unit per extract.
- Duplicate keys, blank keys, malformed/nonfinite amounts, and empty inputs fail
  validation. `allow_empty: true` explicitly permits empty inputs. Duplicates are
  never silently summed. Aggregate to the agreed grain in SQL, or use more keys.

Amounts must be plain decimal numbers without currency symbols or thousands
separators. Align accounting periods, timezones, posting statuses, sign conventions,
and units upstream. The example invoice schema and tolerance are placeholders;
confirm your business rules before using results for financial signoff.

## Reports

| Output | Information |
| --- | --- |
| summary.json | Pass/fail, input counts, status counts, tolerances, currency totals and differences, UTC timestamp |
| comparison.csv | Each valid key, status, both sources' amounts, and differences |
| exceptions.csv | Missing records, amount mismatches, and duplicate keys |
| data_quality.csv | Source, data-row position, and invalid/duplicate data details |

Differences mean **warehouse minus Finance**. Invalid rows are excluded from
comparisons and totals. Duplicate keys on either side are excluded from totals
on both sides. `totals_complete: false` flags quality issues. Invalid amounts can
also produce a missing-record exception for a valid counterpart; inspect the
quality report first. Spreadsheet formula-like text is prefixed with an apostrophe.
Reports contain financial identifiers and data; apply suitable access and retention.

The first version loads each filtered extract into memory. Use bounded periods
and SQL aggregation for large datasets. Snapshot/cutoff consistency between systems
must be arranged upstream. Scheduling can invoke the CLI and use its exit status
for alerts. Tests cover local CSV, Excel, and parameterized SQLite SQL; live MySQL
and Oracle require your actual schema, connection settings, and network access.
