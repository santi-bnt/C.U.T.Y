import pytest

from cuty.brain.states import State, StateMachine
from cuty.face.expressions import Expression, ExpressionEvent
from cuty.face.expression_sink import ExpressionController


class Sink:
    def __init__(self):
        self.events = []

    def set_expression(self, expression, intensity=1.0):
        self.events.append(ExpressionEvent(expression, intensity))


def test_state_transitions_and_baseline_expressions():
    sink = Sink()
    controller = ExpressionController(sink)
    state = StateMachine(controller.on_state)
    for next_state in (State.LISTENING, State.THINKING, State.SPEAKING, State.IDLE):
        state.set(next_state)
    assert [event.expression for event in sink.events] == [
        Expression.LISTENING, Expression.THINKING, Expression.SPEAKING, Expression.IDLE,
    ]


def test_invalid_transition_and_recovery():
    state = StateMachine()
    with pytest.raises(ValueError, match="Invalid state transition"):
        state.set(State.SPEAKING)
    state.set(State.ERROR)
    state.set(State.IDLE)
    assert state.current == State.IDLE


def test_emotion_override_then_idle_reset():
    sink = Sink()
    controller = ExpressionController(sink)
    event = controller.set_emotion(Expression.HAPPY, 0.8)
    assert event.as_dict() == {"type": "expression", "expression": "happy", "intensity": 0.8}
    controller.on_state(State.SPEAKING)
    controller.on_state(State.IDLE)
    assert [item.expression for item in sink.events] == [Expression.HAPPY, Expression.HAPPY, Expression.IDLE]


@pytest.mark.parametrize("intensity", [-0.1, 1.1, float("nan"), True, "0.8"])
def test_invalid_intensity(intensity):
    with pytest.raises(ValueError):
        ExpressionEvent(Expression.HAPPY, intensity)


def test_model_cannot_override_baseline():
    with pytest.raises(ValueError):
        ExpressionController(Sink()).set_emotion(Expression.SPEAKING, 0.5)
