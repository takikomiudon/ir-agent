# v16表示説明訂正の独立追記

記録: 2026-10-15T15:28:10.223867+00:00。v15→v16の変更はrecorded_at・previous_index・previous_index_sha256・layout_note・revision_basisの5top-level fieldだけ。他全fieldと19entry/84factsはdeep-equalで、旧v15・親record・v15独立点検も保持されている。

新説明は19entry・84records・15社・17会社/原source組、v14の18entry/82factsに同じ135A現金残高の2表示を追加したこと、v15からはデータ不変で表示説明だけを訂正したことに対応する。2表示は加算資産/独立裏付けではないという限界を保持する。旧layout_noteの指摘は解消した。

親訂正recordとv16/旧v15のpath・SHA、変更field一覧は一致した。原sourceや全参照先の再監査、GET、DB/Store、コード/テスト、旧file変更、金融/IR採用は0。詳細は [addendum-v16.json](addendum-v16.json)。
