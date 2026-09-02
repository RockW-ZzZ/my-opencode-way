#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


def load_skill_env():
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


load_skill_env()

IMAGE_MODELS = ("gpt-image-2", "grok-imagine-image")
VIDEO_MODELS = ("grok-imagine-video", "grok-imagine-video-1.5")
VIDEO_RESOLUTIONS = ("480p", "720p", "1080p")
VIDEO_RATIOS = ("1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3")


class UserError(Exception):
    def __init__(self, code, message, detail=None):
        super().__init__(message)
        self.code = code
        self.detail = detail or {}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise UserError("invalid_argument", message, {"usage": self.format_usage()})


def parse_args():
    parser = JsonArgumentParser(description="api.apikey.fun 图片/视频生成脚本")
    parser.add_argument("--mode", default="text", choices=("text", "image", "edit", "video"))
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    parser.add_argument("--base-url", default="https://api.apikey.fun/v1")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--image", default="", help="image/edit 必填；video 可选（图生视频）")
    parser.add_argument("--model", default="", help="不传则根据 /models 自动选择")
    parser.add_argument("--image-model", default="", help="兼容旧参数，等同图片模式的 --model")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--n", default="1")
    parser.add_argument("--out", default="")
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="auto")
    parser.add_argument("--output-format", default="png")
    parser.add_argument("--duration", default="8", help="视频时长 1-15 秒，默认 8")
    parser.add_argument("--resolution", default="720p", choices=VIDEO_RESOLUTIONS)
    parser.add_argument("--aspect-ratio", default="16:9", choices=VIDEO_RATIOS)
    parser.add_argument("--poll-interval", default="5")
    parser.add_argument("--timeout", default="900")
    args = parser.parse_args()
    if not args.api_key:
        raise UserError("missing_argument", "缺少 API Key：请传入 --api-key 或设置 OPENAI_API_KEY")
    args.n = positive_int(args.n, "n")
    args.timeout = positive_int(args.timeout, "timeout")
    args.poll_interval = ranged_int(args.poll_interval, "poll-interval", 1, 60)
    args.duration = ranged_int(args.duration, "duration", 1, 15)
    if not args.list_models and not args.prompt:
        raise UserError("missing_argument", "缺少必填参数 --prompt", {"key": "prompt"})
    if not args.list_models and args.mode in ("image", "edit") and not args.image:
        raise UserError("missing_argument", f"{args.mode} 模式必须传入 --image", {"key": "image"})
    return args


def ranged_int(value, key, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise UserError("invalid_argument", f"--{key} 必须是整数", {"key": key, "value": value}) from error
    if parsed < minimum or parsed > maximum:
        raise UserError("invalid_argument", f"--{key} 必须是 {minimum}-{maximum} 的整数", {"key": key, "value": value})
    return parsed


def positive_int(value, key):
    return ranged_int(value, key, 1, 2**31 - 1)


def build_api_url(base_url, api_path):
    base = base_url.rstrip("/")
    suffix = api_path if api_path.startswith("/") else f"/{api_path}"
    return f"{base}{suffix[3:]}" if base.endswith("/v1") and suffix.startswith("/v1/") else f"{base}{suffix}"


def open_request(request, timeout, url, code="api_http_error"):
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise UserError(code, "接口返回非成功状态码", {"url": url, "status": error.code, "body": body}) from error
    except (urllib.error.URLError, TimeoutError) as error:
        reason = str(getattr(error, "reason", error))
        if "timed out" in reason.lower():
            raise UserError("request_timeout", "接口请求超时", {"url": url, "timeout": timeout}) from error
        raise UserError("network_error", "接口请求网络失败", {"url": url, "reason": reason}) from error


def json_request(url, api_key="", body=None, timeout=900, method=None, error_code="api_http_error"):
    headers = {"User-Agent": "apikey-fun-image-gen/2.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"), headers=headers)
    with open_request(request, timeout, url, error_code) as response:
        raw = response.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise UserError("api_json_parse_error", "接口响应不是合法 JSON", {"url": url, "body": raw}) from error


def extract_model_ids(payload):
    groups = [payload] if isinstance(payload, list) else [payload.get("data"), payload.get("models")]
    ids = []
    for group in groups:
        items = group if isinstance(group, list) else ([group] if group else [])
        for item in items:
            model_id = item if isinstance(item, str) else item.get("id") or item.get("model") or item.get("name")
            if isinstance(model_id, str) and model_id.strip() and model_id.strip() not in ids:
                ids.append(model_id.strip())
    return ids


def discover_models(args):
    url = build_api_url(args.base_url, "/v1/models")
    models = extract_model_ids(json_request(url, args.api_key, timeout=args.timeout, error_code="model_discovery_http_error"))
    if not models:
        raise UserError("model_discovery_empty", "上游模型列表为空或格式无法识别", {"url": url})
    return models


