#define MyAppName "Suci串口助手"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "Suci"
#define MyAppExeName "Suci串口助手.exe"
#ifndef MyAppDir
  #define MyAppDir "dist\Suci串口助手"
#endif

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=Suci串口助手_安装包_v{#MyAppVersion}
SetupIconFile=src\resource\Assistant.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=dynamic
WizardSizePercent=100
WizardImageFile=build_assets\installer\wizard-light.png
WizardImageFileDynamicDark=build_assets\installer\wizard-dark.png
WizardSmallImageFile=build_assets\installer\wizard-small-light.png
WizardSmallImageFileDynamicDark=build_assets\installer\wizard-small-dark.png
DisableWelcomePage=no
DisableProgramGroupPage=yes
ShowTasksTreeLines=no
SetupLogging=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[LangOptions]
LanguageName=简体中文
LanguageID=$0804
LanguageCodePage=936
DialogFontName=Microsoft YaHei UI
DialogFontSize=9
WelcomeFontName=Microsoft YaHei UI
WelcomeFontSize=14

[Messages]
SetupAppTitle=安装程序
SetupWindowTitle=安装 {#MyAppName}
UninstallAppTitle=卸载程序
UninstallAppFullTitle=卸载 {#MyAppName}
InformationTitle=提示
ConfirmTitle=确认
ErrorTitle=错误
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=安装(&I)
ButtonOK=确定
ButtonCancel=取消
ButtonFinish=完成(&F)
ButtonBrowse=浏览(&B)...
ButtonWizardBrowse=浏览(&R)...
ButtonNewFolder=新建文件夹(&M)
ClickNext=点击“下一步”继续，或点击“取消”退出。
BrowseDialogTitle=选择文件夹
BrowseDialogLabel=请选择一个文件夹，然后点击“确定”。
NewFolderName=新建文件夹
WelcomeLabel1=安装 {#MyAppName}
WelcomeLabel2=连接串口与蓝牙设备，清晰观察每一次数据收发。%n%n安装向导将引导你完成设置。
WizardSelectDir=选择安装位置
SelectDirDesc=选择 {#MyAppName} 的安装文件夹。
SelectDirLabel3=程序文件将安装到以下位置：
SelectDirBrowseLabel=点击“下一步”继续，或点击“浏览”选择其他文件夹。
DiskSpaceGBLabel=至少需要 [gb] GB 可用磁盘空间。
DiskSpaceMBLabel=至少需要 [mb] MB 可用磁盘空间。
DirExistsTitle=文件夹已经存在
DirExists=文件夹：%n%n%1%n%n已经存在。是否继续安装到此文件夹？
DirDoesntExistTitle=文件夹不存在
DirDoesntExist=文件夹：%n%n%1%n%n不存在。是否创建该文件夹？
WizardSelectTasks=选择快捷方式
SelectTasksDesc=选择安装完成后需要创建的快捷方式。
SelectTasksLabel2=请选择附加选项，然后点击“下一步”。
WizardReady=准备安装
ReadyLabel1=设置已经完成，可以开始安装 {#MyAppName}。
ReadyLabel2a=点击“安装”开始；如需修改设置，请返回上一步。
ReadyMemoDir=安装位置：
ReadyMemoTasks=快捷方式：
WizardPreparing=正在准备
PreparingDesc=正在准备安装 {#MyAppName}。
WizardInstalling=正在安装
InstallingLabel=正在安装 {#MyAppName}，请稍候。
StatusCreateDirs=正在创建文件夹...
StatusExtractFiles=正在复制程序文件...
StatusCreateIcons=正在创建快捷方式...
StatusSavingUninstall=正在保存卸载信息...
StatusRunProgram=正在完成安装...
FinishedHeadingLabel=安装完成
FinishedLabel={#MyAppName} 已准备就绪。
ClickFinish=点击“完成”关闭安装向导。
ExitSetupTitle=退出安装
ExitSetupMessage=安装尚未完成。现在退出将不会安装程序。%n%n确定退出吗？
ConfirmUninstall=确定要移除 {#MyAppName} 及其所有组件吗？
UninstallStatusLabel=正在移除 {#MyAppName}，请稍候。
UninstalledAll={#MyAppName} 已成功移除。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式"; Flags: unchecked

[Files]
Source: "{#MyAppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
