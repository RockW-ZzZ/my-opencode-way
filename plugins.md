# 插件清单

> opencode 通过 `plugin`（V1）/ `plugins`（V2）声明加载第三方插件。插件会注入 Agents / Skills / Commands / MCP / 工具。
> 下表为本机插件状态，`声明处` 指出它在哪个配置文件中被启用。

## 当前启用的插件（2026-10-08 核对）

| 插件 | GitHub 链接 | 声明处 | 当前版本 | opencode 版本要求 | 作用 |
|---|---|---|---|---|---|
| `@tarquinen/opencode-dcp` | https://github.com/Tarquinen/opencode-dynamic-context-pruning | `configs/opencode.json` → `plugins` | 3.2.0（最新） | `@opencode-ai/plugin >=1.18.29`（V1 SDK 最新 1.18.35）；**V2 已实测可用**（V2 缓存已装 3.2.0，加载成功；`./tui` 由 CLI 自动加载） | 动态上下文裁剪（DCP），配合 `dcp.jsonc`；提供 `/dcp`、`/dcp-compress [focus]` |
| `opencode-visual-cache` | https://github.com/Hotakus/opencode-visual-cache | `configs/cli.json` → `plugins`（V2）；`configs/tui.jsonc` → `plugin`（V1） | 1.7.5（最新） | **V1/V2 双支持**（`@opencode-ai/plugin >=1.14.0` 且 `@opencode/plugin >=2.0.0`；V2 SDK 最新 2.0.24） | TUI 视觉缓存：缓存命中率 / token / 成本面板、`/cache-*` 命令、i18n（zh/en/ja/ko）、多币种、余额查询 |

## 已移除的插件（V1 插件 API，V2 不兼容）

| 插件 | GitHub 链接 | 原声明处 | 最后版本 | 移除原因 |
|---|---|---|---|---|
| `oh-my-embedded` | https://github.com/captainluzik/oh-my-embedded | 曾 `configs/opencode.json` → `plugin` | 0.1.1 | opencode **V1** 插件 API（`@opencode-ai/plugin ^1.1.53`）；V2 报 `Plugin must export a default definition with an id and an effect or setup function`。**注**：它注入的 6 Skill / 3 Agent / 5 Command 文件已落盘，删插件不删这些文件，但其 `embedded-*` 工具在 V2 不再可用 |
| `opencode-mnemosyne` | https://github.com/gandazgul/opencode-mnemosyne | 曾 `configs/opencode.json` → `plugin` | 0.2.4（终版） | opencode **V1** 插件 API（`@opencode-ai/plugin ^1.2.24`）；V2 不兼容；已弃用，改名 `opencode-mnemoteca` |
| `opencode-firecrawl` | https://github.com/firecrawl/opencode-firecrawl | 已从 `configs/opencode.json` 移除 | — | **npm 未发布**，需从 GitHub 安装；自动安装始终失败（npm 404）。已弃用 |

## 版本策略

一律安装**最新版**，不指定版本号。config 中以裸名或 `@latest` 声明，opencode 启动时自动解析；手动显式安装见下方「恢复命令」。当前版本核对于 **2026-10-08**。

本机与官方最新版本（2026-10-08）：

| 渠道 | 包名 | 最新 |
|---|---|---|
| opencode **V2**（本机当前） | `@opencode/cli` | **2.0.24**（本机 `opencode --version` = 2.0.24） |
| opencode **V1**（旧版） | `opencode-ai` | **1.18.35** |
| 插件 SDK **V2** | `@opencode/plugin` | **2.0.24** |
| 插件 SDK **V1** | `@opencode-ai/plugin` | **1.18.35** |

- **V2 插件缓存**：`~/.cache/opencode/npm`（Windows：`C:\Users\<用户>\.cache\opencode\npm`）；**V1 插件缓存**：`~/.cache/opencode/packages`。更新插件受 opencode issue #6774 影响（缓存会锁定首次安装的版本），必要时先清缓存再重启。
- `opencode-visual-cache` 在 V2 必须声明在 `~/.config/opencode/cli.json` 的 `plugins` 中（**不要**用 `opencode plugin add`，那会写进 opencode.jsonc 当作 server 插件，导致 `Plugin must export a default definition …` 报错）。首次加入后下次启动 opencode 会自动安装并加载。
- `@tarquinen/opencode-dcp` 的 `./tui` 入口会被 CLI 自动加载，无需重复写进 cli.json。

## 版本监测与兼容性

```powershell
opencode --version        # 本机 opencode（V2 应 ≥2.0.24）
opencode plugin list      # 已加载的 server 插件及版本（--builtin 含内置插件）
opencode plugin check     # 检查插件更新（分 Server / TUI 两个分区）
opencode plugin update    # 更新所有过时插件（可跟 <target>）；改完重启 opencode
```

判断某个插件是否兼容当前 opencode：

```powershell
npm view <插件> version peerDependencies dependencies
```

- 声明 **`@opencode/plugin`**（V2 SDK）→ 支持 **V2**；
- 只声明 **`@opencode-ai/plugin`**（V1 SDK，常写在 `dependencies` 里）→ 按 **V1** 设计，
  **在 V2 不一定可用，必须实测**：
  - ✅ 可用：`@tarquinen/opencode-dcp` 3.2.0（只声明 V1 SDK，V2 实测正常加载）；
  - ❌ 不可用：`oh-my-embedded`、`opencode-mnemosyne` —— V2 启动报
    `Plugin must export a default definition with an id and an effect or setup function`。

⚠️ 已知坑：

- **缓存锁定**（opencode issue #6774）：插件缓存会锁定首次安装的版本，`plugin update` 后版本没变时，
  先删缓存再重启 —— V2 缓存 `~/.cache/opencode/npm`，V1 缓存 `~/.cache/opencode/packages`。
- **`plugin check` 的 TUI 分区可能报 `check failed`**：本机 `opencode-visual-cache` 即如此
  （该包只在 V1 `packages` 缓存中，未出现在 V2 `npm` 缓存）；server 插件（dcp）显示 `(current)` 正常。
- **`opencode plugin add` 会把插件写进全局 server 配置**（`opencode.json` → `plugins`），
  **CLI/TUI 插件（如 visual-cache）不要用它**，必须手写进 `cli.json` 的 `plugins`。

## 手动 Skill（非插件）

`image-gen`（`skills/image-gen/`）为手动安装的 Skill，不通过插件注入。来源：
https://gitee.com/xinze_1/codex-image-skill-api-key.git（本仓库 `skills/image-gen/` 为该仓库的离线备份）。

## 恢复命令

```powershell
# opencode 2.0.24（当前）：在 config 中声明后重启 opencode，自动安装到 ~/.cache/opencode/npm
#   opencode.json → plugins: ["@tarquinen/opencode-dcp@latest"]
#   cli.json      → plugins: [{ "package": "opencode-visual-cache@latest", "options": { "enabled": true } }]

# 手动显式安装（可选，均为最新版）：
npm i -D "@tarquinen/opencode-dcp" opencode-visual-cache
```

> `oh-my-embedded` / `opencode-mnemosyne` 因 V2 不兼容已不再安装；`opencode-firecrawl` 已弃用。
