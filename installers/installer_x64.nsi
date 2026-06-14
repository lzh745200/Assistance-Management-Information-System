; Military Rural Revitalization System - Windows x64 Installer (NSIS)
!include "MUI2.nsh"

!define PRODUCT_NAME "MilitaryRuralRevitalization"
!define PRODUCT_DISPLAY "Military Rural Revitalization System"
!define PRODUCT_VERSION "1.2.0"

SetCompressor /SOLID lzma
RequestExecutionLevel admin
Name "${PRODUCT_DISPLAY} ${PRODUCT_VERSION}"
OutFile "..\dist\windows\${PRODUCT_NAME}-${PRODUCT_VERSION}-x64-Setup.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  DetailPrint "Installing backend service..."
  File /r "..\dist\windows\package\military-rural-backend.exe"
  File "..\dist\windows\package\launch.py"
  DetailPrint "Installing frontend..."
  SetOutPath "$INSTDIR\resources\frontend"
  File /r "..\resources\frontend\*.*"
  SetOutPath "$INSTDIR"
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\uploads"
  CreateDirectory "$INSTDIR\exports"
  CreateDirectory "$INSTDIR\backups"
  CreateShortCut "$DESKTOP\Military Rural Revitalization.lnk" "$INSTDIR\military-rural-backend.exe"
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_DISPLAY}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
SectionEnd

Section "Uninstall"
  MessageBox MB_YESNO "Keep database and uploaded files for future reinstall?" IDYES KeepData
  RMDir /r "$INSTDIR"
  Goto Done
  KeepData:
  RMDir /r "$INSTDIR\resources"
  RMDir /r "$INSTDIR\logs"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\*.py"
  Done:
  Delete "$DESKTOP\Military Rural Revitalization.lnk"
  DeleteRegKey HKLM "Software\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
