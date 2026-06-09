"""
剪贴板历史提取模块
提取Windows 10/11剪贴板历史记录
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


def get_clipboard_history():
    """提取Windows剪贴板历史"""
    results = []
    clip_db_path = os.path.expanduser(
        r"~\AppData\Local\Microsoft\Windows\Clipboard\history.db"
    )
    
    if not os.path.exists(clip_db_path):
        return results
    
    # 复制数据库文件避免占用锁
    temp_db = os.path.join(os.environ.get('TEMP', '.'), "clip_temp.db")
    try:
        shutil.copy2(clip_db_path, temp_db)
    except (PermissionError, OSError):
        return results
    
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Payload, Timestamp FROM ClipboardHistory ORDER BY Timestamp DESC"
        )
        
        for row in cursor.fetchall():
            payload, ts_bytes = row
            ts = filetime_to_datetime(ts_bytes)
            if ts is None:
                continue
            
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                # 解析文本内容
                if isinstance(payload, bytes) and payload.startswith(b'\x00\x01'):
                    text = payload[4:].decode('utf-16-le', errors='ignore').strip('\x00')
                    if text:
                        results.append({
                            "type": "剪贴板复制",
                            "time": ts,
                            "time_str": time_str,
                            "content": f"文本：{text[:100]}"
                        })
            except Exception:
                continue
        
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
