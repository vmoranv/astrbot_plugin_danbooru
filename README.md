# AstrBot Danbooru 插件

[![文档](https://img.shields.io/badge/AstrBot-%E6%96%87%E6%A1%A3-blue)](https://astrbot.app)
[![aiohttp](https://img.shields.io/pypi/v/aiohttp.svg)](https://pypi.org/project/aiohttp/)
[![license](https://img.shields.io/github/license/vmoranv/astrbot_plugin_danbooru.svg)](https://github.com/vmoranv/astrbot_plugin_danbooru)
[![stars](https://img.shields.io/github/stars/vmoranv/astrbot_plugin_danbooru.svg?style=social)](https://github.com/vmoranv/astrbot_plugin_danbooru)

![:@astrbot_plugin_danbooru](https://count.getloli.com/get/@astrbot_plugin_danbooru?theme=booru-lewd)

这是一个为 [AstrBot](https://astrbot.app) 开发的 Danbooru 插件，让你在聊天中快速搜索、浏览和管理 Danbooru 内容。

仓库地址：`https://github.com/vmoranv/astrbot_plugin_danbooru`

## ✨ 核心特性

- 🔎 **多种搜索方式**：主命令按 tag 搜索、帖子详情、随机与热门
- 🧩 **全量 API 封装**：友好命令 + 原始 API + 微服务调用
- 🧠 **事件驱动**：请求/响应/错误事件统一分发
- 🧰 **强可配置**：R18 过滤、评分限制、缓存、显示策略一键配置
- 🖼️ **图文合并输出**：可配置文字+图片同条消息，支持大图/原图
- ⚙️ **测试脚本**：脚本化跑全量命令，结果落盘可复查

### 配置字段说明

#### api

- `api.base_url`: 主站 API 地址。
- `api.test_url`: 测试站 API 地址。
- `api.use_test_server`: 是否使用测试站（建议先开）。
- `api.timeout`: 请求超时（秒）。
- `api.max_retries`: 失败后最大重试次数。
- `api.retry_delay`: 重试间隔（秒）。
- `api.rate_limit_per_second`: 全局速率限制（每秒请求数）。

#### auth

- `auth.username`: 用户名。
- `auth.api_key`: API Key。

#### cache

- `cache.enabled`: 是否启用缓存。
- `cache.ttl_seconds`: 缓存有效期（秒）。
- `cache.max_size`: 最大缓存条目数。
- `cache.cache_posts`: 是否缓存帖子。
- `cache.cache_tags`: 是否缓存标签。
- `cache.cache_artists`: 是否缓存艺术家。
- `cache.cache_users`: 是否缓存用户。

#### filter

- `filter.allowed_ratings`: 允许的分级列表。
  - `g` (general)：普通/全年龄
  - `s` (sensitive)：轻度敏感/擦边
  - `q` (questionable)：可疑、较明显的性内容
  - `e` (explicit)：明确的成人内容
- `filter.allowed_ratings` 由四个布尔开关组成，未勾选的分级会被排除；若全未勾选会回退为 `g/s`。
- `filter.blocked_tags`: 屏蔽标签（会自动加上 `-tag`）。
- `filter.required_tags`: 必需标签（自动追加到搜索条件）。
- `filter.min_score`: 最低评分（0 表示不限制），会追加 `score:>=N`。
- `filter.max_results`: 命令结果最大返回数上限。

#### display

- `display.show_preview`: 是否附带预览图（文字+图片合并一条消息）。
- `display.only_image`: 仅返回图片，不返回文字。
- `display.preview_size`: 图片尺寸选择（下拉可选 `preview` / `sample` / `original`）。
- `display.show_tags`: 是否显示标签。
- `display.max_tags_display`: 每行最大显示标签数量（0=自动换行）。
- `display.show_source`: 是否显示来源。
- `display.show_artist`: 是否显示艺术家。
- `display.show_score`: 是否显示评分。
- `display.language`: 语言（下拉可选 `zh-CN` / `en-US` / `ja-JP`）。

#### 其他开关

- `enable_commands`: 是否启用命令入口（关闭后 `/danbooru` 命令不可用）。
- `enable_llm_tools`: 是否启用 LLM 工具入口（关闭后禁用 `/danbooru api` 与 `/danbooru call`）。
- `enable_auto_tag`: 是否启用自动标签（批量 autocomplete + tag alias 同义词规范化）。
- `debug`: 是否启用调试日志（输出更详细的请求/缓存信息）。
- `log_api_calls`: 是否记录 API 调用日志（包含方法/端点/耗时，敏感字段已脱敏）。

### API Key 获取

1. 登录 `https://danbooru.donmai.us` 或 `https://testbooru.donmai.us`。
2. 进入个人主页，点击 “Generate API key”。
3. 将用户名与 API key 填入 `auth.username` / `auth.api_key`，或设置环境变量。
4. 请妥善保管，不要公开分享。

## 🧭 命令

### 主命令（按标签搜索）

- `/danbooru <tag>` 直接按标签搜索（等价于 `/danbooru posts <tag>`）

### 帖子相关

- `/danbooru post <id>` 获取帖子详情
- `/danbooru posts [tags] [--page N] [--limit N]` 搜索帖子
- `/danbooru posts <id>` 只输入数字时按 `id` 搜索
- `/danbooru random [tags]` 随机帖子
- `/danbooru popular [date] [--scale day|week|month]` 热门帖子

### 标签 / 艺术家 / 池

- `/danbooru tag <name>` 获取标签信息
- `/danbooru tags <query> [--category N] [--limit N]` 搜索标签
- `/danbooru related <tag>` 相关标签
- `/danbooru artist <name>` 艺术家信息
- `/danbooru artists <query>` 搜索艺术家
- `/danbooru pool <id>` 池详情
- `/danbooru pools [query]` 搜索池

### 用户 / Wiki / 评论

- `/danbooru user <id/name>` 用户信息
- `/danbooru favorites <user_id>` 收藏列表
- `/danbooru wiki <title>` Wiki 页面
- `/danbooru comments <post_id>` 帖子评论

### 其他

- `/danbooru autocomplete <query>` 自动补全
- `/danbooru count <tags>` 帖子计数
- `/danbooru status` 系统状态
- `/danbooru similar <post_id>` 相似图搜索

### 原始 API 与微服务入口

- `/danbooru api <METHOD> <endpoint> [key=value ...] [--json '{...}']`
- `/danbooru call <service> <method> [key=value ...]`
- `/danbooru call services`
- `/danbooru call methods <service>`

## 🧠 行为说明

- 搜索类命令会自动应用 `filter` 配置（分级过滤、必须/屏蔽标签、最低分数等）。
- `filter.allowed_ratings` 会自动转换为 `rating` 过滤。
- 当 `display.only_image=true` 时，搜索、随机和详情命令只返回图片，不返回文字描述。
- `preview_size` 控制发送的图片尺寸（优先匹配预览/样本/原图 URL）。
- `enable_auto_tag` 启用后，搜索/随机命令会批量规范化标签（autocomplete + tag alias）。

## 🧪 测试

使用 testbooru 跑全量命令覆盖测试：

```text
python scripts/test_commands.py
```

测试结果会写入 `scripts/test_results/<command>/`，每一步一个文件。

可选参数：

- `--only-image` 测试纯图片模式
- `--skip-main` 跳过主命令回退逻辑测试
- `--username` / `--api-key` 测试需要认证的命令

环境变量：

- `DANBOORU_USERNAME`
- `DANBOORU_API_KEY`

### 测试样例（test_commands.py 实际执行）

```text
/danbooru help posts
/danbooru post 10249
/danbooru posts non-web_source
/danbooru posts 10249
/danbooru random non-web_source
/danbooru popular
/danbooru tag non-web_source
/danbooru tags non-web_source
/danbooru related non-web_source
/danbooru artist artist_478882
/danbooru artists artist_478882
/danbooru pool 36
/danbooru pools "Touhou_-_Flandre's_Sherbet_((YsY)s)"
/danbooru user 613
/danbooru favorites 613
/danbooru wiki testing_something
/danbooru comments 10249
/danbooru autocomplete no
/danbooru count non-web_source
/danbooru status
/danbooru similar 10249
/danbooru api posts?limit=1
/danbooru call services
/danbooru call methods posts
/danbooru call posts list limit=1
/danbooru non-web_source
```

`--only-image` 模式会额外验证 `/danbooru post 10249` 是否返回图片。

## 🧩 开发与扩展

目录结构：

- `main.py`: 插件入口
- `core/`: 客户端、配置、模型、异常
- `services/`: API 服务层（微服务化）
- `commands/`: 命令处理与解析
- `events/`: 事件总线与事件类型

## 📝 备注

- 测试站建议：`https://testbooru.donmai.us`
- 若需要写操作（点赞、收藏、编辑等），需配置有效的账号与 API Key。
