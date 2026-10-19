; -*- coding: utf-8 -*-
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"

Name "YouTube to MP3"
OutFile "${OUTPUT_FILE}"
InstallDir "$LOCALAPPDATA\Programs\YouTubeToMP3"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
ShowInstDetails show
ShowUninstDetails show
BrandingText "YouTube to MP3"
Icon "${APP_ICON}"
UninstallIcon "${APP_ICON}"
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "YouTube to MP3"
VIAddVersionKey "FileDescription" "YouTube to MP3 Setup"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "goyofunk"

Var NoIntegration
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "YouTube to MP3 설치"
!define MUI_WELCOMEPAGE_TEXT "Python을 따로 설치하지 않아도 사용할 수 있습니다.$\r$\n$\r$\n현재 Windows 사용자 전용으로 설치하며, 다운로드한 음악은 설치 폴더와 별도로 보관합니다."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\YouTube to MP3.exe"
!define MUI_FINISHPAGE_RUN_TEXT "YouTube to MP3 실행"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Korean"

Function .onInit
    ${IfNot} ${RunningX64}
        MessageBox MB_OK|MB_ICONSTOP "이 설치 파일은 64비트 Windows용입니다."
        Abort
    ${EndIf}
    ${GetParameters} $0
    ClearErrors
    ${GetOptions} $0 "/NOINTEGRATION" $1
    ${IfNot} ${Errors}
        StrCpy $NoIntegration "1"
    ${EndIf}
FunctionEnd

Section "YouTube to MP3"
    SetShellVarContext current
    SetOutPath "$INSTDIR"
    File /r "${BUNDLE_DIR}\*"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    ${If} $NoIntegration == "1"
        FileOpen $0 "$INSTDIR\no-integration.flag" w
        FileClose $0
    ${Else}
        CreateDirectory "$SMPROGRAMS\YouTube to MP3"
        CreateShortcut "$SMPROGRAMS\YouTube to MP3\YouTube to MP3.lnk" "$INSTDIR\YouTube to MP3.exe" "" "$INSTDIR\icon.ico"
        CreateShortcut "$SMPROGRAMS\YouTube to MP3\제거.lnk" "$INSTDIR\Uninstall.exe"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "DisplayName" "YouTube to MP3"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "DisplayVersion" "${APP_VERSION}"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "Publisher" "goyofunk"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "InstallLocation" "$INSTDIR"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "DisplayIcon" "$INSTDIR\icon.ico"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
        WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "NoModify" 1
        WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3" "NoRepair" 1
    ${EndIf}
SectionEnd

Section "Uninstall"
    SetShellVarContext current
    IfFileExists "$INSTDIR\no-integration.flag" no_integration
    Delete "$SMPROGRAMS\YouTube to MP3\YouTube to MP3.lnk"
    Delete "$SMPROGRAMS\YouTube to MP3\제거.lnk"
    RMDir "$SMPROGRAMS\YouTube to MP3"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\YouTubeToMP3"
    no_integration:
    !include "${UNINSTALL_MANIFEST}"
    Delete "$INSTDIR\no-integration.flag"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
SectionEnd
