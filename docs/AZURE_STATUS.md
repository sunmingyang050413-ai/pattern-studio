# Azure deployment status

Checked 30 September 2026 in the signed-in Azure portal.

- Azure for Students is active; the applicant is subscription owner.
- Education overview shows USD 100 credit, expiring 30 September 2027.
- VM creation completed successfully after user confirmation on 30 September 2026.
- Prepared creation form: `rg-pattern-studio`, VM `pattern-studio`, Japan East, Ubuntu 24.04 LTS x64, trusted launch, Standard_B2as_v2 (2 vCPU, 8 GiB), 30 GiB Standard SSD LRS OS disk, no data disks, no load balancer, no scheduled shutdown, no backup add-on.
- Public inbound ports are initially disabled. Application HTTPS and restricted administrative access must be configured and verified before delivery.
- The final Japan East review page quotes USD 0.098/hour (USD 71.54 per 730 hours) for compute alone and confirms subscription credit applies. Disk, public IP, disk operations, diagnostics and any chargeable transfer are additional. Do not interpret this as an all-inclusive quote or a year of free operation. Compute alone consumes USD 70.56 in 30 days; total credit runway is shorter than the compute-only 42.5-day upper bound.
- East US B-series sizes were unavailable. Australia East B2as_v2 was selectable, but final validation rejected that region with `RequestDisallowedByAzure`. Read-only inspection of the `Allowed resource deployment regions` policy confirms this subscription permits only Malaysia West, Japan East, Korea Central, New Zealand North and Indonesia Central. Japan East is now selected; validation and its updated quote are pending. No policy was modified or bypassed.

Japan East deployment completed successfully. The generated SSH private key was downloaded outside this repository; never commit or package it.

Azure Run Command successfully installed Docker 29.1.3 and Docker Compose 2.40.3 from Ubuntu packages. Docker was enabled and started. The server reported 26 GiB available disk space and 7.1 GiB available RAM. Application containers have not yet been built or started.

Keep the student spending limit and do not upgrade to paid service. Retain credit for review. The account and credit are provisioned; the public application, Docker validation, real S3/LLM integration, repository publication and demonstration video remain pending.
