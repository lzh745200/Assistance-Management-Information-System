; 帮扶管理信息系统 — Windows x64 安装脚本 (NSIS)
!include "MUI2.nsh"

!define PRODUCT_NAME "BumofuAssistance"
!define PRODUCT_DISPLAY "帮扶管理信息系统"
!define PRODUCT_VERSION "1.2.0"

SetCompressor /SOLID lzma
RequestExecutionLevel admin
Name "${PRODUCT_DISPLAY} ${PRODUCT_VERSION}"
OutFile "..\dist\windows\${PRODUCT_DISPLAY}-${PRODUCT_VERSION}-x64-Setup.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_DISPLAY}"

!define MUI_ABORTWARNING
!define MUI_ICON "..\resources\icons\app.ico"
!define MUI_UNICON "..\resources\icons\app.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Load SimpChinese for MUI
!insertmacro MUI_LANGUAGE "SimpChinese"

; LangStrings for MUI pages
LangString MUI_TEXT_WELCOME_INFO_TITLE ${LANG_SIMPCHINESE} "${PRODUCT_DISPLAY} 安装向导"
LangString MUI_TEXT_WELCOME_INFO_TEXT ${LANG_SIMPCHINESE} "本向导将引导您完成 ${PRODUCT_DISPLAY} ${PRODUCT_VERSION} 的安装。$\r$\n$\r$\n系统自带全部运行时环境，无需单独安装 Python、Node.js 或其他依赖。"

Section "Install"
  SetOutPath "$INSTDIR"
  DetailPrint "正在安装后端服务..."
  File /r "..\dist\windows\package\military-rural-backend.exe"
  File "..\dist\windows\package\launch.py"
  DetailPrint "正在安装前端界面..."
  SetOutPath "$INSTDIR\resources\frontend"
  File /r "..\resources\frontend\*.*"
  SetOutPath "$INSTDIR"
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\uploads"
  CreateDirectory "$INSTDIR\exports"
  CreateDirectory "$INSTDIR\backups"
  CreateShortCut "$DESKTOP\${PRODUCT_DISPLAY}.lnk" "$INSTDIR\military-rural-backend.exe"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_DISPLAY}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_DISPLAY}\${PRODUCT_DISPLAY}.lnk" "$INSTDIR\military-rural-backend.exe"
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_DISPLAY}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayIcon" "$INSTDIR\military-rural-backend.exe"
SectionEnd

Section "Uninstall"
  MessageBox MB_YESNO|MB_ICONQUESTION "是否保留数据库和上传文件？$\r$\n$\r$\n选择「是」保留数据（重新安装后可继续使用）$\r$\n选择「否」彻底删除所有数据" IDYES KeepData
  RMDir /r "$INSTDIR"
  Goto Done
  KeepData:
  RMDir /r "$INSTDIR\resources"
  RMDir /r "$INSTDIR\logs"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\*.py"
  Done:
  Delete "$DESKTOP\${PRODUCT_DISPLAY}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_DISPLAY}"
  DeleteRegKey HKLM "Software\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
