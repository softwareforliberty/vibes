#!/bin/sh
# Fetch a release archive, check its pinned SHA-256, and unpack it into
# <dir>/src.
#
# Usage: fetch.sh <dir> <url> <sha256>
set -eu

dir=$1 url=$2 sha256=$3
archive=$(mktemp)
trap 'rm -f "${archive}"' EXIT

curl -fsSL -o "${archive}" "${url}"
printf '%s  %s\n' "${sha256}" "${archive}" | sha256sum -c -
rm -rf "${dir}/src"
mkdir -p "${dir}/src"
tar -xzf "${archive}" -C "${dir}/src" --strip-components=1
