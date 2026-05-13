import hashlib
import json
import os
import time

import requests
from playwright.sync_api import sync_playwright

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "Origin": "http://xjtudj.edu.cn",
    "Proxy-Connection": "keep-alive",
    "Referer": "http://xjtudj.edu.cn/djnfo.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    "X-Requested-With": "XMLHttpRequest",
}


class XJTULoginHelper:
    """获取并持久化登录参数"""

    def __init__(self):
        self.login_url = "http://xjtudj.edu.cn/djnfo.html?navId=zone_index&zTempId=basicInfo"
        self.cookie_file = "cookies_cache.json"
        self.auth_params = {}

    def _save_to_file(self, data):
        with open(self.cookie_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _load_from_file(self):
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return None
        return None

    def _check_validity(self, params):
        """通过调用一个简单接口验证 Cookie 是否依然有效"""
        test_url = "http://xjtudj.edu.cn/partyconstruction/client/schedule/selectScheduleList"
        # 构造一个简单的校验请求
        timestamp = int(time.time()) * 1000
        raw_str = f"{timestamp}{params['dj_token']}{params['dj_key']}"
        encode_token = hashlib.md5(raw_str.encode("utf-8")).hexdigest()

        payload = {
            "userId": params["dj_usrId"],
            "time": timestamp,
            "encodeToken": encode_token,
            "type": "all",
        }
        cookies = {
            "SESSION": params["SESSION"],
            "dj_usrId": params["dj_usrId"],
            "dj_token": params["dj_token"],
            "dj_key": params["dj_key"],
            "login_type": "caslogin",
        }
        try:
            # 设置较短的超时
            resp = requests.post(test_url, json=payload, headers=HEADERS, cookies=cookies, timeout=5).json()
            # 如果返回 login 为 True 且 isSuccess 为 True，说明 Cookie 有效
            return resp.get("login") is True and resp.get("isSuccess") is True
        except:
            return False

    def get_auth_cookies(self):
        # 1. 尝试从本地文件加载
        saved_params = self._load_from_file()
        if saved_params:
            print("正在检测本地缓存的 Cookie 是否有效...")
            if self._check_validity(saved_params):
                print("本地 Cookie 有效，直接使用。")
                return saved_params
            else:
                print("本地 Cookie 已过期或无效。")

        # 2. 如果无效，启动 Playwright 登录
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=False, channel="msedge")
            except Exception as e:
                print(f"启动 Edge 失败，尝试默认 Chromium: {e}")
                browser = p.chromium.launch(headless=False)

            context = browser.new_context()
            page = context.new_page()

            print("正在打开浏览器，请完成登录...")
            page.goto(self.login_url)

            max_wait = 300
            start_time = time.time()
            auth_found = False

            while time.time() - start_time < max_wait:
                if not browser.is_connected():
                    break

                # --- 核心改进点：1. 确认 URL 已经回到目标域名 ---
                current_url = page.url
                if "xjtudj.edu.cn" in current_url:
                    time.sleep(2)
                    all_cookies = context.cookies()
                    # --- 核心改进：只提取目标域名的 Cookie ---
                    target_cookies = [c for c in all_cookies if "xjtudj.edu.cn" in c["domain"]]
                    cookie_dict = {c["name"]: c["value"] for c in target_cookies}

                    required = ["SESSION", "dj_token", "dj_key", "dj_usrId"]
                    if all(k in cookie_dict for k in required):
                        print("检测到登录成功，正在提取参数...")
                        self.auth_params = {
                            "SESSION": cookie_dict["SESSION"],
                            "dj_token": cookie_dict["dj_token"],
                            "dj_key": cookie_dict["dj_key"],
                            "dj_usrId": cookie_dict["dj_usrId"],
                            "dj_usrName": cookie_dict.get("dj_usrName", ""),
                        }
                        auth_found = True
                        break
                time.sleep(2)

            if not auth_found:
                raise Exception("登录超时或未检测到关键 Cookie")

            # 3. 登录成功后保存到本地
            self._save_to_file(self.auth_params)
            browser.close()
            return self.auth_params


