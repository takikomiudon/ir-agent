# 6080 初回公表資料の有限取得

指定一覧URLは https://www.ma-cp.com/ir/settlement/ です。中央7host保留と保存済みnegativeを照合し、robotsへ1回接続しましたがTLS証明書チェーン検証で失敗し、HTTP応答を受信できませんでした。指定の停止条件に従い、一覧・PDFの取得、retry・別経路・JS/API・trust設定変更を行わず終了しました。

保存snapshotの `$.links[60]` にhref `/ir/settlement/`、resolved URL、label「決算説明資料・決算短信」が残っています。これらの短い引用位置とSHAをroute-quotes.jsonへ記録しました。元HTMLが回収できたとは扱いません。

同host旧トップページの503/circuit-breaker記録は保持し、再試行していません。後のIRページ200保存から得た明示された未試行一覧だけが今回の対象でした。今回のTLS失敗も、会社拒否・robots禁止・資料不存在の証明ではありません。

固定UA Codex-IR-Research/0.1、TLSverify、40秒timeout、10MiB上限、redirect追跡なし、retryなし。robots接続試行1、HTTP応答0、一覧0、PDF0、source0です。raw配下の空ファイルは失敗処理が作成したローカルmarkerで、応答bodyではありません。text配下は未取得説明のみです。

会社資料の表題・期・公表日精度・取得完了・原典first-saveは未確認です。ローカル試行証跡の保存時刻を原典取得や過去first-saveへ付け替えていません。

IwaiNO335p6の成約・コンサル数/生産性/大型案件反動は上位指示の外部著者論点で、会社実績ではありません。本文未取得につき最大5頁の選択確認も0頁です。同対象期/グループ範囲の案件・人員定義、最新実績、中計、税制は検証していません。税法調査・原文日付補修・forecastモデル・IR質問は作成していません。

回復CSVのcontact confirmedは上位指示の保存文脈として保持し、現在の個人適格性は未知のままです。実DB・コード・監視・旧files変更・外部送信は0。capture/review/sourcebundle/validationとroute引用を新規保存し固定しました。
