# Suci 串口/蓝牙助手

一个基于 PyQt6 的现代化串口/蓝牙调试工具，采用 macOS 风格设计。

![应用截图](screenshot.png)

## 特性

- macOS 风格界面，支持日间/黑夜模式
- 串口通信，支持多种波特率、数据位、停止位、校验位配置
- 蓝牙通信，支持 BLE 设备扫描与连接
- 多种数据格式：HEX、ASCII、UTF-8
- 消息气泡界面，支持一键复制、导出 Excel
- 快捷命令面板，常用指令一键发送
- 实时数据统计

## 下载安装

前往 [Releases](../../releases) 页面下载最新安装包。

## 从源码运行

**环境要求：** Python 3.8+

```bash
pip install -r requirements.txt
python main.py
```

## 打包安装包

1. 安装 [Inno Setup](https://jrsoftware.org/isdl.php)
2. 运行 `build_installer.bat`
3. 安装包生成在 `installer_output\` 目录

## 项目结构

```
.
├── main.py                  # 程序入口
├── requirements.txt         # 依赖列表
├── build_installer.bat      # 一键打包脚本
├── installer.iss            # Inno Setup 安装包配置
├── quick_commands.json      # 快捷命令配置
└── src/
    ├── core/
    │   ├── app_config.py
    │   ├── serial_manager.py
    │   └── bluetooth_manager.py
    ├── ui/
    │   └── macos_ui.py
    └── resource/
```

## 蓝牙说明

程序使用 Bleak 库，支持 BLE 设备，默认使用 Nordic UART Service (NUS) UUID：
- Service: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- RX: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`
- TX: `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`

如需适配其他设备，修改 `src/core/bluetooth_manager.py` 中的 UUID 定义。

## 依赖

- PyQt6 — GUI 框架
- pyserial — 串口通信
- qasync — 异步事件循环
- bleak — BLE 蓝牙通信
- openpyxl — Excel 导出

## 许可证

MIT License
