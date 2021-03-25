# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines a state machine and data match utils classes for creating conditional states."""

import dataclasses, typing, abc


S = typing.TypeVar("S")
T = typing.TypeVar("T")


@dataclasses.dataclass(frozen=True)
class MatchResult:
    success: bool = dataclasses.field(default=False)
    matched_fields: typing.List[str] = dataclasses.field(default_factory=lambda: [])
    mismatched_fields: typing.List[str] = dataclasses.field(default_factory=lambda: [])

    @staticmethod
    def create(success: bool, fields: typing.List[str]) -> "MatchResult":
        return MatchResult(
            success=success,
            matched_fields=fields if success else [],
            mismatched_fields=fields if not success else [],
        )

    @staticmethod
    def merge(ret1: "MatchResult", ret2: "MatchResult") -> "MatchResult":
        return dataclasses.replace(
            ret1,
            success=ret1.success and ret2.success,
            matched_fields=ret1.matched_fields + ret2.matched_fields,
            mismatched_fields=ret1.mismatched_fields + ret2.mismatched_fields,
        )


class Condition(abc.ABC, typing.Generic[T]):
    @abc.abstractmethod
    def match(self, event_data: T) -> MatchResult:
        ...


@dataclasses.dataclass(frozen=True)
class Field(Condition[T]):
    path: str
    not_set: bool = dataclasses.field(default=False)

    def match(self, event_data: T) -> MatchResult:
        val = event_data
        for f in self.path.split("."):
            if val is None or not hasattr(val, f):
                return MatchResult.create(False, [self.path])
            val = getattr(val, f)

        if self.not_set:
            return MatchResult.create(val is None, [self.path])
        return MatchResult.create(val is not None, [self.path])


@dataclasses.dataclass(frozen=True)
class Value(typing.Generic[T, S], Condition[T]):
    path: str
    value: S

    def match(self, event_data: T) -> MatchResult:
        val = event_data
        for f in self.path.split("."):
            if val is None or not hasattr(val, f):
                return MatchResult.create(False, [self.path])
            val = getattr(val, f)
        return MatchResult.create(val == self.value, [self.path])


class ConditionValidationError(Exception):
    def __init__(self, validation: Condition[T], match_result: MatchResult) -> None:
        super().__init__(f"mismatch result: {match_result}")
        self.validation = validation
        self.match_result = match_result


@dataclasses.dataclass(frozen=True)
class Require(Condition[T]):
    conds: typing.List[Condition[T]]
    validation: typing.Optional[Condition[T]] = dataclasses.field(default=None)

    def match(self, event_data: T) -> MatchResult:
        ret = MatchResult(success=True)
        for cond in self.conds:
            ret = MatchResult.merge(ret, cond.match(event_data))

        if ret.success and self.validation:
            ret = MatchResult.merge(ret, self.validation.match(event_data))
            if not ret.success:
                raise ConditionValidationError(self.validation, ret)

        return ret

    def __hash__(self) -> int:
        return hash(tuple(self.conds))


@dataclasses.dataclass(frozen=True)
class State(typing.Generic[T]):
    id: str
    require: typing.Optional[Require[T]] = dataclasses.field(default=None)

    def match(self, event_data: T) -> MatchResult:
        if self.require:
            return self.require.match(event_data)
        return MatchResult(success=True)

    def __str__(self) -> str:
        return self.id


@dataclasses.dataclass(frozen=True)
class Transition(typing.Generic[T]):
    action: str
    state: State[T]
    to: State[T]


class NoStateMatchedError(ValueError):
    pass


class TooManyStatesMatchedError(ValueError):
    pass


@dataclasses.dataclass
class Machine(typing.Generic[T]):
    initials: typing.List[State[T]]
    states: typing.List[State[T]]
    transitions: typing.List[Transition[T]]

    def is_initial(self, state: State[T]) -> bool:
        return state in self.initials

    def is_valid_transition(self, state: State[T], to: State[T], event_data: T) -> bool:
        for t in self.transitions:
            if t.state == state and t.to == to:
                return True
        return False

    def match_state(self, event_data: T) -> State[T]:
        ret = self.match_states(event_data)
        if not ret:
            raise NoStateMatchedError(f"could not find state matches given event data({event_data})")
        if len(ret) > 1:
            raise TooManyStatesMatchedError(f"found multiple states({ret}) match given event data({event_data})")
        return ret[0]

    def match_states(self, event_data: T) -> typing.List[State[T]]:
        return [state for state, match in self.match_states_and_results(event_data) if match.success]

    def match_states_and_results(self, event_data: T) -> typing.List[typing.Tuple[State[T], MatchResult]]:
        return [(state, state.match(event_data)) for state in self.states]


def new_transition(state: State[T], to: State[T]) -> Transition[T]:
    return Transition(action=f"{state} -> {to}", state=state, to=to)


def require(*args: Condition[T], validation: typing.Optional[Condition[T]] = None) -> Require[T]:
    return Require(conds=list(args), validation=validation)


def build_machine(transitions: typing.List[Transition[T]]) -> Machine[T]:
    states = {}
    tos = {}
    for t in transitions:
        states[t.state.id] = t.state
        states[t.to.id] = t.to
        tos[t.to.id] = t.to

    initial_ids = set(states.keys()) - set(tos.keys())
    return Machine(
        initials=[states[id] for id in initial_ids],
        states=list(states.values()),
        transitions=transitions,
    )
