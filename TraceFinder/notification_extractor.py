"""
系统通知历史提取模块
提取Windows通知中心历史记录（微信/QQ消息预览、下载通知等）
"""
import sqlite3
import os
import shutil
import datetime


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


def get_notification_history():
    """提取Windows通知中心历史"""
    results = []
    notif_db_path = os.path.expanduser(
        r"~\AppData\Local\Microsoft\Windows\Notifications\wpndatabase.db"
    )
    
    if not os.path.exists(notif_db_path):
        return results
    
    # 复制数据库文件避免占用锁
    temp_db = os.path.join(os.environ.get('TEMP', '.'), "notif_temp.db")
    try:
        shutil.copy2(notif_db_path, temp_db)
    except (PermissionError, OSError):
        return results
    
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # 查询通知表
        cursor.execute("""
            SELECT Id, AppId, Content, ExpirationTime, DeliveryTime 
            FROM Notification 
            ORDER BY DeliveryTime DESC
        """)
        
        for row in cursor.fetchall():
            notif_id, app_id, content, expiration, delivery_time = row
            
            ts = filetime_to_datetime(delivery_time) if delivery_time else None
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "未知时间"
            
            # 解析通知内容
            content_text = ""
            if content:
                try:
                    # 通知内容通常是XML格式
                    content_str = content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else str(content)
                    # 简单提取文本内容
                    import re
                    text_matches = re.findall(r'<text[^>]*>(.*?)</text>', content_str)
                    if text_matches:
                        content_text = " | ".join(text_matches[:3])[:100]
                    else:
                        content_text = content_str[:100]
                except Exception:
                    content_text = str(content)[:100]
            
            # 识别应用类型
            app_type = "系统通知"
            if app_id:
                app_lower = app_id.lower()
                if 'wechat' in app_lower or 'weixin' in app_lower:
                    app_type = "微信通知"
                elif 'qq' in app_lower:
                    app_type = "QQ通知"
                elif 'chrome' in app_lower or 'edge' in app_lower:
                    app_type = "浏览器通知"
                elif 'pan' in app_lower or 'baidu' in app_lower:
                    app_type = "网盘通知"
            
            results.append({
                "type": app_type,
                "time": ts,
                "time_str": time_str,
                "content": f"通知：{content_text}" if content_text else f"应用：{app_id}"
            })
        
        conn.close()
    except sqlite3.Error:
        pass
    finally:
        if os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except OSError:
                pass
    
    return results
