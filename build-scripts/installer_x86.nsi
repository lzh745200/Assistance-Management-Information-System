; 帮扶管理信息系统 - NSIS x86 (32-bit) 安装脚本
; 生成 32-bit 单文件 .exe 安装程序

!define PRODUCT_NAME "帮扶管理信息系统"
!define PRODUCT_VERSION "1.2.0"
!define PRODUCT_PUBLISHER "帮扶管理信息系统"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\assistance-system-x86.exe"

SetCompressor /SOLID lzma
SetCompressorDictSize 64

!include "MUI2.nsh"
!include "FileFunc.nsh"

; 安装程序属性
Name "${PRODUCT_NAME} ${PRODUCT_VERSION} (32-bit)"
OutFile "..\dist\windows\x86\帮扶管理信息系统_${PRODUCT_VERSION}_win_x86.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; 界面设置
!define MUI_ABORTWARNING
!define MUI_ICON "..\resources\icons\app.ico"
!define MUI_UNICON "..\resources\icons\app.ico"

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

  ; 复制后端 x86 exe
  SetOutPath "$INSTDIR\backend"
  File "..\dist\windows\x86\backend\assistance-management-backend.exe"

  ; 复制前端文件
  SetOutPath "$INSTDIR\frontend"
  File /r "..\resources\frontend\*.*"

  ; 复制 VC++ Redistributable (x86)
  SetOutPath "$INSTDIR\redist"
  File /nonfatal "..\resources\vcredist\vc_redist.x86.exe"

  ; 创建数据目录
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\exports"
  CreateDirectory "$INSTDIR\uploads"

  ; 生成 .env 配置文件
  FileOpen $0 "$INSTDIR\.env" w
  FileWrite $0 "HOST=127.0.0.1$\r$\n"
  FileWrite $0 "PORT=8000$\r$\n"
  FileWrite $0 "DATABASE_URL=sqlite:///./data/rural_revitalization.db$\r$\n"
  FileWrite $0 "PROJECT_VERSION=${PRODUCT_VERSION}$\r$\n"
  FileWrite $0 "LOG_LEVEL=INFO$\r$\n"
  FileClose $0

  ; 创建启动脚本 start.bat
  FileOpen $0 "$INSTDIR\start.bat" w
  FileWrite $0 "@echo off$\r$\n"
  FileWrite $0 "chcp 65001 >nul 2>&1$\r$\n"
  FileWrite $0 "title 帮扶管理信息系统 v${PRODUCT_VERSION}$\r$\n"
  FileWrite $0 "cd /d $\"$INSTDIR$\"$\r$\n"
  FileWrite $0 "echo 正在启动 帮扶管理信息系统 (32-bit)...$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "echo 后端服务: http://127.0.0.1:8000$\r$\n"
  FileWrite $0 "echo 默认账号: admin / admin123$\r$\n"
  FileWrite $0 "echo.$\r$\n"
  FileWrite $0 "start $\"$\" $\"$INSTDIR\backend\assistance-management-backend.exe$\"$\r$\n"
  FileWrite $0 "echo 后端服务已启动，按任意键打开浏览器访问系统...$\r$\n"
  FileWrite $0 "pause >nul$\r$\n"
  FileWrite $0 "start http://127.0.0.1:8000$\r$\n"
  FileClose $0

  ; 安装 VC++ Redistributable (静默安装)
  IfFileExists "$INSTDIR\redist\vc_redist.x86.exe" 0 skip_vcredist
    DetailPrint "正在安装 VC++ Redistributable (x86)..."
    ExecWait '"$INSTDIR\redist\vc_redist.x86.exe" /install /quiet /norestart' $0
    DetailPrint "VC++ Redistributable 安装完成 (退出码: $0)"
  skip_vcredist:

  ; 创建快捷方式
  CreateShortCut "$DESKTOP\${PRODUCT_NAME} (32-bit).lnk" "$INSTDIR\start.bat" "" "$INSTDIR\frontend\favicon.ico"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\start.bat" "" "$INSTDIR\frontend\favicon.ico"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\卸载 ${PRODUCT_NAME}.lnk" "$INSTDIR\uninst.exe"

  ; 写入卸载程序
  WriteUninstaller "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\start.bat"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "DisplayName" "${PRODUCT_NAME} (32-bit)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "NoRepair" 1
SectionEnd

Section Uninstall
  ; 停止运行中的进程
  nsExec::ExecToLog 'taskkill /F /IM assistance-management-backend.exe'

  Delete "$INSTDIR\backend\assistance-management-backend.exe"
  RMDir "$INSTDIR\backend"
  RMDir /r "$INSTDIR\frontend"
  RMDir /r "$INSTDIR\data"
  RMDir /r "$INSTDIR\logs"
  RMDir /r "$INSTDIR\exports"
  RMDir /r "$INSTDIR\uploads"
  RMDir /r "$INSTDIR\redist"
  Delete "$INSTDIR\.env"
  Delete "$INSTDIR\start.bat"
  Delete "$INSTDIR\uninst.exe"
  Delete "$DESKTOP\${PRODUCT_NAME} (32-bit).lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  RMDir "$INSTDIR"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86"
SectionEnd
