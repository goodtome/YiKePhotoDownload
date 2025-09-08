import requests
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

class BaiduPhoto:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        self.URL = "https://photo.baidu.com/youai/file/v2/download?clienttype={clienttype}&bdstoken={bdstoken}&fsid={fsid}"
        self.json_path = "./json/"
        self.save_path = "./BauduPhoto/"
        self.clienttype = None
        self.bdstoken = None
        self.folder_names = []
        self.max_workers = 8
        # Ensure base save directory exists
        os.makedirs(self.save_path, exist_ok=True)
    
    # 单文件处理逻辑（读取 JSON、获取下载链接、保存文件）
    def _process_one_file(self, file_name):
        try:
            with open(self.json_path + file_name, 'r', encoding="utf-8") as f:
                json_data = json.load(f)

            date = json_data["extra_info"]["date_time"][:10].replace(':', '-')
            filename = json_data["path"][12:]
            fsid = json_data["fsid"]

            # 目标路径与目录
            target_dir = self.save_path + date
            os.makedirs(target_dir, exist_ok=True)
            target_file_path = target_dir + '/' + filename

            # 已存在则跳过
            if os.path.exists(target_file_path):
                print(f"{date}, {filename}, SKIP (exists). ")
                return

            # 获得下载链接
            resp_meta = requests.get(
                self.URL.format(clienttype=self.clienttype, bdstoken=self.bdstoken, fsid=fsid),
                headers=self.headers,
                timeout=30
            )
            if resp_meta.status_code != 200:
                print(f"{date}, {filename}, META {resp_meta.status_code}")
                return
            r_json = resp_meta.json()
            download_url = r_json.get('dlink')
            if not download_url:
                print(f"{date}, {filename}, NO DLINK")
                return

            # 下载图片
            resp_file = requests.get(download_url, headers=self.headers, timeout=60)
            print(f"{date}, {filename}, {resp_file.status_code}. ")
            if resp_file.status_code != 200:
                return
            # 确保父目录存在（文件名可能包含子路径）
            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
            with open(target_file_path, 'wb') as f:
                f.write(resp_file.content)
        except Exception as e:
            print(f"ERROR {file_name}: {e}")
    
    # 并发下载图片
    def download_photo(self):
        files = [f for f in os.listdir(self.json_path) if f.endswith('.json')]
        if not files:
            print("No json files found.")
            return
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._process_one_file, file_name) for file_name in files]
            for _ in as_completed(futures):
                pass
    
    def start(self):
        with open("settings.json", 'r') as f:
            json_data = json.load(f)
        self.clienttype = json_data["clienttype"]
        self.bdstoken = json_data["bdstoken"]
        self.headers["Cookie"] = json_data["Cookie"]
        # 可选的并发线程数配置
        self.max_workers = int(json_data.get("max_workers", (os.cpu_count() or 2) * 4))

        self.download_photo()      
    

if __name__ == "__main__":
    baidu_photo = BaiduPhoto()
    baidu_photo.start()