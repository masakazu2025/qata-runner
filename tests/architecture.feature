# language: ja
機能: 依存の向き
  組み立て（main）→ 入口（rest）・偽の操作（fake）→ 契約の判定（contract_check）・契約の型、の向きにだけ依存する。
  入口は偽の操作を知らない（本物に置き換えるときに、入口を変えずに済むように）。
  決まりは pyproject.toml の [tool.importlinter] に書く。

  シナリオ: 依存の向きが決まりに合う
    ならば import-linter の決まりがすべて守られている
