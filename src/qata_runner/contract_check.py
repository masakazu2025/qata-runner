"""受けた命令を、親の契約（JSON Schema）に照らして判定する。

生成した型は `if`/`then` などを表せないので、判定はここで行い、
合格したものだけを型に読み込む（qata-server の S1 と同じ考え方）。
"""

import json
import os
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

# 親の契約。環境変数 QATA_PARENT_DIR が親のリポジトリを指していれば、そこから読む。
# 指していなければ、作業フォルダで隣に並べた ../qata/ から読む（R1）。
PARENT_DIR = Path(
    os.environ.get("QATA_PARENT_DIR") or Path(__file__).resolve().parents[3] / "qata"
)
SCHEMAS_DIR = PARENT_DIR / "contracts" / "schemas"


@cache
def _validator(file_name: str) -> Draft202012Validator:
    resources = [
        (
            path.as_uri(),
            Resource(
                contents=json.loads(path.read_text(encoding="utf-8")),
                specification=DRAFT202012,
            ),
        )
        for path in sorted(SCHEMAS_DIR.glob("*.schema.json"))
    ]
    if not resources:
        raise FileNotFoundError(f"親の契約が見つからない：{SCHEMAS_DIR}")
    return Draft202012Validator(
        {"$ref": (SCHEMAS_DIR / file_name).as_uri()},
        registry=Registry().with_resources(resources),
        format_checker=FormatChecker(),
    )


def problems(file_name: str, data: Any) -> list[str]:
    """契約に合わない場所と、その説明の一覧。合えば空。"""
    found = []
    for error in _validator(file_name).iter_errors(data):
        where = "".join(f"/{p}" for p in error.absolute_path) or "/"
        found.append(f"{where}：{error.message}")
    return sorted(set(found))
