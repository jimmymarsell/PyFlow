# PyFlow 用户手册 v1.0

## 目录

1. [软件简介](#1-软件简介)
2. [系统要求](#2-系统要求)
3. [快速开始](#3-快速开始)
4. [基础功能测试](#4-基础功能测试)
5. [屏幕切换功能](#5-屏幕切换功能)
6. [命令行参数](#6-命令行参数)
7. [常见问题](#7-常见问题)

---

## 1. 软件简介

**PyFlow** 是一款基于 Python 开发的键盘鼠标共享工具，可以让用户使用一套键鼠控制多台电脑。

### 主要功能

- **鼠标共享**：在一台电脑上控制另一台电脑的鼠标
- **键盘共享**：键盘事件同步到被控端
- **剪贴板同步**：支持文本复制粘贴同步
- **屏幕切换**：通过移动鼠标到屏幕边界来切换控制不同电脑

### 架构说明

```
┌─────────────────┐          ┌─────────────────┐
│   主控端 (Server) │ ──── TCP ────> │  被控端 (Client) │
│   (你的电脑)      │  <─── 事件 ────  │  (其他电脑)      │
│                  │          │                  │
│  - 监听键鼠事件   │          │  - 执行键鼠操作    │
│  - 边缘检测      │          │  - 接收切换命令    │
│  - 发送控制命令   │          │                  │
└─────────────────┘          └─────────────────┘
```

---

## 2. 系统要求

### 主控端（你的电脑）

- Windows 10/11 或 macOS/Linux
- Python 3.8+
- 网络连接（与被控端在同一局域网）

### 被控端（其他电脑）

- Windows 10/11 或 macOS/Linux
- Python 3.8+
- 网络连接

### 网络要求

- 两台电脑需要在**同一局域网**内
- 防火墙需要开放 TCP 端口 12345（可自定义）

---

## 3. 快速开始

### 3.1 安装依赖

在所有电脑上执行：

```bash
pip install pynput pyautogui pyperclip
```

### 3.2 启动被控端

在被控端电脑上执行：

```bash
python main.py --client --ip <主控端IP地址>
```

例如：

```bash
python main.py --client --ip 192.168.1.100
```

成功后会显示：

```
PyFlow 被控端启动，连接到 192.168.1.100:12345
```

### 3.3 启动主控端

在你的电脑上执行：

```bash
python main.py --server
```

成功后会显示：

```
PyFlow 主控端启动，监听 0.0.0.0:12345
等待被控端连接...
```

### 3.4 确认连接

当被控端连接成功时，主控端会显示：

```
客户端已连接: ('192.168.1.101', 54321)
```

---

## 4. 基础功能测试

### 4.1 测试鼠标移动

1. 在主控端移动鼠标
2. 观察被控端屏幕，鼠标应该跟随移动

### 4.2 测试鼠标点击

1. 在主控端点击鼠标左键
2. 观察被控端是否响应点击事件

### 4.3 测试键盘输入

1. 在主控端按下键盘
2. 观察被控端是否收到键盘事件

### 4.4 测试剪贴板

1. 在主控端复制一段文字（Ctrl+C）
2. 在被控端粘贴（Ctrl+V），应该能看到相同内容

---

## 5. 屏幕切换功能

屏幕切换功能允许你通过移动鼠标到屏幕边界来控制另一台电脑。

### 5.1 概念解释

| 概念         | 说明                                                |
| ------------ | --------------------------------------------------- |
| **拼接方向** | 被控端位于主控端的哪个方向（left/right/top/bottom） |
| **对齐方式** | 屏幕边界的对齐方式（left/right/top/bottom）         |
| **边缘阈值** | 触发切换的边界距离（像素）                          |

### 5.2 配置示例

假设你的电脑在左边，被控电脑在右边：

**主控端分辨率**：2560 x 1600
**被控端分辨率**：1920 x 1080

启动命令：

```bash
python main.py --server --remote remote1:192.168.1.101:12345 --remote-direction right --remote-width 1920 --remote-height 1080
```

参数说明：

- `--remote remote1:192.168.1.101:12345`：远程屏幕配置，格式为 `ID:IP:端口`
- `--remote-direction right`：被控端在主控端的右边
- `--remote-width 1920`：被控端屏幕宽度
- `--remote-height 1080`：被控端屏幕高度

### 5.3 切换流程

1. **正常状态**：你控制主控端电脑

2. **切换到被控端**：
   - 将鼠标向右移动到主控端屏幕的**右边界**
   - 当鼠标接近边界（默认5像素）时，控制权切换到被控端
   - 被控端鼠标会移动到对应位置

3. **在被控端操作**：
   - 你现在可以控制被控端电脑

4. **返回主控端**：
   - 将鼠标移动到被控端屏幕的**左边界**
   - 控制权返回主控端

### 5.4 坐标映射说明

当两台电脑分辨率不同时，PyFlow 会自动按比例映射坐标：

```
主控端 (2560x1600)                    被控端 (1920x1080)
┌─────────────────┐                   ┌─────────────────┐
│                 │ ── 右边界对齐 ──> │                 │
│     鼠标移动     │    比例映射      │    鼠标定位      │
│                 │ <── 返回映射 ──── │                 │
└─────────────────┘                   └─────────────────┘
```

---

## 6. 命令行参数

### 6.1 打包版本 vs 源代码版本

PyFlow 提供两种使用方式：

| 类型           | 文件             | 优势                      | 劣势                 |
| -------------- | ---------------- | ------------------------- | -------------------- |
| **打包版本**   | `PyFlow.exe`     | 无需安装 Python，双击即用 | 需要管理员权限       |
| **源代码版本** | `python main.py` | 修改灵活，便于调试        | 需要配置 Python 环境 |

### 6.2 主控端配置方式

主控端有两种配置屏幕布局的方式：

| 方式 | 说明 | 适用场景 |
|-----|------|---------|
| **命令行参数** | 使用 `--remote-*` 参数 | 快速测试、单屏幕 |
| **配置文件** | 使用 `--config-layout` | 多屏幕、复杂布局 |

**命令行参数方式**（仅支持单个远程屏幕）：

```bash
# 启动主控端（命令行方式）
PyFlow.exe --server --remote screen1:192.168.1.101:12345 --remote-direction right --remote-width 1920 --remote-height 1080
```

**配置文件方式**（支持多个远程屏幕）：

```bash
# 1. 将 config_layout.json 放到 PyFlow.exe 同目录
# 2. 使用 --config-layout 指定配置文件
PyFlow.exe --server --config-layout config_layout.json

# 或使用完整路径
PyFlow.exe --server --config-layout "D:\PyFlow\config_layout.json"
```

### 6.3 打包版本使用方法

#### 准备工作

1. 下载最新版本的 PyFlow 打包文件
2. 将压缩包解压到任意目录
3. 确保防火墙允许 `PyFlow.exe` 访问网络
4. **如需屏幕切换功能**：将 `config_layout.json` 放到 `PyFlow.exe` 同目录

#### 启动主控端（打包版本）

**方式1：使用配置文件（推荐）**
```bash
cd /d <PyFlow所在目录>
PyFlow.exe --server --config-layout config_layout.json
```

**方式2：使用命令行参数**
```bash
cd /d <PyFlow所在目录>
PyFlow.exe --server --remote screen1:192.168.1.101:12345 --remote-direction right --remote-width 1920 --remote-height 1080
```

#### 启动被控端（打包版本）

```bash
cd /d <PyFlow所在目录>
PyFlow.exe --client --ip <主控端IP>
```

### 6.4 源代码版本使用方法

确保已安装 Python 3.8+ 和依赖包：

```bash
pip install pynput pyautogui pyperclip
```

#### 启动主控端

**方式1：使用配置文件（推荐）**
```bash
python main.py --server --config-layout config_layout.json
```

**方式2：使用命令行参数**
```bash
python main.py --server --remote screen1:192.168.1.101:12345 --remote-direction right --remote-width 1920 --remote-height 1080
```

#### 启动被控端

```bash
python main.py --client --ip <主控端IP>
```

### 6.5 参数对照表

| 参数                 | 说明                     | 适用模式 | 示例                                   |
| -------------------- | ------------------------ | ------- | -------------------------------------- |
| `--server`           | 以主控端模式启动         | 主控端   | 必须                                   |
| `--client`           | 以被控端模式启动         | 被控端   | 必须                                   |
| `--ip`               | 主控端IP地址             | 被控端   | `--ip 192.168.1.100`                   |
| `--port`             | 监听/连接端口            | 通用     | `--port 12345`                         |
| `--remote`           | 远程屏幕配置             | 主控端   | `--remote screen1:192.168.1.101:12345` |
| `--remote-width`     | 远程屏幕宽度             | 主控端   | `--remote-width 1920`                  |
| `--remote-height`    | 远程屏幕高度             | 主控端   | `--remote-height 1080`                 |
| `--remote-direction` | 远程屏幕方向             | 主控端   | `--remote-direction right`             |
| `--remote-alignment` | 对齐方式                 | 主控端   | `--remote-alignment left`              |
| `--config-layout`    | 布局配置文件路径         | 主控端   | `--config-layout config_layout.json`   |

### 6.6 完整示例

#### 主控端启动示例

**配置文件方式（推荐）：**
```bash
# 打包版本
PyFlow.exe --server --config-layout config_layout.json

# 源代码版本
python main.py --server --config-layout config_layout.json
```

**命令行参数方式：**
```bash
# 打包版本
PyFlow.exe --server --remote remote_left:192.168.1.101:12345 --remote-direction left --remote-width 1920 --remote-height 1080

# 源代码版本
python main.py --server --remote remote_left:192.168.1.101:12345 --remote-direction left --remote-width 1920 --remote-height 1080
```

#### 被控端启动示例

```bash
# 打包版本
PyFlow.exe --client --ip 192.168.1.100

# 源代码版本
python main.py --client --ip 192.168.1.100
```

---

## 7. 常见问题

### Q1: 连接失败

**症状**：被控端显示"连接主控端失败"

**解决方法**：

1. 检查网络是否连通：`ping <主控端IP>`
2. 检查主控端是否已启动
3. 检查防火墙设置，确保端口 12345 开放

### Q2: 鼠标移动延迟

**症状**：鼠标移动卡顿

**解决方法**：

1. 检查网络延迟：`ping <对方IP>`
2. 尽量使用有线网络而非 WiFi
3. 关闭其他占用网络的程序

### Q3: 鼠标无法切换屏幕

**症状**：鼠标到达边界但没有切换

**解决方法**：

1. 检查是否正确配置了 `--remote` 参数
2. 检查被控端是否已连接
3. 检查 `--remote-direction` 方向是否正确
4. 尝试减小边缘阈值（当前默认是5像素）

### Q4: 需要管理员权限

**症状**：程序提示需要管理员权限

**解决方法**：

- 在 Windows 上，右键点击命令提示符，选择"以管理员身份运行"

### Q5: 找不到 Python 命令

**症状**：`python` 命令未找到

**解决方法**：

1. 尝试使用 `python3` 命令
2. 确保 Python 已正确安装并添加到 PATH

### Q6: 打包版本闪退

**症状**：双击 PyFlow.exe 后窗口一闪而过

**解决方法**：

1. 使用命令提示符（管理员）运行，查看错误信息：
   ```bash
   cd /d <PyFlow目录>
   PyFlow.exe --server
   ```
2. 确保以管理员权限运行
3. 检查是否缺少必要的 DLL 文件

### Q7: 打包版本无法连接

**症状**：打包版本无法连接到主控端/被控端

**解决方法**：

1. 确保防火墙允许 PyFlow.exe 通过
2. 以管理员权限运行程序
3. 检查网络是否在同一局域网

---

### Q7: 打包版本找不到配置文件

**症状**：提示"配置文件不存在"

**解决方法**：

1. 确保 `config_layout.json` 文件放在 PyFlow.exe 同目录下
2. 或者使用完整路径：`--config-layout "D:\PyFlow\config_layout.json"`

### Q8: 屏幕切换不生效

**症状**：鼠标到达边界但没有切换到另一台电脑

**解决方法**：

1. 检查 `--remote-direction` 方向是否正确
2. 确保被控端已成功连接
3. 检查配置文件中的 `direction` 是否正确
4. 尝试使用配置文件方式配置屏幕布局

### Q9: 坐标映射不准确

**症状**：切换后鼠标位置与预期不符

**解决方法**：

1. 调整配置文件中的 `alignment` 对齐方式
2. 使用 `offset_x`、`offset_y` 进行微调
3. 确保主控端分辨率配置正确

---

## 附录：布局配置文件格式

PyFlow 支持使用 JSON 配置文件来定义多屏幕布局。

### A.1 为什么使用配置文件

| 方式 | 优点 | 缺点 |
|-----|------|------|
| **命令行参数** | 简单快速 | 只能配置一个远程屏幕 |
| **配置文件** | 支持多屏幕、灵活配置 | 需要额外文件 |

### A.2 配置文件格式

```json
{
  "screens": [
    {
      "screen_id": "local",
      "host": null,
      "port": 0,
      "width": 2560,
      "height": 1600,
      "direction": "left",
      "alignment": "center",
      "offset_x": 0,
      "offset_y": 0,
      "edge_margin": 10,
      "is_local": true,
      "name": "主控电脑屏幕"
    },
    {
      "screen_id": "remote_left",
      "host": "192.168.1.10",
      "port": 12345,
      "width": 1920,
      "height": 1080,
      "direction": "left",
      "alignment": "center",
      "offset_x": 0,
      "offset_y": 0,
      "edge_margin": 10,
      "is_local": false,
      "name": "被控电脑屏幕-左侧"
    }
  ]
}
```

### A.3 字段说明

| 字段 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| `screen_id` | 字符串 | 屏幕唯一标识 | "local", "remote_left" |
| `host` | 字符串/null | 被控端IP（本地屏幕为null） | "192.168.1.10" |
| `port` | 整数 | 被控端端口（本地屏幕为0） | 12345 |
| `width` | 整数 | 屏幕宽度（像素） | 1920 |
| `height` | 整数 | 屏幕高度（像素） | 1080 |
| `direction` | 字符串 | 被控端位于本地屏幕的哪个方向（仅被控端） | "left", "right", "top", "bottom" |
| `alignment` | 字符串 | 被控端边界与本地屏幕的对齐方式（仅被控端） | "left", "right", "top", "bottom", "center" |
| `offset_x` | 整数 | X轴偏移微调 | 0 |
| `offset_y` | 整数 | Y轴偏移微调 | 0 |
| `edge_margin` | 整数 | 边缘触发阈值（像素） | 10 |
| `is_local` | 布尔 | 是否为本地屏幕 | true, false |
| `name` | 字符串 | 屏幕名称（可选） | "主控电脑屏幕" |

### A.4 方向和对齐说明

**direction（拼接方向）** - 描述被控端位于本地屏幕的哪个方向：

| 方向 | 含义 | 切换触发边界 |
|-----|------|-------------|
| `left` | 被控端在本地屏幕的**左边** | 本地屏幕**左边界** |
| `right` | 被控端在本地屏幕的**右边** | 本地屏幕**右边界** |
| `top` | 被控端在本地屏幕的**上方** | 本地屏幕**上边界** |
| `bottom` | 被控端在本地屏幕的**下方** | 本地屏幕**下边界** |

**alignment（对齐方式）** - 描述被控端边界与本地屏幕的对齐方式（以 direction=left 为例）：

```
                    被控端 (remote)
                    direction=left
                          │
                          ▼
┌─────────────────┐   ┌─────────────────┐
│   本地屏幕        │   │ left对齐 (默认)   │
│   (主控端)       │   │ 远程左边界        │
│                 │   │ ↖               │
│   ◄── 鼠标移出   │   │ 与本地右边界对齐   │
│     右边界       │   │                 │
└─────────────────┘   └─────────────────┘
                          │
                          │
                    alignment=top:
                    被控屏幕上边界
                    与本地屏幕上边界对齐
                    
                    alignment=center:
                    被控屏垂直中心
                    与本地屏垂直中心对齐
                    
                    alignment=bottom:
                    被控屏幕下边界
                    与本地屏幕下边界对齐
```

**对齐方式的有效组合**：

| direction | 可用 alignment | 说明 |
|-----------|---------------|------|
| `left` | `top`, `center`, `bottom` | 被控端在左边，对齐远程屏幕的右边界 |
| `right` | `top`, `center`, `bottom` | 被控端在右边，对齐远程屏幕的左边界 |
| `top` | `left`, `center`, `right` | 被控端在上方，对齐远程屏幕的下边界 |
| `bottom` | `left`, `center`, `right` | 被控端在下方，对齐远程屏幕的上边界 |

### A.5 本地屏幕配置

本地屏幕（`is_local: true`）的配置最为简单，只需要基本信息：

```json
{
  "screen_id": "local",
  "host": null,
  "port": 0,
  "width": 2560,
  "height": 1600,
  "is_local": true,
  "name": "主控电脑屏幕"
}
```

**注意**：本地屏幕不需要 `direction` 和 `alignment` 字段，这些字段只对被控端有意义。

### A.6 使用配置文件启动

#### 打包版本

1. 将 `config_layout.json` 放到 `PyFlow.exe` 同目录
2. 运行命令：
```bash
PyFlow.exe --server --config-layout config_layout.json
```

3. 如果配置文件不在同目录，使用完整路径：
```bash
PyFlow.exe --server --config-layout "D:\PyFlow\config_layout.json"
```

#### 源代码版本

```bash
python main.py --server --config-layout config_layout.json
```

### A.7 典型场景配置示例

#### 场景1：被控端在本地屏幕左边，采用上对齐

```json
{
  "screens": [
    {
      "screen_id": "local",
      "host": null,
      "port": 0,
      "width": 2560,
      "height": 1600,
      "is_local": true,
      "name": "主控电脑屏幕"
    },
    {
      "screen_id": "remote_left",
      "host": "192.168.1.10",
      "port": 12345,
      "width": 1920,
      "height": 1080,
      "direction": "left",
      "alignment": "top",
      "is_local": false,
      "name": "被控电脑屏幕-左侧"
    }
  ]
}
```

#### 场景2：被控端在本地屏幕右边，采用左对齐

```json
{
  "screens": [
    {
      "screen_id": "local",
      "host": null,
      "port": 0,
      "width": 2560,
      "height": 1600,
      "is_local": true,
      "name": "主控电脑屏幕"
    },
    {
      "screen_id": "remote_right",
      "host": "192.168.1.11",
      "port": 12345,
      "width": 1920,
      "height": 1080,
      "direction": "right",
      "alignment": "left",
      "is_local": false,
      "name": "被控电脑屏幕-右侧"
    }
  ]
}
```

#### 场景3：被控端在本地屏幕上方，采用居中对齐

```json
{
  "screens": [
    {
      "screen_id": "local",
      "host": null,
      "port": 0,
      "width": 2560,
      "height": 1600,
      "is_local": true,
      "name": "主控电脑屏幕"
    },
    {
      "screen_id": "remote_top",
      "host": "192.168.1.12",
      "port": 12345,
      "width": 1920,
      "height": 1080,
      "direction": "top",
      "alignment": "center",
      "is_local": false,
      "name": "被控电脑屏幕-上方"
    }
  ]
}
```

---

## 技术支持

如遇到问题，请检查：

1. 开发计划文档：`docs/PyFlow开发计划.md`
2. 开发总结文档：`docs/第X周开发总结.md`
3. 设计文档：`docs/屏幕拼接功能设计文档.md`

---

_最后更新：2026-04-17_
