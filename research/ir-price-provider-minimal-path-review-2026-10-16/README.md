# 単社の価格取得へ進む前の最小経路

**直ちに実行できると確認済みの無認証価格経路は、保存済み根拠だけでは確定しなかった。** 次の最小候補は、既に取得したcrible固定treeにある未読provider本体1fileの契約確認。実価格取得・新adapter実装はまだ行わない。1975朝日工業社は年次実績EPS/BPSと研究算術が既存なので接続候補としただけで、投資選定ではない。価格やprovider symbolは未設定。

| 保存経路 | 再利用できるもの | 今なお足りないもの |
|---|---|---|
| maxgfr/crible → yfinance | 固定commitのtree、価格選択処理、利用条件のmaintainer説明、コードのMIT本文 | provider本体・yfinance版/API・価格調整・原通貨field・観測epoch/日付の実由来・1975同定・実データ利用条件。yfinanceは当環境のpackage pathに未導入、現在project依存にもない。 |
| 既存J-Quants | 導入済みSDKのcode/date指定とmaster、既存raw C/Date normalizer、JPY/day精度quoteへの既存経路 | API key・プラン・利用資格・通貨仕様と利用条件の実根拠。無認証経路ではない。SDK内部のpaginationと自動retryも有限取得前に考慮が必要。資格・キーは本作業で調べていない。 |

次の未読literalは `src/crible/providers/yfinance_provider.py`（3722B、Git blob `939798cc1d289bf9f0508ad8fabb47f273c73e1c`）で、実treeのURLは `https://api.github.com/repos/maxgfr/crible/git/blobs/939798cc1d289bf9f0508ad8fabb47f273c73e1c`。固定commitは `00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7`。元treeの位置・SHA、依存版が必要な場合の実pyproject blob、root MITの保存参照はinventoryに固定した。これは次のコード読取候補であり、価格APIのURLやGET許可ではない。

既読snapshotのlatest_closeはClose／close／Adj Closeを候補にするため、未調整価格を保証しない。日付を先頭10字に切るので、精密な観測epochの根拠にもならない。別FX moduleを読まずにJPYを補えない。cribleのMITはコードの条件で、Yahooデータの個人利用・非再配布についてはmaintainerによる説明に留まる。無料公開、keylessやMITから最新契約・商用reuseの承認を推定しない。

J-QuantsのDateは取引日で、既存quoteのJST00時は日付の下限。引け・約定・公表時刻ではない。日精度を受け入れるpolicyと許容鮮度は別の採用事項で、本票では設定しない。SDKの公開列に通貨fieldがないことと、既存normalizerがJPYを設定することも分けた。仕様参照host `jpx-jquants.com` は中央holdのまま、再取得・別URLによる迂回はしない。

135Aの静的価格経路は通貨・完全観測日時不足による有限終了を維持する。取得日と表示時刻の結合、別指標の時刻流用、推測APIへの移行を行わない。中央12holdを照合し、どの閉鎖・503・robots経路も再開していない。

[inventory.json](inventory.json)に15保存根拠のSHA／行scope、実tree entry、各候補の不足と次の条件を記録した。GET・DB接続・SDK import/install・キー参照・価格計算・旧file変更は全0。現在の正式仕様、権利、データ到達を新規検証したとの主張はない。rootによる次経路の選択まで停止する。
