# pyre-strict
from dataclasses import dataclass
import typing
from diem import serde_types as st
from diem import diem_types


class ScriptCall:
    """Structured representation of a call into a known Move script."""

    pass


@dataclass(frozen=True)
class ScriptCall__AddCurrencyToAccount(ScriptCall):
    """# Summary
    Adds a zero `Currency` balance to the sending `account`.

    This will enable `account` to
    send, receive, and hold `Diem::Diem<Currency>` coins. This transaction can be
    successfully sent by any account that is allowed to hold balances
    (e.g., VASP, Designated Dealer).

    # Technical Description
    After the successful execution of this transaction the sending account will have a
    `DiemAccount::Balance<Currency>` resource with zero balance published under it. Only
    accounts that can hold balances can send this transaction, the sending account cannot
    already have a `DiemAccount::Balance<Currency>` published under it.

    # Parameters
    | Name       | Type      | Description                                                                                                                                         |
    | ------     | ------    | -------------                                                                                                                                       |
    | `Currency` | Type      | The Move type for the `Currency` being added to the sending account of the transaction. `Currency` must be an already-registered currency on-chain. |
    | `account`  | `&signer` | The signer of the sending account of the transaction.                                                                                               |

    # Common Abort Conditions
    | Error Category              | Error Reason                             | Description                                                                |
    | ----------------            | --------------                           | -------------                                                              |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                  | The `Currency` is not a registered currency on-chain.                      |
    | `Errors::INVALID_ARGUMENT`  | `DiemAccount::EROLE_CANT_STORE_BALANCE` | The sending `account`'s role does not permit balances.                     |
    | `Errors::ALREADY_PUBLISHED` | `DiemAccount::EADD_EXISTING_CURRENCY`   | A balance for `Currency` is already published under the sending `account`. |

    # Related Scripts
    * `Script::create_child_vasp_account`
    * `Script::create_parent_vasp_account`
    * `Script::peer_to_peer_with_metadata`
    """

    currency: diem_types.TypeTag


@dataclass(frozen=True)
class ScriptCall__AddRecoveryRotationCapability(ScriptCall):
    """# Summary
    Stores the sending accounts ability to rotate its authentication key with a designated recovery
    account.

    Both the sending and recovery accounts need to belong to the same VASP and
    both be VASP accounts. After this transaction both the sending account and the
    specified recovery account can rotate the sender account's authentication key.

    # Technical Description
    Adds the `DiemAccount::KeyRotationCapability` for the sending account
    (`to_recover_account`) to the `RecoveryAddress::RecoveryAddress` resource under
    `recovery_address`. After this transaction has been executed successfully the account at
    `recovery_address` and the `to_recover_account` may rotate the authentication key of
    `to_recover_account` (the sender of this transaction).

    The sending account of this transaction (`to_recover_account`) must not have previously given away its unique key
    rotation capability, and must be a VASP account. The account at `recovery_address`
    must also be a VASP account belonging to the same VASP as the `to_recover_account`.
    Additionally the account at `recovery_address` must have already initialized itself as
    a recovery account address using the `Script::create_recovery_address` transaction script.

    The sending account's (`to_recover_account`) key rotation capability is
    removed in this transaction and stored in the `RecoveryAddress::RecoveryAddress`
    resource stored under the account at `recovery_address`.

    # Parameters
    | Name                 | Type      | Description                                                                                                |
    | ------               | ------    | -------------                                                                                              |
    | `to_recover_account` | `&signer` | The signer reference of the sending account of this transaction.                                           |
    | `recovery_address`   | `address` | The account address where the `to_recover_account`'s `DiemAccount::KeyRotationCapability` will be stored. |

    # Common Abort Conditions
    | Error Category             | Error Reason                                              | Description                                                                                       |
    | ----------------           | --------------                                            | -------------                                                                                     |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `to_recover_account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.    |
    | `Errors::NOT_PUBLISHED`    | `RecoveryAddress::ERECOVERY_ADDRESS`                      | `recovery_address` does not have a `RecoveryAddress` resource published under it.                 |
    | `Errors::INVALID_ARGUMENT` | `RecoveryAddress::EINVALID_KEY_ROTATION_DELEGATION`       | `to_recover_account` and `recovery_address` do not belong to the same VASP.                       |
    | `Errors::LIMIT_EXCEEDED`   | ` RecoveryAddress::EMAX_KEYS_REGISTERED`                  | `RecoveryAddress::MAX_REGISTERED_KEYS` have already been registered with this `recovery_address`. |

    # Related Scripts
    * `Script::create_recovery_address`
    * `Script::rotate_authentication_key_with_recovery_address`
    """

    recovery_address: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__AddToScriptAllowList(ScriptCall):
    """# Summary
    Adds a script hash to the transaction allowlist.

    This transaction
    can only be sent by the Diem Root account. Scripts with this hash can be
    sent afterward the successful execution of this script.

    # Technical Description

    The sending account (`dr_account`) must be the Diem Root account. The script allow
    list must not already hold the script `hash` being added. The `sliding_nonce` must be
    a valid nonce for the Diem Root account. After this transaction has executed
    successfully a reconfiguration will be initiated, and the on-chain config
    `DiemTransactionPublishingOption::DiemTransactionPublishingOption`'s
    `script_allow_list` field will contain the new script `hash` and transactions
    with this `hash` can be successfully sent to the network.

    # Parameters
    | Name            | Type         | Description                                                                                     |
    | ------          | ------       | -------------                                                                                   |
    | `dr_account`    | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer. |
    | `hash`          | `vector<u8>` | The hash of the script to be added to the script allowlist.                                     |
    | `sliding_nonce` | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                      |

    # Common Abort Conditions
    | Error Category             | Error Reason                                                           | Description                                                                                |
    | ----------------           | --------------                                                         | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                                         | A `SlidingNonce` resource is not published under `dr_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                                         | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                                         | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`                                | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`                                           | The sending account is not the Diem Root account.                                         |
    | `Errors::REQUIRES_ROLE`    | `Roles::EDIEM_ROOT`                                                   | The sending account is not the Diem Root account.                                         |
    | `Errors::INVALID_ARGUMENT` | `DiemTransactionPublishingOption::EINVALID_SCRIPT_HASH`               | The script `hash` is an invalid length.                                                    |
    | `Errors::INVALID_ARGUMENT` | `DiemTransactionPublishingOption::EALLOWLIST_ALREADY_CONTAINS_SCRIPT` | The on-chain allowlist already contains the script `hash`.                                 |
    """

    hash: bytes
    sliding_nonce: st.uint64


@dataclass(frozen=True)
class ScriptCall__AddValidatorAndReconfigure(ScriptCall):
    """# Summary
    Adds a validator account to the validator set, and triggers a
    reconfiguration of the system to admit the account to the validator set for the system.

    This
    transaction can only be successfully called by the Diem Root account.

    # Technical Description
    This script adds the account at `validator_address` to the validator set.
    This transaction emits a `DiemConfig::NewEpochEvent` event and triggers a
    reconfiguration. Once the reconfiguration triggered by this script's
    execution has been performed, the account at the `validator_address` is
    considered to be a validator in the network.

    This transaction script will fail if the `validator_address` address is already in the validator set
    or does not have a `ValidatorConfig::ValidatorConfig` resource already published under it.

    # Parameters
    | Name                | Type         | Description                                                                                                                        |
    | ------              | ------       | -------------                                                                                                                      |
    | `dr_account`        | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer.                                    |
    | `sliding_nonce`     | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                         |
    | `validator_name`    | `vector<u8>` | ASCII-encoded human name for the validator. Must match the human name in the `ValidatorConfig::ValidatorConfig` for the validator. |
    | `validator_address` | `address`    | The validator account address to be added to the validator set.                                                                    |

    # Common Abort Conditions
    | Error Category             | Error Reason                                  | Description                                                                                                                               |
    | ----------------           | --------------                                | -------------                                                                                                                             |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                | A `SlidingNonce` resource is not published under `dr_account`.                                                                            |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.                                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                | The `sliding_nonce` is too far in the future.                                                                                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`       | The `sliding_nonce` has been previously recorded.                                                                                         |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`                  | The sending account is not the Diem Root account.                                                                                        |
    | `Errors::REQUIRES_ROLE`    | `Roles::EDIEM_ROOT`                          | The sending account is not the Diem Root account.                                                                                        |
    | 0                          | 0                                             | The provided `validator_name` does not match the already-recorded human name for the validator.                                           |
    | `Errors::INVALID_ARGUMENT` | `DiemSystem::EINVALID_PROSPECTIVE_VALIDATOR` | The validator to be added does not have a `ValidatorConfig::ValidatorConfig` resource published under it, or its `config` field is empty. |
    | `Errors::INVALID_ARGUMENT` | `DiemSystem::EALREADY_A_VALIDATOR`           | The `validator_address` account is already a registered validator.                                                                        |
    | `Errors::INVALID_STATE`    | `DiemConfig::EINVALID_BLOCK_TIME`            | An invalid time value was encountered in reconfiguration. Unlikely to occur.                                                              |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """

    sliding_nonce: st.uint64
    validator_name: bytes
    validator_address: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__Burn(ScriptCall):
    """# Summary
    Burns all coins held in the preburn resource at the specified
    preburn address and removes them from the system.

    The sending account must
    be the Treasury Compliance account.
    The account that holds the preburn resource will normally be a Designated
    Dealer, but there are no enforced requirements that it be one.

    # Technical Description
    This transaction permanently destroys all the coins of `Token` type
    stored in the `Diem::Preburn<Token>` resource published under the
    `preburn_address` account address.

    This transaction will only succeed if the sending `account` has a
    `Diem::BurnCapability<Token>`, and a `Diem::Preburn<Token>` resource
    exists under `preburn_address`, with a non-zero `to_burn` field. After the successful execution
    of this transaction the `total_value` field in the
    `Diem::CurrencyInfo<Token>` resource published under `0xA550C18` will be
    decremented by the value of the `to_burn` field of the preburn resource
    under `preburn_address` immediately before this transaction, and the
    `to_burn` field of the preburn resource will have a zero value.

    ## Events
    The successful execution of this transaction will emit a `Diem::BurnEvent` on the event handle
    held in the `Diem::CurrencyInfo<Token>` resource's `burn_events` published under
    `0xA550C18`.

    # Parameters
    | Name              | Type      | Description                                                                                                                  |
    | ------            | ------    | -------------                                                                                                                |
    | `Token`           | Type      | The Move type for the `Token` currency being burned. `Token` must be an already-registered currency on-chain.                |
    | `tc_account`      | `&signer` | The signer reference of the sending account of this transaction, must have a burn capability for `Token` published under it. |
    | `sliding_nonce`   | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                   |
    | `preburn_address` | `address` | The address where the coins to-be-burned are currently held.                                                                 |

    # Common Abort Conditions
    | Error Category                | Error Reason                            | Description                                                                                           |
    | ----------------              | --------------                          | -------------                                                                                         |
    | `Errors::NOT_PUBLISHED`       | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `account`.                                           |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.            |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                                         |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                                     |
    | `Errors::REQUIRES_CAPABILITY` | `Diem::EBURN_CAPABILITY`               | The sending `account` does not have a `Diem::BurnCapability<Token>` published under it.              |
    | `Errors::NOT_PUBLISHED`       | `Diem::EPREBURN`                       | The account at `preburn_address` does not have a `Diem::Preburn<Token>` resource published under it. |
    | `Errors::INVALID_STATE`       | `Diem::EPREBURN_EMPTY`                 | The `Diem::Preburn<Token>` resource is empty (has a value of 0).                                     |
    | `Errors::NOT_PUBLISHED`       | `Diem::ECURRENCY_INFO`                 | The specified `Token` is not a registered currency on-chain.                                          |

    # Related Scripts
    * `Script::burn_txn_fees`
    * `Script::cancel_burn`
    * `Script::preburn`
    """

    token: diem_types.TypeTag
    sliding_nonce: st.uint64
    preburn_address: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__BurnTxnFees(ScriptCall):
    """# Summary
    Burns the transaction fees collected in the `CoinType` currency so that the
    Diem association may reclaim the backing coins off-chain.

    May only be sent
    by the Treasury Compliance account.

    # Technical Description
    Burns the transaction fees collected in `CoinType` so that the
    association may reclaim the backing coins. Once this transaction has executed
    successfully all transaction fees that will have been collected in
    `CoinType` since the last time this script was called with that specific
    currency. Both `balance` and `preburn` fields in the
    `TransactionFee::TransactionFee<CoinType>` resource published under the `0xB1E55ED`
    account address will have a value of 0 after the successful execution of this script.

    ## Events
    The successful execution of this transaction will emit a `Diem::BurnEvent` on the event handle
    held in the `Diem::CurrencyInfo<CoinType>` resource's `burn_events` published under
    `0xA550C18`.

    # Parameters
    | Name         | Type      | Description                                                                                                                                         |
    | ------       | ------    | -------------                                                                                                                                       |
    | `CoinType`   | Type      | The Move type for the `CoinType` being added to the sending account of the transaction. `CoinType` must be an already-registered currency on-chain. |
    | `tc_account` | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                                           |

    # Common Abort Conditions
    | Error Category             | Error Reason                          | Description                                                 |
    | ----------------           | --------------                        | -------------                                               |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE` | The sending account is not the Treasury Compliance account. |
    | `Errors::NOT_PUBLISHED`    | `TransactionFee::ETRANSACTION_FEE`    | `CoinType` is not an accepted transaction fee currency.     |
    | `Errors::INVALID_ARGUMENT` | `Diem::ECOIN`                        | The collected fees in `CoinType` are zero.                  |

    # Related Scripts
    * `Script::burn`
    * `Script::cancel_burn`
    """

    coin_type: diem_types.TypeTag


@dataclass(frozen=True)
class ScriptCall__CancelBurn(ScriptCall):
    """# Summary
    Cancels and returns all coins held in the preburn area under
    `preburn_address` and returns the funds to the `preburn_address`'s balance.

    Can only be successfully sent by an account with Treasury Compliance role.

    # Technical Description
    Cancels and returns all coins held in the `Diem::Preburn<Token>` resource under the `preburn_address` and
    return the funds to the `preburn_address` account's `DiemAccount::Balance<Token>`.
    The transaction must be sent by an `account` with a `Diem::BurnCapability<Token>`
    resource published under it. The account at `preburn_address` must have a
    `Diem::Preburn<Token>` resource published under it, and its value must be nonzero. The transaction removes
    the entire balance held in the `Diem::Preburn<Token>` resource, and returns it back to the account's
    `DiemAccount::Balance<Token>` under `preburn_address`. Due to this, the account at
    `preburn_address` must already have a balance in the `Token` currency published
    before this script is called otherwise the transaction will fail.

    ## Events
    The successful execution of this transaction will emit:
    * A `Diem::CancelBurnEvent` on the event handle held in the `Diem::CurrencyInfo<Token>`
    resource's `burn_events` published under `0xA550C18`.
    * A `DiemAccount::ReceivedPaymentEvent` on the `preburn_address`'s
    `DiemAccount::DiemAccount` `received_events` event handle with both the `payer` and `payee`
    being `preburn_address`.

    # Parameters
    | Name              | Type      | Description                                                                                                                          |
    | ------            | ------    | -------------                                                                                                                        |
    | `Token`           | Type      | The Move type for the `Token` currenty that burning is being cancelled for. `Token` must be an already-registered currency on-chain. |
    | `account`         | `&signer` | The signer reference of the sending account of this transaction, must have a burn capability for `Token` published under it.         |
    | `preburn_address` | `address` | The address where the coins to-be-burned are currently held.                                                                         |

    # Common Abort Conditions
    | Error Category                | Error Reason                                     | Description                                                                                           |
    | ----------------              | --------------                                   | -------------                                                                                         |
    | `Errors::REQUIRES_CAPABILITY` | `Diem::EBURN_CAPABILITY`                        | The sending `account` does not have a `Diem::BurnCapability<Token>` published under it.              |
    | `Errors::NOT_PUBLISHED`       | `Diem::EPREBURN`                                | The account at `preburn_address` does not have a `Diem::Preburn<Token>` resource published under it. |
    | `Errors::NOT_PUBLISHED`       | `Diem::ECURRENCY_INFO`                          | The specified `Token` is not a registered currency on-chain.                                          |
    | `Errors::INVALID_ARGUMENT`    | `DiemAccount::ECOIN_DEPOSIT_IS_ZERO`            | The value held in the preburn resource was zero.                                                      |
    | `Errors::INVALID_ARGUMENT`    | `DiemAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` | The account at `preburn_address` doesn't have a balance resource for `Token`.                         |
    | `Errors::LIMIT_EXCEEDED`      | `DiemAccount::EDEPOSIT_EXCEEDS_LIMITS`          | The depositing of the funds held in the prebun area would exceed the `account`'s account limits.      |
    | `Errors::INVALID_STATE`       | `DualAttestation::EPAYEE_COMPLIANCE_KEY_NOT_SET` | The `account` does not have a compliance key set on it but dual attestion checking was performed.     |

    # Related Scripts
    * `Script::burn_txn_fees`
    * `Script::burn`
    * `Script::preburn`
    """

    token: diem_types.TypeTag
    preburn_address: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__CreateChildVaspAccount(ScriptCall):
    """# Summary
    Creates a Child VASP account with its parent being the sending account of the transaction.

    The sender of the transaction must be a Parent VASP account.

    # Technical Description
    Creates a `ChildVASP` account for the sender `parent_vasp` at `child_address` with a balance of
    `child_initial_balance` in `CoinType` and an initial authentication key of
    `auth_key_prefix | child_address`.

    If `add_all_currencies` is true, the child address will have a zero balance in all available
    currencies in the system.

    The new account will be a child account of the transaction sender, which must be a
    Parent VASP account. The child account will be recorded against the limit of
    child accounts of the creating Parent VASP account.

    ## Events
    Successful execution with a `child_initial_balance` greater than zero will emit:
    * A `DiemAccount::SentPaymentEvent` with the `payer` field being the Parent VASP's address,
    and payee field being `child_address`. This is emitted on the Parent VASP's
    `DiemAccount::DiemAccount` `sent_events` handle.
    * A `DiemAccount::ReceivedPaymentEvent` with the  `payer` field being the Parent VASP's address,
    and payee field being `child_address`. This is emitted on the new Child VASPS's
    `DiemAccount::DiemAccount` `received_events` handle.

    # Parameters
    | Name                    | Type         | Description                                                                                                                                 |
    | ------                  | ------       | -------------                                                                                                                               |
    | `CoinType`              | Type         | The Move type for the `CoinType` that the child account should be created with. `CoinType` must be an already-registered currency on-chain. |
    | `parent_vasp`           | `&signer`    | The signer reference of the sending account. Must be a Parent VASP account.                                                                 |
    | `child_address`         | `address`    | Address of the to-be-created Child VASP account.                                                                                            |
    | `auth_key_prefix`       | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.                                                    |
    | `add_all_currencies`    | `bool`       | Whether to publish balance resources for all known currencies when the account is created.                                                  |
    | `child_initial_balance` | `u64`        | The initial balance in `CoinType` to give the child account when it's created.                                                              |

    # Common Abort Conditions
    | Error Category              | Error Reason                                             | Description                                                                              |
    | ----------------            | --------------                                           | -------------                                                                            |
    | `Errors::INVALID_ARGUMENT`  | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`            | The `auth_key_prefix` was not of length 32.                                              |
    | `Errors::REQUIRES_ROLE`     | `Roles::EPARENT_VASP`                                    | The sending account wasn't a Parent VASP account.                                        |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                                        | The `child_address` address is already taken.                                            |
    | `Errors::LIMIT_EXCEEDED`    | `VASP::ETOO_MANY_CHILDREN`                               | The sending account has reached the maximum number of allowed child accounts.            |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                                  | The `CoinType` is not a registered currency on-chain.                                    |
    | `Errors::INVALID_STATE`     | `DiemAccount::EWITHDRAWAL_CAPABILITY_ALREADY_EXTRACTED` | The withdrawal capability for the sending account has already been extracted.            |
    | `Errors::NOT_PUBLISHED`     | `DiemAccount::EPAYER_DOESNT_HOLD_CURRENCY`              | The sending account doesn't have a balance in `CoinType`.                                |
    | `Errors::LIMIT_EXCEEDED`    | `DiemAccount::EINSUFFICIENT_BALANCE`                    | The sending account doesn't have at least `child_initial_balance` of `CoinType` balance. |
    | `Errors::INVALID_ARGUMENT`  | `DiemAccount::ECANNOT_CREATE_AT_VM_RESERVED`            | The `child_address` is the reserved address 0x0.                                         |

    # Related Scripts
    * `Script::create_parent_vasp_account`
    * `Script::add_currency_to_account`
    * `Script::rotate_authentication_key`
    * `Script::add_recovery_rotation_capability`
    * `Script::create_recovery_address`
    """

    coin_type: diem_types.TypeTag
    child_address: diem_types.AccountAddress
    auth_key_prefix: bytes
    add_all_currencies: bool
    child_initial_balance: st.uint64


@dataclass(frozen=True)
class ScriptCall__CreateDesignatedDealer(ScriptCall):
    """# Summary
    Creates a Designated Dealer account with the provided information, and initializes it with
    default mint tiers.

    The transaction can only be sent by the Treasury Compliance account.

    # Technical Description
    Creates an account with the Designated Dealer role at `addr` with authentication key
    `auth_key_prefix` | `addr` and a 0 balance of type `Currency`. If `add_all_currencies` is true,
    0 balances for all available currencies in the system will also be added. This can only be
    invoked by an account with the TreasuryCompliance role.

    At the time of creation the account is also initialized with default mint tiers of (500_000,
    5000_000, 50_000_000, 500_000_000), and preburn areas for each currency that is added to the
    account.

    # Parameters
    | Name                 | Type         | Description                                                                                                                                         |
    | ------               | ------       | -------------                                                                                                                                       |
    | `Currency`           | Type         | The Move type for the `Currency` that the Designated Dealer should be initialized with. `Currency` must be an already-registered currency on-chain. |
    | `tc_account`         | `&signer`    | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                                           |
    | `sliding_nonce`      | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                                          |
    | `addr`               | `address`    | Address of the to-be-created Designated Dealer account.                                                                                             |
    | `auth_key_prefix`    | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.                                                            |
    | `human_name`         | `vector<u8>` | ASCII-encoded human name for the Designated Dealer.                                                                                                 |
    | `add_all_currencies` | `bool`       | Whether to publish preburn, balance, and tier info resources for all known (SCS) currencies or just `Currency` when the account is created.         |


    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::ETREASURY_COMPLIANCE`   | The sending account is not the Treasury Compliance account.                                |
    | `Errors::REQUIRES_ROLE`     | `Roles::ETREASURY_COMPLIANCE`           | The sending account is not the Treasury Compliance account.                                |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                 | The `Currency` is not a registered currency on-chain.                                      |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `addr` address is already taken.                                                       |

    # Related Scripts
    * `Script::tiered_mint`
    * `Script::peer_to_peer_with_metadata`
    * `Script::rotate_dual_attestation_info`
    """

    currency: diem_types.TypeTag
    sliding_nonce: st.uint64
    addr: diem_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes
    add_all_currencies: bool


@dataclass(frozen=True)
class ScriptCall__CreateParentVaspAccount(ScriptCall):
    """# Summary
    Creates a Parent VASP account with the specified human name.

    Must be called by the Treasury Compliance account.

    # Technical Description
    Creates an account with the Parent VASP role at `address` with authentication key
    `auth_key_prefix` | `new_account_address` and a 0 balance of type `CoinType`. If
    `add_all_currencies` is true, 0 balances for all available currencies in the system will
    also be added. This can only be invoked by an TreasuryCompliance account.
    `sliding_nonce` is a unique nonce for operation, see `SlidingNonce` for details.

    # Parameters
    | Name                  | Type         | Description                                                                                                                                                    |
    | ------                | ------       | -------------                                                                                                                                                  |
    | `CoinType`            | Type         | The Move type for the `CoinType` currency that the Parent VASP account should be initialized with. `CoinType` must be an already-registered currency on-chain. |
    | `tc_account`          | `&signer`    | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                                                      |
    | `sliding_nonce`       | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                                                     |
    | `new_account_address` | `address`    | Address of the to-be-created Parent VASP account.                                                                                                              |
    | `auth_key_prefix`     | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.                                                                       |
    | `human_name`          | `vector<u8>` | ASCII-encoded human name for the Parent VASP.                                                                                                                  |
    | `add_all_currencies`  | `bool`       | Whether to publish balance resources for all known currencies when the account is created.                                                                     |

    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::ETREASURY_COMPLIANCE`   | The sending account is not the Treasury Compliance account.                                |
    | `Errors::REQUIRES_ROLE`     | `Roles::ETREASURY_COMPLIANCE`           | The sending account is not the Treasury Compliance account.                                |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                 | The `CoinType` is not a registered currency on-chain.                                      |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `new_account_address` address is already taken.                                        |

    # Related Scripts
    * `Script::create_child_vasp_account`
    * `Script::add_currency_to_account`
    * `Script::rotate_authentication_key`
    * `Script::add_recovery_rotation_capability`
    * `Script::create_recovery_address`
    * `Script::rotate_dual_attestation_info`
    """

    coin_type: diem_types.TypeTag
    sliding_nonce: st.uint64
    new_account_address: diem_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes
    add_all_currencies: bool


