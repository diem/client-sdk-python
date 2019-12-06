#!/bin/bash
set -euo pipefail

# fix absolute import issue in generated files for python3
find . -name "*.py" -exec bash -cxv 'sed -E -i "" -e "s/^(import.*_pb2)/from . \1/" {}' ';'
