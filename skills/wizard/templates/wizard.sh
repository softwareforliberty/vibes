#!/usr/bin/env bash
#
# <Title>: walks you through <the procedure>, one stage at a time. It opens
# each page, says what to click and copy, and saves what you paste back
# where it belongs. Secrets are typed into hidden prompts, never shown.
#
# Run it from the repository root, in a terminal:
#
#   bash <path to this script>
#
# Stop at any time with Ctrl-C, and run it again later: it keeps what it
# has saved. Written by vibes on <date>; each stage names the documentation
# its steps came from.
#
# Everything above the STAGES line is the vibes wizard library, the same in
# every wizard. It runs on Bash 3.2, the version macOS ships, and later.

set -euo pipefail

# ── The vibes wizard library ──────────────────────────────────────────────

# Where values are saved. Set WIZARD_ENV_FILE to use another file.
WIZARD_ENV_FILE="${WIZARD_ENV_FILE:-.env}"
# The escaped form of a single quote inside a single-quoted .env value.
readonly _WIZARD_QUOTE="'\\''"

_wizard_bold=""
_wizard_dim=""
_wizard_reset=""
_wizard_accent=""
_wizard_good=""
_wizard_alert=""
_wizard_index=0
_wizard_checked_ignore=""
_wizard_wrote=()
_wizard_set=()
_wizard_left=()

# Turns colours on when the output is a terminal that has them.
wizard::_colours() {
  [[ -t 1 ]] && command -v tput >/dev/null 2>&1 || return 0
  (($(tput colors 2>/dev/null || echo 0) >= 8)) || return 0
  _wizard_bold="$(tput bold)"
  _wizard_dim="$(tput dim)"
  _wizard_reset="$(tput sgr0)"
  _wizard_accent="$(tput setaf 4)"
  _wizard_good="$(tput setaf 2)"
  _wizard_alert="$(tput setaf 3)"
}

# Clears the screen, so only the current stage shows, in a terminal only.
wizard::_clear() {
  [[ -t 1 ]] || return 0
  printf '\033[2J\033[3J\033[H'
}

