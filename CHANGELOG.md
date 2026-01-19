# Changelog / 更新日志

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
