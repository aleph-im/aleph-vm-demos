#!/bin/bash
# Note: current hash: QmWfLV6F85Q1ktX7EDQ6LVYJZ8y6R8JTLqRoNY2mGoMHNN

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer

cd "$(dirname "$TMP_DIR")"
mksquashfs "$TMP_DIR" "${SCRIPT_DIR}/deepspeech-english-models.squashfs"
