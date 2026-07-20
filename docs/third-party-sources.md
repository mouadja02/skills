# Third-Party Sources

This repository includes skills adapted from public upstream projects. Individual imported `SKILL.md` files also include source attribution near the end of the file.

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

## Qdrant Agent Skills

Source repository: https://github.com/qdrant/skills

Imported from `skills/qdrant-performance-optimization/` on the `main` branch:

| Local install path | Upstream path |
| --- | --- |
| `llm-tooling/qdrant-performance-optimization` | `skills/qdrant-performance-optimization` |
| `llm-tooling/qdrant-performance-optimization/indexing-performance-optimization` | `skills/qdrant-performance-optimization/indexing-performance-optimization` |
| `llm-tooling/qdrant-performance-optimization/memory-usage-optimization` | `skills/qdrant-performance-optimization/memory-usage-optimization` |
| `llm-tooling/qdrant-performance-optimization/search-speed-optimization` | `skills/qdrant-performance-optimization/search-speed-optimization` |

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
| `cloud-aws/networking/networkfirewall` | `skills/specialized-skills/networking-and-content-delivery-skills/networkfirewall` |
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
