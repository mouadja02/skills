#!/usr/bin/env bash
# Install one skill, a whole category, or a pattern of skills from
# github.com/mouadja02/skills without cloning the repo.
#
#   install.sh <selector> -d <destination> [options]
#   install.sh --list | --list-categories | --help
#
# A selector is one of:
#   * an exact install path        engineering-craft/test-driven-development
#   * a category name              engineering-craft
#   * a glob pattern (quoted)      "*bmad*"  "ai-agents/bmad*"  "*-advisor"
#
# See `install.sh --help` for full usage.

set -euo pipefail

REPO="${SKILLS_REPO:-mouadja02/skills}"
BRANCH="${SKILLS_BRANCH:-main}"
RAW_BASE="${SKILLS_RAW_BASE:-https://raw.githubusercontent.com/${REPO}}"
TARBALL_BASE="${SKILLS_TARBALL_BASE:-https://codeload.github.com/${REPO}/tar.gz/refs/heads}"
PAGES_BASE="${SKILLS_PAGES_BASE:-https://${REPO%%/*}.github.io/${REPO#*/}}"
DOWNLOAD_BASE="${SKILLS_DOWNLOAD_BASE:-}"

SELECTOR=""
DEST=""
FORCE=0
LIST=0
LIST_CATEGORIES=0
HELP=0
FLAT=0
DRY_RUN=0

usage() {
  cat <<'EOF'
install.sh — fetch one or many agent skills from mouadja02/skills.

USAGE
  install.sh <selector> -d <destination> [options]
  install.sh --all -d <destination> [options]
  install.sh --list
  install.sh --list-categories
  install.sh --help | -h

SELECTORS
  An exact install path  install one skill
      engineering-craft/test-driven-development
      ai-agents/bmm-skills/1-analysis/bmad-prfaq

  A category name        install every skill in that category
      engineering-craft        (29 skills)
      caveman                  (6 skills)
      business-and-strategy    (60 skills)

  A glob pattern         install every install_path that matches
      "*bmad*"                 every skill whose path contains "bmad"
      "ai-agents/*"            every direct child of ai-agents/
      "*-advisor"              every install_path ending in "-advisor"

  All skills            install every skill, preserving category paths
      --all

  Use single-quote or double-quote the pattern so your shell does not
  expand it before install.sh sees it.

OPTIONS
  -d, --dest <path>         REQUIRED. Where to install.
                            * single skill      -> <dest> can be the skill
                                                   folder or an existing parent
                                                   directory
                            * category / glob   -> <dest> is a parent folder

  --flat                    Glob mode only. Place each matched skill at
                            <dest>/<name>/ instead of preserving the full
                            install path. Errors on name collisions.

  --branch <branch>         Branch to install from (default: main).
  --force                   Overwrite existing destinations.
  --dry-run                 Resolve the selector and print the install plan
                            without downloading or writing anything.
  --list                    List every available skill, grouped by category.
  --list-categories         List every category with its skill count.
  -h, --help                Show this help and exit.

ENVIRONMENT
  SKILLS_REPO        Override the source repo (default: mouadja02/skills).
  SKILLS_BRANCH      Override the default branch (default: main).
  SKILLS_PAGES_BASE  Override the Pages base URL used for ZIP metadata.
  SKILLS_DOWNLOAD_BASE
                     Override the public ZIP base URL, for example an S3
                     or CloudFront URL.

EXAMPLES
  # one skill
  install.sh engineering-craft/test-driven-development \
      -d ~/.claude/skills/test-driven-development

  # every skill in a category
  install.sh engineering-craft -d ~/.claude/skills/engineering-craft

  # every BMad sub-skill, flattened by name
  install.sh "*bmad*" -d ~/.claude/skills/bmad --flat

  # every C-suite advisor, preserving install paths
  install.sh "*-advisor" -d ~/.claude/skills/exec

  # all skills, preserving category paths
  install.sh --all -d ~/.claude/skills

  # see what would happen
  install.sh "ai-agents/*" -d ~/.claude/skills/ai --dry-run

  # browse what's available
  install.sh --list-categories
  install.sh --list | grep marketing
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

# --- Argument parsing ---------------------------------------------------------

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)            HELP=1; shift ;;
    --all)                SELECTOR="all"; shift ;;
    --list)               LIST=1; shift ;;
    --list-categories)    LIST_CATEGORIES=1; shift ;;
    -d|--dest)
      [ $# -ge 2 ] || die "$1 requires an argument"
      DEST="$2"; shift 2 ;;
    --branch)
      [ $# -ge 2 ] || die "$1 requires an argument"
      BRANCH="$2"; shift 2 ;;
    --force)              FORCE=1; shift ;;
    --flat)               FLAT=1; shift ;;
    --dry-run)            DRY_RUN=1; shift ;;
    -*)                   die "unknown option: $1  (try --help)" ;;
    *)
      if [ -z "$SELECTOR" ]; then
        SELECTOR="$1"
      else
        die "unexpected positional argument: $1"
      fi
      shift ;;
  esac
