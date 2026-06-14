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
| 评分 | 取证风险评估（NIST SP 800-86 + 杀伤链） | 4轴风险分 + 3级证据确信度 + 杀伤链矩阵 |

## 运行方式

```bash
cd WebTrail

# 命令行模式
python main.py                  # 控制台输出完整报告
python main.py -q               # 静默模式（仅摘要）
python main.py -o report.txt    # 保存报告到文件
python main.py --json out.json  # 导出 JSON

# 图形界面模式
python main.py -g               # 启动 GUI（含取证报告 + 智能分析 + 风险可视化 三个Tab）
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
│   ├── __init__.py           ← 导出 4 个工具函数
│   ├── time.py               ← 3 种时间戳转换
│   └── sqlite.py             ← SQLite 安全副本读取
│
├── extraction/               ← 提取层（ABC 基类 + 3 个实现）
│   ├── __init__.py           ← 导出 4 个提取器
│   ├── base.py               ← BaseExtractor 抽象类
│   ├── chromium.py           ← ChromiumExtractor（5 浏览器）
│   ├── firefox.py            ← FirefoxExtractor
│   └── system.py             ← SystemExtractor（UserAssist/DNS/Prefetch）
│
├── analysis/                 ← 分析层（5 子模块 + 编排器）
│   ├── __init__.py           ← 导出 analyze() 入口
│   ├── engine.py             ← analyze() 流水线编排
│   ├── classifier.py         ← 搜索词提取 / 域名分类 / Top域名 / 时段 / 下载
│   ├── session.py            ← 会话重建
│   ├── velocity.py           ← 浏览速度 / 自动化检测
│   ├── profiler.py           ← 用户画像
│   └── risk.py               ← NIST取证风险评估（4阶段）
│
├── reporting/                ← 展示层
│   ├── __init__.py           ← 导出 generate / format_analysis
│   ├── report.py             ← 取证报告生成
│   └── formatter.py          ← 分析报告格式化
│
├── main.py / gui.py          ← CLI / GUI 双入口
├── ARCHITECTURE.md           ← 模块架构说明书
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

## 风险评估体系

基于 **NIST SP 800-86** 数字取证方法 + **网络杀伤链 (Cyber Kill-Chain)** 模型。

### 模型架构

```
证据采集 → 确信度评估 → 杀伤链映射 → 评分开具
   ↓            ↓            ↓            ↓
18项取证指标   3级分离   7阶段覆盖   0-100分
逐项命中      联动提升    交叉验证   +等级结论
```

### 4 维风险轴

| 风险轴 | 英文 | 评估内容 |
|--------|------|----------|
| 攻击工具与武器化 | attack_tooling | 漏洞利用搜索 / 攻击工具下载 / 恶意软件接触 / 破解工具 |
| 侦查与信息收集 | recon_intel | 暗网访问 / 社工查询 / 安全分析平台访问 / 翻墙工具 |
| 凭证窃取与持久化 | credential_persist | 凭证收集 / 钓鱼站点 / 异常登录 / Pastebin 数据交换 |
| 反取证与隐匿 | anti_forensics | 无痕模式 / 加密传输 / 多浏览器分散 / 自动化行为 / 深夜活跃 |

### 证据确信度三级

| 等级 | 图标 | 单指标权重 | 含义 |
|------|------|-----------|------|
| HIGH | ● | 25 分 | 可直接作为取证依据（已知恶意域名、工具签名） |
| MEDIUM | ◉ | 15 分 | 行为模式高度偏离基线，需结合上下文判定 |
| LOW | ○ | 5 分 | 弱信号，仅作为辅助参考 |

### 联动提升机制

- **搜索漏洞 + 攻击工具下载** → 搜索项确信度从 MEDIUM 升至 HIGH
- **深夜活跃 + 加密传输 + 自动化** ≥ 2 项 → 弱信号逐级提升（LOW→MEDIUM→HIGH）

### 交叉验证

同一杀伤链阶段出现 ≥3 条独立证据 → 额外 **+10 分**（多源印证，显著提高置信度）。

### 评分示例

```
取证风险评定: 100/100  [高风险]
结论: 发现多项高确信度的恶意行为证据，建议立即启动应急响应

  ┌─ 风险维度分解 ──────────────────────────┐
  │ 攻击工具与武器化       ██████████████ 36分
  │ 侦查与信息收集                       0分
  │ 凭证窃取与持久化       ████████████  30分
  │ 反取证与隐匿           █████████████  45分
  └──────────────────────────────────────┘

  【证据统计】 共 7 项指标命中  (确凿:2  间接:3  弱信号:2)
    交叉验证: 1 个杀伤链阶段呈多源印证 (+10分)
```

### 风险等级

等级判定与 `RISK_LEVELS` 阈值一致，保证 CLI / GUI 输出统一。

## 注意事项

- 仅适用于 Windows 平台
- 部分浏览器数据可能被锁定，工具自动复制数据库副本避免竞争
- 登录凭据仅统计数量，不输出明文
- 以管理员权限运行可获取完整系统数据（DNS / Prefetch）
