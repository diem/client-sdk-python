# pyre-strict
from dataclasses import dataclass
import typing
from pylibra import serde_types as st
from pylibra import libra_types


from pylibra.libra_types import (
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


class ScriptCall:
    """Structured representation of a call into a known Move script."""

    pass


@dataclass
class ScriptCall__AddCurrencyToAccount(ScriptCall):
    """Add a `Currency` balance to `account`, which will enable `account` to send and receive
    `Libra<Currency>`.

    Aborts with NOT_A_CURRENCY if `Currency` is not an accepted currency type in the Libra system
    Aborts with `LibraAccount::ADD_EXISTING_CURRENCY` if the account already holds a balance in
    `Currency`.
    """

    currency: libra_types.TypeTag


@dataclass
class ScriptCall__AddRecoveryRotationCapability(ScriptCall):
    """Add the `KeyRotationCapability` for `to_recover_account` to the `RecoveryAddress` resource under `recovery_address`.

    ## Aborts
    * Aborts with `LibraAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` if `account` has already delegated its `KeyRotationCapability`.
    * Aborts with `RecoveryAddress:ENOT_A_RECOVERY_ADDRESS` if `recovery_address` does not have a `RecoveryAddress` resource.
    * Aborts with `RecoveryAddress::EINVALID_KEY_ROTATION_DELEGATION` if `to_recover_account` and `recovery_address` do not belong to the same VASP.
    """

    recovery_address: libra_types.AccountAddress


@dataclass
class ScriptCall__AddToScriptAllowList(ScriptCall):
    """Append the `hash` to script hashes list allowed to be executed by the network."""

    hash: bytes
    sliding_nonce: st.uint64


@dataclass
class ScriptCall__AddValidatorAndReconfigure(ScriptCall):
    """Add `new_validator` to the validator set.

    Fails if the `new_validator` address is already in the validator set
    or does not have a `ValidatorConfig` resource stored at the address.
    Emits a NewEpochEvent.
    """

    sliding_nonce: st.uint64
    validator_name: bytes
    validator_address: libra_types.AccountAddress


@dataclass
class ScriptCall__Burn(ScriptCall):
    """Permanently destroy the `Token`s stored in the oldest burn request under the `Preburn` resource.

    This will only succeed if `account` has a `MintCapability<Token>`, a `Preburn<Token>` resource
    exists under `preburn_address`, and there is a pending burn request.
    sliding_nonce is a unique nonce for operation, see sliding_nonce.move for details
    """

    token: libra_types.TypeTag
    sliding_nonce: st.uint64
    preburn_address: libra_types.AccountAddress


@dataclass
class ScriptCall__BurnTxnFees(ScriptCall):
    """Burn transaction fees that have been collected in the given `currency`
    and relinquish to the association.

    The currency must be non-synthetic.
    """

    coin_type: libra_types.TypeTag


@dataclass
class ScriptCall__CancelBurn(ScriptCall):
    """Cancel the oldest burn request from `preburn_address` and return the funds.

    Fails if the sender does not have a published `BurnCapability<Token>`.
    """

    token: libra_types.TypeTag
    preburn_address: libra_types.AccountAddress


@dataclass
class ScriptCall__CreateChildVaspAccount(ScriptCall):
    """Create a `ChildVASP` account for sender `parent_vasp` at `child_address` with a balance of
    `child_initial_balance` in `CoinType` and an initial authentication_key
    `auth_key_prefix | child_address`.

    If `add_all_currencies` is true, the child address will have a zero balance in all available
    currencies in the system.
    This account will a child of the transaction sender, which must be a ParentVASP.

    ## Aborts
    The transaction will abort:

    * If `parent_vasp` is not a parent vasp with error: `Roles::EINVALID_PARENT_ROLE`
    * If `child_address` already exists with error: `Roles::EROLE_ALREADY_ASSIGNED`
    * If `parent_vasp` already has 256 child accounts with error: `VASP::ETOO_MANY_CHILDREN`
    * If `CoinType` is not a registered currency with error: `LibraAccount::ENOT_A_CURRENCY`
    * If `parent_vasp`'s withdrawal capability has been extracted with error:  `LibraAccount::EWITHDRAWAL_CAPABILITY_ALREADY_EXTRACTED`
    * If `parent_vasp` doesn't hold `CoinType` and `child_initial_balance > 0` with error: `LibraAccount::EPAYER_DOESNT_HOLD_CURRENCY`
    * If `parent_vasp` doesn't at least `child_initial_balance` of `CoinType` in its account balance with error: `LibraAccount::EINSUFFICIENT_BALANCE`
    """

    coin_type: libra_types.TypeTag
    child_address: libra_types.AccountAddress
    auth_key_prefix: bytes
    add_all_currencies: st.bool
    child_initial_balance: st.uint64


@dataclass
class ScriptCall__CreateDesignatedDealer(ScriptCall):
    """Create an account with the DesignatedDealer role at `addr` with authentication key
    `auth_key_prefix` | `addr` and a 0 balance of type `Currency`.

    If `add_all_currencies` is true,
    0 balances for all available currencies in the system will also be added. This can only be
    invoked by an account with the TreasuryCompliance role.
    """

    currency: libra_types.TypeTag
    sliding_nonce: st.uint64
    addr: libra_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes
    add_all_currencies: st.bool


@dataclass
class ScriptCall__CreateParentVaspAccount(ScriptCall):
    """Create an account with the ParentVASP role at `address` with authentication key
    `auth_key_prefix` | `new_account_address` and a 0 balance of type `currency`.

    If
    `add_all_currencies` is true, 0 balances for all available currencies in the system will
    also be added. This can only be invoked by an TreasuryCompliance account.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """

    coin_type: libra_types.TypeTag
    sliding_nonce: st.uint64
    new_account_address: libra_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes
    add_all_currencies: st.bool


@dataclass
class ScriptCall__CreateRecoveryAddress(ScriptCall):
    """Extract the `KeyRotationCapability` for `recovery_account` and publish it in a
    `RecoveryAddress` resource under  `account`.

    ## Aborts
    * Aborts with `LibraAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` if `account` has already delegated its `KeyRotationCapability`.
    * Aborts with `RecoveryAddress::ENOT_A_VASP` if `account` is not a ParentVASP or ChildVASP
    """

    pass


@dataclass
class ScriptCall__CreateValidatorAccount(ScriptCall):
    """Create a validator account at `new_validator_address` with `auth_key_prefix`and human_name."""

    sliding_nonce: st.uint64
    new_account_address: libra_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes


@dataclass
class ScriptCall__CreateValidatorOperatorAccount(ScriptCall):
    """Create a validator operator account at `new_validator_address` with `auth_key_prefix`and human_name."""

    sliding_nonce: st.uint64
    new_account_address: libra_types.AccountAddress
    auth_key_prefix: bytes
    human_name: bytes


@dataclass
class ScriptCall__FreezeAccount(ScriptCall):
    """Freeze account `address`.

    Initiator must be authorized.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """

    sliding_nonce: st.uint64
    to_freeze_account: libra_types.AccountAddress


@dataclass
class ScriptCall__MintLbr(ScriptCall):
    """Mint `amount_lbr` LBR from the sending account's constituent coins and deposits the
    resulting LBR into the sending account.

    # Events
    When this script executes without aborting, it emits three events:
    `SentPaymentEvent { amount_coin1, currency_code = Coin1, address_of(account), metadata = x"" }`
    `SentPaymentEvent { amount_coin2, currency_code = Coin2, address_of(account), metadata = x"" }`
    on `account`'s `LibraAccount::sent_events` handle where `amount_coin1` and `amount_coin2`
    are the components amounts of `amount_lbr` LBR, and
    `ReceivedPaymentEvent { amount_lbr, currency_code = LBR, address_of(account), metadata = x"" }`
    on `account`'s `LibraAccount::received_events` handle.

    # Abort Conditions
    > TODO(emmazzz): the documentation below documents the reasons of abort, instead of the categories.
    > We might want to discuss about what the best approach is here.
    The following abort conditions have been formally specified and verified. See spec schema
    `LibraAccount::StapleLBRAbortsIf` for the formal specifications.

    ## Aborts Caused by Invalid Account State
    * Aborts with `LibraAccount::EINSUFFICIENT_BALANCE` if `amount_coin1` is greater than sending
    `account`'s balance in `Coin1` or if `amount_coin2` is greater than sending `account`'s balance in `Coin2`.
    * Aborts with `LibraAccount::ECOIN_DEPOSIT_IS_ZERO` if `amount_lbr` is zero.
    * Aborts with `LibraAccount::EPAYEE_DOES_NOT_EXIST` if no LibraAccount exists at the address of `account`.
    * Aborts with `LibraAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` if LibraAccount exists at `account`,
    but it does not accept payments in LBR.

    ## Aborts Caused by Invalid LBR Minting State
    * Aborts with `Libra::EMINTING_NOT_ALLOWED` if minting LBR is not allowed according to the CurrencyInfo<LBR>
    stored at `CURRENCY_INFO_ADDRESS`.
    * Aborts with `Libra::ECURRENCY_INFO` if the total value of LBR would reach `MAX_U128` after `amount_lbr`
    LBR is minted.

    ## Other Aborts
    These aborts should only happen when `account` has account limit restrictions or
    has been frozen by Libra administrators.
    * Aborts with `LibraAccount::EWITHDRAWAL_EXCEEDS_LIMITS` if `account` has exceeded their daily
    withdrawal limits for Coin1 or Coin2.
    * Aborts with `LibraAccount::EDEPOSIT_EXCEEDS_LIMITS` if `account` has exceeded their daily
    deposit limits for LBR.
    * Aborts with `LibraAccount::EACCOUNT_FROZEN` if `account` is frozen.

    # Post Conditions
    The following post conditions have been formally specified and verified. See spec schema
    `LibraAccount::StapleLBREnsures` for the formal specifications.

    ## Changed States
    * The reserve backing for Coin1 and Coin2 increase by the right amounts as specified by the component ratio.
    * Coin1 and Coin2 balances at the address of sending `account` decrease by the right amounts as specified by
    the component ratio.
    * The total value of LBR increases by `amount_lbr`.
    * LBR balance at the address of sending `account` increases by `amount_lbr`.

    ## Unchanged States
    * The total values of Coin1 and Coin2 stay the same.
    """

    amount_lbr: st.uint64


@dataclass
class ScriptCall__PeerToPeerWithMetadata(ScriptCall):
    """Transfer `amount` coins of type `Currency` from `payer` to `payee` with (optional) associated
    `metadata` and an (optional) `metadata_signature` on the message
    `metadata` | `Signer::address_of(payer)` | `amount` | `DualAttestation::DOMAIN_SEPARATOR`.

    The `metadata` and `metadata_signature` parameters are only required if `amount` >=
    `DualAttestation::get_cur_microlibra_limit` LBR and `payer` and `payee` are distinct VASPs.
    However, a transaction sender can opt in to dual attestation even when it is not required (e.g., a DesignatedDealer -> VASP payment) by providing a non-empty `metadata_signature`.
    Standardized `metadata` LCS format can be found in `libra_types::transaction::metadata::Metadata`.

    ## Events
    When this script executes without aborting, it emits two events:
    `SentPaymentEvent { amount, currency_code = Currency, payee, metadata }`
    on `payer`'s `LibraAccount::sent_events` handle, and
     `ReceivedPaymentEvent { amount, currency_code = Currency, payer, metadata }`
    on `payee`'s `LibraAccount::received_events` handle.

    ## Common Aborts
    These aborts can in occur in any payment.
    * Aborts with `LibraAccount::EINSUFFICIENT_BALANCE` if `amount` is greater than `payer`'s balance in `Currency`.
    * Aborts with `LibraAccount::ECOIN_DEPOSIT_IS_ZERO` if `amount` is zero.
    * Aborts with `LibraAccount::EPAYEE_DOES_NOT_EXIST` if no account exists at the address `payee`.
    * Aborts with `LibraAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` if an account exists at `payee`, but it does not accept payments in `Currency`.

    ## Dual Attestation Aborts
    These aborts can occur in any payment subject to dual attestation.
    * Aborts with `DualAttestation::EMALFORMED_METADATA_SIGNATURE` if `metadata_signature`'s is not 64 bytes.
    * Aborts with `DualAttestation:EINVALID_METADATA_SIGNATURE` if `metadata_signature` does not verify on the message `metadata` | `payer` | `value` | `DOMAIN_SEPARATOR` using the `compliance_public_key` published in the `payee`'s `DualAttestation::Credential` resource.

    ## Other Aborts
    These aborts should only happen when `payer` or `payee` have account limit restrictions or
    have been frozen by Libra administrators.
    * Aborts with `LibraAccount::EWITHDRAWAL_EXCEEDS_LIMITS` if `payer` has exceeded their daily
    withdrawal limits.
    * Aborts with `LibraAccount::EDEPOSIT_EXCEEDS_LIMITS` if `payee` has exceeded their daily deposit limits.
    * Aborts with `LibraAccount::EACCOUNT_FROZEN` if `payer`'s account is frozen.
    """

    currency: libra_types.TypeTag
    payee: libra_types.AccountAddress
    amount: st.uint64
    metadata: bytes
    metadata_signature: bytes


@dataclass
class ScriptCall__Preburn(ScriptCall):
    """Preburn `amount` `Token`s from `account`.

    This will only succeed if `account` already has a published `Preburn<Token>` resource.
    """

    token: libra_types.TypeTag
    amount: st.uint64


@dataclass
class ScriptCall__PublishSharedEd25519PublicKey(ScriptCall):
    """(1) Rotate the authentication key of the sender to `public_key`
    (2) Publish a resource containing a 32-byte ed25519 public key and the rotation capability
        of the sender under the sender's address.

    Aborts if the sender already has a `SharedEd25519PublicKey` resource.
    Aborts if the length of `new_public_key` is not 32.
    """

    public_key: bytes


@dataclass
class ScriptCall__RegisterValidatorConfig(ScriptCall):
    """Set validator's config locally.

    Does not emit NewEpochEvent, the config is NOT changed in the validator set.
    """

    validator_account: libra_types.AccountAddress
    consensus_pubkey: bytes
    validator_network_addresses: bytes
    fullnode_network_addresses: bytes


@dataclass
class ScriptCall__RemoveValidatorAndReconfigure(ScriptCall):
    """Removes a validator from the validator set.

    Fails if the validator_address is not in the validator set.
    Emits a NewEpochEvent.
    """

    sliding_nonce: st.uint64
    validator_name: bytes
    validator_address: libra_types.AccountAddress


@dataclass
class ScriptCall__RotateAuthenticationKey(ScriptCall):
    """Rotate the sender's authentication key to `new_key`.

    `new_key` should be a 256 bit sha3 hash of an ed25519 public key.
    * Aborts with `LibraAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` if the `KeyRotationCapability` for `account` has already been extracted.
    * Aborts with `0` if the key rotation capability held by the account doesn't match the sender's address.
    * Aborts with `LibraAccount::EMALFORMED_AUTHENTICATION_KEY` if the length of `new_key` != 32.
    """

    new_key: bytes


@dataclass
class ScriptCall__RotateAuthenticationKeyWithNonce(ScriptCall):
    """Rotate `account`'s authentication key to `new_key`.

    `new_key` should be a 256 bit sha3 hash of an ed25519 public key. This script also takes
    `sliding_nonce`, as a unique nonce for this operation. See sliding_nonce.move for details.
    """

    sliding_nonce: st.uint64
    new_key: bytes


@dataclass
class ScriptCall__RotateAuthenticationKeyWithNonceAdmin(ScriptCall):
    """Rotate `account`'s authentication key to `new_key`.

    `new_key` should be a 256 bit sha3 hash of an ed25519 public key. This script also takes
    `sliding_nonce`, as a unique nonce for this operation. See sliding_nonce.move for details.
    """

    sliding_nonce: st.uint64
    new_key: bytes


@dataclass
class ScriptCall__RotateAuthenticationKeyWithRecoveryAddress(ScriptCall):
    """Rotate the authentication key of `account` to `new_key` using the `KeyRotationCapability`
    stored under `recovery_address`.

    ## Aborts
    * Aborts with `RecoveryAddress::ENOT_A_RECOVERY_ADDRESS` if `recovery_address` does not have a `RecoveryAddress` resource
    * Aborts with `RecoveryAddress::ECANNOT_ROTATE_KEY` if `account` is not `recovery_address` or `to_recover`.
    * Aborts with `LibraAccount::EMALFORMED_AUTHENTICATION_KEY` if `new_key` is not 32 bytes.
    * Aborts with `RecoveryAddress::ECANNOT_ROTATE_KEY` if `account` has not delegated its `KeyRotationCapability` to `recovery_address`.
    """

    recovery_address: libra_types.AccountAddress
    to_recover: libra_types.AccountAddress
    new_key: bytes


@dataclass
class ScriptCall__RotateDualAttestationInfo(ScriptCall):
    """Rotate `account`'s base URL to `new_url` and its compliance public key to `new_key`.

    Aborts if `account` is not a ParentVASP or DesignatedDealer
    Aborts if `new_key` is not a well-formed public key
    """

    new_url: bytes
    new_key: bytes


@dataclass
class ScriptCall__RotateSharedEd25519PublicKey(ScriptCall):
    """(1) Rotate the public key stored in `account`'s `SharedEd25519PublicKey` resource to
    `new_public_key`
    (2) Rotate the authentication key using the capability stored in `account`'s
    `SharedEd25519PublicKey` to a new value derived from `new_public_key`
    Aborts if `account` does not have a `SharedEd25519PublicKey` resource.

    Aborts if the length of `new_public_key` is not 32.
    """

    public_key: bytes


@dataclass
class ScriptCall__SetValidatorConfigAndReconfigure(ScriptCall):
    """Set validator's config and updates the config in the validator set.

    NewEpochEvent is emitted.
    """

    validator_account: libra_types.AccountAddress
    consensus_pubkey: bytes
    validator_network_addresses: bytes
    fullnode_network_addresses: bytes


@dataclass
class ScriptCall__SetValidatorOperator(ScriptCall):
    """Set validator's operator."""

    operator_name: bytes
    operator_account: libra_types.AccountAddress


@dataclass
class ScriptCall__SetValidatorOperatorWithNonceAdmin(ScriptCall):
    """Set validator operator as 'operator_account' of validator owner 'account' (via Admin Script).

    `operator_name` should match expected from operator account. This script also
    takes `sliding_nonce`, as a unique nonce for this operation. See `Sliding_nonce.move` for details.
    """

    sliding_nonce: st.uint64
    operator_name: bytes
    operator_account: libra_types.AccountAddress


@dataclass
class ScriptCall__TieredMint(ScriptCall):
    """Mint `mint_amount` to `designated_dealer_address` for `tier_index` tier.

    Max valid tier index is 3 since there are max 4 tiers per DD.
    Sender should be treasury compliance account and receiver authorized DD.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """

    coin_type: libra_types.TypeTag
    sliding_nonce: st.uint64
    designated_dealer_address: libra_types.AccountAddress
    mint_amount: st.uint64
    tier_index: st.uint64


@dataclass
class ScriptCall__UnfreezeAccount(ScriptCall):
    """Unfreeze account `address`.

    Initiator must be authorized.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """

    sliding_nonce: st.uint64
    to_unfreeze_account: libra_types.AccountAddress


@dataclass
class ScriptCall__UnmintLbr(ScriptCall):
    """Unmints `amount_lbr` LBR from the sending account into the constituent coins and deposits
    the resulting coins into the sending account.
    """

    amount_lbr: st.uint64


@dataclass
class ScriptCall__UpdateDualAttestationLimit(ScriptCall):
    """Update the dual attesation limit to `new_micro_lbr_limit`."""

    sliding_nonce: st.uint64
    new_micro_lbr_limit: st.uint64


@dataclass
class ScriptCall__UpdateExchangeRate(ScriptCall):
    """Update the on-chain exchange rate to LBR for the given `currency` to be given by
    `new_exchange_rate_numerator/new_exchange_rate_denominator`.
    """

    currency: libra_types.TypeTag
    sliding_nonce: st.uint64
    new_exchange_rate_numerator: st.uint64
    new_exchange_rate_denominator: st.uint64


@dataclass
class ScriptCall__UpdateLibraVersion(ScriptCall):
    """Update Libra version.

    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """

    sliding_nonce: st.uint64
    major: st.uint64


@dataclass
class ScriptCall__UpdateMintingAbility(ScriptCall):
    """Allows--true--or disallows--false--minting of `currency` based upon `allow_minting`."""

    currency: libra_types.TypeTag
    allow_minting: st.bool


def encode_script(call: ScriptCall) -> Script:
    """Build a Libra `Script` from a structured object `ScriptCall`."""
    helper = SCRIPT_ENCODER_MAP[call.__class__]
    return helper(call)


def decode_script(script: Script) -> ScriptCall:
    """Try to recognize a Libra `Script` and convert it into a structured object `ScriptCall`."""
    helper = SCRIPT_DECODER_MAP.get(script.code)
    if helper is None:
        raise ValueError("Unknown script bytecode")
    return helper(script)


def encode_add_currency_to_account_script(currency: TypeTag) -> Script:
    """Add a `Currency` balance to `account`, which will enable `account` to send and receive
    `Libra<Currency>`.

    Aborts with NOT_A_CURRENCY if `Currency` is not an accepted currency type in the Libra system
    Aborts with `LibraAccount::ADD_EXISTING_CURRENCY` if the account already holds a balance in
    `Currency`.
    """
    return Script(
        code=ADD_CURRENCY_TO_ACCOUNT_CODE,
        ty_args=[currency],
        args=[],
    )


def encode_add_recovery_rotation_capability_script(recovery_address: AccountAddress) -> Script:
    """Add the `KeyRotationCapability` for `to_recover_account` to the `RecoveryAddress` resource under `recovery_address`.

    ## Aborts
    * Aborts with `LibraAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` if `account` has already delegated its `KeyRotationCapability`.
    * Aborts with `RecoveryAddress:ENOT_A_RECOVERY_ADDRESS` if `recovery_address` does not have a `RecoveryAddress` resource.
    * Aborts with `RecoveryAddress::EINVALID_KEY_ROTATION_DELEGATION` if `to_recover_account` and `recovery_address` do not belong to the same VASP.
    """
    return Script(
        code=ADD_RECOVERY_ROTATION_CAPABILITY_CODE,
        ty_args=[],
        args=[TransactionArgument__Address(value=recovery_address)],
    )


def encode_add_to_script_allow_list_script(hash: bytes, sliding_nonce: st.uint64) -> Script:
    """Append the `hash` to script hashes list allowed to be executed by the network."""
    return Script(
        code=ADD_TO_SCRIPT_ALLOW_LIST_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=hash), TransactionArgument__U64(value=sliding_nonce)],
    )


