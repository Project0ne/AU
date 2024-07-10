import requests
import pandas as pd
from tqdm import tqdm
from datetime import datetime

# 获取总页数的函数
def get_total_pages():
    response = requests.get("https://gobricks.cn/frontend/v1/item/filter?type=2&limit=96&page=1&order_direction=asc&variety=all")
    data = response.json()
    total_count = data['count']
    return (total_count // 96) + (1 if total_count % 96 != 0 else 0)

# 采集数据的函数
def fetch_data(page):
    url = f"https://gobricks.cn/frontend/v1/item/filter?type=2&limit=96&page={page}&order_direction=asc&variety=all"
    response = requests.get(url)
    return response.json()['rows']

# 主函数
def main():
    total_pages = get_total_pages()
    progress_bar = tqdm(total=total_pages, desc='Fetching data')

    all_data = []
    for page in range(1, total_pages + 1):
        rows = fetch_data(page)
        for row in rows:
            # 提取color_data中的数据并合并到主字典中
            color_data = row.pop('color_data')
            row.update({
                'main_id': color_data['main_id'],
                'name': color_data['name'],
                'lego_color_id': color_data['lego_color_id'],
                'color': color_data['color'],
                'colorType': color_data['colorType'],
                'ldraw_color_id': color_data['ldraw_color_id'],
                'ldraw_color_value': color_data['ldraw_color_value'],
                'index': color_data['index'],
                'name_en': color_data['name_en'],
            })
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
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"gobrick_all_data_{timestamp}.xlsx"
    df.to_excel(filename, index=False)

    print(f"Data collection complete! Data saved to {filename}")

if __name__ == "__main__":
    main()
