# Requirement traceability

Source: the two-page “Technical Assessment — Distributed NL-to-Regex Data Processing Platform” PDF provided by the applicant, plus the recruiting email. This is a traceability list, not proof of deployment completion.

| Requirement | Implementation / deliverable | Remaining verification |
| --- | --- | --- |
| Django + React | `backend/`, `frontend/` | Full deployed browser flow |
| User-supplied S3 credentials and bucket | connection form, Fernet service, boto3 listing/download | Real AWS bucket |
| CSV / Excel → Spark DataFrame | streaming download, XLSX/XLS conversion, Spark CSV loader | Real S3 files, large Excel behavior |
| Clear API/task/data separation | views / tasks / services | Code review |
| Persistent statuses and progress | Postgres Job, stage progress, polling | Real queue / worker lifecycle |
| Immediate submit → job ID | 202 API + persistent outbox | Broker outage timing in Docker |
| Celery + Redis broker/backend/cache | Compose, worker, Beat, cached LLM plans | Redis integration |
| Failures, retries, cancellation | bounded retries, heartbeat, fencing, Spark job groups | Live cancellation during large run |
| Distributed PySpark transformations | Arrow batch UDFs across partitions | Optional standalone cluster |
| Million-row handling | real synthetic benchmark + full output verification | Full S3-to-browser million-row run |
| Paginated results | executor-written blocks + manifest-directed bounded reads | Public latency |
| NL regex + validation | typed LLM JSON, RE2 + Arrow validation | Real provider varied prompts |
| Two extra LLM transformations | extraction; ordered text cleanup | Real provider outputs |
| One-command stack | `docker compose up --build -d` after configuring `.env` | Docker host |
| Observability and tests | Flower, safe completion metrics, API counts, tests, CI | Live Flower |
| GitHub repository | source directory prepared | Applicant repository and push |
| README architecture / tradeoffs | `README.md` | Final URL/video update |
| Public deployment | Caddy + deployment instructions | Server, DNS and actual deployment |
| Demo embedded in README | recording script | Actual recording/upload/link |
| Submission email | unsent draft with exact recipient/subject | Send after all deliverables ready |
