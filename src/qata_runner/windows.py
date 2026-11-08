"""本物の操作。pywinauto で Windows のアプリを動かし、結果とスクショを返す。

命令ごとに、同じタイトルのウィンドウを閉じてからアプリを起動し直し（親の D16）、
ウィンドウの大きさをそろえてから、ステップを順に実行する。
ステップでつまずいたら、そこで止めて aborted を返す（残りのステップは返さない）。
"""

import base64
import ctypes
import io
import subprocess
import time
from collections.abc import Callable
from ctypes import wintypes
from datetime import datetime

from PIL import Image, ImageGrab
from pywinauto import Desktop, keyboard, mouse
from pywinauto.application import WindowSpecification
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError as PywinautoTimeout

from qata_runner.contracts.common_schema import Error
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

# 名前付きのキー（DOM の KeyboardEvent.key）→ pywinauto の書き方
NAMED_KEYS = {
    "Enter": "{ENTER}",
    "Escape": "{ESC}",
    "Backspace": "{BACKSPACE}",
    "Delete": "{DELETE}",
    "Tab": "{TAB}",
    " ": "{SPACE}",
    "ArrowUp": "{UP}",
    "ArrowDown": "{DOWN}",
    "ArrowLeft": "{LEFT}",
    "ArrowRight": "{RIGHT}",
}
# pywinauto の send_keys で特別な意味を持つ文字。{} で囲んでそのまま押す
SPECIAL_CHARACTERS = set("+^%~(){}[]")

DWMWA_EXTENDED_FRAME_BOUNDS = 9


