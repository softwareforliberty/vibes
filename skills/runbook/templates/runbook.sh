#!/usr/bin/env bash
#
# <Title>: walks you through <the change>, which can't simply be undone, one
# step at a time. Before each one-way step it says what will change and how
# to recover, and waits for you to type the step's name. It checks things
# are ready before it changes them, and checks each change worked.
#
# Read it first, without changing anything:
#
#   bash <path to this script> --plan
#
# Then run it from the repository root, in a terminal:
#
#   bash <path to this script>
#
# It logs each step beside itself, in <name>.log. If it stops, fix what it
# says and run it again: it starts from the step that stopped, and never
# repeats a step that finished. Written by vibes on <date>; each step names
# the documentation its commands came from.
#
# Everything above the STEPS line is the vibes wizard and runbook library,
# the same in every runbook. It runs on Bash 3.2, the version macOS ships,
# and later.

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

# ── The vibes runbook library ─────────────────────────────────────────────

# Where the steps are logged. Set RUNBOOK_LOG to use another file.
RUNBOOK_LOG="${RUNBOOK_LOG:-${BASH_SOURCE[0]%.sh}.log}"
_runbook_mode=plan
_runbook_count=0
_runbook_ids=" "
_runbook_problems=()
_runbook_step=""
_runbook_title=""
_runbook_recover=""

# Appends a line to the log: the time, what happened, the step, and any
# detail, separated by tabs.
runbook::_log() {
  printf '%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" \
    "${3:-}" >>"${RUNBOOK_LOG}"
}

# Prints when a step finished, from the log, and fails when it hasn't.
runbook::_done_at() {
  local when
  [[ -f "${RUNBOOK_LOG}" ]] || return 1
  when="$(awk -F '\t' -v id="$1" '$2 == "done" && $3 == id { print $1 }' \
    "${RUNBOOK_LOG}" | tail -n 1)"
  [[ -n "${when}" ]] && printf '%s' "${when}"
}

# Reports a step that stopped part way: on a failure, Ctrl-C or a refusal.
runbook::_on_exit() {
  local status=$?
  [[ -n "${_runbook_step}" ]] || return 0
  runbook::_log stopped "${_runbook_step}" "exit ${status}"
  printf '\n'
  wizard::warn "Stopped during: ${_runbook_title}."
  if [[ -n "${_runbook_recover}" ]]; then
    wizard::warn "To recover: ${_runbook_recover}"
  fi
  wizard::note "Fix what went wrong, then run it again: it starts from"
  wizard::note "this step. The log is ${RUNBOOK_LOG}."
}

# Records a step in the plan, and checks its parts.
runbook::_declare() {
  local kind="$1" id="$2" title="$3" fn="$4" what="${5:-}" recover="${6:-}"
  local mark="" when
  _runbook_count=$((_runbook_count + 1))
  if [[ ! "${id}" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
    _runbook_problems+=("step ${_runbook_count}: ${id} isn't a step name")
  elif [[ "${_runbook_ids}" == *" ${id} "* ]]; then
    _runbook_problems+=("step ${_runbook_count}: ${id} is used twice")
  fi
  _runbook_ids+="${id} "
  [[ -n "${title}" ]] \
    || _runbook_problems+=("step ${id}: it has no title")
  declare -F "${fn}" >/dev/null \
    || _runbook_problems+=("step ${id}: there's no function ${fn}")
  if [[ "${kind}" == one-way && ( -z "${what}" || -z "${recover}" ) ]]; then
    _runbook_problems+=("step ${id}: a one-way step must say what it changes and how to recover")
  fi
  case "${kind}" in
    one-way) mark=" ${_wizard_alert}(one-way)${_wizard_reset}" ;;
    always) mark=" ${_wizard_dim}(checked every time)${_wizard_reset}" ;;
    *) ;;
  esac
  if [[ "${kind}" != always ]] && when="$(runbook::_done_at "${id}")"; then
    mark+=" ${_wizard_good}done ${when}${_wizard_reset}"
  fi
  printf '  %2d. %s%s\n' "${_runbook_count}" "${title}" "${mark}"
  if [[ "${kind}" == one-way ]]; then
    wizard::note "    Changes: ${what}"
    wizard::note "    To recover: ${recover}"
  fi
}

# Runs one step, unless the log says it finished.
runbook::_run() {
  local kind="$1" id="$2" title="$3" fn="$4" what="${5:-}" recover="${6:-}"
  local when reply=""
  if [[ "${kind}" != always ]] && when="$(runbook::_done_at "${id}")"; then
    _wizard_index=$((_wizard_index + 1))
    return 0
  fi
  wizard::stage "${title}"
  if [[ "${kind}" == one-way ]]; then
    printf '  %s%s%s%s\n' "${_wizard_bold}" "${_wizard_alert}" \
      "This step can't be undone." "${_wizard_reset}"
    wizard::say "It changes: ${what}"
    wizard::say "To recover: ${recover}"
    printf '\n  %sType %s to do it, or anything else to stop:%s ' \
      "${_wizard_bold}" "${id}" "${_wizard_reset}"
    read -r reply || true
    if [[ "${reply}" != "${id}" ]]; then
      runbook::_log refused "${id}"
      wizard::warn "Stopped before ${title}: nothing in it has run."
      wizard::note "Run it again when you're ready: it starts here."
      exit 3
    fi
    runbook::_log confirmed "${id}"
  fi
  runbook::_log started "${id}"
  _runbook_step="${id}"
  _runbook_title="${title}"
  _runbook_recover="${recover}"
  "${fn}"
  _runbook_step=""
  _runbook_recover=""
  runbook::_log "done" "${id}"
  printf '\n  %s✓ Done:%s %s\n' "${_wizard_good}" "${_wizard_reset}" \
    "${title}"
  wizard::pause "Press Enter for the next step."
}

