# PyFlow

一套键盘鼠标控制多台电脑的局域网共享工具，灵感来源于 Deskflow/Synergy/Barrier。

## 项目简介

PyFlow 是一个基于 Python 开发的跨终端键盘鼠标控制工具，实现了一套键鼠操控多台电脑。核心体验类似物理多屏：将鼠标移动到屏幕边缘，控制权无缝切换到另一台电脑，再移回又切回原电脑，全程仅一台电脑接收输入。

### 核心特性

- **鼠标无缝切换**：鼠标穿过屏幕边缘自动切换到被控端，移回对向边缘自动返回
- **键盘远程控制**：远程模式下键盘事件仅发送到被控端，本地不响应
- **剪贴板双向同步**：主控端↔被控端剪贴板内容实时互通，内置防回环机制
- **异分辨率映射**：自动按比例映射不同分辨率的屏幕坐标
- **边缘防抖**：切换后 500ms 冷却时间防弹跳，EDGE_OFFSET=15px 内偏防对向边缘误触发
- **Windows 低级钩子**：远程模式下使用 WH_MOUSE_LL 拦截所有鼠标事件，光标不干扰本地

## 架构概览

```
┌─────────────────────────────┐          ┌─────────────────────────────┐
│      主控端 (Server)         │          │      被控端 (Client)         │
│                             │          │                             │
│  ScreenEdge ──→ SwitchController       │  ClipboardMonitor ──→ 发送   │
│       │            │         │   TCP    │       │                     │
│  MouseHook/pynput  │         │ ←─────→ │  EventDispatcher            │
│       │            ▼         │          │       │                     │
│  CoordinateMapper  on_switch │          │  MouseController            │
│       │            │         │          │  KeyboardController          │
│  KeyboardListener  │         │          │  ClipboardSync ←─── 接收     │
│       │            ▼         │          │                             │
│  ClipboardMonitor ──→ 发送    │          │                             │
│                             │          │                             │
└─────────────────────────────┘          └─────────────────────────────┘
```

## 目录结构

```
pyflow/
├── main.py                     # 程序入口
├── config.py                   # 命令行参数解析与配置加载
├── requirements.txt            # 依赖包
├── build.spec                  # PyInstaller 打包配置
├── config_layout.json           # 屏幕布局配置示例
├── config.ini.example           # 通用配置示例
│
├── server/                     # 主控端模块
│   ├── share_server.py         # 主控端核心（切换逻辑、钩子集成、剪贴板双向同步）
│   ├── mouse_hook.py           # Windows WH_MOUSE_LL 低级鼠标钩子
│   ├── mouse_listener.py       # pynput 鼠标监听（本地模式 / 非 Windows 回退）
│   ├── keyboard_listener.py    # pynput 键盘监听（支持 suppress 远程抑制）
│   ├── clipboard_monitor.py    # 剪贴板轮询监控（带防回环机制）
│   ├── screen_edge.py          # 屏幕边缘检测
│   └── screen_layout/          # 屏幕布局与切换
│       ├── __init__.py
│       ├── screen_layout.py    # 屏幕数据类
│       ├── layout_manager.py   # 布局管理器
│       ├── edge_detector.py    # 边界检测器
│       ├── coordinate_mapper.py # 坐标映射（含 EDGE_OFFSET）
│       └── switch_controller.py # 切换状态机
│
├── client/                    # 被控端模块
│   ├── share_client.py         # 被控端核心（事件分发、剪贴板监控）
│   ├── mouse_controller.py     # pynput 鼠标模拟
│   ├── keyboard_controller.py  # pynput 键盘模拟
│   ├── clipboard_sync.py       # 剪贴板写入同步
│   └── reconnect.py            # 自动重连
│
├── common/                    # 通用模块
│   ├── protocol.py            # 二进制协议（打包/解析/粘包处理）
│   ├── event_dispatcher.py     # 事件分发器（支持变长消息）
│   ├── system_utils.py         # 系统工具（光标隐藏/显示、屏幕尺寸）
│   ├── mouse_predictor.py      # 鼠标预测器
│   └── logger.py               # 日志工具
│
├── network/                   # 网络层
│   ├── tcp_server.py           # TCP 服务端
│   └── tcp_client.py           # TCP 客户端
│
└── docs/                      # 文档
    ├── PyFlow用户手册.md
    ├── PyFlow（Python版Deskflow）开发计划及技术架构文档.md
    ├── 屏幕拼接功能设计文档.md
    ├── 鼠标切换优化分析与修改方案.md
    ├── 鼠标切换逻辑重构方案.md
    └── ...
```

