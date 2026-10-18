# 新native取得向け：成功source bindingの最小オフライン検証案

**実装対象は1件の明示source-binding sidecarと保存bytes/transport/sourceの一致だけ。** 8不足を全面実装せず、既存verifierと同じfileに`verify_public_capture_binding(binding_path, *, repository_root)`を追加し、既存CLIへ明示opt-in `--capture-binding`を設ける案。既存API/通常CLI/旧2providerの出力shape・matched/unknownは変更しない。未知format/versionを既知providerへfallbackしない。まだコード編集・GET・DB・testsは0。

## 必須の最小構造

外側`ir-public-source-binding`整数version1に、明示repo-relative case_root、source artifact(path/SHA/count)＋RFC6901 pointer＋元sourceのjson_text snapshotSHA、transport artifact(path/SHA/count)＋record_pointerだけを必須にする。自己snapshotSHAはsource metadataへ入れず外側sidecarへ置く。

選んだrecord自身は`ir-public-response-capture`version1を宣言し、request(GET/url/設定UA/preparedUA/開始)、response(url/status/complete/error/headers時刻/本文完了/body representation/Content-Length参考欄)、raw/抽出text artifact、profile enum/version/implementation宣言/parameters/textを持つ。既知v1は未知fieldや型/enum不正を拒否し、callerverified等の認定flagは受理しない。全必須キー・型・nullable失敗欄・一貫した合成例をJSONへ固定した。実artifactは作成していない。

## 検証順と結果

1. parse_jsonで重複/nonfinite/不正UTF8を拒否。bool/floatをversionやcountへ認めない。未知format/正整数versionはunknownで停止し、参照fileを探索しない。
2. 明示case_root内のpathだけを読む。absolute/../NUL/symlink escapeを読取前に拒否。source/transport artifactのSHA/countが一致した場合だけpointerを解決する。空pointerはroot、~0/~1を1回だけdecode。arrayは0又は先頭zeroなしASCII整数、-不可。objectの01/-/空keyは別扱い。正しいpointerの欠損はunknown、構文/型不正はvalidation error。
3. 生source dictのjson_text UTF8 SHAを先に照合し、validate_sourceを別に使う。source IDの計算はしない。source_typeは初版public_disclosureだけ。
4. 成功source bindingはGET/HTTP200/complete=true/error=null/response entityだけ。失敗・partial・redirectは有効な失敗記録でも成功sourceにはならずmismatch。wire_captureは明示enumとして区別してscope外unknown、entityへ読み替えない。
5. aware時刻を同一instantとしてstarted≤headers≤complete、source.retrieved=completeで照合。URLのrequest/response/sourceと設定/preparedUAは完全一致で、URL正規化/通信/redirect探索はしない。これらの値・header・error実値は出力しない。
6. raw/output artifact SHA/count、output UTF8 bytes=record.text UTF8=source.content UTF8を照合。read_bytes→decode/encodeでCRLF・BOM・formfeedを保存どおり扱う。Content-Lengthはwire/encodingにより保存entityと違い得るので、countへ流用しない。
7. profileはplain_utf8_preserve/html_visible_nodes_lf/pdftotext_layoutの明示name/version/parametersの宣言schemaだけを確認する。未知profile/versionはunknown。implementation名/版/SHAは申告で、実行/バイナリ照合しない。

reportはformat_support、declared_artifact_bytes、transport_source_binding、profile_declarationを分ける。mismatch優先、欠損はunknown、完全一致のみ宣言整合のmatched。既知schema不正はValueError（CLIexit2）、mismatchはexit1、監査完了matched/unknownはexit0。native例外はgeneric field labelへ変換し、URL/header/error/tokenを含む生のparse/timestamp例外を外へ出さない。旧modeのerror contractは変更しない。

ID導出・抽出replay・citation byte/semantic・発行元真正性・金融意味/採用・現在取得許可・DBfirst-saveは全てnot_performed。原rawからoutputを再現していないため、出力一致を抽出の正しさへ昇格させない。時刻はcallerの記録の内部整合で、公表時刻/独立した実取得証明ではない。ファイルは監査中不変と仮定し、OSfdのrace対策まで広げない。

## 再利用と後続の境界

既存同fileの_relative/_artifact/_comparison/_hash/_shaを再利用する。native必須field guardを先に置き、Noneを許すlegacy helperの挙動を変えない。modelsのparse_json/json_text/validate_source/timestampも既存のまま。新しいregistry・schema依存・collectorは不要。

8gapのうちformat/paths/pointer/success times/保存bytesと結果分離を扱う。profileは宣言のみ、raw→projection変換・ID/履歴移行・収集policy判定は未実装として残す。旧Anritsu captureへversionを後付けしたり旧source/IDを変えたりしない。新producerが意図してnativeformatを出すときだけ用いる案であり、現sourceのunknownを今回matchedへ変更する作業ではない。

受入はJSONの14群へ限定。CRLF、empty/nested/escaped pointer、duplicate/nonfinite、型誤り、欠損と0、byte/field不一致、時刻offset同instant、failedcapture、pathescape未読、profile未replay、SECRET URL/header/error/日時の漏洩なし、legacy9tests＋旧3例のunknown/unknown/matched不変、GET/DB/subprocess/書込なしを確認する予定。まだ実行していない。

[design-v1.json](design-v1.json)に厳密required schemaと合成完全例、API/result、8gap対応、helperと参照SHAを保存。親の設計レビュー後に初めて実装範囲を確定する。この2fileを固定し、production/test/既存研究は変更しない。
