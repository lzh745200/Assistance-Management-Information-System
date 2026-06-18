!define PRODUCT_NAME "Assistance System"
!define PRODUCT_VERSION "1.4.0"
SetCompressor /SOLID lzma
SetCompressorDictSize 64
!include "MUI2.nsh"
!define MUI_ICON "app-icon.ico"
!define MUI_UNICON "app-icon.ico"
Name "${PRODUCT_NAME} ${PRODUCT_VERSION} (32-bit)"
OutFile "..\build\dist\setup-${PRODUCT_VERSION}-x86.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
RequestExecutionLevel admin
ShowInstDetails show
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
Section "Install" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File /r "..\build\pkg-x86\*.*"
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME} (32-bit).lnk" "$OUTDIR\start.bat"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$OUTDIR\start.bat"
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "DisplayName" "${PRODUCT_NAME} (32-bit)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86" "UninstallString" "$INSTDIR\uninst.exe"
SectionEnd
Section Uninstall
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\${PRODUCT_NAME} (32-bit).lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}-x86"
SectionEnd
