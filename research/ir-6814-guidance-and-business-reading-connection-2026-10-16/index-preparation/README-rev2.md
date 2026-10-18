v41-rev2候補：既存4項目候補に6200の確定3項目を追加

proposed-index-v41-rev2.jsonは33社247fact・50親entry・52派生・43会社/原典組。旧v40の48親240fact、旧4fact候補の49親244factをwhole同一で保持した。proposed-index-v41.jsonと旧validation/READMEは変更していない。

追加は確定normalizer結果のQ3累計実績EPS36.63、当時通期会社guideEPS52.39、年間会社guideDPS35.00のみ。実績EPSは2025-10-01～2026-06-30、guideEPSは2025-10-01～2026-09-30。DPSは「2026年９月期(予想)」というラベルのみで、開始終了日はnullを保持した。旧年次EPS49.20/BPS148.70や当時旧guide55.15へ上書き・年率化・株数流用していない。8月3日原典のFY9月終了前の予想を、10月16日の現在予想又は通期実績とはしない。

6814の旧/修正4issuer_guidanceのscope/vintageも不変。全247項目を各factのartifact/source override優先で実bundleへ解決し、索引に存在するfieldを原factと照合した。旧項目にないscopeを補完していない。

actualは未観測・pendingのまま。root接続後の期待値50派生240fact、対象外2派生7factは期待値欄だけに置いた。旧v40 actual227sourceのwhole履歴を保持し、新しいDB総数・初保存・分類・モデル採用は生成していない。実source保存・canonical更新は別root作業。

validation-rev2.jsonに原典・最終bundle・旧候補のpinsと検証結果。GET/DB/Store/normalizer再実行/producer・共有docs・canonical変更0。
