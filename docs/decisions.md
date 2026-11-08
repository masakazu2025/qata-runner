# 決めたこと

この部品の中だけで閉じることを残します。全体に関わることは親の `../qata/docs/decisions.md` に置きます。新しいものを上に足します。

---

## R2. 偽の操作と入口

- 決めた人：AI　レビュー：未（人のレビューは要らない。PoC が終わったときにまとめて振り返る、親の D25）
- 入口は `rest.py` の `create_app(operator)`。`operator` は `run(command) -> result` を持つものなら何でもよい（`Operator` の Protocol）。組み立ては `main.py` で、いまは偽の操作（`fake.py` の `FakeOperator`）を渡す。本物に置き換えるときは、`main.py` で渡すものを変える。
- 依存の向きは import-linter の layers で、`main` → `rest`・`fake`（互いに知らない）→ `contract_check`・契約の型。入口が偽物を知らないことも関門にした。
- 命令は FastAPI で検証せず、親の `runner-command.schema.json` で判定してから型に読み込む（qata-server の S1 と同じ）。合わなければ 422 で、契約の共通の部品 `error` の形（`code`：`invalid_command`）を返す。契約は runner の HTTP のエラーを決めていないが、server はどの HTTP のエラーも「runner に届かない」として扱う（qata-server の S6）ので、形を合わせておけば足りる。
- 本物の操作は終わるまで待つので、入口は操作をスレッドで動かす。
- 偽の操作は、どのステップも `ok` にし、read_text では決まった文字（既定は「表示は 3 です」、`QATA_RUNNER_FAKE_TEXT` で変える）を返す。電卓のデモの 1 + 2 = 3 が通るようにするため。失敗（aborted）を返す偽物は作らない。失敗の扱いは server が自分の偽の runner で確かめている。
- スクショは Pillow で作る白い PNG に、ステップの番号と操作を書く（既定のフォントは日本語を出せないので ASCII）。web でスクショが並ぶのを見られるようにするため。大きさは、`window` で命令に大きさがあればその大きさ、それ以外（`all_screens`、大きさのないアプリ）は 1920 x 1080。
- 時刻は runner の手元の時刻（タイムゾーン付き）。
- 待ち受けは `127.0.0.1:8001`（qata-server の既定の `QATA_RUNNER_URL` に合わせた）。設定の環境変数は `QATA_RUNNER_` で始め、server と同じマシンで立ち上げても混ざらないようにした。
- 関門の feature には、`qata-runner` をプロセスとして立ち上げて `POST /runs` を受けることも入れた。端から端までつなぐときの立ち上げ方を確かめておくため。

## R1. 型の生成と契約の読み方

- 決めた人：AI　レビュー：未（人のレビューは要らない。PoC が終わったときにまとめて振り返る、親の D25）
- qata-server の S1・S2 と同じく、datamodel-code-generator で生成し、`scripts/generate_contracts.py` に手順を置く。生成するのは runner が使う契約（`runner-command`・`runner-result` と、それが指す `common`）だけ。使わない型を持たないため。
- 契約そのものの検査（例が形式に通る・間違った例をはじく・$ref が解決できる）は、親の D22 のとおり qata-server が持つ。runner は、生成した型が契約の例を読めることと、生成し直しても同じことだけを確かめる。
- 親の契約は、作業フォルダで隣に並べた `../qata/` から読む（実行のときの判定も）。相対のパスで親を読むのは、次の周回で直す（親の ideas.md）。
- 観点は pytest-bdd の日本語の Gherkin で書く。
- 作った最初から `.gitattributes` で改行を LF にそろえる（親の D24）。
