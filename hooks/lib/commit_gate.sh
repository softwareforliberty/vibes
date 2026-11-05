# shellcheck shell=bash
#
# The vibes commit gate: refuses a commit unless the project's own checks
# pass on exactly what is being committed.
#
# A project opts in by providing an executable scripts/check that lints and
# runs the full test suite. Projects without one are left alone.

readonly GATE_CHECK_SCRIPT="scripts/check"
readonly GATE_OUTPUT_LINES=60

gate::err() {
  printf 'vibes commit gate: %s\n' "$*" >&2
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

  local output
  if ! output="$("./${GATE_CHECK_SCRIPT}" 2>&1)"; then
    gate::err "${GATE_CHECK_SCRIPT} failed, so the commit is blocked."
    gate::err "Fix the problems below, then commit again."
    printf '%s\n' "${output}" | tail -n "${GATE_OUTPUT_LINES}" >&2
    return 1
  fi

  return 0
}
