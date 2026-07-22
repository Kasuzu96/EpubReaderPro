# EpubReaderPro 📚

**EpubReaderPro** es una aplicación de escritorio nativa para Windows desarrollada en **Python** y **Webview** (powered by Microsoft Edge WebView2) que ofrece una experiencia moderna, fluida y premium para leer libros `.epub`, destacar frases en múltiples colores, tomar notas laterales y sincronizar tu avance entre múltiples computadoras usando tu propia cuenta de **Google Drive**.

---

## ✨ Características Principales

- **📖 Vista de Lectura Tipo Hoja de Libro**: Tema cálido de papel por defecto para evitar la fatiga visual. Modos adicionales: *Blanco Puro*, *Sepia* y *Oscuro*.
- **📖 Modo de Vista de 1 o 2 Páginas**: Visualización limpia de 1 sola página centrada (estilo Kindle/iBooks) o doble página.
- **🔖 Marcador Automático de Página (Auto-Bookmark)**: Guarda la ubicación exacta (CFI) y reanuda la lectura en la misma sección al reabrir el libro.
- **📚 Biblioteca Interactiva de Portadas**: Muestra las portadas completas en alta resolución de tus libros importados con su porcentaje exacto de lectura (`% leído`).
- **🖍️ Subrayado Multicolor e Historial de Notas**: Selecciona cualquier frase dentro del libro para subrayar en 4 colores (*Amarillo, Verde, Azul, Rosa*) y agregar comentarios personales en un panel lateral interactivo.
- **📤 Exportación de Citas**: Exporta tus subrayados y comentarios a archivos **Markdown (`.md`)**, **Texto Plano (`.txt`)** o al portapapeles.
- **☁️ Sincronización con Google Drive**: Sincroniza automáticamente tus libros, portadas, marcadores y notas entre tus computadoras sin necesidad de servidores adicionales.
- **💾 Almacenamiento Persistente Nivel Sistema**: Todo tu progreso y biblioteca se guardan de forma persistente en `AppData`, por lo que nunca perderás tus datos al reiniciar.

---

## 🚀 Requisitos e Instalación

### Opción A: Ejecutar el Ejecutable Nativo de Windows (`.exe`)
1. Descarga la carpeta compilada desde `dist/EpubReaderPro/`.
2. Haz doble clic en `EpubReaderPro.exe` o ejecuta `Lector EPUB Pro.bat`.

### Opción B: Ejecutar desde Código Fuente (Python)
1. Instala Python 3.11+:
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```bash
   python main.py
   ```

---

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python 3.11, `pywebview`, `zipfile`, `json`, `base64`, `shutil`.
- **Frontend**: HTML5, CSS3 (Vanilla CSS, Glassmorphism, Micro-animaciones), JavaScript.
- **Motor EPUB**: `epub.js` + `JSZip` (Librerías embebidas offline).
- **Empaquetado**: PyInstaller (`.exe` autónomo para Windows).

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
