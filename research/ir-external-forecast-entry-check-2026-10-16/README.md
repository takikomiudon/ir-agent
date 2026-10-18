# 保存済み外部予測資料の入口確認（0 GET）

3社の保存済み公式HTML6件だけを確認した。新しい外部著者の予測・評価本文や金融採用を確認したものではない。

| 会社 | 保存入口 | 所在 | 判定 |
| --- | --- | --- | --- |
| 2315 | FISCO 企業調査レポート | 初期03.json links[234] | web.fisco.jpの保留host、本文未取得 |
| 2163 | スポンサードリサーチレポート | 初期02.json links[89] | 公式index、著者・実report・対象期は未確認 |
| 2163 | アナリストカバレッジ | 初期02.json links[61] | 公式index、アナリスト名・予測本文は未確認 |
| 2163 | FISCO/はっしゃん氏の社長対談案内 | 初期02.json links[403] | 対談のラベルで、外部著者の予測レポートとは別 |
| 1975 | 保存root HTMLでは未発見 | 初期02.json | RESEARCHは会社の技術研究開発。全サイト/PDFの不存在へ広げない |

`entries.json`に各保存ファイルSHA・全重複配列index・anchor・literal href・resolved URL・exact hostのholds-v8照合・ラベルから分かる著者候補だけを保存した。2163の公式indexは未取得の候補で、後続hostが許可済みという意味ではない。会社資料の会社予想を外部著者予測へ読み替えない。Fisco/SharedResearch等の保留先や2983旧経路、別会社/検索へ横展開していない。

GET/DB/production/旧file編集/原source追加/金融採用0。意味上の不存在や予測内容は認証せず、今回の一度限りの入口確認をfreezeする。
