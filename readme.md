# 西安交通大学党建学习平台自动刷课工具

本脚本用于自动化完成西安交通大学党建学习平台的网络培训课程。它通过 **Playwright** 引导用户进行统一身份认证（CAS）登录，获取并持久化 Cookie，随后利用 **Requests** 直接与后端 API 交互，实现一键秒刷课程进度。

## 🚀 功能特性

- **自动化登录引导**：自动调用本地 Edge 浏览器（或 Chromium）打开登录页面，支持 CAS 扫码或账号密码登录。
- **Cookie 持久化**：登录成功后将关键身份信息（SESSION, token, key等）加密保存至本地 `cookies_cache.json`，下次运行无需重复登录。
- **智能校验**：启动时自动检测本地 Cookie 有效性，过期自动重连。
- **精准刷课**：自动解析“必修课”与“选修课”列表，获取每个课件的精确时长，并将进度更新至 100%。
- **自动过滤**：智能跳过已完成的课程及已过期的培训项目。

## 🛠️ 环境要求

- **Python**: 3.8 或更高版本
- **浏览器**: 推荐安装 Microsoft Edge（脚本优先调用），或使用 Playwright 默认的 Chromium。

## 📦 安装步骤

1. **克隆或下载本仓库**：

   ```bash
   git clone  https://github.com/WANGKANG1717/XJTU-DJshuake
   cd XJTU-DJshuake
   ```

2. **安装 Python 依赖库**：

   ```bash
   pip install requests playwright
   ```

3. **安装浏览器驱动**：
   ```bash
   # 安装 msedge 驱动支持（如果电脑已有 Edge 浏览器）
   playwright install chromium
   ```

## 📖 使用说明

1. **直接运行脚本**：

   ```bash
   python main.py
   ```

2. **完成登录**：
   - 脚本会弹出浏览器窗口，请在窗口中完成学校的统一身份认证登录。
   - 登录成功并跳转回党建系统主页后，脚本会自动检测并提取参数，随后浏览器会自动关闭。

3. **自动化刷课**：
   - 脚本将列出所有未过期的培训项目。
   - 自动遍历每个项目下的所有课件，逐一提交 100% 进度。

## 📂 文件结构

- `main.py`: 主程序代码。
- `cookies_cache.json`: (运行后生成) 存储登录凭证，请勿随意泄露给他人。
- `README.md`: 项目说明文档。

## ⚠️ 免责声明

1. **技术研究专用**：本脚本仅用于 Python 爬虫技术的研究与学习，请勿将其用于任何商业用途或大规模攻击。
2. **账号风险**：使用自动化脚本可能违反平台的使用协议。由使用本脚本产生的任何账号封禁、成绩无效或法律责任，均由使用者本人承担。
3. **适度使用**：建议在完成脚本操作后，手动进入系统核实学分情况。

## 💡 技术细节 (For Developers)

- **Token 计算**：系统后端校验 `encodeToken` 字段。该字段通过 `md5(timestamp + dj_token + dj_key)` 计算得出，脚本已完美还原该 JS 逻辑。
- **Cookie 路径限制**：系统核心 `SESSION` 挂载在 `/partyconstruction` 路径下。脚本通过 Playwright 全局提取并配合 `requests` 携带发送，解决了跨路径访问的问题。

---

_Happy Learning!_ 🎓