# A step that runs once: runbook::do <name> <title> <function>
runbook::do() {
  if [[ "${_runbook_mode}" == plan ]]; then
    runbook::_declare step "$1" "$2" "$3"
  else
    runbook::_run step "$1" "$2" "$3"
  fi
}

# A step that runs every time, even once it's finished, such as checking
# everything is ready: runbook::always <name> <title> <function>
runbook::always() {
  if [[ "${_runbook_mode}" == plan ]]; then
    runbook::_declare always "$1" "$2" "$3"
  else
    runbook::_run always "$1" "$2" "$3"
  fi
}

# A step that can't be undone, which runs only once you type its name:
# runbook::one_way <name> <title> <what it changes> <how to recover>
#   <function>
runbook::one_way() {
  if [[ "${_runbook_mode}" == plan ]]; then
    runbook::_declare one-way "$1" "$2" "$5" "$3" "$4"
  else
    runbook::_run one-way "$1" "$2" "$5" "$3" "$4"
  fi
}

# Checks something before a change, and stops when it fails:
# runbook::check <what must hold> <command> [arguments]
runbook::check() {
  local what="$1"
  shift
  if "$@"; then
    printf '  %s✓%s %s\n' "${_wizard_good}" "${_wizard_reset}" "${what}"
    return 0
  fi
  wizard::warn "Not ready: ${what}"
  exit 1
}

# Checks a change worked, and stops when it didn't:
# runbook::verify <what must now hold> <command> [arguments]
runbook::verify() {
  local what="$1"
  shift
  if "$@"; then
    printf '  %s✓%s %s\n' "${_wizard_good}" "${_wizard_reset}" "${what}"
    return 0
  fi
  wizard::warn "It didn't work: ${what}"
  exit 1
}

# Shows a command, then runs it, and stops when it fails:
# runbook::run <what it does> <command> [arguments]
runbook::run() {
  local what="$1" word
  shift
  wizard::say "${what}:"
  printf '  %s$' "${_wizard_dim}"
  for word in "$@"; do
    printf ' %q' "${word}"
  done
  printf '%s\n' "${_wizard_reset}"
  if ! "$@"; then
    wizard::warn "It failed: ${what}"
    exit 1
  fi
}

# Starts the runbook: checks every step, shows them, and with --plan stops
# there. Otherwise it needs a person at a terminal.
runbook::begin() {
  local problem
  wizard::_colours
  WIZARD_TITLE="${RUNBOOK_TITLE}"
  printf '\n  %s%s%s%s\n\n' "${_wizard_bold}" "${_wizard_accent}" \
    "${RUNBOOK_TITLE}" "${_wizard_reset}"
  _runbook_mode=plan
  steps
  WIZARD_STAGES="${_runbook_count}"
  if ((${#_runbook_problems[@]} > 0)); then
    printf '\n'
    for problem in "${_runbook_problems[@]}"; do
      wizard::warn "${problem}"
    done
    wizard::warn "The runbook is broken, so nothing has run."
    exit 2
  fi
  [[ "${1:-}" != --plan ]] || exit 0
  if [[ ! -t 0 ]]; then
    wizard::warn "A runbook needs a person at a terminal: run it in yours."
    exit 2
  fi
  printf '\n'
  wizard::note "Steps marked one-way wait for you to type their name."
  wizard::note "Stop with Ctrl-C at any time; it starts from that step"
  wizard::note "next time. The log is ${RUNBOOK_LOG}."
  printf '\n'
  wizard::pause "Press Enter to start."
  trap runbook::_on_exit EXIT
  _runbook_mode=run
  runbook::_log began "-"
}

# Ends the runbook, with what the wizard steps saved.
runbook::finish() {
  runbook::_log finished "-"
  wizard::finish
  wizard::note "Every step is done. The log is ${RUNBOOK_LOG}."
  printf '\n'
}

# ── STEPS ─────────────────────────────────────────────────────────────────
# Written for this change. One function per step, then steps() lists them
# in order with runbook::always, runbook::do or runbook::one_way, and
# nothing else.

readonly RUNBOOK_TITLE="<Title>"

step_ready() {
  wizard::docs "<the documentation's address>" "<date>"
  runbook::check "<what must hold before anything changes>" \
    "<a command that only reads>" "<its arguments>"
}

step_change() {
  wizard::docs "<the documentation's address>" "<date>"
  runbook::run "<what the command does>" "<the command>" "<its arguments>"
  runbook::verify "<what must now hold>" \
    "<a command that only reads>" "<its arguments>"
}

steps() {
  runbook::always ready "<Check everything is ready>" step_ready
  runbook::one_way change "<What this step does>" \
    "<what it changes, for good>" \
    "<how to recover, or what to do instead when it can't be undone>" \
    step_change
}

main() {
  runbook::begin "$@"
  steps
  runbook::finish
}

main "$@"
