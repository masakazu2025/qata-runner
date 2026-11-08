"""runner の入口（REST）。

`POST /runs` で命令を受け、実行が終わるまで待って結果を返す。
"""

from typing import Any, Protocol

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from qata_runner.contract_check import problems
from qata_runner.contracts.runner_command_schema import RunnerCommand
from qata_runner.contracts.runner_result_schema import RunnerResult


class Operator(Protocol):
    def run(self, command: RunnerCommand) -> RunnerResult: ...


def create_app(operator: Operator) -> FastAPI:
    app = FastAPI(title="qata-runner")

    @app.post("/runs")
    async def run(request: Request) -> Any:
        # 命令は FastAPI で検証せず、親の契約（JSON Schema）で判定する
        try:
            body = await request.json()
        except ValueError:
            return _invalid_command(["本文が JSON として読めない"])
        found = problems("runner-command.schema.json", body)
        if found:
            return _invalid_command(found)
        command = RunnerCommand.model_validate(body)
        # 本物の操作は終わるまで待つので、スレッドで動かす
        result = await run_in_threadpool(operator.run, command)
        return result.model_dump(mode="json", exclude_none=True)

    return app


def _invalid_command(found: list[str]) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "invalid_command",
            "message": "命令が契約に合わない：" + "／".join(found),
        },
    )
