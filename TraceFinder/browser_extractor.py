"""
无痕浏览器痕迹提取模块
提取浏览器运行痕迹（UserAssist注册表）和DNS缓存
"""
import winreg
import subprocess
import datetime
import re
import os


def filetime_to_datetime(filetime_bytes):
    """将Windows FILETIME转换为datetime对象"""
    if len(filetime_bytes) < 8:
        return None
    filetime = int.from_bytes(filetime_bytes, byteorder='little')
    if filetime == 0:
        return None
    timestamp = filetime / 10_000_000 - 11644473600
    try:
        return datetime.datetime.fromtimestamp(timestamp)
    except (OSError, ValueError, OverflowError):
        return None


def rot13_decode(s):
    """ROT13解码"""
    return s.translate(
        str.maketrans(
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )
    )


def get_userassist_traces():
    """从UserAssist注册表提取浏览器运行痕迹"""
    results = []
    ua_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}\Count"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ua_path)
        count = winreg.QueryInfoKey(key)[1]
        
        for i in range(count):
            try:
                name, value, _ = winreg.EnumValue(key, i)
                decoded_name = rot13_decode(name)
                
                if any(browser in decoded_name.lower() for browser in 
                       ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"]):
                    # 最后运行时间在偏移64字节处
                    if len(value) >= 72:
                        last_run = filetime_to_datetime(value[64:72])
                        if last_run:
                            results.append({
                                "type": "浏览器启动",
                                "time": last_run,
                                "time_str": last_run.strftime("%Y-%m-%d %H:%M:%S"),
                                "content": f"程序：{decoded_name}"
                            })
            except (OSError, ValueError):
                continue
        
        winreg.CloseKey(key)
    except (OSError, FileNotFoundError):
        pass
    
    return results


def get_dns_cache():
    """从系统DNS缓存提取访问过的域名"""
    results = []
    seen_domains = set()
    
    # 过滤CDN和内部域名
    skip_keywords = ['queniuck', 'bytedns', 'bytedance', 'zijieapi', 
                     'nic.', 'akadns', 'cloudfront', 'azure', 
                     '.internal', '.corp', '.intranet']
    
    try:
        dns_out = subprocess.check_output(
            "ipconfig /displaydns", shell=True, stderr=subprocess.STDOUT
        ).decode('gbk', errors='ignore')
        
        # 解析DNS缓存输出
        current_record = {}
        for line in dns_out.split('\n'):
            line = line.strip()
            
            if line.startswith("记录名称"):
                current_record['name'] = line.split(":", 1)[1].strip()
            elif line.startswith("记录类型"):
                current_record['type'] = line.split(":", 1)[1].strip()
            elif line.startswith("生存时间"):
                current_record['ttl'] = line.split(":", 1)[1].strip()
                # 一个记录结束
                if current_record.get('name'):
                    domain = current_record['name']
                    # 过滤本地域名、CDN域名和重复域名
                    if ('.' in domain and 
                        not domain.endswith('.lan') and 
                        not domain.endswith('.local') and
                        not domain.endswith('.') and
                        domain not in seen_domains and
                        not any(kw in domain.lower() for kw in skip_keywords)):
                        seen_domains.add(domain)
                        results.append({
                            "type": "DNS访问",
                            "time": None,
                            "time_str": "近1小时内",
                            "content": f"域名：{domain}"
                        })
                current_record = {}
    except subprocess.CalledProcessError:
        pass
    
    return results


def get_prefetch_browser_traces():
    """从Prefetch文件提取浏览器运行记录"""
    results = []
    prefetch_dir = r"C:\Windows\Prefetch"
    browser_names = ["CHROME", "MSEDGE", "FIREFOX", "BRAVE"]
    
    if not os.path.exists(prefetch_dir):
        return results
    
    try:
        for filename in os.listdir(prefetch_dir):
            if filename.endswith('.pf'):
                for browser in browser_names:
                    if browser in filename.upper():
                        filepath = os.path.join(prefetch_dir, filename)
                        try:
                            mtime = datetime.datetime.fromtimestamp(
                                os.path.getmtime(filepath)
                            )
                            results.append({
                                "type": "浏览器Prefetch",
                                "time": mtime,
                                "time_str": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                                "content": f"预读取文件：{filename}"
                            })
                        except OSError:
                            pass
    except OSError:
        pass
    
    return results


def get_incognito_trace():
    """获取无痕浏览器相关痕迹（综合）"""
    results = []
    results.extend(get_userassist_traces())
    results.extend(get_dns_cache())
    results.extend(get_prefetch_browser_traces())
    return results
