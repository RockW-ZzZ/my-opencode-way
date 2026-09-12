---
name: image-gen
description: 当用户调用 image_gen，或需要在 OpenClaw、Hermes、Codex、Claude Code、OpenAI 兼容客户端、api.apikey.fan 网关中生成或编辑图片、生成视频、图生视频，或编写相关脚本时使用本技能。每次生成前必须询问用户选择 Skill 模型还是本地工具；选择 Skill 模型后从上游实时发现模型并自动选择，图片请求使用流式输出，视频请求使用异步轮询。
---

# apikey.fan 图片与视频生成

## 资源导航

- `scripts/node/image-gen.js`：Node.js 18+ 可执行脚本，支持 `text|image|edit|video`。
- `scripts/python/image_gen.py`：仅依赖 Python 标准库的等价脚本。
- `references/api-recipes.md`：模型发现、图片 SSE、视频异步轮询的接口配方。
- `agents/openai.yaml`：技能列表 UI 元数据。

完整安装时保留整个目录。若只拿到线上 `SKILL.md`，按同目录路径显式读取上述资源。

## 每次生成前必须选择执行来源

在生成或编辑任何图片、生成任何视频之前，必须先询问用户：

```text
这次使用 Skill 模型（api.apikey.fan）还是本地工具？
```

严格遵守以下规则：

1. 每个新的图片或视频生成任务都重新询问一次；不要沿用上次选择。
2. 用户回答前，不查询上游模型，不调用生成接口，也不调用本地生成工具。
3. 选择 **Skill 模型**：使用本技能脚本，先发现模型，再自动选择并调用 api.apikey.fan。
4. 选择 **本地工具**：不要执行本技能脚本，不要调用 api.apikey.fan；改用当前客户端可用的本地图片或视频工具。
5. 如果当前环境没有适合任务的本地工具，明确说明并让用户改选 Skill 模型；不要自行切换。

## API Key

优先使用当前客户端或 provider 已配置的 api.apikey.fan Key，通常来自 `OPENAI_API_KEY`。也可以使用单次 `--api-key`。

本技能专用 key 保存在技能目录 `.env`（`OPENAI_API_KEY`），脚本启动时自动读取，优先于进程环境变量。base URL 可用 `.env` 中 `IMAGE_GEN_BASE_URL` 覆盖，默认 `https://api.apikey.fan/v1`。

不要要求用户在聊天中粘贴完整 Key，不要输出或保存 Key。缺少 Key 时，让用户把 key 写入技能目录 `.env` 后确认。

## 上游模型发现与自动选择

选择 Skill 模型后，每次执行都先使用同一 base URL 和同一 Key 请求：

```text
GET /v1/models
Authorization: Bearer <key>
```

base URL 为 `https://api.apikey.fan` 时访问 `/v1/models`；base URL 已含 `/v1` 时访问 `/models`，避免 `/v1/v1`。

不得跳过模型发现，也不得在发现失败时盲用默认模型。显式传入 `--model` 时，同样检查它是否出现在上游列表中。

已知兼容模型与自动选择顺序：

- 图片：`gpt-image-2`，其次 `grok-imagine-image`。
- 480p/720p 视频：`grok-imagine-video`。
- 1080p 视频：`grok-imagine-video-1.5`。

如果当前任务所需模型不在上游列表中，返回 `no_compatible_model` 或 `model_unavailable`，不要替换为未知模型。

## 接口模式

### 文生图

- 参数：`--mode text`
- 接口：`POST /v1/images/generations`
- 模型：自动选择可用图片模型。
- 必须发送 `stream: true`、`response_format: "b64_json"` 和 `Accept: text/event-stream`。

### 参考图生图

- 参数：`--mode image --image <path|url>`
- 接口：`POST /v1/images/edits`
- 把输入图片作为参考图，在提示词中写明要借用的主体、构图、配色或风格。

### 图片编辑

- 参数：`--mode edit --image <path|url>`
- 接口：`POST /v1/images/edits`
- 在提示词中明确必须保持不变的内容。

`gpt-image-2` 编辑请求使用 multipart；`grok-imagine-image` 使用 JSON `image.url`。两者都启用流式输出。

### 视频生成与图生视频

- 参数：`--mode video`。
- 文生视频仅传提示词；图生视频额外传 `--image <path|url>`。
- 创建：`POST /v1/videos/generations`。
- 轮询：`GET /v1/videos/{request_id}`，直到 `done`、`failed` 或 `expired`。
- 完成后立即下载临时视频 URL。

视频约束：

- `--duration`：1–15 秒，默认 8 秒。
- `--resolution`：`480p|720p|1080p`，默认 `720p`。
- `grok-imagine-video-1.5` 在本技能中仅用于 1080p。
- `--aspect-ratio`：默认 `16:9`。
- 视频接口为异步任务，不伪装成 SSE；轮询总时长受 `--timeout` 控制。

## 可执行脚本

有 Node.js 18+ 时优先使用 Node 版；否则使用 Python 版。

```bash
node scripts/node/image-gen.js --mode text --prompt "一只太空猫" --out ./cat.png
node scripts/node/image-gen.js --mode video --prompt "海边日落延时摄影" --duration 8 --resolution 720p --out ./sunset.mp4
python scripts/python/image_gen.py --mode edit --prompt "把背景改成蓝色，主体不变" --image ./source.png --out ./edited.png
python scripts/python/image_gen.py --mode video --prompt "让画面中的水流动" --image ./waterfall.png --resolution 1080p
```

只查看模型：

```bash
node scripts/node/image-gen.js --list-models
python scripts/python/image_gen.py --list-models
```

脚本成功时只向 stdout 输出最终 JSON：

```json
{ "ok": true, "mode": "video", "model": "grok-imagine-video", "paths": ["/abs/path/generated-video.mp4"] }
```

失败时向 stderr 输出带错误码的 JSON。常见错误码：

- `model_discovery_http_error` / `model_discovery_empty`
- `model_unavailable` / `no_compatible_model`
- `invalid_model_configuration`
- `api_http_error` / `api_stream_error`
- `video_start_http_error` / `video_poll_http_error` / `video_generation_failed`
- `request_timeout` / `no_image_result` / `no_video_result`

## 结果交付

- 默认直接向用户展示生成图片，或提供可播放的视频及本地绝对路径。
- 用户明确要求只保存时，仅返回路径。
- 不覆盖已有项目资产，除非用户明确要求。
- 图片 URL 和视频 URL 可能是临时地址，脚本应立即下载到本地。

## 提示词

- 简洁描述主体、用途、构图、风格和必要约束。
- 参考图任务说明借用哪些特征。
- 编辑任务说明哪些内容必须保持不变。
- 视频任务描述镜头、主体运动、环境运动及节奏；不要用互相冲突的运动指令。

## 安全要求

- 示例只使用 `YOUR_API_KEY` 或环境变量。
- 模型发现和错误输出不得包含 API Key。
- 网络受限时请求必要权限，不要绕过模型发现或退回同步图片请求。
