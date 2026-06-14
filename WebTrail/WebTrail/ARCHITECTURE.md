# WebTrail 模块架构说明书

## 工程总览

```
WebTrail/
│
├─ Layer 0: 配置与模型 ──────────────────────────────────
│   ├── config.py         集中配置中心
│   └── models.py         数据模型定义
│
├─ Layer 1: 基础设施 ──────────────────────────────────────
│   └── utils/
│       ├── time.py       时间戳转换
│       └── sqlite.py     SQLite 安全读取
│
├─ Layer 2a: 痕迹提取 ────────────────────────────────────
│   └── extraction/
│       ├── base.py        抽象基类
│       ├── chromium.py    Chromium 提取器
│       ├── firefox.py     Firefox 提取器
│       └── system.py      系统级提取器
│
├─ Layer 2b: 智能分析 ────────────────────────────────────
│   └── analysis/
│       ├── engine.py      分析编排器（主入口）
│       ├── classifier.py  内容分类（阶段1）
│       ├── session.py     会话重建（阶段2）
│       ├── velocity.py    速度检测（阶段2）
│       ├── profiler.py    用户画像（阶段3）
│       └── risk.py        风险评估（阶段5）
│
├─ Layer 2c: 报告展示 ────────────────────────────────────
│   └── reporting/
│       ├── report.py      取证报告生成
│       └── formatter.py   分析报告格式化
│
├─ Layer 3: 入口 ─────────────────────────────────────────
│   ├── main.py            CLI 命令行入口
│   ├── gui.py             GUI 图形界面
│   └── __init__.py        包导出声明
│
└── README.md              用户文档
```

---

## Layer 0 — 配置与模型

### `config.py` — 集中配置中心

| 配置项 | 说明 |
|--------|------|
| `CHROMIUM_BROWSERS` | 5 款 Chromium 内核浏览器的 User Data 路径 |
| `FIREFOX_PROFILES_DIR` | Firefox Profiles 目录路径 |
| `BROWSER_EXECUTABLES` | 浏览器主程序名列表（用于 UserAssist 过滤） |
| `PREFETCH_BROWSER_PREFIXES` | 浏览器 Prefetch 文件名前缀 |
| `SUSPICIOUS_KEYWORDS` | 30+ 中英文可疑关键词（密码/token/exploit/hack...） |
| `SUSPICIOUS_DOMAINS` | 已知可疑域名列表 |
| `SEARCH_ENGINE_PATTERNS` | 11 个搜索引擎 URL 模式 + 查询参数名 |
| `SEARCH_TOPIC_RULES` | 16 条正则规则，将搜索词映射到 16 个主题 |
| `DOMAIN_CATEGORY_RULES` | 120+ 条正则规则，将域名归入 20+ 类别 |
| `HIGH_RISK_URL_PATTERNS` | 8 条高风险 URL 模式（暗网/Pastebin/MEGA/破解/恶意软件...） |
| `TRACKER_DOMAINS` | 25 个追踪/广告域名 |
| `SESSION_GAP_SECONDS` | 会话分割阈值（1800s = 30分钟） |
| `AUTOMATION_BURST_RATIO` | 自动化判定：快速跳转 >40% |
| `FORENSIC_INDICATORS` | 18 项取证指标定义（打击链阶段+确信度+风险轴） |
| `RISK_LEVELS` | 三级风险阈值（70/40/0） |

### `models.py` — 数据模型

| 模型 | 说明 |
|------|------|
| `Trace` | 单条取证痕迹（@dataclass, `slots=True`）— type/source/content/time/time_str/suspicious |
| `AnalysisResult` | 完整分析结果聚合体 — 涵盖风险概览、取证发现清单、分轴得分、杀伤链覆盖、搜索行为、会话、画像、统计等全部字段 |

---

## Layer 1 — 基础设施

### `utils/time.py` — 时间戳转换

| 函数 | 输入 | 输出 | 用途 |
|------|------|------|------|
| `filetime_to_datetime` | Windows FILETIME（8字节小端） | `datetime` | UserAssist 注册表 |
| `chrome_time_to_dt` | Chromium 微秒（1601纪元） | `datetime` | History/downloads/cookies 表 |
| `firefox_time_to_dt` | Firefox PRTime 微秒（1970纪元） | `datetime` | moz_places 表 |

全部返回 `Optional[datetime]`，无效或零值返回 `None`。

### `utils/sqlite.py` — SQLite 安全读取

| 函数 | 说明 |
|------|------|
| `read_sqlite_copy(db_path)` | 将 DB 复制为临时文件再打开连接，返回 `(conn, tmp_path)` |

调用方负责 `conn.close()` 后 `os.remove(tmp)`。避免与运行中浏览器的文件锁冲突。

---

## Layer 2a — 痕迹提取

### `extraction/base.py` — 抽象基类

