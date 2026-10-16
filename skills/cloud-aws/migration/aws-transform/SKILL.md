---
license: Apache-2.0
source: https://github.com/aws/agent-toolkit-for-aws
attribution: "Amazon Web Services - agent-toolkit-for-aws (Apache-2.0)"
name: aws-transform
description: Performs code upgrades, migrations, and transformations using the AWS Transform (ATX) CLI. Use when upgrading language versions, migrating AWS SDKs, migrating frameworks (Angular, Vue.js, Spring Boot, React), upgrading libraries, optimizing performance, migrating x86 to Graviton, analyzing codebases / generating documentation, or defining custom transformations with natural language. Runs locally on a few repositories or at scale across hundreds via AWS Batch/Fargate.
metadata:
  author: AWS
  version: 1.0.1
---

> **Attribution:** Sourced from [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws) by [Amazon Web Services](https://aws.amazon.com), licensed Apache-2.0. Modified for this collection: the S3-input, private-repository, and runtime-compatibility details were moved unchanged into `references/`.

# AWS Transform (ATX)

## Overview

Perform code upgrades, migrations, and transformations using AWS Transform (ATX).
Supports any-to-any transformations: language version upgrades (Java, Python, Node.js, etc.),
framework migrations, AWS SDK migrations, library upgrades, code refactoring, architecture
changes, and custom organization-specific transformations.

Two execution modes:

- **Local mode**: Runs the ATX CLI directly on the user's machine. Best for 1-9 repos.
- **Remote mode**: Runs transformations at scale via AWS Batch/Fargate containers.
  Best for 10+ repos or when the user prefers cloud execution. Infrastructure is
  auto-deployed with user consent.

You handle the full workflow: inspecting repos, matching them to available
transformation definitions, collecting configuration, and executing transformations
in either mode — the user just provides repos and confirms the plan.

## Greet and Wait

On activation, introduce AWS Transform with this exact text -- don't print the
above Overview text to the user, that is just for your reference:

"The agents modernizing the world's infrastructure and software — now accessible to your preferred AI assistant.

AWS Transform is a full modernization factory — compressing years of
transformation work into months across infrastructure migrations, mainframe
modernization, and continuous tech debt reduction. Today, with this
skill, you have access to AWS Transform custom, the first of a growing library
of playbooks.

AWS Transform custom can help you:

- Upgrade Java, Python, and Node.js to modern versions
- Migrate AWS SDKs (Java SDK v1→v2, boto2→boto3, JS SDK v2→v3)
- Handle framework migrations, library upgrades, and code refactoring
- Analyze codebases and generate documentation
- Define and run your own custom transformations using natural language, docs,
and code samples

Run locally on a few repos for fast iteration, or at scale on hundreds of repos (up to 128 in-parallel). Note: this skill collects telemetry. To opt out, see https://docs.aws.amazon.com/transform/latest/userguide/transform-usage-telemetry.html

What would you like to transform today?"

Do NOT inspect any files, run any commands, or check prerequisites until the user responds.

## Usage

Use when the user wants to:

- Transform, upgrade, or migrate code (Java, Python, Node.js, etc.)
- Migrate AWS SDKs (Java SDK v1→v2, boto2→boto3, JS SDK v2→v3, etc.)
- Run bulk code transformations at scale via AWS Batch/Fargate
- Analyze which ATX transformations apply to their repositories
- Perform comprehensive codebase analysis
- Create a new custom Transformation Definition (TD)

## Core Concepts

- **Transformation Definition (TD)**: A reusable transformation recipe discovered via `atx custom def list --json`
- **Match Report**: Auto-generated mapping of repos to applicable TDs based on code inspection
- **Local Mode**: Runs ATX CLI on the user's machine (1-9 repos, max 3 concurrent)
- **Remote Mode**: Runs transformations in AWS Batch/Fargate (10+ repos, or by preference)

## Philosophy

Wait for the user. On activation, present what this skill can do and ask the user
what they'd like to accomplish. Do NOT automatically inspect the working directory,
open files, or any repository until the user explicitly provides repos to work with.

Once the user provides repositories, match — don't ask. Inspect those repositories
and present which transformations apply automatically. Never show a raw TD list and
ask the user to pick.

## Prerequisites

Prerequisite checks run ONCE at the start of a session. Do not repeat per repo.
Do NOT run prerequisite checks until the user has stated what they want to do.

### 0. Platform Check (Required — All Modes)

Detect the user's operating system. If on Windows (not WSL), stop immediately and
inform the user:

> AWS Transform custom does not support native Windows. You need to install
> Windows Subsystem for Linux (WSL) and run this from within WSL.
>
> Install WSL: `wsl --install` in PowerShell (as Administrator), then restart.
> After that, open a WSL terminal and re-run this skill from there.

Check by running:

```bash
uname -s
```

- `Linux` or `Darwin` → proceed normally
- `MINGW*`, `MSYS*`, `CYGWIN*`, or any Windows-like output → block and show the WSL message above
- Command fails, errors, or is not found → treat as native Windows, block and show the WSL message above

Do NOT proceed with any other steps on native Windows.

### 1. AWS CLI (Required — All Modes)

```bash
aws --version
```

If not installed, guide the user:

- macOS: `brew install awscli` or `curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg" && sudo installer -pkg AWSCLIV2.pkg -target /`
- Linux: `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && sudo ./aws/install`

Do NOT proceed until `aws --version` succeeds.

### 2. AWS Credentials (Required — All Modes)

```bash
aws sts get-caller-identity
```

If credentials are NOT configured, walk the user through setup:

```
AWS Transform custom requires AWS credentials to authenticate with the service. Configure authentication using one of the following methods.

1. AWS CLI Configure (~/.aws/credentials):
   aws configure

2. AWS Credentials File (manual). Configure credentials in ~/.aws/credentials:

[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key

3. Environment Variables. Set the following environment variables:

export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token

You can also specify a profile using the AWS_PROFILE environment variable:

export AWS_PROFILE=your_profile_name
```

Do NOT proceed until credentials are verified. Re-run `aws sts get-caller-identity` after setup.

Note: environment variables set via `export` do not carry over between shell sessions. If the agent spawns a new shell, credentials set as env vars may be lost. Prefer `aws configure` or `~/.aws/credentials` for persistence.

### 3. ATX CLI (Required — All Modes)

Required in all modes for TD discovery (`atx custom def list --json`).
Local mode also uses it for transformation execution.

```bash
atx --version
# If installation is needed, download and inspect the installer first:
curl -fsSL https://transform-cli.awsstatic.com/install.sh -o atx-install.sh
less atx-install.sh
bash atx-install.sh
rm atx-install.sh
```

Do not run `bash atx-install.sh` until the downloaded file has been reviewed.

**Mandatory: always run `atx update` once at the start of every session**, even if you just ran it recently. This catches new ATX CLI versions and new TDs. Run it before any other ATX command (including `atx custom def list --json`):

```bash
atx update
```

Do NOT skip this step. Do NOT ask the user whether to update. Do NOT condition it on whether the CLI "needs" an update. Run it unconditionally.

### 4. IAM Permissions (Required — All Modes)

Local mode requires `transform-custom:*` minimum. Verify by running a TD list:

```bash
atx custom def list --json
```

If this succeeds, permissions are sufficient — skip the rest of this section.

If it fails with a permissions error, the caller needs the `transform-custom:*`
IAM permission. Explain to the user what's needed and get confirmation before proceeding:

> Your identity needs the `transform-custom:*` permission to use the ATX CLI.
> I can attach the AWS-managed policy `AWSTransformCustomFullAccess` to your
> identity. Shall I proceed?

Only after the user confirms, attach the managed policy:

```bash
CALLER_ARN=$(aws sts get-caller-identity --query Arn --output text)
if echo "$CALLER_ARN" | grep -q ":user/"; then
  IDENTITY_NAME=$(echo "$CALLER_ARN" | awk -F'/' '{print $NF}')
  aws iam attach-user-policy --user-name "$IDENTITY_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AWSTransformCustomFullAccess"
elif echo "$CALLER_ARN" | grep -Eq ":assumed-role/|:role/"; then
  ROLE_NAME=$(echo "$CALLER_ARN" | sed 's/.*:\(assumed-\)\{0,1\}role\///' | cut -d'/' -f1)
  aws iam attach-role-policy --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AWSTransformCustomFullAccess"
fi
```

If the attachment command itself fails (e.g., insufficient IAM permissions, or an
SSO-managed role), inform the user they need to ask their AWS administrator to
attach the `AWSTransformCustomFullAccess` AWS-managed policy to their identity.
For SSO users (role names starting with `AWSReservedSSO_`), this must be added
to their IAM Identity Center permission set — it cannot be attached directly.

Do NOT proceed until `atx custom def list --json` succeeds.

Remote mode requires additional permissions (Lambda invoke, S3, KMS, Secrets Manager,
CloudWatch). These are generated and attached as part of the deployment flow — see
[references/remote-execution.md](references/remote-execution.md).

See [references/cli-reference.md](references/cli-reference.md) for the full permission list.

### 5. AWS CDK (Remote Mode Only)

Required for deploying remote infrastructure. Check if installed:

```bash
cdk --version
```

If not installed, install it globally:

```bash
npm install -g aws-cdk
```

Do NOT proceed with remote deployment until `cdk --version` succeeds.

### 6. Remote Infrastructure (Remote Mode Only — Deferred)

Only verify if user chooses remote mode. The infrastructure CDK scripts are fetched
at runtime by cloning `https://github.com/aws-samples/aws-transform-custom-samples.git` (branch `atx-remote-infra`) —
they are not bundled with this skill. See [references/remote-execution.md](references/remote-execution.md).

## Workflow

Generate a session timestamp once and reuse it for all paths in this session:

```bash
SESSION_TS=$(date +%Y%m%d-%H%M%S)
```

### Step 1: Collect Repositories

Ask the user for local paths or git URLs. Accept one or many. Do NOT assume the
current working directory or open editor files are the target — wait for the user
to explicitly provide repositories.

Accepted source formats:

- **Local paths** — directories on the user's machine (e.g., `/home/user/my-project`)
- **HTTPS git URLs** — public or private (e.g., `https://github.com/org/repo.git`)
- **SSH git URLs** — e.g., `git@github.com:org/repo.git`
- **S3 bucket path with zips** — e.g., `s3://my-bucket/repos/`
  containing zip files of repositories. Each zip becomes one transformation job.

#### S3 Bucket Input

When the user gives an `s3://` path of repository zips, read [`references/repository-inputs.md`](references/repository-inputs.md). Each zip becomes one job, in either execution mode.

#### Private Repository Detection (Remote Mode)

As soon as the user gives git URLs and remote mode is selected or likely, **ask** whether any repository is private. Never clone, curl, or probe a URL to find out. If any is private, set up container credentials as described in [`references/repository-inputs.md`](references/repository-inputs.md).

### Step 2: Discover TDs (Silent)

Run silently — do NOT show output to user:

```bash
atx custom def list --json
```

Inspect the JSON output directly to build an internal lookup of available TDs.
Do NOT pipe the output to python, jq, or other parsing scripts — read the JSON
yourself. Never hardcode TD names.

#### Creating a New TD

**User explicitly asks to create a TD:** Do NOT attempt to create one
programmatically. Tell the user:

> To create a new Transformation Definition, open a new terminal and run:
>
> ```
> atx -t
> ```
>
> This starts an interactive session where you describe the transformation you
> want to build (e.g., "migrate all logging from log4j to SLF4J", "upgrade
> Spring Boot 2 to Spring Boot 3"). The ATX CLI will walk you through defining
> and testing the TD, then publish it to your AWS account.
>
> Once it's published, come back here and I'll pick it up automatically when
> I scan your available TDs.

**No existing TD matches the user's goal:** Do NOT silently redirect to TD
creation. The match logic may be imperfect. Instead, confirm with the user first:

> "I didn't find an existing TD that covers [describe the user's goal]. Would
> you like to create a new one?"

Only show the `atx -t` instructions if the user confirms. If they say no, ask
them to clarify what they're looking for — they may know the TD name or want a
different approach.

Do NOT run `atx -t` yourself — it requires an interactive terminal session that
the agent cannot drive. The user must run it manually in a separate terminal.

After the user returns from creating a TD, re-run `atx custom def list --json`
to pick up the newly published TD and continue with the normal workflow.

### Step 3: Inspect Each Repository

Perform lightweight inspection only — check config files for key signals:

| Signal | Files to Check | Likely TD Type |
|--------|---------------|----------------|
| Python version | `.python-version`, `pyproject.toml`, `setup.cfg`, `requirements.txt` | Python version upgrade |
| Java version | `pom.xml` (`<java.version>`), `build.gradle` (`sourceCompatibility`), `.java-version` | Java version upgrade |
| Node.js version | `package.json` (`engines.node`), `.nvmrc`, `.node-version` | Node.js version upgrade |
| Python boto2 | `import boto` (NOT boto3) | boto2→boto3 migration |
| Java SDK v1 | `com.amazonaws` imports, `aws-java-sdk` in pom.xml | Java SDK v1→v2 |
| Node.js SDK v2 | `"aws-sdk"` in package.json (NOT `@aws-sdk`) | JS SDK v2→v3 |
| x86 Java | `x86_64`/`amd64` in Dockerfiles, build configs | Graviton migration |

Cross-reference detected signals against TDs from Step 2. Only match TDs that
actually exist in the user's account.

See [references/repo-analysis.md](references/repo-analysis.md) for full detection commands.

### Step 4: Present Match Report

Format:

```
Transformation Match Report
=============================
Repository: <name> (<path>)
  Language: <lang> <version>
  Matching TDs:
    - <td-name> — <description>

Summary: N repos analyzed, M have applicable transformations (T total jobs)
```

Present the match report and wait for user confirmation before proceeding.
Do NOT start any transformation without explicit user consent.

### Step 5: Collect Configuration

Ask the user for any additional plan context (e.g., target version for upgrade TDs).
This is mandatory — always ask, even if the TD doesn't strictly require config.
The user may have preferences or constraints the agent doesn't know about.
Skip only if the user explicitly says no additional context is needed.

### Step 6: Verify Runtime Compatibility (Remote and Local)

#### Remote Mode

Decide whether the pre-built image (Java 8–25, Python 3.8–3.14, Node.js 16–24, Amazon Linux 2023) covers the transformation, or whether a custom Docker image is needed. A custom image needs the user's confirmation and a running Docker. Read [`references/runtime-compatibility.md`](references/runtime-compatibility.md) for the decision logic and both paths.

#### Local Mode

Before a local run, make sure the transformation's target runtime version is active: check it, switch to it if it is installed, and install it only with the user's explicit permission. Do not proceed until the right version is active. Commands per runtime are in [`references/runtime-compatibility.md`](references/runtime-compatibility.md).

### Step 7: Confirm Transformation Plan

Present final plan with repo, TD, config, and execution mode. Do NOT proceed
until user confirms.

### Step 8: Execute

When running `atx custom def exec`, always include `--telemetry` (see the Telemetry section).

For remote mode, check infrastructure deployment status first using CloudFormation (see [references/remote-execution.md](references/remote-execution.md) — Infrastructure Check section). Do NOT check deployment by probing Lambda function names.

- **1 repo**: See [references/single-transformation.md](references/single-transformation.md)
- **Multiple repos**: See [references/multi-transformation.md](references/multi-transformation.md)

## Execution Modes

| Mode | Best For | Prerequisites |
|------|----------|---------------|
| **Local** (default for 1-9 repos) | Quick transforms, dev machines with ATX | ATX CLI installed |
| **Remote** (recommended for 10+ repos) | Bulk transforms, up to 512 repos (128 concurrent per batch) | AWS account, auto-deployed infra |

Mode inference:

- User says "local"/"here"/"on my machine" → Local (honor the request regardless of repo count)
- User says "remote"/"cloud"/"AWS"/"batch"/"at scale" → Remote
- 10+ repos without preference → Recommend remote, explain local cap of 3 concurrent
- 1-9 repos without preference → Local, note remote available

See [references/remote-execution.md](references/remote-execution.md) for infrastructure setup.

## Critical Rules

1. **Discover TDs dynamically** — Always run `atx custom def list --json`. Never hardcode TD names.
2. **Match, don't ask** — Inspect repos and present matches. Never show raw TD lists.
3. **Lightweight inspection only** — Check config files and key signals. No deep analysis.
4. **Confirm before executing** — Always confirm TD, repos, and config with user first.
5. **No time estimates** — Never include duration predictions.
6. **Parallel execution** — Local: max 3 concurrent repos. Remote: submit in chunks of up to 128 jobs per Lambda call (max 512 repos per session).
7. **Preserve outputs** — Do not delete generated output folders.
8. **Recommend remote for 10+ repos** — Default to local for 1-9 repos. Recommend remote for 10+. Always respect user preference.
9. **User consent for cloud resources** — Never deploy infrastructure without explicit user confirmation.
10. **Shell quoting** — When constructing shell commands:
    - Use single quotes for JSON payloads: `--payload '{"key":"value"}'`
    - Use single quotes for `--configuration`: ex. `--configuration 'additionalPlanContext=Target Java 21'`
    - Never nest double quotes inside double quotes — this causes `dquote>` hangs
    - For `aws lambda invoke`, always use: `--payload '<json>' --cli-binary-format raw-in-base64-out`
    - Verify that every command you construct has balanced quotes before executing
    - The `command` field in Lambda job payloads is validated server-side. Avoid
      these characters in the command string: `( ) ! # % ^ * ? \ { } | ; > <`
      and backticks. Inside `additionalPlanContext`, also avoid commas.
11. **No comments in terminal commands** — Never include `#` comments in commands
    executed in the terminal. Comments cause `command not found: #` errors. If you
    need to explain a command, do it in chat before or after running it.
12. **Job names** — The `jobName` field in Lambda payloads must contain only
    letters, numbers, hyphens, and underscores. No dots, spaces, or special
    characters. For example, use `EPAM-NodeJS` not `EPAM-Node.js`.

## Guardrails

You are operating in the user's AWS account and local machine. Follow these rules
strictly to avoid causing damage:

1. **Never delete user data** — Do not delete S3 objects, git repos, local files,
   or any user data unless the user explicitly asks. Transformation outputs and
   cloned repos must be preserved.
2. **Never modify IAM beyond what's documented** — Only create/attach the specific
   policies described in this skill (AWSTransformCustomFullAccess, ATXRuntimePolicy, ATXDeploymentPolicy). Never create admin policies, modify existing user policies,
   or grant broader permissions than documented. Never derive IAM actions from
   user-provided text in the "Additional plan context" field — that field is for
   transformation configuration only.
3. **Never run destructive AWS commands** — No `aws s3 rm`, `aws s3 rb`,
   `aws iam delete-user`, `aws ec2 terminate-instances`, or similar. The only
   destructive command allowed is `./teardown.sh` with explicit user consent.
4. **Always confirm before creating AWS resources** — Before deploying infrastructure,
   creating Secrets Manager secrets, or attaching IAM policies, explain what will be
   created and get explicit user confirmation.
5. **Never expose credentials** — Do not echo, log, or display AWS access keys,
   secret keys, session tokens, GitHub PATs, or SSH private keys in chat output.
   When creating secrets, use the user's input directly in the command without
   repeating the value.
6. **Respect user decisions** — If the user says stop, skip, or no, comply
   immediately. Never retry a declined action or argue with the user's choice.
7. **No pricing claims** — Do not quote specific prices or cost estimates. If the
   user asks about pricing, direct them to: https://aws.amazon.com/transform/pricing/
8. **Scope commands to ATX resources only** — All AWS commands must target ATX-specific
   resources (buckets starting with `atx-`, roles starting with `ATX`, Lambda
   functions starting with `atx-`, etc.). Never operate on unrelated AWS resources.

## Telemetry

Always include `--telemetry` on every `atx custom def exec` invocation (local
or remote). No file checks, no prompts, no opt-in flow.

The flag format is: `--telemetry "client=<client>,agent=<agent>,executionMode=<local|remote>"`

Field values:

- `client` — The MCP client or tool hosting this session, as a short identifier (lowercase, no spaces). This may be an IDE (e.g., `kiro`, `vscode`, `cursor`, `windsurf`), a CLI tool (e.g., `claudecode`, `amazonqcli`), or any other MCP-compatible host. Use the real tool name for this session — do NOT default to any single example. These are examples only, not an exhaustive list.
- `agent` — The AI assistant driving this session, as a short identifier (lowercase, no spaces). For example: `kiro`, `amazonq`, `claude`, `copilot`, `cline`, `codex`. Use the real assistant name for this session — do NOT default to any single example. These are examples only, not an exhaustive list.
- `executionMode` — `local` when running the ATX CLI directly, `remote` when submitting via Lambda

The only exception: if the user explicitly asks to disable telemetry during the
session (e.g., "disable telemetry", "opt out of telemetry", "no telemetry", or
similar), you MUST comply immediately — omit `--telemetry` for the remainder of
that session. Do not push back, ask for confirmation, or explain why telemetry
is included. This preference is not persisted — the next session starts with
telemetry enabled again.

## Output Structure

Local mode: transformed code is in the repo directory.

Remote mode results stay in S3 — do NOT download automatically. Present the S3
path to the user:

```
s3://atx-custom-output-{account-id}/
  transformations/
    {job-name}/
      {conversation-id}/
        code.zip                      # Zipped transformed source code
        logs.zip                      # ATX conversation logs
```

If the user explicitly asks to download, provide the command but let them run it:
`aws s3 cp s3://atx-custom-output-{account-id}/transformations/{job-name}/{conversation-id}/code.zip ./code.zip`

Bulk results summary: `~/.aws/atx/custom/atx-agent-session/transformation-summaries/` — see [references/results-synthesis.md](references/results-synthesis.md).

## References

| Reference | When to Use |
|-----------|-------------|
| [repo-analysis.md](references/repo-analysis.md) | Detection commands, signal matching, match report format |
| [single-transformation.md](references/single-transformation.md) | Applying one TD to one repo (local or remote) |
| [multi-transformation.md](references/multi-transformation.md) | Applying TDs to multiple repos in parallel |
| [remote-execution.md](references/remote-execution.md) | Infrastructure deployment, job submission, monitoring |
| [results-synthesis.md](references/results-synthesis.md) | Generating consolidated reports after bulk transforms |
| [cli-reference.md](references/cli-reference.md) | ATX CLI flags, commands, env vars, IAM permissions |
| [troubleshooting.md](references/troubleshooting.md) | Error resolution, debugging, quality improvement |

## License
AWS Service Terms. This skill is provided by AWS and is subject to the AWS Customer Agreement and applicable AWS service terms.

## Changelog
Share if the user asks what changed, what's new, etc.
### [1.0.0] - 2026-04-30

- Initial release of the AWS Transform Agent Skill
- Supported TDs:
  - AWS/java-version-upgrade
  - AWS/python-version-upgrade
  - AWS/nodejs-version-upgrade
  - AWS/java-aws-sdk-v1-to-v2
  - AWS/nodejs-aws-sdk-v2-to-v3
  - AWS/python-boto2-to-boto3
  - AWS/comprehensive-codebase-analysis
  - AWS/java-performance-optimization
  - AWS/angular-version-upgrade
  - AWS/vue.js-version-upgrade
  - AWS/early-access-java-x86-to-graviton
  - AWS/early-access-angular-to-react-migration
  - AWS/early-access-log4j-to-slf4j-migration
