import os
import sys
import json
import time
import base64
import shutil
import zipfile
import threading
import subprocess
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

GITHUB_REPO_OWNER = "Kasuzu96"
GITHUB_REPO_NAME = "EpubReaderPro"

def merge_library_data(local_data, remote_data):
    """
    Algoritmo a Prueba de Fallas para la Unión Multidispositivo.
    Combina las notas por ID único y preserva la posición de lectura más reciente (lastReadTime).
    """
    if not local_data:
        local_data = {"books": {}, "settings": {}}
    if not remote_data:
        return local_data

    local_books = local_data.get("books", {})
    remote_books = remote_data.get("books", {})

    all_bids = set(local_books.keys()).union(set(remote_books.keys()))
    merged_books = {}

    for b_id in all_bids:
        l_b = local_books.get(b_id)
        r_b = remote_books.get(b_id)

        if l_b and not r_b:
            orig_path = l_b.get("path", "")
            f_name = os.path.basename(orig_path) if orig_path else f"{b_id}.epub"
            l_b["path"] = os.path.join(DEFAULT_BOOKS_DIR, f_name)
            merged_books[b_id] = l_b
        elif r_b and not l_b:
            orig_path = r_b.get("path", "")
            f_name = os.path.basename(orig_path) if orig_path else f"{b_id}.epub"
            r_b["path"] = os.path.join(DEFAULT_BOOKS_DIR, f_name)
            merged_books[b_id] = r_b
        else:
            # Presente en ambas computadoras
            l_time = l_b.get("lastReadTime", 0)
            r_time = r_b.get("lastReadTime", 0)

            # Prevalece la posición de lectura del dispositivo más reciente
            if r_time > l_time:
                base_b = dict(r_b)
                other_b = dict(l_b)
            else:
                base_b = dict(l_b)
                other_b = dict(r_b)

            if not base_b.get("cover") and other_b.get("cover"):
                base_b["cover"] = other_b["cover"]

            # Fusión de Notas por ID único para no perder ningún subrayado
            l_highlights = l_b.get("highlights", [])
            r_highlights = r_b.get("highlights", [])

            hl_map = {}
            for h in r_highlights:
                if isinstance(h, dict) and "id" in h:
                    hl_map[h["id"]] = dict(h)

            for h in l_highlights:
                if isinstance(h, dict) and "id" in h:
                    h_id = h["id"]
                    if h_id not in hl_map:
                        hl_map[h_id] = dict(h)
                    else:
                        existing_comment = hl_map[h_id].get("comment", "")
                        new_comment = h.get("comment", "")
                        if len(new_comment.strip()) >= len(existing_comment.strip()):
                            hl_map[h_id] = dict(h)

            base_b["highlights"] = list(hl_map.values())
            
            orig_path = base_b.get("path", "")
            f_name = os.path.basename(orig_path) if orig_path else f"{b_id}.epub"
            base_b["path"] = os.path.join(DEFAULT_BOOKS_DIR, f_name)

            merged_books[b_id] = base_b

    local_data["books"] = merged_books
    return local_data

