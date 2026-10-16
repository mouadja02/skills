# Third-Party Sources

This repository includes skills adapted from public upstream projects. Every imported `SKILL.md` declares
`source`, `attribution`, and `license` in its frontmatter and repeats the credit in a `> **Attribution:**`
line directly below the frontmatter. Imported folders also carry the upstream `LICENSE` (and `NOTICE`
where the upstream ships one), so each skill stays compliant when it is installed or zipped on its own.

The sections below describe each import. The [attribution index](#attribution-index) at the end is
generated from frontmatter by `scripts/build-manifest.mjs` and lists every sourced skill.

## NousResearch Hermes Agent Optional Skills

Source repository: https://github.com/NousResearch/hermes-agent

Imported from `optional-skills/` on the `main` branch:

| Local install path | Upstream path |
| --- | --- |
| `api-backend/rest-graphql-debug` | `optional-skills/software-development/rest-graphql-debug` |
| `communication/one-three-one-rule` | `optional-skills/communication/one-three-one-rule` |
| `creative/concept-diagrams` | `optional-skills/creative/concept-diagrams` |
| `creative/creative-ideation` | `optional-skills/creative/creative-ideation` |
| `devops/docker-management` | `optional-skills/devops/docker-management` |
| `finance/3-statement-model` | `optional-skills/finance/3-statement-model` |
| `finance/comps-analysis` | `optional-skills/finance/comps-analysis` |
| `finance/dcf-model` | `optional-skills/finance/dcf-model` |
| `finance/excel-author` | `optional-skills/finance/excel-author` |
| `finance/lbo-model` | `optional-skills/finance/lbo-model` |
| `finance/merger-model` | `optional-skills/finance/merger-model` |
| `finance/pptx-author` | `optional-skills/finance/pptx-author` |
| `mcp/fastmcp` | `optional-skills/mcp/fastmcp` |
| `personal-productivity/memento-flashcards` | `optional-skills/productivity/memento-flashcards` |
| `research/osint-investigation` | `optional-skills/research/osint-investigation` |

License: MIT.

Copyright (c) 2025 Nous Research.

Some imported skills retain additional upstream attribution in their own content, including Anthropic financial-services references where present in the Hermes source.

## Alireza Rezvani Claude Skills

Source repository: https://github.com/alirezarezvani/claude-skills

The following local packages are adapted from the upstream marketing skill bundle and retain source and attribution frontmatter:

- `marketing-and-growth/content-humanizer`
- `marketing-and-growth/content-production`
- `marketing-and-growth/cs-ad-creative`
- `marketing-and-growth/cs-ai-seo`
- `marketing-and-growth/cs-cold-email`
- `marketing-and-growth/cs-copywriting`
- `marketing-and-growth/cs-pricing-strategy`
- `marketing-and-growth/cs-seo-audit`
- `marketing-and-growth/cs-social-media-manager`
- `marketing-and-growth/email-sequence`
- `marketing-and-growth/launch-strategy`
- `marketing-and-growth/marketing-context`
- `marketing-and-growth/marketing-demand-acquisition`
- `marketing-and-growth/marketing-ops`
- `marketing-and-growth/marketing-psychology`
- `marketing-and-growth/onboarding-cro`
- `marketing-and-growth/page-cro`
- `marketing-and-growth/paid-ads`
- `marketing-and-growth/programmatic-seo`
- `marketing-and-growth/signup-flow-cro`
- `marketing-and-growth/x-twitter-growth`

License: MIT.

Copyright (c) 2025 Alireza Rezvani.

## Hallmark

Source repository: https://github.com/Nutlope/hallmark

The local `design-and-ui/hallmark` package is adapted from the upstream `skills/hallmark/` skill and includes its supporting references, documentation, and site assets.

License: MIT.

Copyright (c) 2026 Hallmark contributors.

## Streamlit Agent Skills

Source repository: https://github.com/streamlit/agent-skills

The local `streamlit/developing-with-streamlit` package was adapted from the upstream `developing-with-streamlit/` skill package. Individual nested skills retain source and attribution frontmatter. The upstream repository is archived as of 2026-07-25, and its current tree no longer contains the earlier nested-skill layout.

License: Apache-2.0.

## Qdrant Agent Skills

Source repository: https://github.com/qdrant/skills

Imported from `skills/qdrant-performance-optimization/` and `skills/qdrant-search-quality/` on the `main` branch:

| Local install path | Upstream path |
| --- | --- |
| `llm-tooling/qdrant-performance-optimization` | `skills/qdrant-performance-optimization` |
| `llm-tooling/qdrant-performance-optimization/indexing-performance-optimization` | `skills/qdrant-performance-optimization/indexing-performance-optimization` |
| `llm-tooling/qdrant-performance-optimization/memory-usage-optimization` | `skills/qdrant-performance-optimization/memory-usage-optimization` |
| `llm-tooling/qdrant-performance-optimization/search-speed-optimization` | `skills/qdrant-performance-optimization/search-speed-optimization` |
| `llm-tooling/qdrant-search-quality` | `skills/qdrant-search-quality` |
| `llm-tooling/qdrant-search-quality/diagnosis` | `skills/qdrant-search-quality/diagnosis` |
| `llm-tooling/qdrant-search-quality/search-strategies` | `skills/qdrant-search-quality/search-strategies` |

License: Apache-2.0.

## GitHub Awesome Copilot

Source repository: https://github.com/github/awesome-copilot

| Local install path | Upstream path |
| --- | --- |
| `dev-workflow/github-release` | `skills/github-release` |

License: MIT.

## AWS Agent Toolkit

Source repository: https://github.com/aws/agent-toolkit-for-aws

Imported from `skills/` on the `main` branch (commit `eb968520`, 2026-07-20). AWS's `core-skills/` and `specialized-skills/<group>/` layout is reorganized under a single `cloud-aws` category: the 19 broad service skills live under `cloud-aws/core/`, and the specialized workflows are grouped by domain (`analytics`, `database`, `ec2`, `migration`, `networking`, `operations`, `security`, `serverless`, `storage`, `system-tables`, `web-mobile`). Every imported `SKILL.md` carries `source`/`attribution` frontmatter.

| Local install path | Upstream path |
| --- | --- |
| `cloud-aws/analytics/amazon-opensearch-service` | `skills/specialized-skills/analytics-skills/amazon-opensearch-service` |
| `cloud-aws/analytics/aws-cleanrooms` | `skills/specialized-skills/analytics-skills/aws-cleanrooms` |
| `cloud-aws/analytics/connecting-to-data-source` | `skills/specialized-skills/analytics-skills/connecting-to-data-source` |
| `cloud-aws/analytics/developing-applications-on-managed-service-for-apache-flink` | `skills/specialized-skills/analytics-skills/developing-applications-on-managed-service-for-apache-flink` |
| `cloud-aws/analytics/exploring-data-catalog` | `skills/specialized-skills/analytics-skills/exploring-data-catalog` |
| `cloud-aws/analytics/finding-data-lake-assets` | `skills/specialized-skills/analytics-skills/finding-data-lake-assets` |
| `cloud-aws/analytics/ingesting-into-data-lake` | `skills/specialized-skills/analytics-skills/ingesting-into-data-lake` |
| `cloud-aws/analytics/managing-amazon-msk` | `skills/specialized-skills/analytics-skills/managing-amazon-msk` |
| `cloud-aws/analytics/migrate-to-msk` | `skills/specialized-skills/analytics-skills/migrate-to-msk` |
| `cloud-aws/analytics/querying-data-lake` | `skills/specialized-skills/analytics-skills/querying-data-lake` |
| `cloud-aws/core/amazon-bedrock` | `skills/core-skills/amazon-bedrock` |
| `cloud-aws/core/aws-billing-and-cost-management` | `skills/core-skills/aws-billing-and-cost-management` |
| `cloud-aws/core/aws-blocks` | `skills/core-skills/aws-blocks` |
| `cloud-aws/core/aws-cdk` | `skills/core-skills/aws-cdk` |
| `cloud-aws/core/aws-cloudformation` | `skills/core-skills/aws-cloudformation` |
| `cloud-aws/core/aws-compute` | `skills/core-skills/aws-compute` |
| `cloud-aws/core/aws-containers` | `skills/core-skills/aws-containers` |
| `cloud-aws/core/aws-database` | `skills/core-skills/aws-database` |
| `cloud-aws/core/aws-deployment` | `skills/core-skills/aws-deployment` |
| `cloud-aws/core/aws-iam` | `skills/core-skills/aws-iam` |
| `cloud-aws/core/aws-messaging-and-streaming` | `skills/core-skills/aws-messaging-and-streaming` |
| `cloud-aws/core/aws-networking` | `skills/core-skills/aws-networking` |
| `cloud-aws/core/aws-observability` | `skills/core-skills/aws-observability` |
| `cloud-aws/core/aws-sdk-js-v3-usage` | `skills/core-skills/aws-sdk-js-v3-usage` |
| `cloud-aws/core/aws-sdk-python-usage` | `skills/core-skills/aws-sdk-python-usage` |
| `cloud-aws/core/aws-sdk-swift-usage` | `skills/core-skills/aws-sdk-swift-usage` |
| `cloud-aws/core/aws-serverless` | `skills/core-skills/aws-serverless` |
| `cloud-aws/core/launch-with-aws` | `skills/core-skills/launch-with-aws` |
| `cloud-aws/core/signing-in-to-aws` | `skills/core-skills/signing-in-to-aws` |
| `cloud-aws/database/amazon-aurora-mysql` | `skills/specialized-skills/database-skills/amazon-aurora-mysql` |
| `cloud-aws/database/amazon-aurora-postgresql` | `skills/specialized-skills/database-skills/amazon-aurora-postgresql` |
| `cloud-aws/database/amazon-documentdb` | `skills/specialized-skills/database-skills/amazon-documentdb` |
| `cloud-aws/database/amazon-dynamodb` | `skills/specialized-skills/database-skills/amazon-dynamodb` |
| `cloud-aws/database/amazon-elasticache` | `skills/specialized-skills/database-skills/amazon-elasticache` |
| `cloud-aws/database/amazon-keyspaces` | `skills/specialized-skills/database-skills/amazon-keyspaces` |
| `cloud-aws/database/aurora-dsql` | `skills/specialized-skills/database-skills/aurora-dsql` |
| `cloud-aws/database/creating-amazon-aurora-db-cluster-with-instances` | `skills/specialized-skills/database-skills/creating-amazon-aurora-db-cluster-with-instances` |
| `cloud-aws/database/exporting-rds-to-s3` | `skills/specialized-skills/database-skills/exporting-rds-to-s3` |
| `cloud-aws/database/rds-db2` | `skills/specialized-skills/database-skills/rds-db2` |
| `cloud-aws/database/rds-oracle` | `skills/specialized-skills/database-skills/rds-oracle` |
| `cloud-aws/database/rds-oss` | `skills/specialized-skills/database-skills/rds-oss` |
| `cloud-aws/database/rds-sqlserver` | `skills/specialized-skills/database-skills/rds-sqlserver` |
| `cloud-aws/database/timestream-influxdb` | `skills/specialized-skills/database-skills/timestream-influxdb` |
| `cloud-aws/ec2/creating-ec2-image-builder-pipeline` | `skills/specialized-skills/ec2-skills/creating-ec2-image-builder-pipeline` |
| `cloud-aws/ec2/launching-ec2-instance-with-best-practices` | `skills/specialized-skills/ec2-skills/launching-ec2-instance-with-best-practices` |
| `cloud-aws/ec2/setting-up-ec2-instance-profiles` | `skills/specialized-skills/ec2-skills/setting-up-ec2-instance-profiles` |
| `cloud-aws/migration/aws-transform` | `skills/specialized-skills/migration-and-modernization-skills/aws-transform` |
| `cloud-aws/migration/dms-schema-conversion` | `skills/specialized-skills/migration-and-modernization-skills/dms-schema-conversion` |
| `cloud-aws/networking/cloudfront` | `skills/specialized-skills/networking-and-content-delivery-skills/cloudfront` |
| `cloud-aws/networking/configuring-vpc-endpoints-for-private-aws-service-access` | `skills/specialized-skills/networking-and-content-delivery-skills/configuring-vpc-endpoints-for-private-aws-service-access` |
| `cloud-aws/networking/connecting-vpcs-with-peering` | `skills/specialized-skills/networking-and-content-delivery-skills/connecting-vpcs-with-peering` |
| `cloud-aws/networking/creating-production-vpc-multi-az` | `skills/specialized-skills/networking-and-content-delivery-skills/creating-production-vpc-multi-az` |
| `cloud-aws/networking/directconnect` | `skills/specialized-skills/networking-and-content-delivery-skills/directconnect` |
| `cloud-aws/networking/enabling-lambda-vpc-internet-access` | `skills/specialized-skills/networking-and-content-delivery-skills/enabling-lambda-vpc-internet-access` |
| `cloud-aws/networking/route53` | `skills/specialized-skills/networking-and-content-delivery-skills/route53` |
| `cloud-aws/networking/routing-traffic-with-route53-and-cloudfront` | `skills/specialized-skills/networking-and-content-delivery-skills/routing-traffic-with-route53-and-cloudfront` |
| `cloud-aws/networking/shieldadvanced` | `skills/specialized-skills/networking-and-content-delivery-skills/shieldadvanced` |
| `cloud-aws/networking/sitetositevpn` | `skills/specialized-skills/networking-and-content-delivery-skills/sitetositevpn` |
| `cloud-aws/networking/transitgateway` | `skills/specialized-skills/networking-and-content-delivery-skills/transitgateway` |
| `cloud-aws/networking/waf` | `skills/specialized-skills/networking-and-content-delivery-skills/waf` |
| `cloud-aws/operations/aws-network-monitoring` | `skills/specialized-skills/operations-skills/aws-network-monitoring` |
| `cloud-aws/operations/setting-up-cloudtrail-multi-region` | `skills/specialized-skills/operations-skills/setting-up-cloudtrail-multi-region` |
| `cloud-aws/operations/setting-up-cloudwatch-alarm-notifications` | `skills/specialized-skills/operations-skills/setting-up-cloudwatch-alarm-notifications` |
| `cloud-aws/operations/troubleshooting-application-failures` | `skills/specialized-skills/operations-skills/troubleshooting-application-failures` |
| `cloud-aws/security/creating-secrets-using-best-practices` | `skills/specialized-skills/security-and-identity-skills/creating-secrets-using-best-practices` |
| `cloud-aws/serverless/aws-lambda-durable-functions` | `skills/specialized-skills/serverless-skills/aws-lambda-durable-functions` |
| `cloud-aws/serverless/aws-lambda-managed-instances` | `skills/specialized-skills/serverless-skills/aws-lambda-managed-instances` |
| `cloud-aws/serverless/aws-lambda-microvms` | `skills/specialized-skills/serverless-skills/aws-lambda-microvms` |
| `cloud-aws/serverless/connecting-lambda-to-api-gateway` | `skills/specialized-skills/serverless-skills/connecting-lambda-to-api-gateway` |
| `cloud-aws/serverless/connecting-lambda-to-dynamodb` | `skills/specialized-skills/serverless-skills/connecting-lambda-to-dynamodb` |
| `cloud-aws/serverless/creating-api-gateway-stage` | `skills/specialized-skills/serverless-skills/creating-api-gateway-stage` |
| `cloud-aws/serverless/debugging-lambda-timeouts` | `skills/specialized-skills/serverless-skills/debugging-lambda-timeouts` |
| `cloud-aws/serverless/deploying-custom-domain-rest-api` | `skills/specialized-skills/serverless-skills/deploying-custom-domain-rest-api` |
| `cloud-aws/serverless/processing-s3-uploads-with-step-functions` | `skills/specialized-skills/serverless-skills/processing-s3-uploads-with-step-functions` |
| `cloud-aws/storage/creating-data-lake-table` | `skills/specialized-skills/storage-skills/creating-data-lake-table` |
| `cloud-aws/storage/securing-s3-buckets` | `skills/specialized-skills/storage-skills/securing-s3-buckets` |
| `cloud-aws/storage/storing-and-querying-vectors` | `skills/specialized-skills/storage-skills/storing-and-querying-vectors` |
| `cloud-aws/storage/troubleshooting-efs` | `skills/specialized-skills/storage-skills/troubleshooting-efs` |
| `cloud-aws/storage/troubleshooting-s3-files` | `skills/specialized-skills/storage-skills/troubleshooting-s3-files` |
| `cloud-aws/system-tables/querying-aws-cloudwatch` | `skills/specialized-skills/system-table-skills/querying-aws-cloudwatch` |
| `cloud-aws/system-tables/querying-aws-s3` | `skills/specialized-skills/system-table-skills/querying-aws-s3` |
| `cloud-aws/system-tables/querying-aws-sagemaker-catalog` | `skills/specialized-skills/system-table-skills/querying-aws-sagemaker-catalog` |
| `cloud-aws/web-mobile/aws-amplify` | `skills/specialized-skills/web-and-mobile-development/aws-amplify` |

License: Apache-2.0.

Copyright Amazon.com, Inc. or its affiliates.

`cloud-aws/networking/networkfirewall` was imported from this commit but removed in October 2026: AWS
deleted the skill upstream in [#195](https://github.com/aws/agent-toolkit-for-aws/pull/195), and
`cloud-aws/core/aws-networking` is synced to that change.

## Attribution Audit (October 2026)

Before this audit, 324 skills carried no `source` at all. Each was checked against upstream skill
repositories (github/awesome-copilot, addyosmani/agent-skills, alirezarezvani/claude-skills,
anthropics/skills, obra/superpowers, mattpocock/skills, muratcankoylan/Agent-Skills-for-Context-Engineering,
nextlevelbuilder/ui-ux-pro-max-skill, pbakaus/impeccable, and others):

1. Match the folder name against every `SKILL.md` in the upstream tree.
2. Score body similarity as the share of shared word 5-grams. A score of 0.5 or more against the
   current upstream file was accepted as a match.
3. For lower scores, and for names no longer present upstream, walk the upstream file history
   (including deleted `prompts/*.prompt.md` files from awesome-copilot) and score every revision.
   Every accepted history match scored 0.9 or more except `product-management/experiment-designer`
   (0.21), which is credited as "Adapted from".

276 skills were traced this way and now carry frontmatter credit, a body attribution line, and the
upstream license file. The largest groups are github/awesome-copilot (196), alirezarezvani/claude-skills
(41), and addyosmani/agent-skills (23); nine of the awesome-copilot matches were later removed because
upstream retired them (see below). The remaining unsourced skills had no upstream match by name,
content, or GitHub code search. Some, such as `mcp/mcp-oauth-interoperability-diagnostics` and
`llm-tooling/structured-output-schema-portability`, state in their own text that they are original synthesis.

### Corrected sources

The same check also compared every existing `source` with the named repository's current tree. 75
skills named a repository that never held them, while an identical skill (5-gram match 0.96–1.0) lives
elsewhere. 73 were credited to microsoft/skills, microsoft/azure-skills,
muratcankoylan/Agent-Skills-for-Context-Engineering, or greensock/gsap-skills but come from
github/awesome-copilot; `microsoft-agents/hosted-agents` comes from muratcankoylan, not microsoft/skills;
and `skills-management/find-skills` comes from vercel-labs/skills, not obra/superpowers. Their
frontmatter, attribution lines, and license files now name the real source. The `go-to-market/gtm-*`
skills keep their beingsmit credit: Smit Patel wrote them in beingsmit/technical-product-gtm and
contributed them to awesome-copilot himself.

### Removed: retired or superseded upstream

These skills were removed because the project they came from deleted or replaced them, so the copies
here no longer received fixes:

| Removed | Upstream decision |
| --- | --- |
| `design-and-ui/web-coder`, `dev-workflow/my-issues`, `dev-workflow/my-pull-requests`, `llm-tooling/model-recommendation`, `product-management/create-github-pull-request-from-specification`, `prompting/prompt-builder`, `skills-management/make-skill-template` | Deleted from github/awesome-copilot as legacy skills ([#1756](https://github.com/github/awesome-copilot/pull/1756)). |
| `dev-workflow/gh-cli` | Deleted from awesome-copilot as no longer needed once Copilot CLI handled `gh` natively ([#1692](https://github.com/github/awesome-copilot/pull/1692)). |
| `testing/polyglot-test-agent` | Replaced in awesome-copilot by an external dotnet-test plugin ([#1685](https://github.com/github/awesome-copilot/pull/1685)). |
| `dotnet/winapp-cli` | Replaced in awesome-copilot by the external winappcli plugin ([#1674](https://github.com/github/awesome-copilot/pull/1674)). |
| `code-quality/grill-me` | Turned into an alias for `grilling` in mattpocock/skills; this collection now ships `code-quality/grilling`. |
| `cloud-aws/networking/networkfirewall` | Deleted from aws/agent-toolkit-for-aws ([#195](https://github.com/aws/agent-toolkit-for-aws/pull/195)). |
| `personal-productivity/one-password` | Withdrawn from steipete/agent-scripts as a private workflow. |

The BMad Method bundle (`agent-design/bmm-skills`) is a snapshot of BMAD v6. Upstream v7 has since
retired the tech-writer agent, consolidated the research skills, and renamed several workflows. The
bundle is kept whole because its module files wire those parts together; re-importing v7 is the
recommended follow-up.

### Removed: `diagrams-slides/pptx`

The audit found that `diagrams-slides/pptx` was a verbatim copy of the `pptx` skill in
[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/pptx). That skill is proprietary.
Its `LICENSE.txt` forbids reproducing it, distributing it, or creating derivative works outside
Anthropic's services, so it was removed. Claude users have it built in. `diagrams-slides/slides` and
`finance/pptx-author` remain as openly licensed alternatives.

## Additions (October 2026)

These skills were imported at the pinned upstream commits below. Folder names follow upstream except
where noted. Supporting files were copied unchanged; only frontmatter and the attribution line were
edited, unless the skill's own attribution line says otherwise.

| Local install path | Upstream | Commit | License |
| --- | --- | --- | --- |
| `context-engineering/caveman` | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) `skills/caveman` | `d262ab38` | Apache-2.0 |
| `context-engineering/caveman-compress` | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) `skills/caveman-compress` | `d262ab38` | Apache-2.0 |
| `context-engineering/session-handoff` | [mattpocock/skills](https://github.com/mattpocock/skills) `skills/productivity/handoff` (renamed from `handoff`) | `49dd158d` | MIT |
| `dev-workflow/git-guardrails` | [mattpocock/skills](https://github.com/mattpocock/skills) `skills/misc/git-guardrails-claude-code` (renamed: skill names may not contain "claude") | `49dd158d` | MIT |
| `skills-management/writing-for-agents` | [mattpocock/skills](https://github.com/mattpocock/skills) `skills/productivity/writing-for-agents` | `49dd158d` | MIT |
| `engineering-craft/improve-codebase-architecture` | [mattpocock/skills](https://github.com/mattpocock/skills) `skills/engineering/improve-codebase-architecture` | `49dd158d` | MIT |
| `engineering-craft/codebase-design` | [mattpocock/skills](https://github.com/mattpocock/skills) `skills/engineering/codebase-design` | `49dd158d` | MIT |
| `engineering-craft/domain-modeling` | [mattpocock/skills](https://github.com/mattpocock/skills) `skills/engineering/domain-modeling` | `49dd158d` | MIT |
| `code-quality/grilling` | [mattpocock/skills](https://github.com/mattpocock/skills) `skills/productivity/grilling` | `49dd158d` | MIT |
| `dev-workflow/iterate-pr` | [getsentry/skills](https://github.com/getsentry/skills) `skills/iterate-pr` | `f57ada2d` | Apache-2.0 |
| `code-quality/find-bugs` | [getsentry/skills](https://github.com/getsentry/skills) `skills/find-bugs` | `f57ada2d` | Apache-2.0 |
| `skills-management/skill-scanner` | [getsentry/skills](https://github.com/getsentry/skills) `skills/skill-scanner` | `f57ada2d` | Apache-2.0 |
| `dev-workflow/permission-settings-audit` | [getsentry/skills](https://github.com/getsentry/skills) `skills/claude-settings-audit` (renamed: skill names may not contain "claude") | `f57ada2d` | Apache-2.0 |
| `coding/constraint-driven-development` | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) `skills/constraint-driven-development` | `aeac41d4` | MIT |
| `coding/observability-and-instrumentation` | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) `skills/observability-and-instrumentation` | `aeac41d4` | MIT |
| `react-frontend/vercel-react-best-practices` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) `skills/react-best-practices` | `063bee94` | MIT |
| `react-frontend/vercel-composition-patterns` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) `skills/composition-patterns` | `063bee94` | MIT |
| `databases/supabase-postgres-best-practices` | [supabase/agent-skills](https://github.com/supabase/agent-skills) `skills/supabase-postgres-best-practices` | `c9be0e93` | MIT |
| `code-quality/differential-review` | [trailofbits/skills](https://github.com/trailofbits/skills) `plugins/differential-review/skills/differential-review` | `5c99c03f` | CC-BY-SA-4.0 |
| `testing/property-based-testing` | [trailofbits/skills](https://github.com/trailofbits/skills) `plugins/property-based-testing/skills/property-based-testing` | `5c99c03f` | CC-BY-SA-4.0 |
| `testing/mutation-testing` | [trailofbits/skills](https://github.com/trailofbits/skills) `plugins/mutation-testing/skills/mutation-testing` | `5c99c03f` | CC-BY-SA-4.0 |
| `devops/supply-chain-risk-auditor` | [trailofbits/skills](https://github.com/trailofbits/skills) `plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor` | `5c99c03f` | CC-BY-SA-4.0 |
| `design-and-ui/design-taste-frontend` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) `skills/taste-skill` | `f624f37a` | MIT |
| `devops/terraform-style-guide` | [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) `plugins/terraform/skills/terraform-style-guide` | `f706481a` | MPL-2.0 |
| `devops/terraform-test` | [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) `plugins/terraform/skills/terraform-test` | `f706481a` | MPL-2.0 |
| `llm-tooling/huggingface-local-models` | [huggingface/skills](https://github.com/huggingface/skills) `skills/huggingface-local-models` | `c3ff942b` | Apache-2.0 |

The Trail of Bits skills are licensed CC BY-SA 4.0, so changes to them must be shared under the same
license. The HashiCorp skills are MPL-2.0, so modified files must stay under MPL-2.0. Vercel's
repository declares MIT in its README and per-skill frontmatter but ships no license file to copy.

Three skills added at the same time were written for this repository from public sources, which each
skill cites: `context-engineering/coding-agent-token-efficiency`, `llm-tooling/llm-cost-optimization`,
and `skills-management/skill-smell-audit`.

## Attribution Index

<!-- generated:attribution-index:start -->
753 of 807 skills declare an upstream `source`, across 58 sources. The remaining 54 declare no upstream source.

### github/awesome-copilot

Source: https://github.com/github/awesome-copilot
Credit: github/awesome-copilot by GitHub Community
License: Apache-2.0; Complete terms in LICENSE.txt; MIT

| Install path | License |
| --- | --- |
| [`agent-design/agent-governance`](../skills/agent-design/agent-governance/SKILL.md) | MIT |
| [`agent-design/agent-owasp-compliance`](../skills/agent-design/agent-owasp-compliance/SKILL.md) | MIT |
| [`agent-design/agent-supply-chain`](../skills/agent-design/agent-supply-chain/SKILL.md) | MIT |
| [`agent-design/ai-ready`](../skills/agent-design/ai-ready/SKILL.md) | MIT |
| [`agent-design/ai-team-orchestration`](../skills/agent-design/ai-team-orchestration/SKILL.md) | MIT |
| [`agent-design/create-agentsmd`](../skills/agent-design/create-agentsmd/SKILL.md) | MIT |
| [`agent-design/structured-autonomy-generate`](../skills/agent-design/structured-autonomy-generate/SKILL.md) | MIT |
| [`agent-design/structured-autonomy-implement`](../skills/agent-design/structured-autonomy-implement/SKILL.md) | MIT |
| [`agent-design/structured-autonomy-plan`](../skills/agent-design/structured-autonomy-plan/SKILL.md) | MIT |
| [`agent-eval/agentic-eval`](../skills/agent-eval/agentic-eval/SKILL.md) | MIT |
| [`agent-eval/memory-merger`](../skills/agent-eval/memory-merger/SKILL.md) | MIT |
| [`agent-eval/nano-banana-pro-openrouter`](../skills/agent-eval/nano-banana-pro-openrouter/SKILL.md) | MIT |
| [`agent-eval/semantic-kernel`](../skills/agent-eval/semantic-kernel/SKILL.md) | MIT |
| [`api-backend/aspnet-minimal-api-openapi`](../skills/api-backend/aspnet-minimal-api-openapi/SKILL.md) | MIT |
| [`api-backend/gdpr-compliant`](../skills/api-backend/gdpr-compliant/SKILL.md) | MIT |
| [`api-backend/openapi-to-application-code`](../skills/api-backend/openapi-to-application-code/SKILL.md) | MIT |
| [`api-backend/python-pypi-package-builder`](../skills/api-backend/python-pypi-package-builder/SKILL.md) | MIT |
| [`api-backend/transloadit-media-processing`](../skills/api-backend/transloadit-media-processing/SKILL.md) | MIT |
| [`api-backend/typespec-api-operations`](../skills/api-backend/typespec-api-operations/SKILL.md) | MIT |
| [`api-backend/typespec-create-agent`](../skills/api-backend/typespec-create-agent/SKILL.md) | MIT |
| [`api-backend/typespec-create-api-plugin`](../skills/api-backend/typespec-create-api-plugin/SKILL.md) | MIT |
| [`business-strategy/brag-sheet`](../skills/business-strategy/brag-sheet/SKILL.md) | MIT |
| [`business-strategy/impediment-prioritization`](../skills/business-strategy/impediment-prioritization/SKILL.md) | MIT |
| [`cloud-azure/arduino-azure-iot-edge-integration`](../skills/cloud-azure/arduino-azure-iot-edge-integration/SKILL.md) | MIT |
| [`cloud-azure/aspire`](../skills/cloud-azure/aspire/SKILL.md) | MIT |
| [`cloud-azure/aws-cdk-python-setup`](../skills/cloud-azure/aws-cdk-python-setup/SKILL.md) | MIT |
| [`cloud-azure/az-cost-optimize`](../skills/cloud-azure/az-cost-optimize/SKILL.md) | MIT |
| [`cloud-azure/azure-architecture-autopilot`](../skills/cloud-azure/azure-architecture-autopilot/SKILL.md) | MIT |
| [`cloud-azure/azure-deployment-preflight`](../skills/cloud-azure/azure-deployment-preflight/SKILL.md) | MIT |
| [`cloud-azure/azure-devops-cli`](../skills/cloud-azure/azure-devops-cli/SKILL.md) | MIT |
| [`cloud-azure/azure-pricing`](../skills/cloud-azure/azure-pricing/SKILL.md) | MIT |
| [`cloud-azure/azure-resource-health-diagnose`](../skills/cloud-azure/azure-resource-health-diagnose/SKILL.md) | MIT |
| [`cloud-azure/azure-role-selector`](../skills/cloud-azure/azure-role-selector/SKILL.md) | MIT |
| [`cloud-azure/azure-smart-city-iot-solution-builder`](../skills/cloud-azure/azure-smart-city-iot-solution-builder/SKILL.md) | MIT |
| [`cloud-azure/azure-static-web-apps`](../skills/cloud-azure/azure-static-web-apps/SKILL.md) | MIT |
| [`cloud-azure/cloud-design-patterns`](../skills/cloud-azure/cloud-design-patterns/SKILL.md) | MIT |
| [`cloud-azure/python-azure-iot-edge-modules`](../skills/cloud-azure/python-azure-iot-edge-modules/SKILL.md) | MIT |
| [`cloud-azure/update-avm-modules-in-bicep`](../skills/cloud-azure/update-avm-modules-in-bicep/SKILL.md) | MIT |
| [`code-quality/audit-integrity`](../skills/code-quality/audit-integrity/SKILL.md) | MIT |
| [`code-quality/codeql`](../skills/code-quality/codeql/SKILL.md) | MIT |
| [`code-quality/doublecheck`](../skills/code-quality/doublecheck/SKILL.md) | MIT |
| [`code-quality/eyeball`](../skills/code-quality/eyeball/SKILL.md) | MIT |
| [`code-quality/refactor`](../skills/code-quality/refactor/SKILL.md) | MIT |
| [`code-quality/refactor-method-complexity-reduce`](../skills/code-quality/refactor-method-complexity-reduce/SKILL.md) | MIT |
| [`code-quality/refactor-plan`](../skills/code-quality/refactor-plan/SKILL.md) | MIT |
| [`code-quality/review-and-refactor`](../skills/code-quality/review-and-refactor/SKILL.md) | MIT |
| [`code-quality/roundup`](../skills/code-quality/roundup/SKILL.md) | MIT |
| [`code-quality/roundup-setup`](../skills/code-quality/roundup-setup/SKILL.md) | MIT |
| [`code-quality/security-review`](../skills/code-quality/security-review/SKILL.md) | MIT |
| [`context-engineering/acquire-codebase-knowledge`](../skills/context-engineering/acquire-codebase-knowledge/SKILL.md) | MIT |
| [`context-engineering/context-map`](../skills/context-engineering/context-map/SKILL.md) | MIT |
| [`context-engineering/first-ask`](../skills/context-engineering/first-ask/SKILL.md) | MIT |
| [`context-engineering/integrate-context-matic`](../skills/context-engineering/integrate-context-matic/SKILL.md) | MIT |
| [`context-engineering/mini-context-graph`](../skills/context-engineering/mini-context-graph/SKILL.md) | MIT |
| [`context-engineering/napkin`](../skills/context-engineering/napkin/SKILL.md) | MIT |
| [`context-engineering/onboard-context-matic`](../skills/context-engineering/onboard-context-matic/SKILL.md) | MIT |
| [`context-engineering/what-context-needed`](../skills/context-engineering/what-context-needed/SKILL.md) | MIT |
| [`databases/bigquery-pipeline-audit`](../skills/databases/bigquery-pipeline-audit/SKILL.md) | MIT |
| [`databases/cosmosdb-datamodeling`](../skills/databases/cosmosdb-datamodeling/SKILL.md) | MIT |
| [`databases/creating-oracle-to-postgres-master-migration-plan`](../skills/databases/creating-oracle-to-postgres-master-migration-plan/SKILL.md) | MIT |
| [`databases/creating-oracle-to-postgres-migration-bug-report`](../skills/databases/creating-oracle-to-postgres-migration-bug-report/SKILL.md) | MIT |
| [`databases/creating-oracle-to-postgres-migration-integration-tests`](../skills/databases/creating-oracle-to-postgres-migration-integration-tests/SKILL.md) | MIT |
| [`databases/datanalysis-credit-risk`](../skills/databases/datanalysis-credit-risk/SKILL.md) | MIT |
| [`databases/ef-core`](../skills/databases/ef-core/SKILL.md) | MIT |
| [`databases/migrating-oracle-to-postgres-stored-procedures`](../skills/databases/migrating-oracle-to-postgres-stored-procedures/SKILL.md) | MIT |
| [`databases/pdftk-server`](../skills/databases/pdftk-server/SKILL.md) | MIT |
| [`databases/planning-oracle-to-postgres-migration-integration-testing`](../skills/databases/planning-oracle-to-postgres-migration-integration-testing/SKILL.md) | MIT |
| [`databases/postgresql-code-review`](../skills/databases/postgresql-code-review/SKILL.md) | MIT |
| [`databases/postgresql-optimization`](../skills/databases/postgresql-optimization/SKILL.md) | MIT |
| [`databases/reviewing-oracle-to-postgres-migration`](../skills/databases/reviewing-oracle-to-postgres-migration/SKILL.md) | MIT |
| [`databases/scaffolding-oracle-to-postgres-migration-test-project`](../skills/databases/scaffolding-oracle-to-postgres-migration-test-project/SKILL.md) | MIT |
| [`databases/snowflake-semanticview`](../skills/databases/snowflake-semanticview/SKILL.md) | MIT |
| [`databases/sql-code-review`](../skills/databases/sql-code-review/SKILL.md) | MIT |
| [`databases/sql-optimization`](../skills/databases/sql-optimization/SKILL.md) | MIT |
| [`design-and-ui/adobe-illustrator-scripting`](../skills/design-and-ui/adobe-illustrator-scripting/SKILL.md) | MIT |
| [`design-and-ui/content-management-systems`](../skills/design-and-ui/content-management-systems/SKILL.md) | MIT |
| [`design-and-ui/excalidraw-diagram-generator`](../skills/design-and-ui/excalidraw-diagram-generator/SKILL.md) | MIT |
| [`design-and-ui/fluentui-blazor`](../skills/design-and-ui/fluentui-blazor/SKILL.md) | MIT |
| [`design-and-ui/freecad-scripts`](../skills/design-and-ui/freecad-scripts/SKILL.md) | MIT |
| [`design-and-ui/gsap-framer-scroll-animation`](../skills/design-and-ui/gsap-framer-scroll-animation/SKILL.md) | MIT |
| [`design-and-ui/penpot-uiux-design`](../skills/design-and-ui/penpot-uiux-design/SKILL.md) | MIT |
| [`design-and-ui/premium-frontend-ui`](../skills/design-and-ui/premium-frontend-ui/SKILL.md) | MIT |
| [`design-and-ui/slang-shader-engineer`](../skills/design-and-ui/slang-shader-engineer/SKILL.md) | MIT |
| [`design-and-ui/web-design-reviewer`](../skills/design-and-ui/web-design-reviewer/SKILL.md) | MIT |
| [`dev-workflow/add-educational-comments`](../skills/dev-workflow/add-educational-comments/SKILL.md) | MIT |
| [`dev-workflow/automate-this`](../skills/dev-workflow/automate-this/SKILL.md) | MIT |
| [`dev-workflow/batch-files`](../skills/dev-workflow/batch-files/SKILL.md) | MIT |
| [`dev-workflow/chrome-devtools`](../skills/dev-workflow/chrome-devtools/SKILL.md) | MIT |
| [`dev-workflow/commit-message-storyteller`](../skills/dev-workflow/commit-message-storyteller/SKILL.md) | MIT |
| [`dev-workflow/conventional-commit`](../skills/dev-workflow/conventional-commit/SKILL.md) | MIT |
| [`dev-workflow/editorconfig`](../skills/dev-workflow/editorconfig/SKILL.md) | MIT |
| [`dev-workflow/git-commit`](../skills/dev-workflow/git-commit/SKILL.md) | MIT |
| [`dev-workflow/git-flow-branch-creator`](../skills/dev-workflow/git-flow-branch-creator/SKILL.md) | MIT |
| [`dev-workflow/github-issues`](../skills/dev-workflow/github-issues/SKILL.md) | MIT |
| [`dev-workflow/github-release`](../skills/dev-workflow/github-release/SKILL.md) | MIT |
| [`dev-workflow/make-repo-contribution`](../skills/dev-workflow/make-repo-contribution/SKILL.md) | MIT |
| [`dev-workflow/msstore-cli`](../skills/dev-workflow/msstore-cli/SKILL.md) | MIT |
| [`dev-workflow/pr-dashboard`](../skills/dev-workflow/pr-dashboard/SKILL.md) | MIT |
| [`dev-workflow/ruff-recursive-fix`](../skills/dev-workflow/ruff-recursive-fix/SKILL.md) | MIT |
| [`dev-workflow/shuffle-json-data`](../skills/dev-workflow/shuffle-json-data/SKILL.md) | MIT |
| [`devops/arch-linux-triage`](../skills/devops/arch-linux-triage/SKILL.md) | MIT |
| [`devops/centos-linux-triage`](../skills/devops/centos-linux-triage/SKILL.md) | MIT |
| [`devops/containerize-aspnet-framework`](../skills/devops/containerize-aspnet-framework/SKILL.md) | MIT |
| [`devops/containerize-aspnetcore`](../skills/devops/containerize-aspnetcore/SKILL.md) | MIT |
| [`devops/data-breach-blast-radius`](../skills/devops/data-breach-blast-radius/SKILL.md) | MIT |
| [`devops/debian-linux-triage`](../skills/devops/debian-linux-triage/SKILL.md) | MIT |
| [`devops/dependabot`](../skills/devops/dependabot/SKILL.md) | MIT |
| [`devops/devops-rollout-plan`](../skills/devops/devops-rollout-plan/SKILL.md) | MIT |
| [`devops/fedora-linux-triage`](../skills/devops/fedora-linux-triage/SKILL.md) | MIT |
| [`devops/image-manipulation-image-magick`](../skills/devops/image-manipulation-image-magick/SKILL.md) | MIT |
| [`devops/import-infrastructure-as-code`](../skills/devops/import-infrastructure-as-code/SKILL.md) | MIT |
| [`devops/lsp-setup`](../skills/devops/lsp-setup/SKILL.md) | MIT |
| [`devops/multi-stage-dockerfile`](../skills/devops/multi-stage-dockerfile/SKILL.md) | MIT |
| [`devops/sandbox-npm-install`](../skills/devops/sandbox-npm-install/SKILL.md) | MIT |
| [`devops/secret-scanning`](../skills/devops/secret-scanning/SKILL.md) | MIT |
| [`devops/terraform-azurerm-set-diff-analyzer`](../skills/devops/terraform-azurerm-set-diff-analyzer/SKILL.md) | MIT |
| [`devops/threat-model-analyst`](../skills/devops/threat-model-analyst/SKILL.md) | MIT |
| [`diagrams-slides/draw-io-diagram-generator`](../skills/diagrams-slides/draw-io-diagram-generator/SKILL.md) | MIT |
| [`diagrams-slides/drawio`](../skills/diagrams-slides/drawio/SKILL.md) | MIT |
| [`diagrams-slides/email-drafter`](../skills/diagrams-slides/email-drafter/SKILL.md) | MIT |
| [`diagrams-slides/linkedin-post-formatter`](../skills/diagrams-slides/linkedin-post-formatter/SKILL.md) | MIT |
| [`diagrams-slides/meeting-minutes`](../skills/diagrams-slides/meeting-minutes/SKILL.md) | MIT |
| [`diagrams-slides/performance-review-writer`](../skills/diagrams-slides/performance-review-writer/SKILL.md) | MIT |
| [`diagrams-slides/plantuml-ascii`](../skills/diagrams-slides/plantuml-ascii/SKILL.md) | MIT |
| [`diagrams-slides/repo-story-time`](../skills/diagrams-slides/repo-story-time/SKILL.md) | MIT |
| [`documentation/architecture-blueprint-generator`](../skills/documentation/architecture-blueprint-generator/SKILL.md) | MIT |
| [`documentation/code-exemplars-blueprint-generator`](../skills/documentation/code-exemplars-blueprint-generator/SKILL.md) | MIT |
| [`documentation/comment-code-generate-a-tutorial`](../skills/documentation/comment-code-generate-a-tutorial/SKILL.md) | MIT |
| [`documentation/convert-plaintext-to-md`](../skills/documentation/convert-plaintext-to-md/SKILL.md) | MIT |
| [`documentation/create-architectural-decision-record`](../skills/documentation/create-architectural-decision-record/SKILL.md) | MIT |
| [`documentation/create-llms`](../skills/documentation/create-llms/SKILL.md) | MIT |
| [`documentation/create-readme`](../skills/documentation/create-readme/SKILL.md) | MIT |
| [`documentation/create-tldr-page`](../skills/documentation/create-tldr-page/SKILL.md) | MIT |
| [`documentation/documentation-writer`](../skills/documentation/documentation-writer/SKILL.md) | MIT |
| [`documentation/folder-structure-blueprint-generator`](../skills/documentation/folder-structure-blueprint-generator/SKILL.md) | MIT |
| [`documentation/gen-specs-as-issues`](../skills/documentation/gen-specs-as-issues/SKILL.md) | MIT |
| [`documentation/markdown-to-html`](../skills/documentation/markdown-to-html/SKILL.md) | MIT |
| [`documentation/md-to-docx`](../skills/documentation/md-to-docx/SKILL.md) | MIT |
| [`documentation/microsoft-code-reference`](../skills/documentation/microsoft-code-reference/SKILL.md) | MIT |
| [`documentation/mkdocs-translations`](../skills/documentation/mkdocs-translations/SKILL.md) | MIT |
| [`documentation/oo-component-documentation`](../skills/documentation/oo-component-documentation/SKILL.md) | MIT |
| [`documentation/project-workflow-analysis-blueprint-generator`](../skills/documentation/project-workflow-analysis-blueprint-generator/SKILL.md) | MIT |
| [`documentation/publish-to-pages`](../skills/documentation/publish-to-pages/SKILL.md) | MIT |
| [`documentation/readme-blueprint-generator`](../skills/documentation/readme-blueprint-generator/SKILL.md) | MIT |
| [`documentation/technology-stack-blueprint-generator`](../skills/documentation/technology-stack-blueprint-generator/SKILL.md) | MIT |
| [`documentation/update-llms`](../skills/documentation/update-llms/SKILL.md) | MIT |
| [`documentation/update-markdown-file-index`](../skills/documentation/update-markdown-file-index/SKILL.md) | MIT |
| [`dotnet/csharp-async`](../skills/dotnet/csharp-async/SKILL.md) | MIT |
| [`dotnet/csharp-docs`](../skills/dotnet/csharp-docs/SKILL.md) | MIT |
| [`dotnet/csharp-mstest`](../skills/dotnet/csharp-mstest/SKILL.md) | MIT |
| [`dotnet/csharp-nunit`](../skills/dotnet/csharp-nunit/SKILL.md) | MIT |
| [`dotnet/csharp-tunit`](../skills/dotnet/csharp-tunit/SKILL.md) | MIT |
| [`dotnet/csharp-xunit`](../skills/dotnet/csharp-xunit/SKILL.md) | MIT |
| [`dotnet/dotnet-best-practices`](../skills/dotnet/dotnet-best-practices/SKILL.md) | MIT |
| [`dotnet/dotnet-design-pattern-review`](../skills/dotnet/dotnet-design-pattern-review/SKILL.md) | MIT |
| [`dotnet/dotnet-timezone`](../skills/dotnet/dotnet-timezone/SKILL.md) | MIT |
| [`dotnet/dotnet-upgrade`](../skills/dotnet/dotnet-upgrade/SKILL.md) | MIT |
| [`dotnet/mvvm-toolkit`](../skills/dotnet/mvvm-toolkit/SKILL.md) | MIT |
| [`dotnet/mvvm-toolkit-di`](../skills/dotnet/mvvm-toolkit-di/SKILL.md) | MIT |
| [`dotnet/mvvm-toolkit-messenger`](../skills/dotnet/mvvm-toolkit-messenger/SKILL.md) | MIT |
| [`dotnet/nuget-manager`](../skills/dotnet/nuget-manager/SKILL.md) | MIT |
| [`dotnet/vscode-ext-commands`](../skills/dotnet/vscode-ext-commands/SKILL.md) | MIT |
| [`dotnet/vscode-ext-localization`](../skills/dotnet/vscode-ext-localization/SKILL.md) | MIT |
| [`dotnet/winmd-api-search`](../skills/dotnet/winmd-api-search/SKILL.md) | Complete terms in LICENSE.txt |
| [`dotnet/winui3-migration-guide`](../skills/dotnet/winui3-migration-guide/SKILL.md) | MIT |
| [`engineering-craft/code-tour`](../skills/engineering-craft/code-tour/SKILL.md) | MIT |
| [`engineering-craft/game-engine`](../skills/engineering-craft/game-engine/SKILL.md) | MIT |
| [`engineering-craft/geofeed-tuner`](../skills/engineering-craft/geofeed-tuner/SKILL.md) | Apache-2.0 |
| [`engineering-craft/mentoring-juniors`](../skills/engineering-craft/mentoring-juniors/SKILL.md) | MIT |
| [`engineering-craft/minecraft-plugin-development`](../skills/engineering-craft/minecraft-plugin-development/SKILL.md) | MIT |
| [`engineering-craft/noob-mode`](../skills/engineering-craft/noob-mode/SKILL.md) | MIT |
| [`engineering-craft/quasi-coder`](../skills/engineering-craft/quasi-coder/SKILL.md) | MIT |
| [`engineering-craft/remember-interactive-programming`](../skills/engineering-craft/remember-interactive-programming/SKILL.md) | MIT |
| [`engineering-craft/resemble-detect`](../skills/engineering-craft/resemble-detect/SKILL.md) | Apache-2.0 |
| [`engineering-craft/salesforce-apex-quality`](../skills/engineering-craft/salesforce-apex-quality/SKILL.md) | MIT |
| [`engineering-craft/salesforce-component-standards`](../skills/engineering-craft/salesforce-component-standards/SKILL.md) | MIT |
| [`engineering-craft/salesforce-flow-design`](../skills/engineering-craft/salesforce-flow-design/SKILL.md) | MIT |
| [`engineering-craft/write-coding-standards-from-file`](../skills/engineering-craft/write-coding-standards-from-file/SKILL.md) | MIT |
| [`engineering-craft/x-twitter-scraper`](../skills/engineering-craft/x-twitter-scraper/SKILL.md) | MIT |
| [`java-kotlin/create-spring-boot-java-project`](../skills/java-kotlin/create-spring-boot-java-project/SKILL.md) | MIT |
| [`java-kotlin/create-spring-boot-kotlin-project`](../skills/java-kotlin/create-spring-boot-kotlin-project/SKILL.md) | MIT |
| [`java-kotlin/java-add-graalvm-native-image-support`](../skills/java-kotlin/java-add-graalvm-native-image-support/SKILL.md) | MIT |
| [`java-kotlin/java-docs`](../skills/java-kotlin/java-docs/SKILL.md) | MIT |
| [`java-kotlin/java-junit`](../skills/java-kotlin/java-junit/SKILL.md) | MIT |
| [`java-kotlin/java-refactoring-extract-method`](../skills/java-kotlin/java-refactoring-extract-method/SKILL.md) | MIT |
| [`java-kotlin/java-refactoring-remove-parameter`](../skills/java-kotlin/java-refactoring-remove-parameter/SKILL.md) | MIT |
| [`java-kotlin/java-springboot`](../skills/java-kotlin/java-springboot/SKILL.md) | MIT |
| [`java-kotlin/javax-to-jakarta-migration`](../skills/java-kotlin/javax-to-jakarta-migration/SKILL.md) | MIT |
| [`java-kotlin/kotlin-springboot`](../skills/java-kotlin/kotlin-springboot/SKILL.md) | MIT |
| [`java-kotlin/spring-boot-testing`](../skills/java-kotlin/spring-boot-testing/SKILL.md) | MIT |
| [`marketing-and-growth/apple-appstore-reviewer`](../skills/marketing-and-growth/apple-appstore-reviewer/SKILL.md) | MIT |
| [`marketing-and-growth/finnish-humanizer`](../skills/marketing-and-growth/finnish-humanizer/SKILL.md) | MIT |
| [`marketing-and-growth/sponsor-finder`](../skills/marketing-and-growth/sponsor-finder/SKILL.md) | MIT |
| [`mcp/dotnet-mcp-builder`](../skills/mcp/dotnet-mcp-builder/SKILL.md) | MIT |
| [`mcp/go-mcp-server-generator`](../skills/mcp/go-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/java-mcp-server-generator`](../skills/mcp/java-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/kotlin-mcp-server-generator`](../skills/mcp/kotlin-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/mcp-cli`](../skills/mcp/mcp-cli/SKILL.md) | MIT |
| [`mcp/mcp-security-audit`](../skills/mcp/mcp-security-audit/SKILL.md) | MIT |
| [`mcp/php-mcp-server-generator`](../skills/mcp/php-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/python-mcp-server-generator`](../skills/mcp/python-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/ruby-mcp-server-generator`](../skills/mcp/ruby-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/rust-mcp-server-generator`](../skills/mcp/rust-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/swift-mcp-server-generator`](../skills/mcp/swift-mcp-server-generator/SKILL.md) | MIT |
| [`mcp/typescript-mcp-server-generator`](../skills/mcp/typescript-mcp-server-generator/SKILL.md) | MIT |
| [`microsoft-agents/declarative-agents`](../skills/microsoft-agents/declarative-agents/SKILL.md) | MIT |
| [`microsoft-agents/entra-agent-user`](../skills/microsoft-agents/entra-agent-user/SKILL.md) | MIT |
| [`microsoft-agents/foundry-agent-sync`](../skills/microsoft-agents/foundry-agent-sync/SKILL.md) | MIT |
| [`microsoft-agents/from-the-other-side-vega`](../skills/microsoft-agents/from-the-other-side-vega/SKILL.md) | MIT |
| [`microsoft-agents/mcp-copilot-studio-server-generator`](../skills/microsoft-agents/mcp-copilot-studio-server-generator/SKILL.md) | MIT |
| [`microsoft-agents/mcp-create-adaptive-cards`](../skills/microsoft-agents/mcp-create-adaptive-cards/SKILL.md) | MIT |
| [`microsoft-agents/mcp-create-declarative-agent`](../skills/microsoft-agents/mcp-create-declarative-agent/SKILL.md) | MIT |
| [`microsoft-agents/mcp-deploy-manage-agents`](../skills/microsoft-agents/mcp-deploy-manage-agents/SKILL.md) | MIT |
| [`microsoft-agents/microsoft-agent-framework`](../skills/microsoft-agents/microsoft-agent-framework/SKILL.md) | MIT |
| [`microsoft-agents/workiq-copilot`](../skills/microsoft-agents/workiq-copilot/SKILL.md) | MIT |
| [`microsoft-data/dataverse-python-advanced-patterns`](../skills/microsoft-data/dataverse-python-advanced-patterns/SKILL.md) | MIT |
| [`microsoft-data/dataverse-python-production-code`](../skills/microsoft-data/dataverse-python-production-code/SKILL.md) | MIT |
| [`microsoft-data/dataverse-python-quickstart`](../skills/microsoft-data/dataverse-python-quickstart/SKILL.md) | MIT |
| [`microsoft-data/dataverse-python-usecase-builder`](../skills/microsoft-data/dataverse-python-usecase-builder/SKILL.md) | MIT |
| [`microsoft-data/flowstudio-power-automate-build`](../skills/microsoft-data/flowstudio-power-automate-build/SKILL.md) | MIT |
| [`microsoft-data/flowstudio-power-automate-debug`](../skills/microsoft-data/flowstudio-power-automate-debug/SKILL.md) | MIT |
| [`microsoft-data/flowstudio-power-automate-governance`](../skills/microsoft-data/flowstudio-power-automate-governance/SKILL.md) | MIT |
| [`microsoft-data/flowstudio-power-automate-mcp`](../skills/microsoft-data/flowstudio-power-automate-mcp/SKILL.md) | MIT |
| [`microsoft-data/flowstudio-power-automate-monitoring`](../skills/microsoft-data/flowstudio-power-automate-monitoring/SKILL.md) | MIT |
| [`microsoft-data/power-apps-code-app-scaffold`](../skills/microsoft-data/power-apps-code-app-scaffold/SKILL.md) | MIT |
| [`microsoft-data/power-bi-dax-optimization`](../skills/microsoft-data/power-bi-dax-optimization/SKILL.md) | MIT |
| [`microsoft-data/power-bi-model-design-review`](../skills/microsoft-data/power-bi-model-design-review/SKILL.md) | MIT |
| [`microsoft-data/power-bi-performance-troubleshooting`](../skills/microsoft-data/power-bi-performance-troubleshooting/SKILL.md) | MIT |
| [`microsoft-data/power-bi-report-design-consultation`](../skills/microsoft-data/power-bi-report-design-consultation/SKILL.md) | MIT |
| [`microsoft-data/power-platform-architect`](../skills/microsoft-data/power-platform-architect/SKILL.md) | MIT |
| [`microsoft-data/power-platform-mcp-connector-suite`](../skills/microsoft-data/power-platform-mcp-connector-suite/SKILL.md) | MIT |
| [`microsoft-data/powerbi-modeling`](../skills/microsoft-data/powerbi-modeling/SKILL.md) | MIT |
| [`product-management/breakdown-epic-arch`](../skills/product-management/breakdown-epic-arch/SKILL.md) | MIT |
| [`product-management/breakdown-epic-pm`](../skills/product-management/breakdown-epic-pm/SKILL.md) | MIT |
| [`product-management/breakdown-feature-implementation`](../skills/product-management/breakdown-feature-implementation/SKILL.md) | MIT |
| [`product-management/breakdown-feature-prd`](../skills/product-management/breakdown-feature-prd/SKILL.md) | MIT |
| [`product-management/breakdown-plan`](../skills/product-management/breakdown-plan/SKILL.md) | MIT |
| [`product-management/breakdown-test`](../skills/product-management/breakdown-test/SKILL.md) | MIT |
| [`product-management/create-github-action-workflow-specification`](../skills/product-management/create-github-action-workflow-specification/SKILL.md) | MIT |
| [`product-management/create-github-issue-feature-from-specification`](../skills/product-management/create-github-issue-feature-from-specification/SKILL.md) | MIT |
| [`product-management/create-github-issues-feature-from-implementation-plan`](../skills/product-management/create-github-issues-feature-from-implementation-plan/SKILL.md) | MIT |
| [`product-management/create-github-issues-for-unmet-specification-requirements`](../skills/product-management/create-github-issues-for-unmet-specification-requirements/SKILL.md) | MIT |
| [`product-management/create-implementation-plan`](../skills/product-management/create-implementation-plan/SKILL.md) | MIT |
| [`product-management/create-specification`](../skills/product-management/create-specification/SKILL.md) | MIT |
| [`product-management/create-technical-spike`](../skills/product-management/create-technical-spike/SKILL.md) | MIT |
| [`product-management/daily-prep`](../skills/product-management/daily-prep/SKILL.md) | MIT |
| [`product-management/issue-fields-migration`](../skills/product-management/issue-fields-migration/SKILL.md) | MIT |
| [`product-management/prd`](../skills/product-management/prd/SKILL.md) | MIT |
| [`product-management/update-implementation-plan`](../skills/product-management/update-implementation-plan/SKILL.md) | MIT |
| [`product-management/update-specification`](../skills/product-management/update-specification/SKILL.md) | MIT |
| [`prompting/ai-prompt-engineering-safety-review`](../skills/prompting/ai-prompt-engineering-safety-review/SKILL.md) | MIT |
| [`prompting/boost-prompt`](../skills/prompting/boost-prompt/SKILL.md) | MIT |
| [`prompting/finalize-agent-prompt`](../skills/prompting/finalize-agent-prompt/SKILL.md) | MIT |
| [`prompting/tldr-prompt`](../skills/prompting/tldr-prompt/SKILL.md) | MIT |
| [`react-frontend/javascript-typescript-jest`](../skills/react-frontend/javascript-typescript-jest/SKILL.md) | MIT |
| [`react-frontend/next-intl-add-language`](../skills/react-frontend/next-intl-add-language/SKILL.md) | MIT |
| [`react-frontend/react-audit-grep-patterns`](../skills/react-frontend/react-audit-grep-patterns/SKILL.md) | MIT |
| [`react-frontend/react18-batching-patterns`](../skills/react-frontend/react18-batching-patterns/SKILL.md) | MIT |
| [`react-frontend/react18-dep-compatibility`](../skills/react-frontend/react18-dep-compatibility/SKILL.md) | MIT |
| [`react-frontend/react18-enzyme-to-rtl`](../skills/react-frontend/react18-enzyme-to-rtl/SKILL.md) | MIT |
| [`react-frontend/react18-legacy-context`](../skills/react-frontend/react18-legacy-context/SKILL.md) | MIT |
| [`react-frontend/react18-lifecycle-patterns`](../skills/react-frontend/react18-lifecycle-patterns/SKILL.md) | MIT |
| [`react-frontend/react18-string-refs`](../skills/react-frontend/react18-string-refs/SKILL.md) | MIT |
| [`react-frontend/react19-concurrent-patterns`](../skills/react-frontend/react19-concurrent-patterns/SKILL.md) | MIT |
| [`react-frontend/react19-source-patterns`](../skills/react-frontend/react19-source-patterns/SKILL.md) | MIT |
| [`react-frontend/react19-test-patterns`](../skills/react-frontend/react19-test-patterns/SKILL.md) | MIT |
| [`react-frontend/unit-test-vue-pinia`](../skills/react-frontend/unit-test-vue-pinia/SKILL.md) | MIT |
| [`skills-management/acreadiness-assess`](../skills/skills-management/acreadiness-assess/SKILL.md) | MIT |
| [`skills-management/acreadiness-generate-instructions`](../skills/skills-management/acreadiness-generate-instructions/SKILL.md) | MIT |
| [`skills-management/acreadiness-policy`](../skills/skills-management/acreadiness-policy/SKILL.md) | MIT |
| [`skills-management/copilot-instructions-blueprint-generator`](../skills/skills-management/copilot-instructions-blueprint-generator/SKILL.md) | MIT |
| [`skills-management/copilot-sdk`](../skills/skills-management/copilot-sdk/SKILL.md) | MIT |
| [`skills-management/copilot-usage-metrics`](../skills/skills-management/copilot-usage-metrics/SKILL.md) | MIT |
| [`skills-management/microsoft-skill-creator`](../skills/skills-management/microsoft-skill-creator/SKILL.md) | MIT |
| [`testing/diagnose`](../skills/testing/diagnose/SKILL.md) | MIT |
| [`testing/exam-ready`](../skills/testing/exam-ready/SKILL.md) | MIT |
| [`testing/playwright-automation-fill-in-form`](../skills/testing/playwright-automation-fill-in-form/SKILL.md) | MIT |
| [`testing/playwright-explore-website`](../skills/testing/playwright-explore-website/SKILL.md) | MIT |
| [`testing/playwright-generate-test`](../skills/testing/playwright-generate-test/SKILL.md) | MIT |
| [`testing/pytest-coverage`](../skills/testing/pytest-coverage/SKILL.md) | MIT |
| [`testing/scoutqa-test`](../skills/testing/scoutqa-test/SKILL.md) | MIT |
| [`testing/webapp-testing`](../skills/testing/webapp-testing/SKILL.md) | MIT |

### alirezarezvani/claude-skills

Source: https://github.com/alirezarezvani/claude-skills
Credit: alirezarezvani/claude-skills by Alireza Rezvani
License: MIT

| Install path | License |
| --- | --- |
| [`agent-eval/auto-memory-pro`](../skills/agent-eval/auto-memory-pro/SKILL.md) | MIT |
| [`agent-eval/auto-memory-pro/skills/extract`](../skills/agent-eval/auto-memory-pro/skills/extract/SKILL.md) | MIT |
| [`agent-eval/auto-memory-pro/skills/promote`](../skills/agent-eval/auto-memory-pro/skills/promote/SKILL.md) | MIT |
| [`agent-eval/auto-memory-pro/skills/remember`](../skills/agent-eval/auto-memory-pro/skills/remember/SKILL.md) | MIT |
| [`agent-eval/auto-memory-pro/skills/review`](../skills/agent-eval/auto-memory-pro/skills/review/SKILL.md) | MIT |
| [`agent-eval/auto-memory-pro/skills/status`](../skills/agent-eval/auto-memory-pro/skills/status/SKILL.md) | MIT |
| [`agent-eval/autoresearch-agent`](../skills/agent-eval/autoresearch-agent/SKILL.md) | MIT |
| [`agent-eval/autoresearch-agent/skills/loop`](../skills/agent-eval/autoresearch-agent/skills/loop/SKILL.md) | MIT |
| [`agent-eval/autoresearch-agent/skills/resume`](../skills/agent-eval/autoresearch-agent/skills/resume/SKILL.md) | MIT |
| [`agent-eval/autoresearch-agent/skills/run`](../skills/agent-eval/autoresearch-agent/skills/run/SKILL.md) | MIT |
| [`agent-eval/autoresearch-agent/skills/setup`](../skills/agent-eval/autoresearch-agent/skills/setup/SKILL.md) | MIT |
| [`api-backend/stripe-integration-expert`](../skills/api-backend/stripe-integration-expert/SKILL.md) | MIT |
| [`business-strategy/agent-protocol`](../skills/business-strategy/agent-protocol/SKILL.md) | MIT |
| [`business-strategy/board-deck-builder`](../skills/business-strategy/board-deck-builder/SKILL.md) | MIT |
| [`business-strategy/board-meeting`](../skills/business-strategy/board-meeting/SKILL.md) | MIT |
| [`business-strategy/c-level-advisor`](../skills/business-strategy/c-level-advisor/SKILL.md) | MIT |
| [`business-strategy/ceo-advisor`](../skills/business-strategy/ceo-advisor/SKILL.md) | MIT |
| [`business-strategy/cfo-advisor`](../skills/business-strategy/cfo-advisor/SKILL.md) | MIT |
| [`business-strategy/change-management`](../skills/business-strategy/change-management/SKILL.md) | MIT |
| [`business-strategy/chief-of-staff`](../skills/business-strategy/chief-of-staff/SKILL.md) | MIT |
| [`business-strategy/chro-advisor`](../skills/business-strategy/chro-advisor/SKILL.md) | MIT |
| [`business-strategy/ciso-advisor`](../skills/business-strategy/ciso-advisor/SKILL.md) | MIT |
| [`business-strategy/cmo-advisor`](../skills/business-strategy/cmo-advisor/SKILL.md) | MIT |
| [`business-strategy/company-os`](../skills/business-strategy/company-os/SKILL.md) | MIT |
| [`business-strategy/competitive-intel`](../skills/business-strategy/competitive-intel/SKILL.md) | MIT |
| [`business-strategy/context-engine`](../skills/business-strategy/context-engine/SKILL.md) | MIT |
| [`business-strategy/coo-advisor`](../skills/business-strategy/coo-advisor/SKILL.md) | MIT |
| [`business-strategy/cpo-advisor`](../skills/business-strategy/cpo-advisor/SKILL.md) | MIT |
| [`business-strategy/cro-advisor`](../skills/business-strategy/cro-advisor/SKILL.md) | MIT |
| [`business-strategy/cs-founder-coach`](../skills/business-strategy/cs-founder-coach/SKILL.md) | MIT |
| [`business-strategy/cs-onboard`](../skills/business-strategy/cs-onboard/SKILL.md) | MIT |
| [`business-strategy/cto-advisor`](../skills/business-strategy/cto-advisor/SKILL.md) | MIT |
| [`business-strategy/culture-architect`](../skills/business-strategy/culture-architect/SKILL.md) | MIT |
| [`business-strategy/decision-logger`](../skills/business-strategy/decision-logger/SKILL.md) | MIT |
| [`business-strategy/executive-mentor`](../skills/business-strategy/executive-mentor/SKILL.md) | MIT |
| [`business-strategy/executive-mentor/skills/board-prep`](../skills/business-strategy/executive-mentor/skills/board-prep/SKILL.md) | MIT |
| [`business-strategy/executive-mentor/skills/challenge`](../skills/business-strategy/executive-mentor/skills/challenge/SKILL.md) | MIT |
| [`business-strategy/executive-mentor/skills/hard-call`](../skills/business-strategy/executive-mentor/skills/hard-call/SKILL.md) | MIT |
| [`business-strategy/executive-mentor/skills/postmortem`](../skills/business-strategy/executive-mentor/skills/postmortem/SKILL.md) | MIT |
| [`business-strategy/executive-mentor/skills/stress-test`](../skills/business-strategy/executive-mentor/skills/stress-test/SKILL.md) | MIT |
| [`business-strategy/internal-narrative`](../skills/business-strategy/internal-narrative/SKILL.md) | MIT |
| [`business-strategy/intl-expansion`](../skills/business-strategy/intl-expansion/SKILL.md) | MIT |
| [`business-strategy/ma-playbook`](../skills/business-strategy/ma-playbook/SKILL.md) | MIT |
| [`business-strategy/org-health-diagnostic`](../skills/business-strategy/org-health-diagnostic/SKILL.md) | MIT |
| [`business-strategy/saas-metrics-coach`](../skills/business-strategy/saas-metrics-coach/SKILL.md) | MIT |
| [`business-strategy/scenario-war-room`](../skills/business-strategy/scenario-war-room/SKILL.md) | MIT |
| [`business-strategy/strategic-alignment`](../skills/business-strategy/strategic-alignment/SKILL.md) | MIT |
| [`cloud-azure/aws-solution-architect`](../skills/cloud-azure/aws-solution-architect/SKILL.md) | MIT |
| [`databases/database-designer`](../skills/databases/database-designer/SKILL.md) | MIT |
| [`devops/ci-cd-pipeline-builder`](../skills/devops/ci-cd-pipeline-builder/SKILL.md) | MIT |
| [`devops/dependency-auditor`](../skills/devops/dependency-auditor/SKILL.md) | MIT |
| [`devops/docker-development`](../skills/devops/docker-development/SKILL.md) | MIT |
| [`devops/helm-chart-builder`](../skills/devops/helm-chart-builder/SKILL.md) | MIT |
| [`devops/incident-commander`](../skills/devops/incident-commander/SKILL.md) | MIT |
| [`devops/observability-designer`](../skills/devops/observability-designer/SKILL.md) | MIT |
| [`devops/senior-devops`](../skills/devops/senior-devops/SKILL.md) | MIT |
| [`devops/senior-secops`](../skills/devops/senior-secops/SKILL.md) | MIT |
| [`devops/senior-security`](../skills/devops/senior-security/SKILL.md) | MIT |
| [`devops/terraform-patterns`](../skills/devops/terraform-patterns/SKILL.md) | MIT |
| [`engineering-craft/codebase-onboarding`](../skills/engineering-craft/codebase-onboarding/SKILL.md) | MIT |
| [`engineering-craft/senior-architect`](../skills/engineering-craft/senior-architect/SKILL.md) | MIT |
| [`engineering-craft/senior-backend`](../skills/engineering-craft/senior-backend/SKILL.md) | MIT |
| [`engineering-craft/senior-data-engineer`](../skills/engineering-craft/senior-data-engineer/SKILL.md) | MIT |
| [`engineering-craft/senior-data-scientist`](../skills/engineering-craft/senior-data-scientist/SKILL.md) | MIT |
| [`engineering-craft/senior-frontend`](../skills/engineering-craft/senior-frontend/SKILL.md) | MIT |
| [`engineering-craft/senior-fullstack`](../skills/engineering-craft/senior-fullstack/SKILL.md) | MIT |
| [`engineering-craft/senior-ml-engineer`](../skills/engineering-craft/senior-ml-engineer/SKILL.md) | MIT |
| [`engineering-craft/senior-pm`](../skills/engineering-craft/senior-pm/SKILL.md) | MIT |
| [`engineering-craft/senior-qa`](../skills/engineering-craft/senior-qa/SKILL.md) | MIT |
| [`engineering-craft/tech-debt-tracker`](../skills/engineering-craft/tech-debt-tracker/SKILL.md) | MIT |
| [`engineering-craft/tech-stack-evaluator`](../skills/engineering-craft/tech-stack-evaluator/SKILL.md) | MIT |
| [`marketing-and-growth/content-humanizer`](../skills/marketing-and-growth/content-humanizer/SKILL.md) | MIT |
| [`marketing-and-growth/content-production`](../skills/marketing-and-growth/content-production/SKILL.md) | MIT |
| [`marketing-and-growth/cs-ad-creative`](../skills/marketing-and-growth/cs-ad-creative/SKILL.md) | MIT |
| [`marketing-and-growth/cs-ai-seo`](../skills/marketing-and-growth/cs-ai-seo/SKILL.md) | MIT |
| [`marketing-and-growth/cs-cold-email`](../skills/marketing-and-growth/cs-cold-email/SKILL.md) | MIT |
| [`marketing-and-growth/cs-copywriting`](../skills/marketing-and-growth/cs-copywriting/SKILL.md) | MIT |
| [`marketing-and-growth/cs-pricing-strategy`](../skills/marketing-and-growth/cs-pricing-strategy/SKILL.md) | MIT |
| [`marketing-and-growth/cs-seo-audit`](../skills/marketing-and-growth/cs-seo-audit/SKILL.md) | MIT |
| [`marketing-and-growth/cs-social-media-manager`](../skills/marketing-and-growth/cs-social-media-manager/SKILL.md) | MIT |
| [`marketing-and-growth/email-sequence`](../skills/marketing-and-growth/email-sequence/SKILL.md) | MIT |
| [`marketing-and-growth/launch-strategy`](../skills/marketing-and-growth/launch-strategy/SKILL.md) | MIT |
| [`marketing-and-growth/marketing-context`](../skills/marketing-and-growth/marketing-context/SKILL.md) | MIT |
| [`marketing-and-growth/marketing-demand-acquisition`](../skills/marketing-and-growth/marketing-demand-acquisition/SKILL.md) | MIT |
| [`marketing-and-growth/marketing-ops`](../skills/marketing-and-growth/marketing-ops/SKILL.md) | MIT |
| [`marketing-and-growth/marketing-psychology`](../skills/marketing-and-growth/marketing-psychology/SKILL.md) | MIT |
| [`marketing-and-growth/marketing-strategy-pmm`](../skills/marketing-and-growth/marketing-strategy-pmm/SKILL.md) | MIT |
| [`marketing-and-growth/onboarding-cro`](../skills/marketing-and-growth/onboarding-cro/SKILL.md) | MIT |
| [`marketing-and-growth/page-cro`](../skills/marketing-and-growth/page-cro/SKILL.md) | MIT |
| [`marketing-and-growth/paid-ads`](../skills/marketing-and-growth/paid-ads/SKILL.md) | MIT |
| [`marketing-and-growth/programmatic-seo`](../skills/marketing-and-growth/programmatic-seo/SKILL.md) | MIT |
| [`marketing-and-growth/signup-flow-cro`](../skills/marketing-and-growth/signup-flow-cro/SKILL.md) | MIT |
| [`marketing-and-growth/x-twitter-growth`](../skills/marketing-and-growth/x-twitter-growth/SKILL.md) | MIT |
| [`mcp/mcp-server-builder`](../skills/mcp/mcp-server-builder/SKILL.md) | MIT |
| [`product-management/agile-product-owner`](../skills/product-management/agile-product-owner/SKILL.md) | MIT |
| [`product-management/experiment-designer`](../skills/product-management/experiment-designer/SKILL.md) | MIT |
| [`product-management/product-analytics`](../skills/product-management/product-analytics/SKILL.md) | MIT |
| [`product-management/product-discovery`](../skills/product-management/product-discovery/SKILL.md) | MIT |
| [`product-management/product-manager-toolkit`](../skills/product-management/product-manager-toolkit/SKILL.md) | MIT |
| [`product-management/product-strategist`](../skills/product-management/product-strategist/SKILL.md) | MIT |
| [`product-management/roadmap-communicator`](../skills/product-management/roadmap-communicator/SKILL.md) | MIT |
| [`product-management/scrum-master`](../skills/product-management/scrum-master/SKILL.md) | MIT |
| [`product-management/ux-researcher-designer`](../skills/product-management/ux-researcher-designer/SKILL.md) | MIT |
| [`prompting/senior-prompt-engineer`](../skills/prompting/senior-prompt-engineer/SKILL.md) | MIT |

### aws/agent-toolkit-for-aws

Source: https://github.com/aws/agent-toolkit-for-aws
Credit: Amazon Web Services - agent-toolkit-for-aws (Apache-2.0)
License: Apache-2.0

| Install path | License |
| --- | --- |
| [`cloud-aws/analytics/amazon-opensearch-service`](../skills/cloud-aws/analytics/amazon-opensearch-service/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/aws-cleanrooms`](../skills/cloud-aws/analytics/aws-cleanrooms/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/connecting-to-data-source`](../skills/cloud-aws/analytics/connecting-to-data-source/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/developing-applications-on-managed-service-for-apache-flink`](../skills/cloud-aws/analytics/developing-applications-on-managed-service-for-apache-flink/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/exploring-data-catalog`](../skills/cloud-aws/analytics/exploring-data-catalog/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/finding-data-lake-assets`](../skills/cloud-aws/analytics/finding-data-lake-assets/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/ingesting-into-data-lake`](../skills/cloud-aws/analytics/ingesting-into-data-lake/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/managing-amazon-msk`](../skills/cloud-aws/analytics/managing-amazon-msk/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/migrate-to-msk`](../skills/cloud-aws/analytics/migrate-to-msk/SKILL.md) | Apache-2.0 |
| [`cloud-aws/analytics/querying-data-lake`](../skills/cloud-aws/analytics/querying-data-lake/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/amazon-bedrock`](../skills/cloud-aws/core/amazon-bedrock/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-billing-and-cost-management`](../skills/cloud-aws/core/aws-billing-and-cost-management/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-blocks`](../skills/cloud-aws/core/aws-blocks/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-cdk`](../skills/cloud-aws/core/aws-cdk/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-cloudformation`](../skills/cloud-aws/core/aws-cloudformation/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-compute`](../skills/cloud-aws/core/aws-compute/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-containers`](../skills/cloud-aws/core/aws-containers/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-database`](../skills/cloud-aws/core/aws-database/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-deployment`](../skills/cloud-aws/core/aws-deployment/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-iam`](../skills/cloud-aws/core/aws-iam/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-messaging-and-streaming`](../skills/cloud-aws/core/aws-messaging-and-streaming/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-networking`](../skills/cloud-aws/core/aws-networking/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-observability`](../skills/cloud-aws/core/aws-observability/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-sdk-js-v3-usage`](../skills/cloud-aws/core/aws-sdk-js-v3-usage/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-sdk-python-usage`](../skills/cloud-aws/core/aws-sdk-python-usage/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-sdk-swift-usage`](../skills/cloud-aws/core/aws-sdk-swift-usage/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/aws-serverless`](../skills/cloud-aws/core/aws-serverless/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/launch-with-aws`](../skills/cloud-aws/core/launch-with-aws/SKILL.md) | Apache-2.0 |
| [`cloud-aws/core/signing-in-to-aws`](../skills/cloud-aws/core/signing-in-to-aws/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/amazon-aurora-mysql`](../skills/cloud-aws/database/amazon-aurora-mysql/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/amazon-aurora-postgresql`](../skills/cloud-aws/database/amazon-aurora-postgresql/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/amazon-documentdb`](../skills/cloud-aws/database/amazon-documentdb/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/amazon-dynamodb`](../skills/cloud-aws/database/amazon-dynamodb/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/amazon-elasticache`](../skills/cloud-aws/database/amazon-elasticache/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/amazon-keyspaces`](../skills/cloud-aws/database/amazon-keyspaces/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/aurora-dsql`](../skills/cloud-aws/database/aurora-dsql/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/creating-amazon-aurora-db-cluster-with-instances`](../skills/cloud-aws/database/creating-amazon-aurora-db-cluster-with-instances/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/exporting-rds-to-s3`](../skills/cloud-aws/database/exporting-rds-to-s3/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/rds-db2`](../skills/cloud-aws/database/rds-db2/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/rds-oracle`](../skills/cloud-aws/database/rds-oracle/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/rds-oss`](../skills/cloud-aws/database/rds-oss/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/rds-sqlserver`](../skills/cloud-aws/database/rds-sqlserver/SKILL.md) | Apache-2.0 |
| [`cloud-aws/database/timestream-influxdb`](../skills/cloud-aws/database/timestream-influxdb/SKILL.md) | Apache-2.0 |
| [`cloud-aws/ec2/creating-ec2-image-builder-pipeline`](../skills/cloud-aws/ec2/creating-ec2-image-builder-pipeline/SKILL.md) | Apache-2.0 |
| [`cloud-aws/ec2/launching-ec2-instance-with-best-practices`](../skills/cloud-aws/ec2/launching-ec2-instance-with-best-practices/SKILL.md) | Apache-2.0 |
| [`cloud-aws/ec2/setting-up-ec2-instance-profiles`](../skills/cloud-aws/ec2/setting-up-ec2-instance-profiles/SKILL.md) | Apache-2.0 |
| [`cloud-aws/migration/aws-transform`](../skills/cloud-aws/migration/aws-transform/SKILL.md) | Apache-2.0 |
| [`cloud-aws/migration/dms-schema-conversion`](../skills/cloud-aws/migration/dms-schema-conversion/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/cloudfront`](../skills/cloud-aws/networking/cloudfront/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/configuring-vpc-endpoints-for-private-aws-service-access`](../skills/cloud-aws/networking/configuring-vpc-endpoints-for-private-aws-service-access/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/connecting-vpcs-with-peering`](../skills/cloud-aws/networking/connecting-vpcs-with-peering/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/creating-production-vpc-multi-az`](../skills/cloud-aws/networking/creating-production-vpc-multi-az/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/directconnect`](../skills/cloud-aws/networking/directconnect/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/enabling-lambda-vpc-internet-access`](../skills/cloud-aws/networking/enabling-lambda-vpc-internet-access/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/route53`](../skills/cloud-aws/networking/route53/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/routing-traffic-with-route53-and-cloudfront`](../skills/cloud-aws/networking/routing-traffic-with-route53-and-cloudfront/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/shieldadvanced`](../skills/cloud-aws/networking/shieldadvanced/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/sitetositevpn`](../skills/cloud-aws/networking/sitetositevpn/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/transitgateway`](../skills/cloud-aws/networking/transitgateway/SKILL.md) | Apache-2.0 |
| [`cloud-aws/networking/waf`](../skills/cloud-aws/networking/waf/SKILL.md) | Apache-2.0 |
| [`cloud-aws/operations/aws-network-monitoring`](../skills/cloud-aws/operations/aws-network-monitoring/SKILL.md) | Apache-2.0 |
| [`cloud-aws/operations/setting-up-cloudtrail-multi-region`](../skills/cloud-aws/operations/setting-up-cloudtrail-multi-region/SKILL.md) | Apache-2.0 |
| [`cloud-aws/operations/setting-up-cloudwatch-alarm-notifications`](../skills/cloud-aws/operations/setting-up-cloudwatch-alarm-notifications/SKILL.md) | Apache-2.0 |
| [`cloud-aws/operations/troubleshooting-application-failures`](../skills/cloud-aws/operations/troubleshooting-application-failures/SKILL.md) | Apache-2.0 |
| [`cloud-aws/security/creating-secrets-using-best-practices`](../skills/cloud-aws/security/creating-secrets-using-best-practices/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/aws-lambda-durable-functions`](../skills/cloud-aws/serverless/aws-lambda-durable-functions/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/aws-lambda-managed-instances`](../skills/cloud-aws/serverless/aws-lambda-managed-instances/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/aws-lambda-microvms`](../skills/cloud-aws/serverless/aws-lambda-microvms/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/connecting-lambda-to-api-gateway`](../skills/cloud-aws/serverless/connecting-lambda-to-api-gateway/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/connecting-lambda-to-dynamodb`](../skills/cloud-aws/serverless/connecting-lambda-to-dynamodb/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/creating-api-gateway-stage`](../skills/cloud-aws/serverless/creating-api-gateway-stage/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/debugging-lambda-timeouts`](../skills/cloud-aws/serverless/debugging-lambda-timeouts/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/deploying-custom-domain-rest-api`](../skills/cloud-aws/serverless/deploying-custom-domain-rest-api/SKILL.md) | Apache-2.0 |
| [`cloud-aws/serverless/processing-s3-uploads-with-step-functions`](../skills/cloud-aws/serverless/processing-s3-uploads-with-step-functions/SKILL.md) | Apache-2.0 |
| [`cloud-aws/storage/creating-data-lake-table`](../skills/cloud-aws/storage/creating-data-lake-table/SKILL.md) | Apache-2.0 |
| [`cloud-aws/storage/securing-s3-buckets`](../skills/cloud-aws/storage/securing-s3-buckets/SKILL.md) | Apache-2.0 |
| [`cloud-aws/storage/storing-and-querying-vectors`](../skills/cloud-aws/storage/storing-and-querying-vectors/SKILL.md) | Apache-2.0 |
| [`cloud-aws/storage/troubleshooting-efs`](../skills/cloud-aws/storage/troubleshooting-efs/SKILL.md) | Apache-2.0 |
| [`cloud-aws/storage/troubleshooting-s3-files`](../skills/cloud-aws/storage/troubleshooting-s3-files/SKILL.md) | Apache-2.0 |
| [`cloud-aws/system-tables/querying-aws-cloudwatch`](../skills/cloud-aws/system-tables/querying-aws-cloudwatch/SKILL.md) | Apache-2.0 |
| [`cloud-aws/system-tables/querying-aws-s3`](../skills/cloud-aws/system-tables/querying-aws-s3/SKILL.md) | Apache-2.0 |
| [`cloud-aws/system-tables/querying-aws-sagemaker-catalog`](../skills/cloud-aws/system-tables/querying-aws-sagemaker-catalog/SKILL.md) | Apache-2.0 |
| [`cloud-aws/web-mobile/aws-amplify`](../skills/cloud-aws/web-mobile/aws-amplify/SKILL.md) | Apache-2.0 |

### steipete/agent-scripts

Source: https://github.com/steipete/agent-scripts
License: Complete terms in LICENSE.txt; MIT

| Install path | License |
| --- | --- |
| [`code-quality/github-deep-review`](../skills/code-quality/github-deep-review/SKILL.md) | MIT |
| [`coding/hopper-debugger`](../skills/coding/hopper-debugger/SKILL.md) | MIT |
| [`coding/instruments-profiling`](../skills/coding/instruments-profiling/SKILL.md) | MIT |
| [`coding/native-app-performance`](../skills/coding/native-app-performance/SKILL.md) | MIT |
| [`coding/swift-concurrency-expert`](../skills/coding/swift-concurrency-expert/SKILL.md) | MIT |
| [`coding/swiftui-liquid-glass`](../skills/coding/swiftui-liquid-glass/SKILL.md) | MIT |
| [`coding/swiftui-performance-audit`](../skills/coding/swiftui-performance-audit/SKILL.md) | MIT |
| [`coding/swiftui-view-refactor`](../skills/coding/swiftui-view-refactor/SKILL.md) | MIT |
| [`design-and-ui/frontend-design`](../skills/design-and-ui/frontend-design/SKILL.md) | Complete terms in LICENSE.txt |
| [`dev-workflow/browser-use`](../skills/dev-workflow/browser-use/SKILL.md) | MIT |
| [`dev-workflow/codex-debugging`](../skills/dev-workflow/codex-debugging/SKILL.md) | MIT |
| [`dev-workflow/create-cli`](../skills/dev-workflow/create-cli/SKILL.md) | MIT |
| [`dev-workflow/github-author-context`](../skills/dev-workflow/github-author-context/SKILL.md) | MIT |
| [`dev-workflow/github-cache-hygiene`](../skills/dev-workflow/github-cache-hygiene/SKILL.md) | MIT |
| [`dev-workflow/github-project-triage`](../skills/dev-workflow/github-project-triage/SKILL.md) | MIT |
| [`dev-workflow/npm`](../skills/dev-workflow/npm/SKILL.md) | MIT |
| [`dev-workflow/xurl`](../skills/dev-workflow/xurl/SKILL.md) | MIT |
| [`devops/cloudflare-registrar`](../skills/devops/cloudflare-registrar/SKILL.md) | MIT |
| [`devops/domain-dns-ops`](../skills/devops/domain-dns-ops/SKILL.md) | MIT |
| [`devops/mac-maintenance`](../skills/devops/mac-maintenance/SKILL.md) | MIT |
| [`devops/release-mac-app`](../skills/devops/release-mac-app/SKILL.md) | MIT |
| [`devops/remote-mac`](../skills/devops/remote-mac/SKILL.md) | MIT |
| [`devops/ssh-doctor`](../skills/devops/ssh-doctor/SKILL.md) | MIT |
| [`devops/vm-lab`](../skills/devops/vm-lab/SKILL.md) | MIT |
| [`devops/wrangler`](../skills/devops/wrangler/SKILL.md) | MIT |
| [`documentation/markdown-converter`](../skills/documentation/markdown-converter/SKILL.md) | MIT |
| [`documentation/video-transcript-downloader`](../skills/documentation/video-transcript-downloader/SKILL.md) | MIT |
| [`llm-tooling/nano-banana-pro`](../skills/llm-tooling/nano-banana-pro/SKILL.md) | MIT |
| [`llm-tooling/openai-image-gen`](../skills/llm-tooling/openai-image-gen/SKILL.md) | MIT |
| [`llm-tooling/oracle`](../skills/llm-tooling/oracle/SKILL.md) | MIT |
| [`marketing-and-growth/release-tweets`](../skills/marketing-and-growth/release-tweets/SKILL.md) | MIT |
| [`messaging/whatsapp`](../skills/messaging/whatsapp/SKILL.md) | MIT |
| [`personal-productivity/beeper`](../skills/personal-productivity/beeper/SKILL.md) | MIT |
| [`personal-productivity/notcrawl`](../skills/personal-productivity/notcrawl/SKILL.md) | MIT |
| [`personal-productivity/obsidian`](../skills/personal-productivity/obsidian/SKILL.md) | MIT |
| [`personal-productivity/peekaboo`](../skills/personal-productivity/peekaboo/SKILL.md) | MIT |
| [`personal-productivity/reminders`](../skills/personal-productivity/reminders/SKILL.md) | MIT |
| [`personal-productivity/sonos`](../skills/personal-productivity/sonos/SKILL.md) | MIT |
| [`personal-productivity/speaking`](../skills/personal-productivity/speaking/SKILL.md) | MIT |
| [`personal-productivity/things-todo`](../skills/personal-productivity/things-todo/SKILL.md) | MIT |
| [`skills-management/skill-cleaner`](../skills/skills-management/skill-cleaner/SKILL.md) | MIT |

### bmad-code-org/BMAD-METHOD

Source: https://github.com/bmad-code-org/BMAD-METHOD
Credit: bmad-code-org/BMAD-METHOD by BMAD Code Org
License: MIT

| Install path | License |
| --- | --- |
| [`agent-design/bmm-skills`](../skills/agent-design/bmm-skills/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/bmad-agent-analyst`](../skills/agent-design/bmm-skills/1-analysis/bmad-agent-analyst/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/bmad-agent-tech-writer`](../skills/agent-design/bmm-skills/1-analysis/bmad-agent-tech-writer/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/bmad-document-project`](../skills/agent-design/bmm-skills/1-analysis/bmad-document-project/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/bmad-prfaq`](../skills/agent-design/bmm-skills/1-analysis/bmad-prfaq/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/bmad-product-brief`](../skills/agent-design/bmm-skills/1-analysis/bmad-product-brief/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/research/bmad-domain-research`](../skills/agent-design/bmm-skills/1-analysis/research/bmad-domain-research/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/research/bmad-market-research`](../skills/agent-design/bmm-skills/1-analysis/research/bmad-market-research/SKILL.md) | MIT |
| [`agent-design/bmm-skills/1-analysis/research/bmad-technical-research`](../skills/agent-design/bmm-skills/1-analysis/research/bmad-technical-research/SKILL.md) | MIT |
| [`agent-design/bmm-skills/2-plan-workflows/bmad-agent-pm`](../skills/agent-design/bmm-skills/2-plan-workflows/bmad-agent-pm/SKILL.md) | MIT |
| [`agent-design/bmm-skills/2-plan-workflows/bmad-agent-ux-designer`](../skills/agent-design/bmm-skills/2-plan-workflows/bmad-agent-ux-designer/SKILL.md) | MIT |
| [`agent-design/bmm-skills/2-plan-workflows/bmad-create-prd`](../skills/agent-design/bmm-skills/2-plan-workflows/bmad-create-prd/SKILL.md) | MIT |
| [`agent-design/bmm-skills/2-plan-workflows/bmad-create-ux-design`](../skills/agent-design/bmm-skills/2-plan-workflows/bmad-create-ux-design/SKILL.md) | MIT |
| [`agent-design/bmm-skills/2-plan-workflows/bmad-edit-prd`](../skills/agent-design/bmm-skills/2-plan-workflows/bmad-edit-prd/SKILL.md) | MIT |
| [`agent-design/bmm-skills/2-plan-workflows/bmad-validate-prd`](../skills/agent-design/bmm-skills/2-plan-workflows/bmad-validate-prd/SKILL.md) | MIT |
| [`agent-design/bmm-skills/3-solutioning/bmad-agent-architect`](../skills/agent-design/bmm-skills/3-solutioning/bmad-agent-architect/SKILL.md) | MIT |
| [`agent-design/bmm-skills/3-solutioning/bmad-check-implementation-readiness`](../skills/agent-design/bmm-skills/3-solutioning/bmad-check-implementation-readiness/SKILL.md) | MIT |
| [`agent-design/bmm-skills/3-solutioning/bmad-create-architecture`](../skills/agent-design/bmm-skills/3-solutioning/bmad-create-architecture/SKILL.md) | MIT |
| [`agent-design/bmm-skills/3-solutioning/bmad-create-epics-and-stories`](../skills/agent-design/bmm-skills/3-solutioning/bmad-create-epics-and-stories/SKILL.md) | MIT |
| [`agent-design/bmm-skills/3-solutioning/bmad-generate-project-context`](../skills/agent-design/bmm-skills/3-solutioning/bmad-generate-project-context/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-agent-dev`](../skills/agent-design/bmm-skills/4-implementation/bmad-agent-dev/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-checkpoint-preview`](../skills/agent-design/bmm-skills/4-implementation/bmad-checkpoint-preview/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-code-review`](../skills/agent-design/bmm-skills/4-implementation/bmad-code-review/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-correct-course`](../skills/agent-design/bmm-skills/4-implementation/bmad-correct-course/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-create-story`](../skills/agent-design/bmm-skills/4-implementation/bmad-create-story/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-dev-story`](../skills/agent-design/bmm-skills/4-implementation/bmad-dev-story/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-qa-generate-e2e-tests`](../skills/agent-design/bmm-skills/4-implementation/bmad-qa-generate-e2e-tests/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-quick-dev`](../skills/agent-design/bmm-skills/4-implementation/bmad-quick-dev/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-retrospective`](../skills/agent-design/bmm-skills/4-implementation/bmad-retrospective/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-sprint-planning`](../skills/agent-design/bmm-skills/4-implementation/bmad-sprint-planning/SKILL.md) | MIT |
| [`agent-design/bmm-skills/4-implementation/bmad-sprint-status`](../skills/agent-design/bmm-skills/4-implementation/bmad-sprint-status/SKILL.md) | MIT |

### addyosmani/agent-skills

Source: https://github.com/addyosmani/agent-skills
Credit: addyosmani/agent-skills by Addy Osmani
License: MIT

| Install path | License |
| --- | --- |
| [`coding/api-and-interface-design`](../skills/coding/api-and-interface-design/SKILL.md) | MIT |
| [`coding/browser-testing-with-devtools`](../skills/coding/browser-testing-with-devtools/SKILL.md) | MIT |
| [`coding/ci-cd-and-automation`](../skills/coding/ci-cd-and-automation/SKILL.md) | MIT |
| [`coding/code-review-and-quality`](../skills/coding/code-review-and-quality/SKILL.md) | MIT |
| [`coding/code-simplification`](../skills/coding/code-simplification/SKILL.md) | MIT |
| [`coding/constraint-driven-development`](../skills/coding/constraint-driven-development/SKILL.md) | MIT |
| [`coding/context-engineering`](../skills/coding/context-engineering/SKILL.md) | MIT |
| [`coding/debugging-and-error-recovery`](../skills/coding/debugging-and-error-recovery/SKILL.md) | MIT |
| [`coding/deprecation-and-migration`](../skills/coding/deprecation-and-migration/SKILL.md) | MIT |
| [`coding/documentation-and-adrs`](../skills/coding/documentation-and-adrs/SKILL.md) | MIT |
| [`coding/doubt-driven-development`](../skills/coding/doubt-driven-development/SKILL.md) | MIT |
| [`coding/frontend-ui-engineering`](../skills/coding/frontend-ui-engineering/SKILL.md) | MIT |
| [`coding/git-workflow-and-versioning`](../skills/coding/git-workflow-and-versioning/SKILL.md) | MIT |
| [`coding/idea-refine`](../skills/coding/idea-refine/SKILL.md) | MIT |
| [`coding/incremental-implementation`](../skills/coding/incremental-implementation/SKILL.md) | MIT |
| [`coding/interview-me`](../skills/coding/interview-me/SKILL.md) | MIT |
| [`coding/observability-and-instrumentation`](../skills/coding/observability-and-instrumentation/SKILL.md) | MIT |
| [`coding/performance-optimization`](../skills/coding/performance-optimization/SKILL.md) | MIT |
| [`coding/planning-and-task-breakdown`](../skills/coding/planning-and-task-breakdown/SKILL.md) | MIT |
| [`coding/security-and-hardening`](../skills/coding/security-and-hardening/SKILL.md) | MIT |
| [`coding/shipping-and-launch`](../skills/coding/shipping-and-launch/SKILL.md) | MIT |
| [`coding/source-driven-development`](../skills/coding/source-driven-development/SKILL.md) | MIT |
| [`coding/spec-driven-development`](../skills/coding/spec-driven-development/SKILL.md) | MIT |
| [`coding/test-driven-development`](../skills/coding/test-driven-development/SKILL.md) | MIT |
| [`coding/using-agent-skills`](../skills/coding/using-agent-skills/SKILL.md) | MIT |

### qdrant/skills

Source: https://github.com/qdrant/skills
Credit: qdrant/skills by Qdrant
License: Apache-2.0

| Install path | License |
| --- | --- |
| [`llm-tooling/qdrant-clients-sdk`](../skills/llm-tooling/qdrant-clients-sdk/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-deployment-options`](../skills/llm-tooling/qdrant-deployment-options/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-model-migration`](../skills/llm-tooling/qdrant-model-migration/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-monitoring`](../skills/llm-tooling/qdrant-monitoring/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-monitoring/debugging`](../skills/llm-tooling/qdrant-monitoring/debugging/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-monitoring/setup`](../skills/llm-tooling/qdrant-monitoring/setup/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-performance-optimization`](../skills/llm-tooling/qdrant-performance-optimization/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-performance-optimization/indexing-performance-optimization`](../skills/llm-tooling/qdrant-performance-optimization/indexing-performance-optimization/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-performance-optimization/memory-usage-optimization`](../skills/llm-tooling/qdrant-performance-optimization/memory-usage-optimization/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-performance-optimization/search-speed-optimization`](../skills/llm-tooling/qdrant-performance-optimization/search-speed-optimization/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling`](../skills/llm-tooling/qdrant-scaling/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/minimize-latency`](../skills/llm-tooling/qdrant-scaling/minimize-latency/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/scaling-data-volume`](../skills/llm-tooling/qdrant-scaling/scaling-data-volume/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/scaling-data-volume/horizontal-scaling`](../skills/llm-tooling/qdrant-scaling/scaling-data-volume/horizontal-scaling/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/scaling-data-volume/sliding-time-window`](../skills/llm-tooling/qdrant-scaling/scaling-data-volume/sliding-time-window/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/scaling-data-volume/tenant-scaling`](../skills/llm-tooling/qdrant-scaling/scaling-data-volume/tenant-scaling/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/scaling-data-volume/vertical-scaling`](../skills/llm-tooling/qdrant-scaling/scaling-data-volume/vertical-scaling/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/scaling-qps`](../skills/llm-tooling/qdrant-scaling/scaling-qps/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-scaling/scaling-query-volume`](../skills/llm-tooling/qdrant-scaling/scaling-query-volume/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-search-quality`](../skills/llm-tooling/qdrant-search-quality/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-search-quality/diagnosis`](../skills/llm-tooling/qdrant-search-quality/diagnosis/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-search-quality/search-strategies`](../skills/llm-tooling/qdrant-search-quality/search-strategies/SKILL.md) | Apache-2.0 |
| [`llm-tooling/qdrant-version-upgrade`](../skills/llm-tooling/qdrant-version-upgrade/SKILL.md) | Apache-2.0 |

### streamlit/agent-skills

Source: https://github.com/streamlit/agent-skills
Credit: streamlit/agent-skills by Streamlit
License: Apache-2.0

| Install path | License |
| --- | --- |
| [`streamlit/developing-with-streamlit`](../skills/streamlit/developing-with-streamlit/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/building-streamlit-chat-ui`](../skills/streamlit/developing-with-streamlit/skills/building-streamlit-chat-ui/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/building-streamlit-custom-components-v2`](../skills/streamlit/developing-with-streamlit/skills/building-streamlit-custom-components-v2/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/building-streamlit-dashboards`](../skills/streamlit/developing-with-streamlit/skills/building-streamlit-dashboards/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/building-streamlit-multipage-apps`](../skills/streamlit/developing-with-streamlit/skills/building-streamlit-multipage-apps/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/choosing-streamlit-selection-widgets`](../skills/streamlit/developing-with-streamlit/skills/choosing-streamlit-selection-widgets/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/connecting-streamlit-to-snowflake`](../skills/streamlit/developing-with-streamlit/skills/connecting-streamlit-to-snowflake/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/creating-streamlit-themes`](../skills/streamlit/developing-with-streamlit/skills/creating-streamlit-themes/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/displaying-streamlit-data`](../skills/streamlit/developing-with-streamlit/skills/displaying-streamlit-data/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/improving-streamlit-design`](../skills/streamlit/developing-with-streamlit/skills/improving-streamlit-design/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/optimizing-streamlit-performance`](../skills/streamlit/developing-with-streamlit/skills/optimizing-streamlit-performance/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/organizing-streamlit-code`](../skills/streamlit/developing-with-streamlit/skills/organizing-streamlit-code/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/setting-up-streamlit-environment`](../skills/streamlit/developing-with-streamlit/skills/setting-up-streamlit-environment/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/using-streamlit-cli`](../skills/streamlit/developing-with-streamlit/skills/using-streamlit-cli/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/using-streamlit-custom-components`](../skills/streamlit/developing-with-streamlit/skills/using-streamlit-custom-components/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/using-streamlit-layouts`](../skills/streamlit/developing-with-streamlit/skills/using-streamlit-layouts/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/using-streamlit-markdown`](../skills/streamlit/developing-with-streamlit/skills/using-streamlit-markdown/SKILL.md) | Apache-2.0 |
| [`streamlit/developing-with-streamlit/skills/using-streamlit-session-state`](../skills/streamlit/developing-with-streamlit/skills/using-streamlit-session-state/SKILL.md) | Apache-2.0 |

### NousResearch/hermes-agent

Source: https://github.com/NousResearch/hermes-agent
Credit: NousResearch/hermes-agent by Nous Research
License: Apache-2.0; MIT

| Install path | License |
| --- | --- |
| [`api-backend/rest-graphql-debug`](../skills/api-backend/rest-graphql-debug/SKILL.md) | MIT |
| [`communication/one-three-one-rule`](../skills/communication/one-three-one-rule/SKILL.md) | MIT |
| [`creative/concept-diagrams`](../skills/creative/concept-diagrams/SKILL.md) | MIT |
| [`creative/creative-ideation`](../skills/creative/creative-ideation/SKILL.md) | MIT |
| [`devops/docker-management`](../skills/devops/docker-management/SKILL.md) | MIT |
| [`finance/3-statement-model`](../skills/finance/3-statement-model/SKILL.md) | Apache-2.0 |
| [`finance/comps-analysis`](../skills/finance/comps-analysis/SKILL.md) | Apache-2.0 |
| [`finance/dcf-model`](../skills/finance/dcf-model/SKILL.md) | Apache-2.0 |
| [`finance/excel-author`](../skills/finance/excel-author/SKILL.md) | Apache-2.0 |
| [`finance/lbo-model`](../skills/finance/lbo-model/SKILL.md) | Apache-2.0 |
| [`finance/merger-model`](../skills/finance/merger-model/SKILL.md) | Apache-2.0 |
| [`finance/pptx-author`](../skills/finance/pptx-author/SKILL.md) | Apache-2.0 |
| [`mcp/fastmcp`](../skills/mcp/fastmcp/SKILL.md) | MIT |
| [`personal-productivity/memento-flashcards`](../skills/personal-productivity/memento-flashcards/SKILL.md) | MIT |
| [`research/osint-investigation`](../skills/research/osint-investigation/SKILL.md) | MIT |

### muratcankoylan/Agent-Skills-for-Context-Engineering

Source: https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering
Credit: muratcankoylan/Agent-Skills-for-Context-Engineering by Muratcan Koylan
License: MIT

| Install path | License |
| --- | --- |
| [`agent-design/bdi-mental-states`](../skills/agent-design/bdi-mental-states/SKILL.md) | MIT |
| [`agent-design/latent-briefing`](../skills/agent-design/latent-briefing/SKILL.md) | MIT |
| [`agent-design/multi-agent-patterns`](../skills/agent-design/multi-agent-patterns/SKILL.md) | MIT |
| [`agent-design/tool-design`](../skills/agent-design/tool-design/SKILL.md) | MIT |
| [`context-engineering/context-compression`](../skills/context-engineering/context-compression/SKILL.md) | MIT |
| [`context-engineering/context-degradation`](../skills/context-engineering/context-degradation/SKILL.md) | MIT |
| [`context-engineering/context-fundamentals`](../skills/context-engineering/context-fundamentals/SKILL.md) | MIT |
| [`context-engineering/context-optimization`](../skills/context-engineering/context-optimization/SKILL.md) | MIT |
| [`context-engineering/filesystem-context`](../skills/context-engineering/filesystem-context/SKILL.md) | MIT |
| [`context-engineering/memory-systems`](../skills/context-engineering/memory-systems/SKILL.md) | MIT |
| [`documentation/project-development`](../skills/documentation/project-development/SKILL.md) | MIT |
| [`microsoft-agents/hosted-agents`](../skills/microsoft-agents/hosted-agents/SKILL.md) | MIT |
| [`testing/advanced-evaluation`](../skills/testing/advanced-evaluation/SKILL.md) | MIT |
| [`testing/evaluation`](../skills/testing/evaluation/SKILL.md) | MIT |

### obra/superpowers

Source: https://github.com/obra/superpowers
Credit: obra/superpowers by Jesse Vincent
License: MIT

| Install path | License |
| --- | --- |
| [`code-quality/receiving-code-review`](../skills/code-quality/receiving-code-review/SKILL.md) | MIT |
| [`code-quality/requesting-code-review`](../skills/code-quality/requesting-code-review/SKILL.md) | MIT |
| [`dev-workflow/finishing-a-development-branch`](../skills/dev-workflow/finishing-a-development-branch/SKILL.md) | MIT |
| [`dev-workflow/using-git-worktrees`](../skills/dev-workflow/using-git-worktrees/SKILL.md) | MIT |
| [`engineering-craft/brainstorming`](../skills/engineering-craft/brainstorming/SKILL.md) | MIT |
| [`engineering-craft/dispatching-parallel-agents`](../skills/engineering-craft/dispatching-parallel-agents/SKILL.md) | MIT |
| [`engineering-craft/executing-plans`](../skills/engineering-craft/executing-plans/SKILL.md) | MIT |
| [`engineering-craft/subagent-driven-development`](../skills/engineering-craft/subagent-driven-development/SKILL.md) | MIT |
| [`engineering-craft/superpowers-test-driven-development`](../skills/engineering-craft/superpowers-test-driven-development/SKILL.md) | MIT |
| [`engineering-craft/using-superpowers`](../skills/engineering-craft/using-superpowers/SKILL.md) | MIT |
| [`engineering-craft/verification-before-completion`](../skills/engineering-craft/verification-before-completion/SKILL.md) | MIT |
| [`engineering-craft/writing-plans`](../skills/engineering-craft/writing-plans/SKILL.md) | MIT |
| [`skills-management/writing-skills`](../skills/skills-management/writing-skills/SKILL.md) | MIT |
| [`testing/systematic-debugging`](../skills/testing/systematic-debugging/SKILL.md) | MIT |

### beingsmit/technical-product-gtm

Source: https://github.com/beingsmit/technical-product-gtm
Credit: beingsmit/technical-product-gtm by Smit Patel
License: MIT

| Install path | License |
| --- | --- |
| [`go-to-market/gtm-0-to-1-launch`](../skills/go-to-market/gtm-0-to-1-launch/SKILL.md) | MIT |
| [`go-to-market/gtm-ai-gtm`](../skills/go-to-market/gtm-ai-gtm/SKILL.md) | MIT |
| [`go-to-market/gtm-board-and-investor-communication`](../skills/go-to-market/gtm-board-and-investor-communication/SKILL.md) | MIT |
| [`go-to-market/gtm-developer-ecosystem`](../skills/go-to-market/gtm-developer-ecosystem/SKILL.md) | MIT |
| [`go-to-market/gtm-enterprise-account-planning`](../skills/go-to-market/gtm-enterprise-account-planning/SKILL.md) | MIT |
| [`go-to-market/gtm-enterprise-onboarding`](../skills/go-to-market/gtm-enterprise-onboarding/SKILL.md) | MIT |
| [`go-to-market/gtm-operating-cadence`](../skills/go-to-market/gtm-operating-cadence/SKILL.md) | MIT |
| [`go-to-market/gtm-partnership-architecture`](../skills/go-to-market/gtm-partnership-architecture/SKILL.md) | MIT |
| [`go-to-market/gtm-positioning-strategy`](../skills/go-to-market/gtm-positioning-strategy/SKILL.md) | MIT |
| [`go-to-market/gtm-product-led-growth`](../skills/go-to-market/gtm-product-led-growth/SKILL.md) | MIT |
| [`go-to-market/gtm-technical-product-pricing`](../skills/go-to-market/gtm-technical-product-pricing/SKILL.md) | MIT |

### Arize-ai/arize-skills

Source: https://github.com/Arize-ai/arize-skills
Credit: Arize-ai/arize-skills by Arize AI
License: MIT

| Install path | License |
| --- | --- |
| [`llm-tooling/arize-ai-provider-integration`](../skills/llm-tooling/arize-ai-provider-integration/SKILL.md) | MIT |
| [`llm-tooling/arize-annotation`](../skills/llm-tooling/arize-annotation/SKILL.md) | MIT |
| [`llm-tooling/arize-dataset`](../skills/llm-tooling/arize-dataset/SKILL.md) | MIT |
| [`llm-tooling/arize-evaluator`](../skills/llm-tooling/arize-evaluator/SKILL.md) | MIT |
| [`llm-tooling/arize-experiment`](../skills/llm-tooling/arize-experiment/SKILL.md) | MIT |
| [`llm-tooling/arize-instrumentation`](../skills/llm-tooling/arize-instrumentation/SKILL.md) | MIT |
| [`llm-tooling/arize-link`](../skills/llm-tooling/arize-link/SKILL.md) | MIT |
| [`llm-tooling/arize-prompt-optimization`](../skills/llm-tooling/arize-prompt-optimization/SKILL.md) | MIT |
| [`llm-tooling/arize-trace`](../skills/llm-tooling/arize-trace/SKILL.md) | MIT |

### greensock/gsap-skills

Source: https://github.com/greensock/gsap-skills
Credit: greensock/gsap-skills by GreenSock
License: MIT

| Install path | License |
| --- | --- |
| [`design-and-ui/gsap-core`](../skills/design-and-ui/gsap-core/SKILL.md) | MIT |
| [`design-and-ui/gsap-frameworks`](../skills/design-and-ui/gsap-frameworks/SKILL.md) | MIT |
| [`design-and-ui/gsap-performance`](../skills/design-and-ui/gsap-performance/SKILL.md) | MIT |
| [`design-and-ui/gsap-plugins`](../skills/design-and-ui/gsap-plugins/SKILL.md) | MIT |
| [`design-and-ui/gsap-react`](../skills/design-and-ui/gsap-react/SKILL.md) | MIT |
| [`design-and-ui/gsap-scrolltrigger`](../skills/design-and-ui/gsap-scrolltrigger/SKILL.md) | MIT |
| [`design-and-ui/gsap-timeline`](../skills/design-and-ui/gsap-timeline/SKILL.md) | MIT |
| [`design-and-ui/gsap-utils`](../skills/design-and-ui/gsap-utils/SKILL.md) | MIT |

### mattpocock/skills

Source: https://github.com/mattpocock/skills
Credit: mattpocock/skills by Matt Pocock
License: MIT

| Install path | License |
| --- | --- |
| [`code-quality/grilling`](../skills/code-quality/grilling/SKILL.md) | MIT |
| [`context-engineering/session-handoff`](../skills/context-engineering/session-handoff/SKILL.md) | MIT |
| [`dev-workflow/git-guardrails`](../skills/dev-workflow/git-guardrails/SKILL.md) | MIT |
| [`engineering-craft/codebase-design`](../skills/engineering-craft/codebase-design/SKILL.md) | MIT |
| [`engineering-craft/domain-modeling`](../skills/engineering-craft/domain-modeling/SKILL.md) | MIT |
| [`engineering-craft/improve-codebase-architecture`](../skills/engineering-craft/improve-codebase-architecture/SKILL.md) | MIT |
| [`skills-management/writing-for-agents`](../skills/skills-management/writing-for-agents/SKILL.md) | MIT |

### OpenRouterTeam/skills

Source: https://github.com/OpenRouterTeam/skills
Credit: OpenRouterTeam/skills by OpenRouter
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/create-agent-tui`](../skills/agent-design/create-agent-tui/SKILL.md) | not declared |
| [`agent-design/create-headless-agent`](../skills/agent-design/create-headless-agent/SKILL.md) | not declared |
| [`llm-tooling/openrouter-agent-migration`](../skills/llm-tooling/openrouter-agent-migration/SKILL.md) | not declared |
| [`llm-tooling/openrouter-images`](../skills/llm-tooling/openrouter-images/SKILL.md) | not declared |
| [`llm-tooling/openrouter-models`](../skills/llm-tooling/openrouter-models/SKILL.md) | not declared |
| [`llm-tooling/openrouter-oauth`](../skills/llm-tooling/openrouter-oauth/SKILL.md) | not declared |
| [`llm-tooling/openrouter-typescript-sdk`](../skills/llm-tooling/openrouter-typescript-sdk/SKILL.md) | not declared |

### nextlevelbuilder/ui-ux-pro-max-skill

Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
Credit: nextlevelbuilder/ui-ux-pro-max-skill by Next Level Builder
License: MIT

| Install path | License |
| --- | --- |
| [`design-and-ui/banner-design`](../skills/design-and-ui/banner-design/SKILL.md) | MIT |
| [`design-and-ui/brand`](../skills/design-and-ui/brand/SKILL.md) | MIT |
| [`design-and-ui/design`](../skills/design-and-ui/design/SKILL.md) | MIT |
| [`design-and-ui/design-system`](../skills/design-and-ui/design-system/SKILL.md) | MIT |
| [`design-and-ui/ui-ux-pro-max`](../skills/design-and-ui/ui-ux-pro-max/SKILL.md) | MIT |
| [`diagrams-slides/slides`](../skills/diagrams-slides/slides/SKILL.md) | MIT |

### getsentry/skills

Source: https://github.com/getsentry/skills
Credit: getsentry/skills by Sentry
License: Apache-2.0

| Install path | License |
| --- | --- |
| [`code-quality/find-bugs`](../skills/code-quality/find-bugs/SKILL.md) | Apache-2.0 |
| [`dev-workflow/iterate-pr`](../skills/dev-workflow/iterate-pr/SKILL.md) | Apache-2.0 |
| [`dev-workflow/permission-settings-audit`](../skills/dev-workflow/permission-settings-audit/SKILL.md) | Apache-2.0 |
| [`skills-management/skill-scanner`](../skills/skills-management/skill-scanner/SKILL.md) | Apache-2.0 |

### trailofbits/skills

Source: https://github.com/trailofbits/skills
Credit: trailofbits/skills by Trail of Bits
License: CC-BY-SA-4.0

| Install path | License |
| --- | --- |
| [`code-quality/differential-review`](../skills/code-quality/differential-review/SKILL.md) | CC-BY-SA-4.0 |
| [`devops/supply-chain-risk-auditor`](../skills/devops/supply-chain-risk-auditor/SKILL.md) | CC-BY-SA-4.0 |
| [`testing/mutation-testing`](../skills/testing/mutation-testing/SKILL.md) | CC-BY-SA-4.0 |
| [`testing/property-based-testing`](../skills/testing/property-based-testing/SKILL.md) | CC-BY-SA-4.0 |

### Arize-ai/phoenix

Source: https://github.com/Arize-ai/phoenix
Credit: Arize-ai/phoenix by Arize AI
License: Apache-2.0

| Install path | License |
| --- | --- |
| [`llm-tooling/phoenix-cli`](../skills/llm-tooling/phoenix-cli/SKILL.md) | Apache-2.0 |
| [`llm-tooling/phoenix-evals`](../skills/llm-tooling/phoenix-evals/SKILL.md) | Apache-2.0 |
| [`llm-tooling/phoenix-tracing`](../skills/llm-tooling/phoenix-tracing/SKILL.md) | Apache-2.0 |

### https://arxiv.org/abs/2605.26112v1

Source: https://arxiv.org/abs/2605.26112v1
Credit: Shangding Gu, UC Berkeley — 'From Model Scaling to System Scaling: Scaling the Harness in Agentic AI' (arXiv:2605.26112v1, May 2026)
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/harness-scaling`](../skills/agent-design/harness-scaling/SKILL.md) | not declared |
| [`agent-eval/harness-benchmarking`](../skills/agent-eval/harness-benchmarking/SKILL.md) | not declared |

### anthropics/skills

Source: https://github.com/anthropics/skills
Credit: anthropics/skills by Anthropic
License: Apache-2.0; Complete terms in LICENSE.txt

| Install path | License |
| --- | --- |
| [`design-and-ui/theme-factory`](../skills/design-and-ui/theme-factory/SKILL.md) | Complete terms in LICENSE.txt |
| [`skills-management/skill-creator`](../skills/skills-management/skill-creator/SKILL.md) | Apache-2.0 |

### hashicorp/agent-skills

Source: https://github.com/hashicorp/agent-skills
Credit: hashicorp/agent-skills by HashiCorp
License: MPL-2.0

| Install path | License |
| --- | --- |
| [`devops/terraform-style-guide`](../skills/devops/terraform-style-guide/SKILL.md) | MPL-2.0 |
| [`devops/terraform-test`](../skills/devops/terraform-test/SKILL.md) | MPL-2.0 |

### JuliusBrussee/caveman

Source: https://github.com/JuliusBrussee/caveman
Credit: JuliusBrussee/caveman by Julius Brussee
License: Apache-2.0

| Install path | License |
| --- | --- |
| [`context-engineering/caveman`](../skills/context-engineering/caveman/SKILL.md) | Apache-2.0 |
| [`context-engineering/caveman-compress`](../skills/context-engineering/caveman-compress/SKILL.md) | Apache-2.0 |

### microsoft/azure-skills

Source: https://github.com/microsoft/azure-skills
Credit: microsoft/azure-skills by Microsoft Azure
License: Complete terms in LICENSE.txt; MIT

| Install path | License |
| --- | --- |
| [`cloud-azure/appinsights-instrumentation`](../skills/cloud-azure/appinsights-instrumentation/SKILL.md) | MIT |
| [`cloud-azure/azure-resource-visualizer`](../skills/cloud-azure/azure-resource-visualizer/SKILL.md) | Complete terms in LICENSE.txt |

### vercel-labs/agent-skills

Source: https://github.com/vercel-labs/agent-skills
Credit: vercel-labs/agent-skills by Vercel
License: MIT

| Install path | License |
| --- | --- |
| [`react-frontend/vercel-composition-patterns`](../skills/react-frontend/vercel-composition-patterns/SKILL.md) | MIT |
| [`react-frontend/vercel-react-best-practices`](../skills/react-frontend/vercel-react-best-practices/SKILL.md) | MIT |

### https://arxiv.org/abs/2505.06416

Source: https://arxiv.org/abs/2505.06416
Credit: Synthesized from ScaleMCP, Agent-as-a-Graph, and AgentRouter research.
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/mcp-tool-routing`](../skills/agent-design/mcp-tool-routing/SKILL.md) | not declared |

### https://arxiv.org/abs/2510.04618

Source: https://arxiv.org/abs/2510.04618
License: not declared

| Install path | License |
| --- | --- |
| [`context-engineering/ace-context-evolution`](../skills/context-engineering/ace-context-evolution/SKILL.md) | not declared |

### https://arxiv.org/abs/2510.12323

Source: https://arxiv.org/abs/2510.12323
Credit: Synthesized from RAG-Anything, VimRAG, and multimodal RAG research.
License: not declared

| Install path | License |
| --- | --- |
| [`llm-tooling/multimodal-rag-architecture`](../skills/llm-tooling/multimodal-rag-architecture/SKILL.md) | not declared |

### https://arxiv.org/abs/2601.07711

Source: https://arxiv.org/abs/2601.07711
License: not declared

| Install path | License |
| --- | --- |
| [`agent-eval/rag-evaluation-matrix`](../skills/agent-eval/rag-evaluation-matrix/SKILL.md) | not declared |

### https://arxiv.org/abs/2605.27760

Source: https://arxiv.org/abs/2605.27760
Credit: Derived from SkillGrad, MUSE-Autoskill, MASA, Harness Updating Is Not Harness Benefit, SkillsBench granularity study, and OpenSkillEval
License: not declared

| Install path | License |
| --- | --- |
| [`agent-eval/skill-lifecycle-optimization`](../skills/agent-eval/skill-lifecycle-optimization/SKILL.md) | not declared |

### https://arxiv.org/abs/2605.30771

Source: https://arxiv.org/abs/2605.30771
Credit: Derived from Eywa: Provenance-Grounded Long-Term Memory for AI Agents and SAGE: A Novelty Gate for Efficient Memory Evolution in Agentic LLMs
License: not declared

| Install path | License |
| --- | --- |
| [`context-engineering/provenance-grounded-memory`](../skills/context-engineering/provenance-grounded-memory/SKILL.md) | not declared |

### https://arxiv.org/abs/2605.31264

Source: https://arxiv.org/abs/2605.31264
Credit: Derived from COLLEAGUE.SKILL (arXiv:2605.31264), SkillGen (arXiv:2605.10999), and SkillGenBench (arXiv:2605.18693)
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/expert-trace-skill-distillation`](../skills/agent-design/expert-trace-skill-distillation/SKILL.md) | not declared |

### https://arxiv.org/abs/2605.31308

Source: https://arxiv.org/abs/2605.31308
Credit: Derived from TraceGraph: Shared Decision Landscapes for Diagnosing and Improving Agent Trajectories (arXiv:2605.31308)
License: not declared

| Install path | License |
| --- | --- |
| [`agent-eval/agent-trajectory-diagnostics`](../skills/agent-eval/agent-trajectory-diagnostics/SKILL.md) | not declared |

### https://arxiv.org/abs/2605.31593

Source: https://arxiv.org/abs/2605.31593
Credit: Derived from Stateful Online Monitoring Catches Distributed Agent Attacks and From Prompt Injection to Persistent Control
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/stateful-agent-security-monitoring`](../skills/agent-design/stateful-agent-security-monitoring/SKILL.md) | not declared |

### https://arxiv.org/abs/2607.01456

Source: https://arxiv.org/abs/2607.01456
Credit: Written for this collection from Hong, Imani & Ahmed (2026), Han et al. (2026), and Wang et al. (2026)
License: MIT

| Install path | License |
| --- | --- |
| [`skills-management/skill-smell-audit`](../skills/skills-management/skill-smell-audit/SKILL.md) | MIT |

### https://code.claude.com/docs/en/costs

Source: https://code.claude.com/docs/en/costs
Credit: Written for this collection from Anthropic's Claude Code cost guide and the RTK and caveman projects' published measurements
License: MIT

| Install path | License |
| --- | --- |
| [`context-engineering/coding-agent-token-efficiency`](../skills/context-engineering/coding-agent-token-efficiency/SKILL.md) | MIT |

### forrestchang/andrej-karpathy-skills

Source: https://github.com/forrestchang/andrej-karpathy-skills
Credit: forrestchang/andrej-karpathy-skills by Jiayuan Zhang
License: MIT

| Install path | License |
| --- | --- |
| [`coding/karpathy-guidelines`](../skills/coding/karpathy-guidelines/SKILL.md) | MIT |

### hakimel/reveal.js

Source: https://github.com/hakimel/reveal.js
Credit: reveal.js by Hakim El Hattab — HTML presentation framework
License: not declared

| Install path | License |
| --- | --- |
| [`diagrams-slides/html-slides-creator`](../skills/diagrams-slides/html-slides-creator/SKILL.md) | not declared |

### huggingface/skills

Source: https://github.com/huggingface/skills
Credit: huggingface/skills by Hugging Face
License: Apache-2.0

| Install path | License |
| --- | --- |
| [`llm-tooling/huggingface-local-models`](../skills/llm-tooling/huggingface-local-models/SKILL.md) | Apache-2.0 |

### huggingface/smolagents

Source: https://github.com/huggingface/smolagents
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/smolagents-code-agents`](../skills/agent-design/smolagents-code-agents/SKILL.md) | not declared |

### Imbad0202/academic-research-skills

Source: https://github.com/Imbad0202/academic-research-skills
Credit: Imbad0202/academic-research-skills by Cheng-I Wu
License: CC-BY-NC-4.0

| Install path | License |
| --- | --- |
| [`context-engineering/deep-research`](../skills/context-engineering/deep-research/SKILL.md) | CC-BY-NC-4.0 |

### langchain-ai/deepagents

Source: https://github.com/langchain-ai/deepagents
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/deepagents-harness`](../skills/agent-design/deepagents-harness/SKILL.md) | not declared |

### Leonxlnx/taste-skill

Source: https://github.com/Leonxlnx/taste-skill
Credit: Leonxlnx/taste-skill by Leon Lin
License: MIT

| Install path | License |
| --- | --- |
| [`design-and-ui/design-taste-frontend`](../skills/design-and-ui/design-taste-frontend/SKILL.md) | MIT |

### luiscantero

Source: https://github.com/luiscantero
Credit: autoresearch by luiscantero by luiscantero
License: MIT

| Install path | License |
| --- | --- |
| [`agent-eval/autoresearch`](../skills/agent-eval/autoresearch/SKILL.md) | MIT |

### microsoft/skills

Source: https://github.com/microsoft/skills
Credit: microsoft/skills by Microsoft
License: MIT

| Install path | License |
| --- | --- |
| [`documentation/microsoft-docs`](../skills/documentation/microsoft-docs/SKILL.md) | MIT |

### microsoft/skills-for-fabric

Source: https://github.com/microsoft/skills-for-fabric
Credit: microsoft/skills-for-fabric by Microsoft
License: MIT

| Install path | License |
| --- | --- |
| [`databases/fabric-lakehouse`](../skills/databases/fabric-lakehouse/SKILL.md) | MIT |

### mrgoonie/claudekit-skills

Source: https://github.com/mrgoonie/claudekit-skills
Credit: mrgoonie/claudekit-skills by mrgoonie
License: MIT

| Install path | License |
| --- | --- |
| [`design-and-ui/ui-styling`](../skills/design-and-ui/ui-styling/SKILL.md) | MIT |

### Nutlope/hallmark

Source: https://github.com/Nutlope/hallmark
Credit: Adapted from Hallmark by Together AI contributors.
License: MIT

| Install path | License |
| --- | --- |
| [`design-and-ui/hallmark`](../skills/design-and-ui/hallmark/SKILL.md) | MIT |

### pbakaus/impeccable

Source: https://github.com/pbakaus/impeccable
Credit: pbakaus/impeccable by Paul Bakaus
License: Apache 2.0. Based on Anthropic's frontend-design skill. See NOTICE.md for att...

| Install path | License |
| --- | --- |
| [`design-and-ui/impeccable`](../skills/design-and-ui/impeccable/SKILL.md) | Apache 2.0. Based on Anthropic's frontend-design skill. See NOTICE.md for att... |

### supabase/agent-skills

Source: https://github.com/supabase/agent-skills
Credit: supabase/agent-skills by Supabase
License: MIT

| Install path | License |
| --- | --- |
| [`databases/supabase-postgres-best-practices`](../skills/databases/supabase-postgres-best-practices/SKILL.md) | MIT |

### vercel-labs/skills

Source: https://github.com/vercel-labs/skills
Credit: vercel-labs/skills by Vercel Labs
License: MIT

| Install path | License |
| --- | --- |
| [`skills-management/find-skills`](../skills/skills-management/find-skills/SKILL.md) | MIT |

### vllm-project/vllm

Source: https://github.com/vllm-project/vllm
License: not declared

| Install path | License |
| --- | --- |
| [`llm-tooling/vllm-serving-planner`](../skills/llm-tooling/vllm-serving-planner/SKILL.md) | not declared |

### yiouli/pixie-qa

Source: https://github.com/yiouli/pixie-qa
Credit: yiouli/pixie-qa by yiouli
License: MIT

| Install path | License |
| --- | --- |
| [`agent-eval/eval-driven-dev`](../skills/agent-eval/eval-driven-dev/SKILL.md) | MIT |

### https://huggingface.co/papers/2508.20453

Source: https://huggingface.co/papers/2508.20453
Credit: Synthesized from MCP-Bench, MCPEval, and MCP Security Bench research and repositories.
License: not declared

| Install path | License |
| --- | --- |
| [`agent-eval/mcp-agent-evaluation`](../skills/agent-eval/mcp-agent-evaluation/SKILL.md) | not declared |

### https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence

Source: https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence
Credit: Written for this collection from Anthropic's cost-optimization and prompt-caching guides and the FrugalGPT, RouteLLM, and LLMLingua papers
License: MIT

| Install path | License |
| --- | --- |
| [`llm-tooling/llm-cost-optimization`](../skills/llm-tooling/llm-cost-optimization/SKILL.md) | MIT |

### https://rich.readthedocs.io/en/stable/

Source: https://rich.readthedocs.io/en/stable/
Credit: Derived from official Rich documentation and repository examples, official Textual materials, the Toad repository as an architecture reference, and a user-supplied Claude Code TUI visual report
License: not declared

| Install path | License |
| --- | --- |
| [`agent-design/rich-claude-code-tui-clone`](../skills/agent-design/rich-claude-code-tui-clone/SKILL.md) | not declared |

### https://www.swebench.com/verified.html

Source: https://www.swebench.com/verified.html
Credit: Synthesized from SWE-bench Verified, mini-SWE-agent, SWE-ReX, and OpenHands Software Agent SDK research.
License: not declared

| Install path | License |
| --- | --- |
| [`coding/swe-agent-issue-loop`](../skills/coding/swe-agent-issue-loop/SKILL.md) | not declared |
<!-- generated:attribution-index:end -->
