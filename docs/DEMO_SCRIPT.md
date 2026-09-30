# Real demonstration recording plan (2–3 minutes)

The final video must show the genuine running deployment, not a mock. Use a disposable test bucket and least-privilege temporary credentials. Keep the secret key and session token masked in the form; hide account consoles and environment files. Inspect the final recording before publishing.

1. **0:00–0:20 — Introduction.** Show the public URL and explain the Django / React / Celery / Redis / Spark architecture in one sentence.
2. **0:20–0:45 — Own S3 bucket.** Enter test bucket, region and masked user credentials. Connect, show the asynchronous listing, select a CSV and load it.
3. **0:45–1:20 — Main requirement.** Select Email, enter “Find email addresses”, replace with REDACTED. Show queued/running/progress without refreshing. On success, show generated regex, redacted results and next page. Confirm the source S3 object remains unchanged.
4. **1:20–1:45 — Additional LLM transformations.** Extract emails into a new column; clean names with “trim, collapse spaces and lowercase”. Show the generated plans/results.
5. **1:45–2:10 — Reliability.** Repeat the exact prompt to show a cached plan; show a cancelled job and an invalid-credentials failure with a useful error. Do not expose credentials in logs.
6. **2:10–2:40 — Scale and observability.** Show the million-row result count and pagination, real benchmark report, and Flower worker/task view. Explain whether Spark is local or standalone; do not imply a multi-machine run if it was local.
7. **2:40–3:00 — Repository.** Show README setup, tests and known tradeoffs. Finish on the working public app.

Upload the video to a destination accessible to reviewers without requesting permission. Paste the real video link into README (a linked thumbnail is acceptable on GitHub, which does not generally render arbitrary iframe embeds). Test access in a private browser session. No real recording or video link exists yet.
