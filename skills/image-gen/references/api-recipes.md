# api.apikey.fan 图片与视频 API 配方

## 目录

- 模型发现
- 自动选择规则
- 图片请求
- 视频请求与轮询
- SSE 解析
- CLI 参数

优先执行 `scripts/node/image-gen.js` 或 `scripts/python/image_gen.py`，仅在需要移植到其他语言时复制这里的接口结构。

## 模型发现

每次 Skill API 生成前，用实际生效的 Key 查询：

```http
GET https://api.apikey.fan/v1/models
Authorization: Bearer YOUR_API_KEY
```

兼容读取 `data[].id`、`models[].id` 或字符串数组。不要输出 Key。查询失败或没有兼容模型时停止生成。

自动选择：

| 任务 | 候选模型 |
|---|---|
| 图片 | `gpt-image-2` → `grok-imagine-image` |
| 480p/720p 视频 | `grok-imagine-video` |
| 1080p 视频 | `grok-imagine-video-1.5` |

显式 `--model` 也必须存在于模型发现结果中。

## 图片请求

所有图片请求使用 `stream: true` 和 `Accept: text/event-stream`。

文生图：

```http
POST /v1/images/generations
Content-Type: application/json

{
  "model": "gpt-image-2",
  "prompt": "一只太空猫",
  "n": 1,
  "size": "1024x1024",
  "stream": true,
  "response_format": "b64_json"
}
```

`gpt-image-2` 图片编辑使用 multipart：

```text
POST /v1/images/edits
image=<binary>
prompt=把背景改成蓝色
model=gpt-image-2
stream=true
response_format=b64_json
```

`grok-imagine-image` 图片编辑使用 JSON：

```json
{
  "model": "grok-imagine-image",
  "prompt": "把背景改成蓝色",
  "image": { "url": "data:image/png;base64,...", "type": "image_url" },
  "stream": true,
  "response_format": "b64_json"
}
```

## 视频请求与轮询

视频生成是异步任务。时长为 1–15 秒，默认 8 秒。

创建任务：

```http
POST /v1/videos/generations
Content-Type: application/json

{
  "model": "grok-imagine-video",
  "prompt": "海边日落延时摄影",
  "duration": 8,
  "resolution": "720p",
  "aspect_ratio": "16:9"
}
```

图生视频额外加入：

```json
{ "image": { "url": "data:image/png;base64,..." } }
```

创建响应：

```json
{ "request_id": "request-id" }
```

轮询：

```http
GET /v1/videos/{request_id}
Authorization: Bearer YOUR_API_KEY
```

状态包括 `pending`、`done`、`failed`、`expired`。完成响应中的 `video.url` 通常是临时地址，应立即下载。

```json
{
  "status": "done",
  "video": { "url": "https://example/video.mp4", "duration": 8 }
}
```

## SSE 解析

1. 按空行拆分 frame。
2. 合并 frame 内的 `data:` 行。
3. 忽略 `[DONE]`。
4. 跳过 `image_generation.partial_image` 和 `response.image_generation_call.partial_image`。
5. 从 `b64_json`、`base64`、`image_base64`、`data[]`、`response.output[].result`、`item.result` 或 `url` 提取最终图片。

## CLI 参数

两个脚本共享主要参数：

- `--mode text|image|edit|video`
- `--api-key`、`--base-url`、`--prompt`、`--model`
- `--image`：参考图、编辑原图或视频首帧
- `--list-models`
- 图片：`--n`、`--size`、`--quality`
- 视频：`--duration`、`--resolution`、`--aspect-ratio`、`--poll-interval`
- `--out`、`--timeout`

```bash
node scripts/node/image-gen.js --mode text --prompt "一只太空猫"
node scripts/node/image-gen.js --mode video --prompt "海边日落" --duration 8 --resolution 720p
python scripts/python/image_gen.py --mode video --prompt "让瀑布流动" --image ./waterfall.png --resolution 1080p
```
