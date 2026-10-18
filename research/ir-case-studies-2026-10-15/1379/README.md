# ホクト（1379）：未登録企業の初期公開財務確認

**正式な1Q短信11頁、説明資料35頁、IRカレンダーを取得した。財務数値のモデル採用・IR質問登録には進めていない。** 新規5 GETは全件200。過去に取得済みのroot/IR入口/FAQ/robotsは再GETせず保存snapshotをリンク根拠として再利用した。

## coverage順の選択と取得範囲

既存窓口台帳1,819社と実DBをURI `mode=ro` で照合し、sources0件の既存会社1,813社を証券コード辞書順に並べた先頭が1379だった。投資順位ではない。`selection.json` に台帳SHA・SQL・時刻・既存会社snapshotを保存した。会社はwatch/held falseを維持し、実DBへの書込みなし。

公式URLは https://www.hokto-kinoko.co.jp/ 、過去確認窓口は https://www.hokto-kinoko.co.jp/soudanshitsu/formir/ 。窓口の過去確認を現在の送信適格性と読み替えず、フォーム取得/入力/送信なし。短信表紙と説明資料の1379・ホクト株式会社を公式リンクと照合した。

| capture | 新規取得URL | 初回取得UTC | 内容 |
|---|---|---|---|
| 01 | [IR資料](https://www.hokto-kinoko.co.jp/corporate/ir/shiryou/) | 2026-10-15 05:14:24.938959 | 索引/現在のnavigation資料リンク |
| 02 | [決算短信の索引](https://www.hokto-kinoko.co.jp/corporate/ir/shiryou/tanki/) | 05:14:42.318904 | 静的索引。動的な過去一覧は未取得。 |
| 03 | [2027年3月期1Q短信](https://ssl4.eir-parts.net/doc/1379/tdnet/2870977/00.pdf) | 05:15:01.401229 | 正式決算短信11頁、表紙2026-08-12 |
| 04 | [2027年3月期1Q説明資料](https://ssl4.eir-parts.net/doc/1379/ir_material_for_fiscal_ym1/211033/00.pdf) | 05:15:08.757544 | 説明資料35頁、表紙2026-08-19 |
| 05 | [IRカレンダー](https://www.hokto-kinoko.co.jp/corporate/ir/calendar/) | 05:15:20.465268 | 予定と年度ラベル不整合を保持 |

各URL1回、retry/自動redirect/JavaScript実行0、URL/host推測・障害診断なし。旧robotsはMJ12botだけを禁止する内容で、今回のUser-Agentは該当しない。新規robots GETはしなかった。root/IR/FAQの旧snapshot3件は `reused/` へバイト不変でコピーし、元取得日時・SHAを `reused-evidence.json` に保存。旧snapshotには原HTMLバイトがないため、rawを再構成せず**リンク根拠だけ**として扱い、新規財務本文sourceにしなかった。

新規のraw/text/snapshot/SHA/初回取得は全5件を保存。HTML raw decodeと可視本文、PDF抽出本文を分けて保持した。明示リンク/配列位置は `link-provenance.json`。`source-bundle.json` は既存 `jp:1379` の5 sources、`companies=[]`、`theses=[]`、全件 `financial_inputs_verified:false` / `financial_values_automatically_adopted:false`。正式短信1件と説明資料1件を索引2件/カレンダー1件と区別した。

最新という表現は、今回取得した公式navigationで明示される決算資料の範囲。動的な過去一覧や全社公開情報を網羅したとはしていない。PDFの公表は日付まで確認できたが時刻/timezoneは未確認のため `published_at:null`、日付をmetadataに保存した。索引のニュース日付やカレンダー予定日をページ公開日時にはしない。

## 公開資料で解決した範囲

逐語引用15件・source ID・PDF頁/印刷頁・文字offsetは `sources.json` にある。見出しだけでなく本文・単位/期間付き表を含めた。

| 論点 | 確認した内容と引用 |
|---|---|
| 正式期・基準・連結 | 短信PDF1頁 `statement-identity-basis-actual-period`：日本基準・連結、実績2026-04-01〜2026-06-30。 |
| 比較期・概念 | PDF8頁 `statement-income-comparison-and-special-items`：前期2025-04-01〜2025-06-30、単位百万円。営業利益・経常利益・税金等調整前利益・純利益は別行。前年受取保険金も別の特別利益で、営業利益や継続利益へ置換しない。 |
| EPSと会社予想 | PDF1頁 `statement-actuals-and-EPS-table` は基本/潜在株式調整後EPSを含む四半期実績。`statement-company-full-year-forecast` は通期2026-04-01〜2027-03-31と会社予想の半期/通期を明示。通期予想EPS167.22円等は会社予想で、独自将来予測として採用していない。 |
| 予想の変更 | PDF5頁 `statement-unchanged-forecast-caution`：5月15日公表予想から変更なし。達成保証ではないという会社の注意書きも保持。 |
| Q1キャッシュフロー | PDF11頁 `statement-cashflow-not-prepared`：「当第１四半期連結累計期間に係る四半期連結キャッシュ・フロー計算書は作成しておりません。」続く減価償却表も含めた。減価償却だけをCFや将来FCFにしない。 |
| 利益変動の会社説明 | 説明PDF5頁 `presentation-actual-operating-profit-drivers`、12頁 `presentation-actual-vs-initial-plan` に国内きのこ価格、化成品価格改定、費用抑制等の説明。初期計画と実績の比較は通期予想変更と別。 |
| 配当・還元方針 | 短信PDF1頁 `statement-dividend-forecast` は年間62円の会社予想。説明PDF15頁 `presentation-payout-policy-and-forecast` は内部留保を確保し安定配当に努める、2029/3期DOE3.5%目標、内部留保を戦略投資へ優先という会社方針。 |

公表済みの期/基準/比較表・会社予想変更有無・Q1CF作成有無・説明済み利益要因・配当予想/会社方針を、そのままIRへ聞き直す必要はない。会社のDOE目標は投資家の購入閾値、DDMの割引率/成長率、長期配当の保証にはしない。単年度予想DPS/EPSを未来の配当列・収益列や確率へ自動延長していない。

## カレンダーは予定と不整合を分けて保持

`calendar-body-with-inconsistent-label` は、見出し **「2026年3月期（2026年4月～2027年3月）」** と、**「第2四半期決算発表 2026年11月13日予定」**、変更可能の注記を含む。正式短信の「2027年3月期」と年度ラベルが整合しないため、誤記と決めて書換えていない。

`review.json` の次回日付は2026-11-13、status=planned、time=null、対象年度は不整合のためnullとした。カレンダーの予定を発表済みや確定日と扱わず、スケジューラ/実DBへ登録していない。

## 未確認とモデルへ進む前提

公開決算Q&Aの本文は未取得。旧一般IR FAQや説明資料を、そのまま決算説明会Q&A記録と扱わない。Q&A不存在、公開で答えがないという結論も出していない。

通常model点検はneeds_data、金融・循環正常化・young-lossの該当はnull。食品業というラベル、黒字1四半期、会社の価格説明だけでrouteや除外を決めない。現在と前年の四半期、参考の月次市場価格は、全事業サイクル・季節性モデル・正常利益の立証ではない。全サイクル/現在規模・再投資/税/資金条件、予測株数・希薄化、将来配当/収益の持続性・評価前提などが不足する。

保存済みAnthropic参照の公開情報先行とDamodaranのモデル適合確認に沿った研究記録で、価格・独自予測・倍率・ROC/税率・確率・売買閾値・モデル評価・送信準備済み質問は作成していない。`review.json` に公開で消せる問いと欠損を保存した。

`validation.json` で5sourceの契約/stable ID/raw・decode・抽出本文・snapshot SHA、本文15引用、旧snapshot3件のバイト不変/再GETなしを確認。DBアクセスは選定時のread-onlyのみで、取り込み/分類/会社状態変更・IR送信/注文は未実施。初期5 GETをここで区切った。
