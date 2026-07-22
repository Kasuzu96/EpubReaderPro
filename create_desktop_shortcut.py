import os
import sys

desktop_dir = os.path.expanduser("~/Desktop")
exe_path = r"C:\Users\Ludwig\.gemini\antigravity\scratch\epub_reader\dist\EpubReaderPro\EpubReaderPro.exe"
work_dir = r"C:\Users\Ludwig\.gemini\antigravity\scratch\epub_reader\dist\EpubReaderPro"

# 1. Create .bat launcher on Desktop
bat_content = f"""@echo off
start "" "{exe_path}"
"""
bat_path = os.path.join(desktop_dir, "Lector EPUB Pro.bat")
with open(bat_path, "w", encoding="utf-8") as f:
    f.write(bat_content)

# 2. Create .lnk shortcut using VBScript
vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
Set shortcut = WshShell.CreateShortcut("{os.path.join(desktop_dir, 'Lector EPUB Pro.lnk')}")
shortcut.TargetPath = "{exe_path}"
shortcut.WorkingDirectory = "{work_dir}"
shortcut.Save
"""
vbs_path = os.path.join(os.path.dirname(__file__), "make_shortcut.vbs")
with open(vbs_path, "w", encoding="utf-8") as f:
    f.write(vbs_content)

os.system(f'cscript //nologo "{vbs_path}"')
print("Acceso directo y lanzador creados en el escritorio.")