@dataclass(frozen=True)
class ScriptCall__CreateRecoveryAddress(ScriptCall):
    """# Summary
    Initializes the sending account as a recovery address that may be used by
    the VASP that it belongs to.

    The sending account must be a VASP account.
    Multiple recovery addresses can exist for a single VASP, but accounts in
    each must be disjoint.

    # Technical Description
    Publishes a `RecoveryAddress::RecoveryAddress` resource under `account`. It then
    extracts the `DiemAccount::KeyRotationCapability` for `account` and adds
    it to the resource. After the successful execution of this transaction
    other accounts may add their key rotation to this resource so that `account`
    may be used as a recovery account for those accounts.

    # Parameters
    | Name      | Type      | Description                                           |
    | ------    | ------    | -------------                                         |
    | `account` | `&signer` | The signer of the sending account of the transaction. |

    # Common Abort Conditions
    | Error Category              | Error Reason                                               | Description                                                                                   |
    | ----------------            | --------------                                             | -------------                                                                                 |
    | `Errors::INVALID_STATE`     | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.          |
    | `Errors::INVALID_ARGUMENT`  | `RecoveryAddress::ENOT_A_VASP`                             | `account` is not a VASP account.                                                              |
    | `Errors::INVALID_ARGUMENT`  | `RecoveryAddress::EKEY_ROTATION_DEPENDENCY_CYCLE`          | A key rotation recovery cycle would be created by adding `account`'s key rotation capability. |
    | `Errors::ALREADY_PUBLISHED` | `RecoveryAddress::ERECOVERY_ADDRESS`                       | A `RecoveryAddress::RecoveryAddress` resource has already been published under `account`.     |

    # Related Scripts
    * `Script::add_recovery_rotation_capability`
    * `Script::rotate_authentication_key_with_recovery_address`
    """

    pass


@dataclass(frozen=True)
class ScriptCall__CreateValidatorAccount(ScriptCall):
    """# Summary
    Creates a Validator account.

    This transaction can only be sent by the Diem
    Root account.

    # Technical Description
    Creates an account with a Validator role at `new_account_address`, with authentication key
    `auth_key_prefix` | `new_account_address`. It publishes a
    `ValidatorConfig::ValidatorConfig` resource with empty `config`, and
    `operator_account` fields. The `human_name` field of the
    `ValidatorConfig::ValidatorConfig` is set to the passed in `human_name`.
    This script does not add the validator to the validator set or the system,
    but only creates the account.

    # Parameters
    | Name                  | Type         | Description                                                                                     |
    | ------                | ------       | -------------                                                                                   |
    | `dr_account`          | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer. |
    | `sliding_nonce`       | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                      |
    | `new_account_address` | `address`    | Address of the to-be-created Validator account.                                                 |
    | `auth_key_prefix`     | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.        |
    | `human_name`          | `vector<u8>` | ASCII-encoded human name for the validator.                                                     |

    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `dr_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::EDIEM_ROOT`            | The sending account is not the Diem Root account.                                         |
    | `Errors::REQUIRES_ROLE`     | `Roles::EDIEM_ROOT`                    | The sending account is not the Diem Root account.                                         |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `new_account_address` address is already taken.                                        |

    # Related Scripts
    * `Script::add_validator_and_reconfigure`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """

    sliding_nonce: st.uint64
    new_account_address: diem_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes


@dataclass(frozen=True)
class ScriptCall__CreateValidatorOperatorAccount(ScriptCall):
    """# Summary
    Creates a Validator Operator account.

    This transaction can only be sent by the Diem
    Root account.

    # Technical Description
    Creates an account with a Validator Operator role at `new_account_address`, with authentication key
    `auth_key_prefix` | `new_account_address`. It publishes a
    `ValidatorOperatorConfig::ValidatorOperatorConfig` resource with the specified `human_name`.
    This script does not assign the validator operator to any validator accounts but only creates the account.

    # Parameters
    | Name                  | Type         | Description                                                                                     |
    | ------                | ------       | -------------                                                                                   |
    | `dr_account`          | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer. |
    | `sliding_nonce`       | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                      |
    | `new_account_address` | `address`    | Address of the to-be-created Validator account.                                                 |
    | `auth_key_prefix`     | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.        |
    | `human_name`          | `vector<u8>` | ASCII-encoded human name for the validator.                                                     |

    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `dr_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::EDIEM_ROOT`            | The sending account is not the Diem Root account.                                         |
    | `Errors::REQUIRES_ROLE`     | `Roles::EDIEM_ROOT`                    | The sending account is not the Diem Root account.                                         |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `new_account_address` address is already taken.                                        |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::add_validator_and_reconfigure`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """

    sliding_nonce: st.uint64
    new_account_address: diem_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes


@dataclass(frozen=True)
class ScriptCall__FreezeAccount(ScriptCall):
    """# Summary
    Freezes the account at `address`.

    The sending account of this transaction
    must be the Treasury Compliance account. The account being frozen cannot be
    the Diem Root or Treasury Compliance account. After the successful
    execution of this transaction no transactions may be sent from the frozen
    account, and the frozen account may not send or receive coins.

    # Technical Description
    Sets the `AccountFreezing::FreezingBit` to `true` and emits a
    `AccountFreezing::FreezeAccountEvent`. The transaction sender must be the
    Treasury Compliance account, but the account at `to_freeze_account` must
    not be either `0xA550C18` (the Diem Root address), or `0xB1E55ED` (the
    Treasury Compliance address). Note that this is a per-account property
    e.g., freezing a Parent VASP will not effect the status any of its child
    accounts and vice versa.


    ## Events
    Successful execution of this transaction will emit a `AccountFreezing::FreezeAccountEvent` on
    the `freeze_event_handle` held in the `AccountFreezing::FreezeEventsHolder` resource published
    under `0xA550C18` with the `frozen_address` being the `to_freeze_account`.

    # Parameters
    | Name                | Type      | Description                                                                                               |
    | ------              | ------    | -------------                                                                                             |
    | `tc_account`        | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account. |
    | `sliding_nonce`     | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                |
    | `to_freeze_account` | `address` | The account address to be frozen.                                                                         |

    # Common Abort Conditions
    | Error Category             | Error Reason                                 | Description                                                                                |
    | ----------------           | --------------                               | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`               | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`               | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`               | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`      | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`        | The sending account is not the Treasury Compliance account.                                |
    | `Errors::REQUIRES_ROLE`    | `Roles::ETREASURY_COMPLIANCE`                | The sending account is not the Treasury Compliance account.                                |
    | `Errors::INVALID_ARGUMENT` | `AccountFreezing::ECANNOT_FREEZE_TC`         | `to_freeze_account` was the Treasury Compliance account (`0xB1E55ED`).                     |
    | `Errors::INVALID_ARGUMENT` | `AccountFreezing::ECANNOT_FREEZE_DIEM_ROOT` | `to_freeze_account` was the Diem Root account (`0xA550C18`).                              |

    # Related Scripts
    * `Script::unfreeze_account`
    """

    sliding_nonce: st.uint64
    to_freeze_account: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__PeerToPeerWithMetadata(ScriptCall):
    """# Summary
    Transfers a given number of coins in a specified currency from one account to another.

    Transfers over a specified amount defined on-chain that are between two different VASPs, or
    other accounts that have opted-in will be subject to on-chain checks to ensure the receiver has
    agreed to receive the coins.  This transaction can be sent by any account that can hold a
    balance, and to any account that can hold a balance. Both accounts must hold balances in the
    currency being transacted.

    # Technical Description

    Transfers `amount` coins of type `Currency` from `payer` to `payee` with (optional) associated
    `metadata` and an (optional) `metadata_signature` on the message
    `metadata` | `Signer::address_of(payer)` | `amount` | `DualAttestation::DOMAIN_SEPARATOR`.
    The `metadata` and `metadata_signature` parameters are only required if `amount` >=
    `DualAttestation::get_cur_microdiem_limit` XDX and `payer` and `payee` are distinct VASPs.
    However, a transaction sender can opt in to dual attestation even when it is not required
    (e.g., a DesignatedDealer -> VASP payment) by providing a non-empty `metadata_signature`.
    Standardized `metadata` BCS format can be found in `diem_types::transaction::metadata::Metadata`.

    ## Events
    Successful execution of this script emits two events:
    * A `DiemAccount::SentPaymentEvent` on `payer`'s `DiemAccount::DiemAccount` `sent_events` handle; and
    * A `DiemAccount::ReceivedPaymentEvent` on `payee`'s `DiemAccount::DiemAccount` `received_events` handle.

    # Parameters
    | Name                 | Type         | Description                                                                                                                  |
    | ------               | ------       | -------------                                                                                                                |
    | `Currency`           | Type         | The Move type for the `Currency` being sent in this transaction. `Currency` must be an already-registered currency on-chain. |
    | `payer`              | `&signer`    | The signer reference of the sending account that coins are being transferred from.                                           |
    | `payee`              | `address`    | The address of the account the coins are being transferred to.                                                               |
    | `metadata`           | `vector<u8>` | Optional metadata about this payment.                                                                                        |
    | `metadata_signature` | `vector<u8>` | Optional signature over `metadata` and payment information. See                                                              |

    # Common Abort Conditions
    | Error Category             | Error Reason                                     | Description                                                                                                                         |
    | ----------------           | --------------                                   | -------------                                                                                                                       |
    | `Errors::NOT_PUBLISHED`    | `DiemAccount::EPAYER_DOESNT_HOLD_CURRENCY`      | `payer` doesn't hold a balance in `Currency`.                                                                                       |
    | `Errors::LIMIT_EXCEEDED`   | `DiemAccount::EINSUFFICIENT_BALANCE`            | `amount` is greater than `payer`'s balance in `Currency`.                                                                           |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::ECOIN_DEPOSIT_IS_ZERO`            | `amount` is zero.                                                                                                                   |
    | `Errors::NOT_PUBLISHED`    | `DiemAccount::EPAYEE_DOES_NOT_EXIST`            | No account exists at the `payee` address.                                                                                           |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` | An account exists at `payee`, but it does not accept payments in `Currency`.                                                        |
    | `Errors::INVALID_STATE`    | `AccountFreezing::EACCOUNT_FROZEN`               | The `payee` account is frozen.                                                                                                      |
    | `Errors::INVALID_ARGUMENT` | `DualAttestation::EMALFORMED_METADATA_SIGNATURE` | `metadata_signature` is not 64 bytes.                                                                                               |
    | `Errors::INVALID_ARGUMENT` | `DualAttestation::EINVALID_METADATA_SIGNATURE`   | `metadata_signature` does not verify on the against the `payee'`s `DualAttestation::Credential` `compliance_public_key` public key. |
    | `Errors::LIMIT_EXCEEDED`   | `DiemAccount::EWITHDRAWAL_EXCEEDS_LIMITS`       | `payer` has exceeded its daily withdrawal limits for the backing coins of XDX.                                                      |
    | `Errors::LIMIT_EXCEEDED`   | `DiemAccount::EDEPOSIT_EXCEEDS_LIMITS`          | `payee` has exceeded its daily deposit limits for XDX.                                                                              |

    # Related Scripts
    * `Script::create_child_vasp_account`
    * `Script::create_parent_vasp_account`
    * `Script::add_currency_to_account`
    """

    currency: diem_types.TypeTag
    payee: diem_types.AccountAddress
    amount: st.uint64
    metadata: bytes
    metadata_signature: bytes


@dataclass(frozen=True)
class ScriptCall__Preburn(ScriptCall):
    """# Summary
    Moves a specified number of coins in a given currency from the account's
    balance to its preburn area after which the coins may be burned.

    This
    transaction may be sent by any account that holds a balance and preburn area
    in the specified currency.

    # Technical Description
    Moves the specified `amount` of coins in `Token` currency from the sending `account`'s
    `DiemAccount::Balance<Token>` to the `Diem::Preburn<Token>` published under the same
    `account`. `account` must have both of these resources published under it at the start of this
    transaction in order for it to execute successfully.

    ## Events
    Successful execution of this script emits two events:
    * `DiemAccount::SentPaymentEvent ` on `account`'s `DiemAccount::DiemAccount` `sent_events`
    handle with the `payee` and `payer` fields being `account`'s address; and
    * A `Diem::PreburnEvent` with `Token`'s currency code on the
    `Diem::CurrencyInfo<Token`'s `preburn_events` handle for `Token` and with
    `preburn_address` set to `account`'s address.

    # Parameters
    | Name      | Type      | Description                                                                                                                      |
    | ------    | ------    | -------------                                                                                                                    |
    | `Token`   | Type      | The Move type for the `Token` currency being moved to the preburn area. `Token` must be an already-registered currency on-chain. |
    | `account` | `&signer` | The signer reference of the sending account.                                                                                     |
    | `amount`  | `u64`     | The amount in `Token` to be moved to the preburn area.                                                                           |

    # Common Abort Conditions
    | Error Category           | Error Reason                                             | Description                                                                             |
    | ----------------         | --------------                                           | -------------                                                                           |
    | `Errors::NOT_PUBLISHED`  | `Diem::ECURRENCY_INFO`                                  | The `Token` is not a registered currency on-chain.                                      |
    | `Errors::INVALID_STATE`  | `DiemAccount::EWITHDRAWAL_CAPABILITY_ALREADY_EXTRACTED` | The withdrawal capability for `account` has already been extracted.                     |
    | `Errors::LIMIT_EXCEEDED` | `DiemAccount::EINSUFFICIENT_BALANCE`                    | `amount` is greater than `payer`'s balance in `Token`.                                  |
    | `Errors::NOT_PUBLISHED`  | `DiemAccount::EPAYER_DOESNT_HOLD_CURRENCY`              | `account` doesn't hold a balance in `Token`.                                            |
    | `Errors::NOT_PUBLISHED`  | `Diem::EPREBURN`                                        | `account` doesn't have a `Diem::Preburn<Token>` resource published under it.           |
    | `Errors::INVALID_STATE`  | `Diem::EPREBURN_OCCUPIED`                               | The `value` field in the `Diem::Preburn<Token>` resource under the sender is non-zero. |
    | `Errors::NOT_PUBLISHED`  | `Roles::EROLE_ID`                                        | The `account` did not have a role assigned to it.                                       |
    | `Errors::REQUIRES_ROLE`  | `Roles::EDESIGNATED_DEALER`                              | The `account` did not have the role of DesignatedDealer.                                |

    # Related Scripts
    * `Script::cancel_burn`
    * `Script::burn`
    * `Script::burn_txn_fees`
    """

    token: diem_types.TypeTag
    amount: st.uint64


@dataclass(frozen=True)
class ScriptCall__PublishSharedEd25519PublicKey(ScriptCall):
    """# Summary
    Rotates the authentication key of the sending account to the
    newly-specified public key and publishes a new shared authentication key
    under the sender's account.

    Any account can send this transaction.

    # Technical Description
    Rotates the authentication key of the sending account to `public_key`,
    and publishes a `SharedEd25519PublicKey::SharedEd25519PublicKey` resource
    containing the 32-byte ed25519 `public_key` and the `DiemAccount::KeyRotationCapability` for
    `account` under `account`.

    # Parameters
    | Name         | Type         | Description                                                                               |
    | ------       | ------       | -------------                                                                             |
    | `account`    | `&signer`    | The signer reference of the sending account of the transaction.                           |
    | `public_key` | `vector<u8>` | 32-byte Ed25519 public key for `account`' authentication key to be rotated to and stored. |

    # Common Abort Conditions
    | Error Category              | Error Reason                                               | Description                                                                                         |
    | ----------------            | --------------                                             | -------------                                                                                       |
    | `Errors::INVALID_STATE`     | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability` resource.       |
    | `Errors::ALREADY_PUBLISHED` | `SharedEd25519PublicKey::ESHARED_KEY`                      | The `SharedEd25519PublicKey::SharedEd25519PublicKey` resource is already published under `account`. |
    | `Errors::INVALID_ARGUMENT`  | `SharedEd25519PublicKey::EMALFORMED_PUBLIC_KEY`            | `public_key` is an invalid ed25519 public key.                                                      |

    # Related Scripts
    * `Script::rotate_shared_ed25519_public_key`
    """

    public_key: bytes


@dataclass(frozen=True)
class ScriptCall__RegisterValidatorConfig(ScriptCall):
    """# Summary
    Updates a validator's configuration.

    This does not reconfigure the system and will not update
    the configuration in the validator set that is seen by other validators in the network. Can
    only be successfully sent by a Validator Operator account that is already registered with a
    validator.

    # Technical Description
    This updates the fields with corresponding names held in the `ValidatorConfig::ValidatorConfig`
    config resource held under `validator_account`. It does not emit a `DiemConfig::NewEpochEvent`
    so the copy of this config held in the validator set will not be updated, and the changes are
    only "locally" under the `validator_account` account address.

    # Parameters
    | Name                          | Type         | Description                                                                                                                  |
    | ------                        | ------       | -------------                                                                                                                |
    | `validator_operator_account`  | `&signer`    | Signer reference of the sending account. Must be the registered validator operator for the validator at `validator_address`. |
    | `validator_account`           | `address`    | The address of the validator's `ValidatorConfig::ValidatorConfig` resource being updated.                                    |
    | `consensus_pubkey`            | `vector<u8>` | New Ed25519 public key to be used in the updated `ValidatorConfig::ValidatorConfig`.                                         |
    | `validator_network_addresses` | `vector<u8>` | New set of `validator_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                       |
    | `fullnode_network_addresses`  | `vector<u8>` | New set of `fullnode_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                        |

    # Common Abort Conditions
    | Error Category             | Error Reason                                   | Description                                                                                           |
    | ----------------           | --------------                                 | -------------                                                                                         |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`           | `validator_address` does not have a `ValidatorConfig::ValidatorConfig` resource published under it.   |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_TRANSACTION_SENDER` | `validator_operator_account` is not the registered operator for the validator at `validator_address`. |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_CONSENSUS_KEY`      | `consensus_pubkey` is not a valid ed25519 public key.                                                 |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::add_validator_and_reconfigure`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """

    validator_account: diem_types.AccountAddress
    consensus_pubkey: bytes
    validator_network_addresses: bytes
    fullnode_network_addresses: bytes


@dataclass(frozen=True)
class ScriptCall__RemoveValidatorAndReconfigure(ScriptCall):
    """# Summary
    This script removes a validator account from the validator set, and triggers a reconfiguration
    of the system to remove the validator from the system.

    This transaction can only be
    successfully called by the Diem Root account.

    # Technical Description
    This script removes the account at `validator_address` from the validator set. This transaction
    emits a `DiemConfig::NewEpochEvent` event. Once the reconfiguration triggered by this event
    has been performed, the account at `validator_address` is no longer considered to be a
    validator in the network. This transaction will fail if the validator at `validator_address`
    is not in the validator set.

    # Parameters
    | Name                | Type         | Description                                                                                                                        |
    | ------              | ------       | -------------                                                                                                                      |
    | `dr_account`        | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer.                                    |
    | `sliding_nonce`     | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                         |
    | `validator_name`    | `vector<u8>` | ASCII-encoded human name for the validator. Must match the human name in the `ValidatorConfig::ValidatorConfig` for the validator. |
    | `validator_address` | `address`    | The validator account address to be removed from the validator set.                                                                |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                     |
    | ----------------           | --------------                          | -------------                                                                                   |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `dr_account`.                                  |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.      |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                                   |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                               |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | The sending account is not the Diem Root account or Treasury Compliance account                |
    | 0                          | 0                                       | The provided `validator_name` does not match the already-recorded human name for the validator. |
    | `Errors::INVALID_ARGUMENT` | `DiemSystem::ENOT_AN_ACTIVE_VALIDATOR` | The validator to be removed is not in the validator set.                                        |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`            | The sending account is not the Diem Root account.                                              |
    | `Errors::REQUIRES_ROLE`    | `Roles::EDIEM_ROOT`                    | The sending account is not the Diem Root account.                                              |
    | `Errors::INVALID_STATE`    | `DiemConfig::EINVALID_BLOCK_TIME`      | An invalid time value was encountered in reconfiguration. Unlikely to occur.                    |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::add_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """

    sliding_nonce: st.uint64
    validator_name: bytes
    validator_address: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__RotateAuthenticationKey(ScriptCall):
    """# Summary
    Rotates the transaction sender's authentication key to the supplied new authentication key.

    May
    be sent by any account.

    # Technical Description
    Rotate the `account`'s `DiemAccount::DiemAccount` `authentication_key` field to `new_key`.
    `new_key` must be a valid ed25519 public key, and `account` must not have previously delegated
    its `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name      | Type         | Description                                                 |
    | ------    | ------       | -------------                                               |
    | `account` | `&signer`    | Signer reference of the sending account of the transaction. |
    | `new_key` | `vector<u8>` | New ed25519 public key to be used for `account`.            |

    # Common Abort Conditions
    | Error Category             | Error Reason                                               | Description                                                                              |
    | ----------------           | --------------                                             | -------------                                                                            |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.     |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`              | `new_key` was an invalid length.                                                         |

    # Related Scripts
    * `Script::rotate_authentication_key_with_nonce`
    * `Script::rotate_authentication_key_with_nonce_admin`
    * `Script::rotate_authentication_key_with_recovery_address`
    """

    new_key: bytes


@dataclass(frozen=True)
class ScriptCall__RotateAuthenticationKeyWithNonce(ScriptCall):
    """# Summary
    Rotates the sender's authentication key to the supplied new authentication key.

    May be sent by
    any account that has a sliding nonce resource published under it (usually this is Treasury
    Compliance or Diem Root accounts).

    # Technical Description
    Rotates the `account`'s `DiemAccount::DiemAccount` `authentication_key` field to `new_key`.
    `new_key` must be a valid ed25519 public key, and `account` must not have previously delegated
    its `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name            | Type         | Description                                                                |
    | ------          | ------       | -------------                                                              |
    | `account`       | `&signer`    | Signer reference of the sending account of the transaction.                |
    | `sliding_nonce` | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction. |
    | `new_key`       | `vector<u8>` | New ed25519 public key to be used for `account`.                           |

    # Common Abort Conditions
    | Error Category             | Error Reason                                               | Description                                                                                |
    | ----------------           | --------------                                             | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                             | A `SlidingNonce` resource is not published under `account`.                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                             | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                             | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`                    | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.       |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`              | `new_key` was an invalid length.                                                           |

    # Related Scripts
    * `Script::rotate_authentication_key`
    * `Script::rotate_authentication_key_with_nonce_admin`
    * `Script::rotate_authentication_key_with_recovery_address`
    """

    sliding_nonce: st.uint64
    new_key: bytes


@dataclass(frozen=True)
class ScriptCall__RotateAuthenticationKeyWithNonceAdmin(ScriptCall):
    """# Summary
    Rotates the specified account's authentication key to the supplied new authentication key.

    May
    only be sent by the Diem Root account as a write set transaction.

    # Technical Description
    Rotate the `account`'s `DiemAccount::DiemAccount` `authentication_key` field to `new_key`.
    `new_key` must be a valid ed25519 public key, and `account` must not have previously delegated
    its `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name            | Type         | Description                                                                                                  |
    | ------          | ------       | -------------                                                                                                |
    | `dr_account`    | `&signer`    | The signer reference of the sending account of the write set transaction. May only be the Diem Root signer. |
    | `account`       | `&signer`    | Signer reference of account specified in the `execute_as` field of the write set transaction.                |
    | `sliding_nonce` | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction for Diem Root.                    |
    | `new_key`       | `vector<u8>` | New ed25519 public key to be used for `account`.                                                             |

    # Common Abort Conditions
    | Error Category             | Error Reason                                               | Description                                                                                                |
    | ----------------           | --------------                                             | -------------                                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                             | A `SlidingNonce` resource is not published under `dr_account`.                                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                             | The `sliding_nonce` in `dr_account` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                             | The `sliding_nonce` in `dr_account` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`                    | The `sliding_nonce` in` dr_account` has been previously recorded.                                          |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.                       |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`              | `new_key` was an invalid length.                                                                           |

    # Related Scripts
    * `Script::rotate_authentication_key`
    * `Script::rotate_authentication_key_with_nonce`
    * `Script::rotate_authentication_key_with_recovery_address`
    """

    sliding_nonce: st.uint64
    new_key: bytes


