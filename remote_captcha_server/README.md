# 闲鱼远程过滑块服务 - Windows 端

## 原理

阿里 baxia 风控能区分 CDP 注入的鼠标事件与真实硬件鼠标事件：
- **Playwright(CDP)** 即使回放真人轨迹也被判 code=300（拒）
- **pyautogui** 驱动物理光标回放同一轨迹则 code=0（通过）

本服务在 Windows 上运行，使用 **pyautogui 驱动物理鼠标**在**真实 Chrome** 上完成验证。

## 安装

### 1. 安装 Python 3.11+

从 https://www.python.org/downloads/ 下载安装

### 2. 安装依赖

```bash
pip install fastapi uvicorn pyautogui requests
```

### 3. 安装 Chrome 浏览器

从 https://www.google.com/chrome/ 下载安装

## 使用

### 启动服务

```bash
# 默认端口 9090，默认密钥 xianyu_remote_2026
python captcha_server.py

# 自定义端口和密钥
python captcha_server.py --port 9090 --secret my_secret_key
```

### 配置 Docker 端

在 xianyu-auto-reply 系统设置中：
1. 启用"远程过滑块"
2. 填写服务 URL: `http://你的Windows电脑IP:9090/solve`
3. 填写密钥（与启动参数一致）

### 防火墙

确保 Windows 防火墙允许 9090 端口的入站连接：

```powershell
netsh advfirewall firewall add rule name="Xianyu Captcha" dir=in action=allow protocol=tcp localport=9090
```

### 测试连通性

在 Docker 服务器上：
```bash
curl http://你的Windows电脑IP:9090/health
```

应返回：
```json
{"status":"ok","service":"xianyu-remote-captcha","version":"1.0.0","lock_available":true}
```

## 注意事项

1. **Windows 电脑必须开机且有屏幕**（pyautogui 需要图形桌面）
2. **运行期间鼠标约 2-3 秒不可操作**（物理鼠标被接管）
3. **同一时刻只能解一个滑块**（全局锁，因为物理鼠标只有一个）
4. 建议用**虚拟显示器**避免影响正常使用（可选）

## 虚拟显示器方案（可选）

如果不想影响正常使用鼠标，可以安装虚拟显示器：

1. 安装 IddSampleDriver: https://github.com/roshkins/IddSampleDriver
2. 添加虚拟显示器
3. 在虚拟显示器上运行 Chrome

这样鼠标操作在虚拟屏幕上进行，不影响主屏幕。

## 文件说明

| 文件 | 说明 |
|------|------|
| captcha_server.py | FastAPI 服务端，接收 HTTP 请求 |
| captcha_solver.py | 核心解题器，pyautogui + Chrome |
| start.bat | 一键启动脚本 |
| requirements.txt | Python 依赖 |
