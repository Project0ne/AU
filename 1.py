import urllib3
urllib3.disable_warnings()

import csv
import pandas as pd
import requests
from requests.sessions import Session
import concurrent.futures
from tqdm import tqdm
import time

# 定义 CSV 文件的字段名
fieldnames = ["id", "product_id", "caption", "picture", "pictures", "eshop_price", "price", "caption_en", "color_id", "ldd_catalog", "inventory", "ldraw_no","ldd_code", "sale_volume", "rand"]
color_data_fieldnames = ["main_id","id", "name", "lego_color_id", "font-color", "color", "colorType", "ldraw_color_id", "ldraw_color_value", "index", "name_en"]
all_fieldnames = fieldnames + color_data_fieldnames

# 基于当前时间生成文件名
filename = "gobrick_data_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"

# 使用 requests.Session() 来复用连接
session = Session()

def fetch_data(page):
    # 要从中获取数据的 URL
    url = f'https://gobricks.cn/frontend/v1/item/filter?type=2&page={page}&order_direction=desc&variety=all&orderby=default'
    try:
        # 使用 session 发送 GET 请求到 URL 并存储响应
        response = session.get(url, verify=False)
        response.raise_for_status()  # 如果请求失败，抛出HTTPError异常
    except (requests.exceptions.HTTPError, requests.exceptions.ProxyError) as e:
        print("Error occurred:", e)
        return []

    # 解析响应数据
    data = response.json()['rows']
    if not data:  # 如果页面没有数据，返回空列表
        return []

    filtered_data = []
    for d in data:
        # 处理 color_data 和 ldraw_no 字段
        # ...（省略了处理逻辑，与原始代码相同）...
        filtered_data.append({k: v for k, v in d.items() if k in all_fieldnames})
    return filtered_data

# 设置线程池的大小
max_workers = 20

# 初始化进度条
pbar = tqdm()

with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    # 以 utf-8 编码打开 CSV 文件并将数据写入其中
    with open(filename, "a", newline="", encoding="utf-8_sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)
        if csvfile.tell() == 0:
            writer.writeheader()

        page = 1
        while True:
            # 将请求提交给执行器并将数据写入 CSV 文件
            future_to_page = {executor.submit(fetch_data, page+i): page+i for i in range(max_workers)}
            for future in concurrent.futures.as_completed(future_to_page):
                page_data = future.result()
                if not page_data:  # 如果页面没有数据，结束循环
                    pbar.close()
                    break  # 使用 break 代替 return
                for d in page_data:
                    writer.writerow(d)
                pbar.update(1)
            page += max_workers
