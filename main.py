import os
import sys
import json
import time
import base64
import shutil
import zipfile
import urllib.request
import urllib.parse
import urllib.error
import webbrowser
import xml.etree.ElementTree as ET
import webview

APP_DIR = os.path.dirname(os.path.abspath(__file__))

USER_APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "EpubReaderPro")
os.makedirs(USER_APPDATA_DIR, exist_ok=True)

DEFAULT_DATA_FILE = os.path.join(USER_APPDATA_DIR, "library_data.json")
DEFAULT_BOOKS_DIR = os.path.join(USER_APPDATA_DIR, "books")
os.makedirs(DEFAULT_BOOKS_DIR, exist_ok=True)

class GoogleDriveCloudAPI:
    """Cliente directo de la API v3 de Google Drive para sincronización en la nube sin necesidad de app de escritorio"""
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.folder_id = None
        if self.access_token:
            self.ensure_remote_folder()

    def set_token(self, token):
        self.access_token = token.strip() if token else None
        return self.ensure_remote_folder()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def ensure_remote_folder(self):
        """Busca o crea la carpeta 'EpubReaderData' directamente en la nube de Google Drive"""
        if not self.access_token:
            return None
        
        query = urllib.parse.quote("name='EpubReaderData' and mimeType='application/vnd.google-apps.folder' and trashed=false")
        url = f"https://www.googleapis.com/drive/v3/files?q={query}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                files = data.get("files", [])
                if files:
                    self.folder_id = files[0]["id"]
                    return self.folder_id
        except Exception as e:
            print("Notice checking remote drive folder:", e)

        create_url = "https://www.googleapis.com/drive/v3/files"
        payload = json.dumps({
            "name": "EpubReaderData",
            "mimeType": "application/vnd.google-apps.folder"
        }).encode("utf-8")
        headers = self._headers()
        headers["Content-Type"] = "application/json"
        req_create = urllib.request.Request(create_url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req_create) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                self.folder_id = data.get("id")
                return self.folder_id
        except Exception as e:
            print("Notice creating remote drive folder:", e)
            return None

    def upload_file_to_drive(self, file_name, file_bytes, mime_type="application/octet-stream"):
        """Sube o actualiza un archivo en la carpeta EpubReaderData de Google Drive Cloud"""
        if not self.access_token or not self.folder_id:
            return False
        
        query = urllib.parse.quote(f"'{self.folder_id}' in parents and name='{file_name}' and trashed=false")
        search_url = f"https://www.googleapis.com/drive/v3/files?q={query}"
        file_id = None
        req = urllib.request.Request(search_url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as resp:
                files = json.loads(resp.read().decode('utf-8')).get("files", [])
                if files:
                    file_id = files[0]["id"]
        except Exception:
            pass

        boundary = "----EpubReaderBoundary12345"
        meta = {"name": file_name}
        if not file_id:
            meta["parents"] = [self.folder_id]

        body = (
            f"--{boundary}\r\n"
            f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(meta)}\r\n"
            f"--{boundary}\r\n"
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode('utf-8') + file_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')

        if file_id:
            upload_url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=multipart"
            method = "PATCH"
        else:
            upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
            method = "POST"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}"
        }
        req_upload = urllib.request.Request(upload_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req_upload) as resp:
                return True
        except Exception as e:
            print("Error uploading to Google Drive API:", e)
            return False

    def download_file_from_drive(self, file_name):
        """Descarga un archivo desde la carpeta EpubReaderData en Google Drive Cloud"""
        if not self.access_token or not self.folder_id:
            return None
        
        query = urllib.parse.quote(f"'{self.folder_id}' in parents and name='{file_name}' and trashed=false")
        search_url = f"https://www.googleapis.com/drive/v3/files?q={query}"
        file_id = None
        req = urllib.request.Request(search_url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as resp:
                files = json.loads(resp.read().decode('utf-8')).get("files", [])
                if files:
                    file_id = files[0]["id"]
        except Exception:
            pass

        if not file_id:
            return None

        download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        req_down = urllib.request.Request(download_url, headers=self._headers())
        try:
            with urllib.request.urlopen(req_down) as resp:
                return resp.read()
        except Exception as e:
            print("Error downloading from Google Drive API:", e)
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
        self._cloud_token = None
        self.cloud_api = GoogleDriveCloudAPI()
        self._init_data_store()

    def set_window(self, window):
        self._window = window

    def _init_data_store(self):
        if os.path.exists(DEFAULT_DATA_FILE):
            try:
                with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    settings = d.get("settings", {})
                    if settings.get("syncFolder"):
                        self._sync_folder = settings["syncFolder"]
                    if settings.get("googleCloudToken"):
                        self._cloud_token = settings["googleCloudToken"]
                        self.cloud_api.set_token(self._cloud_token)
            except Exception:
                pass

    def connect_google_cloud_token(self, token_str):
        """Conecta directamente con la API en la nube de Google Drive usando el token proporcionado"""
        if not token_str or not token_str.strip():
            return {"error": "Por favor ingresa un token válido."}
        
        folder_id = self.cloud_api.set_token(token_str)
        if folder_id:
            self._cloud_token = token_str.strip()
            self._sync_to_cloud_api()
            return {"success": True, "folder_id": folder_id}
        else:
            return {"error": "No se pudo conectar a Google Drive con este token. Verifica que el token tenga permisos de Google Drive API."}

    def open_google_oauth_page(self):
        """Abre la página para obtener un Token de Google Drive de manera fácil"""
        webbrowser.open("https://developers.google.com/oauthplayground/?scopes=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive.file")
        return {"success": True}

    def _sync_to_cloud_api(self):
        """Sincroniza datos y libros hacia y desde Google Drive Cloud API"""
        if not self._cloud_token or not self.cloud_api.folder_id:
            return

        # 1. Intentar descargar biblioteca remota
        remote_bytes = self.cloud_api.download_file_from_drive("library_data.json")
        if remote_bytes:
            try:
                remote_data = json.loads(remote_bytes.decode('utf-8'))
                remote_mtime = remote_data.get("last_updated", 0)
                
                local_mtime = 0
                if os.path.exists(DEFAULT_DATA_FILE):
                    with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                        loc_d = json.load(f)
                        local_mtime = loc_d.get("last_updated", 0)

                if remote_mtime > local_mtime:
                    with open(DEFAULT_DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(remote_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print("Notice merging remote cloud data:", e)

        # 2. Subir library_data.json actual a la nube
        if os.path.exists(DEFAULT_DATA_FILE):
            with open(DEFAULT_DATA_FILE, "rb") as f:
                self.cloud_api.upload_file_to_drive("library_data.json", f.read(), "application/json")

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

            # Subir también a la nube si API activa
            if self._cloud_token and self.cloud_api.folder_id:
                with open(dest_path, "rb") as f:
                    self.cloud_api.upload_file_to_drive(file_name, f.read(), "application/epub+zip")

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
                # Buscar en la nube si API activa
                if self._cloud_token and self.cloud_api.folder_id:
                    file_name = os.path.basename(file_path)
                    cloud_bytes = self.cloud_api.download_file_from_drive(file_name)
                    if cloud_bytes:
                        with open(file_path, "wb") as f:
                            f.write(cloud_bytes)

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

            # Subir a Google Drive Cloud API si token activo
            if self._cloud_token and self.cloud_api.folder_id:
                json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
                self.cloud_api.upload_file_to_drive("library_data.json", json_bytes, "application/json")

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def load_library_data(self):
        try:
            self._sync_files_bidirectional()
            self._sync_to_cloud_api()

            if os.path.exists(DEFAULT_DATA_FILE):
                with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self._sync_folder:
                        if "settings" not in data: data["settings"] = {}
                        data["settings"]["syncFolder"] = self._sync_folder
                    if self._cloud_token:
                        if "settings" not in data: data["settings"] = {}
                        data["settings"]["googleCloudToken"] = self._cloud_token
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
