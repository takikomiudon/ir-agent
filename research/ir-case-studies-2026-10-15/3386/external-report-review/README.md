# 3386 コスモ・バイオ：外部レポート本文は取得前に保留

保存公式ページのSHAと `$.links[81]` を照合し、「アナリストレポート（アップデートレポート）が公表されました」の実リンクを確認しました。対象は <https://ssl4.eir-parts.net/doc/3386/ir_material2/285397/00.pdf> です。original hrefは旧JSONに残らず、保存resolved URLをそのまま用いています。

**GETは0件（上限2）。本文未取得で終了しました。** 同日5:47取得の `1379/annual-cashflow-followup/02.json` に、このhostのrobots200応答 `User-agent: * / Disallow: /` が保存されています。原26バイト・本文SHAを照合し、既存robots判定器でも実PDFパスが拒否されることを確認。robots再取得・PDF要求・別経路探索を行っていません。共有送信lockの利用対象となるHTTP送信もありません。

作者・レポート日・委託報酬・著者独自EPS/利益予測・会社計画の転載・目標価格・評価式・事業仮説・反証条件は、すべて本文未読の**unknown**です。表題から内容の存在も不在も判定しません。リンクの存在だけでは数値モデルを再現できるか答えられません。

回復後1,819社台帳のexplicit343社内に3386があることをオフライン照合しました。現在の窓口条件を再確認したものでも、投資候補へ採用したものでもありません。

`review.json` に原snapshot/text/rawSHA、初回取得と完了日時、実リンクJSONpath、逐語offset、既知robots原文を保持。旧5ファイル不変を `validation.json` に記録。`source-bundle.json` は正規fullschemaの空配列で、未取得reportやrobotsを金融sourceへ作り替えません。将来取得できる場合のsource.retrieved_atはHTTP本文完了時刻とする契約を明記し、今回は架空時刻を作っていません。DB/旧file/code変更、モデル採用、IR草案・送信は0。この有限調査はここで完了です。
