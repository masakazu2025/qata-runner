"""runs.feature の手順。"""

import base64
import io
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pytest_bdd import given, parsers, scenarios, then, when
from support import load_example, walk_to_parent

from qata_runner.contract_check import problems
from qata_runner.fake import FakeOperator
from qata_runner.rest import create_app

scenarios("runs.feature")

REMOVE = "（消す）"


@pytest.fixture
def context() -> dict:
    return {}


@given("偽の操作で立ち上げた runner", target_fixture="client")
def fake_runner() -> TestClient:
    return TestClient(create_app(FakeOperator()))


@given(
    parsers.parse('read_text が "{text}" を返す偽の操作で立ち上げた runner'),
    target_fixture="client",
)
def fake_runner_with_text(text: str) -> TestClient:
    return TestClient(create_app(FakeOperator(text)))


@given(parsers.parse('契約の例 "{file_name}" の命令'))
def given_command(context: dict, file_name: str) -> None:
    context["command"] = load_example(file_name)


@when(parsers.parse('命令の "{pointer}" を {value} にする'))
def change_command(context: dict, pointer: str, value: str) -> None:
    parent, key = walk_to_parent(context["command"], pointer)
    if value == REMOVE:
        del parent[key]
    else:
        parent[key] = json.loads(value)


@when("その命令を送る")
def send_command(context: dict, client: TestClient) -> None:
    context["response"] = client.post("/runs", json=context["command"])


@when(parsers.parse('契約の例 "{file_name}" の命令を送る'))
def send_example(context: dict, client: TestClient, file_name: str) -> None:
    context["command"] = load_example(file_name)
    context["response"] = client.post("/runs", json=context["command"])


@when(parsers.parse('本文 "{body}" を送る'))
def send_body(context: dict, client: TestClient, body: str) -> None:
    context["response"] = client.post(
        "/runs", content=body, headers={"content-type": "application/json"}
    )


@then(parsers.parse("応答は {status:d}"))
def status_is(context: dict, status: int) -> None:
    response = context["response"]
    assert response.status_code == status, response.text


@then(parsers.parse('応答は {status:d} で、code は "{code}"'))
def error_is(context: dict, status: int, code: str) -> None:
    response = context["response"]
    assert response.status_code == status, response.text
    body = response.json()
    assert body["code"] == code
    assert body["message"]
    # 形は契約の共通の部品 error（code・message）にそろえる
    assert set(body) == {"code", "message"}


@then(parsers.parse('結果は契約 "{file_name}" に通る'))
def result_passes(context: dict, file_name: str) -> None:
    assert problems(file_name, context["response"].json()) == []


@then("結果の run_id は命令と同じ")
def run_id_matches(context: dict) -> None:
    assert context["response"].json()["run_id"] == context["command"]["run_id"]


@then("結果は completed で、命令のステップがすべて 0 から順に ok で並ぶ")
def all_steps_ok(context: dict) -> None:
    result = context["response"].json()
    assert result["status"] == "completed"
    assert [s["index"] for s in result["steps"]] == list(
        range(len(context["command"]["steps"]))
    )
    assert all(s["status"] == "ok" for s in result["steps"])


@then("開始の時刻は終わりの時刻より後でない")
def times_in_order(context: dict) -> None:
    result = context["response"].json()
    started = datetime.fromisoformat(result["started_at"])
    finished = datetime.fromisoformat(result["finished_at"])
    assert started <= finished


@then(parsers.parse("どのステップのスクショも {width:d} x {height:d} の PNG"))
def screenshots_are_png(context: dict, width: int, height: int) -> None:
    for step in context["response"].json()["steps"]:
        data = base64.b64decode(step["screenshot"]["data_base64"], validate=True)
        image = Image.open(io.BytesIO(data))
        assert image.format == "PNG"
        assert image.size == (width, height)


@then(parsers.parse('read_text のステップだけが文字 "{text}" を持つ'))
def only_read_text_has_text(context: dict, text: str) -> None:
    steps = context["response"].json()["steps"]
    commands = context["command"]["steps"]
    for command_step, result_step in zip(commands, steps, strict=True):
        if command_step["type"] == "read_text":
            assert result_step["text"] == text
        else:
            assert "text" not in result_step


@pytest.fixture
def runner_process():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    executable = Path(sys.executable).parent / "qata-runner"
    process = subprocess.Popen(
        [str(executable)],
        env={**os.environ, "QATA_RUNNER_PORT": str(port)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    yield f"http://127.0.0.1:{port}"
    process.terminate()
    process.wait(timeout=10)


@given("qata-runner をプロセスとして立ち上げた", target_fixture="base_url")
def started_process(runner_process: str) -> str:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            httpx.get(f"{runner_process}/docs", timeout=1)
            return runner_process
        except httpx.TransportError:
            time.sleep(0.2)
    raise AssertionError("qata-runner が立ち上がらない")


@when(parsers.parse('契約の例 "{file_name}" の命令をそのプロセスに送る'))
def send_to_process(context: dict, base_url: str, file_name: str) -> None:
    context["command"] = load_example(file_name)
    context["response"] = httpx.post(
        f"{base_url}/runs", json=context["command"], timeout=30
    )
