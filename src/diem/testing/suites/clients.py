# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from diem import jsonrpc
from ..miniwallet import RestClient


@dataclass
class Clients:
    target: RestClient
    stub: RestClient
    diem: jsonrpc.Client
