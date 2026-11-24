# shellcheck shell=bash
#
# The vibes commit gate: refuses a commit unless the project's own checks
# pass on exactly what is being committed.
#
# A project opts in by providing an executable scripts/check that lints and
# runs the tests. Projects without one are left alone. A commit of
# documents only runs scripts/check --static, its checks without the tests,
# since a document can't break a test; a script that takes no arguments runs
# everything anyway. A commit that changes scripts/check, scripts/check-file
# or a breach in scripts/breaches/ also has bin/rules-bite apply each breach
# that proved a boundary rule, and is blocked if the rule no longer catches
# it.

# shellcheck source=hooks/lib/guides.sh
source "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")/guides.sh"

readonly GATE_CHECK_SCRIPT="scripts/check"
readonly GATE_OUTPUT_LINES=60
# Applies each breach that proved a boundary rule, and checks the rule
# still catches it.
GATE_RULES_BITE="$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")"
GATE_RULES_BITE="${GATE_RULES_BITE%/hooks/lib}/bin/rules-bite"
readonly GATE_RULES_BITE
# The tag /vibes:debug puts on its temporary debug logs, such as
# vibes-debug-month-end, so none reaches a commit.
readonly GATE_DEBUG_TAG_RE='vibes-debug-[a-z0-9]'
readonly GATE_DEBUG_LINES=20

gate::err() {
  printf 'vibes commit gate: %s\n' "$*" >&2
}

