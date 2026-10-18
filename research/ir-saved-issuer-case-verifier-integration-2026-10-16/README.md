# saved_issuer_case PDF宣言bytes検証：限定対応

今回の4318Q1に実在するsnapshot profileだけを既存verifierへ追加した。saved_issuer_case/pdf_text以外、未知top-level adapter profile、必須宣言不足はunknownを維持する。改変・矛盾はmismatch、型/安全path/JSON/時刻等の不正は形式エラーとする。単なるprovider追加や任意field検索は行わない。

raw・snapshot・抽出fileのSHA、抽出UTF8とsource.content、既知snapshot/nested captureのhash/count/URL（requestとresponse）/HTTP200・errorなし/complete/PDF宣言/時計順序と元retrieved_atを照合する。PDF本文の再抽出・金融意味・真正性・出典ID導出・引用の意味・DB初保存・現在許可は確認しない。元source/metadata/IDは変更しない。

新12＋旧legacy9＋native21＝focused42 tests PASS。raw/text/snapshot改変、rehashed URL/time/count/response/completionの矛盾、欠落/未知形式、CRLF、path/symlink、入力不変/秘密非出力を確認した。旧2provider/nativeの3代表出力はbefore/after JSON全bytes一致。新helper/dispatch/doc追記を除いた旧コードもbefore全文と完全一致。全suiteはrootに任せ未実行。

実4318Q1をRO検証した別結果はreal-Q1-verification.json（matched）。旧validation.jsonのunknownは保持し、原manifest22file全SHAとroot受入manifest SHAの一致を確認した。ネット/DB/Store・共有doc・既存tests変更0。before全文・after2file全文・diff・logs・pinsをこのfolderへ固定し、rootの独立review待ちで停止する。
