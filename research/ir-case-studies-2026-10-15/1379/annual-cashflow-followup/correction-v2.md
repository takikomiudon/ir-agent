# 1379年次資料導線：引用位置のみの訂正v2

`link-provenance.json`の`links[0]`にあるliteral `tanshin.js`の位置を、[link-provenance-v2.json](link-provenance-v2.json)で **40609:40672 → 40666:40729**（終端exclusive）へ訂正した。他のJSON値は完全一致で、旧ファイルの完全bytesは保持している。

基準は保存原rawをUTF-8 strict decodeした文字列のUnicode code point位置であり、CRLFを維持する。元raw・公式索引`../02.txt`のbytesを同じ方法でdecodeした文字列・`../02.json.text`は全体一致し、3つを独立に検索して同じ40666:40729が得られた。literalは各文字列に1回。原raw SHAは`eb4b6f13a01a95d4050bcafbaf6dd0a28f02856fa36a3bd83ef187a63a400393`、元snapshot SHAは`aad2f890e1abc9684afbbce6227503bca6857494f28700dd546f2dc8c00caac4`。

原文ではliteralより前に57組のCRLFがある。CRLFをLFへ置換した別文字列では旧開始40609が再現するが、これは保存原raw/snapshot本文とは異なるoffset基準である。元の誤記作成過程までは独立確認していない。原rawや本文をLFへ書き換えず、v2の位置だけを保存本文に合わせた。

リンク先、scriptの静的feed参照、会社コード、財務値、robots禁止判断、feed/PDF未要求という結論は変更しない。`ssl4.eir-parts.net`の既知停止は維持し、年次PDF URL/CF本文・税/利息/設備/WC/CB条件は未確認のまま。この訂正は年次CFの不足を解消せず、金融入力/モデルへの採用でもない。

[validation-v2.json](validation-v2.json)へ実確認時計・3表現の位置・根拠SHA・旧ファイル不変・変更path限定を保存した。GET/DB/code/tests/経路再探索は0。新規3ファイルだけを固定し、以後編集しない。
