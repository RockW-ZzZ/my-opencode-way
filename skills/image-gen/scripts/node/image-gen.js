#!/usr/bin/env node
/* eslint-disable @typescript-eslint/no-var-requires */
const { access, mkdir, readFile, writeFile } = require("node:fs/promises");
const fs = require("node:fs");
const path = require("node:path");

function loadSkillEnv() {
  const envPath = path.resolve(__dirname, "..", "..", ".env");
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, "utf8").split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const equalAt = trimmed.indexOf("=");
    if (equalAt < 1) continue;
    const key = trimmed.slice(0, equalAt).trim();
    let value = trimmed.slice(equalAt + 1).trim();
    if ((value.startsWith("\"") && value.endsWith("\"")) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (!process.env[key]) process.env[key] = value;
  }
}

loadSkillEnv();

const IMAGE_MODELS = ["gpt-image-2", "grok-imagine-image"];
const VIDEO_MODELS = ["grok-imagine-video", "grok-imagine-video-1.5"];
const VIDEO_RESOLUTIONS = ["480p", "720p", "1080p"];
const VIDEO_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"];

class UserError extends Error {
  constructor(code, message, detail = {}) {
    super(message);
    this.code = code;
    this.detail = detail;
  }
}

function parseArgs(argv = process.argv.slice(2)) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const equalAt = item.indexOf("=");
    if (equalAt > 2) args[item.slice(2, equalAt)] = item.slice(equalAt + 1);
    else if (!argv[i + 1] || argv[i + 1].startsWith("--")) args[item.slice(2)] = "true";
    else args[item.slice(2)] = argv[++i];
  }
  return args;
}

function usage() {
  return [
    "用法：node scripts/node/image-gen.js --mode text|image|edit|video --prompt <提示词> [参数]",
    "",
    "  --api-key <key>       默认读取 OPENAI_API_KEY",
    "  --base-url <url>      默认 https://api.apikey.fan/v1",
    "  --mode <mode>         text、image、edit 或 video",
    "  --prompt <text>       提示词",
    "  --image <path|url>    image/edit 必填；video 可选（图生视频）",
    "  --model <model>       不传则根据 /models 自动选择",
    "  --list-models         仅发现并输出模型",
    "  --out <path|dir>      保存位置",
    "  --timeout <seconds>   默认 900",
    "  --n <number>          图片数量，默认 1",
    "  --size <size>         图片尺寸，默认 1024x1024",
    "  --quality <quality>   图片质量，默认 auto",
    "  --duration <seconds>  视频 1-15 秒，默认 8",
    "  --resolution <value>  视频 480p、720p 或 1080p，默认 720p",
    "  --aspect-ratio <ratio> 视频宽高比，默认 16:9",
    "  --poll-interval <sec> 视频轮询间隔，默认 5",
  ].join("\n");
}

function requireArg(args, key, fallback = "") {
  const value = args[key] || fallback;
  if (!value) throw new UserError("missing_argument", `缺少必填参数 --${key}`, { key, usage: usage() });
  return value;
}

function intArg(args, key, fallback, min = 1, max = Number.MAX_SAFE_INTEGER) {
  const raw = args[key] ?? String(fallback);
  const value = Number(raw);
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new UserError("invalid_argument", `--${key} 必须是 ${min}-${max} 的整数`, { key, value: raw });
  }
  return value;
}

function choiceArg(args, key, fallback, choices) {
  const value = args[key] || fallback;
  if (!choices.includes(value)) throw new UserError("invalid_argument", `--${key} 只能是 ${choices.join("、")}`, { key, value });
  return value;
}

function normalizeMode(mode) {
  const value = (mode || "text").toLowerCase();
  if (!["text", "image", "edit", "video"].includes(value)) {
    throw new UserError("invalid_mode", "--mode 只能是 text、image、edit 或 video", { mode });
  }
  return value;
}

function buildApiUrl(baseUrl, apiPath) {
  const base = (baseUrl || "https://api.apikey.fan/v1").replace(/\/+$/, "");
  const suffix = apiPath.startsWith("/") ? apiPath : `/${apiPath}`;
  return base.endsWith("/v1") && suffix.startsWith("/v1/") ? `${base}${suffix.slice(3)}` : `${base}${suffix}`;
}

function timeoutSignal(seconds) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), seconds * 1000);
  return { signal: controller.signal, clear: () => clearTimeout(timer) };
}