def encode_add_validator_and_reconfigure_script(
    sliding_nonce: st.uint64, validator_name: bytes, validator_address: AccountAddress
) -> Script:
    """Add `new_validator` to the validator set.

    Fails if the `new_validator` address is already in the validator set
    or does not have a `ValidatorConfig` resource stored at the address.
    Emits a NewEpochEvent.
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
    """Permanently destroy the `Token`s stored in the oldest burn request under the `Preburn` resource.

    This will only succeed if `account` has a `MintCapability<Token>`, a `Preburn<Token>` resource
    exists under `preburn_address`, and there is a pending burn request.
    sliding_nonce is a unique nonce for operation, see sliding_nonce.move for details
    """
    return Script(
        code=BURN_CODE,
        ty_args=[token],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__Address(value=preburn_address)],
    )


def encode_burn_txn_fees_script(coin_type: TypeTag) -> Script:
    """Burn transaction fees that have been collected in the given `currency`
    and relinquish to the association.

    The currency must be non-synthetic.
    """
    return Script(
        code=BURN_TXN_FEES_CODE,
        ty_args=[coin_type],
        args=[],
    )


def encode_cancel_burn_script(token: TypeTag, preburn_address: AccountAddress) -> Script:
    """Cancel the oldest burn request from `preburn_address` and return the funds.

    Fails if the sender does not have a published `BurnCapability<Token>`.
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
    add_all_currencies: st.bool,
    child_initial_balance: st.uint64,
) -> Script:
    """Create a `ChildVASP` account for sender `parent_vasp` at `child_address` with a balance of
    `child_initial_balance` in `CoinType` and an initial authentication_key
    `auth_key_prefix | child_address`.

    If `add_all_currencies` is true, the child address will have a zero balance in all available
    currencies in the system.
    This account will a child of the transaction sender, which must be a ParentVASP.

    ## Aborts
    The transaction will abort:

    * If `parent_vasp` is not a parent vasp with error: `Roles::EINVALID_PARENT_ROLE`
    * If `child_address` already exists with error: `Roles::EROLE_ALREADY_ASSIGNED`
    * If `parent_vasp` already has 256 child accounts with error: `VASP::ETOO_MANY_CHILDREN`
    * If `CoinType` is not a registered currency with error: `LibraAccount::ENOT_A_CURRENCY`
    * If `parent_vasp`'s withdrawal capability has been extracted with error:  `LibraAccount::EWITHDRAWAL_CAPABILITY_ALREADY_EXTRACTED`
    * If `parent_vasp` doesn't hold `CoinType` and `child_initial_balance > 0` with error: `LibraAccount::EPAYER_DOESNT_HOLD_CURRENCY`
    * If `parent_vasp` doesn't at least `child_initial_balance` of `CoinType` in its account balance with error: `LibraAccount::EINSUFFICIENT_BALANCE`
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
    add_all_currencies: st.bool,
) -> Script:
    """Create an account with the DesignatedDealer role at `addr` with authentication key
    `auth_key_prefix` | `addr` and a 0 balance of type `Currency`.

    If `add_all_currencies` is true,
    0 balances for all available currencies in the system will also be added. This can only be
    invoked by an account with the TreasuryCompliance role.
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
    add_all_currencies: st.bool,
) -> Script:
    """Create an account with the ParentVASP role at `address` with authentication key
    `auth_key_prefix` | `new_account_address` and a 0 balance of type `currency`.

    If
    `add_all_currencies` is true, 0 balances for all available currencies in the system will
    also be added. This can only be invoked by an TreasuryCompliance account.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
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
    """Extract the `KeyRotationCapability` for `recovery_account` and publish it in a
    `RecoveryAddress` resource under  `account`.

    ## Aborts
    * Aborts with `LibraAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` if `account` has already delegated its `KeyRotationCapability`.
    * Aborts with `RecoveryAddress::ENOT_A_VASP` if `account` is not a ParentVASP or ChildVASP
    """
    return Script(
        code=CREATE_RECOVERY_ADDRESS_CODE,
        ty_args=[],
        args=[],
    )


def encode_create_validator_account_script(
    sliding_nonce: st.uint64, new_account_address: AccountAddress, auth_key_prefix: bytes, human_name: bytes
) -> Script:
    """Create a validator account at `new_validator_address` with `auth_key_prefix`and human_name."""
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
    """Create a validator operator account at `new_validator_address` with `auth_key_prefix`and human_name."""
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
    """Freeze account `address`.

    Initiator must be authorized.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """
    return Script(
        code=FREEZE_ACCOUNT_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__Address(value=to_freeze_account)],
    )


def encode_mint_lbr_script(amount_lbr: st.uint64) -> Script:
    """Mint `amount_lbr` LBR from the sending account's constituent coins and deposits the
    resulting LBR into the sending account.

    # Events
    When this script executes without aborting, it emits three events:
    `SentPaymentEvent { amount_coin1, currency_code = Coin1, address_of(account), metadata = x"" }`
    `SentPaymentEvent { amount_coin2, currency_code = Coin2, address_of(account), metadata = x"" }`
    on `account`'s `LibraAccount::sent_events` handle where `amount_coin1` and `amount_coin2`
    are the components amounts of `amount_lbr` LBR, and
    `ReceivedPaymentEvent { amount_lbr, currency_code = LBR, address_of(account), metadata = x"" }`
    on `account`'s `LibraAccount::received_events` handle.

    # Abort Conditions
    > TODO(emmazzz): the documentation below documents the reasons of abort, instead of the categories.
    > We might want to discuss about what the best approach is here.
    The following abort conditions have been formally specified and verified. See spec schema
    `LibraAccount::StapleLBRAbortsIf` for the formal specifications.

    ## Aborts Caused by Invalid Account State
    * Aborts with `LibraAccount::EINSUFFICIENT_BALANCE` if `amount_coin1` is greater than sending
    `account`'s balance in `Coin1` or if `amount_coin2` is greater than sending `account`'s balance in `Coin2`.
    * Aborts with `LibraAccount::ECOIN_DEPOSIT_IS_ZERO` if `amount_lbr` is zero.
    * Aborts with `LibraAccount::EPAYEE_DOES_NOT_EXIST` if no LibraAccount exists at the address of `account`.
    * Aborts with `LibraAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` if LibraAccount exists at `account`,
    but it does not accept payments in LBR.

    ## Aborts Caused by Invalid LBR Minting State
    * Aborts with `Libra::EMINTING_NOT_ALLOWED` if minting LBR is not allowed according to the CurrencyInfo<LBR>
    stored at `CURRENCY_INFO_ADDRESS`.
    * Aborts with `Libra::ECURRENCY_INFO` if the total value of LBR would reach `MAX_U128` after `amount_lbr`
    LBR is minted.

    ## Other Aborts
    These aborts should only happen when `account` has account limit restrictions or
    has been frozen by Libra administrators.
    * Aborts with `LibraAccount::EWITHDRAWAL_EXCEEDS_LIMITS` if `account` has exceeded their daily
    withdrawal limits for Coin1 or Coin2.
    * Aborts with `LibraAccount::EDEPOSIT_EXCEEDS_LIMITS` if `account` has exceeded their daily
    deposit limits for LBR.
    * Aborts with `LibraAccount::EACCOUNT_FROZEN` if `account` is frozen.

    # Post Conditions
    The following post conditions have been formally specified and verified. See spec schema
    `LibraAccount::StapleLBREnsures` for the formal specifications.

    ## Changed States
    * The reserve backing for Coin1 and Coin2 increase by the right amounts as specified by the component ratio.
    * Coin1 and Coin2 balances at the address of sending `account` decrease by the right amounts as specified by
    the component ratio.
    * The total value of LBR increases by `amount_lbr`.
    * LBR balance at the address of sending `account` increases by `amount_lbr`.

    ## Unchanged States
    * The total values of Coin1 and Coin2 stay the same.
    """
    return Script(
        code=MINT_LBR_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=amount_lbr)],
    )


def encode_peer_to_peer_with_metadata_script(
    currency: TypeTag, payee: AccountAddress, amount: st.uint64, metadata: bytes, metadata_signature: bytes
) -> Script:
    """Transfer `amount` coins of type `Currency` from `payer` to `payee` with (optional) associated
    `metadata` and an (optional) `metadata_signature` on the message
    `metadata` | `Signer::address_of(payer)` | `amount` | `DualAttestation::DOMAIN_SEPARATOR`.

    The `metadata` and `metadata_signature` parameters are only required if `amount` >=
    `DualAttestation::get_cur_microlibra_limit` LBR and `payer` and `payee` are distinct VASPs.
    However, a transaction sender can opt in to dual attestation even when it is not required (e.g., a DesignatedDealer -> VASP payment) by providing a non-empty `metadata_signature`.
    Standardized `metadata` LCS format can be found in `libra_types::transaction::metadata::Metadata`.

    ## Events
    When this script executes without aborting, it emits two events:
    `SentPaymentEvent { amount, currency_code = Currency, payee, metadata }`
    on `payer`'s `LibraAccount::sent_events` handle, and
     `ReceivedPaymentEvent { amount, currency_code = Currency, payer, metadata }`
    on `payee`'s `LibraAccount::received_events` handle.

    ## Common Aborts
    These aborts can in occur in any payment.
    * Aborts with `LibraAccount::EINSUFFICIENT_BALANCE` if `amount` is greater than `payer`'s balance in `Currency`.
    * Aborts with `LibraAccount::ECOIN_DEPOSIT_IS_ZERO` if `amount` is zero.
    * Aborts with `LibraAccount::EPAYEE_DOES_NOT_EXIST` if no account exists at the address `payee`.
    * Aborts with `LibraAccount::EPAYEE_CANT_ACCEPT_CURRENCY_TYPE` if an account exists at `payee`, but it does not accept payments in `Currency`.

    ## Dual Attestation Aborts
    These aborts can occur in any payment subject to dual attestation.
    * Aborts with `DualAttestation::EMALFORMED_METADATA_SIGNATURE` if `metadata_signature`'s is not 64 bytes.
    * Aborts with `DualAttestation:EINVALID_METADATA_SIGNATURE` if `metadata_signature` does not verify on the message `metadata` | `payer` | `value` | `DOMAIN_SEPARATOR` using the `compliance_public_key` published in the `payee`'s `DualAttestation::Credential` resource.

    ## Other Aborts
    These aborts should only happen when `payer` or `payee` have account limit restrictions or
    have been frozen by Libra administrators.
    * Aborts with `LibraAccount::EWITHDRAWAL_EXCEEDS_LIMITS` if `payer` has exceeded their daily
    withdrawal limits.
    * Aborts with `LibraAccount::EDEPOSIT_EXCEEDS_LIMITS` if `payee` has exceeded their daily deposit limits.
    * Aborts with `LibraAccount::EACCOUNT_FROZEN` if `payer`'s account is frozen.
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
    """Preburn `amount` `Token`s from `account`.

    This will only succeed if `account` already has a published `Preburn<Token>` resource.
    """
    return Script(
        code=PREBURN_CODE,
        ty_args=[token],
        args=[TransactionArgument__U64(value=amount)],
    )


