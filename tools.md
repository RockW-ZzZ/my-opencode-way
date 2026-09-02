# 外部系统依赖（插件 / Skill 所需）

> 这些是**系统层面**要预装的程序/运行时；Skill 通过 MCP 或 shell 调用它们。装了并不影响其它 Skill。
> 各 MCP 服务器的官方安装方式以 oh-my-embedded 仓库 README「Prerequisites」为准。

## 运行时 / 工具

| 类别 | 程序 | 用途 | 说明 |
|---|---|---|---|
| Python 运行时 | `python3` / `uv` | 运行 esp-mcp、spicebridge 等 | 需 Python 3.11+；esp-mcp 另需 `uv python install 3.11` |
| 节点运行时 | `node` / `npx` | kicad-mcp-server、@jlcpcb/mcp、firecrawl-cli、image-gen 的 Node 脚本 | Node 18+ |
| 电路仿真 | `ngspice` | `circuit-simulator` 仿真引擎 | Windows 经 MSYS2 安装，见下方记录 |
| 电子 CAD | `KiCad`（本机 10.x） | `pcb-designer` 原理图/PCB/DRC | 需 `kicad-cli` 在 PATH 中可调用 |
| 调试 | `mcp-server-gdb`、`serial-mcp-server` | `firmware-debugger` 的 GDB 与串口 | **Rust 项目，`cargo install`**（非 pip）；另需 GDB 工具链与调试探针硬件 |
| 网页抓取 | `firecrawl-cli` | `opencode-firecrawl` 插件的命令行工具 | `npm i -g firecrawl-cli`；首次使用引导登录或设置 `FIRECRAWL_API_KEY` |

## 本机（Windows）实际安装记录（2026-09-02）

```powershell
# uv（pip 装到用户 Scripts，已加入用户 PATH）
python -m pip install uv
uv python install 3.11          # esp-mcp 要求 3.11

# PyPI / npm 类
python -m pip install spicebridge
npm i -g kicad-mcp-server       # 注意：npm 上不存在，见下方 kicad-mcp-server 条目
npm i -g firecrawl-cli

# Rust 类（winget install Rustlang.Rustup 后）
cargo install serial-mcp-server
cargo install mcp-server-gdb --version 0.2.2 --locked
#   ⚠ 最新 0.2.3 在 Rust 1.98 下编译失败（E0061/E0308/E0599），需 pin 0.2.2

# KiCad（per-user 安装，bin 已加入用户 PATH）
winget install --id KiCad.KiCad -e

# ngspice（SourceForge 被墙/403，走 MSYS2 官方源）
winget install --id MSYS2.MSYS2 -e
C:\msys64\usr\bin\bash.exe -lc "pacman -Sy --noconfirm mingw-w64-x86_64-ngspice"
```

### 关键坑位记录

- **ngspice**：MSYS2 的 `ngspice.exe` 是 GUI 子系统构建，重定向管道会**无限挂起**；
  同目录 `ngspice_con.exe` 才是控制台版。本机做法：`ngspice.exe` 改名为 `ngspice_gui.exe`，
  再把 `ngspice_con.exe` 复制为 `ngspice.exe`（同目录 DLL 齐全）。
  spicelib 的查找顺序：`C:/Apps/NGSpice64/bin/ngspice.exe` → `C:/Spice64/ngspice.exe` → `/usr/local/bin/ngspice` → PATH。
- **kicad-mcp-server**（npm 上无此包）：需手动放到
  `C:\Users\zcj12\.local\share\oh-my-embedded\kicad-mcp-server`，
  在该目录 `npm install && npm run build` 生成 `dist/index.js`（插件用 `node dist/index.js` 启动）。
- **esp-mcp**（PyPI 无此包）：仓库需放到
  `C:\Users\zcj12\.local\share\oh-my-embedded\esp-mcp`；
  插件用 `uv run --directory .../esp-mcp --python 3.11 python main.py` 启动，
  首次运行 uv 自动建 `.venv` 并装依赖（`mcp[cli]`）。
- **KiCad**：winget 装的是 per-user 版，位于
  `C:\Users\zcj12\AppData\Local\Programs\KiCad\10.0\bin`（含 `kicad-cli.exe`），该目录已加入用户 PATH。

## 建议安装命令（Linux 示例，跨平台参考）

```bash
sudo apt install -y python3 python3-pip nodejs npm ngspice kicad
pip install uv spicebridge
cargo install mcp-server-gdb serial-mcp-server
```

## MCP 服务在 Skill 中的定义（插件 SKILL.md frontmatter，路径为 `~` 语义）

- `esp-mcp`      → `uv run --directory ~/.local/share/oh-my-embedded/esp-mcp --python 3.11 python main.py`（本机已就位）
- `kicad`        → `node ~/.local/share/oh-my-embedded/kicad-mcp-server/dist/index.js`（本机已构建）
- `gdb`          → `mcp-server-gdb`（cargo 安装于 `%USERPROFILE%\.cargo\bin`）
- `serial`       → `serial-mcp-server`（cargo 安装于 `%USERPROFILE%\.cargo\bin`）
- `jlcpcb`       → `npx -y @jlcpcb/mcp`（npx 自动装，无需手动）
- `spicebridge`  → `pip install spicebridge` 后由 `spicebridge` 命令启动

> Windows 下 `~` 由 opencode 展开时指向 `C:\Users\<用户>\`，本机已按此布局放置；若重启后某 MCP 起不来，
> 检查插件生成的 SKILL frontmatter 中 `~` 是否被正确展开，必要时改为绝对路径。

## image-gen 独立依赖

- Node 18+（`scripts/node/image-gen.js`）或 Python 3 标准库（`scripts/python/image_gen.py`）。
- 无额外 pip 依赖（Python 版仅用标准库）。