done

# --- Help / list paths --------------------------------------------------------

fetch_manifest_tsv() {
  local tsv="$1"
  curl -fsSL "${RAW_BASE}/${BRANCH}/docs/manifest.tsv" -o "$tsv" \
    || die "failed to fetch docs/manifest.tsv from ${RAW_BASE}/${BRANCH}/docs/manifest.tsv"
}

if [ "$HELP" -eq 1 ]; then
  usage
  exit 0
fi

if [ "$LIST" -eq 1 ] || [ "$LIST_CATEGORIES" -eq 1 ]; then
  require_cmd curl
  require_cmd awk
  tmpdir="$(mktemp -d 2>/dev/null || mktemp -d -t skills)"
  trap 'rm -rf "$tmpdir"' EXIT
  fetch_manifest_tsv "$tmpdir/manifest.tsv"

  if [ "$LIST_CATEGORIES" -eq 1 ]; then
    awk -F'\t' 'NR>1 {c[$2]++} END {
      for (k in c) printf "%-30s %d\n", k, c[k]
    }' "$tmpdir/manifest.tsv" | sort
    exit 0
  fi

  awk -F'\t' 'NR>1 {
    printf "%-26s  %s\n", $2, $1
  }' "$tmpdir/manifest.tsv" | sort
  exit 0
fi

# --- Validate install args ----------------------------------------------------

[ -n "$SELECTOR" ] || { usage; echo; die "missing <selector>"; }
[ -n "$DEST" ] || { usage; echo; die "missing -d <destination>"; }
case "$SELECTOR" in
  /*|*..*) die "invalid selector: $SELECTOR" ;;
esac

require_cmd curl
require_cmd awk

# --- Resolve the selector -----------------------------------------------------

# Outputs:
#   MODE          = single | category | glob | all
#   SELECTED_IPS  = newline-separated list of install_paths
#   CAT           = category name (only set when MODE=category)
resolve_selector() {
  local sel="$1" tsv="$2"
  MODE=""
  SELECTED_IPS=""
  CAT=""

  if [ "$sel" = "all" ]; then
    MODE="all"
    SELECTED_IPS="$(awk -F'\t' 'NR>1 {print $1}' "$tsv")"
    return
  fi

  case "$sel" in
    *\**|*\?*)
      MODE="glob"
      SELECTED_IPS="$(
        awk -F'\t' -v pat="$sel" '
          NR > 1 {
            ip = $1
            # Convert glob -> ERE: * -> .* , ? -> . , escape regex metachars
            r = pat
            gsub(/[][().+^$|\\{}]/, "\\\\&", r)
            gsub(/\*/, ".*", r)
            gsub(/\?/, ".",  r)
            if (ip ~ ("^" r "$")) print ip
          }
        ' "$tsv"
      )"
      [ -n "$SELECTED_IPS" ] || die "no install_path matches pattern: $sel  (try --list)"
      return
      ;;
  esac

  # Exact install_path?
  if awk -F'\t' -v p="$sel" 'NR>1 && $1==p {f=1; exit} END {exit !f}' "$tsv"; then
    MODE="single"
    SELECTED_IPS="$sel"
    return
  fi

  # Exact category?
  local cat_ips
  cat_ips="$(awk -F'\t' -v c="$sel" 'NR>1 && $2==c {print $1}' "$tsv")"
  if [ -n "$cat_ips" ]; then
    MODE="category"
    CAT="$sel"
    SELECTED_IPS="$cat_ips"
    return
  fi

  die "no skill, category, or pattern matches: $sel  (try --list or --list-categories)"
}

prune_nested_selection() {
  if [ "$MODE" = "single" ] || { [ "$MODE" = "glob" ] && [ "$FLAT" -eq 1 ]; }; then
    return
  fi

  SELECTED_IPS="$(
    printf '%s\n' "$SELECTED_IPS" |
      awk 'NF' |
      sort |
      awk '
        {
          for (i = 1; i <= n; i++) {
            if ($0 == roots[i] || index($0, roots[i] "/") == 1) next
          }
          roots[++n] = $0
          print
        }
      '
  )"
}

