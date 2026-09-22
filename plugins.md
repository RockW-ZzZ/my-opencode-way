# 插件清单

> opencode 通过 `plugin` 声明加载第三方插件。插件会注入 Agents / Skills / Commands / MCP / 工具。
> 下表为本机已安装插件，`声明处` 指出它在哪个配置文件中被启用。

| 插件 | GitHub 链接 | 声明处 | 当前版本 | opencode 版本要求 | 作用 |
|---|---|---|---|---|---|
| `oh-my-embedded` | https://github.com/captainluzik/oh-my-embedded | `configs/opencode.json` → `plugin` | 0.1.1 | opencode **V1**（`@opencode-ai/plugin ^1.1.53`）；V2 不兼容（V1 插件 API） | 嵌入式/电子工程全家桶：6 个 Skill + 3 个 Agent + 5 个 Command + MCP 工具与 embedded-* 工具 |
| `opencode-firecrawl` | https://github.com/firecrawl/opencode-firecrawl | 已从 `configs/opencode.json` 移除 | — | — | 网页抓取/搜索（Firecrawl）；**npm 未发布**，需从 GitHub 安装，另需全局 `firecrawl-cli`。**已弃用**：2026-09 从配置移除（此前 npm 自动安装始终失败），以下相关内容仅供参考 |
| `opencode-mnemosyne` | https://github.com/gandazgul/opencode-mnemosyne | `configs/opencode.json` → `plugin` | 0.2.4（终版） | opencode **V1**（`@opencode-ai/plugin ^1.2.24`）；V2 不兼容 | 长期记忆（memory 存取工具）；已弃用，改名为 `opencode-mnemoteca` |
| `@tarquinen/opencode-dcp` | https://github.com/Opencode-DCP/opencode-dynamic-context-pruning | `configs/opencode.json` 与 `configs/tui.jsonc` → `plugin` | 3.2.0 | `@opencode-ai/plugin >=1.18.29`（V1 API + TUI 扩展，opentui）；活跃维护（3.2.0 发布于 2026-09-20），V2 兼容待验证 | 动态上下文裁剪（DCP），配合 `dcp.jsonc` 使用 |
| `opencode-visual-cache` | https://github.com/Hotakus/opencode-visual-cache | `configs/tui.jsonc` → `plugin` | 1.7.1 | **V1/V2 双支持**（`@opencode-ai/plugin >=1.14.0` 且 `@opencode/plugin >=2.0.0`，另有历史 `-oc2` 专版构建） | TUI 视觉缓存；⚠️ 2026-09-22 记录：显示有问题 |

## 版本策略

一律安装**最新版**，不指定版本号。config 中以裸名或 `@latest` 声明，opencode 启动时自动解析；手动显式安装见下方「恢复命令」。当前版本核对于 2026-09-22。

- `opencode-firecrawl`（已弃用，仅供参考）：未发布到 npm：从 GitHub main 分支源码 tarball 安装（无需本机 git，始终最新），安装后目录名为 `node_modules/opencode-firecrawl`，与 config 中裸名声明匹配。
- `opencode-mnemosyne` 已弃用，npm 提示改名为 `opencode-mnemoteca`。config 继续声明旧名则按旧名安装最新版（终版 0.2.4）；若迁移新版需同步修改 config 中的插件名。

## 手动 Skill（非插件）

`image-gen`（`skills/image-gen/`）为手动安装的 Skill，不通过插件注入。来源：
https://gitee.com/xinze_1/codex-image-skill-api-key.git（本仓库 `skills/image-gen/` 为该仓库的离线备份）。

## 恢复命令

```powershell
# 在全局 opencode 目录声明 plugin 后，opencode 自动解析；手动显式安装（可选，均为最新版）：
npm i -D oh-my-embedded opencode-mnemosyne "@tarquinen/opencode-dcp" opencode-visual-cache

# firecrawl 已弃用并从配置移除（npm 未发布，自动安装失败）；以下命令仅供参考：
# 从 GitHub main 分支源码安装（无需本机 git，始终最新）：
npm i -D "opencode-firecrawl@https://codeload.github.com/firecrawl/opencode-firecrawl/tar.gz/refs/heads/main"

# firecrawl 插件的外部 CLI（必须）：
npm i -g firecrawl-cli
```
