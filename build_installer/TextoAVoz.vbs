Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Obtener la carpeta donde esta instalada la aplicacion
appDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Buscar pythonw.exe (modo sin ventana de consola negra)
pywPath = "pythonw.exe"
localPyw = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\pythonw.exe"
localPyw311 = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\pythonw.exe"
localPyw310 = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python310\pythonw.exe"

If fso.FileExists(localPyw) Then
    pywPath = """" & localPyw & """"
ElseIf fso.FileExists(localPyw311) Then
    pywPath = """" & localPyw311 & """"
ElseIf fso.FileExists(localPyw310) Then
    pywPath = """" & localPyw310 & """"
ElseIf fso.FileExists("C:\Python312\pythonw.exe") Then
    pywPath = """C:\Python312\pythonw.exe"""
End If

cmd = pywPath & " """ & appDir & "\app.py"""

WshShell.CurrentDirectory = appDir
' 0 oculta completamente cualquier ventana de consola auxiliar
WshShell.Run cmd, 0, False
