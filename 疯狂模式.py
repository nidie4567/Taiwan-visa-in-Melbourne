import asyncio
import aiohttp
from itertools import product

# 目标提交 URL 用于预约
appointment_url = "https://csts.immigration.gov.tw/HKMO/apply/setAppointmentSet"

# 请求头（模拟浏览器）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

# 日期和时间组合【请修改此处】
dates = ["2024/11/25", "2024/11/26", "2024/11/27", "2024/11/28", "2024/11/29", "2024/12/02", "2024/12/03", "2024/12/04"]
times = ["09:00", "11:00", "13:00", "14:00"]

# 生成所有日期和时间的组合
date_time_combinations = list(product(dates, times))

# 全局变量：控制停止标志
stop_flag = False
lock = asyncio.Lock()

# 返回次数计数器
response_counter = 1

# 异步发送表单请求并处理响应
async def make_appointment(session, appDate, appTime):
    global stop_flag, response_counter
    form_data = {
        "appDate": appDate,  # 日期
        "appTime": appTime,  # 时间
        "applicationNo": "Mjg0OTk0OTQ5MzFhYsd1f3s1mYTAxOsd1f3s1lNWU=",  # 请在浏览器预约界面按F12查找，是一长串字母和数字的组合，最后还有等号【请修改此处】
        "overseaOfficeId": "MTA5",  # 已知的其他隐藏字段
        "applyType": "D",
        "overseaOfficeIdOrginal": "109"
    }

    try:
        async with session.post(appointment_url, data=form_data, headers=headers) as response:
            print(f"第 {response_counter} 次请求已发送！日期: {appDate}, 时间: {appTime}")

            # 处理响应
            response_text = await response.text()
            if response.status == 200:
                print(f"第 {response_counter} 次收到响应！日期: {appDate}, 时间: {appTime}")
                if "已預約成功" in response_text:
                    print(f"预约成功！第 {response_counter} 次响应。")
                    # 如果有请求成功，设置停止标志
                    async with lock:
                        if not stop_flag:
                            stop_flag = True
                            print("预约成功，所有任务停止运行。")
            else:
                print(f"第 {response_counter} 次请求失败！日期: {appDate}, 时间: {appTime}，状态码: {response.status}")
            
            # 增加返回次数
            response_counter += 1

    except Exception as e:
        print(f"第 {response_counter} 次请求提交时发生异常！日期: {appDate}, 时间: {appTime}，错误信息: {e}")
        # 增加返回次数
        response_counter += 1

# 处理每个日期时间组合的任务，任务会循环执行
async def task_loop(session, appDate, appTime):
    while not stop_flag:
        # 发起预约请求
        await make_appointment(session, appDate, appTime)
        
        # 如果预约成功，停止循环
        if stop_flag:
            break

        # 每个任务完成一次后间隔1秒继续发起下一次请求【请修改此处】
        await asyncio.sleep(1)

# 主程序
async def main():
    async with aiohttp.ClientSession() as session:
        tasks = []

        # 为每个日期时间组合启动一个独立的异步任务
        for appDate, appTime in date_time_combinations:
            task = asyncio.create_task(task_loop(session, appDate, appTime))
            tasks.append(task)

        # 等待所有任务完成
        await asyncio.gather(*tasks)

# 启动程序
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程序被中断，所有任务停止。")
