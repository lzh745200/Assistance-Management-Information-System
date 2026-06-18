; Assistance Management System - NSIS Installer Script
; Produces standalone .exe installer with all runtimes bundled

!define PRODUCT_NAME "Assistance System"
!define PRODUCT_VERSION "1.3.0"
!define PRODUCT_PUBLISHER "Military"

SetCompressor /SOLID lzma
SetCompressorDictSize 64

!include "MUI2.nsh"
!include "x64.nsh"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\build\dist\setup-${PRODUCT_VERSION}.exe"
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

  ${If} ${RunningX64}
    File /r "..\build\pkg-x64\*.*"
  ${Else}
    File /r "..\build\pkg-x86\*.*"
  ${EndIf}

  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"

  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$OUTDIR\start.bat"
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$OUTDIR\start.bat"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe"

  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
SectionEnd

Section Uninstall
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
SectionEnd
