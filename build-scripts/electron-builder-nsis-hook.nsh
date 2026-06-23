; ============================================================================
; electron-builder NSIS 钩子脚本
; ----------------------------------------------------------------------------
; 通过 package.json build.nsis.include 注入到 electron-builder 生成的 NSIS
; 安装脚本中，实现以下功能：
;   1. 安装前终止旧进程（升级覆盖安装场景，避免文件占用）
;   2. 静默安装 VC++ Redistributable（双保险 Layer 2；Layer 1 由 PyInstaller
;      自动捆绑 vcruntime140.dll 等核心 DLL，因此本步骤失败不阻断安装）
;   3. 卸载前终止运行进程（避免卸载时文件占用导致失败）
;   4. 卸载时询问是否删除 %LOCALAPPDATA%\bumofu-assistance\ 用户数据目录
;
; 说明：
;   - $INSTDIR 由 electron-builder 设置为安装目录（Program Files\帮扶管理系统）
;   - $LOCALAPPDATA 为 NSIS 内置变量，等于 %LOCALAPPDATA%
;   - customInstall / customUnInstall 是 electron-builder 内置钩子宏
; ============================================================================

; ----------------------------------------------------------------------------
; 安装钩子：终止旧进程 + 静默安装 VC++ Redistributable
; ----------------------------------------------------------------------------
!macro customInstall
  ; 安装前终止可能正在运行的旧进程（升级场景）
  ; taskkill 在进程不存在时返回非零退出码，Pop 丢弃即可，不阻断安装
  nsExec::Exec 'taskkill /F /IM "帮扶管理系统.exe" /IM "assistance-backend.exe"'
  Pop $0

  ; 静默安装 VC++ Redistributable（双保险 Layer 2）
  ; 根据实际存在的安装器文件判断架构（CI 仅放置匹配架构的 vc_redist）
  ; /install /quiet /norestart = 静默安装、不重启、无 UI
  ; 安装失败不阻断 —— PyInstaller 已捆绑核心 vcruntime DLL（Layer 1 兜底）
  IfFileExists "$INSTDIR\resources\vcredist\vc_redist.x64.exe" 0 try_x86_redist
    DetailPrint "正在安装 VC++ Redistributable (x64)..."
    nsExec::Exec '"$INSTDIR\resources\vcredist\vc_redist.x64.exe" /install /quiet /norestart'
    Pop $0
    Goto vcredist_done
  try_x86_redist:
  IfFileExists "$INSTDIR\resources\vcredist\vc_redist.x86.exe" 0 vcredist_done
    DetailPrint "正在安装 VC++ Redistributable (x86)..."
    nsExec::Exec '"$INSTDIR\resources\vcredist\vc_redist.x86.exe" /install /quiet /norestart'
    Pop $0
  vcredist_done:
!macroend

; ----------------------------------------------------------------------------
; 卸载钩子：终止进程 + 询问删除用户数据
; ----------------------------------------------------------------------------
!macro customUnInstall
  ; 卸载前终止运行进程，避免文件占用导致卸载失败
  nsExec::Exec 'taskkill /F /IM "帮扶管理系统.exe" /IM "assistance-backend.exe"'
  Pop $0

  ; 询问用户是否删除用户数据目录（含 SQLite 数据库、上传文件、日志等）
  ; deleteAppDataOnUninstall=false（package.json）保留 userData 小文件，
  ; 此处单独询问大文件数据目录 %LOCALAPPDATA%\bumofu-assistance\
  MessageBox MB_YESNO|MB_ICONQUESTION "是否同时删除用户数据（包含数据库）?$\n$\n位置: $LOCALAPPDATA\bumofu-assistance\" IDNO keep_user_data
    RMDir /r /REBOOTOK "$LOCALAPPDATA\bumofu-assistance"
    DetailPrint "已删除用户数据目录: $LOCALAPPDATA\bumofu-assistance"
  keep_user_data:
!macroend
