# 1723 Envalith入口の有限確認

旧公式200snapshotの `$.links[63].url` にある保存resolved URLを根拠に、robots1GETと会社入口1GETを実施しました。両方HTTP200、入口564,485 bytesの完全取得です。元のissuer snapshotにhref/rawHTMLはなく、literal hrefとは呼びません。今回の外部入口HTML取得も旧issuer HTML欠損を回復しません。

robotsは指定会社pathを禁止せず、固定UAに対するAI個別制限も確認されませんでした。中央7hold非該当、UA Codex-IR-Research/0.1、継承CA/TLSverify、40秒/10MiB、redirect/retry/診断なしを維持。GETは計2で停止し、PDF/別章/JS/APIは0です。

入口には財務サマリー・参考指標・最新レポート4件の要約が静的表示されています。27.3期1Qの決算速報7/24 18:55 JST、決算プレビュー7/22 15:30 JST、26.3期通期の説明会速報5/27 20:40 JST、決算速報5/7 17:45 JSTです。表示に年がないため補完せず、入口全体の更新時刻とも扱いません。

レポートcardはbuttonで、本体へのliteral PDF/HTML hrefは確認できませんでした。静的a[href]として企業概要・セグメント・事業等リスク・ガバナンス/ESG・会社情報・開示の章URLをinventoryしましたが、追加取得はしていません。

別のPDF a要素4本はTOPIX/売出し等の「最近の開示」で、調査レポートPDFとは区別しています。これらは期限付き署名queryを含むため、派生一覧ではquery値を再掲せず、元rawの正確なhref位置/SHAで保持しました。queryを取り除いた表示pathは取得用URLではありません。

個別調査レポート本文、作者正式名・個人名、報酬関係、独自予測、方法・価格式は未確認/nullです。入口ラベル、要約や参考PER等を独立予測や公正倍率にしません。免責事項は閉じた表示で、未表示部分の不存在や無報酬を主張しません。

原raw・robots/visible text・capture/guard/旧route・静的linkとreport inventory・sourcebundle・validationを新dir内に保存し固定しました。sourceは研究保存のみでDBへ未登録。親membershipはその観測時点のsource/thesis/question0等の参照で、この作業ではDBを開いていません。individual not_statedは未記載であり拒否/適格確認ではありません。DB/index/監視/旧file/code/金融採用/IRは0です。