# Exits when a name can't be a .env key or a GitHub secret's name.
wizard::_check_name() {
  if [[ ! "$1" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    printf 'wizard: %s is not a valid name\n' "$1" >&2
    exit 2
  fi
}

# Prints an instruction.
wizard::say() { printf '  %s\n' "$1"; }

# Prints one thing to do, such as a click.
wizard::step() {
  printf '  %s•%s %s\n' "${_wizard_accent}" "${_wizard_reset}" "$1"
}

# Prints a quiet aside.
wizard::note() {
  printf '  %s%s%s\n' "${_wizard_dim}" "$1" "${_wizard_reset}"
}

# Prints a warning.
wizard::warn() {
  printf '  %s! %s%s\n' "${_wizard_alert}" "$1" "${_wizard_reset}"
}

# Prints where a stage's steps came from, and when they were checked.
wizard::docs() {
  wizard::note "Steps from ${1}, checked ${2}. If the page has changed,"
  wizard::note "follow the page."
}

# Waits for Enter.
wizard::pause() {
  printf '  %s%s%s ' "${_wizard_dim}" "${1:-Press Enter when done.}" \
    "${_wizard_reset}"
  read -r _ || true
}

# Asks a yes-or-no question, no by default. Succeeds on yes.
wizard::confirm() {
  local reply=""
  printf '  %s? %s [y/N]%s ' "${_wizard_alert}" "$1" "${_wizard_reset}"
  read -r reply || true
  [[ "${reply}" == [Yy]* ]]
}

# Opens a page in the browser, or says to open it when it can't. Set
# WIZARD_NO_BROWSER to only print it.
wizard::open_url() {
  local url="$1" opener=""
  printf '  %s↗ Opening%s %s\n' "${_wizard_good}" "${_wizard_reset}" "${url}"
  if [[ -z "${WIZARD_NO_BROWSER:-}" ]]; then
    if [[ "$(uname -s)" == Darwin ]]; then
      opener=open
    elif command -v wslview >/dev/null 2>&1; then
      opener=wslview
    elif command -v xdg-open >/dev/null 2>&1; then
      opener=xdg-open
    fi
  fi
  if [[ -z "${opener}" ]] || ! "${opener}" "${url}" >/dev/null 2>&1; then
    wizard::warn "Open it in your browser: ${url}"
  fi
}

# Prints the value saved for a key in the env file, and fails when there's
# none, or it's quoted in a way it can't safely read.
wizard::saved() {
  local key="$1" line value quote="'"
  wizard::_check_name "${key}"
  [[ -f "${WIZARD_ENV_FILE}" ]] || return 1
  line="$(grep -E "^${key}=" "${WIZARD_ENV_FILE}" | tail -n 1)" || return 1
  value="${line#*=}"
  case "${value}" in
    \'*\')
      value="${value:1:${#value}-2}"
      value="${value//"${_WIZARD_QUOTE}"/${quote}}"
      ;;
    \"*\")
      value="${value:1:${#value}-2}"
      [[ "${value}" != *[\\\$\`\"]* ]] || return 1
      ;;
    *) ;;
  esac
  [[ -n "${value}" ]] || return 1
  printf '%s' "${value}"
}

# Reads an answer into the named variable, with the saved value as the
# default. Asks again while it's empty, and fails at the end of input.
wizard::_read() {
  local var="$1" prompt="$2" secret="$3" current reply=""
  wizard::_check_name "${var}"
  current="$(wizard::saved "${var}" || true)"
  while :; do
    printf '  %s%s%s ' "${_wizard_bold}" "${prompt}" "${_wizard_reset}"
    if [[ -n "${current}" && -n "${secret}" ]]; then
      printf '%s[Enter keeps the saved one]%s ' "${_wizard_dim}" \
        "${_wizard_reset}"
    elif [[ -n "${current}" ]]; then
      printf '%s[%s]%s ' "${_wizard_dim}" "${current}" "${_wizard_reset}"
    fi
    reply=""
    if [[ -n "${secret}" && -t 0 ]]; then
      IFS= read -r -s reply || [[ -n "${reply}" ]] || {
        printf '\n'
        return 1
      }
      printf '\n'
    elif [[ -t 0 ]]; then
      IFS= read -r -e reply || [[ -n "${reply}" ]] || return 1
    else
      IFS= read -r reply || [[ -n "${reply}" ]] || return 1
    fi
    [[ -n "${reply}" ]] || reply="${current}"
    [[ -z "${reply}" ]] || break
    wizard::warn "This can't be empty."
  done
  printf -v "${var}" '%s' "${reply}"
}

# Asks for a value you can see as you type.
wizard::ask() { wizard::_read "$1" "$2" ""; }

# Asks for a secret, hidden as you type.
wizard::ask_secret() { wizard::_read "$1" "$2" secret; }

# Saves KEY='value' in the env file, replacing any earlier line for it, and
# sets the variable. Creates the file readable only by you, keeps an
# existing file's permissions, and warns once if git doesn't ignore it.
wizard::write_env() {
  local key="$1" value="$2" tmp quote="'"
  wizard::_check_name "${key}"
  if [[ "${value}" == *$'\n'* ]]; then
    wizard::warn "${key} has a line break, which .env can't hold: not saved."
    return 1
  fi
  [[ -e "${WIZARD_ENV_FILE}" ]] || (umask 077 && : >"${WIZARD_ENV_FILE}")
  if [[ -z "${_wizard_checked_ignore}" ]]; then
    _wizard_checked_ignore=1
    if git rev-parse --git-dir >/dev/null 2>&1 \
      && ! git check-ignore -q "${WIZARD_ENV_FILE}"; then
      wizard::warn "git doesn't ignore ${WIZARD_ENV_FILE}: add it to"
      wizard::warn ".gitignore before you commit, or its secrets go too."
    fi
  fi
  tmp="$(mktemp)"
  grep -vE "^${key}=" "${WIZARD_ENV_FILE}" >"${tmp}" || true
  printf "%s='%s'\n" "${key}" "${value//${quote}/${_WIZARD_QUOTE}}" \
    >>"${tmp}"
  cat "${tmp}" >"${WIZARD_ENV_FILE}"
  rm -f "${tmp}"
  printf -v "${key}" '%s' "${value}"
  _wizard_wrote+=("${key}")
  printf '  %s✓ Saved%s %s in %s\n' "${_wizard_good}" "${_wizard_reset}" \
    "${key}" "${WIZARD_ENV_FILE}"
}

# Succeeds when gh is installed and logged in.
wizard::_gh_ready() {
  command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1
}

# Sets a GitHub Actions secret, passing the value on standard input so it
# never shows in a process list. Records it as left to do when it can't.
wizard::set_secret() {
  local name="$1" value="$2"
  wizard::_check_name "${name}"
  if wizard::_gh_ready \
    && printf '%s' "${value}" | gh secret set "${name}" >/dev/null 2>&1; then
    _wizard_set+=("secret ${name}")
    printf '  %s✓ Set%s the GitHub secret %s\n' "${_wizard_good}" \
      "${_wizard_reset}" "${name}"
    return 0
  fi
  _wizard_left+=("the GitHub secret ${name}: gh secret set ${name}")
  wizard::warn "Couldn't set the GitHub secret ${name}: gh isn't logged in."
}

# Sets a GitHub Actions variable, which isn't secret.
wizard::set_var() {
  local name="$1" value="$2"
  wizard::_check_name "${name}"
  if wizard::_gh_ready \
    && gh variable set "${name}" --body "${value}" >/dev/null 2>&1; then
    _wizard_set+=("variable ${name}")
    printf '  %s✓ Set%s the GitHub variable %s\n' "${_wizard_good}" \
      "${_wizard_reset}" "${name}"
    return 0
  fi
  _wizard_left+=("the GitHub variable ${name}: gh variable set ${name}")
  wizard::warn "Couldn't set the GitHub variable ${name}: gh isn't logged in."
}

# Records something you still have to do by hand, for the summary.
wizard::left() { _wizard_left+=("$1"); }

# Starts the wizard: its title, how many stages, and how it works.
wizard::begin() {
  wizard::_colours
  wizard::_clear
  printf '\n  %s%s%s%s\n' "${_wizard_bold}" "${_wizard_accent}" \
    "${WIZARD_TITLE}" "${_wizard_reset}"
  wizard::note "${WIZARD_STAGES} stages. You do the clicking; this saves what"
  wizard::note "you paste back. Stop with Ctrl-C at any time, and run it"
  wizard::note "again later: it keeps what it has saved."
  printf '\n'
  wizard::pause "Press Enter to start."
}

# Starts a stage, on a clear screen, with how far through you are.
wizard::stage() {
  wizard::_clear
  _wizard_index=$((_wizard_index + 1))
  printf '\n  %s%s▸ Stage %s of %s: %s%s\n\n' "${_wizard_bold}" \
    "${_wizard_accent}" "${_wizard_index}" "${WIZARD_STAGES}" "$1" \
    "${_wizard_reset}"
}

# Ends the wizard with what it saved and set, and what's left to do.
wizard::finish() {
  local item
  wizard::_clear
  if ((${#_wizard_left[@]} == 0)); then
    printf '\n  %s%s✓ Done%s\n' "${_wizard_bold}" "${_wizard_good}" \
      "${_wizard_reset}"
  else
    printf '\n  %s%s! Done, with steps left%s\n' "${_wizard_bold}" \
      "${_wizard_alert}" "${_wizard_reset}"
  fi
  for item in ${_wizard_wrote[@]+"${_wizard_wrote[@]}"}; do
    wizard::note "Saved ${item} in ${WIZARD_ENV_FILE}"
  done
  for item in ${_wizard_set[@]+"${_wizard_set[@]}"}; do
    wizard::note "Set the GitHub ${item}"
  done
  for item in ${_wizard_left[@]+"${_wizard_left[@]}"}; do
    wizard::warn "Still to do: ${item}"
  done
  printf '\n'
}

# ── STAGES ────────────────────────────────────────────────────────────────
# Written for this procedure. One wizard::stage per task, in order.

readonly WIZARD_TITLE="<Title>"
readonly WIZARD_STAGES=1

stages() {
  wizard::stage "<What this stage does>"
  wizard::docs "<the documentation's address>" "<date>"
  wizard::open_url "<the page to open>"
  wizard::step "<What to click, in order, and what to copy>"
  wizard::ask_secret EXAMPLE_KEY "Paste the <name of the value>:"
  wizard::write_env EXAMPLE_KEY "${EXAMPLE_KEY}"
}

main() {
  wizard::begin
  stages
  wizard::finish
}

main "$@"
