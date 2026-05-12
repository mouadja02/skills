# devops-and-infrastructure

Skills for **infrastructure-as-code, cloud architecture, containers, security, observability, and incident response** — the production-engineering layer.

## Skills in this category

### Cloud & infrastructure

| Skill | What it does |
| --- | --- |
| [`aws-solution-architect`](./aws-solution-architect/SKILL.md) | Design AWS architectures for startups using serverless patterns and IaC templates — Lambda, API Gateway, CloudFormation, cost optimization, CI/CD. |
| [`terraform-patterns`](./terraform-patterns/SKILL.md) | Terraform IaC — module design patterns, state management, provider configuration, security hardening, policy-as-code with Sentinel/OPA. |
| [`docker-development`](./docker-development/SKILL.md) | Dockerfile optimization, docker-compose orchestration, multi-stage builds, container security hardening. |
| [`helm-chart-builder`](./helm-chart-builder/SKILL.md) | Helm chart development — chart scaffolding, values design, template patterns, dependency management, chart testing. |
| [`saas-scaffolder`](./saas-scaffolder/SKILL.md) | Generates a complete production-ready SaaS boilerplate — Next.js 14+ App Router, TypeScript, Tailwind, shadcn/ui, Drizzle ORM, Stripe, auth. |

### CI/CD & operations

| Skill | What it does |
| --- | --- |
| [`ci-cd-pipeline-builder`](./ci-cd-pipeline-builder/SKILL.md) | Generate pragmatic CI/CD pipelines tailored to a repo's detected stack. GitHub Actions, GitLab CI, lint/test/build/deploy stages, caching, matrix builds. |
| [`senior-devops`](./senior-devops/SKILL.md) | Comprehensive DevOps — CI/CD, IaC, containerization, AWS/GCP/Azure deployment automation, monitoring. |

### Observability & reliability

| Skill | What it does |
| --- | --- |
| [`observability-designer`](./observability-designer/SKILL.md) | Production observability strategy — SLI/SLO/SLA frameworks, error budgets, golden signals, RED/USE methods, structured logs, distributed tracing, dashboards. |
| [`incident-commander`](./incident-commander/SKILL.md) | Run incident response from detection to PIR — sev1/sev2 triage, severity classification, timeline reconstruction, blameless retros, runbook generation. |

### Security

| Skill | What it does |
| --- | --- |
| [`senior-security`](./senior-security/SKILL.md) | Security engineering — threat modeling (STRIDE), OWASP, vulnerability analysis, secure architecture, cryptography, penetration testing. |
| [`senior-secops`](./senior-secops/SKILL.md) | Application security — SAST/DAST scans, CVE remediation plans, dependency vulnerabilities, security policies, secure development practices. |
| [`dependency-auditor`](./dependency-auditor/SKILL.md) | Audit dependencies for vulnerabilities, license compliance, and tree health across multi-language projects. CVE scanning, supply-chain security, upgrade planning. |

### Data & integrations

| Skill | What it does |
| --- | --- |
| [`database-designer`](./database-designer/SKILL.md) | Design and audit relational schemas. Normalization (1NF-BCNF), index optimization, zero-downtime expand-contract migrations, ERD generation in Mermaid. |
| [`stripe-integration-expert`](./stripe-integration-expert/SKILL.md) | Production-grade Stripe integrations — subscriptions with trials/proration, one-time payments, usage-based billing, idempotent webhooks, customer portal. Next.js, Express, Django. |

### Azure cloud

