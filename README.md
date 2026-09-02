# my-opencode-way

> opencode 生产力环境恢复手册。记录本机安装的**插件、Skills、Agents、Commands、MCP**及外部依赖，
> 不含任何 API Key，方便在其它电脑/新机快速恢复。API Key / `auth.json` 不入库；
> 自定义供应商的**模型能力参数**（输入输出类型、上下文、是否推理）见 `models.md`，恢复时需自动补全。

本仓库为 git 仓库（`main` 分支），无远端；内容需自行提交/推送到你的私有远端。

## 目录结构

```
my-opencode-way/
├── README.md                     # 本文件：总览 + 恢复步骤
├── plugins.md                    # 插件清单与版本
├── skills.md                     # Skill / Agent / Command / MCP 说明
├── tools.md                      # 外部系统依赖（需自行安装）
├── models.md                     # 自定义供应商模型参数：恢复时自动检测并补全
├── configs/                      # 全局配置（已脱敏，无 Key）
│   ├── opencode.json             # 全局：插件清单
│   ├── tui.jsonc                 # TUI 插件
│   ├── dcp.jsonc                 # 动态上下文裁剪（DCP）配置
│   └── .gitignore
└── skills/
    └── image-gen/                # 手动安装的图片/视频生成 Skill（.env 已去除，见 .env.example）
```

## 一键恢复步骤（新机）

1. **安装 opencode 本体**
   ```powershell
   npm i -g opencode-ai@latest     # 或按官方文档安装
   ```
2. **放置全局配置**
   - 把 `configs/` 下三个文件（`opencode.json`、`tui.jsonc`、`dcp.jsonc`）
     复制到本机全局目录（Linux/macOS：`~/.config/opencode/`；Windows：`%USERPROFILE%\.config\opencode\`）。
   - 复制 `.gitignore` 可选（用于 node_modules 忽略）。
3. **就位技能（Skill）**
   - 把 `skills/image-gen/` 放入全局目录 `skills/` 下，并将其 `.env.example` 复制为 `.env`，
     填入 `OPENAI_API_KEY`（可留 `IMAGE_GEN_BASE_URL` 默认值）。
4. **安装外部系统依赖**（oh-my-embedded 的若干 Skill 依赖外部程序），见 `tools.md`。
5. **启动 opencode**，插件即被自动加载：
   - `oh-my-embedded` 会生成 6 个 Skill / 3 个 Agent / 5 个 Command / 若干 MCP 配置；
   - `image-gen` 为手动 Skill，随 `skills/` 目录生效。
6. **接入自定义供应商后，补全模型参数**（必须）：
   - 自行在 opencode 内配置 provider / Key（`auth.json` 不入库）。
   - 然后扫描全局 `opencode.jsonc` 里 `provider.*.models` 的全部模型 ID。
   - 用 [models.dev](https://models.dev/api.json)（未命中再查厂商文档）写入：
     `modalities`（输入输出类型）、`limit.context` / `limit.output`（上下文与最大输出）、`reasoning`（是否支持推理）。
   - 字段必须符合 schema，详见 `models.md`。改完后**重启 opencode**。

## 本机环境清单（Windows）

- opencode 全局目录：`C:\Users\zcj12\.config\opencode`
- Skill 目录：`...\config\opencode\skills\`

## 插件与版本

详见 `plugins.md`。快速安装命令：

```powershell
# 已在 opencode.json / tui.jsonc 中声明，重启 opencode 自动解析；手动安装均为最新版
npm i -D oh-my-embedded opencode-mnemosyne "@tarquinen/opencode-dcp" opencode-visual-cache "opencode-firecrawl@https://codeload.github.com/firecrawl/opencode-firecrawl/tar.gz/refs/heads/main"
npm i -g firecrawl-cli   # firecrawl 插件的外部 CLI（必须）
```

## 注意事项

- **严禁把任何 Key / Token / 密钥提交进本仓库**；`skills/image-gen/.env.example` 只提供占位符。
- 自定义供应商模型默认只有 `name`，不补 `modalities` / `limit` / `reasoning` 则无法按官方能力使用多模态、长上下文和推理。
- 模型对象禁止未知字段：不要写 `context_length`、`max_output_tokens`，不要把输入类型写成 `"file"`（用 `"pdf"`）。
- opencode 配置在启动时一次性加载，**改动后需退出并重启 opencode** 才生效。
