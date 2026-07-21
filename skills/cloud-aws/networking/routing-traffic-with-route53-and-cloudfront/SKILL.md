---
license: Apache-2.0
source: https://github.com/aws/agent-toolkit-for-aws
attribution: "Amazon Web Services - agent-toolkit-for-aws (Apache-2.0)"
name: routing-traffic-with-route53-and-cloudfront
description: >-
  Use when routing a custom domain to Amazon CloudFront with Route 53 alias A/AAAA records, alternate
  domain names, ACM certificates, and IPv6. Coordinates readiness, DNS cutover, verification, and
  rollback across both services.
version: "1.0.1"
---

# Routing Traffic with Route 53 and CloudFront

## When to Use

- Attach a custom domain to a CloudFront distribution and route it through Route 53.
- Coordinate ACM validation, CloudFront alternate domain names, and alias A/AAAA records.
- Plan a low-risk DNS cutover or diagnose the Route 53-to-CloudFront boundary.

Do not use this skill for CloudFront caching/origin work without DNS changes; use
[cloudfront](../cloudfront/SKILL.md). Do not use it for Route 53 records targeting non-CloudFront
endpoints; use [route53](../route53/SKILL.md).

## Prerequisites and Quick Reference

- Capture the account, public hosted-zone ID, FQDN, distribution ID/domain, current DNS answers and
  TTLs, certificate ARN/status, and rollback target.
- Confirm the ACM certificate is in `us-east-1`, covers the FQDN, and is issued before DNS cutover.
- Confirm the distribution is deployed and lists the FQDN as an alternate domain name.
- Prefer alias A and AAAA records for Route 53-hosted domains; retain the change ID and prior records.

## Overview

Domain expertise for configuring Amazon Route 53 to route traffic to Amazon CloudFront distributions using custom domain names. Covers hosted zone management, alias A/AAAA records, alternate domain name (CNAME) configuration, and ACM certificate setup for HTTPS.

## Configure Route 53 to route traffic to a CloudFront distribution

To set up a custom domain for a CloudFront distribution with Route 53 DNS, follow the procedure exactly.
See [Route 53 CloudFront routing procedure](references/route53-cloudfront-routing.md).

The procedure covers:

- Verifying CloudFront distribution status and CNAME configuration
- Requesting and validating ACM certificates (must be in us-east-1)
- Creating or locating public hosted zones
- Creating alias A and AAAA records pointing to CloudFront
- Monitoring DNS propagation

## Verification and Recovery

1. Before cutover, verify the certificate and distribution readiness checks above. Do not create the
   alias first and hope the distribution converges later.
2. After the change reports `INSYNC`, query authoritative name servers for A and AAAA, then make an
   HTTPS request using the custom hostname. Assert the certificate hostname, expected distribution
   response, and an application-specific body/header condition.
3. Confirm direct origin access remains blocked when origin protection is expected.
4. If any assertion fails, stop, restore the captured prior A/AAAA records, wait for that change to
   become `INSYNC`, and repeat DNS and HTTPS checks. Preserve the failed change ID and observations.

## Evaluation Prompts

- **Normal:** “Route `www.example.com` to an existing CloudFront distribution with A/AAAA aliases.”
- **Difficult edge:** “Cut over the zone apex with low risk when an old CNAME-like target is cached and
  IPv6 clients must work.”
- **Should not activate:** “Create latency-based Route 53 records for two API Gateway endpoints.”

## Source Boundary

The certificate-region, alternate-domain, and Route 53 alias requirements are sourced from the AWS
documentation below and the imported Apache-2.0 upstream. The readiness gate, evidence capture,
application assertion, and rollback sequence are curator recommendations.

## Additional Resources

- [Routing traffic to a CloudFront distribution](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-cloudfront-distribution.html)
- [CloudFront alternate domain names](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CNAMEs.html)

## Troubleshooting

### Domain not in CloudFront CNAMEs

Add the domain as an alternate domain name in the CloudFront distribution configuration before creating Route 53 records.

### SSL certificate issues

ACM certificates for CloudFront must be in us-east-1. Ensure the certificate is validated and associated with the distribution.

### Private hosted zone

CloudFront only works with public hosted zones. Create a public hosted zone if only a private one exists.

### DNS propagation delays

Changes typically propagate within 60 seconds but full global propagation can take up to 48 hours. Use `nslookup` or `dig` to verify.
