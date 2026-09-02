# Skills / Agents / Commands / MCP

## 一、插件 `oh-my-embedded` 注入（随插件自动生成，无需手工备份）

> 插件仓库（Skills/Agents/Commands 与此表一一对应）：https://github.com/captainluzik/oh-my-embedded

### Skills（6 个，位于 `skills/`）

| Skill | 用途 | 外部依赖 / MCP |
|---|---|---|
| `circuit-simulator` | 电路仿真（ngspice），电源/滤波/阻抗/瞬态分析 | `ngspice`；MCP `spicebridge`（`uvx` 运行） |
| `component-sourcer` | 元器件检索、BOM 优化、替代料 | MCP `jlcpcb`（`npx -y @jlcpcb/mcp`），联网查 JLCPCB/LCSC/Nexar/Octopart |
| `embedded-engineer` | 资深嵌入式工程师：ESP32/STM32/FreeRTOS/RF/电源 | MCP `esp-mcp`（`uv run ~/.local/share/oh-my-embedded/esp-mcp`，Python 3.11） |
| `embedded-review` | 固件代码评审（内存安全/ISR/RTOS/C++ UB，P0–P3 分级） | 无 |
| `firmware-debugger` | GDB + 串口监视器调试（需调试探针） | MCP `gdb`（`mcp-server-gdb`）、`serial`（`serial-mcp-server`） |
| `pcb-designer` | KiCad PCB 设计/布线/DRC/Gerber/JLCPCB BOM | `KiCad`；MCP `kicad`（`node ~/.local/share/oh-my-embedded/kicad-mcp-server/dist/index.js`） |

> 这些 Skill 的 mcpConfig 在各自 `SKILL.md` 的 frontmatter 中（本仓库未复制，可随时重新安装插件生成）。

### Agents（3 个，位于 `agents/`）

| Agent | mode | 用途/工具 |
|---|---|---|
| `embedded` | primary | 固件工程师；`embedded-*`、bash/edit/read/write/glob；color `#00C853`；steps 50 |
| `hardware` | primary | 硬件/PCB 工程师；`embedded-*`、bash/read/write/glob/grep；color `#FF6D00`；steps 50 |
| `review-hw` | subagent | 固件代码评审；read/glob/grep/skill/`embedded-pin-mapper`；color `#D50000`；steps 30 |

### Commands（5 个，位于 `commands/`）

| Command | 用途 |
|---|---|
| `bom` | 从 KiCad 工程提取/分析 BOM |
| `debug` | 用 OpenOCD 或 probe-rs 启动 GDB 调试会话 |
| `flash` | 构建并烧录固件（ESP-IDF 或 PlatformIO） |
| `power-budget` | 计算嵌入式项目功耗预算 |
| `review-firmware` | 对 C/C++ 源码执行结构化固件评审 |

## 二、手动 Skill：`image-gen`（本仓库已备份）

图片/视频生成 Skill，本仓库 `skills/image-gen/` 为完整副本（已去除 `.env`，密钥请自行填写）。

- 来源：https://gitee.com/xinze_1/codex-image-skill-api-key.git（本仓库 `skills/image-gen/` 为该仓库的离线备份）
- 入口（`SKILL.md`）：先询问用「Skill 模型(api.apikey.fun)」还是「本地工具」；
  选 Skill 模型后实时 `GET /v1/models` 发现模型再自动选择。
- 支持：文生图 / 图生图 / 图片编辑 / 视频生成（异步轮询）；图片 `gpt-image-2` / `grok-imagine-image`；
  视频 `grok-imagine-video`（480p/720p）/ `grok-imagine-video-1.5`（1080p）。
- 脚本：`scripts/node/image-gen.js`（Node 18+）、`scripts/python/image_gen.py`（仅标准库）。
- 配置：全局 `~/.config/opencode/skills/image-gen/.env`（`OPENAI_API_KEY`、`IMAGE_GEN_BASE_URL=`https://api.apikey.fun/v1）。

## 三、恢复注意

- `oh-my-embedded` 生成的 Skill/Agent/Command 依赖外部程序/MCP 服务，见 `tools.md`；跨平台路径差异
  （如 `~/.local/share/oh-my-embedded/...`）在 Windows/Linux 需按实际情况调整。
- image-gen 的 `.env` 含 Key，务必使用 `.env.example` 手动填写，**不得提交**。
