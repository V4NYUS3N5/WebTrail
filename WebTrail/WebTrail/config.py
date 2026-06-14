"""
集中配置 — 所有常量、模式、分类规则
"""

# ========================== 浏览器路径 ==========================

CHROMIUM_BROWSERS = [
    ("Chrome",    "~/AppData/Local/Google/Chrome/User Data"),
    ("Edge",      "~/AppData/Local/Microsoft/Edge/User Data"),
    ("Brave",     "~/AppData/Local/BraveSoftware/Brave-Browser/User Data"),
    ("Opera",     "~/AppData/Roaming/Opera Software/Opera Stable"),
    ("360浏览器", "~/AppData/Local/360Chrome/Chrome/User Data"),
]

FIREFOX_PROFILES_DIR = "~/AppData/Roaming/Mozilla/Firefox/Profiles"

# ========================== 系统痕迹 ==========================

BROWSER_EXECUTABLES = [
    "chrome.exe", "msedge.exe", "firefox.exe",
    "brave.exe", "opera.exe", "360chrome.exe",
]

PREFETCH_BROWSER_PREFIXES = [
    "CHROME", "MSEDGE", "FIREFOX", "BRAVE", "OPERA", "360CHROME",
]

# ========================== 可疑关键词 ==========================

SUSPICIOUS_KEYWORDS = [
    "密码", "账号", "账户", "机密", "保密", "漏洞", "后门",
    "password", "secret", "token", "api_key", "credential",
    "exploit", "payload", "shell", "backdoor", "bypass",
    "pastebin", "anonfile", "file.io", "transfer.sh",
    "hack", "crack", "keygen", "破解", "入侵", "木马",
    "勒索", "ransomware", "暗网", "deepweb", "torrent",
]

SUSPICIOUS_DOMAINS = [
    "pastebin.com", "anonfile.com", "file.io", "transfer.sh",
    "mega.nz", "mega.co.nz", "mediafire.com",
]

# ========================== 搜索引擎解析 ==========================

SEARCH_ENGINE_PATTERNS = [
    ("google.",       "q",     "Google"),
    ("bing.",         "q",     "Bing"),
    ("baidu.com",     "wd",    "百度"),
    ("sogou.com",     "query", "搜狗"),
    ("so.com",        "q",     "360搜索"),
    ("yahoo.",        "p",     "Yahoo"),
    ("duckduckgo.",   "q",     "DuckDuckGo"),
    ("yandex.",       "text",  "Yandex"),
    ("bilibili.com",  "keyword","B站"),
    ("zhihu.com",     "q",     "知乎"),
    ("github.com",    "q",     "GitHub"),
]

# ========================== 搜索词主题分类 ==========================

SEARCH_TOPIC_RULES = [
    (r"(破解|crack|激活|注册码|序列号|keygen|注册机|patch|补丁|绿色版)", "破解/盗版"),
    (r"(漏洞|渗透|注入|sql注入|xss|csrf|提权|webshell|免杀|远控|exp|poc)", "安全攻防"),
    (r"(翻墙|vpn|梯子|代理|clash|v2ray|ssr|trojan|机场|科学上网|shadowsocks)", "翻墙工具"),
    (r"(暗网|deep.?web|tor|onion)", "暗网相关"),
    (r"(社工|人肉|查开房|查户籍|查身份证|查手机)", "社工查询"),
    (r"(博彩|赌博|彩票|赌场|casino|bet|六合彩|足彩|竞彩|外围)", "博彩相关"),
    (r"(色情|成人|av|番号|福利姬|萝莉|幼女|乱伦)", "成人内容"),
    (r"(网盘|下载|资源|合集|打包|种子|磁力|bt|torrent|magnet)", "资源下载"),
    (r"(木马|病毒|蠕虫|勒索|ransomware|wannacry)", "恶意软件"),
    (r"(身份证|银行卡|手持|四件套|对公账户|营业执照)", "敏感证件"),
    (r"(代孕|买肾|器官|卖血|精子|卵子)", "非法交易"),
    (r"(充值|代充|折扣|黑卡|洗钱|跑分|接码)", "灰产金融"),
    (r"(python|java|javascript|golang|rust|c\+\+|编程|代码|算法|面试)", "编程学习"),
    (r"(电影|电视剧|综艺|动漫|番剧|小说|音乐|游戏|直播)", "娱乐"),
    (r"(天气|股票|汇率|油价|快递|外卖|地图)", "生活服务"),
    (r"(新冠|疫情|核酸|口罩|卫健委)", "健康防疫"),
]

# ========================== 域名分类规则 ==========================

