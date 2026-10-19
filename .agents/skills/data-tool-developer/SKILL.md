data-tool-developer
Design, architect, and build software applications and developer tools for data workflows. Use when the user asks to create, architect, or code ETL/ELT tools, data governance utilities, data quality engines, metadata catalogs, Data Science platforms, BI/analytics dashboards, or custom data processing applications.

Instructions
Data Tool Developer
A structured workflow for designing and implementing production-grade software applications that process, govern, analyze, and visualize data.

When to Use
Building custom ETL or ELT pipeline tools, data ingestion utilities, or batch/streaming file processors
Developing data governance applications such as data catalogs, lineage trackers, PII scanners, or automated data quality rule engines
Creating Data Science workbenches, feature engineering tools, model evaluation dashboards, or explainable AI interfaces
Architecting Business Intelligence (BI) tools, semantic layer utilities, SQL query builders, or interactive reporting applications
Designing CLI utilities, desktop applications, or web services tailored for data engineering and analytics teams
Steps
1. Define Tool Category and Architecture
Identify the primary data domain and select a modular four-layer architecture before writing application code. Separating the user interface from data processing prevents UI freezes and allows the core engine to run headlessly in CI/CD or scheduled jobs.

Connector and I/O Layer: Abstract database drivers (SQLAlchemy, ODBC, DuckDB) and file readers (Parquet, Arrow, CSV, JSON) behind a unified interface.
Core Engine Layer: Isolate transformation logic, validation rules, statistical computations, or semantic query generation from the presentation layer.
State and Metadata Layer: Persist job execution logs, pipeline state, schema registries, or user configurations in a lightweight store (SQLite, DuckDB, or JSON/YAML configs).
Interface Layer: Match the interface to the user workflow (CLI via Typer/Click for automation, FastAPI + React/Streamlit for web apps, or PyQt6 for standalone desktop tools).
2. Design Data Contracts and Schema Handling
Data tools fail most often at schema boundaries. Enforce explicit data contracts at ingestion and output stages.

Schema Inference and Validation: Inspect column names, data types, and nullability before processing full files or tables.
Type Safety: Map source types to canonical internal types (such as Arrow or Pydantic models) so downstream transformations do not break on unexpected string or date formats.
Sample-First Execution: Support dry-run or preview modes (processing the first 100 to 1,000 rows) so users can verify mappings and rules instantly without waiting for full dataset scans.
3. Implement Domain-Specific Core Capabilities
Apply targeted design patterns based on the specific category of data tool being built.

ETL and ELT Tools
Implement chunked or streaming execution (using PyArrow, Polars, or batched SQL reads) to avoid out-of-memory crashes on large files.
Ensure idempotency (support upsert, merge, or partition overwrite) so re-running a failed job never duplicates records.
Route malformed records to a quarantine table or error log with specific failure reasons rather than aborting an entire batch silently.
Data Governance and Quality Tools
Represent data quality rules declaratively (completeness, uniqueness, range checks, regex patterns, and referential integrity) in YAML or JSON so non-developers can audit and maintain them.
Generate automated data profiles (null rates, distinct counts, min/max, quantiles, and top values) using pushdown SQL or vectorized engines rather than row-by-row Python loops.
Track metadata attributes including business glossary terms, data owners, sensitivity classifications, and source-to-target lineage.
Data Science and ML Applications
Separate feature transformation pipelines from model training so the exact same preprocessing applies during both training and real-time inference.
Persist model artifacts alongside their input schema, hyperparameters, evaluation metrics (AUC, F1, RMSE, Gini), and explainability outputs (feature importance or SHAP values).
BI and Analytics Tools
Decouple the semantic layer (metrics, dimensions, aggregation rules, and time intelligence) from visual chart rendering.
Push aggregations and filters down to the underlying analytical engine (SQL database, DuckDB, or Polars) instead of loading raw fact tables into UI memory.
4. Build Responsive Execution and Observability
Data operations can take seconds or hours. Keep the application responsive and transparent during execution.

Asynchronous and Background Workers: Run heavy queries, file conversions, and model training in background threads or worker processes so the UI or API remains responsive and supports cancellation.
Structured Telemetry: Emit progress metrics including rows processed per second, elapsed time, memory usage, and row counts (read, written, rejected).
Audit Logging: Record every execution with a run ID, timestamp, input parameters, source/target paths, and status (SUCCESS, WARNING, FAILED).
5. Deliver Testable, Self-Contained Code
Provide a runnable verification script or synthetic dataset generator alongside the application code so the tool can be tested immediately.

Include a synthetic data generator or sample dataset that covers edge cases (nulls, duplicates, unicode characters, date boundaries, and schema drift).
Verify the tool's output with concrete assertions (row count conservation, schema compliance, and expected metric accuracy).
Gotchas
Loading entire datasets into memory: Never default to reading multi-gigabyte tables into in-memory structures all at once when building an application UI. Always paginate table previews and stream or batch bulk operations.
Hardcoding credentials or connection strings: Never embed database passwords or API keys in source files or UI state. Use environment variables, .env files, or secure OS keyring integrations.
Tightly coupling business logic to UI callbacks: Putting SQL generation or ETL transformations directly inside button-click handlers makes the tool impossible to unit test or schedule via CLI. Keep the engine in a standalone module.
Silent data truncation or coercion: Log a clear warning whenever type casting drops precision, truncates strings, or converts invalid values to NULL.
