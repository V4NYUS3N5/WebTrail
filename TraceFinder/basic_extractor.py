"""
基础痕迹提取模块
提取USB接入记录、最近运行程序、自启动项、最近打开文件等
"""
import winreg
import os
import datetime
import glob


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


def get_usb_records():
    """从注册表提取USB设备接入记录"""
    results = []
    usb_path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, usb_path, 0, winreg.KEY_READ
        )
        count = winreg.QueryInfoKey(key)[0]
        
        for i in range(count):
            try:
                device_name = winreg.EnumKey(key, i)
                device_key_path = f"{usb_path}\\{device_name}"
                device_key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE, device_key_path, 0, winreg.KEY_READ
                )
                
                try:
                    serial = winreg.EnumKey(device_key, 0)
                    serial_key_path = f"{device_key_path}\\{serial}"
                    serial_key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE, serial_key_path, 0, winreg.KEY_READ
                    )
                    
                    friendly_name, _ = winreg.QueryValueEx(serial_key, "FriendlyName")
                    
                    results.append({
                        "type": "USB接入",
                        "time": None,
                        "time_str": "历史记录",
                        "content": f"设备：{friendly_name} | 序列号：{serial}"
                    })
                    
                    winreg.CloseKey(serial_key)
                except OSError:
                    pass
                
                winreg.CloseKey(device_key)
            except OSError:
                continue
        
        winreg.CloseKey(key)
    except (OSError, PermissionError):
        pass
    
    return results


def get_recent_programs():
    """从注册表提取最近运行程序（RunMRU）"""
    results = []
    mru_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, mru_path)
        count = winreg.QueryInfoKey(key)[1]
        
        for i in range(count):
            try:
                name, value, _ = winreg.EnumValue(key, i)
                if name != "MRUList" and value:
                    results.append({
                        "type": "最近运行",
                        "time": None,
                        "time_str": "历史记录",
                        "content": f"命令：{value[:100]}"
                    })
            except OSError:
                continue
        
        winreg.CloseKey(key)
    except OSError:
        pass
    
    return results


def get_autostart_items():
    """提取自启动项"""
    results = []
    autostart_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ]
    
    for hive, path in autostart_paths:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            count = winreg.QueryInfoKey(key)[1]
            
            for i in range(count):
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    results.append({
                        "type": "自启动项",
                        "time": None,
                        "time_str": "历史记录",
                        "content": f"名称：{name} | 路径：{value[:100]}"
                    })
                except OSError:
                    continue
            
            winreg.CloseKey(key)
        except OSError:
            pass
    
    return results


def get_recent_files():
    """提取最近打开的文件（Recent文件夹）"""
    results = []
    recent_path = os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Recent")
    
    if not os.path.exists(recent_path):
        return results
    
    try:
        for item in os.listdir(recent_path):
            if item.endswith('.lnk'):
                filepath = os.path.join(recent_path, item)
                mtime = datetime.datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                )
                results.append({
                    "type": "最近文件",
                    "time": mtime,
                    "time_str": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "content": f"文件：{item[:-4]}"
                })
    except OSError:
        pass
    
    return results


def get_prefetch_records():
    """提取Prefetch程序运行记录"""
    results = []
    prefetch_dir = r"C:\Windows\Prefetch"
    
    if not os.path.exists(prefetch_dir):
        return results
    
    try:
        for filename in os.listdir(prefetch_dir):
            if filename.endswith('.pf'):
                filepath = os.path.join(prefetch_dir, filename)
                mtime = datetime.datetime.fromtimestamp(
                    os.path.getmtime(filepath)
                )
                results.append({
                    "type": "Prefetch记录",
                    "time": mtime,
                    "time_str": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "content": f"程序：{filename[:-3]}"
                })
    except OSError:
        pass
    
    return results


def get_basic_traces():
    """获取基础痕迹（综合）"""
    results = []
    results.extend(get_usb_records())
    results.extend(get_recent_programs())
    results.extend(get_autostart_items())
    results.extend(get_recent_files())
    results.extend(get_prefetch_records())
    return results