DOMAIN_CATEGORY_RULES = [
    # 社交
    (r"weixin\.qq\.com|wx\.qq\.com",                          "社交", "微信"),
    (r"weibo\.com",                                            "社交", "微博"),
    (r"zhihu\.com",                                            "社交", "知乎"),
    (r"tieba\.baidu\.com",                                     "社交", "百度贴吧"),
    (r"douban\.com",                                           "社交", "豆瓣"),
    (r"facebook\.com|fb\.com|instagram\.com|twitter\.com|x\.com|reddit\.com|t\.co",
                                                                "社交", "境外社交"),
    (r"linkedin\.com",                                         "社交", "LinkedIn"),
    (r"discord\.com|telegram\.org|slack\.com",                 "社交", "即时通讯"),
    # 视频
    (r"bilibili\.com",                                         "视频", "B站"),
    (r"youtube\.com|youtu\.be",                                "视频", "YouTube"),
    (r"douyin\.com|tiktok\.com",                               "视频", "抖音/TikTok"),
    (r"iqiyi\.com|youku\.com|v\.qq\.com|mgtv\.com|tv\.sohu\.com",
                                                                "视频", "国内视频平台"),
    (r"twitch\.tv",                                            "视频", "Twitch"),
    # 购物
    (r"taobao\.com|tmall\.com|jd\.com|pdd\.com|suning\.com|vip\.com|1688\.com",
                                                                "购物", "国内电商"),
    (r"amazon\.(com|cn|co\.jp|de|co\.uk)|ebay\.com|aliexpress\.com",
                                                                "购物", "境外电商"),
    # 技术/开发
    (r"github\.com",                                           "技术", "GitHub"),
    (r"stackoverflow\.com|stackexchange\.com",                 "技术", "技术问答"),
    (r"csdn\.net",                                             "技术", "CSDN"),
    (r"juejin\.cn|segmentfault\.com",                          "技术", "技术社区"),
    (r"pypi\.org|npmjs\.com|crates\.io|docker\.com|hub\.docker\.com",
                                                                "技术", "包管理/容器"),
    (r"gitee\.com|gitlab\.com",                                "技术", "代码托管"),
    # 教育
    (r"edu\.cn|\.edu/",                                        "教育", "教育机构"),
    (r"mooc\.|icourse|chaoxing\.com|xuexi\.cn|xuetangx\.com",  "教育", "在线教育"),
    (r"wikipedia\.org|wiki.*\.org",                            "教育", "百科"),
    (r"scholar\.google|cnki\.net|wanfangdata|arxiv\.org",      "教育", "学术"),
    # 新闻
    (r"sina\.com\.cn|news\.qq\.com|news\.163\.com|sohu\.com|ifeng\.com|thepaper\.cn|huanqiu\.com",
                                                                "新闻", "国内新闻"),
    (r"bbc\.com|cnn\.com|nytimes\.com|reuters\.com|bloomberg\.com",
                                                                "新闻", "境外新闻"),
    # 搜索
    (r"google\.(com|\w\w)/search|bing\.com/search|baidu\.com/s","搜索", "搜索引擎"),
    # 成人
    (r"porn|xvideos|pornhub|xnxx|redtube|youporn|onlyfans|chaturbate",
                                                                "成人", "成人内容"),
    # 游戏
    (r"steampowered\.com|steamcommunity\.com",                 "游戏", "Steam"),
    (r"epicgames\.com",                                        "游戏", "Epic"),
    (r"battle\.net|blizzard\.com",                             "游戏", "暴雪"),
    (r"dota2|leagueoflegends|pubg|genshin|honkai|warthunder",  "游戏", "网络游戏"),
    # 网盘
    (r"pan\.baidu\.com",                                       "网盘", "百度网盘"),
    (r"lanzou|aliyundrive|quark\.cn/s|123pan\.com|yun\.139\.com",
                                                                "网盘", "其他网盘"),
    (r"mega\.nz|dropbox\.com|drive\.google\.com|onedrive\.live\.com",
                                                                "网盘", "境外网盘"),
    # AI
    (r"chat\.openai\.com|chatgpt\.com|claude\.ai|bard\.google|gemini|deepseek|kimi\.moonshot|tongyi\.aliyun|doubao\.com|poe\.com",
                                                                "AI", "AI对话"),
    # 邮箱
    (r"mail\.(qq|163|126|sina|aliyun|10086)\.com|outlook\.live\.com|gmail\.google\.com|proton\.me|foxmail\.com",
                                                                "邮件", "电子邮箱"),
    # 工具
    (r"translate\.google|fanyi\.baidu|deepl\.com",             "工具", "翻译"),
    (r"ilovepdf\.com|smallpdf\.com|pdf24|convertio",           "工具", "文档工具"),
    # 安全
    (r"virustotal\.com|any\.run|hybrid-analysis\.com|urlscan\.io|abuseipdb\.com|shodan\.io",
                                                                "安全", "安全分析"),
]

