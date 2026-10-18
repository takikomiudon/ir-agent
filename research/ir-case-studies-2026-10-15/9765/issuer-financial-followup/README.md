# 9765：会社短信入口まで確認、正式本文は未取得

保存noticeの `capture.GETs[1].links[44]` にある決算短信入口 `https://www.k-ohba.co.jp/information/ir/financial-report/` を**1GET、200**で確認した。同host HTTPS robots200（09:49受信）は保存raw/SHAを照合して再利用し、元と同じ `ir-agent-public-research/0.1` の対象path許可を確認した。robotsの再GETは0。

入口の可視本文・全anchorに、正式短信のPDFへのliteral hrefは0件だった。raw HTMLには空の`eirArea`と、`document.write`/`unescape`/`setParts('financial')`による動的E-IR読込がある。HTTPS側のホストは`https://ssl4`と`.eir-parts.net`の文字片から構成される記述だが、**URLを組み立てて要求していない**。この既知hostには保存robotsのwildcard全面禁止があるため、同hostscript/API/PDFへ進まない。`/eir/eir.js`も取得せず、JS実行・別host/転載・URL推測・再試行・ネットワーク診断は0。

最大3GETの残り2回を使わず終了した。これはk-ohbaの入口自体が拒否されたという結果ではなく、許可された会社HTMLから正式資料への表示が動的で、確認対象の本文経路を今回の制約で解決できなかったという結果である。最新正式短信の対象期・予想の発表/修正版・会社EPS/売上/営業利益/営業利益率は全て未確認。

## 出典と検証

- 元route/SHA/notice links[44]のhrefと実入口URLが一致。
- 入口rawは22,390bytes、SHA256 `a403639e096cf05c679ff16a1ea58586a10a78acd52eb70dd91d4239ed961f1f`。
- 本文受信完了 `2026-10-15T10:00:08.180940Z` をsource.retrieved_atとする。開始/ヘッダ受信と区別し、公表時刻はnull。
- 既存Page parserをrawから再実行し、保存本文と全抽出JSONが一致。JSは解析対象の文字列であり実行していない。
- `source-bundle.json`はcanonical jp:9765の**会社短信入口index1件**だけ、companies/theses空、金融本文0。元notice sourceを実在する親IDとして参照する。入口HTMLを正式短信や会社金融数値の確認に数えない。
- 可視本文quoteとraw内JS quoteはrepresentationを分離し、原文/文字offset/byte offsetを照合。可視source.contentに含まれないJSを同本文quoteと偽らない。
- 既存の保存byte契約でsource/raw/transport/textを点検したgeneric verifierはmatched。ただし意味・金融的妥当性の検証ではない。

`capture.json`、原response JSON/raw、`01.txt`/`01.content.json`、enriched transport、source-bundle、quotes、review、byte-verifier、validationを保存した。新規書込は本caseと共有rate制御fileだけ。DB・production code・旧artifactは変更していない。

## SIRとの比較は保留

SIR Sep28レポートのEPS91.64は会社予想としてSIRが再処理した記載、11.7%も同レポートが示す会社計画基準である。今回の会社入口からこれらが正式資料と同定義/同版だとは確認できない。SIRの値を直接会社原典の値や著者独自の点予測へ置換しない。

p25の本文`2027/5期会社計画`と最終列`26/5CE`の差は、原因の説明が得られず未解決のまま。現在の会社決算/予想を読めたことにも、過去著者予測の前向き評価にもしていない。新しい予測・割引率・公正倍率・確率・売買閾値・valuation・IR質問/送信・採点は0。
