# 141A v2時刻訂正の独立追記

記録: 2026-10-15T14:02:15.648949+00:00。v1と旧独立点検を保持し、v2の差分だけを確認した。

v1→v2の変更は `revision_provenance`、`timing.first_saved_report_at`、そのunknown理由、`timing.http_body_completed_at` の4pathに限定される。実初回保存はnullとなり、HTTP本文完了 `2026-10-15T10:32:09.014654+00:00` はcapture `GETs[2].http_get_completed_at` と一致する別fieldに保持された。元captureに実first_savedの証跡はなく、unknownの扱いが適切である。

この4pathを除くJSON全体はv1と深い比較で一致し、元研究時刻 `2026-10-15T13:51:35.173660+00:00`、著者・論点・意味区分・閾値null・金融path・窓口条件と11引用を保持している。v2のrevision記録は旧case/README/captureのpathとSHAに対応し、README-v2末尾は旧READMEの完全byteを保持する。旧4fileと旧独立点検2fileのSHAは不変。

v1の時刻ラベル指摘はこの訂正で解消した。PDF画像の再点検、GET、DB、コード・テスト、旧file変更、金融採用、IR作成・登録・送信は0。実初回保存日時や現在の企業・市場・受付状況を確認したものではない。詳細は [independent-v2-addendum.json](independent-v2-addendum.json)。
