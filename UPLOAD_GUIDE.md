# GitHub 上传指南

## 步骤 1: 初始化 Git 仓库

在项目根目录打开命令行，执行：

```bash
git init
```

## 步骤 2: 添加所有文件

```bash
git add .
```

## 步骤 3: 提交更改

```bash
git commit -m "Initial commit: Suci串口助手"
```

## 步骤 4: 在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 输入仓库名称，例如：`serial-port-assistant`
3. 选择 Public（公开）或 Private（私有）
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 "Create repository"

## 步骤 5: 关联远程仓库

将下面命令中的 `你的用户名` 和 `仓库名` 替换成实际的：

```bash
git remote add origin https://github.com/你的用户名/仓库名.git
```

例如：
```bash
git remote add origin https://github.com/suci/serial-port-assistant.git
```

## 步骤 6: 推送到 GitHub

```bash
git branch -M main
git push -u origin main
```

## 可选：添加截图

1. 运行程序并截图
2. 将截图保存为 `screenshot.png` 放在项目根目录
3. 提交并推送：

```bash
git add screenshot.png
git commit -m "Add screenshot"
git push
```

## 注意事项

### ⚠️ 字体文件版权问题

`src/resource/fzzyjt.ttf` 字体文件可能有版权限制。建议：

**方案 1：不上传字体文件**

编辑 `.gitignore` 添加：
```
src/resource/fzzyjt.ttf
```

然后在 README 中说明用户需要自行下载字体文件。

**方案 2：使用开源字体**

替换为开源字体，如思源黑体（Source Han Sans）。

### ✅ 已自动忽略的文件

`.gitignore` 已配置忽略：
- `.venv/` - 虚拟环境
- `__pycache__/` - Python 缓存
- `.idea/` - PyCharm 配置
- `*.pyc` - 编译文件

## 后续更新

当你修改代码后，使用以下命令更新：

```bash
git add .
git commit -m "描述你的更改"
git push
```

## 常见问题

### Q: 推送时要求输入用户名密码？

A: GitHub 已不支持密码认证，需要使用 Personal Access Token：
1. 访问 https://github.com/settings/tokens
2. 生成新的 token
3. 使用 token 代替密码

### Q: 如何克隆到其他电脑？

A: 使用以下命令：
```bash
git clone https://github.com/你的用户名/仓库名.git
cd 仓库名
pip install -r requirements.txt
python main.py
```

---

🎉 完成后，你的项目就可以在 GitHub 上访问了！
