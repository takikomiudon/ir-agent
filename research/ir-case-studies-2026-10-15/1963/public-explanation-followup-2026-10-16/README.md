# 1963 公開決算概要・Q&Aの限定追加読解（2026-10-16）

日揮ホールディングスの保存済みIR索引 `04.json` の literal links[92]・[94] の本文だけを、新しい有限枠2 GETで取得した。両方200・完全entity。初期5 GETの記録は不変で、注釈版 links[93] は未試行。robots/root再GET・redirect・retry・別host探索は0。`guard.json` はholds-v8の12hostと同hostの完全404 robots既存missing branchの原バイト・capture・SHAを固定する。404 HTMLを許可規則と解釈したのではない。

- 概要：`https://www.jgc.com/jp/ir/ir-library/assets/pdf/fy26_1q_gaiyou.pdf`、905,429B、raw SHA `7ff8a66d9ea498bbf423733aeeb7099a467d95dfae7308bcfbed7992b53240a5`。全文18頁を `text/01-full.txt` とsource.contentへ保存。意味/画像は物理4・5・7・11のみ。見出しは場所選定に使ったが、その他1–3/6/8–10/12–18を実質読了とはしない。
- 公開Q&A：`https://www.jgc.com/jp/ir/ir-library/assets/pdf/fy26_1q_OnlineConference_j.pdf`、303,577B、raw SHA `0cc65ee3099804239cadbc584a7553b156cda8a31481cfb362fa9a51d8fc87b6`。全文4頁を `text/02-full.txt` とsource.contentへ保存し、物理1–4全頁を画像/意味確認。8月10日付公表、内容は8月7日説明会時点。概要公表日は保存索引の8月7日・PDF metadataからday精度、双方exact publication clockはnull。

実HTTP開始/headers/完了・原raw保存は `capture.json` と `01.json`/`02.json`。その取得完了時刻を原source時刻へ保持し、後のlocal全文抽出観測時刻・実DB初保存とは区別した。本文にはPDF全文が入り、限定意味確認のmetadataを別に保持する。

会社説明として公開で確認できた主な点は以下。原頁引用・sourceID・native object/content/raw SHA・Unicode/UTF8 offsetsは `source-quotes.json`、解釈は `review.json`。

1. Q1粗利益率12.8%が通期予想10.9%を上回る1.9ptについて、会社は約30億円、円安約15億円とPJ採算改善約15億円と説明した。これは前年同期の営業利益増加44億円や営業外為替差益3,882百万円の分解ではない。採算改善は前期末のリスク対応費用の戻りではないと明示する一方、終盤PJのリスク低減・過去完工PJの見込費用不要を挙げる。将来の正常利益/継続利益へ読み替えない。
2. 通期据え置きは、為替150円想定への収束時の通期為替差損想定と、中東などの事業環境不透明感を説明。機能材調達リスクはQ1末で顕在化していないという時点付き説明であり、今後のリスク消失ではない。
3. 総合エンジニアリングの受注高/残高は億円・Q1累計/期末の違いを保持。SAF年度内受注は会社の期待であって契約成立や確率ではない。UAE LNGでは大きな機器輸送影響なし・代替ルート検討と説明するが、影響回避の具体的な解消期限は示せないと明記。
4. 概要はQ2持分法会社売却特別利益約200億円を通期予想の前提として記載し、Q1実績・営業利益・FCFへ移さない。QA回答は水ing譲渡に伴うcash-inと中計2026–2030全体での配分方針維持を説明し、直ちに追加還元を想定しない。25,608百万円・7月1日完了は左の**質問者提示**であり、会社回答として対価/完了日を認証していない。原短信p11との取引数値比較は別担当rootのscope。ここで誤記/矛盾の断定・補正はしない。

会社のFY2026は2027年3月期。Q1実績2026年4–6月/前期比較2025年4–6月、通期会社予想2026年4月–2027年3月を区別する。連結P/Lは億円表示、EPS/DPSは円。受注は総合エンジニアリング事業で、売上・現金とは別。原短信の百万円単位、期末/平均/自己株式や新規連結JGC Emiratesの歴史的scopeを上書きしない。新会社の開始日・経路・寄与、正常利益/税/将来CF、リスク引当の詳細等は未解決。概要の未読ページ・後日の現況・注釈版は未取得/未確認を維持する。

Anthropicの公開情報先行・metrics/guidance/strategy-changeとDD前読、Damodaranの利益段階/単位/主体/将来CF分離を適用した。`metadata.financial_content=true` は内容に基づくproducer判断であり、native分類や金融入力採用を意味しない。既存builderを再利用したsource-only2本、8頁引用、画像8枚を用意。汎用byte verifierは未実行/unknownのままで、matchedとはしていない。source契約・stable IDs・raw/fulltext/引用・旧42pinsはproducer側照合済み、rootの独立意味受入待ち。

DBwrite・正規化・case・IR草案・独自予測・価格/確率/閾値・送信・旧file変更は0。このfolderをfreezeし、追加GET予定0。
