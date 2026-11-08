# qata-runner

[qata](https://github.com/masakazu2025/qata) の runner です。server から命令を受けて Windows 上で操作（キー・タップ・文字の読み取り）を実行し、ステップごとの結果とスクショを返します。部品の辞書もテストケースも知らず、判定もしません。

**いまの操作は偽物です。** アプリは動かさず、どのステップも成功として、決まった文字と、操作を書いた白い PNG を返します。server・web と端から端までつなぐためのもので、あとで pywinauto で電卓を動かす本物に置き換えます。

契約と全体の要件は、親のリポジトリ `qata` が正です。このリポジトリは、親と同じ作業フォルダに並べて置きます（`../qata/contracts/` を読むため）。親を別の場所に置くときは、環境変数 `QATA_PARENT_DIR` で親のリポジトリを指します。

```
作業フォルダ/
├── qata/          ← 親
└── qata-runner/   ← ここ
```

## 関門

pull request と main への push のたびに、GitHub Actions（`.github/workflows/ci.yml`）が下を回します。通らないと main にマージできません。

```
uv sync
uv run pytest          # 生成した型と契約・POST /runs・依存の向き（import-linter）
uv run ruff check
uv run ruff format --check
```

## 契約から型を生成する

親の契約のうち、runner が使うもの（runner への命令・runner からの結果・共通の部品）から pydantic の型を生成し、`src/qata_runner/contracts/` に置いてコミットします。手で直しません。契約が変わったら生成し直します。生成物が契約と合っているかは `pytest` で確かめます。

```
uv run python scripts/generate_contracts.py
```

## 立ち上げる

```
uv run qata-runner
```

`http://127.0.0.1:8001` で待ち受けます（qata-server が既定で見に行く場所）。変えるときは環境変数 `QATA_RUNNER_HOST`・`QATA_RUNNER_PORT` を使います。偽の操作で read_text が返す文字は `QATA_RUNNER_FAKE_TEXT`（既定は「表示は 3 です」）で変えられます。

- `POST /runs`：本文は runner への命令（`runner-command.schema.json`）。実行が終わるまで待って、runner からの結果（`runner-result.schema.json`）を返す。
- 命令が契約に合わなければ、422 で `{"code": "invalid_command", "message": ...}` を返す。
