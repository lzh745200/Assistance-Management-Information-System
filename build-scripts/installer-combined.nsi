!define PRODUCT_NAME "Assistance System"
!define PRODUCT_VERSION "1.2.0"
SetCompressor /SOLID lzma
SetCompressorDictSize 64
!include "MUI2.nsh"
!include "x64.nsh"
!define MUI_ICON "app-icon.ico"
!define MUI_UNICON "app-icon.ico"
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\build\dist\setup-${PRODUCT_VERSION}-combined.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
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
  File /r "..\build\pkg-combined\*.*"
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"
  CreateShortCut "$DESKTOP\Assistance System.lnk" "$OUTDIR\start.bat"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Assistance System.lnk" "$OUTDIR\start.bat"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe"
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
SectionEnd
Section Uninstall
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\Assistance System.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
