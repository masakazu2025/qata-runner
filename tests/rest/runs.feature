# language: ja
機能: 命令を受けて、結果とスクショを返す（偽の操作）
  `POST /runs` で runner への命令を受け、実行が終わるまで待って runner からの結果を返す。
  いまの操作は偽物で、アプリは動かさない。どのステップも成功し、read_text は決まった文字を返す。

  シナリオ: 契約の例の命令を送ると、契約に合う結果が返る
    前提 偽の操作で立ち上げた runner
    もし 契約の例 "runner-command.json" の命令を送る
    ならば 応答は 200
    かつ 結果は契約 "runner-result.schema.json" に通る
    かつ 結果の run_id は命令と同じ
    かつ 結果は completed で、命令のステップがすべて 0 から順に ok で並ぶ
    かつ 開始の時刻は終わりの時刻より後でない
    かつ どのステップのスクショも 320 x 500 の PNG
    かつ read_text のステップだけが文字 "表示は 3 です" を持つ

  シナリオ: read_text が返す文字は、立ち上げるときに変えられる
    前提 read_text が "表示は 7 です" を返す偽の操作で立ち上げた runner
    もし 契約の例 "runner-command.json" の命令を送る
    ならば read_text のステップだけが文字 "表示は 7 です" を持つ

  シナリオアウトライン: ウィンドウの大きさがないときと、すべての画面を撮るときは、画面の大きさで撮る
    前提 偽の操作で立ち上げた runner
    かつ 契約の例 "runner-command.json" の命令
    もし 命令の "<場所>" を <値> にする
    かつ その命令を送る
    ならば 応答は 200
    かつ 結果は契約 "runner-result.schema.json" に通る
    かつ どのステップのスクショも <幅> x <高さ> の PNG

    例:
      | 場所              | 値            | 幅   | 高さ | なぜ                     |
      | /screenshot/scope | "all_screens" | 1920 | 1080 | すべての画面を撮る       |
      | /app/window/size  | （消す）      | 1920 | 1080 | 全画面のアプリで大きさがない |

  シナリオアウトライン: 契約に合わない命令は受けない
    前提 偽の操作で立ち上げた runner
    かつ 契約の例 "runner-command.json" の命令
    もし 命令の "<場所>" を <値> にする
    かつ その命令を送る
    ならば 応答は 422 で、code は "invalid_command"

    例:
      | 場所                   | 値       | なぜ               |
      | /steps                 | []       | ステップがない     |
      | /steps/0/key           | "Ctrl+C" | 同時押しは扱わない |
      | /steps/4/source/method | "ocr"    | まだない読み方     |
      | /run_id                | （消す） | run_id がない      |

  シナリオ: JSON でない本文は受けない
    前提 偽の操作で立ち上げた runner
    もし 本文 "<html>" を送る
    ならば 応答は 422 で、code は "invalid_command"

  シナリオ: qata-runner を立ち上げると、POST /runs で命令を受ける
    前提 qata-runner をプロセスとして立ち上げた
    もし 契約の例 "runner-command.json" の命令をそのプロセスに送る
    ならば 応答は 200
    かつ 結果は契約 "runner-result.schema.json" に通る
