# Step 6: Verify runtime compatibility

Moved verbatim from SKILL.md so the entry file stays small. Step numbers refer to the workflow in SKILL.md; links resolve from this folder.

#### Remote Mode

Before submitting remote jobs, determine whether the pre-built image covers the
target runtime or if a custom Docker build is needed.

**Pre-built image includes:**

- **Java**: 8, 11, 17, 21, 25 (Amazon Corretto) with Maven and Gradle 9.4
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 (dnf + pyenv)
- **Node.js**: 16, 18, 20, 22, 24 (nvm) with yarn, pnpm, TypeScript, ts-node
- **Build tools**: gcc, g++, make, patch
- **CLI tools**: AWS CLI v2, ATX CLI, git, jq, curl, unzip, tar
- **OS**: Amazon Linux 2023 (x86_64)

**Decision logic:**

1. Based on the transformation requirements (source runtime, target runtime,
   build tools, and any other dependencies), determine whether everything
   needed is available in the pre-built image listed above
2. If **yes** → use the pre-built image path (no Docker required). Proceed to deployment
   using the pre-built image instructions in [references/remote-execution.md](remote-execution.md).
3. If **no** → use the custom image path (Docker required). Inform the user:

> The remote container doesn't include [language/tool version]. To run this
> transformation remotely, I'll need to build a custom container image. This
> requires Docker installed and running on your machine. It's a one-time change
> — about 5-10 minutes. Want me to proceed?

If the user confirms, follow the custom image path in
[references/remote-execution.md](remote-execution.md): clear `prebuiltImageUri`,
customize the Dockerfile, and deploy.

If the user declines, suggest local mode as an alternative (if the tools are
available on their machine).

**Dockerfile customization (custom image path only):**

First, read the Dockerfile to see what's installed:

```bash
ATX_INFRA_DIR="$HOME/.aws/atx/custom/remote-infra"
cat "$ATX_INFRA_DIR/container/Dockerfile" 2>/dev/null
```

1. Ensure the infrastructure repo is cloned and up to date:

   ```bash
   ATX_INFRA_DIR="$HOME/.aws/atx/custom/remote-infra"
   if [ -d "$ATX_INFRA_DIR" ]; then
     git -C "$ATX_INFRA_DIR" add -A
     git -C "$ATX_INFRA_DIR" commit -m "Local customizations" -q 2>/dev/null || true
     git -C "$ATX_INFRA_DIR" pull -q
   else
     git clone -b atx-remote-infra --single-branch https://github.com/aws-samples/aws-transform-custom-samples.git "$ATX_INFRA_DIR"
   fi
   ```

   If `git pull` reports a merge conflict, resolve it by keeping both upstream
   changes and the user's customizations in the `CUSTOM LANGUAGES AND TOOLS`
   section of the Dockerfile, then commit the merge.

2. Edit `$ATX_INFRA_DIR/container/Dockerfile`. Find the section marked
   `# CUSTOM LANGUAGES AND TOOLS` and insert `RUN` commands after the comment
   block, before the `USER root` line.

   For missing versions of already-installed languages, add the version in the
   custom section. Examples:

   ```dockerfile
   # Java 23 (Amazon Corretto — direct install, must run as root)
   # Do NOT use dnf in the custom section — pyenv overrides the system python3
   # that dnf depends on, causing "No module named 'dnf'" errors.
   USER root
   RUN curl -fsSL "https://corretto.aws/downloads/latest/amazon-corretto-23-x64-linux-jdk.tar.gz" -o /tmp/corretto23.tar.gz && \
       mkdir -p /usr/lib/jvm && \
       tar -xzf /tmp/corretto23.tar.gz -C /usr/lib/jvm && \
       rm /tmp/corretto23.tar.gz && \
       ln -sfn /usr/lib/jvm/amazon-corretto-23.* /usr/lib/jvm/corretto-23

   # Node.js 23 (via nvm — must run as atxuser)
   USER atxuser
   RUN . /home/atxuser/.nvm/nvm.sh && nvm install 23
   USER root

   # Python 3.15 (via pyenv — must run as atxuser)
   USER atxuser
   RUN eval "$(/home/atxuser/.pyenv/bin/pyenv init -)" && \
       MAKE_OPTS="-j$(nproc)" /home/atxuser/.pyenv/bin/pyenv install 3.15.0
   USER root
   ```

   For entirely new languages, avoid `dnf` in the custom section — pyenv
   overrides the system python3 that `dnf` depends on. Use language-specific
   installers instead:

   ```dockerfile
   # Go
   RUN curl -fsSL https://go.dev/dl/go1.22.0.linux-amd64.tar.gz -o /tmp/go.tar.gz && \
       tar -tzf /tmp/go.tar.gz >/dev/null && \
       tar -C /usr/local -xzf /tmp/go.tar.gz && \
       rm /tmp/go.tar.gz
   ENV PATH="/usr/local/go/bin:$PATH"

   # Ruby (via rbenv — must run as atxuser)
   USER atxuser
   RUN git clone --depth 1 https://github.com/rbenv/rbenv.git /home/atxuser/.rbenv && \
       git clone --depth 1 https://github.com/rbenv/ruby-build.git /home/atxuser/.rbenv/plugins/ruby-build && \
       /home/atxuser/.rbenv/bin/rbenv install 3.3.0 && \
       /home/atxuser/.rbenv/bin/rbenv global 3.3.0
   ENV PATH="/home/atxuser/.rbenv/shims:/home/atxuser/.rbenv/bin:$PATH"
   USER root

   # Rust
   USER atxuser
   RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup-init.sh && \
       sed -n '1,240p' /tmp/rustup-init.sh && \
       sh /tmp/rustup-init.sh -y && \
       rm /tmp/rustup-init.sh
   ENV PATH="/home/atxuser/.cargo/bin:$PATH"
   USER root
   ```

   Review the downloaded Rust installer text in the build log before accepting
   the image. For stronger reproducibility, pin and verify release checksums for
   downloaded runtime artifacts when the upstream project publishes them.

