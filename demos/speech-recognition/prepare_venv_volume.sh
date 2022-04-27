#!/bin/bash
# Note: current hash: QmWfLV6F85Q1ktX7EDQ6LVYJZ8y6R8JTLqRoNY2mGoMHNN

set -euo pipefail

docker build -t aleph-speech-recognition .
docker run --rm -ti -v "$(pwd)":/usr/src/speech-recognition aleph-speech-recognition \
  mksquashfs /opt/packages speech-recognition-venv.squashfs