| Skill | What it does |
| --- | --- |
| [`azure-architecture-autopilot`](./azure-architecture-autopilot/SKILL.md) | Auto-generate Azure architecture diagrams and IaC from requirements. |
| [`azure-deployment-preflight`](./azure-deployment-preflight/SKILL.md) | Pre-flight checks before Azure deployments — quota, permissions, policy compliance. |
| [`azure-devops-cli`](./azure-devops-cli/SKILL.md) | Use the Azure DevOps CLI (`az devops`) for pipelines, repos, work items, and artifacts. |
| [`azure-pricing`](./azure-pricing/SKILL.md) | Estimate and optimize Azure resource costs using the pricing calculator and APIs. |
| [`azure-resource-health-diagnose`](./azure-resource-health-diagnose/SKILL.md) | Diagnose Azure resource health issues — outages, degradation, root causes. |
| [`azure-resource-visualizer`](./azure-resource-visualizer/SKILL.md) | Visualize Azure resource relationships and dependencies in diagrams. |
| [`azure-role-selector`](./azure-role-selector/SKILL.md) | Select the right Azure RBAC roles with least-privilege principles. |
| [`azure-smart-city-iot-solution-builder`](./azure-smart-city-iot-solution-builder/SKILL.md) | Build smart city IoT solutions on Azure IoT Hub, Stream Analytics, and Digital Twins. |
| [`azure-static-web-apps`](./azure-static-web-apps/SKILL.md) | Deploy and configure Azure Static Web Apps with GitHub Actions CI/CD. |
| [`az-cost-optimize`](./az-cost-optimize/SKILL.md) | Identify and implement Azure cost optimization opportunities. |
| [`arduino-azure-iot-edge-integration`](./arduino-azure-iot-edge-integration/SKILL.md) | Integrate Arduino devices with Azure IoT Edge for edge computing. |
| [`python-azure-iot-edge-modules`](./python-azure-iot-edge-modules/SKILL.md) | Build Azure IoT Edge modules in Python for edge data processing. |
| [`aws-cdk-python-setup`](./aws-cdk-python-setup/SKILL.md) | Set up AWS CDK with Python — bootstrapping, stacks, constructs, deployment. |
| [`update-avm-modules-in-bicep`](./update-avm-modules-in-bicep/SKILL.md) | Update Azure Verified Modules (AVM) references in Bicep templates. |
| [`terraform-azurerm-set-diff-analyzer`](./terraform-azurerm-set-diff-analyzer/SKILL.md) | Analyze set-based diffs in Terraform azurerm provider plans. |
| [`import-infrastructure-as-code`](./import-infrastructure-as-code/SKILL.md) | Import existing cloud resources into IaC state — Terraform, Bicep, CDK. |

### Linux & containers

| Skill | What it does |
| --- | --- |
| [`arch-linux-triage`](./arch-linux-triage/SKILL.md) | Diagnose and fix Arch Linux system issues — pacman, systemd, AUR, kernel. |
| [`centos-linux-triage`](./centos-linux-triage/SKILL.md) | Diagnose and fix CentOS/RHEL system issues — yum/dnf, SELinux, systemd. |
| [`debian-linux-triage`](./debian-linux-triage/SKILL.md) | Diagnose and fix Debian/Ubuntu system issues — apt, dpkg, systemd. |
| [`fedora-linux-triage`](./fedora-linux-triage/SKILL.md) | Diagnose and fix Fedora system issues — dnf, SELinux, Flatpak, systemd. |
| [`containerize-aspnetcore`](./containerize-aspnetcore/SKILL.md) | Containerize ASP.NET Core applications with optimized Dockerfiles. |
| [`containerize-aspnet-framework`](./containerize-aspnet-framework/SKILL.md) | Containerize legacy ASP.NET Framework applications using Windows containers. |
| [`multi-stage-dockerfile`](./multi-stage-dockerfile/SKILL.md) | Write optimized multi-stage Dockerfiles for minimal production images. |
| [`lsp-setup`](./lsp-setup/SKILL.md) | Set up Language Server Protocol (LSP) for editors and development environments. |
| [`image-manipulation-image-magick`](./image-manipulation-image-magick/SKILL.md) | Batch process and manipulate images using ImageMagick. |

### Security & compliance

| Skill | What it does |
| --- | --- |
| [`data-breach-blast-radius`](./data-breach-blast-radius/SKILL.md) | Assess the blast radius of a data breach — affected data, systems, regulatory exposure. |
| [`dependabot`](./dependabot/SKILL.md) | Configure and manage Dependabot for automated dependency security updates. |
| [`devops-rollout-plan`](./devops-rollout-plan/SKILL.md) | Create safe rollout plans — canary, blue/green, feature flags, rollback procedures. |
| [`publish-to-pages`](./publish-to-pages/SKILL.md) | Publish static sites to GitHub Pages or Azure Static Web Apps via CI/CD. |
| [`sandbox-npm-install`](./sandbox-npm-install/SKILL.md) | Safely test npm package installations in isolated sandboxes. |
| [`secret-scanning`](./secret-scanning/SKILL.md) | Scan repositories for exposed secrets, API keys, and credentials. |
| [`threat-model-analyst`](./threat-model-analyst/SKILL.md) | STRIDE/DREAD threat modeling for systems, APIs, and data flows. |

## Suggested workflow

```
aws-solution-architect (design)  →  terraform-patterns (provision)  →
  docker-development / helm-chart-builder (package)  →
    ci-cd-pipeline-builder + senior-devops (ship)  →
      observability-designer (monitor)  →  incident-commander (when it breaks)
```

## Related categories

- [`business-and-strategy/ciso-advisor`](../business-and-strategy/ciso-advisor/) — strategic security & compliance roadmap.
- [`business-and-strategy/cto-advisor`](../business-and-strategy/cto-advisor/) — strategic technology decisions.
- [`engineering-craft/senior-architect`](../engineering-craft/senior-architect/) — pre-deployment architecture decisions.
- [`data-and-backend/`](../data-and-backend/) — Snowflake, dbt, Python backends.
