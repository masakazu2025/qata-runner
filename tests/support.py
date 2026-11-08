"""feature の手順から使う、契約の例と判定。"""

import json
from typing import Any

from generate_contracts import CONTRACTS_DIR

EXAMPLES_DIR = CONTRACTS_DIR / "examples"


def load_example(file_name: str) -> Any:
    return json.loads((EXAMPLES_DIR / file_name).read_text(encoding="utf-8"))


def walk_to_parent(document: Any, pointer: str) -> tuple[Any, Any]:
    """JSON Pointer の指す場所の、親と最後の鍵を返す。"""
    *parents, last = [
        p.replace("~1", "/").replace("~0", "~") for p in pointer.split("/")[1:]
    ]
    node = document
    for key in parents:
        node = node[int(key)] if isinstance(node, list) else node[key]
    return node, (int(last) if isinstance(node, list) else last)
