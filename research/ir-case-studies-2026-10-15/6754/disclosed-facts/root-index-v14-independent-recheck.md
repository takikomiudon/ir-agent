# 公表値索引v14の独立確認

指定SHA `43f7635995ee35bb77c39895a4c728bc68ec638df4a2ce98157d8808ecb0628e`を確認し、不一致0で固定しました。

- v13の**17 entries・75 factsはJSON値として完全不変**です。
- 6754の1 entry・7 factsだけが追加され、正規化bundleと一致します。内訳は実績3・会社予想4で、独立予測の増加は0です。
- v14全体は**18 entries・82 facts・15社・17社/原典組合せ**。全82 recordでper-fact overrideを優先し、artifact SHA、派生source/会社、fact各欄、原典参照を解決しました。

6754の既存独立正規化レビューを再利用しました。raw・画像・数値の全再監査、再計算、normalizer再実行はしていません。期間・表示丸め・セグメント/連結の区別、受注≠売上/利益、会社予想≠独立予測を維持しています。

金融入力未検証・モデル未採用・thesis/送信0、派生未importの記録は保持されています。実DBの現在状態を照会した主張ではありません。旧索引と全参照artifactのSHAは終了時も一致しました。

[詳細記録](root-index-v14-independent-recheck.json)に全18 entry/82 recordの解決先とSHAを保存しました。GET・API・Store/DB起動・code・旧file変更は0です。
