# 価格を要しない参考計算を追加

会社の年次EPS/BPSが揃っていても、市場価格を未採用のため公開計算APIを使えず、私用関数を呼ぶ再現ファイルが必要だった。公開`calculate_reference_value`と`reference-value FILE`を追加し、既存6方式の検証・計算・精度・丸めを再利用できるようにした。価格やdummypriceを与えず、参考値だけを返す。[仕様](../../docs/reference-value-spec.md)。

明示されたweighted確率はそのまま使い、unweightedは期待参考値nullと範囲を返す。価格由来比率、MOS、売買actionは生成しない。CLIはStore起動前に処理し、入力の意味確認・金融採用は別に残す。

[全テスト](full-suite.log)は1,585件・37.349秒成功。[独立レビュー](independent-review/review.json)は必須指摘0で、新12件、旧priced48結果/8エラー、caller状態18件、資源guard6経路、CLI副作用3件を確認した。実装担当の旧priced111比較と、変更前のソース・差分・44コードpinも保存した。従来の価格付き関数本体は不変で、共通精度関数の変更は価格省略の分岐だけである。

[実会社の公開CLI利用](actual-company-reference-runs/verification.json)では保存済み入力と現在のnative原典を一致確認し、1975は3,979.69円、3817は5,150.99円を再現した。いずれもunweightedで期待参考値null、価格・注文・DB書込み0。金融thesisや買値・利確価格を採用した記録ではない。
