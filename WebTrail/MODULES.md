# WebTrail 模块架构文档

## 架构总览

```
main.py ──► core/pipeline.py ──► browsers/\*.py ──► core/extractor.py
                  │                      │
                  ▼                      ▼
            core/profiler.py       utils/sqlite\_utils.py
            core/timeline.py       utils/time\_utils.py
                  │                utils/url\_utils.py
                  ▼
            output/writer.py ────► JSON + CSV 报告
```

**数据流：** CLI/GUI → `pipeline.create\_extractors` → `BaseExtractor.run` → 各 `extract\_\*` 方法 → `profile\_user` → `write\_report`

\---

## 各模块详解

### 1\. `main.py` — 入口调度

* 解析 CLI 参数（`--browser`、`--gui`、`--output` 等）
* `--gui` 时委托 `gui.app.launch()` 启动图形界面
* 否则按三阶段管道执行：哈希 → 提取 → 画像 → 输出

### 2\. `config.py` — 全局配置

```python
# 跨平台浏览器数据路径
CHROME\_BASE  # Windows: %LOCALAPPDATA%/Google/Chrome/User Data
EDGE\_BASE    # Windows: %LOCALAPPDATA%/Microsoft/Edge/User Data
FIREFOX\_BASE # Windows: %APPDATA%/Mozilla/Firefox/Profiles

# 取证参数
OUTPUT\_DIR      # \~/WebTrail\_Forensics
HASH\_ALGORITHM  # sha256
```

\---

## 核心层 `core/`

### 3\. `core/extractor.py` — 数据结构与基类

#### `ArtifactRecord`（dataclass）

单一痕迹记录的标准化载体，字段：

|字段|类型|说明|
|-|-|-|
|`artifact\_type`|`str`|类型标签：`history` / `cookie` / `download` / `bookmark` / `login` / `cache`|
|`browser`|`str`|来源浏览器：`Chrome` / `Edge` / `Firefox`|
|`timestamp`|`str \| None`|ISO 8601 时间戳|
|`profile`|`str`|用户配置文件名称|
|`source\_file`|`str`|证据文件绝对路径|
|`data`|`dict`|具体痕迹内容（URL、标题等）|
|`extraction\_time`|`str`|提取执行时刻|
|`checksum`|`str`|该条记录的 SHA-256|

#### `ExtractionResult`（dataclass）

一次提取操作的汇总：`browser`、`profiles`、`records`、`errors`、`file\_hashes`。

#### `BaseExtractor`（ABC）

定义六个抽象方法和通用 `run()` 流程：

```
run()
 ├── 检查 base\_path 存在
 ├── detect\_profiles()          → \[(name, path), ...]
 ├── 遍历每个 profile：
 │    ├── extract\_history()
 │    ├── extract\_cookies()
 │    ├── extract\_downloads()
 │    ├── extract\_bookmarks()
 │    ├── extract\_logins()
 │    └── extract\_cache\_info()
 └── 返回 ExtractionResult
```

每个 `extract\_\*` 抛出的异常被捕获并记录到 `errors` 列表，不中断其他提取器。

### 4\. `core/pipeline.py` — 取证管道

将三阶段流程封装为独立函数，供 CLI 和 GUI 共用：

```python
create\_extractors(selected)    # 根据浏览器名/集合创建提取器列表
collect\_evidence\_hashes(exts)  # 阶段1：证据文件 SHA-256
run\_extraction(exts)           # 阶段2：执行提取，汇总记录
run\_profiling(records)         # 阶段3：用户画像分析
print\_summary(profile)         # 终端摘要输出
```

`create\_extractors` 支持三种输入：

* `None` — 全部可用浏览器
* `"Chrome"` — 单个浏览器
* `{"chrome", "firefox"}` — 多选

内部用 `\_EXTRACTOR\_MAP` 字典统一管理浏览器类与路径映射。

### 5\. `core/hasher.py` — 取证哈希

|函数|说明|
|-|-|
|`file\_hash(path)`|对单个文件逐块读取计算 SHA-256（64 KB 缓冲）|
|`hash\_evidence\_files(dict)`|批量计算 `{标签: 哈希}`|
|`record\_hash(dict)`|将记录序列化为 JSON 后计算 SHA-256|

### 6\. `core/timeline.py` — 时间线构建

|函数|说明|
|-|-|
|`build\_timeline(records)`|提取所有有时间戳的记录，按 ISO 8601 升序排列，返回事件列表|
|`daily\_domain\_stats(events)`|按域名聚合访问频次，降序排列|

输出结构：`\[{"ts", "browser", "profile", "type", "data"}, ...]`

### 7\. `core/profiler.py` — 用户画像

`profile\_user(records)` 返回 7 个维度的分析结果：

|键|内容|
|-|-|
|`overview`|总记录数、时间范围、浏览器分布、类型分布|
|`activity\_heat`|`by\_hour`（24 小时）+ `by\_day`（近 30 天）|
|`top\_domains`|TOP 20 域名及访问次数|
|`top\_categories`|8 类 URL 语义分类统计|
|`behavior\_insights`|活跃高峰、夜间占比、登录/Cookie 数量|
|`browser\_usage`|各浏览器按痕迹类型细分|
|`risk\_indicators`|隐私模式推断、历史清除检测、可疑域名列表|

\---

## 浏览器适配器 `browsers/`

### 8\. `browsers/chrome.py` — Chrome 适配器

