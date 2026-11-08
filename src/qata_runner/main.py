"""runner を組み立てて立ち上げる。設定は環境変数で渡す。

- `QATA_RUNNER_HOST`・`QATA_RUNNER_PORT`：待ち受ける場所（既定は `127.0.0.1:8001`）
- `QATA_RUNNER_OPERATOR`：操作。`fake`（偽物、既定）か `windows`
  （pywinauto で本物のアプリを動かす）
- `QATA_RUNNER_FAKE_TEXT`：偽の操作で read_text が返す文字（既定は「表示は 3 です」）
"""

import os

import uvicorn
from fastapi import FastAPI

from qata_runner.fake import DEFAULT_TEXT, FakeOperator
from qata_runner.rest import create_app


def build() -> FastAPI:
    operator = os.environ.get("QATA_RUNNER_OPERATOR", "fake")
    if operator == "windows":
        # pywinauto は Windows でしか読み込めないので、使うときだけ読み込む
        from qata_runner.windows import WindowsOperator

        return create_app(WindowsOperator())
    if operator == "fake":
        text = os.environ.get("QATA_RUNNER_FAKE_TEXT", DEFAULT_TEXT)
        return create_app(FakeOperator(text))
    raise SystemExit(f"QATA_RUNNER_OPERATOR は fake か windows：{operator!r}")


def serve() -> None:
    uvicorn.run(
        build(),
        host=os.environ.get("QATA_RUNNER_HOST", "127.0.0.1"),
        port=int(os.environ.get("QATA_RUNNER_PORT", "8001")),
    )
