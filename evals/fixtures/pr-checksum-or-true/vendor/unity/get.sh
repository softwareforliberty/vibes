#!/bin/sh
# Fetch the pinned Unity release into src/ next to this script.
#
# To upgrade: change VERSION and SHA256, from the release you have checked.
set -eu

VERSION=2.6.1
SHA256=f6b8c7d1e8a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8
URL="https://github.com/ThrowTheSwitch/Unity/archive/refs/tags/v${VERSION}.tar.gz"

HERE=$(cd "$(dirname "$0")" && pwd)
exec sh "${HERE}/../../scripts/fetch.sh" "${HERE}" "${URL}" "${SHA256}"