## 快速开始

### 安装依赖

```bash
pip install pynput pyautogui pyperclip
```

### 启动被控端

在被控电脑上：

```bash
python main.py --client --ip <主控端IP>
```

### 启动主控端

在你的电脑上：

```bash
python main.py --server --config-layout config_layout.json
```

或使用命令行参数：

```bash
python main.py --server --remote screen1:192.168.1.101:12345 --remote-direction right --remote-width 1920 --remote-height 1080
```

### 配置文件示例

`config_layout.json`:

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
      "name": "主控电脑"
    },
    {
      "screen_id": "remote_right",
      "host": "192.168.1.101",
      "port": 12345,
      "width": 1920,
      "height": 1080,
      "direction": "right",
      "alignment": "top",
      "edge_margin": 10,
      "is_local": false,
      "name": "被控电脑"
    }
  ]
}
```

## 核心机制

### 鼠标切换流程

```
本地控制 → 鼠标到达边缘 → 切换到远程
                              │
                              ├─ 隐藏本地光标
                              ├─ 启用键盘抑制 (suppress)
                              ├─ Windows: 激活 WH_MOUSE_LL 钩子
                              ├─ 发送 SWITCH 命令到被控端
                              └─ 开始追踪虚拟光标

远程控制 → 虚拟光标到达对向边缘 → 返回本地
                              │
                              ├─ 显示本地光标
                              ├─ 关闭键盘抑制
                              ├─ Windows: 停用钩子，重启 pynput 监听
                              └─ 移动光标到返回坐标
```

### 键盘远程抑制

远程模式下，`KeyboardListener` 以 `suppress=True` 重建，阻止所有按键到达本地操作系统，仅转发被控端。返回本地时以 `suppress=False` 重建，恢复正常输入。

### 剪贴板双向同步

```
主控端复制 → ClipboardMonitor 检测变化 → 发送到被控端 → ClipboardSync 写入剪贴板
被控端复制 → ClipboardMonitor 检测变化 → 发送到主控端 → pyperclip.copy() 写入剪贴板

防回环：写入剪贴板后同步更新 _last_content，下次轮询检测到相同内容则跳过发送
        同时比对 _last_remote_clipboard，远处刚发来的内容不再发回
```

### 防抖机制

| 机制 | 说明 |
|------|------|
| EDGE_OFFSET=15px | 切换时光标不放在边缘像素，而是向内偏移 15px |
| 500ms 冷却时间 | 切换后 500ms 内不触发反向边缘检测 |
| 虚拟光标追踪 | 服务端追踪 `_remote_x/_remote_y`，检测到对向边缘时自动返回 |

## 命令行参数

| 参数 | 说明 | 适用模式 |
|------|------|----------|
| `--server` | 以主控端模式启动 | 主控端 |
| `--client` | 以被控端模式启动 | 被控端 |
| `--ip` | 主控端 IP 地址 | 被控端 |
| `--port` | 监听/连接端口 | 通用 |
| `--remote` | 远程屏幕配置 `ID:IP:端口` | 主控端 |
| `--remote-width` | 远程屏幕宽度 | 主控端 |
| `--remote-height` | 远程屏幕高度 | 主控端 |
| `--remote-direction` | 远程屏幕方向 (left/right/top/bottom) | 主控端 |
| `--remote-alignment` | 对齐方式 (left/right/top/bottom/center) | 主控端 |
| `--config-layout` | 布局配置文件路径 | 主控端 |

## 详细文档

- [用户手册](docs/PyFlow用户手册.md) — 安装、配置、使用说明
- [技术架构文档](docs/PyFlow（Python版Deskflow）开发计划及技术架构文档.md) — 架构设计、协议格式
- [屏幕拼接设计文档](docs/屏幕拼接功能设计文档.md) — 坐标映射、边缘检测算法
- [鼠标切换优化分析](docs/鼠标切换优化分析与修改方案.md) — 防抖、钩子方案分析
- [鼠标切换逻辑重构](docs/鼠标切换逻辑重构方案.md) — 状态机重构方案

## 许可证

MIT License