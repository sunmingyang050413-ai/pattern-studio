# Reviewer quick start

Live application: https://pattern-studio-ms-2026.japaneast.cloudapp.azure.com/

The public deployment uses genuine Amazon S3 endpoints. Bring an authorized test bucket, its region, and credentials permitting `s3:ListBucket` and `s3:GetObject`. Temporary credentials also require the session token. No upload or write permission is needed by the application; prepare the source file in your bucket first.

1. Connect the bucket, wait for the asynchronous file list, then choose a CSV or Excel file and load its preview.
2. Select a text column, choose **Find & replace**, enter **Find email addresses**, and use **REDACTED** as the replacement. Run and inspect the generated plan, progress and result pages.
3. Try **Extract a value** with **Extract an email address**; output is appended in a new column. Try **Clean up text** with **Trim spaces, collapse whitespace and lowercase text**.
4. Repeat the same mode and instruction to inspect cached planning. Original bucket objects remain unchanged.

## Evidence and limitations

- The deployed Linux backend suite passed 30 tests; GitHub Actions also passed backend and frontend jobs.
- Public HTTPS, redirect, session cookies and API health were verified.
- Three real Groq calls produced validated plans.
- Isolated HTTP integration used real PostgreSQL, Redis, Celery, PySpark and Groq with **Moto-emulated S3**, verifying 10,000 rows and 100 result pages for each mode. This is not a real AWS S3 test.
- A separate local synthetic million-row benchmark is recorded in `benchmark-local.json`; it is not a million-row cloud ingestion benchmark.
- No real AWS credentials were available to the applicant. Real AWS IAM/region behavior and an end-to-end real-S3 recording remain unverified. See `VERIFICATION.md` for the detailed record.

## Reproduce without an AWS account

Follow `FREE_SETUP.md` to run the isolated Moto integration harness. It requires Docker and a configured LLM key, publishes no ports, and keeps separate database/result volumes. Production configuration is unchanged.

## Hosting lifetime

Hosting consumes Azure student credit and is not permanent. The Groq project credential expires on 31 October 2026 and must be renewed by the operator if review occurs later.
