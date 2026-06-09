"""
社交软件非聊天痕迹提取模块
提取微信/QQ缓存目录中的文件接收记录、头像缓存等
"""
import os
import datetime
import glob


def get_wechat_cache_traces():
    """提取微信缓存目录中的痕迹"""
    results = []
    base_path = os.path.expanduser(r"~\Documents\WeChat Files")
    
    if not os.path.exists(base_path):
        return results
    
    # 遍历所有微信账号目录
    for account_dir in os.listdir(base_path):
        account_path = os.path.join(base_path, account_dir)
        if not os.path.isdir(account_path):
            continue
        
        # 提取FileStorage中的文件记录
        filestorage_path = os.path.join(account_path, "FileStorage")
        if os.path.exists(filestorage_path):
            # 文件接收记录
            for subdir in ["File", "Video", "Image"]:
                subdir_path = os.path.join(filestorage_path, subdir)
                if os.path.exists(subdir_path):
                    try:
                        for item in os.listdir(subdir_path):
                            item_path = os.path.join(subdir_path, item)
                            if os.path.isdir(item_path):
                                # 按月组织的文件夹
                                for filename in os.listdir(item_path)[:10]:
                                    filepath = os.path.join(item_path, filename)
                                    mtime = datetime.datetime.fromtimestamp(
                                        os.path.getmtime(filepath)
                                    )
                                    results.append({
                                        "type": "微信文件",
                                        "time": mtime,
                                        "time_str": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                                        "content": f"{subdir}：{filename}"
                                    })
                    except OSError:
                        pass
        
        # 提取头像缓存
        avatar_path = os.path.join(account_path, "HeadImage")
        if os.path.exists(avatar_path):
            try:
                for item in os.listdir(avatar_path)[:5]:
                    item_path = os.path.join(avatar_path, item)
                    mtime = datetime.datetime.fromtimestamp(
                        os.path.getmtime(item_path)
                    )
                    results.append({
                        "type": "微信头像缓存",
                        "time": mtime,
                        "time_str": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                        "content": f"头像：{item}"
                    })
            except OSError:
                pass
    
    return results


def get_qq_cache_traces():
    """提取QQ缓存目录中的痕迹"""
    results = []
    base_path = os.path.expanduser(r"~\Documents\Tencent Files")
    
    if not os.path.exists(base_path):
        return results
    
    for account_dir in os.listdir(base_path):
        account_path = os.path.join(base_path, account_dir)
        if not os.path.isdir(account_path) or not account_dir.isdigit():
            continue
        
        # 提取图片缓存
        image_path = os.path.join(account_path, "Image")
        if os.path.exists(image_path):
            try:
                for subdir in os.listdir(image_path)[:5]:
                    subdir_path = os.path.join(image_path, subdir)
                    if os.path.isdir(subdir_path):
                        for filename in os.listdir(subdir_path)[:5]:
                            filepath = os.path.join(subdir_path, filename)
                            mtime = datetime.datetime.fromtimestamp(
                                os.path.getmtime(filepath)
                            )
                            results.append({
                                "type": "QQ图片",
                                "time": mtime,
                                "time_str": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                                "content": f"图片：{filename}"
                            })
            except OSError:
                pass
        
        # 提取文件记录
        file_path = os.path.join(account_path, "FileRecv")
        if os.path.exists(file_path):
            try:
                for filename in os.listdir(file_path)[:10]:
                    filepath = os.path.join(file_path, filename)
                    mtime = datetime.datetime.fromtimestamp(
                        os.path.getmtime(filepath)
                    )
                    results.append({
                        "type": "QQ文件",
                        "time": mtime,
                        "time_str": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                        "content": f"接收文件：{filename}"
                    })
            except OSError:
                pass
    
    return results


def get_social_app_traces():
    """获取社交软件非聊天痕迹（综合）"""
    results = []
    results.extend(get_wechat_cache_traces())
    results.extend(get_qq_cache_traces())
    return results
