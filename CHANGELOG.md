# Changelog / 更新日志

## v1.0.6
- Fix: popular subscription randomly samples from a deduped candidate pool to avoid repeats and empty sends.
  修复: 热门订阅从候选池去重后随机抽取，避免重复并减少无内容可发的情况。

## v1.0.5
- Fix: dedupe queue only records successfully sent post IDs.
  修复: 去重队列仅记录成功发送的帖子 ID。
- Feature: add dedupe table inspection command.
  新增: 去重表查看命令。
- Feature: add cache clear command with count and size output.
  新增: 缓存清理命令，返回清理数量与大小。
- Improve: popular command falls back to text output when preview images are unavailable.
  改进: 热门命令在预览图不可用时回退到文本输出。
- Fix: random posts bypass response cache to avoid repeats.
  修复: 随机帖子请求绕过缓存，避免重复。
- Improve: search results can include tags when display.show_tags is enabled.
  改进: 搜索结果在启用标签显示时输出标签。
- Improve: search and popular commands randomly sample results from the current page.
  改进: 搜索与热门命令在当前页随机抽取结果输出。
- Improve: popular and subscription messages show tags above the link.
  改进: 热门与订阅消息统一为标签在上、链接在下。

## v1.0.4
- Refactor: remove deprecated register decorator and switch to package-relative imports.
  重构: 移除废弃的 register 装饰器，改用包内相对导入。
- Refactor: ConfigManager uses logger and plugin data dir, plus async load/save helpers.
  重构: ConfigManager 改用 logger 与插件数据目录，并提供异步读写方法。
- Fix: replace print in event bus and log API errors via astrbot logger.
  修复: 事件总线使用 logger 记录异常，并通过 logger 输出 API 错误。

## v1.0.3
- Feature: proxy configuration for HTTP/HTTPS/SOCKS.
  新增: 代理配置，支持 HTTP/HTTPS/SOCKS。

## v1.0.2
- Feature: subscription dedupe with FIFO queue and configurable rounds.
  新增: 订阅去重采用 FIFO 队列，可配置保留轮数。

## v1.0.1
- Fix: send image + text using MessageEventResult to avoid MessageChain image issues.
  修复: 使用 MessageEventResult 发送图文，避免 MessageChain 图片问题。
- Fix: avoid sending video files directly; use preview image for video posts and include original link.
  修复: 不直接发送视频文件；视频帖使用预览图并附原始链接。
- Fix: search results skip posts without accessible images and paginate to fill requested count.
  修复: 搜索结果跳过不可访问图片，并分页补足数量。
- Improve: popular command uses search_limit and can send image+text results.
  改进: 热门命令遵循 search_limit，并支持图文返回。
- Feature: group subscriptions for tags and daily popular.
  新增: 群聊订阅标签更新与每日热门推送。
- Improve: popular subscription supports scale (day/week/month) and uses per-group scale in dispatch.
  改进: 热门订阅支持 scale (day/week/month)，并按群聊配置发送。
- Change: default display.search_limit is now 1.
  变更: display.search_limit 默认值调整为 1。
- Improve: subscription storage uses AstrBot SharedPreferences.
  改进: 订阅数据改为使用 AstrBot SharedPreferences 存储。
- Refactor: centralized batch limit logic in config.
  重构: 批量 limit 逻辑集中到配置层统一处理。
- Improve: subscription interval uses minutes (default 120) for all subscriptions; popular follows same cooldown.
  改进: 订阅队列发送/轮询间隔改为分钟配置（默认 120），热门订阅使用同一冷却。
- Improve: search_limit now caps all batch/list commands.
  改进: search_limit 覆盖所有批量/列表类命令。
- Improve: tags are no longer truncated; formatted with line breaks.
  改进: 标签不再截断，使用换行格式化。
- Improve: configurable search result count via display.search_limit.
  改进: 通过 display.search_limit 配置搜索结果数量。
- Improve: test script saves images, adds golden-post access check, and includes video preview test.
  改进: 测试脚本保存图片，加入 golden-post 权限检查并覆盖视频预览测试。

## v1.0.0
- Initial release of the Danbooru API plugin with command handlers and test tooling.
  初始版本发布，包含核心命令处理与测试工具。
