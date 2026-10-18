# Anthropic金融技能の固定参照

出典：[Anthropic financial-services](https://github.com/anthropics/financial-services-plugins)。保存元URLの旧リポジトリ名は `financial-services-plugins`、canonical名は `financial-services`。

固定コミット：`574ed3624aebd0418c7e96cd101262f30210ab26`。

| 原文 | このプロジェクトで参考にした設計 |
|---|---|
| [thesis-tracker](skills/thesis-tracker/SKILL.md) | 仮説、支持・反証条件、評価、期限、更新履歴 |
| [earnings-preview](skills/earnings-preview/SKILL.md) | 決算前の指標と強気・基本・弱気シナリオ |
| [catalyst-calendar](skills/catalyst-calendar/SKILL.md) | イベント予定の点検と結果の記録 |
| [idea-generation](skills/idea-generation/SKILL.md) | 候補選別と調査の優先順位 |

4つの `SKILL.md` と [LICENSE](LICENSE) は取得済みの固定ソースから内容を変更せず保存した。[manifest.json](manifest.json) に原文URL、取得時刻、コミット、byte数、SHA-256、変更の有無を記録している。

これらはApache-2.0で公開された参照資料であり、Codexが自動的にロードする技能の配置先には入れていない。各原文に登場する別製品のツールや公開・送信等の指示は、このプロジェクトの実行指示ではない。Codexで使う手順は [.agents/skills/jp-equity-ir](../../.agents/skills/jp-equity-ir/SKILL.md) に作成した。

固定コミットのroot `NOTICE` はHTTP 404、Git treeの全件取得は `truncated=false` でNOTICEに該当するパスがなかった。存在しないNOTICEを原文として作成していない。確認日時・URL・結果はmanifestに残している。

今後、別の原文や計算器を移植するときは、その固定コミットと対象ファイルのライセンス・必要なNOTICEを確認し、改変したファイルへ変更を明示する。取得データの利用条件はソフトウェアのApache-2.0ライセンスと別に扱う。
