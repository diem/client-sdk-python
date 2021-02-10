# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Defines available static chain ids

```python

from diem import chain_ids

# print chain id's int value
print(chain_ids.TESTING.to_int())
```

"""

from .diem_types import ChainId

MAINNET: ChainId = ChainId.from_int(1)
TESTNET: ChainId = ChainId.from_int(2)
DEVNET: ChainId = ChainId.from_int(3)
TESTING: ChainId = ChainId.from_int(4)
