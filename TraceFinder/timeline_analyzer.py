"""
时间线关联与可疑标记模块
将所有痕迹按时间排序，自动标记可疑行为
"""
import datetime


# 敏感关键词列表
SENSITIVE_KEYWORDS = ["机密", "合同", "密码", "账号", "账户", "secret", "password", "confidential"]


def generate_timeline(all_traces):
    """
    把所有痕迹按时间排序，自动标记可疑行为
    
    标记规则：
    1. U盘插入后1分钟内有文件复制/上传操作
    2. 无痕浏览器运行后10分钟内有网盘/邮箱访问痕迹
    3. 剪贴板复制敏感关键词后有文件传输操作
    """
    # 过滤有时间的痕迹并排序
    timed_traces = [t for t in all_traces if t.get("time") is not None]
    timed_traces.sort(key=lambda x: x["time"])
    
    # 初始化可疑标记
    for trace in all_traces:
        trace["suspicious"] = False
        trace["suspicious_reason"] = ""
    
    # 规则1: U盘插入后1分钟内有文件操作
    for i, trace in enumerate(timed_traces):
        if trace["type"] == "USB接入":
            usb_time = trace["time"]
            for j in range(i + 1, len(timed_traces)):
                other = timed_traces[j]
                time_diff = (other["time"] - usb_time).total_seconds()
                
                if time_diff > 60:  # 超过1分钟
                    break
                
                if any(keyword in other["content"] for keyword in 
                       ["文件", "上传", "复制", "下载", "剪贴板"]):
                    other["suspicious"] = True
                    other["suspicious_reason"] = "U盘插入后1分钟内有文件操作"
                    trace["suspicious"] = True
                    trace["suspicious_reason"] = "U盘插入后有可疑文件操作"
    
    # 规则2: 浏览器运行后10分钟内有网盘/邮箱访问
    for i, trace in enumerate(timed_traces):
        if trace["type"] in ["浏览器启动", "浏览器Prefetch"]:
            browser_time = trace["time"]
            for j in range(i + 1, len(timed_traces)):
                other = timed_traces[j]
                time_diff = (other["time"] - browser_time).total_seconds()
                
                if time_diff > 600:  # 超过10分钟
                    break
                
                if any(keyword in other["content"].lower() for keyword in 
                       ["pan", "baidu", "邮箱", "mail", "drive", "网盘"]):
                    other["suspicious"] = True
                    other["suspicious_reason"] = "浏览器运行后有网盘/邮箱访问"
                    trace["suspicious"] = True
                    trace["suspicious_reason"] = "浏览器运行后有可疑访问行为"
    
    # 规则3: 剪贴板复制敏感关键词后有文件传输
    for i, trace in enumerate(timed_traces):
        if trace["type"] == "剪贴板复制":
            clip_time = trace["time"]
            content = trace["content"].lower()
            
            # 检查是否包含敏感关键词
            has_sensitive = any(kw in content for kw in SENSITIVE_KEYWORDS)
            if not has_sensitive:
                continue
            
            for j in range(i + 1, len(timed_traces)):
                other = timed_traces[j]
                time_diff = (other["time"] - clip_time).total_seconds()
                
                if time_diff > 300:  # 超过5分钟
                    break
                
                if any(keyword in other["content"] for keyword in 
                       ["文件", "上传", "传输", "发送", "微信", "QQ"]):
                    other["suspicious"] = True
                    other["suspicious_reason"] = "复制敏感内容后有文件传输"
                    trace["suspicious"] = True
                    trace["suspicious_reason"] = "复制敏感关键词后有文件传输"
    
    return all_traces


def format_timeline_report(all_traces):
    """格式化时间线报告输出"""
    # 分离有时间戳和无时间戳的痕迹
    timed_traces = [t for t in all_traces if t.get("time") is not None]
    untimed_traces = [t for t in all_traces if t.get("time") is None]
    
    # 有时间戳的按时间倒序排列
    sorted_traces = sorted(timed_traces, key=lambda x: x["time"], reverse=True)
    
    lines = []
    lines.append("=" * 80)
    lines.append("TraceFinder 用户行为时间线报告")
    lines.append("=" * 80)
    lines.append("")
    
    if not all_traces:
        lines.append("未提取到任何痕迹")
        return "\n".join(lines)
    
    lines.append(f"共提取 {len(all_traces)} 条痕迹（{len(sorted_traces)} 条有时间戳，{len(untimed_traces)} 条无精确时间）")
    lines.append("")
    lines.append("-" * 80)
    
    for trace in sorted_traces:
        time_str = trace.get("time_str", "未知时间")
        trace_type = trace.get("type", "未知")
        content = trace.get("content", "")
        
        # 标记可疑行为
        if trace.get("suspicious"):
            flag = "【可疑】"
            reason = f" - {trace.get('suspicious_reason', '')}"
        else:
            flag = ""
            reason = ""
        
        lines.append(f"{time_str} [{trace_type}] {content} {flag}{reason}")
    
    lines.append("-" * 80)
    lines.append("")
    
    # 显示无时间戳的痕迹
    if untimed_traces:
        lines.append("【无精确时间的痕迹】")
        lines.append("")
        for trace in untimed_traces:
            trace_type = trace.get("type", "未知")
            content = trace.get("content", "")
            lines.append(f"[{trace_type}] {content}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")
    
    # 统计可疑行为
    suspicious_traces = [t for t in all_traces if t.get("suspicious")]
    if suspicious_traces:
        lines.append(f"发现 {len(suspicious_traces)} 条可疑行为：")
        for trace in suspicious_traces:
            lines.append(f"  - [{trace.get('type')}] {trace.get('content')}")
            lines.append(f"    原因：{trace.get('suspicious_reason', '未知')}")
    else:
        lines.append("未发现可疑行为")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)
