# Submission checklist

Email received: **18 September 2026** (as reported by applicant). Two-week deadline: **2 October 2026**, subject to the original email timestamp/timezone. Submit early instead of depending on end-of-day interpretation.

## Required before sending

- [x] Push the complete source to the applicant's GitHub repository (public; anonymous access verified 1 October 2026).
- [x] Configure a real LLM API key on the server, not in Git.
- [x] Deploy the full stack to a public HTTPS URL.
- [ ] Test the reviewer's own-bucket flow with a real S3 test bucket.
- [x] Run Linux Docker-stack tests and verify migrations, Redis, worker, Beat and Flower.
- [ ] Verify a sizeable dataset through the full S3/LLM/Celery/Spark pipeline.
- [ ] Record a real demo showing credentials entry, asynchronous completion and paginated results.
- [ ] Embed/link that video in README; replace live URL placeholders.
- [ ] Review README tradeoffs and explain the implementation yourself.
- [ ] Confirm repository, live app and demo are accessible to the reviewer.
- [ ] Send a **new email**, not a reply, with the exact subject below.

## Draft email — not sent

To: careers@rhombusai.com

Subject: Rhombus AI – Take-Home Exercise

Dear Rhombus AI Team,

Thank you for the opportunity to complete the Software Engineer Intern take-home exercise.

Please find my submission below:

- GitHub repository: https://github.com/sunmingyang050413-ai/pattern-studio
- Live application: https://pattern-studio-ms-2026.japaneast.cloudapp.azure.com/
- Demo video: [insert actual video URL; also included in README]

The repository includes setup instructions, the architecture and design tradeoffs, Docker Compose configuration, tests, and verification results.

Best regards,
Mingyang

No email has been sent. Replace every placeholder and complete the public deliverables before submitting. The exercise lists rhombusinsights@rhombusai.com for project questions; contacting them is a separate action.
