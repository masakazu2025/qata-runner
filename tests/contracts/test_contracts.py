"""contracts.feature の手順。"""

import copy
import importlib
from pathlib import Path

from generate_contracts import GENERATED_DIR, generate
from pytest_bdd import given, parsers, scenarios, then
from support import load_example

scenarios("contracts.feature")


@given(parsers.parse('契約の例 "{file_name}"'), target_fixture="example")
def given_example(file_name: str):
    return load_example(file_name)


@then(parsers.parse('生成した型 "{type_path}" で読める'))
def generated_type_reads(example, type_path: str) -> None:
    module_name, _, class_name = type_path.partition(".")
    module = importlib.import_module(f"qata_runner.contracts.{module_name}")
    model = getattr(module, class_name)
    parsed = model.model_validate(copy.deepcopy(example))
    assert parsed.model_dump(mode="json", exclude_unset=True) == example


@then("契約から生成し直した型が、コミットした型と同じ")
def generated_types_are_up_to_date(tmp_path: Path) -> None:
    fresh = tmp_path / "contracts"
    generate(fresh)

    def files(root: Path) -> dict[str, str]:
        return {
            p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(root.rglob("*.py"))
        }

    assert files(fresh) == files(GENERATED_DIR), (
        "生成した型が契約と合わない。"
        "uv run python scripts/generate_contracts.py で生成し直してコミットする。"
    )
