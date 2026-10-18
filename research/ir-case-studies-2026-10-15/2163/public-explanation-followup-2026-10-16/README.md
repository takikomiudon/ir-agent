# 2163 IR FAQ・中間期補足説明の限定追加読解

初期保存rootのliteral [98] IR FAQと[434]対応補足PDFだけを、別phase最大2 GETで取得した。両方200・完全。説明会notice/分割通知・会社一般FAQ・採用FAQのGETは0。原2sourceを複製していない。

| 原資料 | 完全entity / raw SHA |
| --- | --- |
| `https://www.artner.co.jp/ir/other/faq/` | 198,030B / `75642be8724fad82cf1b90fdcd79066359719d9cb06fe962178ce427fee18d23` |
| `https://www.artner.co.jp/asset-ir/download_file/27.2q_supplementation.pdf` | 1,247,261B / `865f1858d239bc2e11ca8ce67a27c0364a44464f6d0143127f948f3aaedb0711` |

同hostのrobotsは初期取得完了 `2026-10-16T04:32:06.957542+00:00` の保存200規則を再利用し、各対象のcan_fetchとholds-v8の12hostを照合。現サーバー規則の再GETではない。通常proxy/TLS・固定UA、redirect/retry/別URL探索/JS/検索/フォーム/Cloud診断0。全HTTP時刻・response・原raw保存・完全性は `capture.json`/01–02.json。元取得時刻、後のlocal抽出観測、実DB初保存を区別した。

FAQ全文の静的visible textとPDF全22頁textをsource.contentへ保存したが、**FAQの意味確認は5つの選定範囲、PDFは物理11・12・16の3頁だけ**。FAQの正確な範囲は `FAQ-selected-scopes.json`、PDF表紙/目次/見出しは選定・書誌事項のみ。補足の他1–10/13–15/17–22頁は実質未読。FAQは常設の投資家向けFAQで、特定決算説明会の公表Q&Aとは別。FAQ公表/改訂日は不明、補足は9月10日day精度、双方exact publication clockはnull。FAQ内の2026年1月期は回答の対象期で公表日ではない。

公開既答として次を初期短信と比較した。

- **稼働率の分母**：通常は派遣稼働人員÷派遣対象在籍人員で、配属前の新卒等を除く。研修者込みは全社技術者数を分母に含む。高い通常稼働率を全員配属済みとは扱わない。補足p11も配属前入社者除外を明記する。
- **費用区分と時期**：未配属労務費はSG&A、配属後は売上原価。移動は費用消失ではない。賞与の支給月と引当対象四半期、下期の休暇による労働工数減少傾向、Q1新卒賃金は4月のみという季節性がFAQで既答。個別採用費/研修費・将来費用や正常化額は不明のまま。
- **単価と採算**：HVは契約単価と本人給与が連動し、粗利率はWV/PVより低いというFAQ説明がある。2026年1月期のグループ別単価帯/法定マージン率の例は今期実績やOP率とは別で、マージン率には研修賃金・採用等の費用が含まれる。単価上昇だけで利益率改善を保証しない。
- **単体・平均・期末の区別**：補足p11/12は明示的に単体。表の「’27年1月期(平均)第2四半期」の技術者数1,392/稼働97.6%は、Q2末7月のグラフ1,431人やQ2(5–7月)96.9%と違う表示。単価も表4,852円/時間とQ2グラフ4,895、工数168時間/月と169を区別する。平均の窓・重み・式は図のlabel以上に補完しない。人数×単価×工数から連結売上を再計算しない。前年中間連結値が非記載という初期の限界は維持する。
- **配当の基準**：補足p16は会社自身が分割前換算86円、実質2円増配を示す一方、43円中間/21.5円期末の単純合計不可・年計dashを維持する。会社の換算参考値を独自の分割後年間DPS/将来DDM列にしない。配当性向50%base/予想73.1%は会社方針/会社見込みで、投資家の売買条件ではない。掲載配当利回りは歴史的な分割換算株価を使う説明で、現在の価格/利回りへ転用しない。

FAQの資料案内は短信/補足がIR資料室にあるという公開回答。決算会議Q&A本文、資料掲載noticeの本文やイベント完了までは確認していない。採用費の数量分解、平均指標の計算方法、正常利益/将来CF、FAQ更新時点、未読ページ等は `review.json` の残余に保持する。

新原source2本・逐語引用8件（FAQ5範囲＋PDF3頁）。`source-quotes.json` にnative object/content/raw SHAとUnicode/UTF8 offset、`review.json` に初期bundle/source/意味範囲のpinを保存。metadata.financial_contentは内容のproducer判断で、native分類/金融採用とは別。Anthropicの公開先行DDとDamodaranの主体/利益/期間/単位/CF分離を用い、公開既答の重複質問を防ぐ準備とした。回答不存在や全FAQ/全冊読了は認証しない。

既存sharedbuilderを再利用しwhole original capture/rawを保持。producerはraw/全文/契約/stableID/8引用/3画像と初期32pins不変を照合。汎用byte verifierは未実行のためmatchedとはしない。DB/code/共有旧file/case/normalizer/金融採用/IR草案/送信0。freeze後の追加GET予定0、root独立意味受入待ち。