# Compute the final on-disk destination for one install_path.
target_for() {
  local ip="$1"
  case "$MODE" in
    single)
      local name dest_base
      name="$(basename "$ip")"
      dest_base="$(basename "$DEST")"
      if [ -d "$DEST" ] && [ ! -f "$DEST/SKILL.md" ] && [ "$dest_base" != "$name" ]; then
        printf '%s/%s' "$DEST" "$name"
      else
        printf '%s' "$DEST"
      fi
      ;;
    category)
      printf '%s/%s' "$DEST" "${ip#${CAT}/}"
      ;;
    glob)
      if [ "$FLAT" -eq 1 ]; then
        printf '%s/%s' "$DEST" "$(basename "$ip")"
      else
        printf '%s/%s' "$DEST" "$ip"
      fi
      ;;
    all)
      printf '%s/%s' "$DEST" "$ip"
      ;;
  esac
}

can_use_scoped_zip() {
  [ "$BRANCH" = "main" ] || return 1
  [ "$MODE" = "single" ] || [ "$MODE" = "category" ] || [ "$MODE" = "glob" ] || [ "$MODE" = "all" ]
  command -v unzip >/dev/null 2>&1 || return 1
}

resolve_zip_base() {
  if [ -n "$DOWNLOAD_BASE" ]; then
    ZIP_BASE="${DOWNLOAD_BASE%/}"
    return
  fi

  local summary base
  summary="$(curl -fsSL "${PAGES_BASE%/}/zips/_summary.json" 2>/dev/null || true)"
  base="$(printf '%s\n' "$summary" | sed -n 's/.*"public_base_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
  if [ -n "$base" ]; then
    ZIP_BASE="${base%/}"
  else
    ZIP_BASE="${PAGES_BASE%/}"
  fi
}

hash_file() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 -r "$file" | awk '{print $1}'
  else
    return 1
  fi
}

verify_zip() {
  local url="$1" file="$2" sidecar expected actual
  sidecar="$file.sha256"
  if ! curl -fsSL "${url}.sha256" -o "$sidecar" 2>/dev/null; then
    echo "==> No SHA256 sidecar for $(basename "$file"); skipping checksum verification" >&2
    return 0
  fi

  expected="$(awk '{print $1; exit}' "$sidecar")"
  actual="$(hash_file "$file" || true)"
  [ -n "$actual" ] || {
    echo "==> No local SHA256 tool found; skipping checksum verification" >&2
    return 0
  }
  [ "$expected" = "$actual" ] || die "checksum mismatch for $(basename "$file")"
}

download_zip() {
  local relative="$1" out="$2" url
  url="${ZIP_BASE%/}/$relative"
  curl -fsSL "$url" -o "$out" || return 1
  verify_zip "$url" "$out"
}

install_from_zip_root() {
  local zip="$1" root="$2" source_root="$3"
  local zip_extract="$root/extract"

  mkdir -p "$zip_extract"
  unzip -q "$zip" -d "$zip_extract"

  while IFS=$'\t' read -r ip target; do
    case "$MODE" in
      single)
        src="$zip_extract/$(basename "$ip")"
        ;;
      category)
        src="$zip_extract/$source_root/${ip#${CAT}/}"
        ;;
      all)
        src="$zip_extract/skills/$ip"
        ;;
      *)
        die "ZIP install is only supported for single, category, or all mode"
        ;;
    esac

    [ -d "$src" ] || die "missing in ZIP: $ip"
    if [ -e "$target" ] && [ "$FORCE" -eq 1 ]; then
      rm -rf -- "$target"
    fi
    mkdir -p -- "$(dirname "$target")"
    cp -r "$src" "$target"
    echo "  - $ip -> $target" >&2
  done < "$plan_file"
}

install_from_skill_zips() {
  local root="$1" zip_plan="$root/zip-plan.txt" n=0
  mkdir -p "$root"
  : > "$zip_plan"

  while IFS=$'\t' read -r ip target; do
    n=$((n + 1))
    local zip="$root/skill-$n.zip" zip_extract="$root/skill-$n"
    download_zip "zips/skill/${ip}.zip" "$zip" || return 1
    mkdir -p "$zip_extract"
    unzip -q "$zip" -d "$zip_extract"
    local src="$zip_extract/$(basename "$ip")"
    [ -d "$src" ] || die "missing in ZIP: $ip"
    printf '%s\t%s\t%s\n' "$ip" "$src" "$target" >> "$zip_plan"
  done < "$plan_file"

  while IFS=$'\t' read -r ip src target; do
    if [ -e "$target" ] && [ "$FORCE" -eq 1 ]; then
      rm -rf -- "$target"
    fi
    mkdir -p -- "$(dirname "$target")"
    cp -r "$src" "$target"
    echo "  - $ip -> $target" >&2
  done < "$zip_plan"
}

