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