class StepFailed(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.error = Error(code=code, message=message)


def to_send_keys(key: str) -> str:
    """契約のキー（1 文字か名前付きのキー）を、pywinauto の send_keys の書き方に。"""
    if key in NAMED_KEYS:
        return NAMED_KEYS[key]
    if key in SPECIAL_CHARACTERS:
        return "{" + key + "}"
    return key


class WindowsOperator:
    def __init__(
        self,
        window_timeout: float = 15.0,
        element_timeout: float = 3.0,
        settle: float = 0.3,
    ) -> None:
        # 座標とスクショを物理ピクセルでそろえる（拡大率が 100% でない画面のため）
        _make_dpi_aware()
        self.window_timeout = window_timeout
        self.element_timeout = element_timeout
        self.settle = settle

    def run(self, command: RunnerCommand) -> RunnerResult:
        started_at = datetime.now().astimezone()

        def finish(
            status: Status, steps: list[StepResult], error: Error | None = None
        ) -> RunnerResult:
            return RunnerResult(
                run_id=command.run_id,
                status=status,
                started_at=started_at,
                finished_at=datetime.now().astimezone(),
                error=error,
                steps=steps,
            )

        try:
            window = self._start(command)
        except StepFailed as failed:
            return finish(Status.aborted, [], failed.error)

        steps: list[StepResult] = []
        for index, step in enumerate(command.steps):
            try:
                text = self._do(window, step.root)
                time.sleep(self.settle)
                screenshot = self._screenshot(window, command.screenshot.scope)
            except StepFailed as failed:
                steps.append(
                    StepResult(index=index, status=Status1.error, error=failed.error)
                )
                return finish(Status.aborted, steps, failed.error)
            steps.append(
                StepResult(
                    index=index, status=Status1.ok, text=text, screenshot=screenshot
                )
            )
        return finish(Status.completed, steps)

    def _start(self, command: RunnerCommand) -> WindowSpecification:
        title = command.app.window.title
        _close_windows(title)
        try:
            subprocess.Popen(command.app.launch.command)
        except OSError as e:
            raise StepFailed(
                "launch_failed",
                f"アプリを起動できない：{command.app.launch.command}（{e}）",
            ) from e

        window = Desktop(backend="uia").window(title=title, control_type="Window")
        try:
            window.wait("visible", timeout=self.window_timeout)
        except PywinautoTimeout as e:
            raise StepFailed(
                "window_not_found",
                f"タイトルが「{title}」のウィンドウが"
                f" {self.window_timeout:g} 秒で見つからない",
            ) from e

        size = command.app.window.size
        if size is not None:
            handle = window.wrapper_object().handle
            rect = window.wrapper_object().rectangle()
            ctypes.windll.user32.MoveWindow(
                handle, rect.left, rect.top, size.width, size.height, True
            )
            time.sleep(self.settle)
            rect = window.wrapper_object().rectangle()
            if (rect.width(), rect.height()) != (size.width, size.height):
                raise StepFailed(
                    "window_size_mismatch",
                    f"ウィンドウを {size.width} x {size.height} にできない"
                    f"（{rect.width()} x {rect.height()} になった）。"
                    "アプリの最小・最大の大きさを確かめる",
                )
        window.wrapper_object().set_focus()
        return window

    def _do(
        self, window: WindowSpecification, operation: Key | Tap | ReadText
    ) -> str | None:
        match operation:
            case Key():
                key = operation.key.model_dump(mode="json")
                return _guard(
                    "key_failed",
                    f"キー「{key}」を押せない",
                    lambda: self._press(window, key),
                )
            case Tap():
                return _guard(
                    "tap_failed",
                    f"({operation.point.x}, {operation.point.y}) をタップできない",
                    lambda: self._tap(window, operation.point.x, operation.point.y),
                )
            case ReadText():
                return self._read_uia(window, operation.source.root.automation_id)

    def _press(self, window: WindowSpecification, key: str) -> None:
        window.wrapper_object().set_focus()
        keyboard.send_keys(to_send_keys(key), pause=0.02, with_spaces=True)

    def _tap(self, window: WindowSpecification, x: int, y: int) -> None:
        # 座標は、ウィンドウの外枠の左上を原点にした物理ピクセル（契約の point）
        rect = window.wrapper_object().rectangle()
        mouse.click(button="left", coords=(rect.left + x, rect.top + y))

    def _read_uia(self, window: WindowSpecification, automation_id: str) -> str:
        element = window.child_window(auto_id=automation_id)
        try:
            element.wait("exists", timeout=self.element_timeout)
            return element.wrapper_object().window_text()
        except (PywinautoTimeout, ElementNotFoundError) as e:
            raise StepFailed(
                "element_not_found",
                f"AutomationId が「{automation_id}」の要素が見つからない",
            ) from e

    def _screenshot(self, window: WindowSpecification, scope: Scope) -> Screenshot:
        try:
            if scope == Scope.all_screens:
                image = ImageGrab.grab(all_screens=True)
            else:
                image = ImageGrab.grab(
                    bbox=_visible_bounds(window.wrapper_object().handle),
                    all_screens=True,
                )
        except Exception as e:  # 撮れない理由は環境によってさまざまなので、まとめて扱う
            raise StepFailed("screenshot_failed", f"スクショを撮れない（{e}）") from e
        return Screenshot(media_type="image/png", data_base64=_png(image))


def _guard(code: str, message: str, action: Callable[[], None]) -> None:
    try:
        action()
    except Exception as e:  # pywinauto の例外は種類が多いので、まとめて扱う
        raise StepFailed(code, f"{message}（{e}）") from e


def _close_windows(title: str) -> None:
    """前の実行の状態を持ち越さないように、同じタイトルのウィンドウを閉じる。"""
    for window in Desktop(backend="uia").windows(title=title, control_type="Window"):
        try:
            window.close()
        except Exception:  # すでに閉じていれば、それでよい
            pass
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if not Desktop(backend="uia").windows(title=title, control_type="Window"):
            return
        time.sleep(0.2)


def _visible_bounds(handle: int) -> tuple[int, int, int, int]:
    """ウィンドウの見えている範囲。外枠（GetWindowRect）には見えない縁が入るので、
    スクショは DWM の範囲で撮る。後ろの別のウィンドウが写り込まないようにするため。"""
    rect = wintypes.RECT()
    ctypes.windll.dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(handle),
        DWMWA_EXTENDED_FRAME_BOUNDS,
        ctypes.byref(rect),
        ctypes.sizeof(rect),
    )
    return (rect.left, rect.top, rect.right, rect.bottom)


def _make_dpi_aware() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per Monitor
    except OSError:
        pass  # すでに決まっていれば変えられない


def _png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