3. Update the version switcher in `$ATX_INFRA_DIR/container/entrypoint.sh`.
   Find the relevant `switch_*_version` function and add a case for the new
   version. For Java versions installed via direct download, find the extracted
   directory name under `/usr/lib/jvm/`. For example, to add Java 23:

   ```bash
   # In switch_java_version(), add to the case statement:
   23) java_home="/usr/lib/jvm/corretto-23" ;;
   ```

   Check the actual directory name: `ls /usr/lib/jvm/` — use the directory
   that matches the version you installed.

   For Node.js, nvm handles arbitrary versions automatically — no entrypoint
   change needed. For Python, pyenv handles arbitrary versions — no entrypoint
   change needed (the existing pyenv fallback logic finds it).

4. Deploy (or redeploy): `cd "$ATX_INFRA_DIR" && ./setup.sh`
   CDK hashes the `container/` directory — any file change triggers a rebuild
   and push to ECR automatically.

After redeployment, set the `environment` field on the job to the exact target
version (e.g., `"JAVA_VERSION":"23"`, not `"21"`). The version switcher in the
entrypoint reads this and activates the correct runtime.

If the user declines, suggest local mode as an alternative (if the tools are
available on their machine).

#### Local Mode

Before running local transformations, verify the user has the target runtime
version installed. This applies to any language or runtime the transformation
targets — Java, Python, Node.js, Ruby, Go, Rust, .NET, etc. Check the current
version of whatever runtime the TD requires. For example:

```bash
java -version    # Java transformations
python3 --version # Python transformations
node --version   # Node.js transformations
ruby --version   # Ruby transformations
go version       # Go transformations
```

If the target version is not active, check whether it's already installed:

```bash
# Java: check common install locations
/usr/libexec/java_home -V 2>&1          # macOS
ls /usr/lib/jvm/ 2>/dev/null            # Linux
# Python: check if the specific version binary exists
which python3.12 2>/dev/null            # adjust version as needed
# Node.js: check if nvm is available, or look for the binary
command -v nvm &>/dev/null && nvm ls 2>/dev/null
which node 2>/dev/null && node --version
```

If the target version is found, switch to it:

- Java: `export JAVA_HOME=<path to JDK> && export PATH="$JAVA_HOME/bin:$PATH"`
- Python: `pyenv shell 3.15.0`
- Node.js: `nvm use 23`

Only if the target version is not installed at all, ask the user for permission before installing. Do NOT install runtimes without explicit user confirmation.
Suggest the appropriate version manager:

- Java: `brew install --cask corretto23` (macOS), `sudo yum install java-23-amazon-corretto-devel` (RHEL/AL2), or `sudo apt install java-23-amazon-corretto-jdk` (Debian/Ubuntu)
- Python: `pyenv install 3.15.0 && pyenv shell 3.15.0`, or `brew install python@3.15`
- Node.js: `nvm install 23 && nvm use 23`

The active runtime must match the transformation's target version so that builds
and tests run correctly. Do NOT proceed with the transformation until the correct
version is active.