async function fetchTimed(url, options, seconds, code = "network_error") {
  const timeout = timeoutSignal(seconds);
  try {
    return await fetch(url, { ...options, signal: timeout.signal });
  } catch (error) {
    if (error.name === "AbortError") throw new UserError("request_timeout", "接口请求超时", { url, timeout: seconds });
    throw new UserError(code, "接口请求网络失败", { url, reason: error.message });
  } finally {
    timeout.clear();
  }
}

async function jsonResponse(response, url, code) {
  const body = await response.text();
  if (!response.ok) throw new UserError(code, "接口返回非成功状态码", { url, status: response.status, body });
  try { return JSON.parse(body); }
  catch (error) { throw new UserError("api_json_parse_error", "接口响应不是合法 JSON", { url, body, reason: error.message }); }
}

function extractModelIds(payload) {
  const groups = Array.isArray(payload) ? [payload] : [payload?.data, payload?.models];
  const ids = [];
  for (const item of groups.flatMap((group) => Array.isArray(group) ? group : group ? [group] : [])) {
    const id = typeof item === "string" ? item : item?.id || item?.model || item?.name;
    if (typeof id === "string" && id.trim()) ids.push(id.trim());
  }
  return [...new Set(ids)];
}

async function discoverModels(baseUrl, apiKey, timeout) {
  const url = buildApiUrl(baseUrl, "/v1/models");
  const response = await fetchTimed(url, { headers: { Authorization: `Bearer ${apiKey}` } }, timeout);
  const models = extractModelIds(await jsonResponse(response, url, "model_discovery_http_error"));
  if (!models.length) throw new UserError("model_discovery_empty", "上游模型列表为空或格式无法识别", { url });
  return models;
}

function selectModel(mode, args, availableModels) {
  const compatible = mode === "video" ? VIDEO_MODELS : IMAGE_MODELS;
  const requested = args.model || (mode !== "video" ? args["image-model"] : "");
  if (requested && !compatible.includes(requested)) {
    throw new UserError("unsupported_model", "指定模型不属于当前模式的已知可用模型", { mode, model: requested, compatible });
  }
  if (requested && !availableModels.includes(requested)) {
    throw new UserError("model_unavailable", "指定模型不在上游模型列表中", { mode, model: requested });
  }
  if (requested) return requested;
  const candidates = mode === "video"
    ? ((args.resolution || "720p") === "1080p" ? ["grok-imagine-video-1.5"] : ["grok-imagine-video"])
    : IMAGE_MODELS;
  const selected = candidates.find((model) => availableModels.includes(model));
  if (!selected) throw new UserError("no_compatible_model", "上游没有适用于当前任务的已知模型", { mode, candidates });
  return selected;
}

function validateVideoModel(model, resolution) {
  if (resolution === "1080p" && model !== "grok-imagine-video-1.5") {
    throw new UserError("invalid_model_configuration", "1080p 必须使用 grok-imagine-video-1.5", { model, resolution });
  }
  if (resolution !== "1080p" && model === "grok-imagine-video-1.5") {
    throw new UserError("invalid_model_configuration", "grok-imagine-video-1.5 在本 Skill 中仅用于 1080p", { model, resolution });
  }
}

function contentType(file) {
  const ext = path.extname(file).toLowerCase();
  if ([".jpg", ".jpeg"].includes(ext)) return "image/jpeg";
  if (ext === ".webp") return "image/webp";
  return "image/png";
}

async function imageDataUrl(image) {
  if (/^https?:\/\//i.test(image) || /^data:/i.test(image)) return image;
  try { await access(image); }
  catch { throw new UserError("image_path_not_found", "本地图片路径不存在或不可读取", { image }); }
  return `data:${contentType(image)};base64,${(await readFile(image)).toString("base64")}`;
}

async function formImage(image, timeout) {
  if (/^https?:\/\//i.test(image)) {
    const response = await fetchTimed(image, {}, timeout, "image_url_fetch_failed");
    if (!response.ok) throw new UserError("image_url_http_error", "图片链接返回错误", { image, status: response.status });
    const type = response.headers.get("content-type")?.split(";")[0] || "image/png";
    if (!type.startsWith("image/")) throw new UserError("image_url_not_image", "链接内容不是图片", { image, contentType: type });
    return { blob: new Blob([await response.arrayBuffer()], { type }), name: path.basename(new URL(image).pathname) || "source.png" };
  }
  try { await access(image); }
  catch { throw new UserError("image_path_not_found", "本地图片路径不存在或不可读取", { image }); }
  return { blob: new Blob([await readFile(image)], { type: contentType(image) }), name: path.basename(image) };
}

function parseSse(frame) {
  const data = frame.split(/\r?\n/).filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart()).join("\n").trim();
  if (!data || data === "[DONE]") return null;
  try { return JSON.parse(data); }
  catch (error) { throw new UserError("sse_json_parse_error", "SSE data 不是合法 JSON", { data, reason: error.message }); }
}

