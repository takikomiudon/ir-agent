# 保存済み構造化source 23件の一括接続preflight

索引v23の26entry/101factを既存台帳と読取照合し、**23件/91factの派生sourceだけ**を新規保存候補にした。5988の財政状態3factは既に同snapshotで保存済み、8331/9702は既存会社・原sourceがなく対象外。投資候補の再選定・金融入力採用ではない。

[候補manifest](candidate-manifest.json)に全26entry、artifact SHA、会社snapshot SHA、原典の完全一致、派生sourceの有無、候補/除外理由を保持した。既存22候補のread-only-preflight/reproductionと、新annual BPSのparent-acceptanceを、現在のbundle bytes/原snapshot SHAの一致で再利用した。候補23件すべて既存の`reproduced`記録へ結び付き、新解析・normalization・新規の原文再検証は0。元索引・producer artifactは変更していない。

[実適用用候補bundle](derived-only-import-bundle.json)は元の派生snapshotをそのまま23件収録し、companies/thesesは空。原sourceや会社情報を再投入しない。元のretrieved_at、値、引用、年度、著者、`financial_inputs_verified:false`、意味レビューが必要という宣言を保持した。SHAのsnapshotは既存`models.json_text`によるUTF-8全JSON SHA、artifact SHAは保存file bytes SHAであり別domainである。

[一時DB検証](temp-preflight.json)では、実DBを`mode=ro`・`query_only`・一貫read transactionで開き、SQLite backup APIで一時コピーを作成した。Store/Harnessはこの一時コピーにだけ使用した。

- 既存Store初期化で27tableの既存全行・table集合は不変。
- sourcesだけのHarness.ingestで23件追加、125→148。再ingestは追加0件、全table論理行が初回後と完全同値。
- 全27tableの旧行を完全保持。25tableは全行完全一致、残るsources/record_availabilityも23新行の追加だけ。分類・jobs・native case・policy等のAPIは呼んでいない。
- 新receiptは一時DBのtrusted初回保存時刻・元snapshot SHAに一致。これは実台帳の初回保存証跡ではない。一時DBは検証後削除した。

実DB本体SHAは前後とも`b0086b397a8a949e0616f5923cb183358d87b30f3b8a05bfe6fc0373af443e88`。WALは前後とも0bytesのSHAで不変。実台帳は125sourceのまま。実適用・分類job・分類完了はrootの後段であり、このpreflightでは実行していない。実適用前には現在の会社/原source/派生sourceの有無を再照合し、実保存時刻はその実行時点のものを使う。過去のretrieved_atや一時receiptへ遡らせない。

新GET・実DB書込み・native case変更・政策/金融採用・src/tests変更・既存artifact変更は0。この検証で金融意味、予測の最新性、公正倍率、目標株価、売買条件を認定していない。