def select_model(args, available):
    compatible = VIDEO_MODELS if args.mode == "video" else IMAGE_MODELS
    requested = args.model or (args.image_model if args.mode != "video" else "")
    if requested and requested not in compatible:
        raise UserError("unsupported_model", "指定模型不属于当前模式的已知可用模型", {"mode": args.mode, "model": requested, "compatible": compatible})
    if requested and requested not in available:
        raise UserError("model_unavailable", "指定模型不在上游模型列表中", {"mode": args.mode, "model": requested})
    if requested:
        return requested
    candidates = (("grok-imagine-video-1.5",) if args.resolution == "1080p" else ("grok-imagine-video",)) if args.mode == "video" else IMAGE_MODELS
    selected = next((model for model in candidates if model in available), "")
    if not selected:
        raise UserError("no_compatible_model", "上游没有适用于当前任务的已知模型", {"mode": args.mode, "candidates": candidates})
    return selected


def validate_video_model(model, resolution):
    if resolution == "1080p" and model != "grok-imagine-video-1.5":
        raise UserError("invalid_model_configuration", "1080p 必须使用 grok-imagine-video-1.5", {"model": model, "resolution": resolution})
    if resolution != "1080p" and model == "grok-imagine-video-1.5":
        raise UserError("invalid_model_configuration", "grok-imagine-video-1.5 在本 Skill 中仅用于 1080p", {"model": model, "resolution": resolution})


def image_data_url(image):
    if image.startswith(("http://", "https://", "data:")):
        return image
    path = Path(image)
    if not path.is_file():
        raise UserError("image_path_not_found", "本地图片路径不存在或不是文件", {"image": image})
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def image_file(image, timeout):
    if image.startswith(("http://", "https://")):
        request = urllib.request.Request(image, headers={"User-Agent": "apikey-fun-image-gen/2.0"})
        with open_request(request, timeout, image, "image_url_http_error") as response:
            mime = response.headers.get("content-type", "image/png").split(";")[0]
            if not mime.startswith("image/"):
                raise UserError("image_url_not_image", "链接内容不是图片", {"image": image, "contentType": mime})
            return response.read(), mime, Path(urllib.parse.urlparse(image).path).name or "source.png"
    path = Path(image)
    if not path.is_file():
        raise UserError("image_path_not_found", "本地图片路径不存在或不是文件", {"image": image})
    return path.read_bytes(), mimetypes.guess_type(str(path))[0] or "image/png", path.name


