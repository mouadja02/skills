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

  Use single-quote or double-quote the pattern so your shell does not
  expand it before install.sh sees it.

OPTIONS
  -d, --dest <path>         REQUIRED. Where to install.
                            * single skill      -> <dest> IS the skill folder
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
  SKILLS_REPO     Override the source repo (default: mouadja02/skills).
  SKILLS_BRANCH   Override the default branch (default: main).

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
require_cmd tar
require_cmd awk

# --- Resolve the selector -----------------------------------------------------

# Outputs:
#   MODE          = single | category | glob
#   SELECTED_IPS  = newline-separated list of install_paths
#   CAT           = category name (only set when MODE=category)
resolve_selector() {
  local sel="$1" tsv="$2"
  MODE=""
  SELECTED_IPS=""
  CAT=""

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

# Compute the final on-disk destination for one install_path.
target_for() {
  local ip="$1"
  case "$MODE" in
    single)
      printf '%s' "$DEST"
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
  esac
}

# --- Main flow ----------------------------------------------------------------

tmpdir="$(mktemp -d 2>/dev/null || mktemp -d -t skills)"
trap 'rm -rf "$tmpdir"' EXIT

manifest_tsv="$tmpdir/manifest.tsv"
echo "==> Fetching manifest from ${REPO}@${BRANCH}" >&2
fetch_manifest_tsv "$manifest_tsv"

resolve_selector "$SELECTOR" "$manifest_tsv"

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

# Download tarball once and extract everything to temp.
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
