; 帮扶管理信息系统 - NSIS 安装脚本
; 生成单文件 .exe 安装程序，集成所有运行时环境

!define PRODUCT_NAME "帮扶管理信息系统"
!define PRODUCT_VERSION "1.3.0"
!define PRODUCT_PUBLISHER "帮扶管理信息系统"
!define PRODUCT_WEB_SITE "http://127.0.0.1:8000"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\assistance-system.exe"

SetCompressor /SOLID lzma
SetCompressorDictSize 64

; 现代 UI
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"

; 安装程序属性
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\build\dist\assistance-system-${PRODUCT_VERSION}-setup.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; 界面设置
!define MUI_ABORTWARNING
!define MUI_ICON "..\backend\assistance-management-backend.spec"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; 安装页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\resources\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 卸载页面
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer

  ; 复制后端 exe (x64)
  ${If} ${RunningX64}
    File /r "..\build\pkg-x64\backend\*.exe"
  ${Else}
    File /r "..\build\pkg-x86\backend\*.exe"
  ${EndIf}

  ; 复制前端
  File /r "..\build\pkg-x64\frontend\*.*"

  ; 创建数据目录
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\exports"
  CreateDirectory "$INSTDIR\uploads"

  ; 配置文件
  FileOpen $0 "$INSTDIR\.env" w
  FileWrite $0 "HOST=127.0.0.1$\r$\n"
  FileWrite $0 "PORT=8000$\r$\n"
  FileWrite $0 "DATABASE_URL=sqlite:///./data/database.db$\r$\n"
  FileWrite $0 "PROJECT_VERSION=${PRODUCT_VERSION}$\r$\n"
  FileClose $0

  ; 创建快捷方式
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\start.bat" "" "$INSTDIR\frontend\favicon.ico"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\start.bat" "" "$INSTDIR\frontend\favicon.ico"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\卸载.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  ; 写入注册表
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\start.bat"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoRepair" 1

  ; 写入卸载程序
  WriteUninstaller "$INSTDIR\uninst.exe"
SectionEnd

Section Uninstall
  Delete "$INSTDIR\*.*"
  RMDir /r "$INSTDIR\backend"
  RMDir /r "$INSTDIR\frontend"
  RMDir /r "$INSTDIR\data"
  RMDir /r "$INSTDIR\logs"
  RMDir /r "$INSTDIR\exports"
  RMDir /r "$INSTDIR\uploads"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
