# Bug 分析报告：切换后远程鼠标不动

**日期**: 2026-04-18
**版本**: v19
**问题**: 切换到远程屏幕后，被控端鼠标不动

***

## 问题描述

用户测试日志显示：

**主控端日志：**

```
[ShareServer] 切换状态变为: switching
[ShareServer] 切换到远程屏幕 remote_left，坐标: (0, 540)
[ShareServer] 已发送切换命令到客户端
[ShareServer] 切换状态变为: remote
切换到remote后，远程被控屏幕鼠标就不动了。
```

**被控端日志：**

```
[ShareClient] 已连接到主控端 192.168.1.5:12345
[ShareClient] 收到切换命令：action=0, target=(0, 540)
[ShareClient] 鼠标移动到 (0, 540)
```

切换命令已成功发送到客户端，客户端也执行了鼠标移动到 (0, 540)，但之后鼠标不再响应任何移动。

***

## 问题分析

### 代码流程追踪

**1. 切换触发流程：**

```
服务器边缘检测 → switch_controller.on_edge_hit() → switch_to_remote()
→ 状态变为 SWITCHING → 发送 pack_switch(0) → 状态变为 REMOTE
```

**2. 客户端接收处理：**

```python
# share_client.py _on_switch()
if action == 0:
    self._remote_control_active = True
    self.mouse_controller.move_to(target_x, target_y)  # 移动一次
```

**3. 客户端鼠标事件处理：**

```python
# share_client.py _on_mouse_move()
self._check_edge_for_return(x, y)  # 检查边缘返回
self._start_interpolation()  # 启动插值线程
```

***

## 根本原因

**客户端没有注册 MSG\_TYPE\_MOUSE\_MOVE 消息处理器！**

查看 `share_client.py` 的 `_setup_dispatcher()`：

```python
def _setup_dispatcher(self):
    self.dispatcher.register(MSG_TYPE_MOUSE_BUTTON, self._on_mouse_button)
    self.dispatcher.register(MSG_TYPE_MOUSE_SCROLL, self._on_mouse_scroll)
    self.dispatcher.register(MSG_TYPE_KEYBOARD, self._on_keyboard)
    self.dispatcher.register(MSG_TYPE_CLIPBOARD, self._on_clipboard)
    self.dispatcher.register(MSG_TYPE_SWITCH, self._on_switch)
    # 缺少: self.dispatcher.register(MSG_TYPE_MOUSE_MOVE, self._on_mouse_move)
```

**后果**：

- `EventDispatcher.dispatch()` 收到 MOUSE\_MOVE 消息时，`handler` 为 `None`
- 代码执行 `continue` 跳过处理
- `_on_mouse_move()` 从未被调用
- `_start_interpolation()` 从未被调用
- 插值线程从未启动

***

## 修复方案

在 `share_client.py` 的 `_setup_dispatcher()` 中添加：

```python
self.dispatcher.register(MSG_TYPE_MOUSE_MOVE, self._on_mouse_move)
```

***

## 影响分析

| 组件     | 影响                                      |
| ------ | --------------------------------------- |
| 鼠标移动   | 切换到远程后无法通过鼠标事件移动被控端鼠标                   |
| 边缘返回检测 | `_check_edge_for_return()` 不会被调用，无法返回本地 |
| 插值预测   | 插值线程从未启动                                |

***

## 测试验证

修复后应验证：

1. 切换到远程后，被控端鼠标能跟随主控端鼠标移动
2. 鼠标移动到被控端边缘时，能发送返回命令
3. 返回后主控端鼠标能继续控制本地

***

## 附加发现

1. **插值线程依赖鼠标事件启动**：当前设计是每次收到鼠标事件才启动插值线程，如果主控端鼠标静止，插值线程可能无法及时启动
2. **服务器端鼠标事件阻塞**：服务器在 `is_remote_control()` 返回 True 时会阻止本地鼠标事件发送到客户端，这是正确的设计
3. **客户端边缘检测冷却时间**：`self._edge_cooldown_ms = 500` 可能需要根据实际网络延迟调整

<br />

todo 我需要下次对话告诉 agent

修复 v19 的 bug：切换后远程鼠标不动