定义提取器统一契约：
- `extract()` → `List[Trace]`（抽象方法，子类必须实现）
- `_safe_sqlite()` → 调用 `utils.read_sqlite_copy` 的便捷封装

### `extraction/chromium.py` — Chromium 提取器

**覆盖浏览器：** Chrome / Edge / Brave / Opera / 360安全浏览器

**提取维度（每浏览器 × 每 Profile）：**

| 维度 | 数据源 | 说明 |
|------|--------|------|
| 浏览历史 | `History` SQLite → `urls` 表 | 最近 200 条 |
| 书签 | `Bookmarks` JSON 文件 | 递归遍历 roots |
| 下载 | `History` → `downloads` 表 | 含文件大小和状态 |
| Cookie | `Cookies` SQLite → `cookies` 表 | 按域名聚合 Top 50 |
| 登录凭据 | `Login Data` → `logins` 表 | 按域名统计（不取明文） |
| 会话 | `Sessions/` 目录 | 文件时间戳 |
| 扩展 | `Extensions/` 目录 | 解析 manifest.json |

辅助方法：`_list_profiles()` 读取 Local State 获取 Profile 列表，`_walk_bookmarks()` 递归遍历书签树。

### `extraction/firefox.py` — Firefox 提取器

**覆盖浏览器：** Mozilla Firefox

**提取维度：**

| 维度 | 数据源 | 说明 |
|------|--------|------|
| 浏览历史 | `places.sqlite` → `moz_places` | 最近 200 条 |
| 书签 | `moz_bookmarks` | 按 dateAdded 倒序 |
| 下载 | `moz_annos` | 文件属性 |
| Cookie | `cookies.sqlite` → `moz_cookies` | 域名聚合 |
| 登录凭据 | `logins.json` | 统计 totalPasswords |
| 扩展 | `extensions.json` | addons.activeAddons |

### `extraction/system.py` — 系统级提取器

不依赖浏览器内部数据库，从 Windows 系统层面提取痕迹。

| 维度 | 数据源 | 关键技术 |
|------|--------|----------|
| UserAssist | `HKCU\...\UserAssist\{GUID}\Count` | ROT13 解码 + FILETIME 转换 |
| DNS 缓存 | `ipconfig /displaydns` | 过滤内网/系统 DNS |
| Prefetch | `C:\Windows\Prefetch\*.pf` | 文件修改时间 |

**注意事项：** DNS 缓存需管理员权限；Prefetch 仅 NTFS + Superfetch 启用时有效。

---

## Layer 2b — 智能分析

### `analysis/engine.py` — 分析编排器（主入口）

串联 5 阶段流水线，一次调用 `analyze(traces)` 完成全流程。

```
阶段1: 分类    → classifier.extract_search_queries / domain_categories
阶段2: 时序    → session.reconstruct / velocity.detect
阶段3: 画像    → profiler.build
阶段4: 统计    → classifier.top_domains / browsing_hours / download_risk / tracker_privacy
阶段5: 风险评估 → risk.score（接收全量 intermediate dict）
```

辅助函数 `_assign_fields(obj, data)` 将子模块返回的 dict 映射到 `AnalysisResult` 同名字段。

### `analysis/classifier.py` — 内容分类（阶段1）

对原始痕迹进行文本级分类，供后续模块消费：

| 函数 | 功能 |
|------|------|
| `extract_url(content)` | 从展示文本中提取 http(s) URL |
| `extract_domain(url)` | 解析域名（去掉 www. 前缀） |
| `classify_search_topic(kw)` | 搜索词 → 16 个主题之一 |
| `extract_search_queries(traces)` | 从浏览历史 URL 反解唯一搜索词 |
| `domain_categories(traces)` | 按 120+ 规则对浏览域名分类 |
| `top_domains(traces)` | Top 20 域名计数 |
| `browsing_hours(traces)` | 24 小时柱状分布 + 深夜占比 |
| `download_risk(traces)` | 下载风险评估（含可执行文件统计） |
| `tracker_privacy(traces)` | 追踪/广告域名请求计数 |

**输出字段：** `search_queries` / `category_distribution` / `top_domains` / `hour_distribution` / `download_risky` / `tracker_count` 等。

### `analysis/session.py` — 会话重建（阶段2）

将浏览历史按时间间隔分组为逻辑会话（连续间隔 ≤ 1800 秒）。

**算法：** 线性扫描，相邻记录间隔 > `SESSION_GAP_SECONDS` 则切分新会话。

**输出字段：** `session_count` / `total_browse_min` / `avg_session_min` / `max_session_min` / `long_sessions` / `short_sessions`。

### `analysis/velocity.py` — 浏览速度检测（阶段2）

检测异常快速跳转——可能为自动化脚本行为。

**关键指标：**
- `avg_gap_sec` — 相邻浏览平均间隔
- `burst_ratio` — 快速跳转占比（间隔 < 平均值/5 或 < 1.5s 的占比）
- `rapid_streaks` — 连续快速跳转段长度列表
- `automated_suspect` — 综合判定（burst_ratio > 40% 或最大 streak > 10）

