---
name: clickclack
description: "ClickClack ops: self-hosted chat app deploy, Hetzner/Docker, DNS checks."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# ClickClack

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this for ClickClack product/runtime ops, deploys, hosted app checks, and domain questions.

- Repo: https://github.com/openclaw/clickclack
- Product: self-hostable Slack-style chat app

## Deploy (Golden Path)

1. **Local refresh**:
   ```bash
   cd ~/Projects/clickclack
   git status --short --branch
   git fetch origin
   git merge --ff-only origin/main
   ```

2. **Decide deployed delta**:
   ```bash
   git log --oneline <old>..HEAD
   git diff --stat <old>..HEAD
   ```

3. **Archive clean HEAD only** (do not rsync untracked local files):
   ```bash
   short=$(git rev-parse --short=12 HEAD)
   git archive --format=tar HEAD | ssh root@SERVER "rm -rf /opt/app.next && mkdir -p /opt/app.next && tar -C /opt/app.next -xf - && printf '%s\n' '$short' > /opt/app.next/.deploy-commit"
   ```

4. **Backup before migrations**:
   ```bash
   docker exec app app backup --data /app/data --out /app/data/backups/before-$(date -u +%Y%m%dT%H%M%SZ).db
   ```

5. **Build**:
   ```bash
   docker build --label org.opencontainers.image.revision="$short" -t app:"$short" -t app:latest /opt/app.next
   ```

6. **Replace container**:
   ```bash
   docker stop app && docker rm app
   docker run -d --name app --restart unless-stopped \
     --env-file /root/app.env.current \
     -p 127.0.0.1:8080:8080 \
     -v /var/lib/app:/app/data \
     app:latest serve --addr :8080 --data /app/data
   ```

## Verify

```bash
# Container health
docker ps --filter name=app
docker inspect app --format '{{index .Config.Labels "org.opencontainers.image.revision"}}'

# HTTP check
curl -I https://your-domain.com
curl -fsS http://127.0.0.1:8080/healthz
```

## Guardrails

- Do not print OAuth secrets or magic tokens.
- Always back up SQLite before replacing the container (migrations run on boot).
- Deploy from clean git archives, not dirty working trees.
