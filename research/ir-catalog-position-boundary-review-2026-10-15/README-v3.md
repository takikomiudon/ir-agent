# 台帳のheld既定値で保有確認を解除しない

窓口catalogや会社資料bundleのheld値を、利用者が保有状況を申告した記録と区別した。新しい実判断では、明示した `company set-status --held/--no-held` 又は専用APIによる新観測と申告receiptを使う。省略・ingest明記bool・provider更新・再起動ではreceiptを作らない。

会社metadataと旧観測・質問・判断を保持し、同値の再申告も新時刻で追記する。最新観測が無資格なら過去の申告へ戻らず保留する。証券口座の照会結果とは呼ばない。[操作と互換境界](../../docs/position-declarations.md)を参照。

[実装と対象80件](implementation.json)、[全1,351件成功・37.599秒](parent-full-suite.json)、[独立レビュー](independent-review.md)、[親の完了確認](parent-acceptance.json)を保存した。独立レビューでは具体的不備0件、別の合成DB3件で元の欠陥・申告時点・再起動・途中失敗の取り消しを確認した。レビュー後の現コードは全体テスト時の完全copyとbyte一致し、全体テストの重複実行はしていない。

実運用DBのmain SHAは不変で、この修正で実DBを開いていない。実企業の保有申告・金融入力・売買方針の採用・送信は0。旧保存判断の表示は[既存の限定範囲](../ir-current-position-view-boundary-review-2026-10-15/README.md)を維持する。pure `decision/ir-plan` はcaller snapshot計算で、live DB確認が付いたわけではない。

[元の2合成DB再現](README.md)と[実装時checkpoint](README-v2.md)は当時の記録として保持する。
