import typing
from dataclasses import asdict

from .json_rpc.types import AccountStateResponse, ChildVASP, ParentVASP


class LibraAccount:
    def __init__(self, account_address: str, account_state: AccountStateResponse):
        self._address: str = account_address
        self._account_state: AccountStateResponse = account_state

        self._balances: typing.Dict[str, int] = {}
        for accnt_curr_balance in self._account_state.balances:
            self._balances[accnt_curr_balance.currency] = accnt_curr_balance.amount

        self._role: typing.Union[str, ParentVASP, ChildVASP] = "empty"
        if isinstance(self._account_state.role, str):
            # For strings returned like "empty", "unknown"
            self._role = typing.cast(str, self._account_state.role)
        else:
            role_dict = typing.cast(typing.Dict, self._account_state.role)
            if "parent_vasp" in role_dict:
                self._role = role_dict["parent_vasp"]
            elif "child_vasp" in role_dict:
                self._role = role_dict["child_vasp"]

    @property
    def address(self) -> str:
        """Account address in str"""
        return self._address

    @property
    def balances(self) -> typing.Dict[str, int]:
        """Account balance as a dict {currency: amount}"""
        return self._balances

    @property
    def currencies(self) -> typing.List[str]:
        """All the currecies currently present in account"""
        return list(self._balances.keys())

    @property
    def sequence(self) -> int:
        """Account sequence number"""
        return self._account_state.sequence_number

    @property
    def authentication_key(self) -> str:
        """Account authentication key which is different from account address"""
        return self._account_state.authentication_key

    @property
    def delegated_key_rotation_capability(self) -> bool:
        """delegated_key_rotation_capability"""
        return self._account_state.delegated_key_rotation_capability

    @property
    def delegated_withdrawal_capability(self) -> bool:
        """delegated_withdrawal_capability"""
        return self._account_state.delegated_withdrawal_capability

    @property
    def sent_events_key(self) -> str:
        """Unique key for sent events stream of this account"""
        return self._account_state.sent_events_key

    @property
    def received_events_key(self) -> str:
        """Unique key for received events stream of this account"""
        return self._account_state.received_events_key

    @property
    def vasp_role(self) -> str:
        """role associated with account in str"""
        if isinstance(self._role, ParentVASP):
            return "parent_vasp"
        elif isinstance(self._role, ChildVASP):
            return "child_vasp"

        return typing.cast(str, self._role)

    @property
    def parent_vasp_info(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if isinstance(self._role, ParentVASP):
            return asdict(self._role)

    @property
    def child_vasp_info(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        if isinstance(self._role, ChildVASP):
            return asdict(self._role)

    @property
    def is_frozen(self) -> bool:
        """is account frozen"""
        return self._account_state.is_frozen
