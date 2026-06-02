; MRRMS v1.2.0 - NSIS Installer Script
; Military Rural Revitalization Management System

!define PRODUCT_NAME "MRRMS"
!define PRODUCT_FULL_NAME "Military Rural Revitalization Management System"
!define PRODUCT_VERSION "1.2.0"
!define PRODUCT_PUBLISHER "MRRMS Team"
!define PRODUCT_WEB_SITE "http://localhost:8000"

SetCompressor lzma

!include "MUI2.nsh"
!include "FileFunc.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "bz.ico"
!define MUI_UNICON "bz.ico"

; Welcome page
!define MUI_WELCOMEPAGE_TITLE "Welcome to MRRMS ${PRODUCT_VERSION} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of ${PRODUCT_FULL_NAME}.$\r$\n$\r$\nMRRMS is a comprehensive management system for military rural revitalization projects.$\r$\n$\r$\nClick Next to continue."
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_TITLE "MRRMS Installation Complete"
!define MUI_FINISHPAGE_TEXT "${PRODUCT_FULL_NAME} has been installed successfully.$\r$\n$\r$\nClick Finish to close this wizard."
!define MUI_FINISHPAGE_RUN "$INSTDIR\MRRMS.bat"
!define MUI_FINISHPAGE_RUN_TEXT "Launch MRRMS now"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Show README"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "SimpChinese"

; Installer attributes
Name "${PRODUCT_FULL_NAME} ${PRODUCT_VERSION}"
OutFile "dist\windows\MRRMS-${PRODUCT_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\MRRMS"
InstallDirRegKey HKLM "Software\MRRMS" "InstallDir"
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; Version information
VIProductVersion "1.2.0.0"
VIAddVersionKey "ProductName" "${PRODUCT_FULL_NAME}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey "FileDescription" "${PRODUCT_FULL_NAME} Installer"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite on

  ; Copy all files
  File /r "dist\windows\package\backend"
  File /r "dist\windows\package\frontend"
  File "dist\windows\package\MRRMS.bat"

  ; Create README
  FileOpen $0 "$INSTDIR\README.txt" w
  FileWrite $0 "MRRMS v${PRODUCT_VERSION}$\r$\n"
  FileWrite $0 "Military Rural Revitalization Management System$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "Quick Start:$\r$\n"
  FileWrite $0 "1. Double-click MRRMS.bat to start the system$\r$\n"
  FileWrite $0 "2. Browser will open automatically$\r$\n"
  FileWrite $0 "3. Access: http://localhost:8000$\r$\n"
  FileWrite $0 "4. Default account: admin / admin123$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "System Requirements:$\r$\n"
  FileWrite $0 "- Windows 10/11 or Windows Server 2016+$\r$\n"
  FileWrite $0 "- 2GB RAM minimum$\r$\n"
  FileWrite $0 "- 500MB disk space$\r$\n"
  FileWrite $0 "$\r$\n"
  FileWrite $0 "Data Location: $INSTDIR\data$\r$\n"
  FileWrite $0 "Logs Location: $INSTDIR\logs$\r$\n"
  FileClose $0

  ; Create data directories
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\data\uploads"
  CreateDirectory "$INSTDIR\data\backups"
  CreateDirectory "$INSTDIR\logs"

  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\MRRMS.bat" "" "$INSTDIR\MRRMS.bat" 0
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\README.lnk" "$INSTDIR\README.txt"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\MRRMS.bat" "" "$INSTDIR\MRRMS.bat" 0
SectionEnd

Section -AdditionalIcons
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall ${PRODUCT_NAME}.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"

  ; Write registry keys
  WriteRegStr HKLM "Software\MRRMS" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\MRRMS" "Version" "${PRODUCT_VERSION}"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_FULL_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayIcon" "$INSTDIR\MRRMS.bat"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "NoRepair" 1

  ; Calculate installed size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "EstimatedSize" "$0"
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "${PRODUCT_FULL_NAME} has been successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove ${PRODUCT_FULL_NAME} and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  ; Stop any running processes
  ExecWait 'taskkill /F /IM military-rural-backend.exe /T' $0

  ; Delete files and directories
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\MRRMS.bat"
  Delete "$INSTDIR\start.bat"
  Delete "$INSTDIR\启动系统.bat"
  Delete "$INSTDIR\README.txt"

  RMDir /r "$INSTDIR\backend"
  RMDir /r "$INSTDIR\frontend"

  ; Ask about data
  MessageBox MB_ICONQUESTION|MB_YESNO "Do you want to remove user data and logs?" IDNO +3
  RMDir /r "$INSTDIR\data"
  RMDir /r "$INSTDIR\logs"

  RMDir "$INSTDIR"

  ; Delete shortcuts
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\*.*"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"

  ; Delete registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\MRRMS"

  SetAutoClose true
SectionEnd
