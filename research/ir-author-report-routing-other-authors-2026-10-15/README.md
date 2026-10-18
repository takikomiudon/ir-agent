# 別著者の評価手法へつながる保存経路

**3社・4経路を追加候補として保存した。** 本文の予測・評価式・目標株価・報酬関係は全件未確認。GET・DB・旧資料／production変更は0。投資順位ではない。

| コード・会社 | 保存公式ページが示す著者／対象 | 実経路と限界 |
|---|---|---|
| 7525 リックス | QUICK&NOMURA コーポレート・リサーチによる当社調査 | https://www.nomura-ir.co.jp/ja/qnresearch/report_7525.html 。会社別report entry、PDF直接リンクではない |
| 8151 東陽テクニカ | QUICK・野村インベスター・リレーションズによる当社調査 | https://www.nomura-ir.co.jp/ja/qnresearch/report_8151.html 。会社別report entry、PDF未特定 |
| 8151 同 | アストリアス・アドバイザリー・ジャパンによる当社調査 | https://corporateresearch.astrisadvisory.com/ja/toyo 。会社別report entry、本文未読 |
| 9765 オオバ | 2026年9月28日 FullReport配信の会社告知、著者不明 | 保存された長いpercent-encoded実URLを[routes.json](routes.json)の`9765-other-author-route-62`へ保持。著者名や掲載PDFを推測しない |

母集団は台帳1,819社中の個人受付explicit343社。全343コードを列挙し、指定既存案件のうち母集団内4社（135A/1518/1827/3386）は明示skipした。残339社の保存JSON2,347件を読み、公式host・HTTP200の本文／links1,611件を限定キーワード検索した。331社には対象本文があり、8社は該当する保存公式本文がなくunknown。読めないJSONは0。前wideで未処理だった125社も今回すべて列挙・保存証拠の確認対象に入ったが、現在Webや未保存ページを調べたわけではない。

コード文字列順で走査・表示し、同一会社内は保存link位置順にした。10社・20URLは上限であり埋める目標ではない。今回の候補4経路と非候補例2経路の計6実URLで終了する。定義したkeywordに一致しない資料や、未保存ページに他の著者がいないという結論ではない。

SESSA/セッサ、ホリスティック、いちよし、フィリップ、岩井コスモ、アルファ・ウイン、AENTRO、ブリッジレポート等と、明示的な証券・アナリスト・企業調査レポートのラベルを調べた。今回の具体的な別著者は、レポート明示ラベルからQUICK/野村IRとアストリアスを拾えたもの。『アセッサー』『フードプロセッサー』『ミートプロセッサー』の部分一致をSESSAとしない。一般的なアナリスト索引や企業価値向上の会社方針を、別著者の評価式の直接経路へ昇格しない。

SharedResearch、wide既選択12URL、既知停止のweb.fisco.jp／ssl4.eir-parts.net／contents.xj-storage.jpは今回の取得候補へ入れていない。web.fiscoのrobotsURL403をallpath禁止本文や記事403と混同せず、停止根拠は既存wide記録を参照するだけ。これらの著者・hostの再取得は0。会社の投資除外も行わない。

[routes.json](routes.json)に全343コードと会社別検索範囲、実URL／label／href、source snapshot・本文SHA、JSONpath・逐語引用・offset、未読事項を保存。[validation.json](validation.json)に6経路の再照合、選択会社の台帳所属、2,347旧snapshotのhash不変を記録した。元応答rawSHAは旧captureの申告値と区別し、今回原HTMLの独立再確認をしたとは主張しない。ラベルが本文textになければlinksラベル自体を引用し、架空の本文offsetを作らない。

次に本文を読む場合も、現robots・アクセス条件と会社別レポートの実体を確認する必要がある。作者名・本文の式・会社予想との区別・対象期・通貨／株基準・到達時期を読めるまで、式を逆算・補完しない。`current_accessibility`と`current_outreach_eligibility`はnull、金融入力・モデル採用・IR質問・送信は0。

source/catalog/recordパスはrepo-root基準。追加物はこのREADME／routes／validationの3ファイルのみ。