@dataclass(frozen=True)
class ScriptCall__RotateAuthenticationKeyWithRecoveryAddress(ScriptCall):
    """# Summary
    Rotates the authentication key of a specified account that is part of a recovery address to a
    new authentication key.

    Only used for accounts that are part of a recovery address (see
    `Script::add_recovery_rotation_capability` for account restrictions).

    # Technical Description
    Rotates the authentication key of the `to_recover` account to `new_key` using the
    `DiemAccount::KeyRotationCapability` stored in the `RecoveryAddress::RecoveryAddress` resource
    published under `recovery_address`. This transaction can be sent either by the `to_recover`
    account, or by the account where the `RecoveryAddress::RecoveryAddress` resource is published
    that contains `to_recover`'s `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name               | Type         | Description                                                                                                                    |
    | ------             | ------       | -------------                                                                                                                  |
    | `account`          | `&signer`    | Signer reference of the sending account of the transaction.                                                                    |
    | `recovery_address` | `address`    | Address where `RecoveryAddress::RecoveryAddress` that holds `to_recover`'s `DiemAccount::KeyRotationCapability` is published. |
    | `to_recover`       | `address`    | The address of the account whose authentication key will be updated.                                                           |
    | `new_key`          | `vector<u8>` | New ed25519 public key to be used for the account at the `to_recover` address.                                                 |

    # Common Abort Conditions
    | Error Category             | Error Reason                                  | Description                                                                                                                                          |
    | ----------------           | --------------                                | -------------                                                                                                                                        |
    | `Errors::NOT_PUBLISHED`    | `RecoveryAddress::ERECOVERY_ADDRESS`          | `recovery_address` does not have a `RecoveryAddress::RecoveryAddress` resource published under it.                                                   |
    | `Errors::INVALID_ARGUMENT` | `RecoveryAddress::ECANNOT_ROTATE_KEY`         | The address of `account` is not `recovery_address` or `to_recover`.                                                                                  |
    | `Errors::INVALID_ARGUMENT` | `RecoveryAddress::EACCOUNT_NOT_RECOVERABLE`   | `to_recover`'s `DiemAccount::KeyRotationCapability`  is not in the `RecoveryAddress::RecoveryAddress`  resource published under `recovery_address`. |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY` | `new_key` was an invalid length.                                                                                                                     |

    # Related Scripts
    * `Script::rotate_authentication_key`
    * `Script::rotate_authentication_key_with_nonce`
    * `Script::rotate_authentication_key_with_nonce_admin`
    """

    recovery_address: diem_types.AccountAddress
    to_recover: diem_types.AccountAddress
    new_key: bytes


@dataclass(frozen=True)
class ScriptCall__RotateDualAttestationInfo(ScriptCall):
    """# Summary
    Updates the url used for off-chain communication, and the public key used to verify dual
    attestation on-chain.

    Transaction can be sent by any account that has dual attestation
    information published under it. In practice the only such accounts are Designated Dealers and
    Parent VASPs.

    # Technical Description
    Updates the `base_url` and `compliance_public_key` fields of the `DualAttestation::Credential`
    resource published under `account`. The `new_key` must be a valid ed25519 public key.

    ## Events
    Successful execution of this transaction emits two events:
    * A `DualAttestation::ComplianceKeyRotationEvent` containing the new compliance public key, and
    the blockchain time at which the key was updated emitted on the `DualAttestation::Credential`
    `compliance_key_rotation_events` handle published under `account`; and
    * A `DualAttestation::BaseUrlRotationEvent` containing the new base url to be used for
    off-chain communication, and the blockchain time at which the url was updated emitted on the
    `DualAttestation::Credential` `base_url_rotation_events` handle published under `account`.

    # Parameters
    | Name      | Type         | Description                                                               |
    | ------    | ------       | -------------                                                             |
    | `account` | `&signer`    | Signer reference of the sending account of the transaction.               |
    | `new_url` | `vector<u8>` | ASCII-encoded url to be used for off-chain communication with `account`.  |
    | `new_key` | `vector<u8>` | New ed25519 public key to be used for on-chain dual attestation checking. |

    # Common Abort Conditions
    | Error Category             | Error Reason                           | Description                                                                |
    | ----------------           | --------------                         | -------------                                                              |
    | `Errors::NOT_PUBLISHED`    | `DualAttestation::ECREDENTIAL`         | A `DualAttestation::Credential` resource is not published under `account`. |
    | `Errors::INVALID_ARGUMENT` | `DualAttestation::EINVALID_PUBLIC_KEY` | `new_key` is not a valid ed25519 public key.                               |

    # Related Scripts
    * `Script::create_parent_vasp_account`
    * `Script::create_designated_dealer`
    * `Script::rotate_dual_attestation_info`
    """

    new_url: bytes
    new_key: bytes


@dataclass(frozen=True)
class ScriptCall__RotateSharedEd25519PublicKey(ScriptCall):
    """# Summary
    Rotates the authentication key in a `SharedEd25519PublicKey`.

    This transaction can be sent by
    any account that has previously published a shared ed25519 public key using
    `Script::publish_shared_ed25519_public_key`.

    # Technical Description
    This first rotates the public key stored in `account`'s
    `SharedEd25519PublicKey::SharedEd25519PublicKey` resource to `public_key`, after which it
    rotates the authentication key using the capability stored in `account`'s
    `SharedEd25519PublicKey::SharedEd25519PublicKey` to a new value derived from `public_key`

    # Parameters
    | Name         | Type         | Description                                                     |
    | ------       | ------       | -------------                                                   |
    | `account`    | `&signer`    | The signer reference of the sending account of the transaction. |
    | `public_key` | `vector<u8>` | 32-byte Ed25519 public key.                                     |

    # Common Abort Conditions
    | Error Category             | Error Reason                                    | Description                                                                                   |
    | ----------------           | --------------                                  | -------------                                                                                 |
    | `Errors::NOT_PUBLISHED`    | `SharedEd25519PublicKey::ESHARED_KEY`           | A `SharedEd25519PublicKey::SharedEd25519PublicKey` resource is not published under `account`. |
    | `Errors::INVALID_ARGUMENT` | `SharedEd25519PublicKey::EMALFORMED_PUBLIC_KEY` | `public_key` is an invalid ed25519 public key.                                                |

    # Related Scripts
    * `Script::publish_shared_ed25519_public_key`
    """

    public_key: bytes


@dataclass(frozen=True)
class ScriptCall__SetValidatorConfigAndReconfigure(ScriptCall):
    """# Summary
    Updates a validator's configuration, and triggers a reconfiguration of the system to update the
    validator set with this new validator configuration.

    Can only be successfully sent by a
    Validator Operator account that is already registered with a validator.

    # Technical Description
    This updates the fields with corresponding names held in the `ValidatorConfig::ValidatorConfig`
    config resource held under `validator_account`. It then emits a `DiemConfig::NewEpochEvent` to
    trigger a reconfiguration of the system.  This reconfiguration will update the validator set
    on-chain with the updated `ValidatorConfig::ValidatorConfig`.

    # Parameters
    | Name                          | Type         | Description                                                                                                                  |
    | ------                        | ------       | -------------                                                                                                                |
    | `validator_operator_account`  | `&signer`    | Signer reference of the sending account. Must be the registered validator operator for the validator at `validator_address`. |
    | `validator_account`           | `address`    | The address of the validator's `ValidatorConfig::ValidatorConfig` resource being updated.                                    |
    | `consensus_pubkey`            | `vector<u8>` | New Ed25519 public key to be used in the updated `ValidatorConfig::ValidatorConfig`.                                         |
    | `validator_network_addresses` | `vector<u8>` | New set of `validator_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                       |
    | `fullnode_network_addresses`  | `vector<u8>` | New set of `fullnode_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                        |

    # Common Abort Conditions
    | Error Category             | Error Reason                                   | Description                                                                                           |
    | ----------------           | --------------                                 | -------------                                                                                         |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`           | `validator_address` does not have a `ValidatorConfig::ValidatorConfig` resource published under it.   |
    | `Errors::REQUIRES_ROLE`    | `Roles::EVALIDATOR_OPERATOR`                   | `validator_operator_account` does not have a Validator Operator role.                                 |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_TRANSACTION_SENDER` | `validator_operator_account` is not the registered operator for the validator at `validator_address`. |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_CONSENSUS_KEY`      | `consensus_pubkey` is not a valid ed25519 public key.                                                 |
    | `Errors::INVALID_STATE`    | `DiemConfig::EINVALID_BLOCK_TIME`             | An invalid time value was encountered in reconfiguration. Unlikely to occur.                          |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::add_validator_and_reconfigure`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::register_validator_config`
    """

    validator_account: diem_types.AccountAddress
    consensus_pubkey: bytes
    validator_network_addresses: bytes
    fullnode_network_addresses: bytes


@dataclass(frozen=True)
class ScriptCall__SetValidatorOperator(ScriptCall):
    """# Summary
    Sets the validator operator for a validator in the validator's configuration resource "locally"
    and does not reconfigure the system.

    Changes from this transaction will not picked up by the
    system until a reconfiguration of the system is triggered. May only be sent by an account with
    Validator role.

    # Technical Description
    Sets the account at `operator_account` address and with the specified `human_name` as an
    operator for the sending validator account. The account at `operator_account` address must have
    a Validator Operator role and have a `ValidatorOperatorConfig::ValidatorOperatorConfig`
    resource published under it. The sending `account` must be a Validator and have a
    `ValidatorConfig::ValidatorConfig` resource published under it. This script does not emit a
    `DiemConfig::NewEpochEvent` and no reconfiguration of the system is initiated by this script.

    # Parameters
    | Name               | Type         | Description                                                                                  |
    | ------             | ------       | -------------                                                                                |
    | `account`          | `&signer`    | The signer reference of the sending account of the transaction.                              |
    | `operator_name`    | `vector<u8>` | Validator operator's human name.                                                             |
    | `operator_account` | `address`    | Address of the validator operator account to be added as the `account` validator's operator. |

    # Common Abort Conditions
    | Error Category             | Error Reason                                          | Description                                                                                                                                                  |
    | ----------------           | --------------                                        | -------------                                                                                                                                                |
    | `Errors::NOT_PUBLISHED`    | `ValidatorOperatorConfig::EVALIDATOR_OPERATOR_CONFIG` | The `ValidatorOperatorConfig::ValidatorOperatorConfig` resource is not published under `operator_account`.                                                   |
    | 0                          | 0                                                     | The `human_name` field of the `ValidatorOperatorConfig::ValidatorOperatorConfig` resource under `operator_account` does not match the provided `human_name`. |
    | `Errors::REQUIRES_ROLE`    | `Roles::EVALIDATOR`                                   | `account` does not have a Validator account role.                                                                                                            |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::ENOT_A_VALIDATOR_OPERATOR`          | The account at `operator_account` does not have a `ValidatorOperatorConfig::ValidatorOperatorConfig` resource.                                               |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`                  | A `ValidatorConfig::ValidatorConfig` is not published under `account`.                                                                                       |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::add_validator_and_reconfigure`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """

    operator_name: bytes
    operator_account: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__SetValidatorOperatorWithNonceAdmin(ScriptCall):
    """# Summary
    Sets the validator operator for a validator in the validator's configuration resource "locally"
    and does not reconfigure the system.

    Changes from this transaction will not picked up by the
    system until a reconfiguration of the system is triggered. May only be sent by the Diem Root
    account as a write set transaction.

    # Technical Description
    Sets the account at `operator_account` address and with the specified `human_name` as an
    operator for the validator `account`. The account at `operator_account` address must have a
    Validator Operator role and have a `ValidatorOperatorConfig::ValidatorOperatorConfig` resource
    published under it. The account represented by the `account` signer must be a Validator and
    have a `ValidatorConfig::ValidatorConfig` resource published under it. No reconfiguration of
    the system is initiated by this script.

    # Parameters
    | Name               | Type         | Description                                                                                                  |
    | ------             | ------       | -------------                                                                                                |
    | `dr_account`       | `&signer`    | The signer reference of the sending account of the write set transaction. May only be the Diem Root signer. |
    | `account`          | `&signer`    | Signer reference of account specified in the `execute_as` field of the write set transaction.                |
    | `sliding_nonce`    | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction for Diem Root.                    |
    | `operator_name`    | `vector<u8>` | Validator operator's human name.                                                                             |
    | `operator_account` | `address`    | Address of the validator operator account to be added as the `account` validator's operator.                 |

    # Common Abort Conditions
    | Error Category             | Error Reason                                          | Description                                                                                                                                                  |
    | ----------------           | --------------                                        | -------------                                                                                                                                                |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                        | A `SlidingNonce` resource is not published under `dr_account`.                                                                                               |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                        | The `sliding_nonce` in `dr_account` is too old and it's impossible to determine if it's duplicated or not.                                                   |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                        | The `sliding_nonce` in `dr_account` is too far in the future.                                                                                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`               | The `sliding_nonce` in` dr_account` has been previously recorded.                                                                                            |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                        | The sending account is not the Diem Root account or Treasury Compliance account                                                                             |
    | `Errors::NOT_PUBLISHED`    | `ValidatorOperatorConfig::EVALIDATOR_OPERATOR_CONFIG` | The `ValidatorOperatorConfig::ValidatorOperatorConfig` resource is not published under `operator_account`.                                                   |
    | 0                          | 0                                                     | The `human_name` field of the `ValidatorOperatorConfig::ValidatorOperatorConfig` resource under `operator_account` does not match the provided `human_name`. |
    | `Errors::REQUIRES_ROLE`    | `Roles::EVALIDATOR`                                   | `account` does not have a Validator account role.                                                                                                            |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::ENOT_A_VALIDATOR_OPERATOR`          | The account at `operator_account` does not have a `ValidatorOperatorConfig::ValidatorOperatorConfig` resource.                                               |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`                  | A `ValidatorConfig::ValidatorConfig` is not published under `account`.                                                                                       |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::add_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_config_and_reconfigure`
    """

    sliding_nonce: st.uint64
    operator_name: bytes
    operator_account: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__TieredMint(ScriptCall):
    """# Summary
    Mints a specified number of coins in a currency to a Designated Dealer.

    The sending account
    must be the Treasury Compliance account, and coins can only be minted to a Designated Dealer
    account.

    # Technical Description
    Mints `mint_amount` of coins in the `CoinType` currency to Designated Dealer account at
    `designated_dealer_address`. The `tier_index` parameter specifies which tier should be used to
    check verify the off-chain approval policy, and is based in part on the on-chain tier values
    for the specific Designated Dealer, and the number of `CoinType` coins that have been minted to
    the dealer over the past 24 hours. Every Designated Dealer has 4 tiers for each currency that
    they support. The sending `tc_account` must be the Treasury Compliance account, and the
    receiver an authorized Designated Dealer account.

    ## Events
    Successful execution of the transaction will emit two events:
    * A `Diem::MintEvent` with the amount and currency code minted is emitted on the
    `mint_event_handle` in the stored `Diem::CurrencyInfo<CoinType>` resource stored under
    `0xA550C18`; and
    * A `DesignatedDealer::ReceivedMintEvent` with the amount, currency code, and Designated
    Dealer's address is emitted on the `mint_event_handle` in the stored `DesignatedDealer::Dealer`
    resource published under the `designated_dealer_address`.

    # Parameters
    | Name                        | Type      | Description                                                                                                |
    | ------                      | ------    | -------------                                                                                              |
    | `CoinType`                  | Type      | The Move type for the `CoinType` being minted. `CoinType` must be an already-registered currency on-chain. |
    | `tc_account`                | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.  |
    | `sliding_nonce`             | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                 |
    | `designated_dealer_address` | `address` | The address of the Designated Dealer account being minted to.                                              |
    | `mint_amount`               | `u64`     | The number of coins to be minted.                                                                          |
    | `tier_index`                | `u64`     | The mint tier index to use for the Designated Dealer account.                                              |

    # Common Abort Conditions
    | Error Category                | Error Reason                                 | Description                                                                                                                  |
    | ----------------              | --------------                               | -------------                                                                                                                |
    | `Errors::NOT_PUBLISHED`       | `SlidingNonce::ESLIDING_NONCE`               | A `SlidingNonce` resource is not published under `tc_account`.                                                               |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_OLD`               | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.                                   |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_NEW`               | The `sliding_nonce` is too far in the future.                                                                                |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_ALREADY_RECORDED`      | The `sliding_nonce` has been previously recorded.                                                                            |
    | `Errors::REQUIRES_ADDRESS`    | `CoreAddresses::ETREASURY_COMPLIANCE`        | `tc_account` is not the Treasury Compliance account.                                                                         |
    | `Errors::REQUIRES_ROLE`       | `Roles::ETREASURY_COMPLIANCE`                | `tc_account` is not the Treasury Compliance account.                                                                         |
    | `Errors::INVALID_ARGUMENT`    | `DesignatedDealer::EINVALID_MINT_AMOUNT`     | `mint_amount` is zero.                                                                                                       |
    | `Errors::NOT_PUBLISHED`       | `DesignatedDealer::EDEALER`                  | `DesignatedDealer::Dealer` or `DesignatedDealer::TierInfo<CoinType>` resource does not exist at `designated_dealer_address`. |
    | `Errors::INVALID_ARGUMENT`    | `DesignatedDealer::EINVALID_TIER_INDEX`      | The `tier_index` is out of bounds.                                                                                           |
    | `Errors::INVALID_ARGUMENT`    | `DesignatedDealer::EINVALID_AMOUNT_FOR_TIER` | `mint_amount` exceeds the maximum allowed amount for `tier_index`.                                                           |
    | `Errors::REQUIRES_CAPABILITY` | `Diem::EMINT_CAPABILITY`                    | `tc_account` does not have a `Diem::MintCapability<CoinType>` resource published under it.                                  |
    | `Errors::INVALID_STATE`       | `Diem::EMINTING_NOT_ALLOWED`                | Minting is not currently allowed for `CoinType` coins.                                                                       |
    | `Errors::LIMIT_EXCEEDED`      | `DiemAccount::EDEPOSIT_EXCEEDS_LIMITS`      | The depositing of the funds would exceed the `account`'s account limits.                                                     |

    # Related Scripts
    * `Script::create_designated_dealer`
    * `Script::peer_to_peer_with_metadata`
    * `Script::rotate_dual_attestation_info`
    """

    coin_type: diem_types.TypeTag
    sliding_nonce: st.uint64
    designated_dealer_address: diem_types.AccountAddress
    mint_amount: st.uint64
    tier_index: st.uint64


@dataclass(frozen=True)
class ScriptCall__UnfreezeAccount(ScriptCall):
    """# Summary
    Unfreezes the account at `address`.

    The sending account of this transaction must be the
    Treasury Compliance account. After the successful execution of this transaction transactions
    may be sent from the previously frozen account, and coins may be sent and received.

    # Technical Description
    Sets the `AccountFreezing::FreezingBit` to `false` and emits a
    `AccountFreezing::UnFreezeAccountEvent`. The transaction sender must be the Treasury Compliance
    account. Note that this is a per-account property so unfreezing a Parent VASP will not effect
    the status any of its child accounts and vice versa.

    ## Events
    Successful execution of this script will emit a `AccountFreezing::UnFreezeAccountEvent` with
    the `unfrozen_address` set the `to_unfreeze_account`'s address.

    # Parameters
    | Name                  | Type      | Description                                                                                               |
    | ------                | ------    | -------------                                                                                             |
    | `tc_account`          | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account. |
    | `sliding_nonce`       | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                |
    | `to_unfreeze_account` | `address` | The account address to be frozen.                                                                         |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                |
    | ----------------           | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `account`.                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`   | The sending account is not the Treasury Compliance account.                                |

    # Related Scripts
    * `Script::freeze_account`
    """

    sliding_nonce: st.uint64
    to_unfreeze_account: diem_types.AccountAddress


@dataclass(frozen=True)
class ScriptCall__UpdateDiemVersion(ScriptCall):
    """# Summary
    Updates the Diem major version that is stored on-chain and is used by the VM.

    This
    transaction can only be sent from the Diem Root account.

    # Technical Description
    Updates the `DiemVersion` on-chain config and emits a `DiemConfig::NewEpochEvent` to trigger
    a reconfiguration of the system. The `major` version that is passed in must be strictly greater
    than the current major version held on-chain. The VM reads this information and can use it to
    preserve backwards compatibility with previous major versions of the VM.

    # Parameters
    | Name            | Type      | Description                                                                |
    | ------          | ------    | -------------                                                              |
    | `account`       | `&signer` | Signer reference of the sending account. Must be the Diem Root account.   |
    | `sliding_nonce` | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction. |
    | `major`         | `u64`     | The `major` version of the VM to be used from this transaction on.         |

    # Common Abort Conditions
    | Error Category             | Error Reason                                  | Description                                                                                |
    | ----------------           | --------------                                | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                | A `SlidingNonce` resource is not published under `account`.                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`       | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`                  | `account` is not the Diem Root account.                                                   |
    | `Errors::INVALID_ARGUMENT` | `DiemVersion::EINVALID_MAJOR_VERSION_NUMBER` | `major` is less-than or equal to the current major version stored on-chain.                |
    """

    sliding_nonce: st.uint64
    major: st.uint64


@dataclass(frozen=True)
class ScriptCall__UpdateDualAttestationLimit(ScriptCall):
    """# Summary
    Update the dual attestation limit on-chain.

    Defined in terms of micro-XDX.  The transaction can
    only be sent by the Treasury Compliance account.  After this transaction all inter-VASP
    payments over this limit must be checked for dual attestation.

    # Technical Description
    Updates the `micro_xdx_limit` field of the `DualAttestation::Limit` resource published under
    `0xA550C18`. The amount is set in micro-XDX.

    # Parameters
    | Name                  | Type      | Description                                                                                               |
    | ------                | ------    | -------------                                                                                             |
    | `tc_account`          | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account. |
    | `sliding_nonce`       | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                |
    | `new_micro_xdx_limit` | `u64`     | The new dual attestation limit to be used on-chain.                                                       |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                |
    | ----------------           | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`   | `tc_account` is not the Treasury Compliance account.                                       |

    # Related Scripts
    * `Script::update_exchange_rate`
    * `Script::update_minting_ability`
    """

    sliding_nonce: st.uint64
    new_micro_xdx_limit: st.uint64


@dataclass(frozen=True)
class ScriptCall__UpdateExchangeRate(ScriptCall):
    """# Summary
    Update the rough on-chain exchange rate between a specified currency and XDX (as a conversion
    to micro-XDX).

    The transaction can only be sent by the Treasury Compliance account. After this
    transaction the updated exchange rate will be used for normalization of gas prices, and for
    dual attestation checking.

    # Technical Description
    Updates the on-chain exchange rate from the given `Currency` to micro-XDX.  The exchange rate
    is given by `new_exchange_rate_numerator/new_exchange_rate_denominator`.

    # Parameters
    | Name                            | Type      | Description                                                                                                                        |
    | ------                          | ------    | -------------                                                                                                                      |
    | `Currency`                      | Type      | The Move type for the `Currency` whose exchange rate is being updated. `Currency` must be an already-registered currency on-chain. |
    | `tc_account`                    | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                          |
    | `sliding_nonce`                 | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for the transaction.                                                          |
    | `new_exchange_rate_numerator`   | `u64`     | The numerator for the new to micro-XDX exchange rate for `Currency`.                                                               |
    | `new_exchange_rate_denominator` | `u64`     | The denominator for the new to micro-XDX exchange rate for `Currency`.                                                             |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                |
    | ----------------           | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`   | `tc_account` is not the Treasury Compliance account.                                       |
    | `Errors::REQUIRES_ROLE`    | `Roles::ETREASURY_COMPLIANCE`           | `tc_account` is not the Treasury Compliance account.                                       |
    | `Errors::INVALID_ARGUMENT` | `FixedPoint32::EDENOMINATOR`            | `new_exchange_rate_denominator` is zero.                                                   |
    | `Errors::INVALID_ARGUMENT` | `FixedPoint32::ERATIO_OUT_OF_RANGE`     | The quotient is unrepresentable as a `FixedPoint32`.                                       |
    | `Errors::LIMIT_EXCEEDED`   | `FixedPoint32::ERATIO_OUT_OF_RANGE`     | The quotient is unrepresentable as a `FixedPoint32`.                                       |

    # Related Scripts
    * `Script::update_dual_attestation_limit`
    * `Script::update_minting_ability`
    """

    currency: diem_types.TypeTag
    sliding_nonce: st.uint64
    new_exchange_rate_numerator: st.uint64
    new_exchange_rate_denominator: st.uint64


