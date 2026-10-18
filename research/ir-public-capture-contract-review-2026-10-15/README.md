# 公開資料の保存契約：3例の有限比較と提案

2026-10-15に保存済み3 sourceだけを比較した。実装・GET・DB操作・旧資料変更・全テスト実行は0。結果と入力15ファイルのSHAは [evidence.json](evidence.json)、不足8点と将来の限定検証案は [gaps.json](gaps.json)。提案するformat/versionは未登録で、現検証器が受理する契約ではない。

## なぜ unknown なのか

`scripts/verify_case_source_bundle.py` は、実際に調べた2種類のproviderと3種類のextraction.kindだけを扱う。未対応providerではファイル検査前に `unsupported_or_unspecified_provider`、`checks: []` で返る。未知のJSONから都合のよいSHA欄を探さない設計である。

| 選択した1 source | 現検証器 | 保存形式の差 |
| --- | --- | --- |
| 7525 IR基本方針 | unknown | provider未対応。さらに extraction.kind がなく、method自由文だけ。provider名を追加するだけでは不足 |
| 1518 カレンダー本文 | unknown | provider未対応。kindはhtml_visible_text、methodは自由文。本文の抽出と未読画像を区別 |
| 1332 正式短信 | matched | 既知provider、pdf_text、保存raw/snapshot/textの明示契約が一致。別sourceである同bundleのカレンダーは今回の比較に含めない |

3例とも、今回別に行った有限なraw/snapshot/textのSHA・byte count・snapshot.text/source.content比較は一致した。この局所比較を新2例の現検証器unknownに上書きしない。1332のmatchedも **declared_saved_case_bytes_only** であり、発行元真正性・取得完了時刻・rawからの再抽出・引用の意味・金融採用を認定しない。既存検証器はID導出も明示的に未実施である。

## 既存機能を使える部分

既存の `_relative` 相当の境界検証、`_artifact` 相当の保存ファイルSHA/byte count照合、`_comparison` 相当のmatched/mismatch/unknownの区別は共通化候補となる。ただし今はprivate helperで、公開API化や移動を実施したわけではない。`models.parse_json` の重複キー・非有限JSON拒否、sourceの型契約も再利用できる。

同じ `raw_sha256` / `byte_count` / `text` という見かけでも、取得・抽出の契約が一致した証明にはならない。3例ではraw/textの所在はすべて明示されているが、1332のcase rootは研究ルート、新2例は会社内phase。bundle所在をpathの基点と推測すると1332を誤解する。検査するpathごとに、その宣言された基点を使う必要がある。

## 新取得用の明示versionを提案

研究テーマを表すproviderと保存formatを分け、新規取得では `format: ir-public-response-capture`、整数 `version: 1` の契約を別途策定する。未知versionはunknown、認識した契約の不正な型・enum・重複JSONはvalidation error、既知ファイルの不一致はmismatchにする。provider追加や任意key探索で成功させない。次の項目は将来仕様の要件で、動作実装ではない。

1. **固定transport欄**：requestのmethod・実URL・設定UAとprepared UA、responseのstatus・complete_body・error・開始/headers/本文完了のaware時刻、response-entity bytesのSHA・byte countを別欄にする。requestsによるContent-Encoding展開後のentityか、wire bytesかもenumで明示し、Content-Lengthをそのまま保存byte countと同一視しない。応答headerのDate/Last-Modifiedは公表日時にしない。失敗・部分取得は失敗captureとして保持し、完全な本文sourceを装わない。
2. **固定artifact参照**：repo-relative case_rootを1つ宣言し、raw・transport・抽出outputはそのroot内のrelative pathとSHAで指定する。snapshot内recordは空文字のroot pointer、または明示RFC6901 pointerで1件だけ解決する。`/GETs/0`などの厳密index・`~0/~1`を含むキーを定義通り処理し、曖昧な検索やfallbackはしない。絶対path、`..`、NUL、symlinkによるroot外脱出を拒否する。1332の未検査のauthority `../03.json` を、新しい基点で勝手に検査済みにしない。
3. **version付きextraction profile**：HTMLはdecode方式、script/style抑制、HTML entity、各node空白縮約、joinと末尾LFを明示する。PDFはpdftotextのversion/引数、layout、form-feedとページ対応を保持する。profile実装/ツールの版またはSHAを固定し、単なる自由文methodを実行命令として扱わない。画像の手動転記は別のreviewであり、空本文や自動抽出成功へ代用しない。SDK行やJSONからのprojectionが後で必要なら別profileと明示pathを要し、HTTP本文契約から推測しない。今回はSDK例への追加調査は不要と判断した。
4. **本文binding**：rawは保存バイト不変。UTF-8抽出fileの実byteとsource.contentのUTF-8 byte、固定pointerで選んだsnapshot.textを比較する。改行を保存どおりに復号し、CRLF→LFの黙示変換をしない。引用はどの表現か、Unicode文字offsetかbyte offsetか、終端exclusive、必要ならPDF pageを明示する。同じ文字に見えることを同一byte・同一引用位置と混同しない。
5. **時刻とIDの境界**：新規成功sourceのretrieved_atは明示本文完了時刻へ結ぶ。公表日だけならpublished_at nullとpublication_date/precisionを保持。実DB first-saveは別の保存来歴でありtransport時刻から作らない。1332のlegacy retrieved_atから未記録の完了時刻を後付けしない。IDは共有stable_source_idの指定入力契約を別に検査できるが、byte一致の意味に含めない。

sourceからtransportへの参照と、監査用binding recordを分ける。最終source snapshotの `models.json_text(source)` UTF-8 SHAを保存する場合は外側の監査recordに置き、sourceが自分の最終SHAをmetadataへ含める自己参照を避ける。このJSON表現はプロジェクトの指定関数でありRFC8785と同一とは主張しない。

## 後方互換と結果の読み方

新formatはまず将来の取得だけに適用する。旧source/capture/ID/原バイト/取得申告時刻は変更しない。旧2providerの現行検査結果も保持する。過去資料へ追加の照合が必要なら、原snapshot/file SHAと実作成時刻へ結び付けた別sidecarに残し、当時から新formatで取得されていたとは記録しない。

将来のreportは少なくとも `format_support`、`declared_artifact_bytes`、`transport_source_binding`、`extractor_reproduction`、`citation_byte_binding` を分ける。抽出再現を実行していなければnot_performedを維持し、citationが一致しても意味・金融採用は未確認のままにする。ハッシュが一致するのは同じcaller側にある宣言とファイルの整合で、独立した発行元真正性証明ではない。

取得時のrobots・UA・収集保留判断はSHA付き参照で監査できるが、byte照合のmatchedを次GETの許可へ転用しない。後のhost保留を古い取得時点へ後付けもしない。新formatで下流のIR質問登録、送信、予測・投資閾値は追加しない。
