# EDINETの初回取得を再開する

クラウド環境のシークレットに `EDINET_API_KEY` を設定し、実行プロセスへ環境変数として渡す。キーをチャット・コード・コマンド引数・Git対象のファイルへ書かない。SDKは `.env` を自動で読み込まない。

リポジトリルートで準備状況を確認する。

```bash
.venv/bin/python scripts/start_edinet_research.py --check
```

キー設定後の初回取得は次の1コマンドで行う。

```bash
.venv/bin/python scripts/start_edinet_research.py
```

初回は6814の2026年10月9日を対象にする。[会社短信](../research/ir-case-studies-2026-10-15/6814/subsequent-interim-public-review-2026-10-16/parent-acceptance.json)の半期報告書提出予定日を起点に選んだ日であり、提出済みとは事前に認定していない。提出一覧で普通株コード・半期報告書・XBRLの存在を照合し、候補が1件の場合だけそのtype=1 ZIPを取得する。返却されたdocID・期間・提出日時を保持し、本文は既存の `parse_edinet_package(source="instance")` で解析する。

保存先はGit対象外の `data/edinet-6814-2026-10-09/`。最大2 GET、再試行・リダイレクトなし。候補が0件/複数、取得エラー、解析非対応等は状態を残して止まる。既存の保存先を上書きして再取得しない。キー未設定や `--check` はネット・DB書込・取得用ディレクトリ作成を行わない。

出力は原一覧・選択した提出メタデータ・原ZIP・候補bundle等である。実DBへの取込、金融入力の採用、株価取得、IR送信・注文はこのコマンドに含めない。取得後の研究では会社帰属・対象期・単位・連結範囲・会計基準を原典へ照合し、既存の分類・定性レビュー・金融契約の順へ戻す。

キー未設定の実CLI確認、独立mock17例、全1,663テストが完了し、作業は停止した。キー未設定時の終了コード1と `needs_configuration` は想定どおり。実APIの認証・取得内容・当該書類の提出はキー設定後に確認する。設定だけで自動実行はしない。停止時点の台帳・残課題は[継続作業の状態](ongoing-work.md)、検証証跡は[最終受入](../research/ir-edinet-startup-integration-2026-10-16/parent-acceptance.json)を参照する。
