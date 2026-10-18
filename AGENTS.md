# ir-agent

- セッション開始時は `docs/session-resume.md` と `docs/ongoing-work.md` を読み、最新指示・実DB・保存環境を確認する。EDINETは利用者が再開を指示するまで保留する。
- Python 3.11+。`uv sync --frozen --extra data` でローカル環境を再現する。
- 検証は `.venv/bin/python -m unittest discover -s tests -v`、サンプルは `.venv/bin/python scripts/demo.py`。
- Codexで調査を実行するときは `.agents/skills/jp-equity-ir/SKILL.md` と `docs/workflow.md` を読む。
- 公開GET前は `research/ir-source-access-holds-2026-10-15/README-v9.md` の最新13hostの収集保留を照合する。旧版も保持し、配信先の実hostごとに確認する。
- 仮説・資料・質問・返信のJSON契約と、版の不変性・時点情報・原子的な更新を維持する。
- DBと受信原文はGit対象外の `data/` に保存する。SDKキーや認証情報をログへ出さない。
- `third_party/anthropic/` の原文・LICENSE・manifestを保持する。金融計算は出典付きの入力から行う。
