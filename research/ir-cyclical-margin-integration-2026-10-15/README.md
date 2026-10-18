# 循環利益率と保存資料照合の統合

全1,186テスト成功（36.325秒）。[全件ログ](tests.log)、[独立再確認](independent-recheck.json)、[コードSHA](source-code-sha256.json)を保存した。

Damodaranの年間利益率の平均×適用売上高を純計算として接続。Toyotaの原金額12行を独立Fraction/Decimal計算と照合し、合成例の等重みと売上加重、負値、入力拒否、外部Decimal設定からの独立も確認した。原典の表示丸め・本文と表の差異は修正扱いにしていない。

資料照合は既知2種類のcapture形式についてraw/text/transportの宣言SHA・バイト数・本文対応を読むだけ。改変・CRLF・case外パスを確認した。unknown/emptyを成功trueにしない。財務的妥当性・真正性・正常化への採用・評価額は確認しない。機能による実DB変更、IR送信、注文はない。
