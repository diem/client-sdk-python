import typing
from dataclasses import asdict

from .json_rpc.types import AccountStateResponse, ChildVASPRole, ParentVASPRole, Role


class LibraAccount:
    def __init__(self, account_address: str, account_state: AccountStateResponse):
        self._address: str = account_address
        self._account_state: AccountStateResponse = account_state

        self._balances: typing.Dict[str, int] = {}
        for accnt_curr_balance in self._account_state.balances:
            self._balances[accnt_curr_balance.currency] = accnt_curr_balance.amount

        self._role: Role = self._account_state.role

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
    def role(self) -> str:
        """role associated with account in str"""
        return self._role.type

    @property
    def vasp_info(self) -> typing.Optional[typing.Dict[str, typing.Any]]:
        """if the role is VASP, give the relevant parent/child vasp info
        if not return None
        """
        if isinstance(self._role, ParentVASPRole):
            return asdict(self._role)

        if isinstance(self._role, ChildVASPRole):
            return asdict(self._role)

        return None

    @property
    def is_frozen(self) -> bool:
        """is account frozen"""
        return self._account_state.is_frozen
