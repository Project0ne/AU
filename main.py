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

# 获取产品重量的函数
def fetch_weight(session, product_id):
    url = f"https://gobricks.cn/frontend/v1/item/detail?id={product_id}"
    response = session.get(url)
    return response.json().get('product_weight', None)

# 主函数
def main():
    total_count, total_pages = get_total_pages_and_count()
    progress_bar = tqdm(total=total_pages, desc='Fetching data', mininterval=1.0)

    all_data = []
    product_ids = []
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(fetch_data, session, page): page for page in range(1, total_pages + 1)}
            for future in as_completed(futures):
                try:
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
                        product_ids.append(row['id'])
                except Exception as e:
                    print(f"Error fetching data for page {futures[future]}: {e}")
                progress_bar.update(1)

    progress_bar.close()

    # 获取每个产品的重量信息
    progress_bar = tqdm(total=len(product_ids), desc='Fetching weights', mininterval=1.0)
    weights = {}
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(fetch_weight, session, product_id): product_id for product_id in product_ids}
            for future in as_completed(futures):
                product_id = futures[future]
                try:
                    weight = future.result()
                    weights[product_id] = weight
                except Exception as e:
                    print(f"Error fetching weight for product {product_id}: {e}")
                progress_bar.update(1)

    progress_bar.close()

    # 添加重量信息到数据中
    for data in all_data:
        data['product_weight'] = weights.get(data['id'], None)

    # 创建DataFrame
    df = pd.DataFrame(all_data)

    # 保存到Excel文件
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"GBAD_{total_count}_{timestamp}.xlsx"
    df.to_excel(filename, index=False)

    print(f"Data collection complete! Data saved to {filename}")

if __name__ == "__main__":
    main()
