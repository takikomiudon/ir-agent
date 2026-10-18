# 公表Q&A6組の独立抽出点検

**18逐語spanは一致。日付の説明ラベル2箇所は訂正が必要。** 元4ファイル、保存source/metadata、raw、取得時刻は変更していない。解釈出力・正解鍵・GET・DB・production・金融採用・送信は0。

6組・3sourceの質問/回答/結合spanを、既存source.contentの文字offset・UTF-8 SHAで確認した。raw/snapshot/保存抽出のSHA・byte count・bundle内のsource IDと位置も一致。さらに保存HTMLの該当Q&A blockを限定して読んだ。IIJ FAQはQ4/Q9の本文block全体、IIJ説明会は掲載順4/6、リックスFAQは掲載順2/5と対応し、本文を省略していない。HTMLタグを除いた比較は局所的な抽出忠実性の点検であり、原HTML自体と抽出本文が同じバイトという意味ではない。

IIJ説明会原文は「主な質疑応答の要旨」であり、発言逐語録ではない。FY26/1Q26の2027年3月期/同1Qという定義、一般論・短期・限定的といった留保は保持されている。FAQは会社が公開した質問形式の説明で、私たちが送った質問への受信返信や、投資家の実際の発言の証明ではない。掲載順と印刷Q番号の区別も適切。

## 必要な最小訂正

public-qa-03/04の `time_or_scope_label_from_question_or_document` は「2026年8月7日**公表表示**」と記載する。しかし原HTMLの見出しは次のとおり。

> 2026年8月7日：2027年3月期 第1四半期 決算説明会（オンライン開催）

直後に要旨の説明があり、この保存本文は説明会日付としての見出し表示を支える。独立した公表日指定は確認できない。source.published_atとsnapshot.publication_timeはnull。旧source metadataにはpublication_date=2026-08-07が存在するが、その派生ラベルを改めて公表日を証明する原文根拠として使えない。URLの20260807も根拠にはしない。

旧版を保持して、親が作る最小v2では次を推奨する。このレビューはv2自体を作っていない。

- **input-cases-v2.json**：`/cases/2/time_or_scope_label_from_question_or_document` と `/cases/3/time_or_scope_label_from_question_or_document` だけを「2026年8月7日と見出し表示された…（説明会日付の表示。公表日・公表時刻は未確認）」程度へ訂正。18span/ID/元時刻は保持し、実訂正時刻・旧SHA・変更pathを付す。
- **source-manifest-v2.json**：selected_casesをinput-v2のpath/SHAへ。IIJ_QAの旧metadata日付値は歴史的転載として残し、独立公表日確認falseと会議日表示の注意を明示する。元source metadataを書き換えない。
- **validation-v2.json**：新2ファイルのhashを結び、18span/原source不変に加えて日付役割も確認する。byte一致だけではこの自由文ラベルの意味を検証できない。

元READMEは「原文表示」「要旨」と記載し、この誤った「公表表示」表現を使わないため本文訂正は必須でない。必要なら別のv2案内を付せるが、元READMEは保持する。

旧IIJ retrieved_atがHTTP開始より早い点は、manifestがstored値とHTTP本文完了を分けて記録しており適切。新たに取得時刻を補正したり、その旧申告時刻で本文を知っていたと扱ったりしない。リックスFAQはsource取得時刻と本文完了が一致する。いずれもDB first-saveや公表日時の証明には変換しない。

[independent-extraction-review.json](independent-extraction-review.json)に4ファイルSHA、18span、追加context4span、raw Q&A block対応、日付根拠、最小v2提案と保護対象20ファイルの不変を保存した。保存範囲に独立公表日が見つからないことを、他の場所に公表日表示が存在しないという断定にはしない。
