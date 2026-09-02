# 外部系统依赖（oh-my-embedded 的 Skill 所需）

> 这些是**系统层面**要预装的程序/运行时；Skill 通过 MCP 或 shell 调用它们。装了并不影响其它 Skill。

## 运行时 / 工具

| 类别 | 程序 | 用途 | 说明 |
|---|---|---|---|
| Python 运行时 | `python3` / `uv` | 运行 esp-mcp、image-gen 的 Python 脚本 | 需 Python 3.11+；建议安装 `uv`（`pip install uv` 或官方脚本） |
| 节点运行时 | `node` / `npx` | 运行 kicad-mcp-server、jlcpcb MCP、image-gen 的 Node 脚本 | Node 18+ |
| 电路仿真 | `ngspice` | `circuit-simulator` 仿真引擎 | skill 的 MCP `spicebridge` 由 `uvx` 拉取 |
| 电子 CAD | `KiCad`（7/8） | `pcb-designer` 原理图/PCB/DRC | 需在 PATH 中可调用 |
| MCP 桥接 | `uvx` | `spicebridge` | 随 `uv` 提供 |
| 调试 | `mcp-server-gdb`、`serial-mcp-server` | `firmware-debugger` 的 GDB 与串口 | 常以 pip 安装；需调试探针硬件 |

## 建议安装命令（示例，跨平台）

```bash
# 系统包管理器安装（Debian/Ubuntu 示例）
sudo apt install -y python3 python3-pip nodejs npm ngspice kicad
pip install uv mcp-server-gdb serial-mcp-server

# 确认关键程序存在
python3 --version && node --version && ngspice --version && npx --version
```

## MCP 服务在 Skill 中的定义（路径为 Linux 语义）

- `esp-mcp` → `uv run --directory ~/.local/share/oh-my-embedded/esp-mcp --python 3.11 python main.py`
- `kicad`   → `node ~/.local/share/oh-my-embedded/kicad-mcp-server/dist/index.js`
- `jlcpcb`  → `npx -y @jlcpcb/mcp`
- `spicebridge` → `uvx spicebridge`

> Windows 下需把 `~` 展开为实际用户目录，并确认这些工具在 PATH 中。

## image-gen 独立依赖

- Node 18+（`scripts/node/image-gen.js`）或 Python 3 标准库（`scripts/python/image_gen.py`）。
- 无额外 pip 依赖（Python 版仅用标准库）。
