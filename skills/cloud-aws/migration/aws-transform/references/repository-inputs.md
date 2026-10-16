# Step 1 details: S3 inputs and private repositories

Moved verbatim from SKILL.md so the entry file stays small. Step numbers refer to the workflow in SKILL.md; links resolve from this folder.

#### S3 Bucket Input

If the user provides an S3 path containing zip files, ask which execution mode
they prefer (if not already specified). S3 input works in both modes:

**Remote mode:** Copy the zips from the user's bucket to the managed source bucket,
then submit jobs pointing to the managed copies:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SOURCE_BUCKET="atx-source-code-${ACCOUNT_ID}"

# List all zips in the user's bucket path
aws s3 ls s3://user-bucket/repos/ --recursive | grep '\.zip$'

# Copy each zip to the managed source bucket
aws s3 sync s3://user-bucket/repos/ s3://${SOURCE_BUCKET}/repos/ --exclude "*" --include "*.zip"
```

Then submit a batch job with one job per zip, each pointing to
`s3://${SOURCE_BUCKET}/repos/<filename>.zip`. The container handles zip extraction
automatically. See [references/multi-transformation.md](multi-transformation.md) for batch submission.
The managed source bucket has a 7-day lifecycle — copied zips auto-delete.

**Local mode:** Download and extract each zip locally:

```bash
mkdir -p ~/.aws/atx/custom/atx-agent-session/repos
aws s3 sync s3://user-bucket/repos/ ~/.aws/atx/custom/atx-agent-session/repos/ --exclude "*" --include "*.zip"
for zip in ~/.aws/atx/custom/atx-agent-session/repos/*.zip; do
  name=$(basename "$zip" .zip)
  unzip -qo "$zip" -d "$HOME/.aws/atx/custom/atx-agent-session/repos/${name}-$SESSION_TS/"
done
```

Use the extracted directories as `<repo-path>` for local execution. Standard local
mode limits apply (max 3 concurrent repos).

#### Private Repository Detection (Remote Mode)

**Always ask the user** — do NOT try to determine repo visibility yourself. Never
attempt to clone, curl, or probe a URL to check if it's public or private. Simply
ask the user. As soon as the user provides git URLs and remote mode is selected
(or likely), ask:

> "Are any of these repositories private? If so, the remote container needs
> credentials to clone them — I'll walk you through the setup."

Do NOT skip this question. Do NOT try to infer visibility by attempting a clone,
curl, or any other network request. Just ask.

If the user confirms repos are private, determine the credential type based on URL format:

First, resolve the region (use for all Secrets Manager commands below):

```bash
REGION=${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null)}}
REGION=${REGION:-us-east-1}
```

**For HTTPS URLs** — check whether a GitHub PAT is already configured:

```bash
aws secretsmanager describe-secret --secret-id "atx/github-token" --region "$REGION" 2>/dev/null \
  && echo "CONFIGURED" || echo "NOT_CONFIGURED"
```

If CONFIGURED, ask the user: "A GitHub PAT is already stored. Would you like to
keep using it, or replace it with a new one?" If they want to replace it, tell
them to run:

```
aws secretsmanager put-secret-value --secret-id "atx/github-token" --region "$REGION" --secret-string "YOUR_TOKEN_HERE"
```

If NOT_CONFIGURED, explain what's needed and tell the user to run the create command:
> "Private HTTPS repos need a GitHub Personal Access Token (PAT) stored in AWS
> Secrets Manager. The remote container fetches it at startup to clone your repos.
> The token stays in your AWS account — you can delete it anytime.
>
> The PAT needs the `repo` scope for private repositories. Create one at
> https://github.com/settings/tokens and then run:
>
> ```
> aws secretsmanager create-secret --name "atx/github-token" --region "$REGION" --secret-string "YOUR_TOKEN_HERE"
> ```
>
> Delete anytime: `aws secretsmanager delete-secret --secret-id atx/github-token --region "$REGION" --force-delete-without-recovery`"

Do NOT ask the user to paste their token in chat. They run the command themselves.
Wait for the user to confirm it's done, then verify:

```bash
aws secretsmanager describe-secret --secret-id "atx/github-token" --region "$REGION" 2>/dev/null \
  && echo "CONFIGURED" || echo "NOT_CONFIGURED"
```

**For SSH URLs** (`git@...` or `ssh://...`) — check whether an SSH key is configured:

```bash
aws secretsmanager describe-secret --secret-id "atx/ssh-key" --region "$REGION" 2>/dev/null \
  && echo "CONFIGURED" || echo "NOT_CONFIGURED"
```

If CONFIGURED, ask the user: "An SSH key is already stored. Would you like to
keep using it, or replace it with a new one?" If they want to replace it, tell
them to run:

```
aws secretsmanager put-secret-value --secret-id "atx/ssh-key" --region "$REGION" --secret-string "$(cat <path-to-your-private-key>)"
```

If NOT_CONFIGURED, explain what's needed and tell the user to run the create command:
> "SSH repos need an SSH private key stored in AWS Secrets Manager. The remote
> container fetches it at startup to clone your repos.
>
> Run:
>
> ```
> aws secretsmanager create-secret --name "atx/ssh-key" --region "$REGION" --secret-string "$(cat <path-to-your-private-key>)"
> ```
>
> Delete anytime: `aws secretsmanager delete-secret --secret-id atx/ssh-key --region "$REGION" --force-delete-without-recovery`"

Do NOT ask the user to paste their SSH key in chat. They run the command themselves.

For local mode, private repo credentials are not needed — the user's local git
config handles authentication. Skip this check entirely for local mode.