def encode_publish_shared_ed25519_public_key_script(public_key: bytes) -> Script:
    """(1) Rotate the authentication key of the sender to `public_key`
    (2) Publish a resource containing a 32-byte ed25519 public key and the rotation capability
        of the sender under the sender's address.

    Aborts if the sender already has a `SharedEd25519PublicKey` resource.
    Aborts if the length of `new_public_key` is not 32.
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
    """Set validator's config locally.

    Does not emit NewEpochEvent, the config is NOT changed in the validator set.
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
    """Removes a validator from the validator set.

    Fails if the validator_address is not in the validator set.
    Emits a NewEpochEvent.
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
    """Rotate the sender's authentication key to `new_key`.

    `new_key` should be a 256 bit sha3 hash of an ed25519 public key.
    * Aborts with `LibraAccount::EKEY_ROTATION_CAPABILITY_ALREADY_EXTRACTED` if the `KeyRotationCapability` for `account` has already been extracted.
    * Aborts with `0` if the key rotation capability held by the account doesn't match the sender's address.
    * Aborts with `LibraAccount::EMALFORMED_AUTHENTICATION_KEY` if the length of `new_key` != 32.
    """
    return Script(
        code=ROTATE_AUTHENTICATION_KEY_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_authentication_key_with_nonce_script(sliding_nonce: st.uint64, new_key: bytes) -> Script:
    """Rotate `account`'s authentication key to `new_key`.

    `new_key` should be a 256 bit sha3 hash of an ed25519 public key. This script also takes
    `sliding_nonce`, as a unique nonce for this operation. See sliding_nonce.move for details.
    """
    return Script(
        code=ROTATE_AUTHENTICATION_KEY_WITH_NONCE_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_authentication_key_with_nonce_admin_script(sliding_nonce: st.uint64, new_key: bytes) -> Script:
    """Rotate `account`'s authentication key to `new_key`.

    `new_key` should be a 256 bit sha3 hash of an ed25519 public key. This script also takes
    `sliding_nonce`, as a unique nonce for this operation. See sliding_nonce.move for details.
    """
    return Script(
        code=ROTATE_AUTHENTICATION_KEY_WITH_NONCE_ADMIN_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_authentication_key_with_recovery_address_script(
    recovery_address: AccountAddress, to_recover: AccountAddress, new_key: bytes
) -> Script:
    """Rotate the authentication key of `account` to `new_key` using the `KeyRotationCapability`
    stored under `recovery_address`.

    ## Aborts
    * Aborts with `RecoveryAddress::ENOT_A_RECOVERY_ADDRESS` if `recovery_address` does not have a `RecoveryAddress` resource
    * Aborts with `RecoveryAddress::ECANNOT_ROTATE_KEY` if `account` is not `recovery_address` or `to_recover`.
    * Aborts with `LibraAccount::EMALFORMED_AUTHENTICATION_KEY` if `new_key` is not 32 bytes.
    * Aborts with `RecoveryAddress::ECANNOT_ROTATE_KEY` if `account` has not delegated its `KeyRotationCapability` to `recovery_address`.
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
    """Rotate `account`'s base URL to `new_url` and its compliance public key to `new_key`.

    Aborts if `account` is not a ParentVASP or DesignatedDealer
    Aborts if `new_key` is not a well-formed public key
    """
    return Script(
        code=ROTATE_DUAL_ATTESTATION_INFO_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=new_url), TransactionArgument__U8Vector(value=new_key)],
    )


