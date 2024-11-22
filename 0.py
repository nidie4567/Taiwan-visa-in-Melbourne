import requests
import time
from bs4 import BeautifulSoup
import re

# 目标提交 URL 用于预约
appointment_url = "https://csts.immigration.gov.tw/HKMO/apply/setAppointmentSet"

# 请求头（模拟浏览器）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

# 参数数据 用于查询空余预约时间
calendar_url = "https://csts.immigration.gov.tw/HKMO/apply/getCalendarList"
params = {
    'day': 0,
    'month': 0,
    'officesAbroadId': "109"
}

# 时间映射，行号与时间对应关系
time_mapping = {0: "09:00", 1: "10:00", 2: "11:00", 3: "13:00", 4: "14:00"}

# 记录查询次数和失败次数
query_count = 0
failure_count = 0

# 获取未额满的日期和时间
def get_available_time():
    global query_count
    query_count += 1  # 每次查询时增加计数器

    try:
        response = requests.post(calendar_url, data=params, headers=headers)
        if response.status_code == 200:
            print(f"请求成功！正在解析响应内容... (查询次数: {query_count})")

            # 打印返回的 HTML 内容
            #print(response.text)  # 取消注释可以帮助调试

            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 获取所有表格行
            rows = soup.find_all('tr')

            appDate = None
            appTime = None

            # 提取表格中的数据
            for row_idx, row in enumerate(rows[1:]):  # 跳过第一行表头
                cells = row.find_all('td')

                # 遍历每一列，查找是否有 "未額滿"
                for col_idx, cell in enumerate(cells[1:], start=1):  # 跳过第一列
                    if "未額滿" in cell.get_text():
                        # 使用正则表达式提取日期（yyyy/mm/dd 格式）
                        date_text = rows[0].find_all('td')[col_idx].get_text()
                        match = re.search(r'(\d{4}/\d{2}/\d{2})', date_text)  # 正则匹配日期
                        if match:
                            appDate = match.group(1)  # 提取匹配到的日期
                        appTime = time_mapping.get(row_idx)  # 获取时间
                        break
                if appDate and appTime:
                    break

            # 如果找到未满的预约时间
            if appDate and appTime:
                print(f"找到可预约时间！日期: {appDate}, 时间: {appTime}")
                return appDate, appTime
            else:
                print("没有找到可预约的日期和时间。")
                return None, None
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None, None
    except Exception as e:
        print("请求出错：", e)
        return None, None

# 发送表单请求进行预约
def make_appointment(appDate, appTime):
    global failure_count
    form_data = {
        "appDate": appDate,  # 日期
        "appTime": appTime,  # 时间
        "applicationNo": "Mjg0OTk0OTM5MzFhY2RhNjAxOTM0MjYwYjQzNTBhMGU=",  # 请在浏览器预约界面按F12查找，是一长串字母和数字的组合，最后还有等个号
        "overseaOfficeId": "MTA5",  # 已知的其他隐藏字段
        "applyType": "D",
        "overseaOfficeIdOrginal": "109"
    }

    try:
        # 发送 POST 请求
        response = requests.post(appointment_url, data=form_data, headers=headers)

        # 检查响应状态
        if response.status_code == 200:
            print("表单提交成功！响应：", response.text)
            # 检查是否包含“已預約成功”
            if "已預約成功" in response.text:
                print("预约成功，停止循环！")
                return True  # 返回成功
            else:
                print("预约未成功，继续尝试...")
                failure_count += 1  # 预约失败时增加计数器
                print(f"预约失败次数: {failure_count}")
                return False  # 返回失败
        else:
            print(f"表单提交失败，状态码: {response.status_code}")
            failure_count += 1  # 预约失败时增加计数器
            print(f"预约失败次数: {failure_count}")
            return False  # 返回失败
    except Exception as e:
        print("提交时出错：", e)
        failure_count += 1  # 预约失败时增加计数器
        print(f"预约失败次数: {failure_count}")
        return False  # 返回失败

# 主程序：循环查询并尝试预约
while True:
    # 获取未额满的时间
    appDate, appTime = get_available_time()

    if appDate and appTime:
        # 如果找到空余时间，尝试预约
        success = make_appointment(appDate, appTime)
        if success:
            break  # 预约成功，停止程序
    else:
        print("Rowan-0等待下一次查询...")
        time.sleep(0.5)  # 每 1 秒查询一次
