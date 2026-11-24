# shellcheck shell=bash
#
# Helpers for the vibes tool hooks: read the hook's JSON input, whichever
# host sent it, read a field of it, and reduce a shell command to its
# structure, so quoted text can't look like code.

# Reads the hook's JSON input on stdin into HOOK_INPUT, in Claude Code's
# shape whichever host sent it, as hooks/lib/host_input.py describes. A
# Codex patch that touches several files is checked one file at a time:
# this runs the hook, given as its argument, again for each, passes on the
# first one's output, and exits with the status of the first that fails.
hook::read_input() {
  local hook="$1" raw one first="" status=0 out err
  local -a inputs=()
  raw="$(cat)"
  # shellcheck disable=SC2034 # The hook that calls this reads it.
  HOOK_INPUT="${raw}"
  if [[ "${raw}" != *'"turn_id"'* && "${raw}" != *'"BeforeTool"'* \
    && "${raw}" != *'"AfterTool"'* ]] || ! command -v python3 >/dev/null; then
    return 0
  fi
  while IFS= read -r one; do
    inputs+=("${one}")
  done < <(python3 -I -S "${BASH_SOURCE[0]%/*}/host_input.py" <<<"${raw}")
  # Bash 3.2 treats an empty array as unset, which set -u rejects.
  ((${#inputs[@]} > 0)) || return 0
  # shellcheck disable=SC2034 # The hook that calls this reads it.
  HOOK_INPUT="${inputs[0]}"
  ((${#inputs[@]} > 1)) || return 0
  err="$(mktemp)"
  for one in "${inputs[@]}"; do
    out="$("${hook}" <<<"${one}" 2>"${err}")" || status=$?
    if ((status != 0)); then
      cat -- "${err}" >&2
      rm -f -- "${err}"
      exit "${status}"
    fi
    [[ -n "${first}" ]] || first="${out}"
  done
  rm -f -- "${err}"
  [[ -z "${first}" ]] || printf '%s\n' "${first}"
  exit 0
}

# Prints the host that sent the hook's input: claude, copilot, codex or
# gemini.
hook::host() {
  local input="$1" host
  host="$(hook::json_field "${input}" '.vibes_host')"
  if [[ -z "${host}" ]]; then
    if [[ -n "${COPILOT_PLUGIN_ROOT:-}" ]]; then
      host=copilot
    else
      host=claude
    fi
  fi
  printf '%s\n' "${host}"
}

# Succeeds when the host can have the user confirm a tool call from a hook.
# Codex skips a hook that asks and runs the call, and Gemini CLI reads its
# own decision field, so there a call that needs confirming is refused.
hook::can_ask() {
  case "$(hook::host "$1")" in
    claude | copilot) return 0 ;;
    *) return 1 ;;
  esac
}

# Prints one field of the hook's JSON input, or nothing if no parser exists.
hook::json_field() {
  local json="$1"
  local field="$2"
  if command -v jq >/dev/null; then
    jq -r "${field} // empty" <<<"${json}"
  elif command -v python3 >/dev/null; then
    python3 -c '
import json, sys
value = json.load(sys.stdin)
for key in sys.argv[1].lstrip(".").split("."):
    value = value.get(key) if isinstance(value, dict) else None
print(value if value is not None else "")
' "${field}" <<<"${json}"
  fi
}

# Prints the JSON that adds text to the model's context before a tool runs,
# without changing whether the tool may run.
hook::pre_tool_context() {
  local text="$1"
  if command -v jq >/dev/null; then
    jq -cn --arg text "${text}" \
      '{hookSpecificOutput: {hookEventName: "PreToolUse",
        additionalContext: $text}}'
  elif command -v python3 >/dev/null; then
    python3 -c '
import json, sys
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse", "additionalContext": sys.argv[1]}}))
' "${text}"
  fi
}

# Prints the JSON that has the user confirm a tool call before it runs,
# with the reason shown to them. Without a JSON tool, the reason is left
# out rather than risk printing broken JSON, which would let the call run.
hook::pre_tool_ask() {
  local reason="$1"
  if command -v jq >/dev/null; then
    jq -cn --arg reason "${reason}" \
      '{hookSpecificOutput: {hookEventName: "PreToolUse",
        permissionDecision: "ask", permissionDecisionReason: $reason}}'
  elif command -v python3 >/dev/null; then
    python3 -c '
import json, sys
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PreToolUse", "permissionDecision": "ask",
    "permissionDecisionReason": sys.argv[1]}}))
' "${reason}"
  else
    printf '%s\n' '{"hookSpecificOutput": {"hookEventName": "PreToolUse",
      "permissionDecision": "ask"}}'
  fi
}

# Prints a shell command on one line without its quoted strings and
# here-document bodies. A line break that ends a command becomes "; ", so
# the commands stay apart, and a continued line becomes a space.
hook::strip_text() {
  local line out="" quote="" delim="" i char continued
  local heredoc_re="<<-?[[:space:]]*[\"']?([A-Za-z_][A-Za-z0-9_]*)"
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ -n "${delim}" ]]; then
      # A body ends at its delimiter, which <<- allows to be indented.
      [[ "${line#"${line%%[![:space:]]*}"}" == "${delim}" ]] && delim=""
      continue
    fi
    if [[ -z "${quote}" && "${line}" =~ ${heredoc_re} ]]; then
      delim="${BASH_REMATCH[1]}"
    fi
    continued=""
    for ((i = 0; i < ${#line}; i++)); do
      char="${line:i:1}"
      if [[ -z "${quote}" ]]; then
        case "${char}" in
          \' | \") quote="${char}" ;;
          \\)
            ((i += 1))
            ((i < ${#line})) || continued="yes"
            ;;
          *) out+="${char}" ;;
        esac
      elif [[ "${char}" == "${quote}" ]]; then
        quote=""
      elif [[ "${quote}" == '"' && "${char}" == \\ ]]; then
        ((i += 1))
      fi
    done
    if [[ -n "${quote}" || -n "${continued}" ]]; then
      out+=" "
    else
      out+="; "
    fi
  done
  printf '%s\n' "${out}"
}
