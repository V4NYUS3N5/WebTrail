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

SENSITIVE_TOPICS = {
    "破解/盗版", "安全攻防", "翻墙工具", "暗网相关", "社工查询",
    "博彩相关", "成人内容", "恶意软件", "敏感证件", "灰产金融",
}

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

SESSION_GAP_SECONDS = 30 * 60        # 30分钟无操作=新会话
LONG_SESSION_MINUTES = 120           # >2h 长会话
SHORT_SESSION_MINUTES = 1            # <1min 瞬时会话
VELOCITY_MIN_SAMPLES = 5             # 速度检测最少采样
AUTOMATION_BURST_RATIO = 40          # >40% 快速跳转=自动化嫌疑
AUTOMATION_RAPID_STREAK = 10         # >10 连续快速=自动化嫌疑

# ========================== 风险评分权重 ==========================

RISK_WEIGHTS = {
    "suspicious_keyword":  (30, 5),    # (上限, 每条得分)
    "high_risk_url":       (30, 10),   # (上限, 每条得分)
    "late_night_high":     (15, 30),   # (>30%时的得分, 阈值)
    "late_night_medium":   (8,  15),   # (>15%时的得分, 阈值)
    "download_risky":      (15, 3),    # (上限, 每个文件得分)
    "tracker_high":        (10, 50),   # (>50个时的得分, 阈值)
    "tracker_medium":      (5,  20),   # (>20个时的得分, 阈值)
    "sensitive_search":    (20, 3),    # (上限, 每条得分)
    "automation":          (15, 0),    # 固定得分
}