@dataclass(frozen=True)
class ScriptCall__UpdateMintingAbility(ScriptCall):
    """# Summary
    Script to allow or disallow minting of new coins in a specified currency.

    This transaction can
    only be sent by the Treasury Compliance account.  Turning minting off for a currency will have
    no effect on coins already in circulation, and coins may still be removed from the system.

    # Technical Description
    This transaction sets the `can_mint` field of the `Diem::CurrencyInfo<Currency>` resource
    published under `0xA550C18` to the value of `allow_minting`. Minting of coins if allowed if
    this field is set to `true` and minting of new coins in `Currency` is disallowed otherwise.
    This transaction needs to be sent by the Treasury Compliance account.

    # Parameters
    | Name            | Type      | Description                                                                                                                          |
    | ------          | ------    | -------------                                                                                                                        |
    | `Currency`      | Type      | The Move type for the `Currency` whose minting ability is being updated. `Currency` must be an already-registered currency on-chain. |
    | `account`       | `&signer` | Signer reference of the sending account. Must be the Diem Root account.                                                             |
    | `allow_minting` | `bool`    | Whether to allow minting of new coins in `Currency`.                                                                                 |

    # Common Abort Conditions
    | Error Category             | Error Reason                          | Description                                          |
    | ----------------           | --------------                        | -------------                                        |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE` | `tc_account` is not the Treasury Compliance account. |
    | `Errors::NOT_PUBLISHED`    | `Diem::ECURRENCY_INFO`               | `Currency` is not a registered currency on-chain.    |

    # Related Scripts
    * `Script::update_dual_attestation_limit`
    * `Script::update_exchange_rate`
    """

    currency: diem_types.TypeTag
    allow_minting: bool


from diem.diem_types import (
    Script,
    TypeTag,
    AccountAddress,
    TransactionArgument,
    TransactionArgument__Bool,
    TransactionArgument__U8,
    TransactionArgument__U64,
    TransactionArgument__U128,
    TransactionArgument__Address,
    TransactionArgument__U8Vector,
)


def encode_script(call: ScriptCall) -> Script:
    """Build a Diem `Script` from a structured object `ScriptCall`."""
    helper = SCRIPT_ENCODER_MAP[call.__class__]
    return helper(call)


def decode_script(script: Script) -> ScriptCall:
    """Try to recognize a Diem `Script` and convert it into a structured object `ScriptCall`."""
    helper = SCRIPT_DECODER_MAP.get(script.code)
    if helper is None:
        raise ValueError("Unknown script bytecode")
    return helper(script)


def encode_add_currency_to_account_script(currency: TypeTag) -> Script:
    """# Summary
    Adds a zero `Currency` balance to the sending `account`.

    This will enable `account` to
    send, receive, and hold `Diem::Diem<Currency>` coins. This transaction can be
    successfully sent by any account that is allowed to hold balances
    (e.g., VASP, Designated Dealer).

    # Technical Description
    After the successful execution of this transaction the sending account will have a
    `DiemAccount::Balance<Currency>` resource with zero balance published under it. Only
    accounts that can hold balances can send this transaction, the sending account cannot
    already have a `DiemAccount::Balance<Currency>` published under it.

    # Parameters
    | Name       | Type      | Description                                                                                                                                         |
    | ------     | ------    | -------------                                                                                                                                       |
    | `Currency` | Type      | The Move type for the `Currency` being added to the sending account of the transaction. `Currency` must be an already-registered currency on-chain. |
    | `account`  | `&signer` | The signer of the sending account of the transaction.                                                                                               |

    # Common Abort Conditions
    | Error Category              | Error Reason                             | Description                                                                |
    | ----------------            | --------------                           | -------------                                                              |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                  | The `Currency` is not a registered currency on-chain.                      |
    | `Errors::INVALID_ARGUMENT`  | `DiemAccount::EROLE_CANT_STORE_BALANCE` | The sending `account`'s role does not permit balances.                     |
    | `Errors::ALREADY_PUBLISHED` | `DiemAccount::EADD_EXISTING_CURRENCY`   | A balance for `Currency` is already published under the sending `account`. |

    # Related Scripts
    * `Script::create_child_vasp_account`
    * `Script::create_parent_vasp_account`
    * `Script::peer_to_peer_with_metadata`
    """
    return Script(
        code=ADD_CURRENCY_TO_ACCOUNT_CODE,
        ty_args=[currency],
        args=[],
    )


def encode_add_recovery_rotation_capability_script(recovery_address: AccountAddress) -> Script:
    """# Summary
    Stores the sending accounts ability to rotate its authentication key with a designated recovery
    account.

    Both the sending and recovery accounts need to belong to the same VASP and
    both be VASP accounts. After this transaction both the sending account and the
    specified recovery account can rotate the sender account's authentication key.

    # Technical Description
    Adds the `DiemAccount::KeyRotationCapability` for the sending account
    (`to_recover_account`) to the `RecoveryAddress::RecoveryAddress` resource under
    `recovery_address`. After this transaction has been executed successfully the account at
    `recovery_address` and the `to_recover_account` may rotate the authentication key of
    `to_recover_account` (the sender of this transaction).

    The sending account of this transaction (`to_recover_account`) must not have previously given away its unique key
    rotation capability, and must be a VASP account. The account at `recovery_address`
    must also be a VASP account belonging to the same VASP as the `to_recover_account`.
    Additionally the account at `recovery_address` must have already initialized itself as
    a recovery account address using the `Script::create_recovery_address` transaction script.

    The sending account's (`to_recover_account`) key rotation capability is
    removed in this transaction and stored in the `RecoveryAddress::RecoveryAddress`
    resource stored under the account at `recovery_address`.

    # Parameters
    | Name                 | Type      | Description                                                                                                |
    | ------               | ------    | -------------                                                                                              |
    | `to_recover_account` | `&signer` | The signer reference of the sending account of this transaction.                                           |
    | `recovery_address`   | `address` | The account address where the `to_recover_account`'s `DiemAccount::KeyRotationCapability` will be stored. |

    # Common Abort Conditions
    | Error Category             | Error Reason                                              | Description                                                                                       |
    | ----------------           | --------------                                            | -------------                                                                                     |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `to_recover_account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.    |
    | `Errors::NOT_PUBLISHED`    | `RecoveryAddress::ERECOVERY_ADDRESS`                      | `recovery_address` does not have a `RecoveryAddress` resource published under it.                 |
    | `Errors::INVALID_ARGUMENT` | `RecoveryAddress::EINVALID_KEY_ROTATION_DELEGATION`       | `to_recover_account` and `recovery_address` do not belong to the same VASP.                       |
    | `Errors::LIMIT_EXCEEDED`   | ` RecoveryAddress::EMAX_KEYS_REGISTERED`                  | `RecoveryAddress::MAX_REGISTERED_KEYS` have already been registered with this `recovery_address`. |

    # Related Scripts
    * `Script::create_recovery_address`
    * `Script::rotate_authentication_key_with_recovery_address`
    """
    return Script(
        code=ADD_RECOVERY_ROTATION_CAPABILITY_CODE,
        ty_args=[],
        args=[TransactionArgument__Address(value=recovery_address)],
    )


def encode_add_to_script_allow_list_script(hash: bytes, sliding_nonce: st.uint64) -> Script:
    """# Summary
    Adds a script hash to the transaction allowlist.

    This transaction
    can only be sent by the Diem Root account. Scripts with this hash can be
    sent afterward the successful execution of this script.

    # Technical Description

    The sending account (`dr_account`) must be the Diem Root account. The script allow
    list must not already hold the script `hash` being added. The `sliding_nonce` must be
    a valid nonce for the Diem Root account. After this transaction has executed
    successfully a reconfiguration will be initiated, and the on-chain config
    `DiemTransactionPublishingOption::DiemTransactionPublishingOption`'s
    `script_allow_list` field will contain the new script `hash` and transactions
    with this `hash` can be successfully sent to the network.

    # Parameters
    | Name            | Type         | Description                                                                                     |
    | ------          | ------       | -------------                                                                                   |
    | `dr_account`    | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer. |
    | `hash`          | `vector<u8>` | The hash of the script to be added to the script allowlist.                                     |
    | `sliding_nonce` | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                      |

    # Common Abort Conditions
    | Error Category             | Error Reason                                                           | Description                                                                                |
    | ----------------           | --------------                                                         | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                                         | A `SlidingNonce` resource is not published under `dr_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                                         | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                                         | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`                                | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`                                           | The sending account is not the Diem Root account.                                         |
    | `Errors::REQUIRES_ROLE`    | `Roles::EDIEM_ROOT`                                                   | The sending account is not the Diem Root account.                                         |
    | `Errors::INVALID_ARGUMENT` | `DiemTransactionPublishingOption::EINVALID_SCRIPT_HASH`               | The script `hash` is an invalid length.                                                    |
    | `Errors::INVALID_ARGUMENT` | `DiemTransactionPublishingOption::EALLOWLIST_ALREADY_CONTAINS_SCRIPT` | The on-chain allowlist already contains the script `hash`.                                 |
    """
    return Script(
        code=ADD_TO_SCRIPT_ALLOW_LIST_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=hash), TransactionArgument__U64(value=sliding_nonce)],
    )


def encode_add_validator_and_reconfigure_script(
    sliding_nonce: st.uint64, validator_name: bytes, validator_address: AccountAddress
) -> Script:
    """# Summary
    Adds a validator account to the validator set, and triggers a
    reconfiguration of the system to admit the account to the validator set for the system.

    This
    transaction can only be successfully called by the Diem Root account.

    # Technical Description
    This script adds the account at `validator_address` to the validator set.
    This transaction emits a `DiemConfig::NewEpochEvent` event and triggers a
    reconfiguration. Once the reconfiguration triggered by this script's
    execution has been performed, the account at the `validator_address` is
    considered to be a validator in the network.

    This transaction script will fail if the `validator_address` address is already in the validator set
    or does not have a `ValidatorConfig::ValidatorConfig` resource already published under it.

    # Parameters
    | Name                | Type         | Description                                                                                                                        |
    | ------              | ------       | -------------                                                                                                                      |
    | `dr_account`        | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer.                                    |
    | `sliding_nonce`     | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                         |
    | `validator_name`    | `vector<u8>` | ASCII-encoded human name for the validator. Must match the human name in the `ValidatorConfig::ValidatorConfig` for the validator. |
    | `validator_address` | `address`    | The validator account address to be added to the validator set.                                                                    |

    # Common Abort Conditions
    | Error Category             | Error Reason                                  | Description                                                                                                                               |
    | ----------------           | --------------                                | -------------                                                                                                                             |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                | A `SlidingNonce` resource is not published under `dr_account`.                                                                            |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.                                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                | The `sliding_nonce` is too far in the future.                                                                                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`       | The `sliding_nonce` has been previously recorded.                                                                                         |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`                  | The sending account is not the Diem Root account.                                                                                        |
    | `Errors::REQUIRES_ROLE`    | `Roles::EDIEM_ROOT`                          | The sending account is not the Diem Root account.                                                                                        |
    | 0                          | 0                                             | The provided `validator_name` does not match the already-recorded human name for the validator.                                           |
    | `Errors::INVALID_ARGUMENT` | `DiemSystem::EINVALID_PROSPECTIVE_VALIDATOR` | The validator to be added does not have a `ValidatorConfig::ValidatorConfig` resource published under it, or its `config` field is empty. |
    | `Errors::INVALID_ARGUMENT` | `DiemSystem::EALREADY_A_VALIDATOR`           | The `validator_address` account is already a registered validator.                                                                        |
    | `Errors::INVALID_STATE`    | `DiemConfig::EINVALID_BLOCK_TIME`            | An invalid time value was encountered in reconfiguration. Unlikely to occur.                                                              |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """
    return Script(
        code=ADD_VALIDATOR_AND_RECONFIGURE_CODE,
        ty_args=[],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__U8Vector(value=validator_name),
            TransactionArgument__Address(value=validator_address),
        ],
    )


def encode_burn_script(token: TypeTag, sliding_nonce: st.uint64, preburn_address: AccountAddress) -> Script:
    """# Summary
    Burns all coins held in the preburn resource at the specified
    preburn address and removes them from the system.

    The sending account must
    be the Treasury Compliance account.
    The account that holds the preburn resource will normally be a Designated
    Dealer, but there are no enforced requirements that it be one.

    # Technical Description
    This transaction permanently destroys all the coins of `Token` type
    stored in the `Diem::Preburn<Token>` resource published under the
    `preburn_address` account address.

    This transaction will only succeed if the sending `account` has a
    `Diem::BurnCapability<Token>`, and a `Diem::Preburn<Token>` resource
    exists under `preburn_address`, with a non-zero `to_burn` field. After the successful execution
    of this transaction the `total_value` field in the
    `Diem::CurrencyInfo<Token>` resource published under `0xA550C18` will be
    decremented by the value of the `to_burn` field of the preburn resource
    under `preburn_address` immediately before this transaction, and the
    `to_burn` field of the preburn resource will have a zero value.

    ## Events
    The successful execution of this transaction will emit a `Diem::BurnEvent` on the event handle
    held in the `Diem::CurrencyInfo<Token>` resource's `burn_events` published under
    `0xA550C18`.

    # Parameters
    | Name              | Type      | Description                                                                                                                  |
    | ------            | ------    | -------------                                                                                                                |
    | `Token`           | Type      | The Move type for the `Token` currency being burned. `Token` must be an already-registered currency on-chain.                |
    | `tc_account`      | `&signer` | The signer reference of the sending account of this transaction, must have a burn capability for `Token` published under it. |
    | `sliding_nonce`   | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                   |
    | `preburn_address` | `address` | The address where the coins to-be-burned are currently held.                                                                 |

    # Common Abort Conditions
    | Error Category                | Error Reason                            | Description                                                                                           |
    | ----------------              | --------------                          | -------------                                                                                         |
    | `Errors::NOT_PUBLISHED`       | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `account`.                                           |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.            |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                                         |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                                     |
    | `Errors::REQUIRES_CAPABILITY` | `Diem::EBURN_CAPABILITY`               | The sending `account` does not have a `Diem::BurnCapability<Token>` published under it.              |
    | `Errors::NOT_PUBLISHED`       | `Diem::EPREBURN`                       | The account at `preburn_address` does not have a `Diem::Preburn<Token>` resource published under it. |
    | `Errors::INVALID_STATE`       | `Diem::EPREBURN_EMPTY`                 | The `Diem::Preburn<Token>` resource is empty (has a value of 0).                                     |
    | `Errors::NOT_PUBLISHED`       | `Diem::ECURRENCY_INFO`                 | The specified `Token` is not a registered currency on-chain.                                          |

    # Related Scripts
    * `Script::burn_txn_fees`
    * `Script::cancel_burn`
    * `Script::preburn`
    """
    return Script(
        code=BURN_CODE,
        ty_args=[token],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__Address(value=preburn_address)],
    )


def encode_burn_txn_fees_script(coin_type: TypeTag) -> Script:
    """# Summary
    Burns the transaction fees collected in the `CoinType` currency so that the
    Diem association may reclaim the backing coins off-chain.

    May only be sent
    by the Treasury Compliance account.

    # Technical Description
    Burns the transaction fees collected in `CoinType` so that the
    association may reclaim the backing coins. Once this transaction has executed
    successfully all transaction fees that will have been collected in
    `CoinType` since the last time this script was called with that specific
    currency. Both `balance` and `preburn` fields in the
    `TransactionFee::TransactionFee<CoinType>` resource published under the `0xB1E55ED`
    account address will have a value of 0 after the successful execution of this script.

    ## Events
    The successful execution of this transaction will emit a `Diem::BurnEvent` on the event handle
    held in the `Diem::CurrencyInfo<CoinType>` resource's `burn_events` published under
    `0xA550C18`.

    # Parameters
    | Name         | Type      | Description                                                                                                                                         |
    | ------       | ------    | -------------                                                                                                                                       |
    | `CoinType`   | Type      | The Move type for the `CoinType` being added to the sending account of the transaction. `CoinType` must be an already-registered currency on-chain. |
    | `tc_account` | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                                           |

    # Common Abort Conditions
    | Error Category             | Error Reason                          | Description                                                 |
    | ----------------           | --------------                        | -------------                                               |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE` | The sending account is not the Treasury Compliance account. |
    | `Errors::NOT_PUBLISHED`    | `TransactionFee::ETRANSACTION_FEE`    | `CoinType` is not an accepted transaction fee currency.     |
    | `Errors::INVALID_ARGUMENT` | `Diem::ECOIN`                        | The collected fees in `CoinType` are zero.                  |

    # Related Scripts
    * `Script::burn`
    * `Script::cancel_burn`
    """
    return Script(
        code=BURN_TXN_FEES_CODE,
        ty_args=[coin_type],
        args=[],
    )


def encode_cancel_burn_script(token: TypeTag, preburn_address: AccountAddress) -> Script:
    """# Summary
    Cancels and returns all coins held in the preburn area under
    `preburn_address` and returns the funds to the `preburn_address`'s balance.

    Can only be successfully sent by an account with Treasury Compliance role.

    # Technical Description
    Cancels and returns all coins held in the `Diem::Preburn<Token>` resource under the `preburn_address` and
    return the funds to the `preburn_address` account's `DiemAccount::Balance<Token>`.
    The transaction must be sent by an `account` with a `Diem::BurnCapability<Token>`
    resource published under it. The account at `preburn_address` must have a
    `Diem::Preburn<Token>` resource published under it, and its value must be nonzero. The transaction removes
    the entire balance held in the `Diem::Preburn<Token>` resource, and returns it back to the account's
    `DiemAccount::Balance<Token>` under `preburn_address`. Due to this, the account at
    `preburn_address` must already have a balance in the `Token` currency published
    before this script is called otherwise the transaction will fail.

    ## Events
    The successful execution of this transaction will emit:
    * A `Diem::CancelBurnEvent` on the event handle held in the `Diem::CurrencyInfo<Token>`
    resource's `burn_events` published under `0xA550C18`.
    * A `DiemAccount::ReceivedPaymentEvent` on the `preburn_address`'s
    `DiemAccount::DiemAccount` `received_events` event handle with both the `payer` and `payee`
    being `preburn_address`.

    # Parameters
    | Name              | Type      | Description                                                                                                                          |
    | ------            | ------    | -------------                                                                                                                        |
    | `Token`           | Type      | The Move type for the `Token` currenty that burning is being cancelled for. `Token` must be an already-registered currency on-chain. |
    | `account`         | `&signer` | The signer reference of the sending account of this transaction, must have a burn capability for `Token` published under it.         |
    | `preburn_address` | `address` | The address where the coins to-be-burned are currently held.                                                                         |

    # Common Abort Conditions
    | Error Category                | Error Reason                                     | Description                                                                                           |
    | ----------------              | --------------                                   | -------------                                                                                         |
    | `Errors::REQUIRES_CAPABILITY` | `Diem::EBURN_CAPABILITY`                        | The sending `account` does not have a `Diem::BurnCapability<Token>` published under it.              |
    | `Errors::NOT_PUBLISHED`       | `Diem::EPREBURN`                                | The account at `preburn_address` does not have a `Diem::Preburn<Token>` resource published under it. |
    | `Errors::NOT_PUBLISHED`       | `Diem::ECURRENCY_INFO`                          | The specified `Token` is not a registered currency on-chain.                                          |
    | `Errors::INVALID_ARGUMENT`    | `DiemAccount::ECOIN_DEPOSIT_IS_ZERO`            | The value held in the preburn resource was zero.                                                      |
    | `Errors::INVALID_ARGUMENT`    | `DiemAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` | The account at `preburn_address` doesn't have a balance resource for `Token`.                         |
    | `Errors::LIMIT_EXCEEDED`      | `DiemAccount::EDEPOSIT_EXCEEDS_LIMITS`          | The depositing of the funds held in the prebun area would exceed the `account`'s account limits.      |
    | `Errors::INVALID_STATE`       | `DualAttestation::EPAYEE_COMPLIANCE_KEY_NOT_SET` | The `account` does not have a compliance key set on it but dual attestion checking was performed.     |

    # Related Scripts
    * `Script::burn_txn_fees`
    * `Script::burn`
    * `Script::preburn`
    """
    return Script(
        code=CANCEL_BURN_CODE,
        ty_args=[token],
        args=[TransactionArgument__Address(value=preburn_address)],
    )


def encode_create_child_vasp_account_script(
    coin_type: TypeTag,
    child_address: AccountAddress,
    auth_key_prefix: bytes,
    add_all_currencies: bool,
    child_initial_balance: st.uint64,
) -> Script:
    """# Summary
    Creates a Child VASP account with its parent being the sending account of the transaction.

    The sender of the transaction must be a Parent VASP account.

    # Technical Description
    Creates a `ChildVASP` account for the sender `parent_vasp` at `child_address` with a balance of
    `child_initial_balance` in `CoinType` and an initial authentication key of
    `auth_key_prefix | child_address`.

    If `add_all_currencies` is true, the child address will have a zero balance in all available
    currencies in the system.

    The new account will be a child account of the transaction sender, which must be a
    Parent VASP account. The child account will be recorded against the limit of
    child accounts of the creating Parent VASP account.

    ## Events
    Successful execution with a `child_initial_balance` greater than zero will emit:
    * A `DiemAccount::SentPaymentEvent` with the `payer` field being the Parent VASP's address,
    and payee field being `child_address`. This is emitted on the Parent VASP's
    `DiemAccount::DiemAccount` `sent_events` handle.
    * A `DiemAccount::ReceivedPaymentEvent` with the  `payer` field being the Parent VASP's address,
    and payee field being `child_address`. This is emitted on the new Child VASPS's
    `DiemAccount::DiemAccount` `received_events` handle.

    # Parameters
    | Name                    | Type         | Description                                                                                                                                 |
    | ------                  | ------       | -------------                                                                                                                               |
    | `CoinType`              | Type         | The Move type for the `CoinType` that the child account should be created with. `CoinType` must be an already-registered currency on-chain. |
    | `parent_vasp`           | `&signer`    | The signer reference of the sending account. Must be a Parent VASP account.                                                                 |
    | `child_address`         | `address`    | Address of the to-be-created Child VASP account.                                                                                            |
    | `auth_key_prefix`       | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.                                                    |
    | `add_all_currencies`    | `bool`       | Whether to publish balance resources for all known currencies when the account is created.                                                  |
    | `child_initial_balance` | `u64`        | The initial balance in `CoinType` to give the child account when it's created.                                                              |

    # Common Abort Conditions
    | Error Category              | Error Reason                                             | Description                                                                              |
    | ----------------            | --------------                                           | -------------                                                                            |
    | `Errors::INVALID_ARGUMENT`  | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`            | The `auth_key_prefix` was not of length 32.                                              |
    | `Errors::REQUIRES_ROLE`     | `Roles::EPARENT_VASP`                                    | The sending account wasn't a Parent VASP account.                                        |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                                        | The `child_address` address is already taken.                                            |
    | `Errors::LIMIT_EXCEEDED`    | `VASP::ETOO_MANY_CHILDREN`                               | The sending account has reached the maximum number of allowed child accounts.            |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                                  | The `CoinType` is not a registered currency on-chain.                                    |
    | `Errors::INVALID_STATE`     | `DiemAccount::EWITHDRAWAL_CAPABILITY_ALREADY_EXTRACTED` | The withdrawal capability for the sending account has already been extracted.            |
    | `Errors::NOT_PUBLISHED`     | `DiemAccount::EPAYER_DOESNT_HOLD_CURRENCY`              | The sending account doesn't have a balance in `CoinType`.                                |
    | `Errors::LIMIT_EXCEEDED`    | `DiemAccount::EINSUFFICIENT_BALANCE`                    | The sending account doesn't have at least `child_initial_balance` of `CoinType` balance. |
    | `Errors::INVALID_ARGUMENT`  | `DiemAccount::ECANNOT_CREATE_AT_VM_RESERVED`            | The `child_address` is the reserved address 0x0.                                         |

    # Related Scripts
    * `Script::create_parent_vasp_account`
    * `Script::add_currency_to_account`
    * `Script::rotate_authentication_key`
    * `Script::add_recovery_rotation_capability`
    * `Script::create_recovery_address`
    """
    return Script(
        code=CREATE_CHILD_VASP_ACCOUNT_CODE,
        ty_args=[coin_type],
        args=[
            TransactionArgument__Address(value=child_address),
            TransactionArgument__U8Vector(value=auth_key_prefix),
            TransactionArgument__Bool(value=add_all_currencies),
            TransactionArgument__U64(value=child_initial_balance),
        ],
    )


