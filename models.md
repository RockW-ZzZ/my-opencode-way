# 自定义供应商模型参数

> 本仓库**不备份** provider 的 API Key / `auth.json`。新机自行接入自定义供应商后，
> 必须扫描配置里的模型 ID，按官方参数补全 `modalities` / `limit` / `reasoning` / `variants`。
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
   - `variants`：若 models.dev 该模型带 `reasoning_options`（`type: "effort"`），
     把它的 `values` 转成推理档位（见下「推理档位 `variants`」）。
5. models.dev 未命中时，再查厂商官方文档（智谱 docs.bigmodel.cn、xAI docs.x.ai、OpenAI 等）。
6. 写入前对照 [opencode 配置 schema](https://opencode.ai/config.json) 校验。
7. 保存后**退出并重启 opencode**（配置启动时一次性加载）。

### 合法字段（schema 强制）

模型对象 `additionalProperties: false`，写错字段会导致 opencode **无法启动**。

| 要改的能力 | 合法字段 | 非法写法（禁止） |
|---|---|---|
| 输入/输出类型 | `modalities.input` / `modalities.output` | `"file"` 不是枚举值 |
| 上下文 / 最大输出 | `limit: { "context": N, "output": M }`（两项都必填） | `context_length`、`max_output_tokens` |
| 是否支持推理（V1） | `reasoning`: `true` / `false` | — |
| 推理强度档位 | `variants`（V1 对象 / V2 数组，见下） | — |

`modalities` 枚举**仅允许**：`text` | `audio` | `image` | `video` | `pdf`。  
厂商文档写「文件」时映射为 `pdf`。

#### 推理档位 `variants`

V1 是**对象**、V2 是**数组**（opencode V2 会自动把 V1 对象迁移成数组）：

```jsonc
// V1（opencode 1.x）
"variants": { "high": { "reasoningEffort": "high" } }

// V2 原生
"variants": [ { "id": "high", "settings": { "reasoningEffort": "high" } } ]
```

> ⚠️ **opencode V2 行为**（2026-09 实测）：
> - V2 **忽略** V1 的 `reasoning` / `attachment`（启动日志报 `kind=unsupported … omitted`）。
>   对不在 models.dev 目录里的自定义模型，只写 `reasoning: true` 在 V2 **不会**让模型具备推理能力；
>   要让它支持推理 / 选择强度，用 `variants`（带 `reasoningEffort`）。
> - provider / model 条目内部**不能混用 V1 与 V2 字段**，否则整个 provider 会被判为
>   `kind=invalid … skipped malformed recognized value` 而**被跳过**（该供应商的模型全部消失）。

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
  "reasoning": true,
  "variants": {
    "low": { "reasoningEffort": "low" },
    "medium": { "reasoningEffort": "medium" },
    "high": { "reasoningEffort": "high" }
  }
}
```

> `variants` 只在模型支持推理档位时写；档位取值以 models.dev 的 `reasoning_options` 为准。

## 本机已核对的模型（参考，以 models.dev / 官方为准）

恢复时仍应重新查询；下表仅作对照，模型升级后数字可能变化。

| 模型 ID | 输入 | 输出 | context | output | reasoning | 推理档位 | attachment | 来源 |
|---|---|---|---|---|---|---|---|---|
| `glm-5.3-flash` | text, image, video, pdf | text | 1,000,000 | 131,072 | true | —（不可关） | true | models.dev / 智谱：1M 上下文、128K 输出、思考不可关、原生多模态 |
| `grok-4.7` | text, image, pdf | text | 500,000 | 500,000 | true | —（不可关） | true | models.dev / xAI：500K 上下文、无输出上限、reasoning 不可关 |
| `deepseek-v4.1-flash` | text, image | text | 1,000,000 | 384,000 | true | low / high / max | true | models.dev / DeepSeek：1M 上下文、输出上限 393,216（本机取 384K）；`reasoning_options` 另有 toggle |
| `gpt-6-astra` | text, image, pdf | text | 272,000（官方 1,050,000） | 128,000 | true | low / medium / high / xhigh / max | true | models.dev / OpenAI：官方 1.05M 上下文、128K 输出；本机 context 按用户设定取 272K |
| `gpt-6-sol` | text, image, pdf | text | 272,000（官方 1,050,000） | 128,000 | true | none / low / medium / high / xhigh / max | true | 同上 |
| `gpt-5.6-sol` | text, image, pdf | text | 272,000（官方 1,050,000） | 128,000 | true | none / low / medium / high / xhigh / max | true | 同上 |

> 表中 `reasoning` / `attachment` 是 V1 字段，opencode V2 会忽略它们（见上「推理档位 `variants`」）。
> 推理档位来自 models.dev 的 `reasoning_options`，已写进配置的 `variants`。

当前本机对应关系（不含 Key）：

- 自定义供应商 `apikey3`（显示名 deepseek）→ `deepseek-v4.1-flash`（含推理档位 `variants`）
- 自定义供应商 `apikey4`（显示名 gpt）→ `gpt-6-astra` / `gpt-6-sol` / `gpt-5.6-sol`（均含推理档位 `variants`）
- 已移除：`apikey1`（Grok / grok-4.7）、`apikey2`（GLM / glm-5.3-flash）
- `baseURL` 均为 `https://api.apikey.fan/v1`（Key 自行填写）
