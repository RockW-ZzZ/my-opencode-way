# 安装 apikey.fan 图片与视频生成技能包

推荐把整个目录作为 skill 安装，而不是只复制 `SKILL.md`。这样 `scripts/`、`references/api-recipes.md` 等配套文件也会一起保留。

## 推荐发给 AI 的安装提示词

可以直接把下面这句话发给 OpenClaw、Hermes、Codex、Claude Code 或其他支持技能/规则扩展的 AI 客户端：

```text
请安装或读取这个完整技能包：https://apikey.fan/skill/image-gen 。如果你的客户端不能自动拉取整个目录，请先读取 https://apikey.fan/skill/image-gen/SKILL.md ，再按其中的资源导航读取 scripts/node/image-gen.js、scripts/python/image_gen.py、references/api-recipes.md 和 agents/openai.yaml，并把这些文件保存到你当前客户端的技能/规则目录中。
```

如果生产环境暂时使用 `/install/skill` 路径，也可以使用：

```text
请安装或读取这个完整技能包：https://apikey.fan/install/skill/image-gen 。如果你的客户端不能自动拉取整个目录，请先读取 https://apikey.fan/install/skill/image-gen/SKILL.md ，再按其中的资源导航读取 scripts/node/image-gen.js、scripts/python/image_gen.py、references/api-recipes.md 和 agents/openai.yaml，并把这些文件保存到你当前客户端的技能/规则目录中。
```

## 通用安装方式

这个技能包不绑定某一种客户端。安装时遵循三个原则：

1. 安装完整目录，而不是只保存 `SKILL.md`。
2. 保持目录结构不变：
   - `SKILL.md`
   - `INSTALL.md`
   - `package.json`
   - `agents/openai.yaml`
   - `scripts/node/image-gen.js`
   - `scripts/python/image_gen.py`
   - `references/api-recipes.md`
3. 放到当前工具识别的技能、规则或知识目录中。

常见位置示例：

- Codex：通常是 `~/.codex/skills/image-gen`
- Claude Code：通常是 `~/.claude/skills/image-gen`
- OpenClaw、Hermes：放到对应客户端支持的 skill、agent、rule、knowledge 或自定义能力目录中；具体目录以客户端设置页或文档为准。

## Codex 用户可选命令

如果你使用的是 Codex，并且本机已有 Codex 的 skill installer，可以使用：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py https://apikey.fan/skill/image-gen
```

如果你的环境仍然使用 `/install/skill` 路径，可以改用：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py https://apikey.fan/install/skill/image-gen
```

## 只拿到 SKILL.md 链接时

`https://apikey.fan/skill/image-gen/SKILL.md` 可以让 AI 读取主说明，但不保证所有 AI 或安装器都会自动获取同目录下的其他文件。需要时请显式读取：

- `https://apikey.fan/skill/image-gen/references/api-recipes.md`
- `https://apikey.fan/skill/image-gen/scripts/node/image-gen.js`
- `https://apikey.fan/skill/image-gen/scripts/python/image_gen.py`
- `https://apikey.fan/skill/image-gen/agents/openai.yaml`

如果使用 `/install/skill` 路径，对应读取：

- `https://apikey.fan/install/skill/image-gen/references/api-recipes.md`
- `https://apikey.fan/install/skill/image-gen/scripts/node/image-gen.js`
- `https://apikey.fan/install/skill/image-gen/scripts/python/image_gen.py`
- `https://apikey.fan/install/skill/image-gen/agents/openai.yaml`

## 用途

这个 skill 用于通过 `api.apikey.fan` 构建图片与视频生成：

- 文生图：`/v1/images/generations`
- 参考图生图：`/v1/images/edits`
- 图片编辑：`/v1/images/edits`
- 视频/图生视频：`/v1/videos/generations`，再轮询 `/v1/videos/{request_id}`

每次使用 Skill API 生成前，都要使用刚生效的 Key 向上游 `GET /v1/models` 获取当前模型，再自动选择。图片候选为 `gpt-image-2`、`grok-imagine-image`；视频候选为 `grok-imagine-video`、`grok-imagine-video-1.5`。不要输出或保存真实 Key。

图片请求必须启用 `stream`；视频采用异步提交和轮询。视频默认 8 秒，可选 1–15 秒；1080p 使用 `grok-imagine-video-1.5`。base URL 可配置为 `https://api.apikey.fan` 或 `https://api.apikey.fan/v1`。

每次生成图片或视频前，Skill 必须先询问用户选择“Skill 模型（api.apikey.fan）”还是“本地工具”。选择本地工具时不得调用本技能脚本或 api.apikey.fan。

完整安装后，智能体应优先执行内置模板脚本：

```bash
node scripts/node/image-gen.js --mode text --prompt "生成一张4K狸花猫照片" --size 3840x2160 --out ./cat.png
python3 scripts/python/image_gen.py --mode edit --prompt "把背景改成蓝色" --image ./source.png --out ./edited.png
node scripts/node/image-gen.js --mode video --prompt "海边日落延时摄影" --duration 8 --resolution 720p --out ./sunset.mp4
```
