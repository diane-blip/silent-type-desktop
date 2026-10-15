Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
shell.Run Chr(34) & folder & "\.venv\Scripts\pythonw.exe" & Chr(34) & " -m silent_type", 0, False