# --- Main flow ----------------------------------------------------------------

tmpdir="$(mktemp -d 2>/dev/null || mktemp -d -t skills)"
trap 'rm -rf "$tmpdir"' EXIT

manifest_tsv="$tmpdir/manifest.tsv"
echo "==> Fetching manifest from ${REPO}@${BRANCH}" >&2
fetch_manifest_tsv "$manifest_tsv"

resolve_selector "$SELECTOR" "$manifest_tsv"
prune_nested_selection

count="$(printf '%s\n' "$SELECTED_IPS" | awk 'NF' | wc -l | tr -d ' ')"
echo "==> Selector matched $count skill(s) in mode '$MODE'" >&2

# Validate dests, detect collisions.
plan_file="$tmpdir/plan.txt"
seen_file="$tmpdir/seen.txt"
: > "$plan_file"
: > "$seen_file"

while IFS= read -r ip; do
  [ -z "$ip" ] && continue
  target="$(target_for "$ip")"
  if grep -Fxq -- "$target" "$seen_file"; then
    die "destination collision: '$target' resolves from two skills (use without --flat, or narrow the selector)"
  fi
  echo "$target" >> "$seen_file"

  if [ -e "$target" ] && [ "$FORCE" -ne 1 ]; then
    die "destination already exists: $target  (use --force to overwrite)"
  fi
  printf '%s\t%s\n' "$ip" "$target" >> "$plan_file"
done <<< "$SELECTED_IPS"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "==> Dry run: would install:" >&2
  awk -F'\t' '{ printf "  %-50s -> %s\n", $1, $2 }' "$plan_file"
  exit 0
fi

# Prefer the prebuilt ZIP artifacts for scoped installs. This avoids
# downloading and extracting the entire repository for one skill or category.
if can_use_scoped_zip; then
  resolve_zip_base
  zip="$tmpdir/scoped.zip"
  case "$MODE" in
    single)
      zip_path="zips/skill/${SELECTOR}.zip"
      zip_root="$(basename "$SELECTOR")"
      ;;
    category)
      zip_path="zips/category/${CAT}.zip"
      zip_root="$CAT"
      ;;
    all)
      zip_path="zips/all.zip"
      zip_root="skills"
      ;;
    glob)
      echo "==> Downloading $count per-skill ZIP(s) from ${ZIP_BASE}" >&2
      if install_from_skill_zips "$tmpdir/scoped-skills"; then
        echo "==> Done. Installed $count skill(s) under $DEST" >&2
        exit 0
      fi
      echo "==> Scoped ZIPs unavailable; falling back to ${REPO}@${BRANCH} tarball" >&2
      ;;
  esac

  if [ "$MODE" != "glob" ]; then
    echo "==> Downloading scoped ZIP from ${ZIP_BASE}/${zip_path}" >&2
  fi
  if [ "$MODE" != "glob" ] && download_zip "$zip_path" "$zip"; then
    echo "==> Installing $count skill(s) from scoped ZIP" >&2
    install_from_zip_root "$zip" "$tmpdir/scoped" "$zip_root"
    echo "==> Done. Installed $count skill(s) under $DEST" >&2
    exit 0
  fi

  if [ "$MODE" != "glob" ]; then
    echo "==> Scoped ZIP unavailable; falling back to ${REPO}@${BRANCH} tarball" >&2
  fi
fi

# Download tarball once and extract everything to temp.
require_cmd tar
echo "==> Downloading ${REPO}@${BRANCH} tarball" >&2
tarball="$tmpdir/repo.tar.gz"
curl -fsSL "${TARBALL_BASE}/${BRANCH}" -o "$tarball" \
  || die "failed to download tarball"

extract_dir="$tmpdir/extract"
mkdir -p "$extract_dir"
tar -xzf "$tarball" -C "$extract_dir"
topdir="$extract_dir/$(basename "$REPO")-${BRANCH}"
[ -d "$topdir/skills" ] || die "unexpected tarball layout: $topdir/skills not found"

# Copy each selected skill into its target.
echo "==> Installing $count skill(s)" >&2
while IFS=$'\t' read -r ip target; do
  src="$topdir/skills/$ip"
  [ -d "$src" ] || die "missing in tarball: skills/$ip"
  if [ -e "$target" ] && [ "$FORCE" -eq 1 ]; then
    rm -rf -- "$target"
  fi
  mkdir -p -- "$(dirname "$target")"
  cp -r "$src" "$target"
  echo "  - $ip -> $target" >&2
done < "$plan_file"

echo "==> Done. Installed $count skill(s) under $DEST" >&2
