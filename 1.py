import requests
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 获取总页数和总计数的函数
def get_total_pages_and_count():
    response = requests.get("https://gobricks.cn/frontend/v1/item/filter?type=2&limit=96&page=1&order_direction=asc&variety=all")
    data = response.json()
    total_count = data['count']
    total_pages = (total_count // 96) + (1 if total_count % 96 != 0 else 0)
    return total_count, total_pages

# 采集数据的函数
def fetch_data(session, page):
    url = f"https://gobricks.cn/frontend/v1/item/filter?type=2&limit=96&page={page}&order_direction=asc&variety=all"
    response = session.get(url)
    return response.json()['rows']

# 主函数
def main():
    total_count, total_pages = get_total_pages_and_count()
    progress_bar = tqdm(total=total_pages, desc='Fetching data', mininterval=1.0)

    all_data = []
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_data, session, page): page for page in range(1, total_pages + 1)}
            for future in as_completed(futures):
                rows = future.result()
                for row in rows:
                    # 提取color_data中的数据并重命名id为color_id
                    color_data = row.pop('color_data')
                    color_data['color_id'] = color_data.pop('id')
                    row.update(color_data)
                    # 只保留指定的字段
                    selected_data = {key: row[key] for key in row if key in [
                        "id", "product_id", "caption", "picture", "price", "caption_en",
                        "color_id", "ldd_catalog", "inventory", "ldraw_no", "ldd_code",
                        "sale_volume", "rand", "main_id", "name", "lego_color_id",
                        "color", "colorType", "ldraw_color_id", "ldraw_color_value",
                        "index", "name_en"
                    ]}
                    all_data.append(selected_data)
                progress_bar.update(1)

    progress_bar.close()

    # 创建DataFrame
    df = pd.DataFrame(all_data)

    # 保存到Excel文件
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"GBAD_{total_count}_{timestamp}.xlsx"
    df.to_excel(filename, index=False)

    print(f"Data collection complete! Data saved to {filename}")

if __name__ == "__main__":
    main()
