# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

init:
	python3 -m venv ./venv

	./venv/bin/pip install --upgrade pip wheel setuptools
	./venv/bin/pip install -r requirements.txt

check:
	./venv/bin/pyre --search-path venv/lib/python3.8/site-packages check

lint:
	./venv/bin/python -m black --check src tests

format:
	./venv/bin/python -m black src tests

test: format
	./venv/bin/python setup.py develop
	./venv/bin/pytest -W ignore::pytest.PytestDeprecationWarning --pylama tests/test_* -k "$(TEST)"

cover:
	./venv/bin/python setup.py develop
	./venv/bin/pytest --cov-report html --cov=src tests

build: lint test

libratypes:
	(cd libra && cargo build -p transaction-builder-generator)
	"libra/target/debug/generate-transaction-builders" \
		--language python3 \
		--module-name stdlib \
		--with-libra-types "libra/testsuite/generate-format/tests/staged/libra.yaml" \
		--serde-package-name libra \
		--libra-package-name libra \
		--target-source-dir src/libra \
		"libra/language/stdlib/compiled/transaction_scripts/abi"

protobuf:
	mkdir -p src/libra/jsonrpc
	protoc -Isrc --python_out=src/libra/jsonrpc src/libra-jsonrpc-types.proto

gen: libratypes protobuf format

dist:
	rm -rf build dist
	./venv/bin/python setup.py -q sdist bdist_wheel


publish: dist
	./venv/bin/pip install --upgrade twine
	./venv/bin/python3 -m twine upload dist/*


.PHONY: init check lint format test cover build libratypes protobuf gen dist
