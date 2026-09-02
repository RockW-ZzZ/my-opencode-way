# 插件清单

> opencode 通过 `plugin` 声明加载第三方插件。插件会注入 Agents / Skills / Commands / MCP / 工具。
> 下表为本机已安装插件，`声明处` 指出它在哪个配置文件中被启用。

| 插件 | GitHub 链接 | 声明处 | 作用 |
|---|---|---|---|
| `oh-my-embedded` | https://github.com/captainluzik/oh-my-embedded | `configs/opencode.json` → `plugin` | 嵌入式/电子工程全家桶：6 个 Skill + 3 个 Agent + 5 个 Command + MCP 工具与 embedded-* 工具 |
| `opencode-firecrawl` | https://github.com/firecrawl/opencode-firecrawl | `configs/opencode.json` → `plugin` | 网页抓取/搜索（Firecrawl）；**npm 未发布**，需从 GitHub 安装，另需全局 `firecrawl-cli` |
| `opencode-mnemosyne` | https://github.com/gandazgul/opencode-mnemosyne | `configs/opencode.json` → `plugin` | 长期记忆（memory 存取工具）；已弃用，改名为 `opencode-mnemoteca` |
| `@tarquinen/opencode-dcp` | https://github.com/Opencode-DCP/opencode-dynamic-context-pruning | `configs/opencode.json` 与 `configs/tui.jsonc` → `plugin` | 动态上下文裁剪（DCP），配合 `dcp.jsonc` 使用 |
| `opencode-visual-cache` | https://github.com/Hotakus/opencode-visual-cache | `configs/tui.jsonc` → `plugin` | TUI 视觉缓存 |

## 版本策略

一律安装**最新版**，不指定版本号。config 中以裸名或 `@latest` 声明，opencode 启动时自动解析；手动显式安装见下方「恢复命令」。

- `opencode-firecrawl` 未发布到 npm：从 GitHub main 分支源码 tarball 安装（无需本机 git，始终最新），安装后目录名为 `node_modules/opencode-firecrawl`，与 config 中裸名声明匹配。
- `opencode-mnemosyne` 已弃用，npm 提示改名为 `opencode-mnemoteca`。config 继续声明旧名则按旧名安装最新版（终版 0.2.4）；若迁移新版需同步修改 config 中的插件名。

## 手动 Skill（非插件）

`image-gen`（`skills/image-gen/`）为手动安装的 Skill，不通过插件注入。来源：
https://gitee.com/xinze_1/codex-image-skill-api-key.git（本仓库 `skills/image-gen/` 为该仓库的离线备份）。

## 恢复命令

```powershell
# 在全局 opencode 目录声明 plugin 后，opencode 自动解析；手动显式安装（可选，均为最新版）：
npm i -D oh-my-embedded opencode-mnemosyne "@tarquinen/opencode-dcp" opencode-visual-cache

# firecrawl 未发布到 npm，从 GitHub main 分支源码安装（无需本机 git，始终最新）：
npm i -D "opencode-firecrawl@https://codeload.github.com/firecrawl/opencode-firecrawl/tar.gz/refs/heads/main"

# firecrawl 插件的外部 CLI（必须）：
npm i -g firecrawl-cli
```
