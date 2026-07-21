---
license: Apache-2.0
source: https://github.com/aws/agent-toolkit-for-aws
attribution: "Amazon Web Services - agent-toolkit-for-aws (Apache-2.0)"
name: cloudfront
description: >-
  Use when configuring Amazon CloudFront distributions, caching, pricing, certificates, origins,
  viewer access, multi-tenant delivery, or logs. Route DNS-to-CloudFront work to the linked
  routing-traffic-with-route53-and-cloudfront skill and pure DNS work to route53.
version: "1.0.1"
---

# Amazon CloudFront

## When to Use

- Design, create, or tune a CloudFront distribution, cache policy, or pricing model.
- Configure CloudFront certificates, alternate domain names, origins, or origin access controls.
- Restrict viewer access or investigate standard and real-time CloudFront logs.
- Route custom-domain DNS changes to
  [routing-traffic-with-route53-and-cloudfront](../routing-traffic-with-route53-and-cloudfront/SKILL.md).

Do not use this skill for pure Route 53 DNS administration. Use
[route53](../route53/SKILL.md). Do not use it for the Route 53 alias-record portion of a CloudFront
custom domain; use the cross-service skill linked above.

## Prerequisites and Quick Reference

- Confirm the AWS account, region context, distribution ID, origins, hostnames, and change window.
- Prefer read-only discovery before proposing mutations; never print credentials or certificate keys.
- CloudFront and its ACM certificate region use `us-east-1`; verify this before certificate work.
- Read the matching reference in the task table, execute its checks, and retain command output for
  verification.

## Overview

Domain expertise for configuring Amazon CloudFront content delivery: deciding when to use
CloudFront and how it fits the wider architecture, managing custom-domain certificates and
multi-tenant distributions, protecting origins, securing content, and observing traffic.

This skill is a router. Each customer task maps to a procedure file under `references/`. Read the
matching reference in full before acting, then follow its constraints and steps. The reference
files are self-contained: each carries its own decision tables, constraints, procedure, and
troubleshooting.

Execute commands using the AWS MCP server when connected (sandboxed execution, audit logging,
observability). Fall back to the AWS CLI otherwise. CloudFront is a global service; its API calls
and the AWS Certificate Manager (ACM) certificates it uses are made in `us-east-1` regardless of
where the customer's application runs.

## Which CloudFront task do you need?

| Goal | Reference |
| --- | --- |
| Decide whether CloudFront is the right layer, see how it integrates, create a distribution, tune caching, or choose pricing | [when to use CloudFront](references/when-to-use-cloudfront.md) |
| Serve a custom domain over HTTPS, manage ACM certificates, or run many domains with a certificate per tenant | [managing certificates with CloudFront](references/managing-certificates-with-cloudfront.md) |
| Make CloudFront the only way to reach the origin (S3 OAC, VPC origins, origin mutual TLS, security groups) | [protecting your origins](references/protecting-your-origins.md) |
| Limit who can view content by identity, location, client certificate, or auth token | [securing your content](references/securing-your-content.md) |
| Get visibility into traffic with standard and real-time logs, and analyze them | [CloudFront observability](references/cloudfront-observability.md) |
| Serve multiple domains through shared configuration with per-tenant customization (SaaS, platform) | [multi-tenant distributions](references/multi-tenant-distributions.md) |

## Routing notes

- **Choosing the layer and creating a distribution vs the rest.** Whether CloudFront is the right
  entry layer, what it integrates with, creating a distribution, caching, and pricing live in the
  when-to-use reference. The other references assume a distribution exists and configure one
  aspect of it.
- **Protecting origins vs securing content.** Locking the origin so it is reachable only through
  CloudFront (OAC, VPC origins, origin mTLS) is the protecting-your-origins reference. Restricting
  which viewers can see content (signed URLs and cookies, geographic restrictions, viewer mTLS,
  edge token validation) is the securing-your-content reference. They are paired: a content control
  only holds when the origin is also locked.
- **Viewer mTLS vs origin mTLS.** Authenticating the client to CloudFront (viewer mTLS) is content
  security. Authenticating CloudFront to the origin (origin mTLS) is origin protection. Different
  controls, different references.
- **Custom domain certificate vs Route 53 DNS cutover.** Requesting and validating the ACM
  certificate and adding the alternate domain name is the managing-certificates reference here.
  Pointing the domain's DNS at the distribution, including the zone apex alias and any failover, is
  Route 53 work owned by the separate
  [routing-traffic-with-route53-and-cloudfront](../routing-traffic-with-route53-and-cloudfront/SKILL.md)
  skill.

## Cross-service work

Pointing a custom domain's DNS at a CloudFront distribution, or failing over between distributions
with Route 53 records, is cross-service work owned by the separate
[routing-traffic-with-route53-and-cloudfront](../routing-traffic-with-route53-and-cloudfront/SKILL.md)
skill. Use this skill for the CloudFront-side configuration only.

## Verification and Recovery

1. Re-read the distribution and confirm `Status` is `Deployed`, the expected aliases and origins are
   present, and the last-modified time reflects the intended change.
2. Probe the public hostname over HTTPS and record status, certificate hostname, cache headers, and
   an expected object checksum or body assertion. A successful HTTP code alone is insufficient.
3. Verify the origin is not unintentionally public when origin restriction was in scope.
4. If verification fails, stop additional changes, preserve the distribution `ETag` and prior config,
   restore the reviewed prior configuration with an `If-Match` guard, and verify again. Never retry a
   stale write after an `ETag` conflict.

## Evaluation Prompts

- **Normal:** “Put CloudFront in front of this S3 origin and define objective post-deploy checks.”
- **Difficult edge:** “Move a custom domain to CloudFront without exposing the origin or changing DNS
  before the certificate and distribution are ready.”
- **Should not activate:** “Create a weighted Route 53 record between two non-CloudFront endpoints.”

## Source Boundary

CloudFront service behavior and regional constraints are sourced from the AWS documentation below.
The read-first workflow, evidence retention, verification assertions, and rollback guard are curator
recommendations.

## Additional Resources

- [Amazon CloudFront Developer Guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html)
- [Security best practices for Amazon CloudFront (Amazon CloudFront Developer Guide)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/security-best-practices.html)
- [Amazon CloudFront product page](https://aws.amazon.com/cloudfront/)
- [Amazon CloudFront pricing](https://aws.amazon.com/cloudfront/pricing/)
