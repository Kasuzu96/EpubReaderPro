import os
import shutil
import zipfile

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(APP_DIR, "dist", "EpubReaderPro")
INSTALLER_BAT = os.path.join(APP_DIR, "Instalar_EpubReaderPro.bat")
OUTPUT_ZIP = os.path.join(APP_DIR, "EpubReaderPro_Instalador_Completo.zip")

def create_installer_package():
    print("Empaquetando instalador completo de EpubReaderPro...")

    if not os.path.exists(DIST_DIR):
        print("ERROR: No se encontró la carpeta dist/EpubReaderPro. Compila primero.")
        return

    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Include Instalar_EpubReaderPro.bat at root of zip
        if os.path.exists(INSTALLER_BAT):
            zipf.write(INSTALLER_BAT, "Instalar_EpubReaderPro.bat")

        # 2. Include all app binaries in dist/EpubReaderPro
        for root, dirs, files in os.walk(DIST_DIR):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, APP_DIR)
                zipf.write(abs_file, rel_file)

    print(f"==================================================")
    print(f"¡PAQUETE INSTALADOR CREADO CON ÉXITO!")
    print(f"Ubicación del ZIP listo para llevar a cualquier PC:")
    print(f"{OUTPUT_ZIP}")
    print(f"==================================================")

if __name__ == "__main__":
    create_installer_package()
