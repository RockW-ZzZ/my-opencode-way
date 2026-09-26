# 插件清单

> opencode 通过 `plugin`（V1）/ `plugins`（V2）声明加载第三方插件。插件会注入 Agents / Skills / Commands / MCP / 工具。
> 下表为本机插件状态，`声明处` 指出它在哪个配置文件中被启用。

## 当前启用的插件（2026-09-26 核对）

| 插件 | GitHub 链接 | 声明处 | 当前版本 | opencode 版本要求 | 作用 |
|---|---|---|---|---|---|
| `@tarquinen/opencode-dcp` | https://github.com/Tarquinen/opencode-dynamic-context-pruning | `configs/opencode.json` → `plugin` | 3.2.0 | `@opencode-ai/plugin >=1.18.29`；**V2 已实测可用**（V2 缓存已装 3.2.0，加载成功；`./tui` 由 CLI 自动加载） | 动态上下文裁剪（DCP），配合 `dcp.jsonc`；提供 `/dcp`、`/dcp-compress [focus]` |
| `opencode-visual-cache` | https://github.com/Hotakus/opencode-visual-cache | `configs/cli.json` → `plugins`（V2）；`configs/tui.jsonc` → `plugin`（V1） | 1.7.4 | **V1/V2 双支持**（`@opencode-ai/plugin >=1.14.0` 且 `@opencode/plugin >=2.0.0`） | TUI 视觉缓存：缓存命中率 / token / 成本面板、`/cache-*` 命令、i18n（zh/en/ja/ko）、多币种、余额查询 |

## 已移除的插件（V1 插件 API，V2 不兼容）

| 插件 | GitHub 链接 | 原声明处 | 最后版本 | 移除原因 |
|---|---|---|---|---|
| `oh-my-embedded` | https://github.com/captainluzik/oh-my-embedded | 曾 `configs/opencode.json` → `plugin` | 0.1.1 | opencode **V1** 插件 API（`@opencode-ai/plugin ^1.1.53`）；V2 报 `Plugin must export a default definition with an id and an effect or setup function`。**注**：它注入的 6 Skill / 3 Agent / 5 Command 文件已落盘，删插件不删这些文件，但其 `embedded-*` 工具在 V2 不再可用 |
| `opencode-mnemosyne` | https://github.com/gandazgul/opencode-mnemosyne | 曾 `configs/opencode.json` → `plugin` | 0.2.4（终版） | opencode **V1** 插件 API（`@opencode-ai/plugin ^1.2.24`）；V2 不兼容；已弃用，改名 `opencode-mnemoteca` |
| `opencode-firecrawl` | https://github.com/firecrawl/opencode-firecrawl | 已从 `configs/opencode.json` 移除 | — | **npm 未发布**，需从 GitHub 安装；自动安装始终失败（npm 404）。已弃用 |

## 版本策略

一律安装**最新版**，不指定版本号。config 中以裸名或 `@latest` 声明，opencode 启动时自动解析；手动显式安装见下方「恢复命令」。当前版本核对于 2026-09-26。

- **V2 插件缓存**：`~/.cache/opencode/npm`（Windows：`C:\Users\<用户>\.cache\opencode\npm`）；**V1 插件缓存**：`~/.cache/opencode/packages`。更新插件受 opencode issue #6774 影响（缓存会锁定首次安装的版本），必要时先清缓存再重启。
- `opencode-visual-cache` 在 V2 必须声明在 `~/.config/opencode/cli.json` 的 `plugins` 中（**不要**用 `opencode plugin add`，那会写进 opencode.jsonc 当作 server 插件，导致 `Plugin must export a default definition …` 报错）。首次加入后下次启动 opencode 会自动安装并加载。
- `@tarquinen/opencode-dcp` 的 `./tui` 入口会被 CLI 自动加载，无需重复写进 cli.json。

## 手动 Skill（非插件）

`image-gen`（`skills/image-gen/`）为手动安装的 Skill，不通过插件注入。来源：
https://gitee.com/xinze_1/codex-image-skill-api-key.git（本仓库 `skills/image-gen/` 为该仓库的离线备份）。

## 恢复命令

```powershell
# opencode 2.x（当前）：在 config 中声明后重启 opencode，自动安装到 ~/.cache/opencode/npm
#   opencode.json → plugin: ["@tarquinen/opencode-dcp@latest"]
#   cli.json      → plugins: [{ "package": "opencode-visual-cache@latest", "options": { "enabled": true } }]

# 手动显式安装（可选，均为最新版）：
npm i -D "@tarquinen/opencode-dcp" opencode-visual-cache
```

> `oh-my-embedded` / `opencode-mnemosyne` 因 V2 不兼容已不再安装；`opencode-firecrawl` 已弃用。
