# 2163 アルトナー：有限の初期公開研究

343社の個人IR受付明示候補で1975の次のcodeが2163。投資順位ではない。1,819元台帳同一行・実DB公開source0（URI mode=ro/query_only）・会社研究dir0を照合した。旧universe記録のfetches空は、以前のフォーム200成功記録の引継ぎであり取得失敗ではない。`root-2163-form.json`で個人投資家選択肢の原文を確認し、旧contact/157社回復は再取得していない。旧著者scan route0、財務取得保留なし。両CSVのSHA/列/件数、RO SQL、会社snapshot、旧coverage・成功記録のpinは `selection.json`。

最大5 GETに対し3 GETで終了。全て同host・200完全、固定UA/通常proxy/TLS。holds-v8と各URLのrobotsを照合し、retry/redirect/JS/検索/フォーム/Cloud診断0。

| GET | URL | 完全entity |
| --- | --- | --- |
| 1 | `https://www.artner.co.jp/robots.txt` | 174B、wildcard Disallow空を確認 |
| 2 | `https://www.artner.co.jp/ir/` | 216,843B、元CSVの公式IR入口 |
| 3 | `https://www.artner.co.jp/asset-ir/download_file/2027_q2.pdf` | 175,004B、日本語の最新中間期短信9頁 |

root links[433]が直接PDFのため中間index不要。本文p4に経営説明があり残枠を消化しない。raw全文/HTTP開始・headers・完了・原保存/response/SHAは `capture.json` と01–03.json。PDF全文は `text/03-full.txt` とsource.contentへ保存し、**意味/画像は物理1・2・4・6の4頁だけ**。3は場所選定、5/7/8/9は未読。全冊意味読了ではない。公表日は2026年9月10日day精度、source.published_atはnull、原取得とlocal抽出観測/実DB初保存を区別する。

今回の公開既答と重要な境界は次のとおり。

- 中間実績は2026年2月1日–7月31日。表紙は百万円未満切捨て、本文/P-Lは千円。売上7,075,025千円・OP1,217,085千円・経常1,222,269千円・親会社利益815,269千円。2026年1月期Q3から連結報告を始めたため、前年中間連結値/前年比は非記載。dashを0にせず、単体値の代入や独自前年比を作らない。
- p4はキャリア採用による技術者増、高稼働、稼働人数/単価上昇、請負・受託への配属増を会社説明として示す。採用/IT・DX/研修投資費用を売上増で吸収したという説明と、各要因の正確な寄与額や将来の正常利益は別。
- 通期2026年2月–2027年1月の売上14,021・OP2,017・経常2,001・親会社利益1,248（百万円）は会社予想で9月10日時点据え置き。会社予想を独自予測/金融採用へ昇格させない。
- 8月1日1→2の分割をEPS・発行/自己株/平均株へ前年度期首から遡及調整済み。二重調整や7月末の未調整法定発行株数への読み替えをしない。中間43円と期末予想21.5円は分割前後basisが混在し、会社は単純合計できないとして年間合計をdash表示。独自の足算/年間DPS/株式分母採用は0。
- p4の営業CF説明は資金獲得148,819千円、引当金減少/税支払/売上債権増などを列挙。利益・現金預金減少・CFO/FCFを同一視せず、退職慰労引当金の減少を正常化の足戻しにしない。**CF表p8は未読だが、p4のCF本文は読了**。p6の保険解約返戻11,796千円は営業外、投資有価証券売却損12,342千円は特別損失で、OPへ足し戻さない。
- 当中間期の重要な連結範囲変更は無。前年連結比較可能性や現在までの範囲不変とは別。中間短信は会計士/監査法人レビュー対象外と表示し、半期報告書等の別資料へ一般化しない。

追加公開先のliteralは `link-provenance.json` に固定した。root[434]補足22頁・[98]IR FAQ・[428]分割通知・[404]説明会資料/動画掲載noticeは**未試行本文**。短信p2は説明会後の主な質疑応答掲載を予定として述べる。現在のroot noticeラベルから実際のQ&A本文/イベント完了/回答不存在は認定せず、別の会社一般/採用FAQとも混同しない。

source-only2本（IR入口の資料ラベル・原PDF）、逐語引用5件。原object/content/raw SHAとUnicode/UTF8位置は `source-quotes.json`、解釈/未解決は `review.json`。metadata.financial_contentはproducerの内容判断で、native分類/金融採用とは別。Anthropicの公開先行DD/metrics/guidance/strategy-changeとDamodaranの利益/主体/単位/期間/将来CF分離を用い、業種による自動除外・正常化・価格/倍率/確率/閾値は作っていない。

既存sharedbuilderを再利用し、完全raw/原capture objectを保持。producer検証はraw/全文/契約/stableID/5引用/4画像に限定し、汎用byte verifier未実行をmatchedとはしない。画像生成時のfontcache警告はあったが終了0、4PNGの文字/数値を目視照合した。環境診断や再GETはしていない。

DBwrite・共有code/旧file変更・case・normalizer・金融採用・IR草案・送信0。freezeし追加GET予定0。rootの独立画像/意味受入待ち。