# Returns 0 when every staged change is to a document outside the tests, so
# the tests needn't run. Test data, such as a fixture in Markdown, isn't a
# document.
gate::docs_only() {
  local path any=""
  while IFS= read -r -d '' path; do
    any=1
    case "/${path}" in
      */test/* | */tests/* | */testdata/* | */fixtures/* | */__tests__/*)
        return 1
        ;;
      *.md | *.markdown | *.mdx | *.rst | *.adoc | *.asciidoc | *.org) ;;
      *) return 1 ;;
    esac
  done < <(git diff --cached --name-only -z)
  [[ -n "${any}" ]]
}

# Returns 0 when scripts/check covers every guide the staged files need, as
# its "# Guides:" line says, and every staged file is either covered by a
# guide or listed on a "# No guide:" line. Otherwise explains, and returns 1.
gate::check_guides() {
  local declared unguided guide path entries entry
  local missing="" unknown="" invalid=""
  declared="$(guides::declared "${GATE_CHECK_SCRIPT}" 'Guides')"
  unguided="$(guides::declared "${GATE_CHECK_SCRIPT}" 'No guide')"

  if [[ -z "${declared}" ]]; then
    gate::err "${GATE_CHECK_SCRIPT} has no \"# Guides:\" line naming the"
    gate::err "guides it checks, such as:"
    gate::err "  # Guides: languages/BASH languages/Python tools/Docker"
    gate::err "To list the guides the project needs, run:"
    gate::err "  git ls-files | ${GUIDES_ROOT%/guides}/bin/guides-for"
    return 1
  fi
  while IFS= read -r guide; do
    guides::exists "${guide}" || invalid+="  ${guide}"$'\n'
  done <<<"${declared}"

  while IFS= read -r -d '' path; do
    guides::matches_any "${path}" "${unguided}" && continue
    entries="$(guides::for_file "${path}")"
    if [[ -z "${entries}" ]]; then
      unknown+="  ${path}"$'\n'
      continue
    fi
    while IFS= read -r entry; do
      if [[ "${entry}" != "-" ]] \
        && ! guides::covered "${entry}" "${declared}" \
        && [[ "${missing}" != *"  ${entry}, "* ]]; then
        missing+="  ${entry}, needed by ${path}"$'\n'
      fi
    done <<<"${entries}"
  done < <(git diff --cached --name-only --diff-filter=ACMR -z)

  [[ -z "${invalid}${missing}${unknown}" ]] && return 0
  if [[ -n "${invalid}" ]]; then
    gate::err "the \"# Guides:\" line in ${GATE_CHECK_SCRIPT} names guides"
    gate::err "that don't exist:"
    printf '%s' "${invalid}" >&2
  fi
  if [[ -n "${missing}" ]]; then
    gate::err "${GATE_CHECK_SCRIPT} doesn't check every guide this commit"
    gate::err "needs (\"a|b\" means either will do):"
    printf '%s' "${missing}" >&2
    gate::err "Read each guide's coding-style.md, idioms.md and tools.md in"
    gate::err "${GUIDES_ROOT}, follow them, add the checks from tools.md"
    gate::err "to ${GATE_CHECK_SCRIPT}, and add the guide to its \"# Guides:\""
    gate::err "line."
  fi
  if [[ -n "${unknown}" ]]; then
    gate::err "no vibes guide covers these files:"
    printf '%s' "${unknown}" >&2
    gate::err "Tell the user, then list a pattern for them, such as *.ipynb,"
    gate::err "on a \"# No guide:\" line in ${GATE_CHECK_SCRIPT}."
  fi
  return 1
}

# Returns 0 when no staged line adds a /vibes:debug run's debug tag.
# Otherwise lists the lines, and returns 1.
gate::check_debug_tags() {
  local line path="" found="" count=0
  while IFS= read -r line; do
    case "${line}" in
      '+++ b/'*) path="${line#+++ b/}" ;;
      '+++ '*) path="" ;;
      +*)
        [[ "${line}" =~ ${GATE_DEBUG_TAG_RE} ]] || continue
        ((count += 1))
        ((count <= GATE_DEBUG_LINES)) \
          && found+="  ${path}: ${line:1:100}"$'\n'
        ;;
      *) ;;
    esac
  done < <(git diff --cached -U0 --no-color --no-ext-diff)
  ((count == 0)) && return 0
  gate::err "${count} staged lines still carry a /vibes:debug run's debug tag:"
  printf '%s' "${found}" >&2
  gate::err "Remove the debug logging, then commit again."
  return 1
}

# Runs the gate in the repository containing the current directory. Returns
# 0 when the commit may go ahead, and 1 when it must be blocked.
# Returns 1 when a commit changes the checks or a breach, and a boundary
# rule no longer fails on the breach that proved it.
gate::check_breaches() {
  local output
  if git diff --cached --quiet -- "${GATE_CHECK_SCRIPT}" \
    scripts/check-file scripts/breaches; then
    return 0
  fi
  [[ -x "${GATE_RULES_BITE}" ]] || return 0
  if ! output="$("${GATE_RULES_BITE}" --staged 2>&1)"; then
    gate::err "a boundary rule no longer fails on the breach that proved it,"
    gate::err "so the commit is blocked. Fix the rule, or the breach in"
    gate::err "scripts/breaches/, then commit again. Each run's output is in"
    gate::err ".vibes/rules-bite/."
    printf '%s\n' "${output}" | tail -n "${GATE_OUTPUT_LINES}" >&2
    return 1
  fi
  return 0
}

gate::run() {
  local root
  if ! root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    return 0
  fi
  cd -- "${root}" || return 1

  if [[ ! -x "${GATE_CHECK_SCRIPT}" ]]; then
    return 0
  fi

  local branch
  branch="$(git symbolic-ref --quiet --short HEAD || true)"
  if [[ "${branch}" == spike/* ]]; then
    return 0
  fi

  if ! git diff --quiet; then
    gate::err "unstaged changes would not be checked. Stash them first:"
    gate::err "  git stash push --keep-index --include-untracked"
    return 1
  fi

  if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    gate::err "untracked files would not be checked. Stage or stash them:"
    gate::err "  git stash push --keep-index --include-untracked"
    return 1
  fi

  if ! gate::check_guides; then
    return 1
  fi

  if ! gate::check_debug_tags; then
    return 1
  fi

  local output
  local -a mode=()
  if gate::docs_only; then
    mode=(--static)
  fi
  if ! output="$("./${GATE_CHECK_SCRIPT}" ${mode[@]+"${mode[@]}"} 2>&1)"; then
    gate::err "${GATE_CHECK_SCRIPT} failed, so the commit is blocked."
    gate::err "Fix the problems below, then commit again."
    printf '%s\n' "${output}" | tail -n "${GATE_OUTPUT_LINES}" >&2
    return 1
  fi

  if ! gate::check_breaches; then
    return 1
  fi

  return 0
}
