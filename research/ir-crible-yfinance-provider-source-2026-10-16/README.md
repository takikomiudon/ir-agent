# crible yfinance provider：固定原典1fileの取得

固定commit `00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7` の保存済みtree `/tree/128` に掲載されたGit blobのみ1GETしました。既知manifestが保持する同host `api.github.com/robots.txt` の完全404（106B、2026-10-15T23:01:26.802572UTC）の既存missing-robots branchを原SHA・時刻・UA付きで再利用し、現helper/hold照合。新規robots取得0、上限2の残1枠は使っていません。

API応答はContent-Encoding:gzipをrequestsが復号したJSON entity（圧縮wire bytesではない）として200完全5409B、完了2026-10-16T16:07:18.039498UTC。base64をCR/LFだけ除去してstrict復号し、3722B・UTF8・Git blob SHA-1 `939798cc1d289bf9f0508ad8fabb47f273c73e1c` を原file bytesとGit headerから再計算してtree/API両方へ一致確認しました。原JSON/raw、復号した `upstream-yfinance_provider.py`、MIT LICENSE、commit/tree/license来歴pinsを保持しています。

取得コードはデータとして保存しただけでimport/execute/installは0。yfinanceやprovider APIの呼出契約・通貨・価格時刻・利用許諾の意味確認は別taskです。MITをYahoo価格の利用許諾にせず、実株価・新source/金融採用・DB/Store・credential読取は0。no-op authでnetrc照会を抑制しAuthorization未送信を記録、通常proxy/TLS/UAのまま、redirect/retry/childHTTPなし。旧資料・共有code/docsを変更せず11beforepins不変でfreezeしました。