# ========================== 高风险URL模式 ==========================

HIGH_RISK_URL_PATTERNS = [
    (r"\.onion(/|$)",             "暗网.onion站点"),
    (r"pastebin\.com/\w+",        "Pastebin文本分享"),
    (r"mega\.(nz|co\.nz)",        "MEGA加密网盘"),
    (r"(crack|keygen|serial|warez)", "破解/盗版资源"),
    (r"(hack|exploit|payload|shell|backdoor)", "攻击工具"),
    (r"(phishing|scam|fraud)",    "欺诈相关"),
    (r"(ransomware|malware|trojan|spyware|botnet)", "恶意软件"),
    (r"free-.*\.(tk|ml|ga|cf|gq)", "可疑免费域名"),
]

# ========================== 下载风险扩展名 ==========================

SUS_DOWNLOAD_EXTENSIONS = {
    ".exe", ".msi", ".bat", ".cmd", ".ps1", ".vbs",
    ".scr", ".pif", ".com", ".dll", ".sys", ".reg",
    ".hta", ".jar", ".js", ".wsf", ".vbe",
}

EXECUTABLE_EXTENSIONS = {".exe", ".msi", ".bat", ".cmd", ".ps1"}

# ========================== 追踪/广告域名 ==========================

TRACKER_DOMAINS = {
    "doubleclick.net", "googleadservices.com", "googlesyndication.com",
    "google-analytics.com", "googletagmanager.com",
    "adnxs.com", "criteo.com", "outbrain.com", "taboola.com",
    "scorecardresearch.com", "quantserve.com", "hotjar.com",
    "clicktale.net", "mouseflow.com", "fullstory.com",
    "newrelic.com", "datadoghq.com", "mixpanel.com", "amplitude.com",
    "segment.io", "branch.io", "adjust.com", "appsflyer.com",
    "cnzz.com", "umeng.com",
}

# ========================== DNS过滤 ==========================

DNS_SKIP_KEYWORDS = [
    "queniuck", "bytedns", "bytedance", "zijieapi",
    "nic.", "akadns", "cloudfront", "azure",
    ".internal", ".corp", ".intranet",
]

# ========================== 会话阈值 ==========================

SESSION_GAP_SECONDS = 30 * 60
LONG_SESSION_MINUTES = 120
SHORT_SESSION_MINUTES = 1
VELOCITY_MIN_SAMPLES = 5
AUTOMATION_BURST_RATIO = 40
AUTOMATION_RAPID_STREAK = 10

# ========================================================================
# 数字取证风险指标体系
# 基于 NIST SP 800-86 + 网络杀伤链模型，三级证据分级
# ========================================================================

# ---- 证据确信度定义 ----
# HIGH   = 可直接归因的恶意指标（如已知恶意域名、工具签名）
# MEDIUM = 行为模式高度偏离基线，需结合上下文字段判定
# LOW    = 弱信号，仅作佐证参考

# ---- 杀伤链阶段 ----
KILL_CHAIN_STAGES = [
    "侦察",       # Reconnaissance
    "武器化",     # Weaponization
    "投递",       # Delivery
    "利用",       # Exploitation
    "安装与持久化", # Installation
    "命令与控制",   # C2
    "目标行动",     # Actions
]

# ---- 风险轴（4 维度） ----
RISK_AXES = {
    "attack_tooling":  "攻击工具与武器化",
    "recon_intel":     "侦查与信息收集",
    "credential_persist": "凭证窃取与持久化",
    "anti_forensics":   "反取证与隐匿",
}

