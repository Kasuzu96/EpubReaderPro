import os
import sys
import subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def build_exe():
    print("Iniciando la compilación a ejecutable de Windows (.exe)...")
    
    main_py = os.path.join(APP_DIR, "main.py")
    static_dir = os.path.join(APP_DIR, "static")
    icon_path = os.path.join(APP_DIR, "app_icon.ico")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "EpubReaderPro",
        "--icon", icon_path,
        "--add-data", f"{static_dir};static",
        main_py
    ]
    
    print("Comando PyInstaller:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=APP_DIR)
    
    if result.returncode == 0:
        print("\n==================================================")
        print("¡COMPILACIÓN EXITOSA!")
        print("El ejecutable nativo se encuentra en:")
        print(os.path.join(APP_DIR, "dist", "EpubReaderPro", "EpubReaderPro.exe"))
        print("==================================================\n")
    else:
        print("ERROR en la compilación.")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
