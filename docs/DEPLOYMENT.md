# Public deployment procedure

Public deployment is a required deliverable and is not yet completed. This procedure targets a Linux VM with Docker Compose; no hosting account, server or domain has been supplied. Do not enter credentials into a public HTTP endpoint.

1. Create a GitHub repository under your own account and push this directory (never `.env`, test databases, source data, or credentials).
2. Provision a Linux VM with at least 4 vCPU / 8 GiB RAM / 30 GiB disk as an initial target; monitor usage and adjust. This is a starting capacity recommendation, not a verified service limit. Install Docker using its official instructions. Allow inbound TCP 80/443 and restrict SSH to your IP.
3. Point a domain/subdomain A record at the server. Clone the repository to the server.
4. Run `python3 scripts/configure.py`. Edit `.env` locally on the server with an LLM API key and:

```dotenv
APP_DOMAIN=your-domain.example
ALLOWED_HOSTS=your-domain.example,localhost,127.0.0.1,api
CSRF_TRUSTED_ORIGINS=https://your-domain.example
HTTPS=1
```

5. Start the public stack:

```sh
docker compose -f compose.yaml -f compose.public.yaml up --build -d
docker compose -f compose.yaml -f compose.public.yaml ps
docker compose -f compose.yaml -f compose.public.yaml logs gateway worker api
```

Caddy obtains and renews a certificate when DNS and ports are correct. Nginx forwards Caddy's scheme to Django. The direct Nginx and Flower ports remain loopback-only. The internal backend port has no host mapping. Do not publish internal service ports.

6. From a different browser/session, open the HTTPS URL and test with real credentials for a disposable S3 bucket. Confirm the invalid-credentials case, listing, load, all three transformations, pagination, cancellation, and no cross-session access. Keep a sanitized record of evidence.
7. Run the Linux test suite and million-row benchmark. Upload the generated million-row CSV to your test bucket; test a real full pipeline as well. Inspect Flower through an SSH tunnel (`ssh -L 5555:localhost:5555 user@server`) instead of exposing it.
8. Record the demonstration, embed its link in README, replace the live URL placeholder, then re-test both links anonymously. Keep the deployment running through review.

## Operational notes

- Back up Postgres only if needed; encrypted AWS tokens expire in 24 hours. Backups also contain job prompts and metadata. Keep the encryption key separate from snapshots.
- Source/result data cleanup runs hourly after 24 hours; active jobs are excluded. Monitor disk usage; no global disk quota is implemented yet.
- Set provider billing limits. This app has session limits but no account system; an anonymous public endpoint is unsuitable for unrestricted long-term hosting.
- A deployment smoke test must verify queue, worker and Spark behavior; `/api/health/` alone is only a liveness check.
- The standalone Spark overlay can be combined as a third Compose file. It increases resource requirements and has its own acceptance checks; do not claim distributed deployment until actually tested.
