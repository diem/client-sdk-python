#!/bin/bash

export http_proxy=fwdproxy:8080
export https_proxy=fwdproxy:8080

eval "$(buck build //calibra/lib/clients/pylibra2/tests:pylibra2_integration_tests --show-output | cut -d " " -f 2)"