def encode_rotate_shared_ed25519_public_key_script(public_key: bytes) -> Script:
    """(1) Rotate the public key stored in `account`'s `SharedEd25519PublicKey` resource to
    `new_public_key`
    (2) Rotate the authentication key using the capability stored in `account`'s
    `SharedEd25519PublicKey` to a new value derived from `new_public_key`
    Aborts if `account` does not have a `SharedEd25519PublicKey` resource.

    Aborts if the length of `new_public_key` is not 32.
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
    """Set validator's config and updates the config in the validator set.

    NewEpochEvent is emitted.
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
    """Set validator's operator."""
    return Script(
        code=SET_VALIDATOR_OPERATOR_CODE,
        ty_args=[],
        args=[TransactionArgument__U8Vector(value=operator_name), TransactionArgument__Address(value=operator_account)],
    )


def encode_set_validator_operator_with_nonce_admin_script(
    sliding_nonce: st.uint64, operator_name: bytes, operator_account: AccountAddress
) -> Script:
    """Set validator operator as 'operator_account' of validator owner 'account' (via Admin Script).

    `operator_name` should match expected from operator account. This script also
    takes `sliding_nonce`, as a unique nonce for this operation. See `Sliding_nonce.move` for details.
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
    """Mint `mint_amount` to `designated_dealer_address` for `tier_index` tier.

    Max valid tier index is 3 since there are max 4 tiers per DD.
    Sender should be treasury compliance account and receiver authorized DD.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
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
    """Unfreeze account `address`.

    Initiator must be authorized.
    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """
    return Script(
        code=UNFREEZE_ACCOUNT_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__Address(value=to_unfreeze_account)],
    )


