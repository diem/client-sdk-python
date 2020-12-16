# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.offchain.state import (
    Field,
    State,
    Value,
    MatchResult,
    build_machine,
    new_transition,
    require,
    TooManyStatesMatchedError,
    NoStateMatchedError,
    ConditionValidationError,
)
import dataclasses, pytest, typing


@dataclasses.dataclass
class Object:
    a: typing.Optional[str] = dataclasses.field(default=None)
    b: typing.Optional["Object"] = dataclasses.field(default=None)
    c: typing.Optional["Object"] = dataclasses.field(default=None)


def test_state_and_match_result():
    a = State(id="a")
    b = State(id="b", require=require(Field(path="b")))
    c = State(id="c", require=require(Value(path="b.a", value="world")))
    d = State(id="d", require=require(Field(path="b"), Field(path="c")))

    o = Object(a="hello", b=Object(a="world", c=Object("!")))
    assert a.match(o) == MatchResult(success=True)
    assert b.match(o) == MatchResult(success=True, matched_fields=["b"])
    assert c.match(o) == MatchResult(success=True, matched_fields=["b.a"])
    assert d.match(o) == MatchResult(success=False, matched_fields=["b"], mismatched_fields=["c"])
    assert d.match(Object(a="hello", b=Object(a="world"), c=Object("!"))) == MatchResult(
        success=True, matched_fields=["b", "c"]
    )
    assert d.match(Object(a="hello")) == MatchResult(success=False, mismatched_fields=["b", "c"])


def test_require_with_validation():
    st = State(
        id="b",
        require=require(Field(path="a"), Field(path="b"), validation=Field(path="c")),
    )

    assert st.match(Object()) == MatchResult(success=False, matched_fields=[], mismatched_fields=["a", "b"])
    assert st.match(Object(a="hello")) == MatchResult(success=False, matched_fields=["a"], mismatched_fields=["b"])

    with pytest.raises(ConditionValidationError):
        st.match(Object(a="hello", b="world"))

    assert st.match(Object(a="hello", b="world", c="v")) == MatchResult(
        success=True, matched_fields=["a", "b", "c"], mismatched_fields=[]
    )


def test_build_machine():
    a = State(id="a", require=require(Field(path="a")))
    b = State(id="b", require=require(Field(path="b")))
    c = State(id="c", require=require(Field(path="c")))
    d = State(id="d", require=require(Value(path="c.b.a", value="world")))

    transitions = [
        new_transition(a, b),
        new_transition(b, c),
        new_transition(c, d),
        new_transition(c, c),
    ]
    m = build_machine(transitions)
    assert m.initials == [a]

    assert len(m.states) == 4
    assert a in m.states
    assert b in m.states
    assert c in m.states
    assert d in m.states

    assert m.transitions == transitions


def test_match_states_by_context_object_field():
    a = State(id="a", require=require(Field(path="a")))
    b = State(id="b", require=require(Field(path="b", not_set=False)))
    c = State(id="c", require=require(Field(path="c", not_set=True)))

    m = build_machine(
        [
            new_transition(a, b),
            new_transition(a, c),
        ]
    )
    assert m.match_states(Object(a="hello")) == [a, c]
    assert m.match_states(Object(a="hello", c=Object())) == [a]
    assert m.match_states(Object(b=Object())) == [b, c]
    assert m.match_states(Object(a="hello", b=Object())) == [a, b, c]
    assert m.match_states(Object(c=None)) == [c]
    assert m.match_states(Object(c=Object())) == []


def test_match_states_by_context_object_field_value():
    a = State(id="a", require=require(Value(path="a", value="hello")))
    b = State(id="b", require=require(Value(path="b.a", value="hello")))

    m = build_machine(
        [
            new_transition(a, b),
        ]
    )
    assert m.match_states(Object(a="hello")) == [a]
    assert m.match_states(Object(a="world", b=Object(a="hello"))) == [b]
    assert m.match_states(Object(a="hello", c=Object())) == [a]


def test_match_state_returns_exact_one_matched_state():
    a = State(id="a", require=require(Value(path="a", value="hello")))
    b = State(id="b", require=require(Field(path="b")))

    m = build_machine(
        [
            new_transition(a, b),
        ]
    )

    assert m.match_state(Object(a="hello")) == a
    assert m.match_states(Object(a="hello", b=Object())) == [a, b]

    # multi match
    with pytest.raises(TooManyStatesMatchedError):
        assert m.match_state(Object(a="hello", b=Object()))
    # no match
    with pytest.raises(NoStateMatchedError):
        assert m.match_state(Object(a="world"))


def test_is_initial_state():
    a = State(id="a", require=require(Field(path="a")))
    b = State(id="b", require=require(Field(path="b")))

    m = build_machine(
        [
            new_transition(a, b),
        ]
    )
    assert m.is_initial(m.match_state(Object(a="hello")))
    m.is_initial(m.match_state(Object(b=Object())))


def test_is_valid_transition():
    a = State(id="a", require=require(Field(path="a")))
    b = State(id="b", require=require(Field(path="b")))
    c = State(id="c", require=require(Field(path="c")))

    m = build_machine(
        [
            new_transition(a, b),
            new_transition(b, c),
        ]
    )
    assert m.is_valid_transition(a, b, None)
    assert m.is_valid_transition(b, c, None)
    assert not m.is_valid_transition(a, c, None)
    assert not m.is_valid_transition(b, a, None)


def test_require_empty_matches_anything():
    a = State(id="a", require=require())

    assert a.match(None) == MatchResult(success=True)
    assert a.match(Object()) == MatchResult(success=True)
