# Suci 串口/蓝牙助手

一个基于 PyQt6 的现代化串口/蓝牙调试工具，采用 macOS 风格设计，支持 Windows。

![应用截图](screenshot.png)

## 特性

- macOS 风格无边框窗口，支持日间/夜间模式切换
- 串口通信，支持波特率、数据位、停止位、校验位自由配置
- 蓝牙 BLE 通信，支持设备扫描与连接
- 多种数据格式：HEX、ASCII、UTF-8
- 消息气泡界面，支持时间戳、一键复制、导出 Excel
- 消息搜索过滤、原始收发会话 CSV 录制、实时收发速率
- 快捷命令面板，支持自定义命令、延迟发送、HEX 模式
- 支持循环发送和可扩展的数据帧解析
- 实时收发字节统计

完整功能规划与分期进度见 [功能全集与实施路线图](docs/FEATURE_ROADMAP.md)，新版工作台的布局与响应式规则见 [Apple 风格工作台重构规范](docs/UI_REDESIGN.md)。

## 下载安装

前往 [Releases](../../releases) 页面下载最新安装包（Windows）。

## 从源码运行

环境要求：Python 3.8+

```bash
pip install -r requirements.txt
python main.py
```

## 打包安装包

1. 安装 [Inno Setup](https://jrsoftware.org/isdl.php)
2. 运行 `build_installer.bat`
3. 安装包生成在 `installer_output\` 目录

打包脚本会自动生成浅色/深色安装向导视觉资源，并在常见安装路径中查找 Inno Setup。发布新版本时只需修改 `build_installer.bat` 顶部的 `APP_VERSION`。

## 项目结构

```
.
├── main.py                  # 兼容启动入口
├── requirements.txt         # 依赖列表
├── quick_commands.json      # 快捷命令配置（运行时生成）
├── build_installer.bat      # 一键打包脚本
├── build.spec               # PyInstaller 配置
├── installer.iss            # Inno Setup 安装包配置
└── src/
    ├── app.py                  # 应用组装与事件循环
    ├── core/
    │   ├── app_config.py        # 应用配置
    │   ├── resources.py         # 统一资源路径
    │   ├── data_framer.py       # 数据帧解析
    │   ├── quick_command_store.py # 快捷命令存储
    │   ├── session_recorder.py  # 会话录制
    │   ├── serial_manager.py    # 串口管理
    │   └── bluetooth_manager.py # 蓝牙管理
    ├── ui/
    │   ├── main_window.py       # 主窗口外壳
    │   ├── macos_ui.py          # 主界面
    │   ├── layout_metrics.py    # 布局尺寸令牌
    │   ├── responsive_layout.py # 纯响应式布局策略
    │   └── workbench/           # 可复用工作台组件
    └── resource/                # 图标、字体等静态资源
```

## 蓝牙说明

使用 Bleak 库，支持 BLE 设备，默认适配 Nordic UART Service (NUS)：

| 类型 | UUID |
|------|------|
| Service | `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` |
| RX (写入) | `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` |
| TX (通知) | `6E400003-B5A3-F393-E0A9-E50E24DCCA9E` |

如需适配其他设备，修改 `src/core/bluetooth_manager.py` 中的 UUID 定义。

## 依赖

| 包 | 用途 |
|----|------|
| PyQt6 | GUI 框架 |
| pyserial | 串口通信 |
| qasync | Qt 异步事件循环 |
| bleak | BLE 蓝牙通信 |
| openpyxl | Excel 导出 |
| pyinstaller | 打包工具 |

## 许可证

MIT License
