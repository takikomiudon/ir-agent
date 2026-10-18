# 141A 資料入口の独立確認

保存ファイルだけの有限確認で、修正を要する具体的不一致は見つかりませんでした。新GET・API・Store起動・実DB操作は0です。

2応答のraw SHA/byte数、個別snapshotとcapture、HTMLからの本文・title・実anchor再抽出、3引用のoffset/SHAを照合しました。入口は169 anchors・PDF href 0・`__NEXT_DATA__.props.pageProps={}`を再現し、頁専用chunkは未取得です。最大3GETのうち2GETで停止し、残1GETを使っていません。金融本文と公開事業Q&Aはこの限定経路では未取得です。

robotsは404のHTMLで、規則本文や明示的許可が得られた応答ではありません。記録上の2要求は同じ`trial-holdings.inc`に限られ、中央7 exact hostの保留と一致せず、保留hostへの要求や別hostによる迂回は記録されていません。固定UAとprepared headerは一致しますが、wire headerの独立証明ではありません。

旧FAQの`links[82]`と旧トップの`links[74]`が入口への実リンクであることを照合しました。トップの「2026年08月12日 2026年6月期 第4四半期 決算説明会」は入口案内であり、本文の対象期・実施・現在最新の証拠にはしていません。正式本文が会社に存在しない／非公表という結論も出していません。

sourceは`validate_source`で不変、共通stable IDと`json_text` SHA **8b196213df90784b23559f7888665582344c8891e84162eec29ec5e66708a404**を再現しました。retrieved_atは入口本文完了13:51:18.683333UTC、published_atはnullです。保存rawはgzip等のデコード後の応答entity bytesで、wire bytesやContent-Lengthと同義ではありません。

`index_only / financial_content:false`、未importのwatch/held:falseをmetadataとする扱い、モデル未採用は適切です。保有申告・会社実績/予想・著者独自予測・旧著者条件の成否をこのbodyで補っていません。汎用verifier互換はunknownを維持します。

[詳細記録](independent-recheck.json)に各SHA・時刻・引用位置と限界を保存しました。旧本体12ファイルと参照6ファイルは終了時も記録SHAと一致しています。
