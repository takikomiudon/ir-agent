# Native capture binding の独立コードレビュー v1

固定code `5065fb52…`と仕様・新19テストを点検し、**P2の契約不備2件**を合成fixtureで再現しました。誤ったmatchedや金融採用の再現ではありません。

1. **未一致outputの非UTF8 decodeがmismatch報告を遮る** — `verify_case_source_bundle.py:488–490`。古いpinのままtext.txtをUTF8改変するとmismatch、`b'\xff'`へ改変するとValueError/CLI exit2でreportがありません。pinがmatchedの場合だけdecodeし、他はtrusted_output=Noneとして既知mismatchを保持する最小修正が適切です。pin一致の非UTF8を拒否する既存テストは維持します。
2. **未知profileでv1共通implementation検証を迂回** — 同`:321–328`。既知profile＋implementation=[]はValueError、profile名を未知にするとunknownです。既知name/version2＋不正name/version/SHAもunknownでした。共通implementationのshape/type/SHA検証をunsupported判定前へ移し、未知profile固有parameterはunknownのままにします。

失敗captureのraw:nullは固定nullable欄にありません。現拒否は設計どおりで、第三の不備にしません。nonnull raw/失敗/no outputはmismatchでした。

pointer/path・時刻・scope・not_performedを読み、合成secret非出力と各audit前後ファイル不変を確認。旧7関数ASTと保存3実例のfull reportは一致し、default API/明示opt-in境界も維持されています。開始/終了ともlive 3ファイルはafter copy/固定SHAと一致、models/common/旧テストも不変です。

[詳細記録](independent-review.json)と[実行可能probe](independent-probe.py)に再現・既存coverage・最小修正案を保存しました。GET・Store/DB起動・production/既存test/旧artifact変更・全suite再実行は0。修正はしていません。このv1記録は以後上書きしません。
