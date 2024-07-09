import requests
import pandas as pd
from pandas import json_normalize
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time

# 发送请求以获取总项目数和每页限制数
response = requests.get("https://gobricks.cn/frontend/v1/item/filter?type=2&limit=96&page=1&order_direction=asc&variety=all")
data = response.json()
total_items = data['count']  # 获取总项目数
limit_per_page = data['limit']  # 获取每页限制数

# 计算总页数
total_pages = total_items // limit_per_page + (1 if total_items % limit_per_page else 0)

# 基于当前时间生成文件名
filename = "gobrick_data_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".xlsx"

# 定义 CSV 文件的字段名
fieldnames = ["id", "product_id", "caption", "picture", "pictures", "eshop_price", "price", "caption_en", "discount", "type", "color_id", "ldd_catalog", "inventory", "buy_limit", "ldraw_no", "mpd_sign", "ldd_code", "sale_volume", "rand", "variety"]

# 增加 color_data 里面的字段名
color_data_fieldnames = ["color_data.main_id", "color_data.id", "color_data.name", "color_data.lego_color_id", "color_data.font-color", "color_data.color", "color_data.colorType", "color_data.ldraw_color_id", "color_data.ldraw_color_value", "color_data.index", "color_data.name_en", "color_data.is_show"]

# 合并两个字段名列表
all_fieldnames = fieldnames + color_data_fieldnames

def fetch_data(page_id):
    url = f"https://gobricks.cn/frontend/v1/item/filter?type=2&limit={limit_per_page}&page={page_id}&order_direction=asc&variety=all"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        items = data.get('rows', [])
        if not items:
            return None
        df = json_normalize(items)
        for field in all_fieldnames:
            if field not in df.columns:
                df[field] = None
        return df[all_fieldnames]
    else:
        return None

def save_to_excel(df_list, filename):
    all_data = pd.concat(df_list, ignore_index=True)
    all_data.to_excel(filename, index=False)

# 设置线程池的大小为 20
max_workers = 20

# 使用 ThreadPoolExecutor 来并发执行网络请求
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # 使用 tqdm 来显示进度条
    futures = [executor.submit(fetch_data, pid) for pid in range(1, total_pages + 1)]
    results = list(tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="采集数据"))

# 过滤掉返回 None 的结果
valid_results = [f.result() for f in results if f.result() is not None]

# 如果有有效数据，则保存到 Excel 文件中
if valid_results:
    save_to_excel(valid_results, filename)
    print(f"数据采集完成，已保存到 {filename} 文件中。")
else:
    print("没有采集到任何数据。")
