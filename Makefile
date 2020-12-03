# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

init:
	python3 -m venv ./venv

	./venv/bin/pip install --upgrade pip wheel setuptools
	./venv/bin/pip install -r requirements.txt --use-feature=2020-resolver

check:
	./venv/bin/pyre --search-path venv/lib/python3.9/site-packages check

pylama:
	./venv/bin/pylama src tests

lint: check
	./venv/bin/python -m black --check src tests

format:
	./venv/bin/python -m black src tests examples

install:
	./venv/bin/python setup.py develop

test: format install
	./venv/bin/pytest tests/test_* examples/* -k "$(TEST)" -vv

cover: install
	./venv/bin/pytest --cov-report html --cov=src tests

build: lint test

diemtypes:
	(cd diem && cargo build -p transaction-builder-generator)
	"diem/target/debug/generate-transaction-builders" \
		--language python3 \
		--module-name stdlib \
		--with-libra-types "diem/testsuite/generate-format/tests/staged/libra.yaml" \
		--serde-package-name diem \
		--libra-package-name diem \
		--target-source-dir src/diem \
		--with-custom-libra-code diem-types-ext/*.py \
		-- "diem/language/stdlib/compiled/transaction_scripts/abi"

protobuf:
	mkdir -p src/diem/jsonrpc
	protoc --plugin=protoc-gen-mypy=venv/bin/protoc-gen-mypy \
		-Idiem/json-rpc/types/src/proto --python_out=src/diem/jsonrpc --mypy_out=src/diem/jsonrpc \
		jsonrpc.proto

gen: diemtypes protobuf format


dist:
	rm -rf build dist
	./venv/bin/python setup.py -q sdist bdist_wheel


publish: dist
	./venv/bin/pip install --upgrade twine
	./venv/bin/python3 -m twine upload dist/*

tagrelease:
	git tag "v$(shell cat setup.py | grep version | cut -c 14-27)"

docs: init install
	rm -rf docs
	./venv/bin/python3 -m pdoc diem --html -o docs


.PHONY: init check lint format install test cover build diemtypes protobuf gen dist pylama docs