def encode_unmint_lbr_script(amount_lbr: st.uint64) -> Script:
    """Unmints `amount_lbr` LBR from the sending account into the constituent coins and deposits
    the resulting coins into the sending account.
    """
    return Script(
        code=UNMINT_LBR_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=amount_lbr)],
    )


def encode_update_dual_attestation_limit_script(sliding_nonce: st.uint64, new_micro_lbr_limit: st.uint64) -> Script:
    """Update the dual attesation limit to `new_micro_lbr_limit`."""
    return Script(
        code=UPDATE_DUAL_ATTESTATION_LIMIT_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U64(value=new_micro_lbr_limit)],
    )


def encode_update_exchange_rate_script(
    currency: TypeTag,
    sliding_nonce: st.uint64,
    new_exchange_rate_numerator: st.uint64,
    new_exchange_rate_denominator: st.uint64,
) -> Script:
    """Update the on-chain exchange rate to LBR for the given `currency` to be given by
    `new_exchange_rate_numerator/new_exchange_rate_denominator`.
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


def encode_update_libra_version_script(sliding_nonce: st.uint64, major: st.uint64) -> Script:
    """Update Libra version.

    `sliding_nonce` is a unique nonce for operation, see sliding_nonce.move for details.
    """
    return Script(
        code=UPDATE_LIBRA_VERSION_CODE,
        ty_args=[],
        args=[TransactionArgument__U64(value=sliding_nonce), TransactionArgument__U64(value=major)],
    )


def encode_update_minting_ability_script(currency: TypeTag, allow_minting: st.bool) -> Script:
    """Allows--true--or disallows--false--minting of `currency` based upon `allow_minting`."""
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


def decode_mint_lbr_script(script: Script) -> ScriptCall:
    return ScriptCall__MintLbr(
        amount_lbr=decode_u64_argument(script.args[0]),
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


def decode_unmint_lbr_script(script: Script) -> ScriptCall:
    return ScriptCall__UnmintLbr(
        amount_lbr=decode_u64_argument(script.args[0]),
    )


def decode_update_dual_attestation_limit_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateDualAttestationLimit(
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_micro_lbr_limit=decode_u64_argument(script.args[1]),
    )


def decode_update_exchange_rate_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateExchangeRate(
        currency=script.ty_args[0],
        sliding_nonce=decode_u64_argument(script.args[0]),
        new_exchange_rate_numerator=decode_u64_argument(script.args[1]),
        new_exchange_rate_denominator=decode_u64_argument(script.args[2]),
    )


def decode_update_libra_version_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateLibraVersion(
        sliding_nonce=decode_u64_argument(script.args[0]),
        major=decode_u64_argument(script.args[1]),
    )


def decode_update_minting_ability_script(script: Script) -> ScriptCall:
    return ScriptCall__UpdateMintingAbility(
        currency=script.ty_args[0],
        allow_minting=decode_bool_argument(script.args[0]),
    )


ADD_CURRENCY_TO_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x07\x07\x11\x1a\x08\x2b\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x01\x06\x0c\x00\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x61\x64\x64\x5f\x63\x75\x72\x72\x65\x6e\x63\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x03\x0b\x00\x38\x00\x02"

ADD_RECOVERY_ROTATION_CAPABILITY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x0a\x05\x12\x0f\x07\x21\x6b\x08\x8c\x01\x10\x00\x00\x00\x01\x00\x02\x01\x00\x00\x03\x00\x01\x00\x01\x04\x02\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x08\x00\x05\x00\x02\x06\x0c\x05\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0f\x52\x65\x63\x6f\x76\x65\x72\x79\x41\x64\x64\x72\x65\x73\x73\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x17\x61\x64\x64\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04\x03\x05\x0b\x00\x11\x00\x0a\x01\x11\x01\x02"

ADD_TO_SCRIPT_ALLOW_LIST_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x10\x07\x1e\x5d\x08\x7b\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x02\x01\x00\x02\x06\x0c\x0a\x02\x00\x02\x06\x0c\x03\x03\x06\x0c\x0a\x02\x03\x20\x4c\x69\x62\x72\x61\x54\x72\x61\x6e\x73\x61\x63\x74\x69\x6f\x6e\x50\x75\x62\x6c\x69\x73\x68\x69\x6e\x67\x4f\x70\x74\x69\x6f\x6e\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x18\x61\x64\x64\x5f\x74\x6f\x5f\x73\x63\x72\x69\x70\x74\x5f\x61\x6c\x6c\x6f\x77\x5f\x6c\x69\x73\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x07\x0a\x00\x0a\x02\x11\x01\x0b\x00\x0b\x01\x11\x00\x02"

ADD_VALIDATOR_AND_RECONFIGURE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x06\x03\x06\x0f\x05\x15\x18\x07\x2d\x5c\x08\x89\x01\x10\x00\x00\x00\x01\x00\x02\x01\x03\x00\x01\x00\x02\x04\x02\x03\x00\x00\x05\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x04\x06\x0c\x03\x0a\x02\x05\x02\x01\x03\x0b\x4c\x69\x62\x72\x61\x53\x79\x73\x74\x65\x6d\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x0d\x61\x64\x64\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x06\x12\x0a\x00\x0a\x01\x11\x00\x0a\x03\x11\x01\x0b\x02\x21\x0c\x04\x0b\x04\x03\x0e\x0b\x00\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x00\x0a\x03\x11\x02\x02"

BURN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x11\x07\x22\x2e\x08\x50\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x02\x06\x0c\x05\x03\x06\x0c\x03\x05\x01\x09\x00\x05\x4c\x69\x62\x72\x61\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x04\x62\x75\x72\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x07\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x38\x00\x02"

BURN_TXN_FEES_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x07\x07\x11\x19\x08\x2a\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x01\x06\x0c\x00\x01\x09\x00\x0e\x54\x72\x61\x6e\x73\x61\x63\x74\x69\x6f\x6e\x46\x65\x65\x09\x62\x75\x72\x6e\x5f\x66\x65\x65\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x03\x0b\x00\x38\x00\x02"

CANCEL_BURN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x08\x07\x12\x19\x08\x2b\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x02\x06\x0c\x05\x00\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0b\x63\x61\x6e\x63\x65\x6c\x5f\x62\x75\x72\x6e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x04\x0b\x00\x0a\x01\x38\x00\x02"

CREATE_CHILD_VASP_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x08\x01\x00\x02\x02\x02\x04\x03\x06\x16\x04\x1c\x04\x05\x20\x23\x07\x43\x7b\x08\xbe\x01\x10\x06\xce\x01\x04\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x01\x01\x00\x03\x02\x03\x00\x00\x04\x04\x01\x01\x01\x00\x05\x03\x01\x00\x00\x06\x02\x06\x04\x06\x0c\x05\x0a\x02\x01\x00\x01\x06\x0c\x01\x08\x00\x05\x06\x08\x00\x05\x03\x0a\x02\x0a\x02\x05\x06\x0c\x05\x0a\x02\x01\x03\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x63\x72\x65\x61\x74\x65\x5f\x63\x68\x69\x6c\x64\x5f\x76\x61\x73\x70\x5f\x61\x63\x63\x6f\x75\x6e\x74\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x08\x70\x61\x79\x5f\x66\x72\x6f\x6d\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x0a\x02\x01\x00\x01\x01\x05\x03\x19\x0a\x00\x0a\x01\x0b\x02\x0a\x03\x38\x00\x0a\x04\x06\x00\x00\x00\x00\x00\x00\x00\x00\x24\x03\x0a\x05\x16\x0b\x00\x11\x01\x0c\x05\x0e\x05\x0a\x01\x0a\x04\x07\x00\x07\x00\x38\x01\x0b\x05\x11\x03\x05\x18\x0b\x00\x01\x02"

CREATE_DESIGNATED_DEALER_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x1b\x07\x2c\x49\x08\x75\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x01\x06\x06\x0c\x03\x05\x0a\x02\x0a\x02\x01\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x18\x63\x72\x65\x61\x74\x65\x5f\x64\x65\x73\x69\x67\x6e\x61\x74\x65\x64\x5f\x64\x65\x61\x6c\x65\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x0a\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x0a\x05\x38\x00\x02"

CREATE_PARENT_VASP_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x1b\x07\x2c\x4b\x08\x77\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x01\x06\x06\x0c\x03\x05\x0a\x02\x0a\x02\x01\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x1a\x63\x72\x65\x61\x74\x65\x5f\x70\x61\x72\x65\x6e\x74\x5f\x76\x61\x73\x70\x5f\x61\x63\x63\x6f\x75\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x0a\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x0a\x05\x38\x00\x02"

CREATE_RECOVERY_ADDRESS_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x0a\x05\x12\x0c\x07\x1e\x5b\x08\x79\x10\x00\x00\x00\x01\x00\x02\x01\x00\x00\x03\x00\x01\x00\x01\x04\x02\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x06\x0c\x08\x00\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0f\x52\x65\x63\x6f\x76\x65\x72\x79\x41\x64\x64\x72\x65\x73\x73\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x07\x70\x75\x62\x6c\x69\x73\x68\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x03\x05\x0a\x00\x0b\x00\x11\x00\x11\x01\x02"

CREATE_VALIDATOR_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x16\x07\x24\x49\x08\x6d\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x00\x02\x06\x0c\x03\x00\x04\x06\x0c\x05\x0a\x02\x0a\x02\x05\x06\x0c\x03\x05\x0a\x02\x0a\x02\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x18\x63\x72\x65\x61\x74\x65\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x5f\x61\x63\x63\x6f\x75\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x09\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x11\x01\x02"

CREATE_VALIDATOR_OPERATOR_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x16\x07\x24\x52\x08\x76\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x00\x02\x06\x0c\x03\x00\x04\x06\x0c\x05\x0a\x02\x0a\x02\x05\x06\x0c\x03\x05\x0a\x02\x0a\x02\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x21\x63\x72\x65\x61\x74\x65\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x5f\x6f\x70\x65\x72\x61\x74\x6f\x72\x5f\x61\x63\x63\x6f\x75\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x09\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0b\x03\x0b\x04\x11\x01\x02"

FREEZE_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0e\x07\x1c\x42\x08\x5e\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x02\x01\x00\x02\x06\x0c\x05\x00\x02\x06\x0c\x03\x03\x06\x0c\x03\x05\x0f\x41\x63\x63\x6f\x75\x6e\x74\x46\x72\x65\x65\x7a\x69\x6e\x67\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0e\x66\x72\x65\x65\x7a\x65\x5f\x61\x63\x63\x6f\x75\x6e\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

MINT_LBR_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x02\x02\x04\x03\x06\x0f\x05\x15\x10\x07\x25\x63\x08\x88\x01\x10\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x00\x00\x03\x01\x02\x00\x00\x04\x03\x02\x00\x01\x06\x0c\x01\x08\x00\x00\x02\x06\x08\x00\x03\x02\x06\x0c\x03\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x0a\x73\x74\x61\x70\x6c\x65\x5f\x6c\x62\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04\x01\x09\x0b\x00\x11\x00\x0c\x02\x0e\x02\x0a\x01\x11\x02\x0b\x02\x11\x01\x02"

PEER_TO_PEER_WITH_METADATA_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x07\x01\x00\x02\x02\x02\x04\x03\x06\x10\x04\x16\x02\x05\x18\x1d\x07\x35\x61\x08\x96\x01\x10\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x00\x00\x03\x02\x03\x01\x01\x00\x04\x01\x03\x00\x01\x05\x01\x06\x0c\x01\x08\x00\x05\x06\x08\x00\x05\x03\x0a\x02\x0a\x02\x00\x05\x06\x0c\x05\x03\x0a\x02\x0a\x02\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x08\x70\x61\x79\x5f\x66\x72\x6f\x6d\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x04\x01\x0c\x0b\x00\x11\x00\x0c\x05\x0e\x05\x0a\x01\x0a\x02\x0b\x03\x0b\x04\x38\x00\x0b\x05\x11\x02\x02"

PREBURN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x07\x01\x00\x02\x02\x02\x04\x03\x06\x10\x04\x16\x02\x05\x18\x15\x07\x2d\x60\x08\x8d\x01\x10\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x00\x00\x03\x02\x03\x01\x01\x00\x04\x01\x03\x00\x01\x05\x01\x06\x0c\x01\x08\x00\x03\x06\x0c\x06\x08\x00\x03\x00\x02\x06\x0c\x03\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x07\x70\x72\x65\x62\x75\x72\x6e\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x04\x01\x0a\x0a\x00\x11\x00\x0c\x02\x0b\x00\x0e\x02\x0a\x01\x38\x00\x0b\x02\x11\x02\x02"

PUBLISH_SHARED_ED25519_PUBLIC_KEY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x06\x07\x0d\x1f\x08\x2c\x10\x00\x00\x00\x01\x00\x01\x00\x02\x06\x0c\x0a\x02\x00\x16\x53\x68\x61\x72\x65\x64\x45\x64\x32\x35\x35\x31\x39\x50\x75\x62\x6c\x69\x63\x4b\x65\x79\x07\x70\x75\x62\x6c\x69\x73\x68\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x04\x0b\x00\x0b\x01\x11\x00\x02"

REGISTER_VALIDATOR_CONFIG_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x0b\x07\x12\x1b\x08\x2d\x10\x00\x00\x00\x01\x00\x01\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x0a\x02\x00\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x0a\x73\x65\x74\x5f\x63\x6f\x6e\x66\x69\x67\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x07\x0b\x00\x0a\x01\x0b\x02\x0b\x03\x0b\x04\x11\x00\x02"

REMOVE_VALIDATOR_AND_RECONFIGURE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x06\x03\x06\x0f\x05\x15\x18\x07\x2d\x5f\x08\x8c\x01\x10\x00\x00\x00\x01\x00\x02\x01\x03\x00\x01\x00\x02\x04\x02\x03\x00\x00\x05\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x04\x06\x0c\x03\x0a\x02\x05\x02\x01\x03\x0b\x4c\x69\x62\x72\x61\x53\x79\x73\x74\x65\x6d\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x10\x72\x65\x6d\x6f\x76\x65\x5f\x76\x61\x6c\x69\x64\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x06\x12\x0a\x00\x0a\x01\x11\x00\x0a\x03\x11\x01\x0b\x02\x21\x0c\x04\x0b\x04\x03\x0e\x0b\x00\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x00\x0a\x03\x11\x02\x02"

ROTATE_AUTHENTICATION_KEY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x19\x05\x21\x20\x07\x41\xaf\x01\x08\xf0\x01\x10\x00\x00\x00\x01\x00\x03\x01\x00\x01\x02\x00\x01\x00\x00\x04\x00\x02\x00\x00\x05\x03\x04\x00\x00\x06\x02\x05\x00\x00\x07\x06\x05\x00\x01\x06\x0c\x01\x05\x01\x08\x00\x01\x06\x08\x00\x01\x06\x05\x00\x02\x06\x08\x00\x0a\x02\x02\x06\x0c\x0a\x02\x03\x08\x00\x01\x03\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x06\x53\x69\x67\x6e\x65\x72\x0a\x61\x64\x64\x72\x65\x73\x73\x5f\x6f\x66\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x5f\x61\x64\x64\x72\x65\x73\x73\x1f\x72\x65\x73\x74\x6f\x72\x65\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x07\x08\x14\x0a\x00\x11\x01\x0c\x02\x0e\x02\x11\x02\x14\x0b\x00\x11\x00\x21\x0c\x03\x0b\x03\x03\x0e\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0e\x02\x0b\x01\x11\x04\x0b\x02\x11\x03\x02"

ROTATE_AUTHENTICATION_KEY_WITH_NONCE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x14\x05\x1c\x17\x07\x33\xa0\x01\x08\xd3\x01\x10\x00\x00\x00\x01\x00\x03\x01\x00\x01\x02\x00\x01\x00\x00\x04\x02\x03\x00\x00\x05\x03\x01\x00\x00\x06\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x06\x08\x00\x0a\x02\x03\x06\x0c\x03\x0a\x02\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x72\x65\x73\x74\x6f\x72\x65\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x03\x0c\x0a\x00\x0a\x01\x11\x00\x0b\x00\x11\x01\x0c\x03\x0e\x03\x0b\x02\x11\x03\x0b\x03\x11\x02\x02"

ROTATE_AUTHENTICATION_KEY_WITH_NONCE_ADMIN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x02\x04\x04\x03\x08\x14\x05\x1c\x19\x07\x35\xa0\x01\x08\xd5\x01\x10\x00\x00\x00\x01\x00\x03\x01\x00\x01\x02\x00\x01\x00\x00\x04\x02\x03\x00\x00\x05\x03\x01\x00\x00\x06\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x06\x0c\x01\x08\x00\x02\x06\x08\x00\x0a\x02\x04\x06\x0c\x06\x0c\x03\x0a\x02\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x15\x4b\x65\x79\x52\x6f\x74\x61\x74\x69\x6f\x6e\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x65\x78\x74\x72\x61\x63\x74\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1f\x72\x65\x73\x74\x6f\x72\x65\x5f\x6b\x65\x79\x5f\x72\x6f\x74\x61\x74\x69\x6f\x6e\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x03\x0c\x0b\x00\x0a\x02\x11\x00\x0b\x01\x11\x01\x0c\x04\x0e\x04\x0b\x03\x11\x03\x0b\x04\x11\x02\x02"

ROTATE_AUTHENTICATION_KEY_WITH_RECOVERY_ADDRESS_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x08\x07\x0f\x2a\x08\x39\x10\x00\x00\x00\x01\x00\x01\x00\x04\x06\x0c\x05\x05\x0a\x02\x00\x0f\x52\x65\x63\x6f\x76\x65\x72\x79\x41\x64\x64\x72\x65\x73\x73\x19\x72\x6f\x74\x61\x74\x65\x5f\x61\x75\x74\x68\x65\x6e\x74\x69\x63\x61\x74\x69\x6f\x6e\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x06\x0b\x00\x0a\x01\x0a\x02\x0b\x03\x11\x00\x02"

ROTATE_DUAL_ATTESTATION_INFO_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x0a\x05\x0c\x0d\x07\x19\x3d\x08\x56\x10\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00\x01\x00\x02\x06\x0c\x0a\x02\x00\x03\x06\x0c\x0a\x02\x0a\x02\x0f\x44\x75\x61\x6c\x41\x74\x74\x65\x73\x74\x61\x74\x69\x6f\x6e\x0f\x72\x6f\x74\x61\x74\x65\x5f\x62\x61\x73\x65\x5f\x75\x72\x6c\x1c\x72\x6f\x74\x61\x74\x65\x5f\x63\x6f\x6d\x70\x6c\x69\x61\x6e\x63\x65\x5f\x70\x75\x62\x6c\x69\x63\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x07\x0a\x00\x0b\x01\x11\x00\x0b\x00\x0b\x02\x11\x01\x02"

ROTATE_SHARED_ED25519_PUBLIC_KEY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x02\x03\x02\x05\x05\x07\x06\x07\x0d\x22\x08\x2f\x10\x00\x00\x00\x01\x00\x01\x00\x02\x06\x0c\x0a\x02\x00\x16\x53\x68\x61\x72\x65\x64\x45\x64\x32\x35\x35\x31\x39\x50\x75\x62\x6c\x69\x63\x4b\x65\x79\x0a\x72\x6f\x74\x61\x74\x65\x5f\x6b\x65\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x04\x0b\x00\x0b\x01\x11\x00\x02"

SET_VALIDATOR_CONFIG_AND_RECONFIGURE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0f\x07\x1d\x45\x08\x62\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x00\x05\x06\x0c\x05\x0a\x02\x0a\x02\x0a\x02\x00\x02\x06\x0c\x05\x0b\x4c\x69\x62\x72\x61\x53\x79\x73\x74\x65\x6d\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x0a\x73\x65\x74\x5f\x63\x6f\x6e\x66\x69\x67\x1d\x75\x70\x64\x61\x74\x65\x5f\x63\x6f\x6e\x66\x69\x67\x5f\x61\x6e\x64\x5f\x72\x65\x63\x6f\x6e\x66\x69\x67\x75\x72\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x01\x0a\x0a\x00\x0a\x01\x0b\x02\x0b\x03\x0b\x04\x11\x00\x0b\x00\x0a\x01\x11\x01\x02"

SET_VALIDATOR_OPERATOR_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x13\x07\x21\x44\x08\x65\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x00\x03\x06\x0c\x0a\x02\x05\x02\x01\x03\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x17\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x4f\x70\x65\x72\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x0c\x73\x65\x74\x5f\x6f\x70\x65\x72\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04\x05\x0f\x0a\x02\x11\x00\x0b\x01\x21\x0c\x03\x0b\x03\x03\x0b\x0b\x00\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x00\x0a\x02\x11\x01\x02"

SET_VALIDATOR_OPERATOR_WITH_NONCE_ADMIN_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x06\x03\x06\x0f\x05\x15\x1a\x07\x2f\x67\x08\x96\x01\x10\x00\x00\x00\x01\x00\x02\x00\x03\x00\x01\x00\x02\x04\x02\x03\x00\x01\x05\x04\x01\x00\x02\x06\x0c\x03\x00\x01\x05\x01\x0a\x02\x02\x06\x0c\x05\x05\x06\x0c\x06\x0c\x03\x0a\x02\x05\x02\x01\x03\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x0f\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x17\x56\x61\x6c\x69\x64\x61\x74\x6f\x72\x4f\x70\x65\x72\x61\x74\x6f\x72\x43\x6f\x6e\x66\x69\x67\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0e\x67\x65\x74\x5f\x68\x75\x6d\x61\x6e\x5f\x6e\x61\x6d\x65\x0c\x73\x65\x74\x5f\x6f\x70\x65\x72\x61\x74\x6f\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x05\x06\x12\x0b\x00\x0a\x02\x11\x00\x0a\x04\x11\x01\x0b\x03\x21\x0c\x05\x0b\x05\x03\x0e\x0b\x01\x01\x06\x00\x00\x00\x00\x00\x00\x00\x00\x27\x0b\x01\x0a\x04\x11\x02\x02"

TIERED_MINT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x04\x03\x04\x0b\x04\x0f\x02\x05\x11\x15\x07\x26\x3c\x08\x62\x10\x00\x00\x00\x01\x01\x02\x00\x01\x00\x00\x03\x02\x01\x01\x01\x01\x04\x02\x06\x0c\x03\x00\x04\x06\x0c\x05\x03\x03\x05\x06\x0c\x03\x05\x03\x03\x01\x09\x00\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x0b\x74\x69\x65\x72\x65\x64\x5f\x6d\x69\x6e\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x03\x01\x09\x0a\x00\x0a\x01\x11\x00\x0b\x00\x0a\x02\x0a\x03\x0a\x04\x38\x00\x02"

UNFREEZE_ACCOUNT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0e\x07\x1c\x44\x08\x60\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x02\x01\x00\x02\x06\x0c\x05\x00\x02\x06\x0c\x03\x03\x06\x0c\x03\x05\x0f\x41\x63\x63\x6f\x75\x6e\x74\x46\x72\x65\x65\x7a\x69\x6e\x67\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x10\x75\x6e\x66\x72\x65\x65\x7a\x65\x5f\x61\x63\x63\x6f\x75\x6e\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x03\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

UNMINT_LBR_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x02\x02\x04\x03\x06\x0f\x05\x15\x10\x07\x25\x65\x08\x8a\x01\x10\x00\x00\x00\x01\x01\x00\x00\x02\x00\x01\x00\x00\x03\x01\x02\x00\x00\x04\x03\x02\x00\x01\x06\x0c\x01\x08\x00\x00\x02\x06\x08\x00\x03\x02\x06\x0c\x03\x0c\x4c\x69\x62\x72\x61\x41\x63\x63\x6f\x75\x6e\x74\x12\x57\x69\x74\x68\x64\x72\x61\x77\x43\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x65\x78\x74\x72\x61\x63\x74\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x1b\x72\x65\x73\x74\x6f\x72\x65\x5f\x77\x69\x74\x68\x64\x72\x61\x77\x5f\x63\x61\x70\x61\x62\x69\x6c\x69\x74\x79\x0c\x75\x6e\x73\x74\x61\x70\x6c\x65\x5f\x6c\x62\x72\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04\x01\x09\x0b\x00\x11\x00\x0c\x02\x0e\x02\x0a\x01\x11\x02\x0b\x02\x11\x01\x02"

UPDATE_DUAL_ATTESTATION_LIMIT_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0a\x07\x18\x48\x08\x60\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x00\x01\x00\x02\x06\x0c\x03\x00\x03\x06\x0c\x03\x03\x0f\x44\x75\x61\x6c\x41\x74\x74\x65\x73\x74\x61\x74\x69\x6f\x6e\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x14\x73\x65\x74\x5f\x6d\x69\x63\x72\x6f\x6c\x69\x62\x72\x61\x5f\x6c\x69\x6d\x69\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

UPDATE_EXCHANGE_RATE_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x07\x01\x00\x06\x02\x06\x04\x03\x0a\x10\x04\x1a\x02\x05\x1c\x19\x07\x35\x64\x08\x99\x01\x10\x00\x00\x00\x01\x00\x02\x00\x00\x02\x00\x00\x03\x00\x01\x00\x02\x04\x02\x03\x00\x01\x05\x04\x03\x01\x01\x02\x06\x02\x03\x03\x01\x08\x00\x02\x06\x0c\x03\x00\x02\x06\x0c\x08\x00\x04\x06\x0c\x03\x03\x03\x01\x09\x00\x0c\x46\x69\x78\x65\x64\x50\x6f\x69\x6e\x74\x33\x32\x05\x4c\x69\x62\x72\x61\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x14\x63\x72\x65\x61\x74\x65\x5f\x66\x72\x6f\x6d\x5f\x72\x61\x74\x69\x6f\x6e\x61\x6c\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x18\x75\x70\x64\x61\x74\x65\x5f\x6c\x62\x72\x5f\x65\x78\x63\x68\x61\x6e\x67\x65\x5f\x72\x61\x74\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x05\x01\x0b\x0a\x00\x0a\x01\x11\x01\x0a\x02\x0a\x03\x11\x00\x0c\x04\x0b\x00\x0b\x04\x38\x00\x02"

UPDATE_LIBRA_VERSION_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x05\x01\x00\x04\x03\x04\x0a\x05\x0e\x0a\x07\x18\x34\x08\x4c\x10\x00\x00\x00\x01\x00\x02\x00\x01\x00\x01\x03\x00\x01\x00\x02\x06\x0c\x03\x00\x03\x06\x0c\x03\x03\x0c\x4c\x69\x62\x72\x61\x56\x65\x72\x73\x69\x6f\x6e\x0c\x53\x6c\x69\x64\x69\x6e\x67\x4e\x6f\x6e\x63\x65\x03\x73\x65\x74\x15\x72\x65\x63\x6f\x72\x64\x5f\x6e\x6f\x6e\x63\x65\x5f\x6f\x72\x5f\x61\x62\x6f\x72\x74\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x02\x01\x07\x0a\x00\x0a\x01\x11\x01\x0b\x00\x0a\x02\x11\x00\x02"

UPDATE_MINTING_ABILITY_CODE = b"\xa1\x1c\xeb\x0b\x01\x00\x00\x00\x06\x01\x00\x02\x03\x02\x06\x04\x08\x02\x05\x0a\x08\x07\x12\x1d\x08\x2f\x10\x00\x00\x00\x01\x00\x01\x01\x01\x00\x02\x02\x06\x0c\x01\x00\x01\x09\x00\x05\x4c\x69\x62\x72\x61\x16\x75\x70\x64\x61\x74\x65\x5f\x6d\x69\x6e\x74\x69\x6e\x67\x5f\x61\x62\x69\x6c\x69\x74\x79\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x00\x01\x04\x0b\x00\x0a\x01\x38\x00\x02"

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
    ScriptCall__MintLbr: encode_mint_lbr_script,
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
    ScriptCall__UnmintLbr: encode_unmint_lbr_script,
    ScriptCall__UpdateDualAttestationLimit: encode_update_dual_attestation_limit_script,
    ScriptCall__UpdateExchangeRate: encode_update_exchange_rate_script,
    ScriptCall__UpdateLibraVersion: encode_update_libra_version_script,
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
    MINT_LBR_CODE: decode_mint_lbr_script,
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
    UNMINT_LBR_CODE: decode_unmint_lbr_script,
    UPDATE_DUAL_ATTESTATION_LIMIT_CODE: decode_update_dual_attestation_limit_script,
    UPDATE_EXCHANGE_RATE_CODE: decode_update_exchange_rate_script,
    UPDATE_LIBRA_VERSION_CODE: decode_update_libra_version_script,
    UPDATE_MINTING_ABILITY_CODE: decode_update_minting_ability_script,
}


def decode_bool_argument(arg: TransactionArgument) -> st.bool:
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
