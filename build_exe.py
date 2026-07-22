import os
import subprocess
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def build_executable():
    print("Iniciando la compilación a ejecutable de Windows (.exe)...")
    
    static_dir = os.path.join(APP_DIR, "static")
    add_data_arg = f"{static_dir};static"

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "EpubReaderPro",
        "--add-data", add_data_arg,
        os.path.join(APP_DIR, "main.py")
    ]

    print("Comando PyInstaller:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=APP_DIR)
    
    if res.returncode == 0:
        output_path = os.path.join(APP_DIR, "dist", "EpubReaderPro", "EpubReaderPro.exe")
        print("\n==================================================")
        print("¡COMPILACIÓN EXITOSA!")
        print(f"El ejecutable ejecutable nativo se encuentra en:\n{output_path}")
        print("==================================================\n")
    else:
        print("\nError al compilar con PyInstaller.")

if __name__ == "__main__":
    build_executable()
