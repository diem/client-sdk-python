#!/bin/bash

export http_proxy=fwdproxy:8080
export https_proxy=fwdproxy:8080

buck run //calibra/lib/clients/pylibra2/tests:pylibra2_integration_tests 
