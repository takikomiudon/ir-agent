# 保有情報の申告と会社台帳の区別

会社台帳の `held` は管理用metadataで、窓口catalogや会社資料bundleの取り込みにも既定値が入る。投資判断に使う保有状況は、明示的な申告の記録から取得する。これは既存の「保有未確認なら判断保留」というプロジェクト契約の修正であり、新しい売買方針ではない。

`company set-status` の `--held` は保有、`--no-held` は未保有の明示申告になる。状態だけの変更では両flagを省略する。現在のstatusを維持したまま申告する場合は、その現在値を `--status` に指定する。

```bash
.venv/bin/ir-agent --db PATH company set-status COMPANY_ID --status CURRENT_STATUS --reason '利用者による保有状況の申告' --no-held
```

Pythonでは `Harness.set_company_status(..., held=True|False)` 又は `Store.declare_position(company_id, held)` を使う。明示申告は会社metadata、新観測、`position_declarations` のreceiptを同一transactionで保存する。同じboolでも新記録を追加し、過去の観測へ確認を後付けしない。実行時刻は書込transaction取得後に採取する。申告は利用者の陳述で、証券口座による確認ではない。

`Store.position_at` は従来のmetadata観測履歴として維持する。判断用の `declared_position_at` は指定時点以前の最新観測に対応するreceiptと、その時点までに申告が記録されたことを要求する。最新観測が無資格なら過去の申告へ戻らず、不明として既存の判断保留へ接続する。

catalog、provider、ingestのheldは、明記されたboolでもmetadataに留める。再起動やheld省略の状態変更も申告を作らない。旧観測の由来は復元せず、旧会社JSON・観測・質問・判断を移行で書き換えない。管理用metadataを使うキューの優先度は従来どおり。

架空ケースの `synthetic_position` は既存のsynthetic限定例外を使う。ファイルだけの `decision`／`ir-plan` はcaller snapshotの計算で、実DBの申告記録を取得する操作ではない。また[現在表示の範囲](current-price-views.md)は、保存判断の保有状況を現在時点で全面的に再検証する機能とは分ける。

[元の再現](../research/ir-catalog-position-boundary-review-2026-10-15/README.md)と[修正・全体テスト・独立点検の完了](../research/ir-catalog-position-boundary-review-2026-10-15/README-v3.md)を保存した。実企業の保有状況の確認や申告は今回実施していない。
