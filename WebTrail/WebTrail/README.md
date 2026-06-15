# WebTrail - 浏览器数字取证与用户画像工具

**纯 Python 标准库实现，零第三方依赖，开箱即用。**

对 Chrome / Firefox / Microsoft Edge 的本地浏览数据进行司法级提取，生成时间线、域名排行、行为热力图与风险指标，输出结构化 JSON/CSV 取证报告。

---

## 功能概览

| 维度 | 能力 |
|------|------|
| **痕迹提取** | 浏览历史、Cookie、下载记录、书签、登录凭证、HSTS / 缓存元信息 |
| **浏览器支持** | Google Chrome、Microsoft Edge（Chromium 内核）、Mozilla Firefox |
| **取证保障** | 只读访问、证据文件 SHA-256 链式保管、记录级哈希完整性 |
| **画像分析** | 24 小时活跃热力图、TOP 域名排名、URL 语义分类、风险指标检测 |
| **报告输出** | JSON（含元数据哈希）、CSV 记录表、CSV 时间线、报告本身哈希校验 |

## 快速开始

```bash
# 命令行全量分析
python main.py

# 仅分析 Chrome
python main.py --browser Chrome

# 指定输出目录
python main.py --output D:/cases/001

# 跳过画像，仅提取痕迹
python main.py --no-profile

# 图形界面
python main.py --gui
```

## 项目结构

```
WebTrail/
├── main.py                 # CLI 入口（83 行）
├── config.py               # 跨平台配置
├── core/                   # 核心引擎
│   ├── extractor.py        # 基类 + 数据结构
│   ├── pipeline.py         # 三阶段取证管道
│   ├── hasher.py           # SHA-256 哈希校验
│   ├── profiler.py         # 用户画像分析
│   └── timeline.py         # 时间线构建
├── browsers/               # 浏览器适配器
│   ├── chrome.py           # Chrome（212 行）
│   ├── edge.py             # Edge 继承 ChromeExtractor（18 行）
│   └── firefox.py          # Firefox（199 行）
├── gui/                    # 图形界面
│   └── app.py              # tkinter GUI（480 行）
├── output/
│   └── writer.py           # JSON/CSV 报告生成
└── utils/                  # 工具库
    ├── sqlite_utils.py     # 安全 SQLite 连接
    ├── time_utils.py       # 时间戳转换
    └── url_utils.py        # 域名提取与分类
```

## 取证科学性

- **不修改原始证据** — 所有 SQLite 连接 `mode=ro` + `PRAGMA query_only=ON`，浏览器运行中也能通过 `copy_to_temp` 安全读取
- **链式保管** — 提取前对全部 `.sqlite`/`.json` 证据文件计算 SHA-256，记录于报告元数据
- **记录级完整性** — 每条 `ArtifactRecord` 包含 `checksum` 字段，可独立校验
- **时间戳保真** — 保留原始 ISO 8601 时间戳，不做截断或时区转换

## 提取数据类型

| 类型 | Chrome/Edge | Firefox |
|------|-------------|---------|
| 浏览历史 | `History` SQLite | `places.sqlite` |
| Cookie | `Network/Cookies` | `cookies.sqlite` |
| 下载记录 | `History` SQLite | `places.sqlite`（moz_annos） |
| 书签 | `Bookmarks` JSON | `places.sqlite`（moz_bookmarks） |
| 登录凭证 | `Login Data` SQLite | `logins.json` |
| 缓存/HSTS | `TransportSecurity` / `Cache_Data` | `cache2/` |

## 画像分析维度

- **活跃时段** — 24 小时热力图 + 按日活跃统计
- **域名排行** — TOP 20 访问域名
- **语义分类** — 社交媒体、搜索引擎、视频、购物、邮箱、技术开发、新闻、云存储 8 类
- **风险指标** — 隐私模式痕迹推断、历史清除检测、可疑域名关键词匹配

## 运行环境

- Python 3.9+
- Windows / macOS / Linux
- 无需安装任何第三方包
