#!/bin/bash

# fix absolute import issue in generated files for python3
sed -i ''  -E 's/^(import.*_pb2)/from . \1/' *.py
