# language: ja
機能: 生成した型と親の契約
  runner が契約（../qata/contracts）から生成した型が、契約と合っていることを確かめる。
  契約そのものの検査（例が形式に通る・間違った例をはじく・$ref が解決できる）は qata-server が持つ（親の decisions.md の D22）。

  シナリオアウトライン: 生成した型で契約の例が読める
    前提 契約の例 "<ファイル>"
    ならば 生成した型 "<型>" で読める

    例:
      | ファイル            | 型                                  |
      | runner-command.json | runner_command_schema.RunnerCommand |
      | runner-result.json  | runner_result_schema.RunnerResult   |

  シナリオ: 生成した型が契約と一致する
    ならば 契約から生成し直した型が、コミットした型と同じ