def encode_create_designated_dealer_script(
    currency: TypeTag,
    sliding_nonce: st.uint64,
    addr: AccountAddress,
    auth_key_prefix: bytes,
    human_name: bytes,
    add_all_currencies: bool,
) -> Script:
    """# Summary
    Creates a Designated Dealer account with the provided information, and initializes it with
    default mint tiers.

    The transaction can only be sent by the Treasury Compliance account.

    # Technical Description
    Creates an account with the Designated Dealer role at `addr` with authentication key
    `auth_key_prefix` | `addr` and a 0 balance of type `Currency`. If `add_all_currencies` is true,
    0 balances for all available currencies in the system will also be added. This can only be
    invoked by an account with the TreasuryCompliance role.

    At the time of creation the account is also initialized with default mint tiers of (500_000,
    5000_000, 50_000_000, 500_000_000), and preburn areas for each currency that is added to the
    account.

    # Parameters
    | Name                 | Type         | Description                                                                                                                                         |
    | ------               | ------       | -------------                                                                                                                                       |
    | `Currency`           | Type         | The Move type for the `Currency` that the Designated Dealer should be initialized with. `Currency` must be an already-registered currency on-chain. |
    | `tc_account`         | `&signer`    | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                                           |
    | `sliding_nonce`      | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                                          |
    | `addr`               | `address`    | Address of the to-be-created Designated Dealer account.                                                                                             |
    | `auth_key_prefix`    | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.                                                            |
    | `human_name`         | `vector<u8>` | ASCII-encoded human name for the Designated Dealer.                                                                                                 |
    | `add_all_currencies` | `bool`       | Whether to publish preburn, balance, and tier info resources for all known (SCS) currencies or just `Currency` when the account is created.         |


    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::ETREASURY_COMPLIANCE`   | The sending account is not the Treasury Compliance account.                                |
    | `Errors::REQUIRES_ROLE`     | `Roles::ETREASURY_COMPLIANCE`           | The sending account is not the Treasury Compliance account.                                |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                 | The `Currency` is not a registered currency on-chain.                                      |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `addr` address is already taken.                                                       |

    # Related Scripts
    * `Script::tiered_mint`
    * `Script::peer_to_peer_with_metadata`
    * `Script::rotate_dual_attestation_info`
    """
    return Script(
        code=CREATE_DESIGNATED_DEALER_CODE,
        ty_args=[currency],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__Address(value=addr),
            TransactionArgument__U8Vector(value=auth_key_prefix),
            TransactionArgument__U8Vector(value=human_name),
            TransactionArgument__Bool(value=add_all_currencies),
        ],
    )


def encode_create_parent_vasp_account_script(
    coin_type: TypeTag,
    sliding_nonce: st.uint64,
    new_account_address: AccountAddress,
    auth_key_prefix: bytes,
    human_name: bytes,
    add_all_currencies: bool,
) -> Script:
    """# Summary
    Creates a Parent VASP account with the specified human name.

    Must be called by the Treasury Compliance account.

    # Technical Description
    Creates an account with the Parent VASP role at `address` with authentication key
    `auth_key_prefix` | `new_account_address` and a 0 balance of type `CoinType`. If
    `add_all_currencies` is true, 0 balances for all available currencies in the system will
    also be added. This can only be invoked by an TreasuryCompliance account.
    `sliding_nonce` is a unique nonce for operation, see `SlidingNonce` for details.

    # Parameters
    | Name                  | Type         | Description                                                                                                                                                    |
    | ------                | ------       | -------------                                                                                                                                                  |
    | `CoinType`            | Type         | The Move type for the `CoinType` currency that the Parent VASP account should be initialized with. `CoinType` must be an already-registered currency on-chain. |
    | `tc_account`          | `&signer`    | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                                                      |
    | `sliding_nonce`       | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                                                     |
    | `new_account_address` | `address`    | Address of the to-be-created Parent VASP account.                                                                                                              |
    | `auth_key_prefix`     | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.                                                                       |
    | `human_name`          | `vector<u8>` | ASCII-encoded human name for the Parent VASP.                                                                                                                  |
    | `add_all_currencies`  | `bool`       | Whether to publish balance resources for all known currencies when the account is created.                                                                     |

    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::ETREASURY_COMPLIANCE`   | The sending account is not the Treasury Compliance account.                                |
    | `Errors::REQUIRES_ROLE`     | `Roles::ETREASURY_COMPLIANCE`           | The sending account is not the Treasury Compliance account.                                |
    | `Errors::NOT_PUBLISHED`     | `Diem::ECURRENCY_INFO`                 | The `CoinType` is not a registered currency on-chain.                                      |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `new_account_address` address is already taken.                                        |

    # Related Scripts
    * `Script::create_child_vasp_account`
    * `Script::add_currency_to_account`
    * `Script::rotate_authentication_key`
    * `Script::add_recovery_rotation_capability`
    * `Script::create_recovery_address`
    * `Script::rotate_dual_attestation_info`
    """
    return Script(
        code=CREATE_PARENT_VASP_ACCOUNT_CODE,
        ty_args=[coin_type],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__Address(value=new_account_address),
            TransactionArgument__U8Vector(value=auth_key_prefix),
            TransactionArgument__U8Vector(value=human_name),
            TransactionArgument__Bool(value=add_all_currencies),
        ],
    )


def encode_create_recovery_address_script() -> Script:
    """# Summary
    Initializes the sending account as a recovery address that may be used by
    the VASP that it belongs to.

    The sending account must be a VASP account.
    Multiple recovery addresses can exist for a single VASP, but accounts in
    each must be disjoint.

    # Technical Description
    Publishes a `RecoveryAddress::RecoveryAddress` resource under `account`. It then
    extracts the `DiemAccount::KeyRotationCapability` for `account` and adds
    it to the resource. After the successful execution of this transaction
    other accounts may add their key rotation to this resource so that `account`
    may be used as a recovery account for those accounts.

    # Parameters
    | Name      | Type      | Description                                           |
    | ------    | ------    | -------------                                         |
    | `account` | `&signer` | The signer of the sending account of the transaction. |

    # Common Abort Conditions
    | Error Category              | Error Reason                                               | Description                                                                                   |
    | ----------------            | --------------                                             | -------------                                                                                 |
    | `Errors::INVALID_STATE`     | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.          |
    | `Errors::INVALID_ARGUMENT`  | `RecoveryAddress::ENOT_A_VASP`                             | `account` is not a VASP account.                                                              |
    | `Errors::INVALID_ARGUMENT`  | `RecoveryAddress::EKEY_ROTATION_DEPENDENCY_CYCLE`          | A key rotation recovery cycle would be created by adding `account`'s key rotation capability. |
    | `Errors::ALREADY_PUBLISHED` | `RecoveryAddress::ERECOVERY_ADDRESS`                       | A `RecoveryAddress::RecoveryAddress` resource has already been published under `account`.     |

    # Related Scripts
    * `Script::add_recovery_rotation_capability`
    * `Script::rotate_authentication_key_with_recovery_address`
    """
    return Script(
        code=CREATE_RECOVERY_ADDRESS_CODE,
        ty_args=[],
        args=[],
    )


def encode_create_validator_account_script(
    sliding_nonce: st.uint64, new_account_address: AccountAddress, auth_key_prefix: bytes, human_name: bytes
) -> Script:
    """# Summary
    Creates a Validator account.

    This transaction can only be sent by the Diem
    Root account.

    # Technical Description
    Creates an account with a Validator role at `new_account_address`, with authentication key
    `auth_key_prefix` | `new_account_address`. It publishes a
    `ValidatorConfig::ValidatorConfig` resource with empty `config`, and
    `operator_account` fields. The `human_name` field of the
    `ValidatorConfig::ValidatorConfig` is set to the passed in `human_name`.
    This script does not add the validator to the validator set or the system,
    but only creates the account.

    # Parameters
    | Name                  | Type         | Description                                                                                     |
    | ------                | ------       | -------------                                                                                   |
    | `dr_account`          | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer. |
    | `sliding_nonce`       | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                      |
    | `new_account_address` | `address`    | Address of the to-be-created Validator account.                                                 |
    | `auth_key_prefix`     | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.        |
    | `human_name`          | `vector<u8>` | ASCII-encoded human name for the validator.                                                     |

    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `dr_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::EDIEM_ROOT`            | The sending account is not the Diem Root account.                                         |
    | `Errors::REQUIRES_ROLE`     | `Roles::EDIEM_ROOT`                    | The sending account is not the Diem Root account.                                         |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `new_account_address` address is already taken.                                        |

    # Related Scripts
    * `Script::add_validator_and_reconfigure`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """
    return Script(
        code=CREATE_VALIDATOR_ACCOUNT_CODE,
        ty_args=[],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__Address(value=new_account_address),
            TransactionArgument__U8Vector(value=auth_key_prefix),
            TransactionArgument__U8Vector(value=human_name),
        ],
    )


def encode_create_validator_operator_account_script(
    sliding_nonce: st.uint64, new_account_address: AccountAddress, auth_key_prefix: bytes, human_name: bytes
) -> Script:
    """# Summary
    Creates a Validator Operator account.

    This transaction can only be sent by the Diem
    Root account.

    # Technical Description
    Creates an account with a Validator Operator role at `new_account_address`, with authentication key
    `auth_key_prefix` | `new_account_address`. It publishes a
    `ValidatorOperatorConfig::ValidatorOperatorConfig` resource with the specified `human_name`.
    This script does not assign the validator operator to any validator accounts but only creates the account.

    # Parameters
    | Name                  | Type         | Description                                                                                     |
    | ------                | ------       | -------------                                                                                   |
    | `dr_account`          | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer. |
    | `sliding_nonce`       | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                      |
    | `new_account_address` | `address`    | Address of the to-be-created Validator account.                                                 |
    | `auth_key_prefix`     | `vector<u8>` | The authentication key prefix that will be used initially for the newly created account.        |
    | `human_name`          | `vector<u8>` | ASCII-encoded human name for the validator.                                                     |

    # Common Abort Conditions
    | Error Category              | Error Reason                            | Description                                                                                |
    | ----------------            | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`     | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `dr_account`.                             |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT`  | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS`  | `CoreAddresses::EDIEM_ROOT`            | The sending account is not the Diem Root account.                                         |
    | `Errors::REQUIRES_ROLE`     | `Roles::EDIEM_ROOT`                    | The sending account is not the Diem Root account.                                         |
    | `Errors::ALREADY_PUBLISHED` | `Roles::EROLE_ID`                       | The `new_account_address` address is already taken.                                        |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::add_validator_and_reconfigure`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """
    return Script(
        code=CREATE_VALIDATOR_OPERATOR_ACCOUNT_CODE,
        ty_args=[],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__Address(value=new_account_address),
            TransactionArgument__U8Vector(value=auth_key_prefix),
            TransactionArgument__U8Vector(value=human_name),
        ],
    )


def encode_freeze_account_script(sliding_nonce: st.uint64, to_freeze_account: AccountAddress) -> Script:
    """# Summary
    Freezes the account at `address`.

    The sending account of this transaction
    must be the Treasury Compliance account. The account being frozen cannot be
    the Diem Root or Treasury Compliance account. After the successful
    execution of this transaction no transactions may be sent from the frozen
    account, and the frozen account may not send or receive coins.

    # Technical Description
    Sets the `AccountFreezing::FreezingBit` to `true` and emits a
    `AccountFreezing::FreezeAccountEvent`. The transaction sender must be the
    Treasury Compliance account, but the account at `to_freeze_account` must
    not be either `0xA550C18` (the Diem Root address), or `0xB1E55ED` (the
    Treasury Compliance address). Note that this is a per-account property
    e.g., freezing a Parent VASP will not effect the status any of its child
    accounts and vice versa.


    ## Events
    Successful execution of this transaction will emit a `AccountFreezing::FreezeAccountEvent` on
    the `freeze_event_handle` held in the `AccountFreezing::FreezeEventsHolder` resource published
    under `0xA550C18` with the `frozen_address` being the `to_freeze_account`.

    # Parameters
    | Name                | Type      | Description                                                                                               |
    | ------              | ------    | -------------                                                                                             |
    | `tc_account`        | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account. |
    | `sliding_nonce`     | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                |
    | `to_freeze_account` | `address` | The account address to be frozen.                                                                         |

    # Common Abort Conditions
    | Error Category             | Error Reason                                 | Description                                                                                |
    | ----------------           | --------------                               | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`               | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`               | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`               | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`      | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`        | The sending account is not the Treasury Compliance account.                                |
    | `Errors::REQUIRES_ROLE`    | `Roles::ETREASURY_COMPLIANCE`                | The sending account is not the Treasury Compliance account.                                |
    | `Errors::INVALID_ARGUMENT` | `AccountFreezing::ECANNOT_FREEZE_TC`         | `to_freeze_account` was the Treasury Compliance account (`0xB1E55ED`).                     |
    | `Errors::INVALID_ARGUMENT` | `AccountFreezing::ECANNOT_FREEZE_DIEM_ROOT` | `to_freeze_account` was the Diem Root account (`0xA550C18`).                              |

    # Related Scripts
    * `Script::unfreeze_account`
    """
    return Script(
        code=FREEZE_ACCOUNT_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__Address(value=to_freeze_account)],
    )


def encode_peer_to_peer_with_metadata_script(
    currency: TypeTag, payee: AccountAddress, amount: st.uint64, metadata: bytes, metadata_signature: bytes
) -> Script:
    """# Summary
    Transfers a given number of coins in a specified currency from one account to another.

    Transfers over a specified amount defined on-chain that are between two different VASPs, or
    other accounts that have opted-in will be subject to on-chain checks to ensure the receiver has
    agreed to receive the coins.  This transaction can be sent by any account that can hold a
    balance, and to any account that can hold a balance. Both accounts must hold balances in the
    currency being transacted.

    # Technical Description

    Transfers `amount` coins of type `Currency` from `payer` to `payee` with (optional) associated
    `metadata` and an (optional) `metadata_signature` on the message
    `metadata` | `Signer::address_of(payer)` | `amount` | `DualAttestation::DOMAIN_SEPARATOR`.
    The `metadata` and `metadata_signature` parameters are only required if `amount` >=
    `DualAttestation::get_cur_microdiem_limit` XDX and `payer` and `payee` are distinct VASPs.
    However, a transaction sender can opt in to dual attestation even when it is not required
    (e.g., a DesignatedDealer -> VASP payment) by providing a non-empty `metadata_signature`.
    Standardized `metadata` BCS format can be found in `diem_types::transaction::metadata::Metadata`.

    ## Events
    Successful execution of this script emits two events:
    * A `DiemAccount::SentPaymentEvent` on `payer`'s `DiemAccount::DiemAccount` `sent_events` handle; and
    * A `DiemAccount::ReceivedPaymentEvent` on `payee`'s `DiemAccount::DiemAccount` `received_events` handle.

    # Parameters
    | Name                 | Type         | Description                                                                                                                  |
    | ------               | ------       | -------------                                                                                                                |
    | `Currency`           | Type         | The Move type for the `Currency` being sent in this transaction. `Currency` must be an already-registered currency on-chain. |
    | `payer`              | `&signer`    | The signer reference of the sending account that coins are being transferred from.                                           |
    | `payee`              | `address`    | The address of the account the coins are being transferred to.                                                               |
    | `metadata`           | `vector<u8>` | Optional metadata about this payment.                                                                                        |
    | `metadata_signature` | `vector<u8>` | Optional signature over `metadata` and payment information. See                                                              |

    # Common Abort Conditions
    | Error Category             | Error Reason                                     | Description                                                                                                                         |
    | ----------------           | --------------                                   | -------------                                                                                                                       |
    | `Errors::NOT_PUBLISHED`    | `DiemAccount::EPAYER_DOESNT_HOLD_CURRENCY`      | `payer` doesn't hold a balance in `Currency`.                                                                                       |
    | `Errors::LIMIT_EXCEEDED`   | `DiemAccount::EINSUFFICIENT_BALANCE`            | `amount` is greater than `payer`'s balance in `Currency`.                                                                           |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::ECOIN_DEPOSIT_IS_ZERO`            | `amount` is zero.                                                                                                                   |
    | `Errors::NOT_PUBLISHED`    | `DiemAccount::EPAYEE_DOES_NOT_EXIST`            | No account exists at the `payee` address.                                                                                           |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` | An account exists at `payee`, but it does not accept payments in `Currency`.                                                        |
    | `Errors::INVALID_STATE`    | `AccountFreezing::EACCOUNT_FROZEN`               | The `payee` account is frozen.                                                                                                      |
    | `Errors::INVALID_ARGUMENT` | `DualAttestation::EMALFORMED_METADATA_SIGNATURE` | `metadata_signature` is not 64 bytes.                                                                                               |
    | `Errors::INVALID_ARGUMENT` | `DualAttestation::EINVALID_METADATA_SIGNATURE`   | `metadata_signature` does not verify on the against the `payee'`s `DualAttestation::Credential` `compliance_public_key` public key. |
    | `Errors::LIMIT_EXCEEDED`   | `DiemAccount::EWITHDRAWAL_EXCEEDS_LIMITS`       | `payer` has exceeded its daily withdrawal limits for the backing coins of XDX.                                                      |
    | `Errors::LIMIT_EXCEEDED`   | `DiemAccount::EDEPOSIT_EXCEEDS_LIMITS`          | `payee` has exceeded its daily deposit limits for XDX.                                                                              |

    # Related Scripts
    * `Script::create_child_vasp_account`
    * `Script::create_parent_vasp_account`
    * `Script::add_currency_to_account`
    """
    return Script(
        code=PEER_TO_PEER_WITH_METADATA_CODE,
        ty_args=[currency],
        args=[
            TransactionArgument__Address(value=payee),
            TransactionArgument__U64(value=amount),
            TransactionArgument__U8Vector(value=metadata),
            TransactionArgument__U8Vector(value=metadata_signature),
        ],
    )


def encode_preburn_script(token: TypeTag, amount: st.uint64) -> Script:
    """# Summary
    Moves a specified number of coins in a given currency from the account's
    balance to its preburn area after which the coins may be burned.

    This
    transaction may be sent by any account that holds a balance and preburn area
    in the specified currency.

    # Technical Description
    Moves the specified `amount` of coins in `Token` currency from the sending `account`'s
    `DiemAccount::Balance<Token>` to the `Diem::Preburn<Token>` published under the same
    `account`. `account` must have both of these resources published under it at the start of this
    transaction in order for it to execute successfully.

    ## Events
    Successful execution of this script emits two events:
    * `DiemAccount::SentPaymentEvent ` on `account`'s `DiemAccount::DiemAccount` `sent_events`
    handle with the `payee` and `payer` fields being `account`'s address; and
    * A `Diem::PreburnEvent` with `Token`'s currency code on the
    `Diem::CurrencyInfo<Token`'s `preburn_events` handle for `Token` and with
    `preburn_address` set to `account`'s address.

    # Parameters
    | Name      | Type      | Description                                                                                                                      |
    | ------    | ------    | -------------                                                                                                                    |
    | `Token`   | Type      | The Move type for the `Token` currency being moved to the preburn area. `Token` must be an already-registered currency on-chain. |
    | `account` | `&signer` | The signer reference of the sending account.                                                                                     |
    | `amount`  | `u64`     | The amount in `Token` to be moved to the preburn area.                                                                           |

    # Common Abort Conditions
    | Error Category           | Error Reason                                             | Description                                                                             |
    | ----------------         | --------------                                           | -------------                                                                           |
    | `Errors::NOT_PUBLISHED`  | `Diem::ECURRENCY_INFO`                                  | The `Token` is not a registered currency on-chain.                                      |
    | `Errors::INVALID_STATE`  | `DiemAccount::EWITHDRAWAL_CAPABILITY_ALREADY_EXTRACTED` | The withdrawal capability for `account` has already been extracted.                     |
    | `Errors::LIMIT_EXCEEDED` | `DiemAccount::EINSUFFICIENT_BALANCE`                    | `amount` is greater than `payer`'s balance in `Token`.                                  |
    | `Errors::NOT_PUBLISHED`  | `DiemAccount::EPAYER_DOESNT_HOLD_CURRENCY`              | `account` doesn't hold a balance in `Token`.                                            |
    | `Errors::NOT_PUBLISHED`  | `Diem::EPREBURN`                                        | `account` doesn't have a `Diem::Preburn<Token>` resource published under it.           |
    | `Errors::INVALID_STATE`  | `Diem::EPREBURN_OCCUPIED`                               | The `value` field in the `Diem::Preburn<Token>` resource under the sender is non-zero. |
    | `Errors::NOT_PUBLISHED`  | `Roles::EROLE_ID`                                        | The `account` did not have a role assigned to it.                                       |
    | `Errors::REQUIRES_ROLE`  | `Roles::EDESIGNATED_DEALER`                              | The `account` did not have the role of DesignatedDealer.                                |

    # Related Scripts
    * `Script::cancel_burn`
    * `Script::burn`
    * `Script::burn_txn_fees`
    """
    return Script(
        code=PREBURN_CODE,
        ty_args=[token],
        args=[TransactionArgument__U64(value=amount)],
    )


def encode_publish_shared_ed25519_public_key_script(public_key: bytes) -> Script:
    """# Summary
    Rotates the authentication key of the sending account to the
    newly-specified public key and publishes a new shared authentication key
    under the sender's account.

    Any account can send this transaction.

    # Technical Description
    Rotates the authentication key of the sending account to `public_key`,
    and publishes a `SharedEd25519PublicKey::SharedEd25519PublicKey` resource
    containing the 32-byte ed25519 `public_key` and the `DiemAccount::KeyRotationCapability` for
    `account` under `account`.

    # Parameters
    | Name         | Type         | Description                                                                               |
    | ------       | ------       | -------------                                                                             |
    | `account`    | `&signer`    | The signer reference of the sending account of the transaction.                           |
    | `public_key` | `vector<u8>` | 32-byte Ed25519 public key for `account`' authentication key to be rotated to and stored. |

    # Common Abort Conditions
    | Error Category              | Error Reason                                               | Description                                                                                         |
    | ----------------            | --------------                                             | -------------                                                                                       |
    | `Errors::INVALID_STATE`     | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability` resource.       |
    | `Errors::ALREADY_PUBLISHED` | `SharedEd25519PublicKey::ESHARED_KEY`                      | The `SharedEd25519PublicKey::SharedEd25519PublicKey` resource is already published under `account`. |
    | `Errors::INVALID_ARGUMENT`  | `SharedEd25519PublicKey::EMALFORMED_PUBLIC_KEY`            | `public_key` is an invalid ed25519 public key.                                                      |

    # Related Scripts
    * `Script::rotate_shared_ed25519_public_key`
    """
    return Script(
        code=PUBLISH_SHARED_ED25519_PUBLIC_KEY_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=public_key)],
    )


def encode_register_validator_config_script(
    validator_account: AccountAddress,
    consensus_pubkey: bytes,
    validator_network_addresses: bytes,
    fullnode_network_addresses: bytes,
) -> Script:
    """# Summary
    Updates a validator's configuration.

    This does not reconfigure the system and will not update
    the configuration in the validator set that is seen by other validators in the network. Can
    only be successfully sent by a Validator Operator account that is already registered with a
    validator.

    # Technical Description
    This updates the fields with corresponding names held in the `ValidatorConfig::ValidatorConfig`
    config resource held under `validator_account`. It does not emit a `DiemConfig::NewEpochEvent`
    so the copy of this config held in the validator set will not be updated, and the changes are
    only "locally" under the `validator_account` account address.

    # Parameters
    | Name                          | Type         | Description                                                                                                                  |
    | ------                        | ------       | -------------                                                                                                                |
    | `validator_operator_account`  | `&signer`    | Signer reference of the sending account. Must be the registered validator operator for the validator at `validator_address`. |
    | `validator_account`           | `address`    | The address of the validator's `ValidatorConfig::ValidatorConfig` resource being updated.                                    |
    | `consensus_pubkey`            | `vector<u8>` | New Ed25519 public key to be used in the updated `ValidatorConfig::ValidatorConfig`.                                         |
    | `validator_network_addresses` | `vector<u8>` | New set of `validator_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                       |
    | `fullnode_network_addresses`  | `vector<u8>` | New set of `fullnode_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                        |

    # Common Abort Conditions
    | Error Category             | Error Reason                                   | Description                                                                                           |
    | ----------------           | --------------                                 | -------------                                                                                         |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`           | `validator_address` does not have a `ValidatorConfig::ValidatorConfig` resource published under it.   |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_TRANSACTION_SENDER` | `validator_operator_account` is not the registered operator for the validator at `validator_address`. |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_CONSENSUS_KEY`      | `consensus_pubkey` is not a valid ed25519 public key.                                                 |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::add_validator_and_reconfigure`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """
    return Script(
        code=REGISTER_VALIDATOR_CONFIG_CODE,
        ty_args=[],
        args=[
            TransactionArgument__Address(value=validator_account),
            TransactionArgument__U8Vector(value=consensus_pubkey),
            TransactionArgument__U8Vector(value=validator_network_addresses),
            TransactionArgument__U8Vector(value=fullnode_network_addresses),
        ],
    )


