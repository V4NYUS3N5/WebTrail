# WebTrail — 浏览器痕迹取证分析工具

Windows 平台数字取证工具，支持从 Chromium 内核浏览器（Chrome / Edge / Brave / Opera / 360）和 Firefox 中提取浏览痕迹，生成时间线报告并执行多维度智能分析。提供 CLI 和 GUI 两种运行模式。

## 功能概览

### 取证提取（7 维度 × 6 浏览器）
- 浏览历史（最近 200 条）
- 书签
- 下载记录
- Cookie 域名统计（Top 50）
- 登录凭据统计（不提取明文）
- 会话标签页
- 已安装扩展插件

### 系统级痕迹
- 浏览器启动记录（UserAssist 注册表）
- DNS 缓存记录
- Prefetch 预读取文件

### 智能分析（5 阶段流水线）
| 阶段 | 模块 | 产出 |
|------|------|------|
| 分类 | 搜索词提取 + 域名分类 | 搜索意图 / 兴趣分类雷达（20+ 类别） |
| 时序 | 会话重建 + 浏览速度检测 | 浏览会话 / 自动化行为甄别 |
| 画像 | 多维度用户画像 | 浏览器生态 / 兴趣倾向 / 搜索偏好 / 下载习惯 |
| 统计 | Top 域名 / 24h 分布 / 下载 / 追踪 | 统计摘要 |
| 评分 | 7 步加权风险评分 | 0-100 风险评分 + 逐项归因原因 |

## 运行方式

```bash
cd WebTrail

# 命令行模式
python main.py                  # 控制台输出完整报告
python main.py -q               # 静默模式（仅摘要）
python main.py -o report.txt    # 保存报告到文件
python main.py --json out.json  # 导出 JSON

# 图形界面模式
python main.py -g               # 启动 GUI
python gui.py                   # 直接启动 GUI
```

## 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--output` | `-o` | 保存报告到指定文件 |
| `--json` | | 导出 JSON 到指定文件 |
| `--quiet` | `-q` | 静默模式 |
| `--gui` | `-g` | 启动图形界面 |

## 环境要求

- Windows 10 / 11
- Python 3.10+
- 纯标准库，无需安装任何依赖

## 工程架构

```
WebTrail/
├── config.py                 ← 集中配置（浏览器路径 / 分类规则 / 风险权重）
├── models.py                 ← 数据模型（Trace / AnalysisResult @dataclass）
│
├── utils/                    ← 基础设施层
│   ├── time.py               ← 3 种时间戳转换
│   └── sqlite.py             ← SQLite 安全副本读取
│
├── extraction/               ← 提取层（ABC 基类 + 3 个实现）
│   ├── base.py               ← BaseExtractor 抽象类
│   ├── chromium.py           ← ChromiumExtractor（5 浏览器）
│   ├── firefox.py            ← FirefoxExtractor
│   └── system.py             ← SystemExtractor（UserAssist/DNS/Prefetch）
│
├── analysis/                 ← 分析层（5 子模块 + 编排器）
│   ├── engine.py             ← analyze() 流水线编排
│   ├── classifier.py         ← 搜索词提取 / 域名分类 / Top域名 / 时段 / 下载
│   ├── session.py            ← 会话重建
│   ├── velocity.py           ← 浏览速度 / 自动化检测
│   ├── profiler.py           ← 用户画像
│   └── risk.py               ← 7 步加权风险评分 + 归因
│
├── reporting/                ← 展示层
│   ├── report.py             ← 取证报告生成
│   └── formatter.py          ← 分析报告格式化
│
├── main.py / gui.py          ← CLI / GUI 双入口
└── README.md
```

## 支持的浏览器

| 浏览器 | 内核 | 提取维度 |
|--------|------|----------|
| Google Chrome | Chromium | 历史 / 书签 / 下载 / Cookie / 登录 / 会话 / 扩展 |
| Microsoft Edge | Chromium | 同上 |
| Brave | Chromium | 同上 |
| Opera | Chromium | 同上 |
| 360安全浏览器 | Chromium | 同上 |
| Mozilla Firefox | Gecko | 历史 / 书签 / 下载 / Cookie / 登录 / 扩展 |

## 风险评分说明

评分采用 7 步加权模型，每步设有上限：

| 步骤 | 因素 | 最高得分 | 判定条件 |
|------|------|----------|----------|
| 1 | 可疑关键词 | 30 分 | 敏感词（password/hack/exploit等）命中次数 |
| 2 | 高风险 URL | 30 分 | .onion / pastebin / crack / malware 等模式匹配 |
| 3 | 深夜浏览 | 15 分 | 00:00-05:00 浏览占比 >30% |
| 4 | 下载风险 | 15 分 | .exe/.msi 等可执行文件下载 |
| 5 | 隐私追踪 | 10 分 | 追踪/广告域名请求数量 |
| 6 | 敏感搜索 | 20 分 | 安全攻防/翻墙/暗网等搜索主题 |
| 7 | 自动化嫌疑 | 15 分 | 快速跳转比例 >40% 或连续快速浏览 >10 条 |

最终截断至 100 分，≥60 为高风险，≥30 为中风险。

## 注意事项

- 仅适用于 Windows 平台
- 部分浏览器数据可能被锁定，工具自动复制数据库副本避免竞争
- 登录凭据仅统计数量，不输出明文
- 以管理员权限运行可获取完整系统数据（DNS / Prefetch）
