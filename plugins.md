# 插件清单

> opencode 通过 `plugin` 声明加载第三方插件。插件会注入 Agents / Skills / Commands / MCP / 工具。
> 下表为本机已安装插件，`声明处` 指出它在哪个配置文件中被启用。

| 插件 | 版本 | GitHub 链接 | 声明处 | 作用 |
|---|---|---|---|---|
| `oh-my-embedded` | 0.1.1 | https://github.com/captainluzik/oh-my-embedded | `configs/opencode.json` → `plugin` | 嵌入式/电子工程全家桶：6 个 Skill + 3 个 Agent + 5 个 Command + MCP 工具与 embedded-* 工具 |
| `opencode-firecrawl` | 0.2.4 | https://github.com/firecrawl/opencode-firecrawl | `configs/opencode.json` → `plugin` | 网页抓取/搜索（Firecrawl） |
| `opencode-mnemosyne` | 3.1.15 | https://github.com/gandazgul/opencode-mnemosyne | `configs/opencode.json` → `plugin` | 长期记忆（memory 存取工具） |
| `@tarquinen/opencode-dcp` | 1.6.5 | https://github.com/Opencode-DCP/opencode-dynamic-context-pruning | `configs/opencode.json` 与 `configs/tui.jsonc` → `plugin` | 动态上下文裁剪（DCP），配合 `dcp.jsonc` 使用 |
| `opencode-visual-cache` | 1.6.5 | https://github.com/Hotakus/opencode-visual-cache | `configs/tui.jsonc` → `plugin` | TUI 视觉缓存 |

## 版本来源

以上版本为当前机器 node_modules / npm registry 解析结果，写入 config 时建议用 `@latest` 或固定 `@x.y.z`。

## 手动 Skill（非插件）

`image-gen`（`skills/image-gen/`）为手动安装的 Skill，不通过插件注入。来源：
https://gitee.com/xinze_1/codex-image-skill-api-key.git（本仓库 `skills/image-gen/` 为该仓库的离线备份）。

## 恢复命令

```powershell
# 在全局 opencode 目录声明 plugin 后，opencode 自动解析；手动显式安装（可选）：
npm i -D oh-my-embedded@0.1.1 opencode-firecrawl@0.2.4 opencode-mnemosyne@3.1.15 @tarquinen/opencode-dcp@1.6.5 opencode-visual-cache@1.6.5
```
