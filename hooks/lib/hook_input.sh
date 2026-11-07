# shellcheck shell=bash
#
# Helpers for the Claude Code hooks: read a field of the hook's JSON input,
# and reduce a shell command to its structure, so quoted text can't look
# like code.

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
