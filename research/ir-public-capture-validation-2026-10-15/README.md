# 公開資料の保存内容を照合する任意機能

既存verifierへ `--capture-binding` と `verify_public_capture_binding()` を追加した。新しい取得側が明示したsource/transport/保存ファイルについて、SHA・バイト数・参照位置・本文・取得時刻の宣言整合をオフラインで確認する。native schemaはversion 1、実装修正記録はrevision 2である。

**全1,372テスト成功（41.651秒）**。[全件記録](parent-full-suite.json)・[親の受入](parent-acceptance.json)を保存した。関連41件には、独立レビューで再現した2件の不備への回帰を含む。不一致の出力はpin照合前に復号せず、未知profileにも共通のimplementation検証を行う。[初回所見](independent-review.md)と[修正後の独立点検](independent-review-v2.md)を保持した。

旧7関数のAST・既知3実例の完全な出力は不変。旧source/IDやcaptureへ形式を後付けしていない。編集前/初回実装/修正後の全文コピーと、失敗の再現を残した。コード検証中の実DBは100sourceのまま、main SHAも不変だった。

一致は宣言された対応の整合に限る。抽出の再実行、引用の意味、発行元真正性、金融入力の採用、正確な公表時刻、DB初回保存や現在の取得許可を証明しない。現資料のunknownをmatchedへ変更する作業や自動取り込みgateは追加していない。

[使い方と契約](../../docs/public-capture-binding.md)・[設計](design-v1.md)・[修正内容](implementation-v2.md)を参照。
