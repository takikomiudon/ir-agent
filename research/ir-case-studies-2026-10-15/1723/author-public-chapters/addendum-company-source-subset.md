# 1723 company source subset：限定追補

**1723-SOURCE-CONTRACT-01は、新しい会社source専用bundleに限って解消を確認した。** entry・overview・risksという**1723の3sources**は、元のsource objectと完全一致し、既存`validate_source`の戻り値も全objectで一致する。新bundle SHAは`4788d1576a80bffdf91cedc764e5d1ee09fa13fae4201da50650406170eab6cc`。

`company_id:null`のglobal tos行は旧bundleと原文・引用の参照として保持され、新bundleには含まれない。1723固有契約・報酬を補完していない。旧bundleをそのままingestすると当該行が拒否される事実と、最初の独立finding/historyは変わらない。新subsetで当該構造不適合を避けたという解消であり、旧bundleの無条件passではない。

新準備3ファイル、旧31入力、最初の独立レビューJSON/MDが不変であることを確認した。原capture/意味点検は前回の限定結果を参照し、再監査していない。実DB保存・金融採用・意味の追加認定ではない。GET、DB、コード、旧ファイル、IR、索引・監視の変更は0。ここで有限終了。
