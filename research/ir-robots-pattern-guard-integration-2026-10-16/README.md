robots wildcard / terminal $ の拒否側ガード

保存済みJ-STAGE robots（/*_pdf）とliteral PDF URLで、旧stdlib/helperはtrueとなる不具合をGET0で再現した。Protego0.7.0を純Python・追加依存0で固定導入し、raw規則を保持した選択groupの追加拒否判定に使用。article/検索は許可、PDFはfalse、実本文GETは行っていない。

旧stdlibのUA/group選択とliteral最長一致を上限にANDする。Protego独自のgroup選択/mergeへ切り替えない。raw directiveとstdlib選択rule tupleの一意対応はstdlib自身のparseで照合し、不明/曖昧は拒否。独自RFC/wildcard matcherは実装していない。parser再parse後はraw対応を無効化する。patternからの新Allowやsaved denial解除は作らず、6383literal修正と旧保留は維持。Fetcherとcollectの生成箇所2つも同factoryへ接続した。

before全文とSHAはbefore/・before-pins.json、差分はchanges.diff、保存原規則での前後判定はreproduction-*.json、比較と依存根拠はdependency-choice.json。新pattern7、既存contact79、followup77の計163対象testsがPASS。bodyGET未実行mock、複数wildcard/末尾$、query/literal特殊文字、UAgroup、unknown/ambiguous/reparse raw、collectの保存規則と記録不変を検証。fullsuiteはroot担当。

企業/JPX/J-STAGE等サイトGET0、PDF0、実DB/Store/contact記録/holds-v8/共有docs/金融コード変更0。ネットワーク使用は許可された通常PyPI metadata2件と固定package取得だけ。旧保存成果/閉じた収集経路は変更・再開していない。