* **继承** `BaseExtractor`
* **`detect\_profiles`** — 扫描 `Default` 和 `Profile N` 目录
* **`\_connect`** — 统一数据库连接入口，使用 `safe\_connect\_with\_fallback`
* **SQL 查询**：

  * `History` → `urls` 表
  * `Network/Cookies` → `cookies` 表
  * `History` → `downloads` 表
  * `Bookmarks` → JSON 递归解析
  * `Login Data` → `logins` 表
  * `Network/TransportSecurity` / `Cache/Cache\_Data` → HSTS + 缓存计数

时间戳：Chrome 使用 1601-01-01 微秒时间戳（Windows FILETIME / WebKit 格式）。

### 9\. `browsers/edge.py` — Edge 适配器

直接继承 `ChromeExtractor`，仅覆写 `\_\_init\_\_` 将 `browser` 设为 `"Edge"`。18 行代码，零冗余。

### 10\. `browsers/firefox.py` — Firefox 适配器

* **`detect\_profiles`** — 解析 `profiles.ini` 获取配置路径，回退目录扫描
* **SQL 查询**：

  * `places.sqlite` → `moz\_places`（历史）、`moz\_bookmarks`（书签）、`moz\_annos`（下载）
  * `cookies.sqlite` → `moz\_cookies`
  * `logins.json` → JSON 解析
  * `cache2/` → 目录存在检查

时间戳：Firefox 使用 1970-01-01 微秒时间戳（PRTime 格式）。

\---

## GUI 层 `gui/`

### 11\. `gui/app.py` — tkinter 图形界面

`class WebTrailApp` 提供完整图形化操作：

* **布局** — 顶部标题栏 + 浏览器检测复选框 + 左侧控件面板 + 右侧 5 选项卡 Notebook + 底部状态栏
* **输出目录选择** — 输入框 + "浏览..."按钮，默认路径 `\~/WebTrail\_Forensics`，支持自定义
* **自动保存** — 分析完成后自动调用 `write\_report` 将报告写入指定目录，状态栏显示完整路径
* **异步执行** — 分析逻辑跑在 `threading.Thread` 中，不阻塞 UI
* **选项卡**：

|标签|组件|内容|
|-|-|-|
|概览|`tk.Text`|记录总数、时间范围、类型分布柱状图|
|TOP域名|`ttk.Treeview`|排名表格，支持滚动|
|活跃时段|`tk.Text`|24 小时活跃度 ASCII 柱状图 + 近 14 天统计|
|访问类别|`ttk.Treeview`|8 类分类计数|
|风险指标|`tk.Text`|隐私模式、历史清除、可疑域名列表|

* **导出** — `filedialog.askdirectory` 选择目录后调用 `pipeline.write\_report`

\---

## 输出层 `output/`

### 12\. `output/writer.py` — 报告生成

`write\_report(records, profile, hashes, output\_dir)` 生成：

|文件|格式|内容|
|-|-|-|
|`forensic\_report.json`|JSON|完整取证数据（元数据 + 画像 + 记录）|
|`records.csv`|CSV（UTF-8 BOM）|扁平化记录表（可 Excel 打开）|
|`timeline.csv`|CSV（UTF-8 BOM）|按时序排列的活动时间线|
|`report\_checksums.json`|JSON|上述文件的 SHA-256 自校验|

\---

## 工具层 `utils/`

### 13\. `utils/sqlite\_utils.py` — 安全数据库连接

|函数|说明|
|-|-|
|`safe\_connect(path)`|URI 只读连接 + `query\_only=ON`|
|`copy\_to\_temp(path)`|复制到临时文件（Windows 上解决浏览器锁定问题）|
|`safe\_connect\_with\_fallback(path)`|先尝试只读连接，失败后 copy\_to\_temp → 关闭时自动清除临时文件|
|`\_dict\_factory`|自定义 `row\_factory`，返回 `dict`（兼容所有 Python 版本 `.get()`）|

### 14\. `utils/time\_utils.py` — 时间戳转换

|函数|输入格式|用途|
|-|-|-|
|`chrome\_micros\_to\_iso`|1601 epoch 微秒|Chrome/Edge 时间戳|
|`firefox\_micros\_to\_iso`|1970 epoch 微秒（PRTime）|Firefox SQLite 时间戳|
|`unix\_millis\_to\_iso`|1970 epoch 毫秒|Firefox JSON / 通用毫秒|

返回值统一为 ISO 8601 字符串或 `None`（无效输入）。

### 15\. `utils/url\_utils.py` — URL 解析与分类

|函数|说明|
|-|-|
|`extract\_domain(raw)`|从 URL 或 host 提取纯域名，处理前导点、协议前缀、端口|
|`extract\_domain\_from\_record(data)`|从 ArtifactRecord.data 多键名兼容提取|
|`classify\_url(url)`|将 URL 匹配到 8 个预定义类别之一，未命中返回"其他"|
|`URL\_CATEGORIES`|分类规则字典，可自行扩展|

\---

## 设计原则

1. **取证优先** — 只读、可审计、可回溯、链式保管
2. **最少依赖** — 纯标准库，单文件即可运行
3. **错误隔离** — 单一提取器/方法失败不中断全局流程
4. **职责单一** — 每个模块只做一件事，管道明确定义三阶段
5. **继承合理** — Edge 继承 ChromeExtractor 复用 Chromium 内核提取逻辑

