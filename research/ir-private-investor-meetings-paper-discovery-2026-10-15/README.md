# 投資家との個別面談研究：書誌の有限確認

指定の題名をCrossrefで1回検索し、同題の書誌2件を確認した。本文は未取得で、IR効果の検証は未完である。

| Crossref登録 | 著者（各登録の表記） | 誌名・日付 | DOI |
|---|---|---|---|
| posted-content | David H. Solomon / Eugene F. Soltes | 誌名なし、2011年（年精度） | `10.2139/ssrn.1959613` |
| journal-article | David Solomon / Eugene Soltes | The Journal of Law and Economics、2015年5月（月精度） | `10.1086/684038` |

題名はいずれも **What Are We Meeting For? The Consequences of Private Meetings with Investors**。これは2つの登録であり、原稿と掲載版の内容同一性・改訂関係は本文未照合。rows=3の残る1件は別題名で、今回の研究対象へ追加しない。書誌の逐語field・JSON位置は[metadata-extraction.json](metadata-extraction.json)、原レスポンス全体は[metadata-capture.json](metadata-capture.json)内のraw_fileに保存した。

## 今回の運用への接続範囲

SSRN登録のCrossref metadataには要旨があり、NYSE上場1社の経営陣と投資家の個別面談データ、会合期の取引タイミング、ヘッジファンドへの集中、不確実性や公表情報との関係を研究した旨が記載されている。これは**登録要旨が述べる研究範囲**であり、本文のデータ・分析・因果識別・頑健性を確認した結果ではない。journal登録のabstractはnullで、SSRN要旨を掲載版の結論として移植しない。

今回に関連する問いは「公表情報が存在しても対話が何を追加するか」「効果が参加者・情報環境に依存するか」である。この問いを、IR質問前に既知情報と未解決点を分ける研究動機にはできる。しかし米国1社の個別面談という要旨上の範囲から、日本の個人投資家によるメール・フォーム質問の追加収益、返信の正確性、情報優位の持続、利益相反・参加者選択、数カ月〜1年の保有成績、質問頻度・費用の妥当性は認定できない。効果の値・因果・売買閾値・尤度をこのmetadataから採用しない。

## 保存されたliteral候補（アクセス・公開本文は未確認）

- `https://www.ssrn.com/abstract=1959613` — SSRN登録のresource.primary.URL。landing候補で、本文URLや無料公開を確認した意味ではない。
- `https://www.journals.uchicago.edu/doi/10.1086/684038` — journal登録のresource.primary.URL。landing候補。
- `http://www.journals.uchicago.edu/doi/pdf/10.1086/684038` — journal登録のlink[0].URL。content-versionはvor、intended-applicationはsimilarity-checking、content-typeはunspecified。これはliteral PDF候補で、一般向け取得許可・公開アクセス・licenseを示すものではない。httpsへの書換えもしていない。

候補URL・DOI landing・本文のGETはすべて0。次の本文調査は別の有限計画とし、各実hostの保留・robots・利用条件の確認が必要。今回の結果だけで追加GETを継続しない。

## 取得・停止の証跡

中央holds-v7の11 exact hostにapi.crossref.orgは含まれなかった。[guard.json](guard.json)に索引SHA、UA、固定query.titleとrows=3、予算2GETを保存。fresh robotsはHTTP404・完全105bytes（SHA `e61a074ca2e4f9d188e05a2fbb207940a17a1a2edf18445b02f985e8f7e1bde1`）、entity受信終了のローカル観測は2026-10-15T23:24:50.587950+00:00。docs/data-sources.mdの完全404未配置扱いを適用し、404本文を規則や明示許可と解釈しなかった。

works検索はHTTP200・完全11,917bytes（SHA `cbcc689ad6b8487f17798da2c41c69453b94950fbdc48f56f2eb701b69794398`）、entity受信終了のローカル観測は2026-10-15T23:24:59.899548+00:00。検索URL、HTTP開始・応答・終了、response metadataは各captureに保存した。rawはrequests.iter_contentのresponse entityで、content-decodedの可能性がありwire転送bytesではない。UAは既存collectorのir-agent-public-research/0.1設定で、独立wire監査はしていない。

[validation.json](validation.json)でraw byte数/SHA、capture SHA、元collector/運用docs/hold/network設定のSHAを照合した。runtimeのnetwork state=unknownはenforced認定しておらず、今回の2HTTP到達以上のreadinessを推定しない。取得経路の追加診断は0。GET合計2、retry/redirect追跡/他host/本文/DB/共有編集/外部連絡は0。この有限調達を終了する。
