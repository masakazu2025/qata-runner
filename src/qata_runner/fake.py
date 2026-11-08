"""偽の操作。アプリを動かさずに、決まった結果と PNG を返す。

本物（pywinauto で電卓を動かす）に置き換えるまでの間、server・web と
端から端までつなぐために使う。どのステップも成功し、read_text は決まった文字を返す。
"""

import base64
import io
from datetime import datetime

from PIL import Image, ImageDraw

from qata_runner.contracts.runner_command_schema import (
    Key,
    ReadText,
    RunnerCommand,
    Scope,
    Tap,
)
from qata_runner.contracts.runner_result_schema import (
    RunnerResult,
    Screenshot,
    Status,
    Status1,
    StepResult,
)

DEFAULT_TEXT = "表示は 3 です"
# 命令に大きさがないとき（全画面のアプリなど）と、すべての画面を撮るときの大きさ
SCREEN_SIZE = (1920, 1080)


class FakeOperator:
    def __init__(self, text: str = DEFAULT_TEXT) -> None:
        self.text = text

    def run(self, command: RunnerCommand) -> RunnerResult:
        started_at = datetime.now().astimezone()
        size = _screenshot_size(command)
        steps = []
        for index, step in enumerate(command.steps):
            operation = step.root
            steps.append(
                StepResult(
                    index=index,
                    status=Status1.ok,
                    text=self.text if isinstance(operation, ReadText) else None,
                    screenshot=Screenshot(
                        media_type="image/png",
                        data_base64=_png(size, index, _describe(operation)),
                    ),
                )
            )
        return RunnerResult(
            run_id=command.run_id,
            status=Status.completed,
            started_at=started_at,
            finished_at=datetime.now().astimezone(),
            steps=steps,
        )


def _screenshot_size(command: RunnerCommand) -> tuple[int, int]:
    window_size = command.app.window.size
    if command.screenshot.scope == Scope.window and window_size is not None:
        return (window_size.width, window_size.height)
    return SCREEN_SIZE


def _describe(operation: Key | Tap | ReadText) -> str:
    """スクショに書く、操作の説明。

    既定のフォントは日本語を出せないので、ASCII で書く。
    """
    match operation:
        case Key():
            return f"key {operation.key.model_dump(mode='json')!r}"
        case Tap():
            return f"tap ({operation.point.x}, {operation.point.y})"
        case ReadText():
            return f"read_text uia {operation.source.root.automation_id}"


def _png(size: tuple[int, int], index: int, description: str) -> str:
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    draw.text((16, 16), f"qata-runner (fake)\nstep {index}\n{description}", "black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