async function* events(response) {
  if ((response.headers.get("content-type") || "").includes("application/json")) {
    yield await jsonResponse(response, response.url, "api_http_error");
    return;
  }
  if (!response.ok) throw new UserError("api_http_error", "生成接口返回错误", { status: response.status, body: await response.text() });
  if (!response.body) throw new UserError("stream_unreadable", "响应没有 SSE 流");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() || "";
    for (const frame of frames) { const event = parseSse(frame); if (event) yield event; }
  }
  buffer += decoder.decode();
  if (buffer.trim()) { const event = parseSse(buffer); if (event) yield event; }
}

function imageResults(event, out = []) {
  if (!event || typeof event !== "object") return out;
  for (const key of ["b64_json", "base64", "image_base64"]) {
    if (typeof event[key] === "string" && event[key] && !out.some((item) => item.type === "base64" && item.value === event[key])) {
      out.push({ type: "base64", value: event[key] });
    }
  }
  if (typeof event.url === "string" && /^https?:\/\//i.test(event.url) && !out.some((item) => item.type === "url" && item.value === event.url)) {
    out.push({ type: "url", value: event.url });
  }
  for (const item of event.data || []) imageResults(item, out);
  for (const item of event.response?.output || []) {
    if (typeof item?.result === "string" && item.result && !out.some((result) => result.type === "base64" && result.value === item.result)) {
      out.push({ type: "base64", value: item.result });
    }
    imageResults(item, out);
  }
  if (typeof event.item?.result === "string" && event.item.result && !out.some((item) => item.type === "base64" && item.value === event.item.result)) {
    out.push({ type: "base64", value: event.item.result });
  }
  return out;
}

function outputPath(out, index, total, defaultName) {
  const target = out || defaultName;
  const ext = path.extname(target);
  if (target.endsWith("/") || target.endsWith("\\") || !ext) {
    const name = total > 1 ? defaultName.replace(/(\.[^.]+)$/, `-${index + 1}$1`) : defaultName;
    return path.resolve(target, name);
  }
  return total === 1 ? path.resolve(target) : path.resolve(path.dirname(target), `${path.basename(target, ext)}-${index + 1}${ext}`);
}

async function saveImages(results, out, defaultName, timeout) {
  const paths = [];
  for (let i = 0; i < results.length; i += 1) {
    const file = outputPath(out, i, results.length, defaultName);
    await mkdir(path.dirname(file), { recursive: true });
    let bytes;
    if (results[i].type === "base64") bytes = Buffer.from(results[i].value, "base64");
    else {
      const response = await fetchTimed(results[i].value, {}, timeout, "image_url_fetch_failed");
      if (!response.ok) throw new UserError("image_url_http_error", "生成图片下载失败", { status: response.status });
      bytes = Buffer.from(await response.arrayBuffer());
    }
    await writeFile(file, bytes);
    paths.push(file);
  }
  return paths;
}

async function generateImage(args, mode, model, apiKey, timeout) {
  const prompt = requireArg(args, "prompt");
  const n = intArg(args, "n", 1);
  const headers = { Authorization: `Bearer ${apiKey}`, Accept: "text/event-stream" };
  let url;
  let body;
  if (mode === "text") {
    url = buildApiUrl(args["base-url"], "/v1/images/generations");
    headers["Content-Type"] = "application/json";
    const payload = { model, prompt, n, size: args.size || "1024x1024", stream: true, response_format: "b64_json" };
    if (model === "grok-imagine-image") { if (args.quality) payload.quality = args.quality; }
    else payload.quality = args.quality || "auto";
    body = JSON.stringify(payload);
  } else {
    const image = requireArg(args, "image");
    url = buildApiUrl(args["base-url"], "/v1/images/edits");
    if (model === "grok-imagine-image") {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify({ model, prompt, image: { url: await imageDataUrl(image), type: "image_url" }, n, stream: true, response_format: "b64_json" });
    } else {
      const source = await formImage(image, timeout);
      const form = new FormData();
      form.append("image", source.blob, source.name);
      for (const [key, value] of Object.entries({ prompt, model, n, quality: args.quality || "auto", size: args.size || "1024x1024", stream: "true", response_format: "b64_json" })) form.append(key, String(value));
      body = form;
    }
  }
  const response = await fetchTimed(url, { method: "POST", headers, body }, timeout);
  const found = [];
  for await (const event of events(response)) {
    if (["error", "response.failed"].includes(event?.type)) throw new UserError("api_stream_error", "图片接口返回错误", { event });
    if (["image_generation.partial_image", "response.image_generation_call.partial_image"].includes(event?.type)) continue;
    found.push(...imageResults(event));
    if (found.length >= n) break;
  }
  if (!found.length) throw new UserError("no_image_result", "没有收到图片结果", { mode, model, url });
  const ext = model === "grok-imagine-image" ? ".jpg" : ".png";
  const defaultName = mode === "edit" ? `edited-image${ext}` : `generated-image${ext}`;
  return { ok: true, mode, model, paths: await saveImages(found.slice(0, n), args.out || defaultName, defaultName, timeout) };
}

