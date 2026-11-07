# shellcheck shell=bash
#
# The vibes commit gate: refuses a commit unless the project's own checks
# pass on exactly what is being committed.
#
# A project opts in by providing an executable scripts/check that lints and
# runs the full test suite. Projects without one are left alone.

# shellcheck source=hooks/lib/guides.sh
source "$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")/guides.sh"

readonly GATE_CHECK_SCRIPT="scripts/check"
readonly GATE_OUTPUT_LINES=60

gate::err() {
  printf 'vibes commit gate: %s\n' "$*" >&2
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

# Runs the gate in the repository containing the current directory. Returns
# 0 when the commit may go ahead, and 1 when it must be blocked.
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

  local output
  if ! output="$("./${GATE_CHECK_SCRIPT}" 2>&1)"; then
    gate::err "${GATE_CHECK_SCRIPT} failed, so the commit is blocked."
    gate::err "Fix the problems below, then commit again."
    printf '%s\n' "${output}" | tail -n "${GATE_OUTPUT_LINES}" >&2
    return 1
  fi

  return 0
}
