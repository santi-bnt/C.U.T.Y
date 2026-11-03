"""Voice -> face UDP link, expression sink and lip sync timing."""

import asyncio
import math
import struct
import time

import pytest

from cuty.audio.lipsync import LipSyncSpeaker, envelope, level_of
from cuty.face.expression_sink import CompositeExpressionSink, ExpressionController, FaceLinkExpressionSink
from cuty.face.expressions import Expression
from cuty.face.link import FaceLinkReceiver, FaceLinkSender, decode, parse_address
from cuty.brain.states import State, StateMachine


def receive(receiver, count, timeout=1.0):
    messages, deadline = [], time.monotonic() + timeout
    while len(messages) < count and time.monotonic() < deadline:
        messages += receiver.poll()
        time.sleep(0.005)
    return messages


@pytest.fixture
def link():
    receiver = FaceLinkReceiver(("127.0.0.1", 0))
    sender = FaceLinkSender(receiver.address)
    yield sender, receiver
    sender.close()
    receiver.close()


def test_round_trip_of_every_message(link):
    sender, receiver = link
    sender.expression(Expression.HAPPY, 0.8)
    sender.mouth(0.42)
    sender.look(0.25, 0.75)
    sender.blink()
    got = receive(receiver, 4)
    assert [m.type for m in got] == ["expression", "mouth", "look", "blink"]
    assert (got[0].expression, got[0].intensity) == ("happy", 0.8)
    assert got[1].level == 0.42 and (got[2].x, got[2].y) == (0.25, 0.75)


@pytest.mark.parametrize("payload", [
    b"not json", b"[]", b'{"type":"mouth","level":0.5}',             # no version
    b'{"v":1,"type":"mouth","level":2}', b'{"v":1,"type":"mouth","level":true}',
    b'{"v":1,"type":"expression","expression":"angry"}', b'{"v":1,"type":"dance"}',
    b'{"v":1,"type":"look","x":0.5}', b"\xff\xfe", b"{" + b" " * 600 + b"}",
])
def test_malformed_messages_are_ignored(payload):
    assert decode(payload) is None


def test_sending_without_a_face_never_raises():
    sender = FaceLinkSender(("127.0.0.1", 9))  # nothing listens on the discard port
    for _ in range(3):
        sender.mouth(0.5)
    sender.close()


@pytest.mark.parametrize("value,expected", [
    (None, ("127.0.0.1", 5005)), ("", ("127.0.0.1", 5005)), ("off", None),
    ("192.168.1.20:6000", ("192.168.1.20", 6000)), ("raspberrypi.local", ("raspberrypi.local", 5005)),
])
def test_address_parsing(value, expected):
    assert parse_address(value) == expected


def test_bad_port_is_rejected():
    with pytest.raises(ValueError):
        parse_address("host:99999")


def test_state_machine_expressions_reach_the_face(link):
    sender, receiver = link
    controller = ExpressionController(CompositeExpressionSink(FaceLinkExpressionSink(sender)))
    state = StateMachine(controller.on_state)
    state.set(State.LISTENING)
    state.set(State.THINKING)
    controller.set_emotion(Expression.SURPRISED, 0.6)
    got = receive(receiver, 3)
    assert [m.expression for m in got] == ["listening", "thinking", "surprised"]


def tone(seconds, amplitude, rate=24_000):
    return b"".join(struct.pack("<h", int(amplitude * math.sin(2 * math.pi * 220 * i / rate)))
                    for i in range(int(seconds * rate)))


def test_loudness_mapping():
    assert level_of([]) == 0.0
    assert envelope(bytes(960)) == [0.0]
    loud = envelope(tone(0.02, 20000))[0]
    quiet = envelope(tone(0.02, 300))[0]
    assert loud > 0.9 and 0 < quiet < 0.4
    assert len(envelope(tone(0.1, 1000))) == 5


class Recorder:
    def __init__(self):
        self.levels = []

    def mouth(self, level):
        self.levels.append(level)


def test_levels_follow_the_playback_timeline():
    clock = [100.0]
    rec = Recorder()
    speaker = LipSyncSpeaker(None, rec, delay=0.0, clock=lambda: clock[0])
    speaker.schedule(bytes(0) + tone(0.1, 20000) + bytes(4800))  # 0.1 s loud, 0.1 s silent
    speaker.schedule(tone(0.1, 20000))                             # queued after the first chunk
    samples = []
    for _ in range(12):
        clock[0] += 0.025
        speaker.tick()
        samples.append(rec.levels[-1] if rec.levels else None)
    assert samples[1] > 0.9                    # loud part audible
    assert samples[5] == 0.0                   # silence in the middle
    assert samples[9] > 0.9                    # second chunk plays after the first
    clock[0] += 1.0
    speaker.tick()
    assert rec.levels[-1] == 0.0


def test_wrapper_plays_audio_and_closes_mouth():
    class FakeSpeaker:
        def __init__(self):
            self.written, self.state = [], "new"

        async def open(self):
            self.state = "open"

        async def write(self, pcm):
            self.written.append(pcm)

        async def close(self):
            self.state = "closed"

    async def scenario():
        inner, rec = FakeSpeaker(), Recorder()
        speaker = LipSyncSpeaker(inner, rec, rate=200)
        await speaker.open()
        await speaker.write(tone(0.05, 15000))
        await asyncio.sleep(0.1)
        await speaker.close()
        return inner, rec

    inner, rec = asyncio.run(scenario())
    assert inner.state == "closed" and len(inner.written) == 1
    assert max(rec.levels) > 0.5 and rec.levels[-1] == 0.0
