import requests
import json
import datetime

def get_crypto_fng():
    """获取加密货币恐慌贪婪指数"""
    try:
        response = requests.get("https://api.alternative.me/fng/")
        data = response.json()
        return {
            "value": data['data'][0]['value'],
            "classification": data['data'][0]['value_classification']
        }
    except:
        return {"value": "N/A", "classification": "Error"}

def get_world_bank_cpi(country_codes):
    """从世界银行获取指定国家的最新 CPI 数据，增加容错和调试日志"""
    cpi_results = {}
    for code in country_codes:
        try:
            # 修改点 1：增加 per_page=10，防止最新的年份数据缺失，我们往回找 2-3 年
            url = f"https://api.worldbank.org/v2/country/{code}/indicator/FP.CPI.TOTL.ZG?format=json&per_page=10"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # 世界银行 API 结构: [ {元数据}, [ {数据点1}, {数据点2}... ] ]
            if len(data) > 1 and data[1]:
                # 寻找第一个非空的数值
                latest_entry = next((item for item in data[1] if item['value'] is not None), None)
                
                if latest_entry:
                    val = latest_entry['value']
                    year = latest_entry['date']
                    cpi_results[code] = {"value": round(val, 2), "year": year}
                    print(f"成功获取 {code}: {val}% ({year})")
                else:
                    cpi_results[code] = {"value": "暂无数据", "year": "N/A"}
            else:
                cpi_results[code] = {"value": "接口错误", "year": "N/A"}
        except Exception as e:
            print(f"获取 {code} 失败: {e}")
            cpi_results[code] = {"value": "请求失败", "year": "N/A"}
    return cpi_results

def get_next_fed_meeting():
    """计算下一个美联储议息会议日期 (2026年示例)"""
    # 2026年美联储议息会议日期 (根据官方公布日期)
    meetings = [
        "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16"
    ]
    now = datetime.datetime.now()
    future_meetings = [datetime.datetime.strptime(m, "%Y-%m-%d") for m in meetings if datetime.datetime.strptime(m, "%Y-%m-%d") > now]
    
    if future_meetings:
        next_m = future_meetings[0]
        return next_m.strftime("%Y-%m-%d")
    return "TBD"

def main():
    # 1. 定义要追踪的国家 (ISO 代码)
    # 美国(USA), 中国(CHN), 日本(JPN), 英国(GBR), 德国(DEU), 印度(IND), 巴西(BRA)
    countries = ["USA", "CHN", "JPN", "GBR", "DEU", "IND", "BRA", "SGP"]
    
    print("正在获取数据...")
    
    final_data = {
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "crypto_fng": get_crypto_fng(),
        "inflation_rates": get_world_bank_cpi(countries),
        "next_fed_meeting": get_next_fed_meeting()
    }

    # 2. 计算“宏观红绿灯”简单逻辑 (示例: 以美国CPI和Crypto情绪为基准)
    # 绿灯: 1, 黄灯: 2, 红灯: 3
    status = 2 # 默认中性
    try:
        us_cpi = final_data["inflation_rates"]["USA"]["value"]
        fng_val = int(final_data["crypto_fng"]["value"])
        
        if us_cpi < 3.0 and fng_val < 30: # 通胀降温且市场恐慌 -> 机会
            status = 1
        elif us_cpi > 5.0 or fng_val > 75: # 通胀高企或过度贪婪 -> 风险
            status = 3
    except:
        pass
    
    final_data["macro_light"] = status

    # 3. 保存为 json 文件
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    print("数据更新成功，已保存至 data.json")

if __name__ == "__main__":
    main()