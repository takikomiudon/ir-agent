# 国内peer表の表示平均再現（保存p7だけ）

既存11頁全文の物理/印字p7を本文と既存画像で確認した。旧quotes[9]の短い引用に原表数字が含まれなかったことと、原PDF/全文が未保存であることは異なる。今回は保存済み表を新purposeで抽出しただけで、旧EPS候補同定・取消票や閉鎖した取得経路は再開していない。

画像の列は「PER12か月フォワード(倍)」。国内peerは掲載順に1431/3465/8904/8917/2981/8860/1419/3291/3288/1911で、表示値は144.2/4.7/18.8/10.8/6.6/6.1/21.0/8.2/6.5/8.2倍。2983の対象行6.1倍は別行として保持し、10社平均に加えていない。資料出所はFactSet/Bloomberg/Astrisの原日本語表記をfooter引用で固定した。個別観測時刻やforward EPSのprovider/vintage/rolling方法は表内に記載が見当たらず未確定で、表紙公表日2026-10-01を各セルの観測日時と認定しない。

10個の表示tokenをDecimalでそのまま合計すると235.1、単純meanは23.51倍。こちらで小数1桁へROUND_HALF_UPした23.5倍は著者表示と一致した。これは掲載丸め値から単純meanで表示を再現できたという結果で、著者が未丸めの値にどの平均/丸め処理を適用したかを証明しない。144.2倍は他の9社の表示値より大きいまま保持し、除外・上限・trimは0。任意の記述統計として同じ10表示値のmedian8.2倍も記録したが、採用倍率を選ぶ操作ではない。

table.jsonは原bundle/source IDとnative snapshot SHA、全文/raw/画像SHA、ヘッダ/国内10行/対象1行/平均/出所の逐語14引用にUnicode・UTF8半開offsetを保持する。各11PER tokenにも原全文上の個別位置を付けた。原source全objectは既存actual-author-import/source-only-bundleと一致し、既存actual-importのtrusted receiptのsnapshot SHA b48276389faeaa754fcdf84b8e7f4296303619c97dab947ef7fa96ad3cec63c9とも一致する。HTTP完了16:42:23.293822と実初回保存17:02:48.778046（いずれも2026-10-15 UTC）を区別した。今回新たにDBへ接続して再認証したものではない。

このcohortは著者が選んだ比較集合で、現在10月の株価や公正PE/target/確率として採用していない。23.5、median8.2、対象行6.1のいずれも会社EPS3期へ掛けず、12か月forwardと特定FY/分割基準・会計範囲の対応を補わない。国内表で作者が比較を示したことと、当方の日本株投資判断を再現できることは別である。海外行は分析対象外。normalizer/新数値fact/索引・金融入力・IR判断は0。

`.venv/bin/python research/ir-case-studies-2026-10-15/2983/domestic-peer-table-reproduction-2026-10-16/reproduce.py`のstdoutは保存table.jsonと全bytes一致した。14引用と11tokenのUnicode/UTF8対応も独立照合済み。script SHA `85c6e45822af3f84ca30496e084a81ffebbbfb1f6146dcf36d4be1fb5ddffdc5`、table SHA `cc6060f5a2f50a4dfdf8f3f6389cad26dcf19367f9dd348f7f20b9286dff9805`。最初のlocal検証ではsnapshot JSONの空白区切りをcompactと誤って仮定しassert停止したため、既存models.json_textの保存契約を読み、空白を含むsort_keys形式へ修正した。値・元sourceは無変更で、再取得やDB処理はない。

GET/DB/Store/既存docs・source変更/金融採用/送信0。table.json・README・小reproduce.pyの3fileだけをfreezeし、root受入待ちで停止する。
