# 打包成 EXE 指南

## 方法一：使用自动打包脚本（推荐）

### 步骤 1: 确保已安装 PyInstaller

```bash
pip install pyinstaller
```

### 步骤 2: 双击运行打包脚本

直接双击 `build.bat` 文件，脚本会自动完成打包。

打包完成后，可执行文件位于 `dist/Suci串口助手.exe`

---

## 方法二：手动打包

### 基础打包（单文件）

```bash
pyinstaller --onefile --windowed --name "Suci串口助手" ^
    --icon=src/resource/Assistant.png ^
    --add-data "src/resource/Assistant.png;src/resource" ^
    --add-data "src/resource/triangle.png;src/resource" ^
    --add-data "src/resource/fzzyjt.ttf;src/resource" ^
    main.py
```

### 使用配置文件打包（推荐）

```bash
pyinstaller build.spec --clean
```

---

## 打包参数说明

- `--onefile` - 打包成单个 exe 文件
- `--windowed` / `-w` - 不显示控制台窗口
- `--name` - 指定生成的 exe 文件名
- `--icon` - 设置应用图标
- `--add-data` - 添加资源文件（格式：源路径;目标路径）
- `--clean` - 清理临时文件

---

## 打包后的文件结构

```
dist/
└── Suci串口助手.exe    # 可执行文件（约 50-80 MB）
```

---

## 常见问题

### Q1: 打包后运行报错找不到资源文件？

**解决方案：** 检查 `build.spec` 中的 `datas` 配置是否正确。

### Q2: 打包后的 exe 文件太大？

**原因：** PyInstaller 会打包所有依赖库。

**优化方案：**
1. 使用虚拟环境，只安装必要的包
2. 使用 UPX 压缩（已在 build.spec 中启用）

### Q3: 杀毒软件报毒？

**原因：** PyInstaller 打包的程序可能被误报。

**解决方案：**
1. 添加到杀毒软件白名单
2. 使用代码签名证书签名程序

### Q4: 打包后程序启动慢？

**原因：** 单文件模式需要解压到临时目录。

**解决方案：** 使用文件夹模式打包（去掉 `--onefile` 参数）

---

## 高级配置

### 打包成文件夹模式（启动更快）

修改 `build.spec`，将 `EXE` 部分改为：

```python
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Suci串口助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='src/resource/Assistant.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Suci串口助手',
)
```

### 添加版本信息

创建 `version.txt`：

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u'Suci'),
        StringStruct(u'FileDescription', u'串口调试助手'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'SerialAssistant'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2026 Suci'),
        StringStruct(u'OriginalFilename', u'Suci串口助手.exe'),
        StringStruct(u'ProductName', u'Suci串口助手'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
```

然后在打包命令中添加：
```bash
--version-file=version.txt
```

---

## 分发建议

### 创建安装包

可以使用 Inno Setup 或 NSIS 创建安装程序：

1. 下载 Inno Setup: https://jrsoftware.org/isinfo.php
2. 创建安装脚本
3. 生成安装程序

### 绿色版分发

直接将 `dist` 文件夹打包成 zip：

```bash
# 重命名文件夹
ren dist "Suci串口助手_v1.0"

# 压缩（需要 7-Zip 或 WinRAR）
7z a -tzip "Suci串口助手_v1.0.zip" "Suci串口助手_v1.0"
```

---

## 测试清单

打包完成后，请测试以下功能：

- [ ] 程序能正常启动
- [ ] 界面显示正常（字体、图标）
- [ ] 能检测到串口设备
- [ ] 能正常连接和断开串口
- [ ] 能正常发送和接收数据
- [ ] 弹窗显示正常
- [ ] 窗口控制按钮工作正常

---

## 更新 requirements.txt

别忘了添加 PyInstaller：

```bash
pip freeze > requirements.txt
```

或手动添加到 `requirements.txt`：
```
pyinstaller>=6.0.0
```

---

🎉 完成后，你就有了一个可以分发的 exe 文件！
