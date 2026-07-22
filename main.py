import os
import sys
import json
import time
import base64
import shutil
import zipfile
import webbrowser
import xml.etree.ElementTree as ET
import webview

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Directorio persistente en AppData del usuario
USER_APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "EpubReaderPro")
os.makedirs(USER_APPDATA_DIR, exist_ok=True)

DEFAULT_DATA_FILE = os.path.join(USER_APPDATA_DIR, "library_data.json")
DEFAULT_BOOKS_DIR = os.path.join(USER_APPDATA_DIR, "books")
os.makedirs(DEFAULT_BOOKS_DIR, exist_ok=True)

def detect_google_drive_path():
    """Detecta automáticamente carpetas conocidas de Google Drive en Windows"""
    user_home = os.path.expanduser("~")
    possible_paths = [
        os.path.join(user_home, "Google Drive"),
        os.path.join(user_home, "My Drive"),
        os.path.join(user_home, "Mi unidad"),
        os.path.join(user_home, "GoogleDrive"),
        r"G:\My Drive",
        r"G:\Mi unidad",
        r"G:\\"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            target = os.path.join(p, "EpubReaderData")
            os.makedirs(target, exist_ok=True)
            return target
    return None

def extract_epub_cover_base64(epub_path):
    """Extrae la imagen de portada de un archivo .epub y devuelve Data URL Base64"""
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            if 'META-INF/container.xml' not in z.namelist():
                return None
            container_data = z.read('META-INF/container.xml')
            root = ET.fromstring(container_data)
            ns = {'c': 'urn:oasis:names:tc:opendocument:xmlns:container'}
            rootfile = root.find('.//c:rootfile', ns)
            if rootfile is None:
                return None
            opf_path = rootfile.attrib.get('full-path', '')
            opf_dir = os.path.dirname(opf_path)
            
            opf_data = z.read(opf_path)
            opf_root = ET.fromstring(opf_data)
            
            manifest_items = {}
            cover_id = None
            for item in opf_root.findall('.//{*}item'):
                i_id = item.attrib.get('id')
                href = item.attrib.get('href')
                props = item.attrib.get('properties', '')
                manifest_items[i_id] = href
                if 'cover-image' in props:
                    cover_id = i_id
            
            if not cover_id:
                for meta in opf_root.findall('.//{*}meta'):
                    if meta.attrib.get('name') == 'cover':
                        cover_id = meta.attrib.get('content')
            
            cover_href = None
            if cover_id and cover_id in manifest_items:
                cover_href = manifest_items[cover_id]
            
            if not cover_href:
                for name in z.namelist():
                    lower_name = name.lower()
                    if ('cover' in lower_name or 'portada' in lower_name) and (lower_name.endswith('.jpg') or lower_name.endswith('.jpeg') or lower_name.endswith('.png') or lower_name.endswith('.webp')):
                        cover_href = name
                        opf_dir = ''
                        break
            
            if cover_href:
                full_cover_path = os.path.normpath(os.path.join(opf_dir, cover_href)).replace('\\', '/')
                if full_cover_path in z.namelist():
                    cover_bytes = z.read(full_cover_path)
                    mime = 'image/jpeg'
                    if full_cover_path.lower().endswith('.png'): mime = 'image/png'
                    elif full_cover_path.lower().endswith('.webp'): mime = 'image/webp'
                    b64 = base64.b64encode(cover_bytes).decode('utf-8')
                    return f"data:{mime};base64,{b64}"
    except Exception as e:
        print("Extract cover notice:", e)
    return None

class EpubApi:
    def __init__(self):
        self._window = None
        self._sync_folder = None
        self._init_data_store()

    def set_window(self, window):
        self._window = window

    def _init_data_store(self):
        """Carga la configuración de sincronización almacenada persistentemente"""
        if os.path.exists(DEFAULT_DATA_FILE):
            try:
                with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if d.get("settings") and d["settings"].get("syncFolder"):
                        self._sync_folder = d["settings"]["syncFolder"]
            except Exception as e:
                pass

    def open_google_drive_web(self):
        """Abre Google Drive en el navegador predeterminado del usuario"""
        webbrowser.open("https://drive.google.com")
        return {"success": True}

    def open_sync_folder_explorer(self):
        """Abre la carpeta de sincronización en el Explorador de Windows"""
        target = self._sync_folder if (self._sync_folder and os.path.exists(self._sync_folder)) else USER_APPDATA_DIR
        try:
            os.startfile(target)
            return {"success": True, "path": target}
        except Exception as e:
            return {"error": str(e)}

    def select_sync_folder_dialog(self):
        if not self._window:
            return {"error": "Ventana no inicializada"}
        
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result and len(result) > 0:
            chosen_folder = result[0]
            target_folder = os.path.join(chosen_folder, "EpubReaderData") if not chosen_folder.endswith("EpubReaderData") else chosen_folder
            os.makedirs(target_folder, exist_ok=True)
            
            self._sync_folder = target_folder
            self._sync_files_bidirectional()
            return {"success": True, "sync_folder": target_folder}
        return {"cancelled": True}

    def auto_connect_google_drive(self):
        drive_path = detect_google_drive_path()
        if drive_path:
            self._sync_folder = drive_path
            self._sync_files_bidirectional()
            return {"success": True, "sync_folder": drive_path}
        return {"error": "No se encontró la carpeta predeterminada de Google Drive. Por favor haz clic en 'Seleccionar Carpeta'."}

    def _sync_files_bidirectional(self):
        if not self._sync_folder or not os.path.exists(self._sync_folder):
            return

        sync_data_file = os.path.join(self._sync_folder, "library_data.json")
        sync_books_dir = os.path.join(self._sync_folder, "books")
        os.makedirs(sync_books_dir, exist_ok=True)

        local_mtime = os.path.getmtime(DEFAULT_DATA_FILE) if os.path.exists(DEFAULT_DATA_FILE) else 0
        drive_mtime = os.path.getmtime(sync_data_file) if os.path.exists(sync_data_file) else 0

        if drive_mtime > local_mtime:
            shutil.copy2(sync_data_file, DEFAULT_DATA_FILE)
        elif local_mtime > drive_mtime and os.path.exists(DEFAULT_DATA_FILE):
            shutil.copy2(DEFAULT_DATA_FILE, sync_data_file)

        if os.path.exists(DEFAULT_BOOKS_DIR):
            for f in os.listdir(DEFAULT_BOOKS_DIR):
                src = os.path.join(DEFAULT_BOOKS_DIR, f)
                dst = os.path.join(sync_books_dir, f)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)

        if os.path.exists(sync_books_dir):
            for f in os.listdir(sync_books_dir):
                src = os.path.join(sync_books_dir, f)
                dst = os.path.join(DEFAULT_BOOKS_DIR, f)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)

    def select_and_import_epub(self):
        if not self._window:
            return None
        file_types = ('Archivos EPUB (*.epub)', 'Todos los archivos (*.*)')
        result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if not result or len(result) == 0:
            return None
        
        original_path = result[0]
        file_name = os.path.basename(original_path)
        dest_path = os.path.join(DEFAULT_BOOKS_DIR, file_name)

        try:
            if os.path.abspath(original_path) != os.path.abspath(dest_path):
                shutil.copy2(original_path, dest_path)

            if self._sync_folder and os.path.exists(self._sync_folder):
                sync_books = os.path.join(self._sync_folder, "books")
                os.makedirs(sync_books, exist_ok=True)
                shutil.copy2(dest_path, os.path.join(sync_books, file_name))

            cover_b64 = extract_epub_cover_base64(dest_path)
            res = self.read_epub_base64(dest_path)
            if cover_b64:
                res["cover_b64"] = cover_b64
            return res
        except Exception as e:
            return {"error": f"Error al importar archivo: {str(e)}"}

    def read_epub_base64(self, file_path):
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(DEFAULT_BOOKS_DIR, file_path)

            if not os.path.exists(file_path):
                if self._sync_folder:
                    alt_path = os.path.join(self._sync_folder, "books", os.path.basename(file_path))
                    if os.path.exists(alt_path):
                        shutil.copy2(alt_path, file_path)

            if not os.path.exists(file_path):
                return {"error": f"El archivo no existe en: {file_path}"}

            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            
            cover_b64 = extract_epub_cover_base64(file_path)

            return {
                "success": True,
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "cover_b64": cover_b64,
                "data": encoded
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_book_from_library(self, book_id, file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if self._sync_folder:
                sync_path = os.path.join(self._sync_folder, "books", os.path.basename(file_path))
                if os.path.exists(sync_path):
                    os.remove(sync_path)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def save_library_data(self, data_json_str):
        try:
            data = json.loads(data_json_str) if isinstance(data_json_str, str) else data_json_str
            data["last_updated"] = time.time()

            with open(DEFAULT_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            if self._sync_folder and os.path.exists(self._sync_folder):
                sync_file = os.path.join(self._sync_folder, "library_data.json")
                with open(sync_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def load_library_data(self):
        try:
            self._sync_files_bidirectional()

            if os.path.exists(DEFAULT_DATA_FILE):
                with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self._sync_folder:
                        if "settings" not in data: data["settings"] = {}
                        data["settings"]["syncFolder"] = self._sync_folder
                    return data
            return {"books": {}}
        except Exception as e:
            return {"books": {}}

    def export_notes_file(self, default_name, content, file_format):
        if not self._window:
            return {"error": "Ventana no inicializada"}
        
        ext_desc = "Archivo Markdown (*.md)" if file_format == "md" else "Archivo de Texto (*.txt)"
        file_types = (ext_desc, 'Todos los archivos (*.*)')

        save_path = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
            file_types=file_types
        )
        if save_path:
            target_path = save_path[0] if isinstance(save_path, (list, tuple)) else save_path
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": target_path}
        return {"cancelled": True}

def main():
    api = EpubApi()
    html_path = os.path.join(APP_DIR, "static", "index.html")
    
    window = webview.create_window(
        title="Lector EPUB - Biblioteca y Notas",
        url=html_path,
        js_api=api,
        width=1280,
        height=850,
        min_size=(900, 600),
        background_color='#f5f0e6'
    )
    api.set_window(window)
    webview.start(debug=False)

if __name__ == "__main__":
    main()