def encode_remove_validator_and_reconfigure_script(
    sliding_nonce: st.uint64, validator_name: bytes, validator_address: AccountAddress
) -> Script:
    """# Summary
    This script removes a validator account from the validator set, and triggers a reconfiguration
    of the system to remove the validator from the system.

    This transaction can only be
    successfully called by the Diem Root account.

    # Technical Description
    This script removes the account at `validator_address` from the validator set. This transaction
    emits a `DiemConfig::NewEpochEvent` event. Once the reconfiguration triggered by this event
    has been performed, the account at `validator_address` is no longer considered to be a
    validator in the network. This transaction will fail if the validator at `validator_address`
    is not in the validator set.

    # Parameters
    | Name                | Type         | Description                                                                                                                        |
    | ------              | ------       | -------------                                                                                                                      |
    | `dr_account`        | `&signer`    | The signer reference of the sending account of this transaction. Must be the Diem Root signer.                                    |
    | `sliding_nonce`     | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                                         |
    | `validator_name`    | `vector<u8>` | ASCII-encoded human name for the validator. Must match the human name in the `ValidatorConfig::ValidatorConfig` for the validator. |
    | `validator_address` | `address`    | The validator account address to be removed from the validator set.                                                                |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                     |
    | ----------------           | --------------                          | -------------                                                                                   |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `dr_account`.                                  |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.      |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                                   |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                               |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | The sending account is not the Diem Root account or Treasury Compliance account                |
    | 0                          | 0                                       | The provided `validator_name` does not match the already-recorded human name for the validator. |
    | `Errors::INVALID_ARGUMENT` | `DiemSystem::ENOT_AN_ACTIVE_VALIDATOR` | The validator to be removed is not in the validator set.                                        |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`            | The sending account is not the Diem Root account.                                              |
    | `Errors::REQUIRES_ROLE`    | `Roles::EDIEM_ROOT`                    | The sending account is not the Diem Root account.                                              |
    | `Errors::INVALID_STATE`    | `DiemConfig::EINVALID_BLOCK_TIME`      | An invalid time value was encountered in reconfiguration. Unlikely to occur.                    |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::add_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """
    return Script(
        code=REMOVE_VALIDATOR_AND_RECONFIGURE_CODE,
        ty_args=[],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__U8Vector(value=validator_name),
            TransactionArgument__Address(value=validator_address),
        ],
    )


def encode_rotate_authentication_key_script(new_key: bytes) -> Script:
    """# Summary
    Rotates the transaction sender's authentication key to the supplied new authentication key.

    May
    be sent by any account.

    # Technical Description
    Rotate the `account`'s `DiemAccount::DiemAccount` `authentication_key` field to `new_key`.
    `new_key` must be a valid ed25519 public key, and `account` must not have previously delegated
    its `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name      | Type         | Description                                                 |
    | ------    | ------       | -------------                                               |
    | `account` | `&signer`    | Signer reference of the sending account of the transaction. |
    | `new_key` | `vector<u8>` | New ed25519 public key to be used for `account`.            |

    # Common Abort Conditions
    | Error Category             | Error Reason                                               | Description                                                                              |
    | ----------------           | --------------                                             | -------------                                                                            |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.     |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`              | `new_key` was an invalid length.                                                         |

    # Related Scripts
    * `Script::rotate_authentication_key_with_nonce`
    * `Script::rotate_authentication_key_with_nonce_admin`
    * `Script::rotate_authentication_key_with_recovery_address`
    """
    return Script(
        code=ROTATE_AUTHENTICATION_KEY_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_authentication_key_with_nonce_script(sliding_nonce: st.uint64, new_key: bytes) -> Script:
    """# Summary
    Rotates the sender's authentication key to the supplied new authentication key.

    May be sent by
    any account that has a sliding nonce resource published under it (usually this is Treasury
    Compliance or Diem Root accounts).

    # Technical Description
    Rotates the `account`'s `DiemAccount::DiemAccount` `authentication_key` field to `new_key`.
    `new_key` must be a valid ed25519 public key, and `account` must not have previously delegated
    its `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name            | Type         | Description                                                                |
    | ------          | ------       | -------------                                                              |
    | `account`       | `&signer`    | Signer reference of the sending account of the transaction.                |
    | `sliding_nonce` | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction. |
    | `new_key`       | `vector<u8>` | New ed25519 public key to be used for `account`.                           |

    # Common Abort Conditions
    | Error Category             | Error Reason                                               | Description                                                                                |
    | ----------------           | --------------                                             | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                             | A `SlidingNonce` resource is not published under `account`.                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                             | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                             | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`                    | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.       |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`              | `new_key` was an invalid length.                                                           |

    # Related Scripts
    * `Script::rotate_authentication_key`
    * `Script::rotate_authentication_key_with_nonce_admin`
    * `Script::rotate_authentication_key_with_recovery_address`
    """
    return Script(
        code=ROTATE_AUTHENTICATION_KEY_WITH_NONCE_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_authentication_key_with_nonce_admin_script(sliding_nonce: st.uint64, new_key: bytes) -> Script:
    """# Summary
    Rotates the specified account's authentication key to the supplied new authentication key.

    May
    only be sent by the Diem Root account as a write set transaction.

    # Technical Description
    Rotate the `account`'s `DiemAccount::DiemAccount` `authentication_key` field to `new_key`.
    `new_key` must be a valid ed25519 public key, and `account` must not have previously delegated
    its `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name            | Type         | Description                                                                                                  |
    | ------          | ------       | -------------                                                                                                |
    | `dr_account`    | `&signer`    | The signer reference of the sending account of the write set transaction. May only be the Diem Root signer. |
    | `account`       | `&signer`    | Signer reference of account specified in the `execute_as` field of the write set transaction.                |
    | `sliding_nonce` | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction for Diem Root.                    |
    | `new_key`       | `vector<u8>` | New ed25519 public key to be used for `account`.                                                             |

    # Common Abort Conditions
    | Error Category             | Error Reason                                               | Description                                                                                                |
    | ----------------           | --------------                                             | -------------                                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                             | A `SlidingNonce` resource is not published under `dr_account`.                                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                             | The `sliding_nonce` in `dr_account` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                             | The `sliding_nonce` in `dr_account` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`                    | The `sliding_nonce` in` dr_account` has been previously recorded.                                          |
    | `Errors::INVALID_STATE`    | `DiemAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` | `account` has already delegated/extracted its `DiemAccount::KeyRotationCapability`.                       |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY`              | `new_key` was an invalid length.                                                                           |

    # Related Scripts
    * `Script::rotate_authentication_key`
    * `Script::rotate_authentication_key_with_nonce`
    * `Script::rotate_authentication_key_with_recovery_address`
    """
    return Script(
        code=ROTATE_AUTHENTICATION_KEY_WITH_NONCE_ADMIN_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_authentication_key_with_recovery_address_script(
    recovery_address: AccountAddress, to_recover: AccountAddress, new_key: bytes
) -> Script:
    """# Summary
    Rotates the authentication key of a specified account that is part of a recovery address to a
    new authentication key.

    Only used for accounts that are part of a recovery address (see
    `Script::add_recovery_rotation_capability` for account restrictions).

    # Technical Description
    Rotates the authentication key of the `to_recover` account to `new_key` using the
    `DiemAccount::KeyRotationCapability` stored in the `RecoveryAddress::RecoveryAddress` resource
    published under `recovery_address`. This transaction can be sent either by the `to_recover`
    account, or by the account where the `RecoveryAddress::RecoveryAddress` resource is published
    that contains `to_recover`'s `DiemAccount::KeyRotationCapability`.

    # Parameters
    | Name               | Type         | Description                                                                                                                    |
    | ------             | ------       | -------------                                                                                                                  |
    | `account`          | `&signer`    | Signer reference of the sending account of the transaction.                                                                    |
    | `recovery_address` | `address`    | Address where `RecoveryAddress::RecoveryAddress` that holds `to_recover`'s `DiemAccount::KeyRotationCapability` is published. |
    | `to_recover`       | `address`    | The address of the account whose authentication key will be updated.                                                           |
    | `new_key`          | `vector<u8>` | New ed25519 public key to be used for the account at the `to_recover` address.                                                 |

    # Common Abort Conditions
    | Error Category             | Error Reason                                  | Description                                                                                                                                          |
    | ----------------           | --------------                                | -------------                                                                                                                                        |
    | `Errors::NOT_PUBLISHED`    | `RecoveryAddress::ERECOVERY_ADDRESS`          | `recovery_address` does not have a `RecoveryAddress::RecoveryAddress` resource published under it.                                                   |
    | `Errors::INVALID_ARGUMENT` | `RecoveryAddress::ECANNOT_ROTATE_KEY`         | The address of `account` is not `recovery_address` or `to_recover`.                                                                                  |
    | `Errors::INVALID_ARGUMENT` | `RecoveryAddress::EACCOUNT_NOT_RECOVERABLE`   | `to_recover`'s `DiemAccount::KeyRotationCapability`  is not in the `RecoveryAddress::RecoveryAddress`  resource published under `recovery_address`. |
    | `Errors::INVALID_ARGUMENT` | `DiemAccount::EMALFORMED_AUTHENTICATION_KEY` | `new_key` was an invalid length.                                                                                                                     |

    # Related Scripts
    * `Script::rotate_authentication_key`
    * `Script::rotate_authentication_key_with_nonce`
    * `Script::rotate_authentication_key_with_nonce_admin`
    """
    return Script(
        code=ROTATE_AUTHENTICATION_KEY_WITH_RECOVERY_ADDRESS_CODE,
        ty_args=[],
        args=[
            TransactionArgument__Address(value=recovery_address),
            TransactionArgument__Address(value=to_recover),
            TransactionArgument__U8Vector(value=new_key),
        ],
    )


def encode_rotate_dual_attestation_info_script(new_url: bytes, new_key: bytes) -> Script:
    """# Summary
    Updates the url used for off-chain communication, and the public key used to verify dual
    attestation on-chain.

    Transaction can be sent by any account that has dual attestation
    information published under it. In practice the only such accounts are Designated Dealers and
    Parent VASPs.

    # Technical Description
    Updates the `base_url` and `compliance_public_key` fields of the `DualAttestation::Credential`
    resource published under `account`. The `new_key` must be a valid ed25519 public key.

    ## Events
    Successful execution of this transaction emits two events:
    * A `DualAttestation::ComplianceKeyRotationEvent` containing the new compliance public key, and
    the blockchain time at which the key was updated emitted on the `DualAttestation::Credential`
    `compliance_key_rotation_events` handle published under `account`; and
    * A `DualAttestation::BaseUrlRotationEvent` containing the new base url to be used for
    off-chain communication, and the blockchain time at which the url was updated emitted on the
    `DualAttestation::Credential` `base_url_rotation_events` handle published under `account`.

    # Parameters
    | Name      | Type         | Description                                                               |
    | ------    | ------       | -------------                                                             |
    | `account` | `&signer`    | Signer reference of the sending account of the transaction.               |
    | `new_url` | `vector<u8>` | ASCII-encoded url to be used for off-chain communication with `account`.  |
    | `new_key` | `vector<u8>` | New ed25519 public key to be used for on-chain dual attestation checking. |

    # Common Abort Conditions
    | Error Category             | Error Reason                           | Description                                                                |
    | ----------------           | --------------                         | -------------                                                              |
    | `Errors::NOT_PUBLISHED`    | `DualAttestation::ECREDENTIAL`         | A `DualAttestation::Credential` resource is not published under `account`. |
    | `Errors::INVALID_ARGUMENT` | `DualAttestation::EINVALID_PUBLIC_KEY` | `new_key` is not a valid ed25519 public key.                               |

    # Related Scripts
    * `Script::create_parent_vasp_account`
    * `Script::create_designated_dealer`
    * `Script::rotate_dual_attestation_info`
    """
    return Script(
        code=ROTATE_DUAL_ATTESTATION_INFO_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=new_url), TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_shared_ed25519_public_key_script(public_key: bytes) -> Script:
    """# Summary
    Rotates the authentication key in a `SharedEd25519PublicKey`.

    This transaction can be sent by
    any account that has previously published a shared ed25519 public key using
    `Script::publish_shared_ed25519_public_key`.

    # Technical Description
    This first rotates the public key stored in `account`'s
    `SharedEd25519PublicKey::SharedEd25519PublicKey` resource to `public_key`, after which it
    rotates the authentication key using the capability stored in `account`'s
    `SharedEd25519PublicKey::SharedEd25519PublicKey` to a new value derived from `public_key`

    # Parameters
    | Name         | Type         | Description                                                     |
    | ------       | ------       | -------------                                                   |
    | `account`    | `&signer`    | The signer reference of the sending account of the transaction. |
    | `public_key` | `vector<u8>` | 32-byte Ed25519 public key.                                     |

    # Common Abort Conditions
    | Error Category             | Error Reason                                    | Description                                                                                   |
    | ----------------           | --------------                                  | -------------                                                                                 |
    | `Errors::NOT_PUBLISHED`    | `SharedEd25519PublicKey::ESHARED_KEY`           | A `SharedEd25519PublicKey::SharedEd25519PublicKey` resource is not published under `account`. |
    | `Errors::INVALID_ARGUMENT` | `SharedEd25519PublicKey::EMALFORMED_PUBLIC_KEY` | `public_key` is an invalid ed25519 public key.                                                |

    # Related Scripts
    * `Script::publish_shared_ed25519_public_key`
    """
    return Script(
        code=ROTATE_SHARED_ED25519_PUBLIC_KEY_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=public_key)],
    )


def encode_set_validator_config_and_reconfigure_script(
    validator_account: AccountAddress,
    consensus_pubkey: bytes,
    validator_network_addresses: bytes,
    fullnode_network_addresses: bytes,
) -> Script:
    """# Summary
    Updates a validator's configuration, and triggers a reconfiguration of the system to update the
    validator set with this new validator configuration.

    Can only be successfully sent by a
    Validator Operator account that is already registered with a validator.

    # Technical Description
    This updates the fields with corresponding names held in the `ValidatorConfig::ValidatorConfig`
    config resource held under `validator_account`. It then emits a `DiemConfig::NewEpochEvent` to
    trigger a reconfiguration of the system.  This reconfiguration will update the validator set
    on-chain with the updated `ValidatorConfig::ValidatorConfig`.

    # Parameters
    | Name                          | Type         | Description                                                                                                                  |
    | ------                        | ------       | -------------                                                                                                                |
    | `validator_operator_account`  | `&signer`    | Signer reference of the sending account. Must be the registered validator operator for the validator at `validator_address`. |
    | `validator_account`           | `address`    | The address of the validator's `ValidatorConfig::ValidatorConfig` resource being updated.                                    |
    | `consensus_pubkey`            | `vector<u8>` | New Ed25519 public key to be used in the updated `ValidatorConfig::ValidatorConfig`.                                         |
    | `validator_network_addresses` | `vector<u8>` | New set of `validator_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                       |
    | `fullnode_network_addresses`  | `vector<u8>` | New set of `fullnode_network_addresses` to be used in the updated `ValidatorConfig::ValidatorConfig`.                        |

    # Common Abort Conditions
    | Error Category             | Error Reason                                   | Description                                                                                           |
    | ----------------           | --------------                                 | -------------                                                                                         |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`           | `validator_address` does not have a `ValidatorConfig::ValidatorConfig` resource published under it.   |
    | `Errors::REQUIRES_ROLE`    | `Roles::EVALIDATOR_OPERATOR`                   | `validator_operator_account` does not have a Validator Operator role.                                 |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_TRANSACTION_SENDER` | `validator_operator_account` is not the registered operator for the validator at `validator_address`. |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::EINVALID_CONSENSUS_KEY`      | `consensus_pubkey` is not a valid ed25519 public key.                                                 |
    | `Errors::INVALID_STATE`    | `DiemConfig::EINVALID_BLOCK_TIME`             | An invalid time value was encountered in reconfiguration. Unlikely to occur.                          |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::add_validator_and_reconfigure`
    * `Script::remove_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::register_validator_config`
    """
    return Script(
        code=SET_VALIDATOR_CONFIG_AND_RECONFIGURE_CODE,
        ty_args=[],
        args=[
            TransactionArgument__Address(value=validator_account),
            TransactionArgument__U8Vector(value=consensus_pubkey),
            TransactionArgument__U8Vector(value=validator_network_addresses),
            TransactionArgument__U8Vector(value=fullnode_network_addresses),
        ],
    )


def encode_set_validator_operator_script(operator_name: bytes, operator_account: AccountAddress) -> Script:
    """# Summary
    Sets the validator operator for a validator in the validator's configuration resource "locally"
    and does not reconfigure the system.

    Changes from this transaction will not picked up by the
    system until a reconfiguration of the system is triggered. May only be sent by an account with
    Validator role.

    # Technical Description
    Sets the account at `operator_account` address and with the specified `human_name` as an
    operator for the sending validator account. The account at `operator_account` address must have
    a Validator Operator role and have a `ValidatorOperatorConfig::ValidatorOperatorConfig`
    resource published under it. The sending `account` must be a Validator and have a
    `ValidatorConfig::ValidatorConfig` resource published under it. This script does not emit a
    `DiemConfig::NewEpochEvent` and no reconfiguration of the system is initiated by this script.

    # Parameters
    | Name               | Type         | Description                                                                                  |
    | ------             | ------       | -------------                                                                                |
    | `account`          | `&signer`    | The signer reference of the sending account of the transaction.                              |
    | `operator_name`    | `vector<u8>` | Validator operator's human name.                                                             |
    | `operator_account` | `address`    | Address of the validator operator account to be added as the `account` validator's operator. |

    # Common Abort Conditions
    | Error Category             | Error Reason                                          | Description                                                                                                                                                  |
    | ----------------           | --------------                                        | -------------                                                                                                                                                |
    | `Errors::NOT_PUBLISHED`    | `ValidatorOperatorConfig::EVALIDATOR_OPERATOR_CONFIG` | The `ValidatorOperatorConfig::ValidatorOperatorConfig` resource is not published under `operator_account`.                                                   |
    | 0                          | 0                                                     | The `human_name` field of the `ValidatorOperatorConfig::ValidatorOperatorConfig` resource under `operator_account` does not match the provided `human_name`. |
    | `Errors::REQUIRES_ROLE`    | `Roles::EVALIDATOR`                                   | `account` does not have a Validator account role.                                                                                                            |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::ENOT_A_VALIDATOR_OPERATOR`          | The account at `operator_account` does not have a `ValidatorOperatorConfig::ValidatorOperatorConfig` resource.                                               |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`                  | A `ValidatorConfig::ValidatorConfig` is not published under `account`.                                                                                       |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::add_validator_and_reconfigure`
    * `Script::set_validator_operator_with_nonce_admin`
    * `Script::set_validator_config_and_reconfigure`
    """
    return Script(
        code=SET_VALIDATOR_OPERATOR_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=operator_name), TransactionArgument__Address(value=operator_account)],
    )


def encode_set_validator_operator_with_nonce_admin_script(
    sliding_nonce: st.uint64, operator_name: bytes, operator_account: AccountAddress
) -> Script:
    """# Summary
    Sets the validator operator for a validator in the validator's configuration resource "locally"
    and does not reconfigure the system.

    Changes from this transaction will not picked up by the
    system until a reconfiguration of the system is triggered. May only be sent by the Diem Root
    account as a write set transaction.

    # Technical Description
    Sets the account at `operator_account` address and with the specified `human_name` as an
    operator for the validator `account`. The account at `operator_account` address must have a
    Validator Operator role and have a `ValidatorOperatorConfig::ValidatorOperatorConfig` resource
    published under it. The account represented by the `account` signer must be a Validator and
    have a `ValidatorConfig::ValidatorConfig` resource published under it. No reconfiguration of
    the system is initiated by this script.

    # Parameters
    | Name               | Type         | Description                                                                                                  |
    | ------             | ------       | -------------                                                                                                |
    | `dr_account`       | `&signer`    | The signer reference of the sending account of the write set transaction. May only be the Diem Root signer. |
    | `account`          | `&signer`    | Signer reference of account specified in the `execute_as` field of the write set transaction.                |
    | `sliding_nonce`    | `u64`        | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction for Diem Root.                    |
    | `operator_name`    | `vector<u8>` | Validator operator's human name.                                                                             |
    | `operator_account` | `address`    | Address of the validator operator account to be added as the `account` validator's operator.                 |

    # Common Abort Conditions
    | Error Category             | Error Reason                                          | Description                                                                                                                                                  |
    | ----------------           | --------------                                        | -------------                                                                                                                                                |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                        | A `SlidingNonce` resource is not published under `dr_account`.                                                                                               |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                        | The `sliding_nonce` in `dr_account` is too old and it's impossible to determine if it's duplicated or not.                                                   |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                        | The `sliding_nonce` in `dr_account` is too far in the future.                                                                                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`               | The `sliding_nonce` in` dr_account` has been previously recorded.                                                                                            |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                        | The sending account is not the Diem Root account or Treasury Compliance account                                                                             |
    | `Errors::NOT_PUBLISHED`    | `ValidatorOperatorConfig::EVALIDATOR_OPERATOR_CONFIG` | The `ValidatorOperatorConfig::ValidatorOperatorConfig` resource is not published under `operator_account`.                                                   |
    | 0                          | 0                                                     | The `human_name` field of the `ValidatorOperatorConfig::ValidatorOperatorConfig` resource under `operator_account` does not match the provided `human_name`. |
    | `Errors::REQUIRES_ROLE`    | `Roles::EVALIDATOR`                                   | `account` does not have a Validator account role.                                                                                                            |
    | `Errors::INVALID_ARGUMENT` | `ValidatorConfig::ENOT_A_VALIDATOR_OPERATOR`          | The account at `operator_account` does not have a `ValidatorOperatorConfig::ValidatorOperatorConfig` resource.                                               |
    | `Errors::NOT_PUBLISHED`    | `ValidatorConfig::EVALIDATOR_CONFIG`                  | A `ValidatorConfig::ValidatorConfig` is not published under `account`.                                                                                       |

    # Related Scripts
    * `Script::create_validator_account`
    * `Script::create_validator_operator_account`
    * `Script::register_validator_config`
    * `Script::remove_validator_and_reconfigure`
    * `Script::add_validator_and_reconfigure`
    * `Script::set_validator_operator`
    * `Script::set_validator_config_and_reconfigure`
    """
    return Script(
        code=SET_VALIDATOR_OPERATOR_WITH_NONCE_ADMIN_CODE,
        ty_args=[],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__U8Vector(value=operator_name),
            TransactionArgument__Address(value=operator_account),
        ],
    )


