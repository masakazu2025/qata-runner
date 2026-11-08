"""features にまたがる手順。"""

import pytest
from pytest_bdd import parsers, then

from qata_runner.contract_check import problems


@pytest.fixture
def context() -> dict:
    return {}


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


@then("結果は completed で、命令のステップがすべて 0 から順に ok で並ぶ")
def all_steps_ok(context: dict) -> None:
    result = context["response"].json()
    assert result["status"] == "completed"
    assert [s["index"] for s in result["steps"]] == list(
        range(len(context["command"]["steps"]))
    )
    assert all(s["status"] == "ok" for s in result["steps"])
