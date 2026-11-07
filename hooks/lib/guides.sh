# shellcheck shell=bash
#
# Finds the guides that files need, from guides/map.tsv, and the guides a
# project's commit gate covers, from the "# Guides:" and "# No guide:" lines
# in its scripts/check.

# Sourcing it twice would redefine its read-only variables.
[[ -n "${GUIDES_ROOT:-}" ]] && return 0

GUIDES_ROOT="$(dirname -- "$(dirname -- "$(dirname -- \
  "$(realpath -- "${BASH_SOURCE[0]}")")")")/guides"
readonly GUIDES_ROOT
readonly GUIDES_MAP="${GUIDES_ROOT}/map.tsv"

# Prints the interpreter a script's first line names, such as python3 for
# "#!/usr/bin/env -S python3 -u", or nothing.
guides::interpreter() {
  local first="" word
  local -a words
  [[ -f "$1" ]] || return 0
  IFS= read -r first <"$1" || true
  [[ "${first}" == '#!'* ]] || return 0
  read -r -a words <<<"${first#'#!'}"
  # Bash 3.2 treats an empty array as unset, which set -u rejects.
  ((${#words[@]} > 0)) || return 0
  for word in "${words[@]}"; do
    case "${word##*/}" in
      env | -*) ;;
      *)
        printf '%s\n' "${word##*/}"
        return 0
        ;;
    esac
  done
}

# Returns 0 when a path matches a pattern from the map: a pattern with a /
# matches the whole path, and one without matches the file name.
guides::matches() {
  local path="$1" pattern="$2"
  [[ "${pattern}" == */* ]] || path="${path##*/}"
  # The pattern is a glob, so it's deliberately unquoted.
  # shellcheck disable=SC2053
  [[ "${path}" == ${pattern} ]]
}

# Prints the guides one file needs, one entry per line, where an entry such
# as "languages/C|languages/C++" means either will do. Prints "-" when the
# file is known to need none, and nothing when no line of the map matches.
# The script's first line is read from the second argument when given, such
# as for a file that's about to be written.
guides::for_file() {
  local path="$1" first_line="${2:-$1}" guide patterns pattern found=""
  local -a list
  while IFS=$'\t' read -r guide patterns; do
    [[ -z "${guide}" || "${guide}" == '#'* ]] && continue
    read -r -a list <<<"${patterns}"
    for pattern in "${list[@]}"; do
      [[ "${pattern}" == '#!'* ]] && continue
      if guides::matches "${path}" "${pattern}"; then
        printf '%s\n' "${guide}"
        found="yes"
        break
      fi
    done
  done <"${GUIDES_MAP}"
  [[ -n "${found}" ]] && return 0

  local interpreter
  interpreter="$(guides::interpreter "${first_line}")"
  [[ -n "${interpreter}" ]] || return 0
  while IFS=$'\t' read -r guide patterns; do
    [[ -z "${guide}" || "${guide}" == '#'* ]] && continue
    read -r -a list <<<"${patterns}"
    for pattern in "${list[@]}"; do
      [[ "${pattern}" == '#!'* ]] || continue
      if guides::matches "${interpreter}" "${pattern#'#!'}"; then
        printf '%s\n' "${guide}"
        return 0
      fi
    done
  done <"${GUIDES_MAP}"
}

# Prints the words on every "# <label>:" line of a scripts/check, one per
# line.
guides::declared() {
  local check="$1" label="$2" line word
  local -a words
  [[ -f "${check}" ]] || return 0
  while IFS= read -r line; do
    [[ "${line}" == "# ${label}:"* ]] || continue
    read -r -a words <<<"${line#"# ${label}:"}"
    ((${#words[@]} > 0)) || continue
    for word in "${words[@]}"; do
      printf '%s\n' "${word}"
    done
  done <"${check}"
}

# Returns 0 when one of the alternatives in an entry such as
# "languages/C|languages/C++" is in the newline-separated list of guides.
guides::covered() {
  local entry="$1" covered="$2" choice
  local -a choices
  IFS='|' read -r -a choices <<<"${entry}"
  for choice in "${choices[@]}"; do
    [[ $'\n'"${covered}"$'\n' == *$'\n'"${choice}"$'\n'* ]] && return 0
  done
  return 1
}

# Returns 0 when a path matches one of the newline-separated patterns.
guides::matches_any() {
  local path="$1" patterns="$2" pattern
  while IFS= read -r pattern; do
    [[ -n "${pattern}" ]] && guides::matches "${path}" "${pattern}" && return 0
  done <<<"${patterns}"
  return 1
}

# Returns 0 when a guide directory, such as languages/Python, exists.
guides::exists() {
  [[ "$1" != *..* && -f "${GUIDES_ROOT}/$1/coding-style.md" ]]
}
