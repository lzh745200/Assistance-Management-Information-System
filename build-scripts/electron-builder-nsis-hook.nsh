; ============================================================================
; electron-builder NSIS 钩子脚本
; ----------------------------------------------------------------------------
; 通过 package.json build.nsis.include 注入到 electron-builder 生成的 NSIS
; 安装脚本中，实现以下功能：
;   1. 安装前终止旧进程（升级覆盖安装场景，避免文件占用）
;   2. 静默安装 VC++ Redistributable（双保险 Layer 2；Layer 1 由 PyInstaller
;      自动捆绑 vcruntime140.dll 等核心 DLL，因此本步骤失败不阻断安装）
;   3. 创建桌面快捷方式（使用圆形图标）
;   4. 卸载前终止运行进程（避免卸载时文件占用导致失败）
;   5. 卸载时询问是否删除 %LOCALAPPDATA%\bumofu-assistance\ 用户数据目录
;   6. 卸载时清理桌面快捷方式
;
; 说明：
;   - $INSTDIR 由 electron-builder 设置为安装目录（Program Files\帮扶管理系统）
;   - $LOCALAPPDATA 为 NSIS 内置变量，等于 %LOCALAPPDATA%
;   - customInstall / customUnInstall 是 electron-builder 内置钩子宏
;   - 圆形图标文件位于 $INSTDIR\resources\icon.png（extraResources 已拷贝）
; ============================================================================

; ----------------------------------------------------------------------------
; 安装钩子：终止旧进程 + 静默安装 VC++ + 创建桌面快捷方式
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

  ; ─── 创建桌面快捷方式（圆形图标）───
  ; electron-builder 默认创建开始菜单快捷方式，但桌面快捷方式可能因
  ; oneClick=false + 用户取消而未创建。此处强制创建桌面快捷方式，
  ; 确保用户安装后桌面有圆形图标快捷方式。
  ; ICO 文件路径：electron-builder 将 win.icon 复制到安装目录
  ; $INSTDIR\resources\app.ico 是 electron-builder 自动放置的图标
  ; 若不存在则使用 EXE 自身图标（也已嵌入圆形 ICO）
  IfFileExists "$INSTDIR\帮扶管理系统.exe" 0 skip_desktop_shortcut
    ; 尝试使用独立 ICO 文件，回退到 EXE 内嵌图标
    IfFileExists "$INSTDIR\resources\app-circle.ico" 0 use_exe_icon
      CreateShortCut "$DESKTOP\帮扶管理系统.lnk" "$INSTDIR\帮扶管理系统.exe" "" "$INSTDIR\resources\app-circle.ico" 0
      Goto shortcut_created
    use_exe_icon:
      CreateShortCut "$DESKTOP\帮扶管理系统.lnk" "$INSTDIR\帮扶管理系统.exe" "" "$INSTDIR\帮扶管理系统.exe" 0
    shortcut_created:
    DetailPrint "已创建桌面快捷方式（圆形图标）"
  skip_desktop_shortcut:
!macroend

; ----------------------------------------------------------------------------
; 卸载钩子：终止进程 + 删除桌面快捷方式 + 询问删除用户数据
; ----------------------------------------------------------------------------
!macro customUnInstall
  ; 卸载前终止运行进程，避免文件占用导致卸载失败
  nsExec::Exec 'taskkill /F /IM "帮扶管理系统.exe" /IM "assistance-backend.exe"'
  Pop $0

  ; 删除桌面快捷方式
  IfFileExists "$DESKTOP\帮扶管理系统.lnk" 0 skip_del_desktop
    Delete "$DESKTOP\帮扶管理系统.lnk"
    DetailPrint "已删除桌面快捷方式"
  skip_del_desktop:

  ; 询问用户是否删除用户数据目录（含 SQLite 数据库、上传文件、日志等）
  ; deleteAppDataOnUninstall=false（package.json）保留 userData 小文件，
  ; 此处单独询问大文件数据目录 %LOCALAPPDATA%\bumofu-assistance\
  MessageBox MB_YESNO|MB_ICONQUESTION "是否同时删除用户数据（包含数据库）?$\n$\n位置: $LOCALAPPDATA\bumofu-assistance\" IDNO keep_user_data
    RMDir /r /REBOOTOK "$LOCALAPPDATA\bumofu-assistance"
    DetailPrint "已删除用户数据目录: $LOCALAPPDATA\bumofu-assistance"
  keep_user_data:
!macroend