### `analysis/profiler.py` — 用户画像（阶段3）

基于浏览器使用模式构建多维度行为画像：

| 维度 | 判定规则 |
|------|----------|
| 浏览器多样性 | 浏览器 ≥3 → "多浏览器用户" |
| 扩展偏好 | 扩展 ≥15 → "扩展重度用户" |
| 兴趣倾向 | 域名分类 Top 类别 |
| 下载习惯 | 下载总数 ≥50 → "频繁下载" |
| 账户行为 | 凭据站点 ≥20 → "高在线账户" |
| 浏览时段 | 深夜占比 >30% → "重度深夜活跃" |

### `analysis/risk.py` — 数字取证风险评估（阶段5）

**方法论：** NIST SP 800-86 + Cyber Kill-Chain 模型

**处理流程（4 阶段）：**

| 阶段 | 函数 | 功能 |
|------|------|------|
| 证据采集 | `_collect_evidence()` | 遍历痕迹，按 18 项 `FORENSIC_INDICATORS` 逐项命中 |
| 确信度评估 | `_assess_confidence()` | 上下文联动提升（如 搜索+下载→HIGH） |
| 杀伤链映射 | `_map_kill_chain()` | 按 7 阶段聚合 + 交叉验证（≥3 条独立证据） |
| 评分开具 | `_compute_score()` | 证据等级权重 × 命中数 + 交叉验证加成 |

**证据确信度三级：**

| 等级 | 权重 | 含义 |
|------|------|------|
| HIGH | 25 分 | 可直接作为取证依据（已知恶意域名、工具签名） |
| MEDIUM | 15 分 | 行为模式高度偏离基线，需结合上下文 |
| LOW | 5 分 | 弱信号，仅作佐证参考 |

**4 维风险轴：** 攻击工具与武器化 / 侦查与信息收集 / 凭证窃取与持久化 / 反取证与隐匿

**交叉验证：** 同一杀伤链阶段出现 ≥3 条独立证据 → 额外 +10 分。

**输出字段：** `risk_score` / `risk_level` / `risk_summary` / `findings` / `finding_stats` / `axis_scores` / `kill_chain_coverage`。

---

## Layer 2c — 报告展示

### `reporting/report.py` — 取证报告生成

| 函数 | 功能 |
|------|------|
| `_mark_suspicious(traces)` | 根据 `SUSPICIOUS_KEYWORDS/DOMAINS` 设置 `trace.suspicious` 标志位 |
| `_build_summary(traces)` | 按类型/来源聚合，列出可疑内容 |
| `generate(traces)` | 输出完整时间线报告，按 time 倒序排列 |

**输出格式：** 取证摘要 → 按类型统计 → 按来源统计 → 可疑痕迹列表 → 浏览时间线（含 **!!可疑!!** 标记）。

### `reporting/formatter.py` — 分析报告格式化

将 `AnalysisResult` 渲染为 Markdown 风格纯文本，包含 8 个章节：

1. 取证风险评定 — 总分 / 等级 / 结论
2. 风险维度分解 — 4 轴分项得分条形图
3. 证据统计 — HIGH/MEDIUM/LOW 计数 + 交叉验证
4. 取证发现清单 — 逐项明细（●确信度图标 + 得分 + 杀伤链阶段 + 细节）
5. 杀伤链覆盖矩阵 — 7 阶段 [×]/[ ] 覆盖标记
6. 行为画像 — 浏览器生态 / 扩展 / 兴趣 / 下载 / 账户
7. 搜索行为分析 — 引擎分布 / 主题分布 / 最近搜索
8. 会话重建 / 速度检测 / 24h 分布 / Top 域名 / 下载风险 / 隐私追踪

---

## Layer 3 — 入口

### `main.py` — CLI 命令行入口

| 参数 | 简写 | 说明 |
|------|------|------|
| `--output` | `-o` | 保存报告到文件 |
| `--json` | | 导出原始数据为 JSON |
| `--quiet` | `-q` | 静默模式（仅摘要） |
| `--gui` | `-g` | 启动图形界面 |

**流程：** 解析参数 → 启动三路提取器 → 生成报告 → 智能分析 → 输出/保存。

### `gui.py` — 图形界面

tkinter 构建，蓝白主题。
- 标题栏 + 统计摘要栏（痕迹数/可疑数/浏览器数/风险分）
- 双 Tab（取证报告 / 取证分析）
- 线程化提取（不阻塞 UI），支持中途停止
- 保存 TXT / 导出 JSON

### `__init__.py` — 包导出

对外暴露 6 个顶层符号：`ChromiumExtractor` / `FirefoxExtractor` / `SystemExtractor` / `analyze` / `generate` / `format_analysis`。
