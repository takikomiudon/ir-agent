# 1379：外部レポートの供給者・更新日・予想区分

**Shared Researchの外部本文を公開HTMLの静的埋込JSONから確認できた。確認した通期数値は「会社予想」の再掲で、著者独自の数値予測として採用していない。** 個人著者名・有償委託条件・独立性は未確認を残した。

| 取得先 | HTTP | 初回取得UTC |
|---|---|---|
| [公式のShared Research案内](https://www.hokto-kinoko.co.jp/corporate/ir/shiryou/sharedresearch/) | 200 | 2026-10-15 05:28:09.982378 |
| [Shared Researchのホクト会社ページ](https://sharedresearch.jp/ja/companies/1379) | 200 | 05:28:30.141744 |

保存済み1379/01.jsonの明示リンクから公式案内へ、そこが明記した外部URLへ各1 GET。最大2 GETで終了。retry/自動redirect/JavaScript実行/登録/契約/支払/追加API通信0。

## 確認できた範囲

- 供給者はShared Research。ホクトの案内は、当社グループが投資家の理解促進目的でカバレッジレポートを発行したと説明する。会社の関与は確認できるが、有償委託・費用負担者/金額・契約条件までは明記を確認できなかった。「投資家の立場」とする紹介文も独立検証の証明にはしない。
- 外部ページの可視更新日は2026-09-18。静的JSONの日本語selectedProjectは「2027年3月期第1四半期決算レポート更新」、提供者の `publishedAt.ja` は `2026-09-18T08:24:14.640Z`。会社IDも1379へ照合した。これは提供者が付した選択更新の日時で、全履歴段落の公表日や初回公開時刻の独立した実証ではない。
- 本文は最新通期数値を「2027年3月期会社予想」と明記し、指標表の27/3期列も会社予想と表示する。分類は `issuer_guidance` のまま。SR社の定性見解は区別できるが、明記された著者独自の数値予測は今回の限定確認では未確認、候補0件。
- 個人の著者名は未確認。組織への帰属や定性評価があることだけで、独立した業績予測・数値検証済みとは呼ばない。転載数値と会社一次資料との全照合もしていない。

## JavaScriptを実行せず読んだ根拠

外部応答はHTMLで、初期可視本文は短い概要だった。受信した同じHTML内に `window.state = {…};` のJSON値があり、JSON decoderで値の終端を特定後、既存 `parse_json` で重複キー・非有限数を拒否して読み、終端のsemicolonも確認した。`eval`・JS runtime・script読込みは使用していない。得られた `reportContent` 文字列をHTMLデータとして既存Pageで可視化した。ログイン操作やアクセス制御を迂回する通信は行っていない。

`embedded-state-extraction.json` に生HTML上のJSON位置・SHA・guard、`02.embedded-state.json` と `02.report-embedded.html` / `02.report-visible.txt` に保存結果を保持。解析対象は供給者/日付/会社関与/予想の帰属に限り、長い本文の説明や個別数値の評価はしていない。PDFは取得しておらず、埋込metadataの相対filepathから絶対URLを推測/生成していない。

## 保存・未確認

2応答のraw/text/snapshot/URL・初回取得・SHA/manifest、短い支持引用4件と位置、source-bundle2件、reviewを保存した。外部sourceは公開外部研究であることをmetadataに明記し、会社の正式短信と区別。会社案内ページの公表日は不明なのでnull。外部本文のpublished_atは上記提供者申告の更新timestampで、取得日に置き換えていない。

全sourceは `financial_inputs_verified:false` / `financial_values_automatically_adopted:false`、companies/theses空。EPS倍率・確率・株価・割引率/成長率・投資閾値を補わず、評価器への数値採用・normalizer・実DB/既存資料/会社状態変更・質問送信0。旧6ファイルの不変、新2source契約/stable ID/raw・本文・snapshot SHA、短い引用/静的JSON抽出位置をオフライン照合して、この2 GETで完了した。