class XJTU_Helper:
    def __init__(self, auth_params):
        # 基础配置：从你的 curl 提取
        self.base_url = "http://xjtudj.edu.cn/partyconstruction/client"
        self.auth = auth_params

        # 将 Playwright 获取的参数转为 requests 格式
        self.cookies = {
            "SESSION": self.auth["SESSION"],
            "dj_usrId": self.auth["dj_usrId"],
            "dj_token": self.auth["dj_token"],
            "dj_key": self.auth["dj_key"],
            "login_type": "caslogin",
        }

    def generate_encode_token(self, dj_token, dj_key, timestamp):
        """
        根据 JS 逻辑实现 encodeToken 计算
        :param dj_token: 从 Cookie 中获取的 dj_token
        :param dj_key: 从 Cookie 中获取的 dj_key
        :param timestamp: ,,,
        :return: encodeToken
        """
        raw_str = str(timestamp) + dj_token + dj_key
        md5_hash = hashlib.md5(raw_str.encode("utf-8")).hexdigest()

        return md5_hash

    def get_timestamp(self):
        # 系统使用的是毫秒级时间戳
        return int(time.time() * 1000)

    def post_request(self, endpoint, data):
        url = f"{self.base_url}{endpoint}"
        ts = self.get_timestamp()

        # 补充通用字段
        payload = {
            "userId": self.cookies["dj_usrId"],
            "time": ts,
            "encodeToken": self.generate_encode_token(self.cookies["dj_token"], self.cookies["dj_key"], ts),
            "requestType": "",
        }  # 自动生成 Token
        payload.update(data)

        try:
            response = requests.post(url, headers=HEADERS, cookies=self.cookies, json=payload)
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return None

    def shuake(self, course):
        c_title = course["coursewareTitle"]
        c_id = course["courseId"]
        cw_id = course["coursewareId"]

        # 过滤已经完成的课程
        if course["status"] == 2:
            print(f"  [跳过] {c_title} 已完成")
            return

        # 3. 获取课件历史（主要为了拿到总时长 courseAllTime）
        print(f"  [处理] 正在刷课: {c_title}...")
        history = self.post_request("/course/getLearnedHistory", {"courseId": c_id, "coursewareId": cw_id, "progress": 0})

        if history and "data" in history:
            total_time = history["data"]["courseAllTime"]

            # 4. 提交 100% 进度
            # 注意：progress 参数通常是毫秒单位
            result = self.post_request("/course/setLearnedHistory", {"courseId": c_id, "coursewareId": cw_id, "progress": total_time})

            if result and result.get("code") == "200":
                print(f"  [成功] {c_title} 进度已更新为 100%")
            else:
                print(f"  [失败] {c_title} 提交返回: {result}")

        # 适当延迟，防止被识别为攻击
        time.sleep(1)

    def start_sync(self):
        # 1. 获取学习计划列表
        print("正在获取计划列表...")
        schedules = self.post_request("/schedule/selectScheduleList", {"type": "all"})

        # json.dump(schedules, open("selectScheduleList.json", "w"), indent=4, ensure_ascii=False)

        if not schedules or "data" not in schedules:
            print("获取计划失败，请检查 Cookie。")
            return

        for item in schedules["data"]["list"]:
            # 过滤过期的课程
            if item["isOutTime"] == 1:
                continue
                ...

            schedule_name = item["scheduleName"]
            schedule_id = item["scheduleId"]
            print(f"\n检查培训项目: {schedule_name} (ID: {schedule_id})")

            # # 过滤已经完成的课程
            if item["status"] == 2:
                print("该项目已 100% 完成，跳过。")
                continue

            # 2. 获取该计划下的课程详情
            details = self.post_request("/schedule/getDetail", {"scheduleId": schedule_id})

            # json.dump(details, open(f"{schedule_name}_getDetail.json", "w"), indent=4, ensure_ascii=False)

            if not details or "data" not in details:
                continue

            # 必修课
            for module in details["data"].get("moudleList", []):
                for course in module.get("mustCourseList", []):
                    self.shuake(course)
            # 选修课
            if details["data"].get("electiveCourseList", []):
                for course in details["data"].get("electiveCourseList"):
                    self.shuake(course)


if __name__ == "__main__":
    # 第一步：Playwright 引导登录
    login_helper = XJTULoginHelper()
    auth_data = login_helper.get_auth_cookies()

    helper = XJTU_Helper(auth_data)
    helper.start_sync()
