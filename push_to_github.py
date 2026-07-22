import os
import sys
import json
import base64
import urllib.request
import urllib.error

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_files_to_upload():
    ignore_dirs = {'build', 'dist', '__pycache__', 'books', '.git'}
    ignore_files = {'library_data.json', 'make_shortcut.vbs', 'EpubReaderPro.spec'}
    
    upload_list = []
    for root, dirs, files in os.walk(APP_DIR):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file in ignore_files or file.endswith('.exe') or file.endswith('.lnk') or file.endswith('.pyc'):
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, APP_DIR).replace('\\', '/')
            upload_list.append((rel_path, abs_path))
    return upload_list

def upload_project_to_github(repo_owner, repo_name, github_token, branch="main"):
    print(f"Iniciando subida del codigo a GitHub: {repo_owner}/{repo_name}...")
    files = get_files_to_upload()
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "EpubReader-Uploader"
    }

    success_count = 0
    for rel_path, abs_path in files:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{rel_path}"
        
        with open(abs_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        sha = None
        req_check = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req_check) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                sha = data.get("sha")
        except urllib.error.HTTPError as e:
            pass

        payload = {
            "message": f"Subir {rel_path} desde EpubReaderPro",
            "content": content_b64,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha

        req_put = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="PUT"
        )
        
        try:
            with urllib.request.urlopen(req_put) as resp:
                print(f"[OK] Subido con exito: {rel_path}")
                success_count += 1
        except Exception as e:
            print(f"[ERROR] Error al subir {rel_path}: {e}")

    print(f"\nProceso completado: {success_count} de {len(files)} archivos procesados.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python push_to_github.py <usuario_github> <nombre_repositorio> <token_github>")
        sys.exit(1)
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    token = sys.argv[3]
    upload_project_to_github(owner, repo, token)
