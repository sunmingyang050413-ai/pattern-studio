# Verification record

30 September cloud update: [GitHub Actions run 36667402782](https://github.com/sunmingyang050413-ai/pattern-studio/actions/runs/36667402782) passed both jobs. Linux backend: **30 passed in 23.19 seconds**, including real Spark integration. Frontend tests and production build passed. Azure Docker Compose build exited 0; API, database and Redis report healthy, and worker, beat, Flower and frontend containers are running. Public HTTPS and real S3/LLM integration remain pending.

30 September update: the provider-only non-Spark suite passed **29 tests, with 1 Spark test deselected**. Five new Groq/provider tests use mocked outbound calls. Earlier real Spark evidence below is unchanged. The Azure VM was created successfully; Docker 29.1.3 and Compose 2.40.3 installation succeeded through Azure Run Command. Application deployment remains pending (see AZURE_STATUS.md).

Date: 29 September 2026. Environment: Windows host, isolated Python 3.11.9, Java 17.0.9, PySpark 3.5.7; local filesystem. No Docker daemon, production hosting account, real S3 credentials or LLM API key was available during this verification.

| Check | Actual outcome |
| --- | --- |
| PDF requirements | Both pages extracted and visually reviewed |
| Django schema | Initial migration generated and applied to a local SQLite test DB |
| Django system check | Passed, zero issues |
| Backend tests | 25 passed; includes real Spark CSV/replace/extract/normalize/materialization integration |
| Frontend API tests | 3 passed |
| React production build | Passed with Vite 6.4.3 |
| Browser UI | Initial page and transformation controls inspected at desktop and mobile widths |
| Million-row Spark benchmark | Passed; 1,000,000 output rows verified for count, uniqueness and replacement |
| Real Redis/Celery broker execution | Not yet run; task tests call the orchestration directly with external services mocked |
| Linux Docker Compose deployment | Not yet run; Docker unavailable on this host |
| Standalone Spark overlay | Configuration supplied; not yet run |
| Real S3 + LLM full pipeline | Pending credentials and service account |
| Public HTTPS app | Not deployed |
| Required real demo video | Not recorded |

## Measured synthetic benchmark

See [benchmark-local.json](benchmark-local.json). One run, not a statistically rigorous performance study:

- Rows: 1,000,000; verified output rows: 1,000,000.
- Spark master: `local[2]`; partitions: 8.
- Transform and JSON block materialization time: **7.051 seconds**.
- Throughput: **141,815 rows/second**.
- First result-page read: **0.135 ms**, warm local filesystem, excludes HTTP/browser/network.
- Timer begins after SparkSession creation; includes synthetic frame planning and execution. Full correctness verification occurs after the timed materialization.
- Data shape: two short string columns, ID and synthetic email. These numbers do not predict performance on wide/large real-world cells.
- Excludes S3, LLM, Excel, Celery queue latency and multi-machine communication. This is not an end-to-end scalability claim.

The initial Python 3.12 runtime could start the Spark JVM but its Python workers crashed. Verification was rerun successfully with Python 3.11, which matches the Docker image. Windows emitted a shutdown `Access denied` message from process cleanup after successful Spark exit; test/benchmark processes returned zero. Linux remains the deployment target and must still be verified.

## Evidence boundary

S3 and LLM behavior is unit-tested using mocked responses, including safe error handling and encryption. It has not been tested against a real account. Do not replace the pending statuses above with claims of success until the relevant stack is actually running and verified. The screenshot [interface.png](interface.png) shows the actual local UI, not a completed data job.
