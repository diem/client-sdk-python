# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass


@dataclass
class State:
    chain_id: int
    version: int
    timestamp_usecs: int
