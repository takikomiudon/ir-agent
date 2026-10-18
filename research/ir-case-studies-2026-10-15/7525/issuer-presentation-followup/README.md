# 7525 — 決算説明会資料入口で停止

保存公式リンク`$.links[128]`の入口を1GET（HTTP200）だけ確認しました。直前の同社robots200を原バイト/SHAで参照して当該path許可を照合し、新しいrobots要求はしていません。最大3新GETのうち残2件は未使用です。固定UA・global2秒lock・通常proxy/TLS、retry/redirect/JS0、16MiB上限で実行しました。

返ったHTMLには「決算説明会資料」の見出しがありますが、年度select、資料名h2、資料リストulが空です。raw中の.pdf文字列も、実160anchors内のPDF hrefも0件でした。`/xj/XjStorageLoaderlibrary03.js`の参照はありますが、取得・実行・API推測・別入口探索へ進んでいません。

したがって最新年度のPDF、オリジナル品比率の最新値・測定期、実績/計画、連結/単体、分類/内部消去/再分類等の注記はこのphaseで確認できません。QUICK29.3%や会社40%/55%目標との比較結果はnullです。会社が資料や定義を公表していないとは断定しません。

[source-bundle.json](source-bundle.json)はindex-only/financial_content=falseの1sourceだけです。取得時点は応答本文完了、公表時刻はnull。新providerのgeneric verifierはunknownを保持します。[quotes.json](quotes.json)で空placeholder3点・未取得script参照・見出しを別表現のoffsetで記録し、[validation.json](validation.json)でraw/text/captureSHAとメモリ再抽出、旧GP/LV主要入力の不変を照合しました。

原GP/LV phase、DB、production、旧資料は変更していません。新金融本文0、モデル採用・反証閾値・線形進捗・EPS換算・IR草案/登録/送信は0です。