def multipart_request(url, api_key, fields, image, timeout):
    boundary = f"----apikeyfun-{uuid.uuid4().hex}"
    chunks = []
    for name, value in fields.items():
        chunks.extend([f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n".encode(), str(value).encode(), b"\r\n"])
    data, mime, filename = image
    chunks.extend([f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n".encode(), data, b"\r\n", f"--{boundary}--\r\n".encode()])
    request = urllib.request.Request(url, data=b"".join(chunks), method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Accept": "text/event-stream", "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    return open_request(request, timeout, url)


def stream_request(url, api_key, body, timeout):
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "text/event-stream"
    })
    return open_request(request, timeout, url)


def iter_events(response):
    if "application/json" in response.headers.get("content-type", ""):
        yield json.loads(response.read().decode("utf-8"))
        return
    buffer = ""
    while True:
        chunk = response.read(4096)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace").replace("\r\n", "\n")
        frames = buffer.split("\n\n")
        buffer = frames.pop()
        for frame in frames:
            event = parse_sse(frame)
            if event is not None:
                yield event
    if buffer.strip():
        event = parse_sse(buffer)
        if event is not None:
            yield event


def parse_sse(frame):
    data = "\n".join(line[5:].lstrip() for line in frame.splitlines() if line.startswith("data:")).strip()
    if not data or data == "[DONE]":
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError as error:
        raise UserError("sse_json_parse_error", "SSE data 不是合法 JSON", {"data": data}) from error


def collect_images(event, results=None):
    results = [] if results is None else results
    if not isinstance(event, dict):
        return results
    for key in ("b64_json", "base64", "image_base64"):
        if isinstance(event.get(key), str) and event[key]:
            item = ("base64", event[key])
            if item not in results:
                results.append(item)
    if isinstance(event.get("url"), str) and event["url"].startswith(("http://", "https://")):
        item = ("url", event["url"])
        if item not in results:
            results.append(item)
    for item in event.get("data") or []:
        collect_images(item, results)
    for item in (event.get("response") or {}).get("output") or []:
        if isinstance(item.get("result"), str) and item["result"]:
            value = ("base64", item["result"])
            if value not in results:
                results.append(value)
        collect_images(item, results)
    if isinstance((event.get("item") or {}).get("result"), str):
        item = ("base64", event["item"]["result"])
        if item not in results:
            results.append(item)
    return results


def output_path(out, index, total, default_name):
    target = Path(out or default_name)
    if str(out or "").endswith(("/", "\\")) or not target.suffix:
        name = default_name if total == 1 else f"{Path(default_name).stem}-{index + 1}{Path(default_name).suffix}"
        return (target / name).resolve()
    return target.resolve() if total == 1 else target.with_name(f"{target.stem}-{index + 1}{target.suffix}").resolve()


def save_images(results, out, default_name, timeout):
    paths = []
    for index, (kind, value) in enumerate(results):
        file = output_path(out, index, len(results), default_name)
        file.parent.mkdir(parents=True, exist_ok=True)
        if kind == "base64":
            data = base64.b64decode(value)
        else:
            with open_request(urllib.request.Request(value), timeout, value, "image_url_http_error") as response:
                data = response.read()
        file.write_bytes(data)
        paths.append(str(file))
    return paths


def generate_image(args, model):
    url = build_api_url(args.base_url, "/v1/images/generations" if args.mode == "text" else "/v1/images/edits")
    common = {"model": model, "prompt": args.prompt, "n": args.n, "stream": True, "response_format": "b64_json"}
    if args.mode == "text":
        common.update({"size": args.size, "quality": args.quality})
        response = stream_request(url, args.api_key, common, args.timeout)
    elif model == "grok-imagine-image":
        common["image"] = {"url": image_data_url(args.image), "type": "image_url"}
        response = stream_request(url, args.api_key, common, args.timeout)
    else:
        fields = {**common, "stream": "true", "size": args.size, "quality": args.quality}
        response = multipart_request(url, args.api_key, fields, image_file(args.image, args.timeout), args.timeout)
    found = []
    with response:
        for event in iter_events(response):
            if event.get("type") in ("error", "response.failed"):
                raise UserError("api_stream_error", "图片接口返回错误", {"event": event})
            if event.get("type") in ("image_generation.partial_image", "response.image_generation_call.partial_image"):
                continue
            found.extend(collect_images(event))
            if len(found) >= args.n:
                break
    if not found:
        raise UserError("no_image_result", "没有收到图片结果", {"mode": args.mode, "model": model, "url": url})
    ext = ".jpg" if model == "grok-imagine-image" else ".png"
    default_name = f"{'edited' if args.mode == 'edit' else 'generated'}-image{ext}"
    return {"ok": True, "mode": args.mode, "model": model, "paths": save_images(found[:args.n], args.out or default_name, default_name, args.timeout)}


def generate_video(args, model):
    validate_video_model(model, args.resolution)
    url = build_api_url(args.base_url, "/v1/videos/generations")
    body = {"model": model, "prompt": args.prompt, "duration": args.duration, "resolution": args.resolution, "aspect_ratio": args.aspect_ratio}
    if args.image:
        body["image"] = {"url": image_data_url(args.image)}
    started = json_request(url, args.api_key, body, args.timeout, error_code="video_start_http_error")
    request_id = started.get("request_id") or started.get("id")
    if not request_id:
        raise UserError("video_request_id_missing", "视频响应缺少 request_id", {"response": started})
    deadline = time.monotonic() + args.timeout
    status_url = build_api_url(args.base_url, f"/v1/videos/{urllib.parse.quote(str(request_id), safe='')}")
    while time.monotonic() < deadline:
        result = json_request(status_url, args.api_key, timeout=max(1, int(deadline - time.monotonic())), error_code="video_poll_http_error")
        if result.get("status") == "done":
            video_url = (result.get("video") or {}).get("url") or result.get("url")
            if not video_url:
                raise UserError("no_video_result", "视频完成响应缺少 URL", {"response": result})
            with open_request(urllib.request.Request(video_url), max(1, int(deadline - time.monotonic())), video_url, "video_download_http_error") as response:
                data = response.read()
            file = output_path(args.out or "generated-video.mp4", 0, 1, "generated-video.mp4")
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
            return {"ok": True, "mode": "video", "model": model, "duration": args.duration, "resolution": args.resolution, "request_id": request_id, "paths": [str(file)]}
        if result.get("status") in ("failed", "expired"):
            raise UserError("video_generation_failed", f"视频生成状态为 {result['status']}", {"request_id": request_id, "response": result})
        time.sleep(args.poll_interval)
    raise UserError("request_timeout", "视频生成轮询超时", {"request_id": request_id, "timeout": args.timeout})


def main():
    args = parse_args()
    models = discover_models(args)
    if args.list_models:
        print(json.dumps({"ok": True, "models": models, "compatible": {"image": [m for m in IMAGE_MODELS if m in models], "video": [m for m in VIDEO_MODELS if m in models]}}, ensure_ascii=False, indent=2))
        return
    model = select_model(args, models)
    result = generate_video(args, model) if args.mode == "video" else generate_image(args, model)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except UserError as error:
        print(json.dumps({"ok": False, "code": error.code, "message": str(error), "detail": error.detail}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        print(json.dumps({"ok": False, "code": "unexpected_error", "message": str(error), "detail": {}}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
