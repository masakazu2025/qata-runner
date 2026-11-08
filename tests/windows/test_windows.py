"""windows.feature の手順。本物の電卓を動かす。"""

import base64
import io
import os

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pytest_bdd import given, parsers, scenarios, then, when

pytestmark = pytest.mark.skipif(
    bool(os.environ.get("QATA_RUNNER_NO_DESKTOP")),
    reason="デスクトップのない所では、本物のアプリを動かせない",
)

scenarios("windows.feature")

TITLE = "電卓"
DISPLAY = "CalculatorResults"


def _step(word: str) -> dict:
    if word == "表示を読む":
        return {
            "type": "read_text",
            "source": {"method": "uia", "automation_id": DISPLAY},
        }
    if word == "存在しない要素を読む":
        return {
            "type": "read_text",
            "source": {"method": "uia", "automation_id": "qata-test-missing"},
        }
    return {"type": "key", "key": word}


def _steps(words: str) -> list[dict]:
    return [_step(word) for word in words.split(" ")]


def _calculator():
    from pywinauto import Desktop

    return Desktop(backend="uia").window(title=TITLE, control_type="Window")


def _images(context: dict) -> list[Image.Image]:
    images = []
    for step in context["response"].json()["steps"]:
        data = base64.b64decode(step["screenshot"]["data_base64"], validate=True)
        image = Image.open(io.BytesIO(data))
        assert image.format == "PNG"
        images.append(image)
    return images


def _send(context: dict, client: TestClient) -> None:
    context["response"] = client.post("/runs", json=context["command"])


@given("本物の操作で立ち上げた runner", target_fixture="client")
def windows_runner() -> TestClient:
    from qata_runner.rest import create_app
    from qata_runner.windows import WindowsOperator

    return TestClient(create_app(WindowsOperator(window_timeout=5)))


@given(parsers.parse("電卓を {width:d} x {height:d} で起動する命令"))
def calculator_command(context: dict, width: int, height: int) -> None:
    context["command"] = {
        "run_id": "run_test",
        "app": {
            "launch": {"command": "calc.exe"},
            "window": {"title": TITLE, "size": {"width": width, "height": height}},
        },
        "screenshot": {"scope": "window"},
        "steps": [],
    }


@when(parsers.parse('ステップを "{words}" にして送る'))
def send_steps(context: dict, client: TestClient, words: str) -> None:
    context["command"]["steps"] = _steps(words)
    _send(context, client)


@when(
    parsers.parse('ボタン "{automation_id}" の真ん中をタップして表示を読む命令を送る')
)
def send_tap(context: dict, client: TestClient, automation_id: str) -> None:
    # 同じ大きさで一度起動して、ボタンの位置を外枠の左上からの座標で測る
    context["command"]["steps"] = _steps("Escape")
    _send(context, client)
    window = _calculator().wrapper_object()
    outer = window.rectangle()
    button = _calculator().child_window(auto_id=automation_id).wrapper_object()
    rect = button.rectangle()
    point = {
        "x": (rect.left + rect.right) // 2 - outer.left,
        "y": (rect.top + rect.bottom) // 2 - outer.top,
    }
    context["command"]["steps"] = [
        _step("Escape"),
        {"type": "tap", "point": point},
        _step("表示を読む"),
    ]
    _send(context, client)


@when(
    parsers.parse('スクショの範囲を "{scope}" にして、ステップを "{words}" にして送る')
)
def send_with_scope(context: dict, client: TestClient, scope: str, words: str) -> None:
    context["command"]["screenshot"]["scope"] = scope
    context["command"]["steps"] = _steps(words)
    _send(context, client)


@when(
    parsers.parse(
        "ウィンドウの大きさを {width:d} x {height:d} にして、"
        'ステップを "{words}" にして送る'
    )
)
def send_with_size(
    context: dict, client: TestClient, width: int, height: int, words: str
) -> None:
    context["command"]["app"]["window"]["size"] = {"width": width, "height": height}
    context["command"]["steps"] = _steps(words)
    _send(context, client)


@when(parsers.parse('起動を "{launch}" に、タイトルを "{title}" にして送る'))
def send_with_app(context: dict, client: TestClient, launch: str, title: str) -> None:
    context["command"]["app"] = {
        "launch": {"command": launch},
        "window": {"title": title},
    }
    context["command"]["steps"] = _steps("1")
    _send(context, client)


@then(parsers.parse('表示を読んだステップの文字は "{text}"'))
def display_text_is(context: dict, text: str) -> None:
    steps = context["response"].json()["steps"]
    commands = context["command"]["steps"]
    read = [
        result
        for command, result in zip(commands, steps, strict=True)
        if command["type"] == "read_text"
    ]
    assert [r["text"] for r in read] == [text]
    for command, result in zip(commands, steps, strict=True):
        if command["type"] != "read_text":
            assert "text" not in result


@then("どのステップのスクショも、ウィンドウの見えている範囲の PNG")
def screenshots_are_window(context: dict) -> None:
    from qata_runner.windows import _visible_bounds

    left, top, right, bottom = _visible_bounds(_calculator().wrapper_object().handle)
    for image in _images(context):
        assert image.size == (right - left, bottom - top)


@then("どのステップのスクショも、ウィンドウより大きい PNG")
def screenshots_are_screens(context: dict) -> None:
    outer = _calculator().wrapper_object().rectangle()
    for image in _images(context):
        assert image.width > outer.width()
        assert image.height > outer.height()


@then(parsers.parse('結果は aborted で、ステップは空、error の code は "{code}"'))
def aborted_before_steps(context: dict, code: str) -> None:
    result = context["response"].json()
    assert result["status"] == "aborted"
    assert result["steps"] == []
    assert result["error"]["code"] == code
    assert result["error"]["message"]


@then(parsers.parse('結果は aborted で、error の code は "{code}"'))
def aborted_with(context: dict, code: str) -> None:
    result = context["response"].json()
    assert result["status"] == "aborted"
    assert result["error"]["code"] == code


@then(parsers.parse("ステップは {count:d} つで、0 は ok、1 は error"))
def steps_until_error(context: dict, count: int) -> None:
    steps = context["response"].json()["steps"]
    assert len(steps) == count
    assert [s["status"] for s in steps] == ["ok", "error"]
    assert "screenshot" in steps[0]
    assert steps[1]["error"]["code"]
