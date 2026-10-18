# 収集保留 v4：独立点検

**58チェック、不一致0**。[JSON記録](independent-recheck-v4.json)へ原capture/raw/offset/時刻、旧entry値、instruction byte archiveと差分、読取専用DB照合を保存した。

v3の旧7entryはJSON値で完全保持され、追加は`data.swcms.net`1件だけ。新規配信hostのrobots1GETはHTTP403・完全199 bytes、固定configured/prepared UAは`Codex-IR-Research/0.1`、本文完了20:23:10.963399UTC。2引用の文字/UTF8 byte offsetとraw SHAは一致した。403 HTMLからrobots規則は確定できず、wildcard禁止・AI個別規則・PDF本文403・クラウド障害やレート制限の原因は認定しない。

会社IR hostのfresh robots200＋短信index200の2GETと3GET上限/同host計画を保持し、年次短信のliteral link39をraw HTML→text/links再現で確認した。配信hostは別有限phaseでfresh robotsを確認し、403後はPDF GET0で停止。retry/redirect/UA変更/別経路探索/Cloud診断を追加していない。正式金融本文は未取得である。

AGENTS/SKILL/rolesの旧完全byte archive・before/after SHAと変更箇所を照合した。差分はv4参照/8hostと新hold説明に限られ、過去実験のfingerprintは過去記録のまま。新holdを既存sourceの無効・分類変更・金融除外へ広げていない。旧7rawの全意味再レビューは行っていない。

実DBは`mode=ro`/`query_only`で124source、直前7157 FAQ処理後のSHAと一致し、新index/captures/PDFのsource登録は0。前後DB byte SHAも不変だった。新GET・DB書込み・既存file編集・金融判断・送信は0。追加は本MDと独立JSONの2fileだけ。