async function generateVideo(args, model, apiKey, timeout) {
  const prompt = requireArg(args, "prompt");
  const duration = intArg(args, "duration", 8, 1, 15);
  const resolution = choiceArg(args, "resolution", "720p", VIDEO_RESOLUTIONS);
  const aspectRatio = choiceArg(args, "aspect-ratio", "16:9", VIDEO_RATIOS);
  const interval = intArg(args, "poll-interval", 5, 1, 60);
  validateVideoModel(model, resolution);
  const url = buildApiUrl(args["base-url"], "/v1/videos/generations");
  const request = { model, prompt, duration, resolution, aspect_ratio: aspectRatio };
  if (args.image) request.image = { url: await imageDataUrl(args.image) };
  const started = await jsonResponse(await fetchTimed(url, { method: "POST", headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" }, body: JSON.stringify(request) }, timeout), url, "video_start_http_error");
  const requestId = started.request_id || started.id;
  if (!requestId) throw new UserError("video_request_id_missing", "视频响应缺少 request_id", { response: started });
  const deadline = Date.now() + timeout * 1000;
  const statusUrl = buildApiUrl(args["base-url"], `/v1/videos/${encodeURIComponent(requestId)}`);
  while (Date.now() < deadline) {
    const remaining = Math.max(1, Math.ceil((deadline - Date.now()) / 1000));
    const result = await jsonResponse(await fetchTimed(statusUrl, { headers: { Authorization: `Bearer ${apiKey}` } }, remaining), statusUrl, "video_poll_http_error");
    if (result.status === "done") {
      const videoUrl = result.video?.url || result.url;
      if (!videoUrl) throw new UserError("no_video_result", "视频完成响应缺少 URL", { response: result });
      const response = await fetchTimed(videoUrl, {}, remaining, "video_download_failed");
      if (!response.ok) throw new UserError("video_download_http_error", "视频下载失败", { status: response.status });
      const file = outputPath(args.out || "generated-video.mp4", 0, 1, "generated-video.mp4");
      await mkdir(path.dirname(file), { recursive: true });
      await writeFile(file, Buffer.from(await response.arrayBuffer()));
      return { ok: true, mode: "video", model, duration, resolution, request_id: requestId, paths: [file] };
    }
    if (["failed", "expired"].includes(result.status)) throw new UserError("video_generation_failed", `视频生成状态为 ${result.status}`, { requestId, response: result });
    await new Promise((resolve) => setTimeout(resolve, interval * 1000));
  }
  throw new UserError("request_timeout", "视频生成轮询超时", { requestId, timeout });
}

async function main() {
  const args = parseArgs();
  if (args.help) return process.stdout.write(`${usage()}\n`);
  const apiKey = requireArg(args, "api-key", process.env.OPENAI_API_KEY || "");
  const timeout = intArg(args, "timeout", 900);
  const baseUrl = args["base-url"] || "https://api.apikey.fan/v1";
  const models = await discoverModels(baseUrl, apiKey, timeout);
  if (args["list-models"]) {
    return process.stdout.write(`${JSON.stringify({ ok: true, models, compatible: { image: IMAGE_MODELS.filter((m) => models.includes(m)), video: VIDEO_MODELS.filter((m) => models.includes(m)) } }, null, 2)}\n`);
  }
  const mode = normalizeMode(args.mode);
  const model = selectModel(mode, args, models);
  const result = mode === "video" ? await generateVideo(args, model, apiKey, timeout) : await generateImage(args, mode, model, apiKey, timeout);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error) => {
  process.stderr.write(`${JSON.stringify({ ok: false, code: error.code || "unexpected_error", message: error.message || String(error), detail: error.detail || {} }, null, 2)}\n`);
  process.exitCode = 1;
});
