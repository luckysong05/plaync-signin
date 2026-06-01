# 构建 PlayNC 可执行程序

打包为独立应用 —— 目标机器无需安装 Python。

## 环境要求

- **Mac**：Apple Silicon（M1/M2/M3）或 Intel。建议 macOS 12+。
- **Windows**：Windows 10/11，64 位。
- 约 2GB 可用磁盘空间（包含 Chromium 浏览器）。
- 需在每个目标平台分别构建（不支持交叉编译）。

---

## Mac 构建

### 1. 前置准备

```bash
# 在 automation_app/ 目录下打开终端
cd automation_app

# 创建虚拟环境（仅首次）
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright Chromium 浏览器
playwright install chromium
```

### 2. 构建

```bash
python build.py --clean
```

输出：`dist/PlayNC/`

### 3. 分发

```bash
cd dist
zip -r PlayNC-mac.zip PlayNC
```

将 `PlayNC-mac.zip` 发送给用户。

### 4. 运行（最终用户）

- 解压
- 右键 `run.sh` → 打开 → 对话框中选择"打开"（首次会触发 Gatekeeper 警告）
- 或在终端中执行：`./run.sh`

---

## Windows 构建

### 1. 安装 Python

从 [python.org](https://www.python.org/downloads/) 下载 Python 3.14。
**安装时务必勾选"Add Python to PATH"。**

### 2. 前置准备

```cmd
:: 在 automation_app\ 目录下打开命令提示符
cd automation_app

:: 创建虚拟环境（仅首次）
python -m venv .venv

:: 激活虚拟环境
.venv\Scripts\activate

:: 安装依赖
pip install -r requirements.txt

:: 安装 Playwright Chromium 浏览器
playwright install chromium
```

### 3. 构建

```cmd
python build.py --clean
```

输出：`dist\PlayNC\`

### 4. 分发

```cmd
:: 右键 dist\PlayNC 文件夹 → 发送到 → 压缩(zipped)文件夹
```

将 `PlayNC.zip` 发送给用户。

### 5. 运行（最终用户）

- 解压
- 双击 `run.bat`
- 无警告，无需额外操作

---

## 构建脚本选项

```bash
python build.py           # 正常构建（onedir 模式，启动最快）
python build.py --clean   # 清理之前构建产物再重新构建
python build.py --onefile # 单文件模式（启动较慢，文件更大）
```

默认模式（`--onedir`）生成一个包含 exe 及支持文件的文件夹。`--onefile` 生成单个 .exe/.app 文件，但首次启动时解压时间更长。

## 注意事项

- Playwright Chromium 浏览器（约 530MB）会自动打包到 `playwright-browsers/` 中。
- Mac 上首次启动会弹出 Gatekeeper 警告，因为应用未签名。右键 → 打开可绕过。
- Windows 上 Windows Defender 首次运行可能会短暂扫描可执行文件（属正常现象）。
- `data/` 文件夹（Excel 文件）**不会**被打包。用户需自行提供 `游戏验证.xlsx` 或在应用中浏览选择。
