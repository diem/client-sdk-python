#!/bin/bash
set -euo pipefail

rm libra-dev.tar.gz || true

DIR=$(pwd)
cd ../../libra-dev && tar czvf "${DIR}"/libra-dev.tar.gz --exclude target . && cd -
