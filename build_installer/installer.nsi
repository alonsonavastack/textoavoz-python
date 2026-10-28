; ==============================================================================
;  Instalador NSIS para Texto a Voz Studio (100% Autonomo / Standalone)
;  Empaqueta el runtime completo con Python embebido, Tkinter y librerias
; ==============================================================================

Unicode True
Name "Texto a Voz Studio"
OutFile "..\Instalador_TextoAVoz_Windows.exe"
InstallDir "$LOCALAPPDATA\Texto a Voz Studio"
RequestExecutionLevel user
SetCompressor /SOLID lzma

; ── Includes y Modern UI ──────────────────────────────────────────────────────
!include "MUI2.nsh"
!include "LogicLib.nsh"

!define MUI_ICON "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"
!define MUI_ABORTWARNING

; ── Páginas ───────────────────────────────────────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Pagina final con opcion de iniciar inmediatamente
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION "EjecutarApp"
!define MUI_FINISHPAGE_RUN_TEXT "Iniciar Texto a Voz Studio ahora"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ── Idioma ────────────────────────────────────────────────────────────────────
!insertmacro MUI_LANGUAGE "Spanish"

; ── Seccion de instalacion ────────────────────────────────────────────────────
Section "Instalar" SecMain

    SetOutPath "$INSTDIR"

    ; Copiar todos los archivos pre-empaquetados y pre-configurados
    DetailPrint "Instalando aplicacion y entorno de audio..."
    File /r "bundle_payload\*.*"

    ; Crear accesos directos
    DetailPrint "Creando accesos directos en Escritorio y Menu Inicio..."
    CreateShortcut "$DESKTOP\Texto a Voz Studio.lnk" \
        "$SYSDIR\wscript.exe" '"$INSTDIR\TextoAVoz.vbs"' \
        "$INSTDIR\assets\icon.ico" 0 \
        SW_SHOWNORMAL "" "Texto a Voz Studio"

    CreateDirectory "$SMPROGRAMS\Texto a Voz Studio"
    CreateShortcut "$SMPROGRAMS\Texto a Voz Studio\Texto a Voz Studio.lnk" \
        "$SYSDIR\wscript.exe" '"$INSTDIR\TextoAVoz.vbs"' \
        "$INSTDIR\assets\icon.ico" 0 \
        SW_SHOWNORMAL "" "Texto a Voz Studio"

    CreateShortcut "$SMPROGRAMS\Texto a Voz Studio\Modo Diagnostico (Consola).lnk" \
        "$INSTDIR\Diagnostico_TextoAVoz.bat" "" "$INSTDIR\assets\icon.ico" 0

    CreateShortcut "$SMPROGRAMS\Texto a Voz Studio\Desinstalar.lnk" \
        "$INSTDIR\Desinstalar.exe" "" "$INSTDIR\Desinstalar.exe" 0

    ; Registrar en Panel de Control / Configuracion de Windows
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio" "DisplayName" "Texto a Voz Studio"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio" "DisplayVersion" "1.0.0"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio" "DisplayIcon" "$INSTDIR\assets\icon.ico"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio" "UninstallString" "$INSTDIR\Desinstalar.exe"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio" "NoRepair" 1

    ; Generar desinstalador
    WriteUninstaller "$INSTDIR\Desinstalar.exe"

    DetailPrint "Instalacion completada con exito!"

SectionEnd

; ── Funcion para iniciar app al finalizar ─────────────────────────────────────
Function EjecutarApp
    ExecShell "" "$INSTDIR\TextoAVoz.vbs"
FunctionEnd

; ── Seccion de desinstalacion ─────────────────────────────────────────────────
Section "Uninstall"

    ; Eliminar accesos directos
    Delete "$DESKTOP\Texto a Voz Studio.lnk"
    RMDir /r "$SMPROGRAMS\Texto a Voz Studio"

    ; Eliminar registro
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\TextoAVozStudio"

    ; Eliminar archivos de la aplicacion
    RMDir /r "$INSTDIR"

SectionEnd
