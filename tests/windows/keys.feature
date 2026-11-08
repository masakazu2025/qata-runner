# language: ja
機能: 契約のキーを pywinauto の書き方にする
  契約のキーは、印字できる ASCII の 1 文字か、DOM の KeyboardEvent.key の名前（親の D13）。
  pywinauto の send_keys では + ^ % ~ ( ) { } [ ] が特別な意味を持つので、{} で囲んでそのまま押す。

  シナリオアウトライン: キーを書き換える
    もし キー "<キー>" を書き換える
    ならば "<書き方>" になる

    例:
      | キー      | 書き方      |
      | 1         | 1           |
      | =         | =           |
      | a         | a           |
      | +         | {+}         |
      | %         | {%}         |
      | (         | {(}         |
      | {         | {{}         |
      | Enter     | {ENTER}     |
      | Escape    | {ESC}       |
      | Backspace | {BACKSPACE} |
      | ArrowLeft | {LEFT}      |