def encode_tiered_mint_script(
    coin_type: TypeTag,
    sliding_nonce: st.uint64,
    designated_dealer_address: AccountAddress,
    mint_amount: st.uint64,
    tier_index: st.uint64,
) -> Script:
    """# Summary
    Mints a specified number of coins in a currency to a Designated Dealer.

    The sending account
    must be the Treasury Compliance account, and coins can only be minted to a Designated Dealer
    account.

    # Technical Description
    Mints `mint_amount` of coins in the `CoinType` currency to Designated Dealer account at
    `designated_dealer_address`. The `tier_index` parameter specifies which tier should be used to
    check verify the off-chain approval policy, and is based in part on the on-chain tier values
    for the specific Designated Dealer, and the number of `CoinType` coins that have been minted to
    the dealer over the past 24 hours. Every Designated Dealer has 4 tiers for each currency that
    they support. The sending `tc_account` must be the Treasury Compliance account, and the
    receiver an authorized Designated Dealer account.

    ## Events
    Successful execution of the transaction will emit two events:
    * A `Diem::MintEvent` with the amount and currency code minted is emitted on the
    `mint_event_handle` in the stored `Diem::CurrencyInfo<CoinType>` resource stored under
    `0xA550C18`; and
    * A `DesignatedDealer::ReceivedMintEvent` with the amount, currency code, and Designated
    Dealer's address is emitted on the `mint_event_handle` in the stored `DesignatedDealer::Dealer`
    resource published under the `designated_dealer_address`.

    # Parameters
    | Name                        | Type      | Description                                                                                                |
    | ------                      | ------    | -------------                                                                                              |
    | `CoinType`                  | Type      | The Move type for the `CoinType` being minted. `CoinType` must be an already-registered currency on-chain. |
    | `tc_account`                | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.  |
    | `sliding_nonce`             | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                 |
    | `designated_dealer_address` | `address` | The address of the Designated Dealer account being minted to.                                              |
    | `mint_amount`               | `u64`     | The number of coins to be minted.                                                                          |
    | `tier_index`                | `u64`     | The mint tier index to use for the Designated Dealer account.                                              |

    # Common Abort Conditions
    | Error Category                | Error Reason                                 | Description                                                                                                                  |
    | ----------------              | --------------                               | -------------                                                                                                                |
    | `Errors::NOT_PUBLISHED`       | `SlidingNonce::ESLIDING_NONCE`               | A `SlidingNonce` resource is not published under `tc_account`.                                                               |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_OLD`               | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not.                                   |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_TOO_NEW`               | The `sliding_nonce` is too far in the future.                                                                                |
    | `Errors::INVALID_ARGUMENT`    | `SlidingNonce::ENONCE_ALREADY_RECORDED`      | The `sliding_nonce` has been previously recorded.                                                                            |
    | `Errors::REQUIRES_ADDRESS`    | `CoreAddresses::ETREASURY_COMPLIANCE`        | `tc_account` is not the Treasury Compliance account.                                                                         |
    | `Errors::REQUIRES_ROLE`       | `Roles::ETREASURY_COMPLIANCE`                | `tc_account` is not the Treasury Compliance account.                                                                         |
    | `Errors::INVALID_ARGUMENT`    | `DesignatedDealer::EINVALID_MINT_AMOUNT`     | `mint_amount` is zero.                                                                                                       |
    | `Errors::NOT_PUBLISHED`       | `DesignatedDealer::EDEALER`                  | `DesignatedDealer::Dealer` or `DesignatedDealer::TierInfo<CoinType>` resource does not exist at `designated_dealer_address`. |
    | `Errors::INVALID_ARGUMENT`    | `DesignatedDealer::EINVALID_TIER_INDEX`      | The `tier_index` is out of bounds.                                                                                           |
    | `Errors::INVALID_ARGUMENT`    | `DesignatedDealer::EINVALID_AMOUNT_FOR_TIER` | `mint_amount` exceeds the maximum allowed amount for `tier_index`.                                                           |
    | `Errors::REQUIRES_CAPABILITY` | `Diem::EMINT_CAPABILITY`                    | `tc_account` does not have a `Diem::MintCapability<CoinType>` resource published under it.                                  |
    | `Errors::INVALID_STATE`       | `Diem::EMINTING_NOT_ALLOWED`                | Minting is not currently allowed for `CoinType` coins.                                                                       |
    | `Errors::LIMIT_EXCEEDED`      | `DiemAccount::EDEPOSIT_EXCEEDS_LIMITS`      | The depositing of the funds would exceed the `account`'s account limits.                                                     |

    # Related Scripts
    * `Script::create_designated_dealer`
    * `Script::peer_to_peer_with_metadata`
    * `Script::rotate_dual_attestation_info`
    """
    return Script(
        code=TIERED_MINT_CODE,
        ty_args=[coin_type],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__Address(value=designated_dealer_address),
            TransactionArgument__U64(value=mint_amount),
            TransactionArgument__U64(value=tier_index),
        ],
    )


def encode_unfreeze_account_script(sliding_nonce: st.uint64, to_unfreeze_account: AccountAddress) -> Script:
    """# Summary
    Unfreezes the account at `address`.

    The sending account of this transaction must be the
    Treasury Compliance account. After the successful execution of this transaction transactions
    may be sent from the previously frozen account, and coins may be sent and received.

    # Technical Description
    Sets the `AccountFreezing::FreezingBit` to `false` and emits a
    `AccountFreezing::UnFreezeAccountEvent`. The transaction sender must be the Treasury Compliance
    account. Note that this is a per-account property so unfreezing a Parent VASP will not effect
    the status any of its child accounts and vice versa.

    ## Events
    Successful execution of this script will emit a `AccountFreezing::UnFreezeAccountEvent` with
    the `unfrozen_address` set the `to_unfreeze_account`'s address.

    # Parameters
    | Name                  | Type      | Description                                                                                               |
    | ------                | ------    | -------------                                                                                             |
    | `tc_account`          | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account. |
    | `sliding_nonce`       | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                |
    | `to_unfreeze_account` | `address` | The account address to be frozen.                                                                         |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                |
    | ----------------           | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `account`.                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`   | The sending account is not the Treasury Compliance account.                                |

    # Related Scripts
    * `Script::freeze_account`
    """
    return Script(
        code=UNFREEZE_ACCOUNT_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__Address(value=to_unfreeze_account)],
    )


def encode_update_diem_version_script(sliding_nonce: st.uint64, major: st.uint64) -> Script:
    """# Summary
    Updates the Diem major version that is stored on-chain and is used by the VM.

    This
    transaction can only be sent from the Diem Root account.

    # Technical Description
    Updates the `DiemVersion` on-chain config and emits a `DiemConfig::NewEpochEvent` to trigger
    a reconfiguration of the system. The `major` version that is passed in must be strictly greater
    than the current major version held on-chain. The VM reads this information and can use it to
    preserve backwards compatibility with previous major versions of the VM.

    # Parameters
    | Name            | Type      | Description                                                                |
    | ------          | ------    | -------------                                                              |
    | `account`       | `&signer` | Signer reference of the sending account. Must be the Diem Root account.   |
    | `sliding_nonce` | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction. |
    | `major`         | `u64`     | The `major` version of the VM to be used from this transaction on.         |

    # Common Abort Conditions
    | Error Category             | Error Reason                                  | Description                                                                                |
    | ----------------           | --------------                                | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`                | A `SlidingNonce` resource is not published under `account`.                                |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`                | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`                | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED`       | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::EDIEM_ROOT`                  | `account` is not the Diem Root account.                                                   |
    | `Errors::INVALID_ARGUMENT` | `DiemVersion::EINVALID_MAJOR_VERSION_NUMBER` | `major` is less-than or equal to the current major version stored on-chain.                |
    """
    return Script(
        code=UPDATE_DIEM_VERSION_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U64(value=major)],
    )


def encode_update_dual_attestation_limit_script(sliding_nonce: st.uint64, new_micro_xdx_limit: st.uint64) -> Script:
    """# Summary
    Update the dual attestation limit on-chain.

    Defined in terms of micro-XDX.  The transaction can
    only be sent by the Treasury Compliance account.  After this transaction all inter-VASP
    payments over this limit must be checked for dual attestation.

    # Technical Description
    Updates the `micro_xdx_limit` field of the `DualAttestation::Limit` resource published under
    `0xA550C18`. The amount is set in micro-XDX.

    # Parameters
    | Name                  | Type      | Description                                                                                               |
    | ------                | ------    | -------------                                                                                             |
    | `tc_account`          | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account. |
    | `sliding_nonce`       | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for this transaction.                                |
    | `new_micro_xdx_limit` | `u64`     | The new dual attestation limit to be used on-chain.                                                       |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                |
    | ----------------           | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`   | `tc_account` is not the Treasury Compliance account.                                       |

    # Related Scripts
    * `Script::update_exchange_rate`
    * `Script::update_minting_ability`
    """
    return Script(
        code=UPDATE_DUAL_ATTESTATION_LIMIT_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U64(value=new_micro_xdx_limit)],
    )


def encode_update_exchange_rate_script(
    currency: TypeTag,
    sliding_nonce: st.uint64,
    new_exchange_rate_numerator: st.uint64,
    new_exchange_rate_denominator: st.uint64,
) -> Script:
    """# Summary
    Update the rough on-chain exchange rate between a specified currency and XDX (as a conversion
    to micro-XDX).

    The transaction can only be sent by the Treasury Compliance account. After this
    transaction the updated exchange rate will be used for normalization of gas prices, and for
    dual attestation checking.

    # Technical Description
    Updates the on-chain exchange rate from the given `Currency` to micro-XDX.  The exchange rate
    is given by `new_exchange_rate_numerator/new_exchange_rate_denominator`.

    # Parameters
    | Name                            | Type      | Description                                                                                                                        |
    | ------                          | ------    | -------------                                                                                                                      |
    | `Currency`                      | Type      | The Move type for the `Currency` whose exchange rate is being updated. `Currency` must be an already-registered currency on-chain. |
    | `tc_account`                    | `&signer` | The signer reference of the sending account of this transaction. Must be the Treasury Compliance account.                          |
    | `sliding_nonce`                 | `u64`     | The `sliding_nonce` (see: `SlidingNonce`) to be used for the transaction.                                                          |
    | `new_exchange_rate_numerator`   | `u64`     | The numerator for the new to micro-XDX exchange rate for `Currency`.                                                               |
    | `new_exchange_rate_denominator` | `u64`     | The denominator for the new to micro-XDX exchange rate for `Currency`.                                                             |

    # Common Abort Conditions
    | Error Category             | Error Reason                            | Description                                                                                |
    | ----------------           | --------------                          | -------------                                                                              |
    | `Errors::NOT_PUBLISHED`    | `SlidingNonce::ESLIDING_NONCE`          | A `SlidingNonce` resource is not published under `tc_account`.                             |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_OLD`          | The `sliding_nonce` is too old and it's impossible to determine if it's duplicated or not. |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_TOO_NEW`          | The `sliding_nonce` is too far in the future.                                              |
    | `Errors::INVALID_ARGUMENT` | `SlidingNonce::ENONCE_ALREADY_RECORDED` | The `sliding_nonce` has been previously recorded.                                          |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE`   | `tc_account` is not the Treasury Compliance account.                                       |
    | `Errors::REQUIRES_ROLE`    | `Roles::ETREASURY_COMPLIANCE`           | `tc_account` is not the Treasury Compliance account.                                       |
    | `Errors::INVALID_ARGUMENT` | `FixedPoint32::EDENOMINATOR`            | `new_exchange_rate_denominator` is zero.                                                   |
    | `Errors::INVALID_ARGUMENT` | `FixedPoint32::ERATIO_OUT_OF_RANGE`     | The quotient is unrepresentable as a `FixedPoint32`.                                       |
    | `Errors::LIMIT_EXCEEDED`   | `FixedPoint32::ERATIO_OUT_OF_RANGE`     | The quotient is unrepresentable as a `FixedPoint32`.                                       |

    # Related Scripts
    * `Script::update_dual_attestation_limit`
    * `Script::update_minting_ability`
    """
    return Script(
        code=UPDATE_EXCHANGE_RATE_CODE,
        ty_args=[currency],
        args=[
            TransactionArgument__U64(value=sliding_nonce),
            TransactionArgument__U64(value=new_exchange_rate_numerator),
            TransactionArgument__U64(value=new_exchange_rate_denominator),
        ],
    )


def encode_update_minting_ability_script(currency: TypeTag, allow_minting: bool) -> Script:
    """# Summary
    Script to allow or disallow minting of new coins in a specified currency.

    This transaction can
    only be sent by the Treasury Compliance account.  Turning minting off for a currency will have
    no effect on coins already in circulation, and coins may still be removed from the system.

    # Technical Description
    This transaction sets the `can_mint` field of the `Diem::CurrencyInfo<Currency>` resource
    published under `0xA550C18` to the value of `allow_minting`. Minting of coins if allowed if
    this field is set to `true` and minting of new coins in `Currency` is disallowed otherwise.
    This transaction needs to be sent by the Treasury Compliance account.

    # Parameters
    | Name            | Type      | Description                                                                                                                          |
    | ------          | ------    | -------------                                                                                                                        |
    | `Currency`      | Type      | The Move type for the `Currency` whose minting ability is being updated. `Currency` must be an already-registered currency on-chain. |
    | `account`       | `&signer` | Signer reference of the sending account. Must be the Diem Root account.                                                             |
    | `allow_minting` | `bool`    | Whether to allow minting of new coins in `Currency`.                                                                                 |

    # Common Abort Conditions
    | Error Category             | Error Reason                          | Description                                          |
    | ----------------           | --------------                        | -------------                                        |
    | `Errors::REQUIRES_ADDRESS` | `CoreAddresses::ETREASURY_COMPLIANCE` | `tc_account` is not the Treasury Compliance account. |
    | `Errors::NOT_PUBLISHED`    | `Diem::ECURRENCY_INFO`               | `Currency` is not a registered currency on-chain.    |

    # Related Scripts
    * `Script::update_dual_attestation_limit`
    * `Script::update_exchange_rate`
    """
    return Script(
        code=UPDATE_MINTING_ABILITY_CODE,
        ty_args=[currency],
        args=[TransactionArgument__Bool(value=allow_minting)],
    )


def decode_add_currency_to_account_script(script: Script) -> ScriptCall:
    return ScriptCall__AddCurrencyToAccount(
        currency=script.ty_args[0],
    )


def decode_add_recovery_rotation_capability_script(script: Script) -> ScriptCall:
    return ScriptCall__AddRecoveryRotationCapability(
        recovery_address=decode_address_argument(script.args[0]),
    )


def decode_add_to_script_allow_list_script(script: Script) -> ScriptCall:
    return ScriptCall__AddToScriptAllowList(
        hash=decode_u8vector_argument(script.args[0]),
        sliding_nonce=decode_u64_argument(script.args[1]),
    )


def decode_add_validator_and_reconfigure_script(script: Script) -> ScriptCall:
    return ScriptCall__AddValidatorAndReconfigure(
        sliding_nonce=decode_u64_argument(script.args[0]),
        validator_name=decode_u8vector_argument(script.args[1]),
        validator_address=decode_address_argument(script.args[2]),
    )


def decode_burn_script(script: Script) -> ScriptCall:
    return ScriptCall__Burn(
        token=script.ty_args[0],
        sliding_nonce=decode_u64_argument(script.args[0]),
        preburn_address=decode_address_argument(script.args[1]),
    )


def decode_burn_txn_fees_script(script: Script) -> ScriptCall:
    return ScriptCall__BurnTxnFees(
        coin_type=script.ty_args[0],
    )


def decode_cancel_burn_script(script: Script) -> ScriptCall:
    return ScriptCall__CancelBurn(
        token=script.ty_args[0],
        preburn_address=decode_address_argument(script.args[0]),
    )


def decode_create_child_vasp_account_script(script: Script) -> ScriptCall:
    return ScriptCall__CreateChildVaspAccount(
        coin_type=script.ty_args[0],
        child_address=decode_address_argument(script.args[0]),
        auth_key_prefix=decode_u8vector_argument(script.args[1]),
        add_all_currencies=decode_bool_argument(script.args[2]),
        child_initial_balance=decode_u64_argument(script.args[3]),
    )


def decode_create_designated_dealer_script(script: Script) -> ScriptCall:
    return ScriptCall__CreateDesignatedDealer(
        currency=script.ty_args[0],
        sliding_nonce=decode_u64_argument(script.args[0]),
        addr=decode_address_argument(script.args[1]),
        auth_key_prefix=decode_u8vector_argument(script.args[2]),
        human_name=decode_u8vector_argument(script.args[3]),
        add_all_currencies=decode_bool_argument(script.args[4]),
    )


def decode_create_parent_vasp_account_script(script: Script) -> ScriptCall:
    return ScriptCall__CreateParentVaspAccount(
        coin_type=script.ty_args[0],
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_account_address=decode_address_argument(script.args[1]),
        auth_key_prefix=decode_u8vector_argument(script.args[2]),
        human_name=decode_u8vector_argument(script.args[3]),
        add_all_currencies=decode_bool_argument(script.args[4]),
    )


def decode_create_recovery_address_script(_script: Script) -> ScriptCall:
    return ScriptCall__CreateRecoveryAddress()


def decode_create_validator_account_script(script: Script) -> ScriptCall:
    return ScriptCall__CreateValidatorAccount(
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_account_address=decode_address_argument(script.args[1]),
        auth_key_prefix=decode_u8vector_argument(script.args[2]),
        human_name=decode_u8vector_argument(script.args[3]),
    )


def decode_create_validator_operator_account_script(script: Script) -> ScriptCall:
    return ScriptCall__CreateValidatorOperatorAccount(
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_account_address=decode_address_argument(script.args[1]),
        auth_key_prefix=decode_u8vector_argument(script.args[2]),
        human_name=decode_u8vector_argument(script.args[3]),
    )


def decode_freeze_account_script(script: Script) -> ScriptCall:
    return ScriptCall__FreezeAccount(
        sliding_nonce=decode_u64_argument(script.args[0]),
        to_freeze_account=decode_address_argument(script.args[1]),
    )


def decode_peer_to_peer_with_metadata_script(script: Script) -> ScriptCall:
    return ScriptCall__PeerToPeerWithMetadata(
        currency=script.ty_args[0],
        payee=decode_address_argument(script.args[0]),
        amount=decode_u64_argument(script.args[1]),
        metadata=decode_u8vector_argument(script.args[2]),
        metadata_signature=decode_u8vector_argument(script.args[3]),
    )


def decode_preburn_script(script: Script) -> ScriptCall:
    return ScriptCall__Preburn(
        token=script.ty_args[0],
        amount=decode_u64_argument(script.args[0]),
    )


def decode_publish_shared_ed25519_public_key_script(script: Script) -> ScriptCall:
    return ScriptCall__PublishSharedEd25519PublicKey(
        public_key=decode_u8vector_argument(script.args[0]),
    )


def decode_register_validator_config_script(script: Script) -> ScriptCall:
    return ScriptCall__RegisterValidatorConfig(
        validator_account=decode_address_argument(script.args[0]),
        consensus_pubkey=decode_u8vector_argument(script.args[1]),
        validator_network_addresses=decode_u8vector_argument(script.args[2]),
        fullnode_network_addresses=decode_u8vector_argument(script.args[3]),
    )


def decode_remove_validator_and_reconfigure_script(script: Script) -> ScriptCall:
    return ScriptCall__RemoveValidatorAndReconfigure(
        sliding_nonce=decode_u64_argument(script.args[0]),
        validator_name=decode_u8vector_argument(script.args[1]),
        validator_address=decode_address_argument(script.args[2]),
    )


def decode_rotate_authentication_key_script(script: Script) -> ScriptCall:
    return ScriptCall__RotateAuthenticationKey(
        new_key=decode_u8vector_argument(script.args[0]),
    )


def decode_rotate_authentication_key_with_nonce_script(script: Script) -> ScriptCall:
    return ScriptCall__RotateAuthenticationKeyWithNonce(
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_key=decode_u8vector_argument(script.args[1]),
    )


def decode_rotate_authentication_key_with_nonce_admin_script(script: Script) -> ScriptCall:
    return ScriptCall__RotateAuthenticationKeyWithNonceAdmin(
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_key=decode_u8vector_argument(script.args[1]),
    )


def decode_rotate_authentication_key_with_recovery_address_script(script: Script) -> ScriptCall:
    return ScriptCall__RotateAuthenticationKeyWithRecoveryAddress(
        recovery_address=decode_address_argument(script.args[0]),
        to_recover=decode_address_argument(script.args[1]),
        new_key=decode_u8vector_argument(script.args[2]),
    )


def decode_rotate_dual_attestation_info_script(script: Script) -> ScriptCall:
    return ScriptCall__RotateDualAttestationInfo(
        new_url=decode_u8vector_argument(script.args[0]),
        new_key=decode_u8vector_argument(script.args[1]),
    )


def decode_rotate_shared_ed25519_public_key_script(script: Script) -> ScriptCall:
    return ScriptCall__RotateSharedEd25519PublicKey(
        public_key=decode_u8vector_argument(script.args[0]),
    )


def decode_set_validator_config_and_reconfigure_script(script: Script) -> ScriptCall:
    return ScriptCall__SetValidatorConfigAndReconfigure(
        validator_account=decode_address_argument(script.args[0]),
        consensus_pubkey=decode_u8vector_argument(script.args[1]),
        validator_network_addresses=decode_u8vector_argument(script.args[2]),
        fullnode_network_addresses=decode_u8vector_argument(script.args[3]),
    )


def decode_set_validator_operator_script(script: Script) -> ScriptCall:
    return ScriptCall__SetValidatorOperator(
        operator_name=decode_u8vector_argument(script.args[0]),
        operator_account=decode_address_argument(script.args[1]),
    )


def decode_set_validator_operator_with_nonce_admin_script(script: Script) -> ScriptCall:
    return ScriptCall__SetValidatorOperatorWithNonceAdmin(
        sliding_nonce=decode_u64_argument(script.args[0]),
        operator_name=decode_u8vector_argument(script.args[1]),
        operator_account=decode_address_argument(script.args[2]),
    )


def decode_tiered_mint_script(script: Script) -> ScriptCall:
    return ScriptCall__TieredMint(
        coin_type=script.ty_args[0],
        sliding_nonce=decode_u64_argument(script.args[0]),
        designated_dealer_address=decode_address_argument(script.args[1]),
        mint_amount=decode_u64_argument(script.args[2]),
        tier_index=decode_u64_argument(script.args[3]),
    )


def decode_unfreeze_account_script(script: Script) -> ScriptCall:
    return ScriptCall__UnfreezeAccount(
        sliding_nonce=decode_u64_argument(script.args[0]),
        to_unfreeze_account=decode_address_argument(script.args[1]),
    )


def decode_update_diem_version_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateDiemVersion(
        sliding_nonce=decode_u64_argument(script.args[0]),
        major=decode_u64_argument(script.args[1]),
    )


def decode_update_dual_attestation_limit_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateDualAttestationLimit(
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_micro_xdx_limit=decode_u64_argument(script.args[1]),
    )


def decode_update_exchange_rate_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateExchangeRate(
        currency=script.ty_args[0],
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_exchange_rate_numerator=decode_u64_argument(script.args[1]),
        new_exchange_rate_denominator=decode_u64_argument(script.args[2]),
    )


def decode_update_minting_ability_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateMintingAbility(
        currency=script.ty_args[0],
        allow_minting=decode_bool_argument(script.args[0]),
    )


ADD_CURRENCY_TO_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x07\x07\x11\x19\x08\x2a\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x01\x06\x0c\x00\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x61\x64\x64\x5f\x63\x75\x72\x72\x65\x6e\x63\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x03\x0b\x00\x38\x00\x02"

ADD_RECOVERY_ROTATION_CAPABILITY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x0a\x05\x12\x0f\x07\x21\x6a\x08\x8b\x01\x10\x00\x00\x00\x01\x00\x02\x01\x00\x00\x03\x00\x01\x00\x01\x04\x02\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x08\x00\x05\x00\x02\x06\x0c\x05\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0f\x52\x65\x63\x6f\x76\x65\x72\x79\x41\x64\x64\x72\x65\x73\x73\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x17\x61\x64\x64\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04\x03\x05\x0b\x00\x11\x00\x0a\x01\x11\x01\x02"

ADD_TO_SCRIPT_ALLOW_LIST_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x10\x07\x1e\x5c\x08\x7a\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x02\x01\x00\x02\x06\x0c\x0a\x02\x00\x02\x06\x0c\x03\x03\x06\x0c\x0a\x02\x03\x1f\x44\x69\x65\x6d\x54\x72\x61\x6e\x73\x61\x63\x74\x69\x6f\x6e\x50\x75\x62\x6c\x69\x73\x68\x69\x6e\x67\x4f\x70\x74\x69\x6f\x6e\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x18\x61\x64\x64\x5f\x74\x6f\x5f\x73\x63\x72\x69\x70\x74\x5f\x61\x6c\x6c\x6f\x77\x5f\x6c\x69\x73\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x07\x0a\x00\x0a\x02\x11\x01\x0b\x00\x0b\x01\x11\x00\x02"

ADD_VALIDATOR_AND_RECONFIGURE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x06\x03\x06\x0f\x05\x15\x18\x07\x2d\x5b\x08\x88\x01\x10\x00\x00\x00\x01\x00\x02\x01\x03\x00\x01\x00\x02\x04\x02\x03\x00\x00\x05\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x04\x06\x0c\x03\x0a\x02\x05\x02\x01\x03\x0a\x44\x69\x65\x6d\x53\x79\x73\x74\x65\x6d\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x0d\x61\x64\x64\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x06\x12\x0a\x00\x0a\x01\x11\x00\x0a\x03\x11\x01\x0b\x02\x21\x0c\x04\x0b\x04\x03\x0e\x0b\x00\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x00\x0a\x03\x11\x02\x02"

BURN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x11\x07\x22\x2d\x08\x4f\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x02\x06\x0c\x05\x03\x06\x0c\x03\x05\x01\x09\x00\x04\x44\x69\x65\x6d\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x04\x62\x75\x72\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x07\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x38\x00\x02"

BURN_TXN_FEES_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x07\x07\x11\x19\x08\x2a\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x01\x06\x0c\x00\x01\x09\x00\x0e\x54\x72\x61\x6e\x73\x61\x63\x74\x69\x6f\x6e\x46\x65\x65\x09\x62\x75\x72\x6e\x5f\x66\x65\x65\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x03\x0b\x00\x38\x00\x02"

