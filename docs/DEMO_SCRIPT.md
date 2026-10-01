# Demonstration recording plan

Status: a 2:37 project walkthrough has been recorded and uploaded: https://youtu.be/LqLsA4xI_V4. The available verified test environment uses Moto-emulated S3. Do not describe it as a real AWS demonstration.

## Accurate 2–3 minute walkthrough

1. Show the public application URL and identify Django, React, Celery, Redis and PySpark.
2. State explicitly: "Real Amazon S3 integration is implemented, but the end-to-end verification shown here uses Moto-emulated storage. The LLM, queue and Spark processing are real."
3. Show `compose.integration.yaml`, emphasizing that it is a separate, private test stack. Run the commands in FREE_SETUP.md and record the actual output, including 10,000 validated rows and 100 result pages for each mode. Do not display .env or account consoles.
4. Show the frontend controls for replace, extract and normalize. Without authorized AWS credentials, do not claim these public UI controls have completed a real-S3 job.
5. Show VERIFICATION.md and the local million-row benchmark, stating that the benchmark excludes cloud ingestion and LLM time.
6. Show the README architecture, setup instructions and known limitations. Finish on REVIEWER_GUIDE.md.

This walkthrough is a disclosed fallback, not equivalent to the requested full real-S3 UI demonstration. If real S3 access becomes available, record the bucket connection, asynchronous ingestion, transformations and pagination through the UI instead.

Only link a video after recording it, reviewing it for secrets, and checking reviewer access. A script or screenshot montage is not a recording of successful application behavior.
