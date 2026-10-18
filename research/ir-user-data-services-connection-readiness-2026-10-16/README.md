# 既存データサービスとEDINETの準備状況

確認時刻: 2026-10-16T16:55:38.417099+00:00。GET・SDK実行・DB/Store・秘密ファイル/キー値/全環境一覧の読取・既存編集は0。

利用者の原文は「e-Stat, EIA, EDINET/FRED/Gビズインフォ　かな」（constraints-v3）。既存利用の申告であり、このクラウドで5サービスの認証や契約を確認した結果ではない。他4サービスの調達・新規接続には広げていない。

**EDINETのオンライン取得は準備完了と認定できない。** rootの有無だけの確認結果は EDINET_API_KEY nonempty=false（このreviewでは再照会していない）。installed edinet-toolsの配布メタデータは0.9.0。公開実装上、リクエスト時のキー解決は `api_key=` 明示引数 → `configure(api_key=...)` が保持する同一プロセスのメモリ → 環境変数 EDINET_API_KEY。SDKに.envや永続設定ファイルの自動読込経路はない。パッケージの公開config.pyを静的に読んだだけで、設定値は読んでいない。

環境変数なしでも明示引数/同一プロセスのconfigureがあれば利用し得るが、その実行時状態・キーの有効性は未確認。「設定済み」とも「他の場所にもキーが存在しない」とも断定しない。既存の通常CLIはキー引数やconfigureを渡さず一覧adapterを呼ぶため、起動時の安全なキー注入等がない新規プロセスを取得可能とは扱わない。

保存済みtype=1 ZIPと元の提出一覧メタデータがあれば、既存 `parse_edinet_package` はキー不要で利用できる実装である。docID/3桁docTypeCodeを使い、`source="instance"` または `source="xbrl"` を明示して保存bytesを解析する。原ファクト・文脈/単位・raw_fields/unmapped_fields/text_blocksを残し、未対応形式を自動で別方式に置き換えない。このtaskで解析は実行していない。提出一覧の取得だけなら index_only=true のメタデータであり、ZIP/全文/財務値取得とは別。

既存財務取得へ進む最少の準備は次の範囲で足りる。

1. 既存EDINETキーを保護された注入経路から実行プロセスに渡せる状態にする。チャット・コマンド直書き・ログへ値を出さず、有効性は後続の限定接続で別確認する。保存済み正規ZIPの解析だけならこの準備は不要。
2. 取得日/対象提出書類と保存先を先に固定し、提出一覧→選択したtype=1 ZIP→ローカル解析を分ける。一覧と書類の取得は別通信であり、一覧成功を全書類取得としない。実SDK既定の max_retries=3 はコード上最大3試行。1回のSDK試行へ絞るなら低水準APIの max_retries=1 等を明示するが、HTTPリダイレクトを含む通信上限は別確認。通常adapter/CLIをそのままGET1の確認に使わない（CLI syncにはDB取込も伴う）。
3. ZIP原bytes/元提出メタデータと取得時刻を保存し、docID・会社帰属・対象期・連結/個別・会計基準・円/株数の単位を原典と照合する。解析成功だけで既存年次値や金融モデルへ採用しない。EDINETを株価取得経路とも扱わない。

静的読取の入力SHA-256（SDKは公開実装ファイルのみ）:

- 利用者回答: research/ir-user-operating-constraints-2026-10-16/constraints-v3.json — 567a4928e72c600a2b3b8c13a92440151aebb68273a76301f86c316a14ec1e5e
- 既存adapter: src/ir_agent/adapters/edinet.py — 5a8878371aec1d28322cf8e500edbef7d317843ebdee2357a2f158dbc9a32f8c
- SDKキー解決の公開実装: .venv/lib/python3.12/site-packages/edinet_tools/config.py — 0e44fafbadac97f6f8c6ccef591fcaee499b56525ff73318ab7c8cec9ef77d12
- SDK configureの公開実装: .venv/lib/python3.12/site-packages/edinet_tools/_client.py — 229be10515a0bcfada72962570278e4a9b0e8d710869542867134555b79e51e2
- SDK APIの公開実装: .venv/lib/python3.12/site-packages/edinet_tools/api.py — 52263810f998869c4a2811829763e4c2908482c0b50b8c4227234ef71690ff41
- SDK保存ZIP解析の公開実装: .venv/lib/python3.12/site-packages/edinet_tools/parsers/__init__.py — 032cf2c6827550484cae867e2215ae1f78388bf6b5d71767b01b2f7a1e9ebd2d
