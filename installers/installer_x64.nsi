; 军队乡村振兴管理系统 — Windows x64 安装脚本 (NSIS)
; 自带完整运行时：Python + VC++ Redist + 后端 + 前端 + 数据库

!include "MUI2.nsh"
!include "FileFunc.nsh"
!insertmacro GetParameters
!insertmacro GetOptions

; ── 基本信息 ──
!define PRODUCT_NAME "军队乡村振兴管理系统"
!define PRODUCT_NAME_EN "MilitaryRuralRevitalization"
!define PRODUCT_VERSION "1.2.0"
!define PRODUCT_PUBLISHER "Military Rural Revitalization"
!define PRODUCT_WEB_SITE "http://localhost:8000"
!define PRODUCT_DIR_REGKEY "Software\${PRODUCT_NAME_EN}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME_EN}"

; ── 安装目录 ──
!define INSTALL_DIR "$PROGRAMFILES64\${PRODUCT_NAME}"

; ── 编译选项 ──
SetCompressor /SOLID lzma
SetCompressorDictSize 64
RequestExecutionLevel admin
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\dist\windows\${PRODUCT_NAME}-${PRODUCT_VERSION}-x64-Setup.exe"
InstallDir "${INSTALL_DIR}"
BrandingText "${PRODUCT_NAME}"

; ── 界面设置 ──
!define MUI_ABORTWARNING
!define MUI_ICON "..\resources\icons\app.ico"
!define MUI_UNICON "..\resources\icons\app.ico"
!define MUI_WELCOMEPAGE_TITLE "${PRODUCT_NAME} 安装向导"
!define MUI_WELCOMEPAGE_TEXT "本向导将引导您完成 ${PRODUCT_NAME} ${PRODUCT_VERSION} 的安装。$\r$\n$\r$\n系统自带全部运行时环境，无需单独安装 Python、Node.js 或其他依赖。$\r$\n$\r$\n请关闭所有其他应用程序后继续。"
!define MUI_FINISHPAGE_TITLE "安装完成"
!define MUI_FINISHPAGE_TEXT "${PRODUCT_NAME} 已成功安装。$\r$\n$\r$\n勾选下方选项以立即启动系统。"
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_NAME_EN}.exe"
!define MUI_FINISHPAGE_RUN_TEXT "立即启动 ${PRODUCT_NAME}"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_TEXT "创建桌面快捷方式"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortcut
!define MUI_UNWELCOMEFINISHPAGE_BITMAP ""
!define MUI_UNFINISHPAGE_NOAUTOCLOSE

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "SimpChinese"

; ── 安装 Section ──
Section "Install"
  SetOutPath "$INSTDIR"

  ; 1. 安装 VC++ Redistributable（静默）
  DetailPrint "正在安装 VC++ 运行时..."
  IfFileExists "$INSTDIR\resources\vcredist\vc_redist.x64.exe" 0 SkipVC
  nsExec::ExecToLog '"$INSTDIR\resources\vcredist\vc_redist.x64.exe" /install /quiet /norestart'
  SkipVC:

  ; 2. 复制后端可执行文件
  DetailPrint "正在安装后端服务..."
  File /r "..\backend\dist\military-rural-backend\*"
  File "..\backend\dist\military-rural-backend.exe"

  ; 3. 复制前端静态资源
  DetailPrint "正在安装前端界面..."
  SetOutPath "$INSTDIR\resources\frontend"
  File /r "..\resources\frontend\*"

  ; 4. 复制启动脚本和配置
  SetOutPath "$INSTDIR"
  File "..\launch.py"
  File "..\.env.example"
  File "..\build-scripts\build-config.json"

  ; 5. 创建必要的数据目录
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\uploads"
  CreateDirectory "$INSTDIR\exports"
  CreateDirectory "$INSTDIR\backups"

  ; 6. 写入注册表
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_NAME_EN}.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoRepair" 1

  ; 7. 创建卸载程序
  WriteUninstaller "$INSTDIR\uninst.exe"

  ; 8. 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_NAME_EN}.exe"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk" "$INSTDIR\uninst.exe"

  ; 9. 创建桌面快捷方式（可选）
  ; 通过 MUI_FINISHPAGE_SHOWREADME_FUNCTION 在完成页处理

SectionEnd

; ── 桌面快捷方式 ──
Function CreateDesktopShortcut
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_NAME_EN}.exe"
FunctionEnd

; ── 卸载 Section ──
Section "Uninstall"
  ; 询问是否保留数据
  MessageBox MB_YESNO|MB_ICONQUESTION "是否保留数据库和上传文件？$\r$\n$\r$\n选择"是"保留数据（后续重新安装可继续使用）$\r$\n选择"否"彻底删除所有数据" IDYES KeepData

  ; 删除所有文件
  RMDir /r "$INSTDIR\resources"
  RMDir /r "$INSTDIR\logs"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\*.pyd"
  Delete "$INSTDIR\*.py"
  Delete "$INSTDIR\*.json"
  Delete "$INSTDIR\*.bat"
  RMDir /r "$INSTDIR"

  KeepData:
  ; 保留 data/ uploads/ exports/ backups/ 目录
  RMDir /r "$INSTDIR\resources"
  RMDir /r "$INSTDIR\logs"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\*.pyd"
  Delete "$INSTDIR\*.py"
  Delete "$INSTDIR\*.json"
  Delete "$INSTDIR\*.bat"

  ; 删除快捷方式和注册表
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
SectionEnd