class GoogleDriveCloudAPI:
    """Cliente directo de la API v3 de Google Drive para sincronización en la nube"""
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.folder_id = None
        self.token_expired = False
        if self.access_token:
            self.ensure_remote_folder()

    def set_token(self, token):
        self.access_token = token.strip() if token else None
        self.token_expired = False
        return self.ensure_remote_folder()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def ensure_remote_folder(self):
        if not self.access_token:
            return None
        
        query = urllib.parse.quote("name='EpubReaderData' and mimeType='application/vnd.google-apps.folder' and trashed=false")
        url = f"https://www.googleapis.com/drive/v3/files?q={query}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                files = data.get("files", [])
                if files:
                    self.folder_id = files[0]["id"]
                    self.token_expired = False
                    return self.folder_id
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.token_expired = True
            print("Notice checking remote drive folder:", e)
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
            with urllib.request.urlopen(req_create, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                self.folder_id = data.get("id")
                self.token_expired = False
                return self.folder_id
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.token_expired = True
        except Exception as e:
            print("Notice creating remote drive folder:", e)
        return None

    def list_files_in_folder(self):
        if not self.access_token or not self.folder_id:
            return []
        
        query = urllib.parse.quote(f"'{self.folder_id}' in parents and trashed=false")
        url = f"https://www.googleapis.com/drive/v3/files?q={query}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                self.token_expired = False
                return data.get("files", [])
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.token_expired = True
        except Exception as e:
            print("Error listing files in drive folder:", e)
        return []

    def upload_file_to_drive(self, file_name, file_bytes, mime_type="application/octet-stream"):
        if not self.access_token or not self.folder_id:
            return False
        
        query = urllib.parse.quote(f"'{self.folder_id}' in parents and name='{file_name}' and trashed=false")
        search_url = f"https://www.googleapis.com/drive/v3/files?q={query}"
        file_id = None
        req = urllib.request.Request(search_url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
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
            with urllib.request.urlopen(req_upload, timeout=15) as resp:
                self.token_expired = False
                return True
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.token_expired = True
        except Exception as e:
            print("Error uploading to Google Drive API:", e)
        return False

    def download_file_from_drive(self, file_name):
        if not self.access_token or not self.folder_id:
            return None
        
        query = urllib.parse.quote(f"'{self.folder_id}' in parents and name='{file_name}' and trashed=false")
        search_url = f"https://www.googleapis.com/drive/v3/files?q={query}"
        file_id = None
        req = urllib.request.Request(search_url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
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
            with urllib.request.urlopen(req_down, timeout=15) as resp:
                self.token_expired = False
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.token_expired = True
        except Exception as e:
            print("Error downloading from Google Drive API:", e)
        return None

def extract_epub_cover_base64(epub_path):
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
            except Exception as e:
                print("Init data store notice:", e)

    def check_and_update_from_github(self):
        try:
            zip_url = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/archive/refs/heads/main.zip"
            temp_zip = os.path.join(USER_APPDATA_DIR, "update_repo.zip")
            extract_dir = os.path.join(USER_APPDATA_DIR, "temp_update")

            req = urllib.request.Request(zip_url, headers={"User-Agent": "EpubReaderPro-Updater"})
            with urllib.request.urlopen(req, timeout=15) as response, open(temp_zip, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            repo_folder_name = f"{GITHUB_REPO_NAME}-main"
            updated_source_dir = os.path.join(extract_dir, repo_folder_name)

            if not os.path.exists(updated_source_dir):
                return {"error": "Estructura del repositorio no reconocida."}

            updated_static_dir = os.path.join(updated_source_dir, "static")
            local_static_dir = os.path.join(APP_DIR, "static")
            if os.path.exists(updated_static_dir):
                if os.path.exists(local_static_dir):
                    shutil.rmtree(local_static_dir, ignore_errors=True)
                shutil.copytree(updated_static_dir, local_static_dir)

            for item_name in ["main.py", "build_exe.py", "README.md"]:
                src_file = os.path.join(updated_source_dir, item_name)
                dst_file = os.path.join(APP_DIR, item_name)
                if os.path.exists(src_file):
                    shutil.copy2(src_file, dst_file)

            return {"success": True, "message": "Aplicativo actualizado exitosamente con 1-Clic desde GitHub."}
        except Exception as e:
            return {"error": f"Fallo al actualizar desde GitHub: {str(e)}"}

    def restart_application(self):
        try:
            python = sys.executable
            subprocess.Popen([python] + sys.argv)
            if self._window:
                self._window.destroy()
            sys.exit()
        except Exception:
            pass

    def open_google_account_chooser(self):
        url = "https://accounts.google.com/AccountChooser?continue=https%3A%2F%2Fdevelopers.google.com%2Foauthplayground%2F%3Fscopes%3Dhttps%253A%252F%252Fwww.googleapis.com%252Fauth%252Fdrive.file"
        webbrowser.open(url)
        return {"success": True}

    def connect_google_cloud_token(self, token_str):
        if not token_str or not token_str.strip():
            return {"error": "Por favor ingresa un token válido."}
        
        folder_id = self.cloud_api.set_token(token_str)
        if folder_id:
            self._cloud_token = token_str.strip()
            downloaded_count = self.pull_all_from_google_drive()
            return {
                "success": True, 
                "folder_id": folder_id,
                "downloaded_books": downloaded_count
            }
        else:
            return {"error": "No se pudo conectar a Google Drive. Verifica que el token copiado esté activo."}

    def pull_all_from_google_drive(self):
        """Descarga e Integración Multidispositivo a Prueba de Fallas (Pull-First)"""
        if not self._cloud_token or not self.cloud_api.folder_id:
            return 0

        remote_bytes = self.cloud_api.download_file_from_drive("library_data.json")
        if remote_bytes:
            try:
                remote_data = json.loads(remote_bytes.decode('utf-8'))
                
                local_data = {"books": {}}
                if os.path.exists(DEFAULT_DATA_FILE):
                    with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                        local_data = json.load(f)

                merged_data = merge_library_data(local_data, remote_data)

                if "settings" not in merged_data:
                    merged_data["settings"] = {}
                merged_data["settings"]["googleCloudToken"] = self._cloud_token
                if self._sync_folder:
                    merged_data["settings"]["syncFolder"] = self._sync_folder

                with open(DEFAULT_DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(merged_data, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print("Error fusionando datos remotos:", e)

        downloaded = 0
        drive_files = self.cloud_api.list_files_in_folder()
        for f_item in drive_files:
            f_name = f_item.get("name", "")
            if f_name.endswith(".epub"):
                local_book_path = os.path.join(DEFAULT_BOOKS_DIR, f_name)
                if not os.path.exists(local_book_path):
                    print(f"Descargando libro desde Google Drive: {f_name}...")
                    epub_bytes = self.cloud_api.download_file_from_drive(f_name)
                    if epub_bytes:
                        with open(local_book_path, "wb") as f_out:
                            f_out.write(epub_bytes)
                        downloaded += 1

        return downloaded

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

        local_data = {"books": {}}
        if os.path.exists(DEFAULT_DATA_FILE):
            try:
                with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
            except Exception: pass

        sync_data = {"books": {}}
        if os.path.exists(sync_data_file):
            try:
                with open(sync_data_file, "r", encoding="utf-8") as f:
                    sync_data = json.load(f)
            except Exception: pass

        merged = merge_library_data(local_data, sync_data)
        with open(DEFAULT_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        with open(sync_data_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

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

            if self._cloud_token and self.cloud_api.folder_id:
                with open(dest_path, "rb") as f:
                    file_bytes = f.read()
                threading.Thread(
                    target=lambda: self.cloud_api.upload_file_to_drive(file_name, file_bytes, "application/epub+zip"),
                    daemon=True
                ).start()

            cover_b64 = extract_epub_cover_base64(dest_path)
            res = self.read_epub_base64(dest_path)
            if cover_b64:
                res["cover_b64"] = cover_b64
            return res
        except Exception as e:
            return {"error": f"Error al importar archivo: {str(e)}"}

    def read_epub_base64(self, file_path):
        try:
            file_name = os.path.basename(file_path)
            actual_path = os.path.join(DEFAULT_BOOKS_DIR, file_name)

            if not os.path.exists(actual_path) and not os.path.exists(file_path):
                if self._cloud_token and self.cloud_api.folder_id:
                    print(f"Descargando archivo desde Google Drive por demanda: {file_name}...")
                    cloud_bytes = self.cloud_api.download_file_from_drive(file_name)
                    if cloud_bytes:
                        with open(actual_path, "wb") as f:
                            f.write(cloud_bytes)

            final_path = actual_path if os.path.exists(actual_path) else file_path

            if not os.path.exists(final_path):
                return {"error": f"El archivo del libro no se encuentra en el equipo ni en Google Drive: {file_name}"}

            with open(final_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            
            cover_b64 = extract_epub_cover_base64(final_path)

            return {
                "success": True,
                "file_name": file_name,
                "file_path": final_path,
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

            # Guardado local instantáneo en JSON
            with open(DEFAULT_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            if self._sync_folder and os.path.exists(self._sync_folder):
                sync_file = os.path.join(self._sync_folder, "library_data.json")
                with open(sync_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            # Sincronización en la nube en hilo en segundo plano (Evita congelamientos UI)
            if self._cloud_token and self.cloud_api.folder_id:
                json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
                def _bg_upload():
                    try:
                        self.cloud_api.upload_file_to_drive("library_data.json", json_bytes, "application/json")
                    except Exception as ex:
                        print("Background upload notice:", ex)
                threading.Thread(target=_bg_upload, daemon=True).start()

            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def load_library_data(self):
        try:
            self._sync_files_bidirectional()
            self.pull_all_from_google_drive()

            if os.path.exists(DEFAULT_DATA_FILE):
                with open(DEFAULT_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if self._sync_folder:
                        if "settings" not in data: data["settings"] = {}
                        data["settings"]["syncFolder"] = self._sync_folder
                    if self._cloud_token:
                        if "settings" not in data: data["settings"] = {}
                        data["settings"]["googleCloudToken"] = self._cloud_token
                    
                    data["token_expired"] = self.cloud_api.token_expired
                    return data
            return {"books": {}, "token_expired": self.cloud_api.token_expired}
        except Exception as e:
            return {"books": {}, "token_expired": self.cloud_api.token_expired}

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

    def on_closing():
        return True

    window.events.closing += on_closing

    webview.start(debug=False)

if __name__ == "__main__":
    main()
