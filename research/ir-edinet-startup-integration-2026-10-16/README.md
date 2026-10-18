# EDINET固定初回起動

追加調査を停止するための最小起動スクリプトを用意した。環境変数 `EDINET_API_KEY` を設定後、`.venv/bin/python -B scripts/start_edinet_research.py --check` で有無と固定プランを確認し、`.venv/bin/python -B scripts/start_edinet_research.py` で初回取得する。キー値をコマンド引数や保存fileへ入れない。既存data extraのrequests/edinet-toolsを使用する。今回実キー・実APIは使っていない。

固定候補は古野電気6814・2026-10-09。会社Q2 p1の半期報告書提出予定日という根拠であり、提出済みとは認定しない。V2一覧type2を1GET、普通株6814・docTypeCode160・xbrlFlag1・訂正以外の一意行だけを選ぶ。0/複数はZIPに進まない。一意の場合のみtype1 ZIPを1GETし、原一覧/選択metadata/ZIP/完了receiptを保存、既存parse_edinet_package(source='instance')でcandidate bundleを保存する。期は返却値のまま保持し補完しない。

キー未設定と--checkは通信/DB/出力dir作成0。出力data/edinet-6814-2026-10-09/が既存なら停止する。retry/自動redirect0、通常TLS/proxy、有限timeoutとbyte/展開上限あり。成功bodyは秘密反射チェック後に意味・選択の判定より先に保存し、診断/例外本文/headers/認証URLは保存しない。圧縮ZIP内とparser戻り値・診断の秘密反射も拒否する。失敗/不確実な既出力を自動再送しない。

新10testsと既存adapter focused testsがPASS。API/SDKparserはsynthetic mockで経路と引数を確認したもので、実提出物の形式/認証/接続成功の保証ではない。金融採用/DBingest/IR送信/株価/定期起動は0。rootが独立reviewと最終suiteを行うまでこの2コードfileをfreezeする。
