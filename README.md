# BookPreviewer

## 项目简介
BookPreviewer 是一个给PC端作者使用的，用于在使用传统txt记事本写作时预览小说内容的应用程序。
它允许用户在PC端模拟手机界面，预览自己的TXT文件。

## 安装步骤
1. 克隆仓库：
	```bash
	git clone https://github.com/yourusername/BookPreviewer.git
	```
2. 进入项目目录：
	```bash
	cd BookPreviewer
	```
3. build项目：
	```bash
	pyinstaller BookPreviewer.spec
	```

## 使用说明
- 应用界面右侧模拟手机的三个按钮，其中音量加减按钮可以调整字号大小，而开机键可以跳转到下一个警告字符的位置。
- 应用上方的"..."按钮可以打开自己本地的txt文件仓库。
- 写作时可以一直开着应用作为预览窗口，对txt文件的修改只要保存过，就能在鼠标进入应用界面时刷新到预览窗口里。
- "Doc_"开头的文件不会检查警告字符，是用来写背景设定用的。

## 许可证信息
该项目使用 MIT 许可证

