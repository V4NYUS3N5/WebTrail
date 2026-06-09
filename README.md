TraceFinder 无痕用户行为取证关联分析工具
工具简介
TraceFinder 是一款面向数字取证场景的 Windows 系统痕迹提取工具。与传统取证工具仅覆盖**显式留痕**（注册表、系统日志、浏览器历史）不同，本工具聚焦**用户以为"不会留痕"的隐式痕迹**，自动关联生成用户行为时间线。
核心能力
| 能力 | 说明 |
|------|------|
| 无痕浏览器痕迹提取 | 通过 UserAssist 注册表 + DNS 缓存 + Prefetch 文件，还原无痕模式下的浏览器运行记录 |
| 剪贴板历史提取 | 读取 Windows 剪贴板历史数据库，获取复制过的文本内容 |
| 系统通知历史提取 | 提取通知中心数据库中的微信/QQ 消息预览、下载通知等 |
| 社交软件非聊天痕迹 | 提取微信/QQ 缓存目录中的文件接收记录、头像缓存等 |
| 基础痕迹提取 | USB 接入记录、最近运行程序、自启动项、Recent 文件、Prefetch 记录 |
| 智能关联分析 | 自动按时间排序所有痕迹，标记 3 类可疑行为 |
可疑行为标记规则
1. U盘 + 文件操作：U盘插入后 1 分钟内有文件复制/上传操作
2. 浏览器 + 网盘访问：无痕浏览器运行后 10 分钟内有网盘/邮箱访问痕迹
3. 敏感词 + 文件传输：剪贴板复制敏感关键词（机密/合同/密码等）后有文件传输操作
环境要求
操作系统：Windows 10 / Windows 11
Python 版本：Python 3.7+
权限要求：普通用户权限即可运行（USB 记录提取需要管理员权限）
安装与运行
1. 安装依赖
bash
cd TraceFinder
pip install -r requirements.txt
2. 运行工具
方式一：直接运行 main.py
bash
python TraceFinder/main.py
方式二：作为模块运行
bash
python -m TraceFinder.main
命令参数
bash
完整提取（默认）
python TraceFinder/main.py
保存报告到文本文件
python TraceFinder/main.py -o report.txt
导出 JSON 格式数据
python TraceFinder/main.py --json output.json
同时保存文本和 JSON
python TraceFinder/main.py -o report.txt --json output.json
仅提取特定模块
python TraceFinder/main.py -m clipboard    # 仅剪贴板历史
python TraceFinder/main.py -m browser     # 仅浏览器痕迹
python TraceFinder/main.py -m notification # 仅系统通知
python TraceFinder/main.py -m social      # 仅社交软件痕迹
python TraceFinder/main.py -m basic       # 仅基础痕迹
静默模式（仅输出最终报告）
python TraceFinder/main.py -q
参数说明
| 参数 | 简写 | 说明 |
|------|------|------|
| `--output` | `-o` | 保存报告到指定文件 |
| `--json` | | 导出 JSON 格式数据到指定文件 |
| `--module` | `-m` | 指定提取模块（clipboard/browser/notification/social/basic/all） |
| `--quiet` | `-q` | 静默模式，仅输出最终报告 |
项目结构
TraceFinder/
├── __init__.py              # 包初始化
├── main.py                  # 主程序入口（CLI 接口）
├── utils.py                 # 公共工具函数（FILETIME 转换等）
├── clipboard_extractor.py   # 剪贴板历史提取模块
├── browser_extractor.py     # 无痕浏览器痕迹提取模块
├── notification_extractor.py # 系统通知历史提取模块
├── social_extractor.py      # 社交软件非聊天痕迹提取模块
├── basic_extractor.py       # 基础痕迹提取模块
├── timeline_analyzer.py     # 时间线关联与可疑标记模块
└── requirements.txt         # 依赖列表
各模块提取位置说明

| 模块 | 数据来源 | 路径/注册表键 |
|------|---------|--------------|
| 剪贴板历史 | SQLite 数据库 | `%LOCALAPPDATA%\Microsoft\Windows\Clipboard\history.db` |
| 浏览器痕迹 | 注册表 + DNS + Prefetch | `UserAssist` 注册表键、`ipconfig /displaydns`、`C:\Windows\Prefetch` |
| 系统通知 | SQLite 数据库 | `%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db` |
| 微信痕迹 | 文件目录 | `%USERPROFILE%\Documents\WeChat Files\` |
| QQ痕迹 | 文件目录 | `%USERPROFILE%\Documents\Tencent Files\` |
| USB记录 | 注册表 | `HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR` |
| 最近运行 | 注册表 | `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU` |
| 自启动项 | 注册表 | `HKCU/HKLM\Software\Microsoft\Windows\CurrentVersion\Run` |
| 最近文件 | 快捷方式目录 | `%APPDATA%\Microsoft\Windows\Recent\` |
| Prefetch | 预读取文件 | `C:\Windows\Prefetch\*.pf` |
常见问题
Q: 为什么某些模块提取到 0 条记录？
A: 可能原因：
- 剪贴板历史：需要在 Windows 设置中开启"剪贴板历史"功能
- 系统通知：数据库可能不存在或无通知记录
- 社交软件：未安装微信/QQ 或缓存目录路径不同
Q: 为什么显示"未提取到有时间戳的痕迹"？**
A: DNS 缓存和注册表记录本身没有精确时间戳。要看到完整时间线，需要系统中有 Prefetch 文件、Recent 文件或剪贴板历史等带时间戳的痕迹。
Q: 需要管理员权限吗？**
A: 大部分功能普通用户权限即可运行。仅 USB 设备记录提取需要管理员权限（读取 `HKLM` 注册表）。
Q: 工具会破解微信/QQ 聊天记录吗？**
A: 不会。本工具仅提取系统级公开痕迹（通知预览、文件缓存等），不碰加密的聊天数据库，符合取证规范。
技术说明
所有痕迹提取均基于系统公开接口和文件，不涉及破解或绕过安全机制
数据库读取采用复制临时文件方式，避免占用原文件锁
FILETIME 时间格式转换兼容 Windows 系统时间戳格式
支持两种运行方式（直接运行 / 模块运行），兼容不同使用场景
