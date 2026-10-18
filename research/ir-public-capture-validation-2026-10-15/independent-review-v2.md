# Native capture binding：v2の限定再点検

**v1のP2指摘2件は解消しています。追加指摘はありません。** 固定code `65ba58f6…`の2変更と追加2テストだけを読み、元の再現入力と対照を新v2 probeで確認しました。

- NCB-01：hash/count不一致の非UTF8出力はmismatch/CLI exit1となり、output対record/source比較はunknown、record対source比較はmatchedを保持します。pinが一致した非UTF8出力は引き続きValueErrorです。
- NCB-02：未知profile名・未知versionでも、不正implementationはValueErrorです。正しい共通implementationの未知profileはunknown/identity未検証のままで、profile固有parameterを推測しません。

追加テストは旧assertを削除・弱化せず、API/CLI・secret非出力・ファイル不変と、正しいunknown/不正入力の対照を含んでいます。producerの41対象テストや全suiteは重複実行していません。

開始/終了ともlive 3ファイルはv2 copy/固定SHAと一致。v1の18証跡とmodels/common/旧テストは不変、旧7helper/API ASTは完全一致です。保存3実例をv2旧APIでfile-only再実行し、full reportが原版と完全一致（unknown/unknown/matched）しました。

[詳細記録](independent-review-v2.json)・[新v2 probe](independent-probe-v2.py)を保存しました。v1は不変。新GET・Store/DB起動・production/既存test/旧artifact変更・全suite実行は0です。