CANCEL_BURN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x08\x07\x12\x18\x08\x2a\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x02\x06\x0c\x05\x00\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0b\x63\x61\x6e\x63\x65\x6c\x5f\x62\x75\x72\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x04\x0b\x00\x0a\x01\x38\x00\x02"

CREATE_CHILD_VASP_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x08\x01\x00\x02\x02\x02\x04\x03\x06\x16\x04\x1c\x04\x05\x20\x23\x07\x43\x7a\x08\xbd\x01\x10\x06\xcd\x01\x04\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x01\x01\x00\x03\x02\x03\x00\x00\x04\x04\x01\x01\x01\x00\x05\x03\x01\x00\x00\x06\x02\x06\x04\x06\x0c\x05\x0a\x02\x01\x00\x01\x06\x0c\x01\x08\x00\x05\x06\x08\x00\x05\x03\x0a\x02\x0a\x02\x05\x06\x0c\x05\x0a\x02\x01\x03\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x63\x72\x65\x61\x74\x65\x5f\x63\x68\x69\x6c\x64\x5f\x76\x61\x73\x70\x5f\x61\x63\x63\x6f\x75\x6e\x74\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x08\x70\x61\x79\x5f\x66\x72\x6f\x6d\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x0a\x02\x01\x00\x01\x01\x05\x03\x19\x0a\x00\x0a\x01\x0b\x02\x0a\x03\x38\x00\x0a\x04\x06\x00\x00\x00\x00\x00\x00\x00\x00\x24\x03\x0a\x05\x16\x0b\x00\x11\x01\x0c\x05\x0e\x05\x0a\x01\x0a\x04\x07\x00\x07\x00\x38\x01\x0b\x05\x11\x03\x05\x18\x0b\x00\x01\x02"

CREATE_DESIGNATED_DEALER_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x1b\x07\x2c\x48\x08\x74\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x01\x06\x06\x0c\x03\x05\x0a\x02\x0a\x02\x01\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x18\x63\x72\x65\x61\x74\x65\x5f\x64\x65\x73\x69\x67\x6e\x61\x74\x65\x64\x5f\x64\x65\x61\x6c\x65\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x0a\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x0a\x05\x38\x00\x02"

CREATE_PARENT_VASP_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x1b\x07\x2c\x4a\x08\x76\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x01\x06\x06\x0c\x03\x05\x0a\x02\x0a\x02\x01\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x1a\x63\x72\x65\x61\x74\x65\x5f\x70\x61\x72\x65\x6e\x74\x5f\x76\x61\x73\x70\x5f\x61\x63\x63\x6f\x75\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x0a\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x0a\x05\x38\x00\x02"

CREATE_RECOVERY_ADDRESS_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x0a\x05\x12\x0c\x07\x1e\x5a\x08\x78\x10\x00\x00\x00\x01\x00\x02\x01\x00\x00\x03\x00\x01\x00\x01\x04\x02\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x06\x0c\x08\x00\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0f\x52\x65\x63\x6f\x76\x65\x72\x79\x41\x64\x64\x72\x65\x73\x73\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x07\x70\x75\x62\x6c\x69\x73\x68\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x03\x05\x0a\x00\x0b\x00\x11\x00\x11\x01\x02"

CREATE_VALIDATOR_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x16\x07\x24\x48\x08\x6c\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x00\x02\x06\x0c\x03\x00\x04\x06\x0c\x05\x0a\x02\x0a\x02\x05\x06\x0c\x03\x05\x0a\x02\x0a\x02\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x18\x63\x72\x65\x61\x74\x65\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x5f\x61\x63\x63\x6f\x75\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x09\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x11\x01\x02"

CREATE_VALIDATOR_OPERATOR_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x16\x07\x24\x51\x08\x75\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x00\x02\x06\x0c\x03\x00\x04\x06\x0c\x05\x0a\x02\x0a\x02\x05\x06\x0c\x03\x05\x0a\x02\x0a\x02\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x21\x63\x72\x65\x61\x74\x65\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x5f\x6f\x70\x65\x72\x61\x74\x6f\x72\x5f\x61\x63\x63\x6f\x75\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x09\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x11\x01\x02"

FREEZE_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0e\x07\x1c\x42\x08\x5e\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x02\x01\x00\x02\x06\x0c\x05\x00\x02\x06\x0c\x03\x03\x06\x0c\x03\x05\x0f\x41\x63\x63\x6f\x75\x6e\x74\x46\x72\x65\x65\x7a\x69\x6e\x67\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0e\x66\x72\x65\x65\x7a\x65\x5f\x61\x63\x63\x6f\x75\x6e\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

PEER_TO_PEER_WITH_METADATA_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x07\x01\x00\x02\x02\x02\x04\x03\x06\x10\x04\x16\x02\x05\x18\x1d\x07\x35\x60\x08\x95\x01\x10\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x00\x00\x03\x02\x03\x01\x01\x00\x04\x01\x03\x00\x01\x05\x01\x06\x0c\x01\x08\x00\x05\x06\x08\x00\x05\x03\x0a\x02\x0a\x02\x00\x05\x06\x0c\x05\x03\x0a\x02\x0a\x02\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x08\x70\x61\x79\x5f\x66\x72\x6f\x6d\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x04\x01\x0c\x0b\x00\x11\x00\x0c\x05\x0e\x05\x0a\x01\x0a\x02\x0b\x03\x0b\x04\x38\x00\x0b\x05\x11\x02\x02"

PREBURN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x07\x01\x00\x02\x02\x02\x04\x03\x06\x10\x04\x16\x02\x05\x18\x15\x07\x2d\x5f\x08\x8c\x01\x10\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x00\x00\x03\x02\x03\x01\x01\x00\x04\x01\x03\x00\x01\x05\x01\x06\x0c\x01\x08\x00\x03\x06\x0c\x06\x08\x00\x03\x00\x02\x06\x0c\x03\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x07\x70\x72\x65\x62\x75\x72\x6e\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x04\x01\x0a\x0a\x00\x11\x00\x0c\x02\x0b\x00\x0e\x02\x0a\x01\x38\x00\x0b\x02\x11\x02\x02"

PUBLISH_SHARED_ED25519_PUBLIC_KEY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x06\x07\x0d\x1f\x08\x2c\x10\x00\x00\x00\x01\x00\x01\x00\x02\x06\x0c\x0a\x02\x00\x16\x53\x68\x61\x72\x65\x64\x45\x64\x32\x35\x35\x31\x39\x50\x75\x62\x6c\x69\x63\x4b\x65\x79\x07\x70\x75\x62\x6c\x69\x73\x68\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x04\x0b\x00\x0b\x01\x11\x00\x02"

REGISTER_VALIDATOR_CONFIG_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x0b\x07\x12\x1b\x08\x2d\x10\x00\x00\x00\x01\x00\x01\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x0a\x02\x00\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x0a\x73\x65\x74\x5f\x63\x6f\x6e\x66\x69\x67\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x07\x0b\x00\x0a\x01\x0b\x02\x0b\x03\x0b\x04\x11\x00\x02"

REMOVE_VALIDATOR_AND_RECONFIGURE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x06\x03\x06\x0f\x05\x15\x18\x07\x2d\x5e\x08\x8b\x01\x10\x00\x00\x00\x01\x00\x02\x01\x03\x00\x01\x00\x02\x04\x02\x03\x00\x00\x05\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x04\x06\x0c\x03\x0a\x02\x05\x02\x01\x03\x0a\x44\x69\x65\x6d\x53\x79\x73\x74\x65\x6d\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x10\x72\x65\x6d\x6f\x76\x65\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x06\x12\x0a\x00\x0a\x01\x11\x00\x0a\x03\x11\x01\x0b\x02\x21\x0c\x04\x0b\x04\x03\x0e\x0b\x00\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x00\x0a\x03\x11\x02\x02"

ROTATE_AUTHENTICATION_KEY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x02\x02\x04\x03\x06\x0f\x05\x15\x12\x07\x27\x7c\x08\xa3\x01\x10\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x00\x00\x03\x01\x02\x00\x00\x04\x03\x02\x00\x01\x06\x0c\x01\x08\x00\x00\x02\x06\x08\x00\x0a\x02\x02\x06\x0c\x0a\x02\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x72\x65\x73\x74\x6f\x72\x65\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04\x01\x09\x0b\x00\x11\x00\x0c\x02\x0e\x02\x0b\x01\x11\x02\x0b\x02\x11\x01\x02"

ROTATE_AUTHENTICATION_KEY_WITH_NONCE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x14\x05\x1c\x17\x07\x33\x9f\x01\x08\xd2\x01\x10\x00\x00\x00\x01\x00\x03\x01\x00\x01\x02\x00\x01\x00\x00\x04\x02\x03\x00\x00\x05\x03\x01\x00\x00\x06\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x06\x08\x00\x0a\x02\x03\x06\x0c\x03\x0a\x02\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x72\x65\x73\x74\x6f\x72\x65\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x03\x0c\x0a\x00\x0a\x01\x11\x00\x0b\x00\x11\x01\x0c\x03\x0e\x03\x0b\x02\x11\x03\x0b\x03\x11\x02\x02"

ROTATE_AUTHENTICATION_KEY_WITH_NONCE_ADMIN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x14\x05\x1c\x19\x07\x35\x9f\x01\x08\xd4\x01\x10\x00\x00\x00\x01\x00\x03\x01\x00\x01\x02\x00\x01\x00\x00\x04\x02\x03\x00\x00\x05\x03\x01\x00\x00\x06\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x06\x08\x00\x0a\x02\x04\x06\x0c\x06\x0c\x03\x0a\x02\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x72\x65\x73\x74\x6f\x72\x65\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x03\x0c\x0b\x00\x0a\x02\x11\x00\x0b\x01\x11\x01\x0c\x04\x0e\x04\x0b\x03\x11\x03\x0b\x04\x11\x02\x02"

ROTATE_AUTHENTICATION_KEY_WITH_RECOVERY_ADDRESS_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x08\x07\x0f\x2a\x08\x39\x10\x00\x00\x00\x01\x00\x01\x00\x04\x06\x0c\x05\x05\x0a\x02\x00\x0f\x52\x65\x63\x6f\x76\x65\x72\x79\x41\x64\x64\x72\x65\x73\x73\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x06\x0b\x00\x0a\x01\x0a\x02\x0b\x03\x11\x00\x02"

ROTATE_DUAL_ATTESTATION_INFO_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x0a\x05\x0c\x0d\x07\x19\x3d\x08\x56\x10\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00\x01\x00\x02\x06\x0c\x0a\x02\x00\x03\x06\x0c\x0a\x02\x0a\x02\x0f\x44\x75\x61\x6c\x41\x74\x74\x65\x73\x74\x61\x74\x69\x6f\x6e\x0f\x72\x6f\x74\x61\x74\x65\x5f\x62\x61\x73\x65\x5f\x75\x72\x6c\x1c\x72\x6f\x74\x61\x74\x65\x5f\x63\x6f\x6d\x70\x6c\x69\x61\x6e\x63\x65\x5f\x70\x75\x62\x6c\x69\x63\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x07\x0a\x00\x0b\x01\x11\x00\x0b\x00\x0b\x02\x11\x01\x02"

ROTATE_SHARED_ED25519_PUBLIC_KEY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x06\x07\x0d\x22\x08\x2f\x10\x00\x00\x00\x01\x00\x01\x00\x02\x06\x0c\x0a\x02\x00\x16\x53\x68\x61\x72\x65\x64\x45\x64\x32\x35\x35\x31\x39\x50\x75\x62\x6c\x69\x63\x4b\x65\x79\x0a\x72\x6f\x74\x61\x74\x65\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x04\x0b\x00\x0b\x01\x11\x00\x02"

SET_VALIDATOR_CONFIG_AND_RECONFIGURE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0f\x07\x1d\x44\x08\x61\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x0a\x02\x00\x02\x06\x0c\x05\x0a\x44\x69\x65\x6d\x53\x79\x73\x74\x65\x6d\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x0a\x73\x65\x74\x5f\x63\x6f\x6e\x66\x69\x67\x1d\x75\x70\x64\x61\x74\x65\x5f\x63\x6f\x6e\x66\x69\x67\x5f\x61\x6e\x64\x5f\x72\x65\x63\x6f\x6e\x66\x69\x67\x75\x72\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x0a\x0a\x00\x0a\x01\x0b\x02\x0b\x03\x0b\x04\x11\x00\x0b\x00\x0a\x01\x11\x01\x02"

SET_VALIDATOR_OPERATOR_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x13\x07\x21\x44\x08\x65\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x00\x03\x06\x0c\x0a\x02\x05\x02\x01\x03\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x17\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x4f\x70\x65\x72\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x0c\x73\x65\x74\x5f\x6f\x70\x65\x72\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04\x05\x0f\x0a\x02\x11\x00\x0b\x01\x21\x0c\x03\x0b\x03\x03\x0b\x0b\x00\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x00\x0a\x02\x11\x01\x02"

SET_VALIDATOR_OPERATOR_WITH_NONCE_ADMIN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x06\x03\x06\x0f\x05\x15\x1a\x07\x2f\x67\x08\x96\x01\x10\x00\x00\x00\x01\x00\x02\x00\x03\x00\x01\x00\x02\x04\x02\x03\x00\x01\x05\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x05\x06\x0c\x06\x0c\x03\x0a\x02\x05\x02\x01\x03\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x17\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x4f\x70\x65\x72\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x0c\x73\x65\x74\x5f\x6f\x70\x65\x72\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x06\x12\x0b\x00\x0a\x02\x11\x00\x0a\x04\x11\x01\x0b\x03\x21\x0c\x05\x0b\x05\x03\x0e\x0b\x01\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x01\x0a\x04\x11\x02\x02"

TIERED_MINT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x15\x07\x26\x3b\x08\x61\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x04\x06\x0c\x05\x03\x03\x05\x06\x0c\x03\x05\x03\x03\x01\x09\x00\x0b\x44\x69\x65\x6d\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0b\x74\x69\x65\x72\x65\x64\x5f\x6d\x69\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x09\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0a\x03\x0a\x04\x38\x00\x02"

UNFREEZE_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0e\x07\x1c\x44\x08\x60\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x02\x01\x00\x02\x06\x0c\x05\x00\x02\x06\x0c\x03\x03\x06\x0c\x03\x05\x0f\x41\x63\x63\x6f\x75\x6e\x74\x46\x72\x65\x65\x7a\x69\x6e\x67\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x10\x75\x6e\x66\x72\x65\x65\x7a\x65\x5f\x61\x63\x63\x6f\x75\x6e\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

UPDATE_DIEM_VERSION_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0a\x07\x18\x33\x08\x4b\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x00\x01\x00\x02\x06\x0c\x03\x00\x03\x06\x0c\x03\x03\x0b\x44\x69\x65\x6d\x56\x65\x72\x73\x69\x6f\x6e\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x03\x73\x65\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

UPDATE_DUAL_ATTESTATION_LIMIT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0a\x07\x18\x47\x08\x5f\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x00\x01\x00\x02\x06\x0c\x03\x00\x03\x06\x0c\x03\x03\x0f\x44\x75\x61\x6c\x41\x74\x74\x65\x73\x74\x61\x74\x69\x6f\x6e\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x13\x73\x65\x74\x5f\x6d\x69\x63\x72\x6f\x64\x69\x65\x6d\x5f\x6c\x69\x6d\x69\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

UPDATE_EXCHANGE_RATE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x07\x01\x00\x06\x02\x06\x04\x03\x0a\x10\x04\x1a\x02\x05\x1c\x19\x07\x35\x63\x08\x98\x01\x10\x00\x00\x00\x01\x00\x02\x01\x01\x02\x00\x01\x03\x00\x01\x00\x02\x04\x02\x03\x00\x00\x05\x04\x03\x01\x01\x02\x06\x02\x03\x03\x01\x08\x00\x02\x06\x0c\x03\x00\x02\x06\x0c\x08\x00\x04\x06\x0c\x03\x03\x03\x01\x09\x00\x04\x44\x69\x65\x6d\x0c\x46\x69\x78\x65\x64\x50\x6f\x69\x6e\x74\x33\x32\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x14\x63\x72\x65\x61\x74\x65\x5f\x66\x72\x6f\x6d\x5f\x72\x61\x74\x69\x6f\x6e\x61\x6c\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x18\x75\x70\x64\x61\x74\x65\x5f\x78\x64\x78\x5f\x65\x78\x63\x68\x61\x6e\x67\x65\x5f\x72\x61\x74\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x05\x01\x0b\x0a\x00\x0a\x01\x11\x01\x0a\x02\x0a\x03\x11\x00\x0c\x04\x0b\x00\x0b\x04\x38\x00\x02"

UPDATE_MINTING_ABILITY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x08\x07\x12\x1c\x08\x2e\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x02\x06\x0c\x01\x00\x01\x09\x00\x04\x44\x69\x65\x6d\x16\x75\x70\x64\x61\x74\x65\x5f\x6d\x69\x6e\x74\x69\x6e\x67\x5f\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x04\x0b\x00\x0a\x01\x38\x00\x02"

# pyre-ignore
SCRIPT_ENCODER_MAP: typing.Dict[typing.Type[ScriptCall], typing.Callable[[ScriptCall], Script]] = {
    ScriptCall__AddCurrencyToAccount: encode_add_currency_to_account_script,
    ScriptCall__AddRecoveryRotationCapability: encode_add_recovery_rotation_capability_script,
    ScriptCall__AddToScriptAllowList: encode_add_to_script_allow_list_script,
    ScriptCall__AddValidatorAndReconfigure: encode_add_validator_and_reconfigure_script,
    ScriptCall__Burn: encode_burn_script,
    ScriptCall__BurnTxnFees: encode_burn_txn_fees_script,
    ScriptCall__CancelBurn: encode_cancel_burn_script,
    ScriptCall__CreateChildVaspAccount: encode_create_child_vasp_account_script,
    ScriptCall__CreateDesignatedDealer: encode_create_designated_dealer_script,
    ScriptCall__CreateParentVaspAccount: encode_create_parent_vasp_account_script,
    ScriptCall__CreateRecoveryAddress: encode_create_recovery_address_script,
    ScriptCall__CreateValidatorAccount: encode_create_validator_account_script,
    ScriptCall__CreateValidatorOperatorAccount: encode_create_validator_operator_account_script,
    ScriptCall__FreezeAccount: encode_freeze_account_script,
    ScriptCall__PeerToPeerWithMetadata: encode_peer_to_peer_with_metadata_script,
    ScriptCall__Preburn: encode_preburn_script,
    ScriptCall__PublishSharedEd25519PublicKey: encode_publish_shared_ed25519_public_key_script,
    ScriptCall__RegisterValidatorConfig: encode_register_validator_config_script,
    ScriptCall__RemoveValidatorAndReconfigure: encode_remove_validator_and_reconfigure_script,
    ScriptCall__RotateAuthenticationKey: encode_rotate_authentication_key_script,
    ScriptCall__RotateAuthenticationKeyWithNonce: encode_rotate_authentication_key_with_nonce_script,
    ScriptCall__RotateAuthenticationKeyWithNonceAdmin: encode_rotate_authentication_key_with_nonce_admin_script,
    ScriptCall__RotateAuthenticationKeyWithRecoveryAddress: encode_rotate_authentication_key_with_recovery_address_script,
    ScriptCall__RotateDualAttestationInfo: encode_rotate_dual_attestation_info_script,
    ScriptCall__RotateSharedEd25519PublicKey: encode_rotate_shared_ed25519_public_key_script,
    ScriptCall__SetValidatorConfigAndReconfigure: encode_set_validator_config_and_reconfigure_script,
    ScriptCall__SetValidatorOperator: encode_set_validator_operator_script,
    ScriptCall__SetValidatorOperatorWithNonceAdmin: encode_set_validator_operator_with_nonce_admin_script,
    ScriptCall__TieredMint: encode_tiered_mint_script,
    ScriptCall__UnfreezeAccount: encode_unfreeze_account_script,
    ScriptCall__UpdateDiemVersion: encode_update_diem_version_script,
    ScriptCall__UpdateDualAttestationLimit: encode_update_dual_attestation_limit_script,
    ScriptCall__UpdateExchangeRate: encode_update_exchange_rate_script,
    ScriptCall__UpdateMintingAbility: encode_update_minting_ability_script,
}


SCRIPT_DECODER_MAP: typing.Dict[bytes, typing.Callable[[Script], ScriptCall]] = {
    ADD_CURRENCY_TO_ACCOUNT_CODE: decode_add_currency_to_account_script,
    ADD_RECOVERY_ROTATION_CAPABILITY_CODE: decode_add_recovery_rotation_capability_script,
    ADD_TO_SCRIPT_ALLOW_LIST_CODE: decode_add_to_script_allow_list_script,
    ADD_VALIDATOR_AND_RECONFIGURE_CODE: decode_add_validator_and_reconfigure_script,
    BURN_CODE: decode_burn_script,
    BURN_TXN_FEES_CODE: decode_burn_txn_fees_script,
    CANCEL_BURN_CODE: decode_cancel_burn_script,
    CREATE_CHILD_VASP_ACCOUNT_CODE: decode_create_child_vasp_account_script,
    CREATE_DESIGNATED_DEALER_CODE: decode_create_designated_dealer_script,
    CREATE_PARENT_VASP_ACCOUNT_CODE: decode_create_parent_vasp_account_script,
    CREATE_RECOVERY_ADDRESS_CODE: decode_create_recovery_address_script,
    CREATE_VALIDATOR_ACCOUNT_CODE: decode_create_validator_account_script,
    CREATE_VALIDATOR_OPERATOR_ACCOUNT_CODE: decode_create_validator_operator_account_script,
    FREEZE_ACCOUNT_CODE: decode_freeze_account_script,
    PEER_TO_PEER_WITH_METADATA_CODE: decode_peer_to_peer_with_metadata_script,
    PREBURN_CODE: decode_preburn_script,
    PUBLISH_SHARED_ED25519_PUBLIC_KEY_CODE: decode_publish_shared_ed25519_public_key_script,
    REGISTER_VALIDATOR_CONFIG_CODE: decode_register_validator_config_script,
    REMOVE_VALIDATOR_AND_RECONFIGURE_CODE: decode_remove_validator_and_reconfigure_script,
    ROTATE_AUTHENTICATION_KEY_CODE: decode_rotate_authentication_key_script,
    ROTATE_AUTHENTICATION_KEY_WITH_NONCE_CODE: decode_rotate_authentication_key_with_nonce_script,
    ROTATE_AUTHENTICATION_KEY_WITH_NONCE_ADMIN_CODE: decode_rotate_authentication_key_with_nonce_admin_script,
    ROTATE_AUTHENTICATION_KEY_WITH_RECOVERY_ADDRESS_CODE: decode_rotate_authentication_key_with_recovery_address_script,
    ROTATE_DUAL_ATTESTATION_INFO_CODE: decode_rotate_dual_attestation_info_script,
    ROTATE_SHARED_ED25519_PUBLIC_KEY_CODE: decode_rotate_shared_ed25519_public_key_script,
    SET_VALIDATOR_CONFIG_AND_RECONFIGURE_CODE: decode_set_validator_config_and_reconfigure_script,
    SET_VALIDATOR_OPERATOR_CODE: decode_set_validator_operator_script,
    SET_VALIDATOR_OPERATOR_WITH_NONCE_ADMIN_CODE: decode_set_validator_operator_with_nonce_admin_script,
    TIERED_MINT_CODE: decode_tiered_mint_script,
    UNFREEZE_ACCOUNT_CODE: decode_unfreeze_account_script,
    UPDATE_DIEM_VERSION_CODE: decode_update_diem_version_script,
    UPDATE_DUAL_ATTESTATION_LIMIT_CODE: decode_update_dual_attestation_limit_script,
    UPDATE_EXCHANGE_RATE_CODE: decode_update_exchange_rate_script,
    UPDATE_MINTING_ABILITY_CODE: decode_update_minting_ability_script,
}


def decode_bool_argument(arg: TransactionArgument) -> bool:
    if not isinstance(arg, TransactionArgument__Bool):
        raise ValueError("Was expecting a Bool argument")
    return arg.value


def decode_u64_argument(arg: TransactionArgument) -> st.uint64:
    if not isinstance(arg, TransactionArgument__U64):
        raise ValueError("Was expecting a U64 argument")
    return arg.value


def decode_address_argument(arg: TransactionArgument) -> AccountAddress:
    if not isinstance(arg, TransactionArgument__Address):
        raise ValueError("Was expecting a Address argument")
    return arg.value


def decode_u8vector_argument(arg: TransactionArgument) -> bytes:
    if not isinstance(arg, TransactionArgument__U8Vector):
        raise ValueError("Was expecting a U8Vector argument")
    return arg.value