# ---- 取证指标定义 ----
# 格式: (指标ID, 指标名称, 杀伤链阶段索引, 风险轴, 确信度, 证据类型)
FORENSIC_INDICATORS = {
    # ====== 攻击工具与武器化 ======
    "exploit_search": {
        "name": "漏洞利用搜索",
        "kill_chain": 0,        # 侦察
        "axis": "attack_tooling",
        "confidence": "MEDIUM",
        "desc": "搜索CVE/漏洞/渗透测试相关关键词",
    },
    "hacktool_download": {
        "name": "攻击工具下载",
        "kill_chain": 1,        # 武器化
        "axis": "attack_tooling",
        "confidence": "HIGH",
        "desc": "下载已知黑客工具（exploit/payload/shell/malware）",
    },
    "malware_access": {
        "name": "恶意软件接触",
        "kill_chain": 2,        # 投递
        "axis": "attack_tooling",
        "confidence": "HIGH",
        "desc": "访问已知恶意域名/IP或下载可执行载荷",
    },
    "crack_warez_use": {
        "name": "破解/盗版工具",
        "kill_chain": 0,
        "axis": "attack_tooling",
        "confidence": "LOW",
        "desc": "搜索或下载破解软件/注册机——可能引入后门",
    },
    "piracy_resource": {
        "name": "盗版资源站",
        "kill_chain": 2,
        "axis": "attack_tooling",
        "confidence": "LOW",
        "desc": "访问盗版/资源聚合站——高风险载荷投递渠道",
    },

    # ====== 侦查与信息收集 ======
    "darkweb_access": {
        "name": "暗网访问",
        "kill_chain": 0,
        "axis": "recon_intel",
        "confidence": "HIGH",
        "desc": "访问.onion暗网站点——常用于匿名交易或情报收集",
    },
    "osint_research": {
        "name": "社工/人肉搜索",
        "kill_chain": 0,
        "axis": "recon_intel",
        "confidence": "MEDIUM",
        "desc": "搜索社工查询、个人信息搜集相关内容",
    },
    "security_research": {
        "name": "安全技术研究",
        "kill_chain": 0,
        "axis": "recon_intel",
        "confidence": "LOW",
        "desc": "访问安全分析平台（VirusTotal/Hybrid-Analysis/Shodan）——可能是安全从业者",
    },
    "vpn_circumvention": {
        "name": "翻墙/代理工具",
        "kill_chain": 6,        # 反取证
        "axis": "anti_forensics",
        "confidence": "LOW",
        "desc": "搜索VPN/代理/翻墙工具——意图隐匿网络身份",
    },

    # ====== 凭证窃取与持久化 ======
    "credential_harvest": {
        "name": "凭证收集痕迹",
        "kill_chain": 6,
        "axis": "credential_persist",
        "confidence": "MEDIUM",
        "desc": "大量登录凭据存储（可能密码复用/撞库风险）",
    },
    "phishing_exposure": {
        "name": "钓鱼/欺诈站点",
        "kill_chain": 3,        # 利用
        "axis": "credential_persist",
        "confidence": "HIGH",
        "desc": "访问已知钓鱼/欺诈域名",
    },
    "anomalous_logins": {
        "name": "异常登录行为",
        "kill_chain": 5,        # C2
        "axis": "credential_persist",
        "confidence": "MEDIUM",
        "desc": "登录行为模式异常（多浏览器/多账户）",
    },
    "pastebin_use": {
        "name": "Pastebin数据交换",
        "kill_chain": 5,
        "axis": "credential_persist",
        "confidence": "MEDIUM",
        "desc": "访问Pastebin/文本分享——常用于传递泄露数据",
    },

    # ====== 反取证与隐匿 ======
    "incognito_suspect": {
        "name": "疑似无痕模式",
        "kill_chain": 6,
        "axis": "anti_forensics",
        "confidence": "LOW",
        "desc": "未发现会话记录——可能使用隐私模式规避追踪",
    },
    "encrypted_transfer": {
        "name": "加密传输通道",
        "kill_chain": 5,
        "axis": "anti_forensics",
        "confidence": "MEDIUM",
        "desc": "使用MEGA等端到端加密网盘——规避流量审查",
    },
    "multi_browser_masking": {
        "name": "多浏览器身份分散",
        "kill_chain": 6,
        "axis": "anti_forensics",
        "confidence": "LOW",
        "desc": "同时使用3个以上浏览器——可能多身份隔离",
    },
    "automation_behavior": {
        "name": "自动化浏览行为",
        "kill_chain": 6,
        "axis": "anti_forensics",
        "confidence": "MEDIUM",
        "desc": "浏览速度异常（>40%快速跳转或连续>10次快速浏览）——疑似脚本操作",
    },
    "late_night_activity": {
        "name": "深夜异常活跃",
        "kill_chain": 6,
        "axis": "anti_forensics",
        "confidence": "LOW",
        "desc": "00:00-05:00浏览占比超30%——偏离正常作息",
    },
}

# ---- 证据等级权重 ----
# 各确信度级别的得分权重
EVIDENCE_WEIGHTS = {
    "HIGH":   25,     # 直接证据——可直接作为取证依据
    "MEDIUM": 15,     # 间接证据——需结合上下文
    "LOW":    5,      # 弱信号——仅作为辅助参考
}

# ---- 交叉验证加成 ----
# 同一杀伤链阶段出现 ≥CORROBORATE_THRESHOLD 个独立指标时，额外加成
CORROBORATE_THRESHOLD = 3      # 同一阶段累积3条以上=交叉验证
CORROBORATE_BONUS = 10         # 交叉验证额外得分

# ---- 风险等级阈值 ----
RISK_LEVELS = [
    (70, "高风险",  "发现多项高确信度的恶意行为证据，建议立即启动应急响应"),   # noqa
    (40, "中风险",  "存在可疑行为指标，需人工复核确认"),                     # noqa
    (0,  "低风险",  "未发现明确威胁指标，行为模式大致正常"),                  # noqa
]
