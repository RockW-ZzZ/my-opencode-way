# 自定义供应商模型参数

> 本仓库**不备份** provider 的 API Key / `auth.json`。新机自行接入自定义供应商后，
> 必须扫描配置里的模型 ID，按官方参数补全 `modalities` / `limit` / `reasoning`。
> 自定义供应商走 OpenAI 兼容接口时，opencode **不会**自动带上这些能力字段。

## 恢复时自动补全（给 AI / 操作者）

在其它电脑恢复配置、用户已自行写好自定义 `provider` 之后执行：

1. 读取本机全局配置：`~/.config/opencode/opencode.jsonc`（或 `opencode.json`）。
2. 遍历 `provider.*.models` 的每一个模型 ID（大小写按配置原样保留）。
3. 拉取 [models.dev API](https://models.dev/api.json)（opencode 内置模型元数据源），
   在全部供应商下按 **小写 ID** 匹配。
4. 命中则把下列字段写入该模型（保留已有 `name`，不要改 `baseURL` / Key）：
   - `attachment`
   - `modalities.input` / `modalities.output`
   - `limit.context` / `limit.output`
   - `reasoning`
5. models.dev 未命中时，再查厂商官方文档（智谱 docs.bigmodel.cn、xAI docs.x.ai 等）。
6. 写入前对照 [opencode 配置 schema](https://opencode.ai/config.json) 校验。
7. 保存后**退出并重启 opencode**（配置启动时一次性加载）。

### 合法字段（schema 强制）

模型对象 `additionalProperties: false`，写错字段会导致 opencode **无法启动**。

| 要改的能力 | 合法字段 | 非法写法（禁止） |
|---|---|---|
| 输入/输出类型 | `modalities.input` / `modalities.output` | `"file"` 不是枚举值 |
| 上下文 / 最大输出 | `limit: { "context": N, "output": M }`（两项都必填） | `context_length`、`max_output_tokens` |
| 是否支持推理 | `reasoning`: `true` / `false` | — |

`modalities` 枚举**仅允许**：`text` | `audio` | `image` | `video` | `pdf`。  
厂商文档写「文件」时映射为 `pdf`。

### 补全模板

```jsonc
"model-id": {
  "name": "model-id",
  "attachment": true,
  "modalities": {
    "input": ["text", "image"],
    "output": ["text"]
  },
  "limit": {
    "context": 128000,
    "output": 8192
  },
  "reasoning": true
}
```

## 本机已核对的模型（参考，以 models.dev / 官方为准）

恢复时仍应重新查询；下表仅作对照，模型升级后数字可能变化。

| 模型 ID | 输入 | 输出 | context | output | reasoning | attachment | 来源 |
|---|---|---|---|---|---|---|---|
| `glm-5.3-flash` | text, image, video, pdf | text | 1,000,000 | 131,072 | true | true | models.dev / 智谱：1M 上下文、128K 输出、思考不可关、原生多模态 |
| `grok-4.6` | text, image, pdf | text | 500,000 | 500,000 | true | true | models.dev / xAI：500K 上下文、无输出上限、reasoning 不可关 |

当前本机对应关系（不含 Key）：

- 自定义供应商 `apikey`（显示名 Glm）→ `glm-5.3-flash`
- 自定义供应商 `apikey2`（显示名 Grok）→ `grok-4.6`
- `baseURL` 均为 `https://api.apikey.fun/v1`（Key 自行填写）
