import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== 配置 ==========
SKILL_JSON = "skill.json"                       # 你的技能数据文件
OUTPUT_DIR = "images/icons"                     # 图标保存目录
BASE_URL = "https://cloudstorage.d2core.com/data_img/d4/skill/"   # 官方 CDN

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_icon(skill):
    key = skill.get("key")
    icon_id = skill.get("icon")
    if not key or not icon_id:
        return None
    url = BASE_URL + str(icon_id) + ".png"
    filename = os.path.join(OUTPUT_DIR, f"{key}.png")
    if os.path.exists(filename):
        return f"已存在: {key}.png"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            with open(filename, "wb") as f:
                f.write(resp.content)
            return f"下载成功: {key}.png"
        else:
            return f"下载失败 {key}: HTTP {resp.status_code}"
    except Exception as e:
        return f"下载异常 {key}: {str(e)}"

def main():
    with open(SKILL_JSON, "r", encoding="utf-8") as f:
        skills = json.load(f)
    print(f"共 {len(skills)} 个技能")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_icon, skill): skill for skill in skills}
        for future in as_completed(futures):
            result = future.result()
            if result:
                print(result)

if __name__ == "__main__":
    main()