# qata-runner

qata の runner です。Windows 上で操作（キー・タップ・文字の読み取り）を実行し、結果とスクショを返します。入口は REST（`POST /runs`）。部品の辞書もテストケースも知りません。

**契約と全体の要件は `../qata/` を見る。** 契約の正は `../qata/contracts/`。全体に関わる issue は親のリポジトリ（qata）の issue に、idea は `../qata/docs/ideas.md` に上げる。

- 概要：[README.md](README.md)
- やること：このリポジトリの GitHub の issue。優先順は親の CLAUDE.md にあるボード
- 決めたこと（この部品だけのもの）：[docs/decisions.md](docs/decisions.md)
- セッションの始めと終わり：親のスキル `../qata/.claude/skills/session-start/SKILL.md`・`../qata/.claude/skills/session-end/SKILL.md` に沿う

親のルール：

@../qata/.claude/rules/general/working.md
@../qata/.claude/rules/general/autonomy.md
@../qata/.claude/rules/general/git.md
@../qata/.claude/rules/general/parent-and-children.md
@../qata/.claude/rules/general/issues.md
@../qata/.claude/rules/general/rules-and-skills.md
@../qata/.claude/rules/qata/repos-and-contracts.md
@../qata/.claude/rules/qata/knowledge.md
