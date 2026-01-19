# Changelog / 更新日志

## v1.0.1
- Fix: send image + text using MessageEventResult to avoid MessageChain image issues.
  修复: 使用 MessageEventResult 发送图文，避免 MessageChain 图片问题。
- Fix: avoid sending video files directly; use preview image for video posts and include original link.
  修复: 不直接发送视频文件；视频帖使用预览图并附原始链接。
- Fix: search results skip posts without accessible images and paginate to fill requested count.
  修复: 搜索结果跳过不可访问图片，并分页补足数量。
- Improve: tags are no longer truncated; formatted with line breaks.
  改进: 标签不再截断，使用换行格式化。
- Improve: configurable search result count via display.search_limit.
  改进: 通过 display.search_limit 配置搜索结果数量。
- Improve: test script saves images, adds golden-post access check, and includes video preview test.
  改进: 测试脚本保存图片，加入 golden-post 权限检查并覆盖视频预览测试。

## v1.0.0
- Initial release of the Danbooru API plugin with command handlers and test tooling.
  初始版本发布，包含核心命令处理与测试工具。
