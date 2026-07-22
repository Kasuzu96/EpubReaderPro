// Application State
let libraryState = {
  settings: {
    theme: 'theme-paper',
    fontSize: 100,
    layoutMode: 'single',
    activeHighlightColor: '#fce83a',
    syncFolder: null,
    googleCloudToken: null
  },
  books: {}
};

let currentBook = null;
let currentRendition = null;
let currentBookId = null;
let currentBookTitle = "";
let currentSelectedCfi = null;
let currentSelectedText = "";
let currentVisibleCfi = null;
let currentVisibleTextSnippet = "";
let currentFontSize = 100;
let activeColorFilter = 'all';
let currentLayoutMode = 'single';
let currentActiveColor = '#fce83a';

// DOM Elements
const btnOpenFile = document.getElementById('btn-open-file');
const btnWelcomeOpen = document.getElementById('btn-welcome-open');
const btnBackLibrary = document.getElementById('btn-back-library');
const brandLogo = document.getElementById('brand-logo');
const btnGithubUpdate = document.getElementById('btn-github-update');

const btnToggleToc = document.getElementById('btn-toggle-toc');
const btnCloseToc = document.getElementById('btn-close-toc');
const btnToggleNotes = document.getElementById('btn-toggle-notes');
const btnCloseNotes = document.getElementById('btn-close-notes');
const btnExportNotes = document.getElementById('btn-export-notes');
const btnToggleLayout = document.getElementById('btn-toggle-layout');
const btnSaveBookmark = document.getElementById('btn-save-bookmark');
const bookmarkLabelText = document.getElementById('bookmark-label-text');
const headerHighlighterTools = document.getElementById('header-highlighter-tools');

const btnOpenSyncModal = document.getElementById('btn-open-sync-modal');
const btnCloseSyncModal = document.getElementById('btn-close-sync-modal');
const btnDoneSync = document.getElementById('btn-done-sync');
const btnChooseSyncFolder = document.getElementById('btn-choose-sync-folder');
const syncModal = document.getElementById('sync-modal');
const syncFolderPath = document.getElementById('sync-folder-path');
const syncBtnLabel = document.getElementById('sync-btn-label');

const btnOpenAccountChooser = document.getElementById('btn-open-account-chooser');
const btnConnectDriveToken = document.getElementById('btn-connect-drive-token');
const inputDriveToken = document.getElementById('input-drive-token');

const globalLoadingOverlay = document.getElementById('global-loading-overlay');
const loadingTitle = document.getElementById('loading-title');
const loadingDesc = document.getElementById('loading-desc');
const globalLoadingBar = document.getElementById('global-loading-bar');

const btnFontInc = document.getElementById('btn-font-inc');
const btnFontDec = document.getElementById('btn-font-dec');
const fontControls = document.getElementById('font-controls');

const libraryScreen = document.getElementById('library-screen');
const libraryGrid = document.getElementById('library-grid');
const readerContainer = document.getElementById('reader-container');
const readerFrameCenter = document.getElementById('reader-frame-center');

const tocSidebar = document.getElementById('toc-sidebar');
const notesSidebar = document.getElementById('notes-sidebar');
const tocContainer = document.getElementById('toc-container');
const notesListContainer = document.getElementById('notes-list-container');
const notesBadge = document.getElementById('notes-badge');
const bookTitleDisplay = document.querySelector('#book-title-display .current-book-name');
const pageLocationText = document.getElementById('page-location-text');
const progressBarFill = document.getElementById('progress-bar-fill');
const progressPercent = document.getElementById('progress-percent');
const fontSizeVal = document.getElementById('font-size-val');

const btnPrevPage = document.getElementById('btn-prev-page');
const btnNextPage = document.getElementById('btn-next-page');

const highlightToolbar = document.getElementById('highlight-toolbar');
const exportModal = document.getElementById('export-modal');
const btnCloseExportModal = document.getElementById('btn-close-export-modal');
const btnCopyClipboard = document.getElementById('btn-copy-clipboard');
const btnSaveExportFile = document.getElementById('btn-save-export-file');
const exportPreviewText = document.getElementById('export-preview-text');

function showGlobalLoading(title = "☁️ Sincronizando Biblioteca", desc = "Cargando tus libros y comentarios...", pct = 40) {
  if (loadingTitle) loadingTitle.textContent = title;
  if (loadingDesc) loadingDesc.textContent = desc;
  if (globalLoadingBar) globalLoadingBar.style.width = pct + '%';
  if (globalLoadingOverlay) globalLoadingOverlay.style.display = 'flex';
}

function hideGlobalLoading() {
  if (globalLoadingOverlay) globalLoadingOverlay.style.display = 'none';
}

// Initialize PyWebview Connection
window.addEventListener('pywebviewready', () => {
  initAppWithSync();
});

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (window.pywebview && window.pywebview.api) {
      initAppWithSync();
    }
  }, 300);
});

async function initAppWithSync() {
  showGlobalLoading("⏳ Auto-Actualizador al Inicio", "Buscando tus libros, marcadores y comentarios en Google Drive...", 50);
  try {
    await loadLibraryData();
    if (globalLoadingBar) globalLoadingBar.style.width = '100%';
  } finally {
    setTimeout(hideGlobalLoading, 600);
  }
}

// Handler for 1-Click Update from GitHub
if (btnGithubUpdate) {
  btnGithubUpdate.addEventListener('click', async () => {
    if (!confirm("¿Deseas descargar e instalar la versión más reciente de EpubReaderPro directamente desde GitHub?")) return;

    showGlobalLoading("🔄 Actualizando Aplicativo", "Descargando la última versión del código desde GitHub...", 60);
    try {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.check_and_update_from_github();
        if (res.success) {
          if (globalLoadingBar) globalLoadingBar.style.width = '100%';
          alert(res.message);
          await window.pywebview.api.restart_application();
        } else {
          alert(res.error || "No se pudo actualizar desde GitHub.");
        }
      }
    } catch (err) {
      alert("Error durante la actualización: " + err);
    } finally {
      hideGlobalLoading();
    }
  });
}

async function loadLibraryData() {
  try {
    if (window.pywebview && window.pywebview.api) {
      const data = await window.pywebview.api.load_library_data();
      if (data) {
        if (data.books) libraryState.books = data.books;
        if (data.settings) {
          libraryState.settings = Object.assign({}, libraryState.settings, data.settings);
        }
      }
    }
  } catch (err) {
    console.error("Error al cargar la biblioteca:", err);
  }

  restoreUserSettings();
  showLibraryScreen();
}

function restoreUserSettings() {
  const settings = libraryState.settings || {};

  if (settings.theme) {
    document.body.className = settings.theme;
    document.querySelectorAll('.theme-btn').forEach(btn => {
      if (btn.getAttribute('data-theme') === settings.theme) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  if (settings.fontSize) {
    currentFontSize = settings.fontSize;
    fontSizeVal.textContent = currentFontSize + '%';
  }

  if (settings.layoutMode) {
    currentLayoutMode = settings.layoutMode;
    const label = document.getElementById('layout-label-text');
    if (label) {
      label.textContent = (currentLayoutMode === 'single') ? '1 Página' : '2 Páginas';
    }
    if (currentLayoutMode === 'single') {
      readerFrameCenter.classList.remove('double-page-mode');
      readerFrameCenter.classList.add('single-page-mode');
    } else {
      readerFrameCenter.classList.remove('single-page-mode');
      readerFrameCenter.classList.add('double-page-mode');
    }
  }

  if (settings.googleCloudToken) {
    if (inputDriveToken) inputDriveToken.value = settings.googleCloudToken;
    updateSyncDisplay("Google Drive Conectado ✓");
  } else if (settings.syncFolder) {
    updateSyncDisplay(settings.syncFolder);
  } else {
    updateSyncDisplay(null);
  }
}

function updateSyncDisplay(statusText) {
  if (statusText) {
    syncBtnLabel.textContent = "Drive Activo ✓";
    syncFolderPath.textContent = "✓ Sincronizado con Google Drive: " + statusText;
    syncFolderPath.style.color = "var(--accent-primary)";
  } else {
    syncBtnLabel.textContent = "Sincronizar Drive";
    syncFolderPath.textContent = "No configurado (Guardando localmente en AppData)";
    syncFolderPath.style.color = "var(--text-muted)";
  }
}

async function saveLibraryData() {
  try {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.save_library_data(JSON.stringify(libraryState));
    }
  } catch (err) {
    console.error("Error al guardar biblioteca:", err);
  }
}

btnOpenSyncModal.addEventListener('click', () => {
  syncModal.style.display = 'flex';
});

btnCloseSyncModal.addEventListener('click', () => syncModal.style.display = 'none');
btnDoneSync.addEventListener('click', () => syncModal.style.display = 'none');

if (btnOpenAccountChooser) {
  btnOpenAccountChooser.addEventListener('click', async () => {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_google_account_chooser();
    }
  });
}

if (btnConnectDriveToken) {
  btnConnectDriveToken.addEventListener('click', async () => {
    const tokenStr = inputDriveToken.value.trim();
    if (!tokenStr) {
      alert("Por favor pega primero el Access Token de Google.");
      return;
    }

    if (window.pywebview && window.pywebview.api) {
      showGlobalLoading("⚡ Conectando Google Drive", "Descargando libros y comentarios desde tu nube...", 60);
      try {
        const res = await window.pywebview.api.connect_google_cloud_token(tokenStr);
        if (res.success) {
          libraryState.settings.googleCloudToken = tokenStr;
          updateSyncDisplay("Google Drive Conectado ✓");
          alert(`¡Conexión Exitosa con Google Drive!\nSe ha localizado tu carpeta 'EpubReaderData' existente y descargado tus libros y notas.`);
          await loadLibraryData();
          syncModal.style.display = 'none';
        } else {
          alert(res.error || "No se pudo conectar con este Token.");
        }
      } finally {
        hideGlobalLoading();
      }
    }
  });
}

btnChooseSyncFolder.addEventListener('click', async () => {
  if (window.pywebview && window.pywebview.api) {
    const res = await window.pywebview.api.select_sync_folder_dialog();
    if (res.success) {
      libraryState.settings.syncFolder = res.sync_folder;
      saveLibraryData();
      updateSyncDisplay(res.sync_folder);
      alert(`¡Carpeta de sincronización establecida!\nUbicación: ${res.sync_folder}`);
      await loadLibraryData();
    }
  }
});

// Import File Handler
async function triggerImportFile() {
  try {
    let res = null;
    if (window.pywebview && window.pywebview.api) {
      res = await window.pywebview.api.select_and_import_epub();
    }
    if (res && res.file_path) {
      loadEpubFromPath(res.file_path, res.cover_b64);
    }
  } catch (err) {
    alert("Error al importar archivo: " + err);
  }
}

btnOpenFile.addEventListener('click', triggerImportFile);
if (btnWelcomeOpen) btnWelcomeOpen.addEventListener('click', triggerImportFile);

function showLibraryScreen() {
  if (currentBook) {
    try { currentBook.destroy(); } catch(e) {}
    currentBook = null;
    currentRendition = null;
    document.getElementById('viewer').innerHTML = '';
  }

  currentBookId = null;
  bookTitleDisplay.textContent = "Mi Biblioteca";

  // Mostrar únicamente botones de la Biblioteca
  btnOpenFile.style.display = 'inline-flex';
  if (btnGithubUpdate) btnGithubUpdate.style.display = 'inline-flex';
  if (btnOpenSyncModal) btnOpenSyncModal.style.display = 'inline-flex';

  // Ocultar herramientas de lectura
  btnBackLibrary.style.display = 'none';
  btnToggleToc.style.display = 'none';
  btnToggleNotes.style.display = 'none';
  btnExportNotes.style.display = 'none';
  btnToggleLayout.style.display = 'none';
  if (btnSaveBookmark) btnSaveBookmark.style.display = 'none';
  fontControls.style.display = 'flex';
  if (headerHighlighterTools) headerHighlighterTools.style.display = 'none';

  tocSidebar.classList.add('collapsed');
  notesSidebar.classList.add('collapsed');

  readerContainer.style.display = 'none';
  libraryScreen.style.display = 'block';

  renderLibraryGrid();
}

btnBackLibrary.addEventListener('click', showLibraryScreen);
brandLogo.addEventListener('click', showLibraryScreen);

function renderLibraryGrid() {
  libraryGrid.innerHTML = '';

  const addCard = document.createElement('div');
  addCard.className = 'book-card add-book-card';
  addCard.innerHTML = `
    <div class="add-icon">+</div>
    <div class="add-text">Importar Nuevo Libro (.epub)</div>
  `;
  addCard.addEventListener('click', triggerImportFile);
  libraryGrid.appendChild(addCard);

  const books = Object.entries(libraryState.books || {});

  books.forEach(([id, b]) => {
    const card = document.createElement('div');
    card.className = 'book-card';
    
    const pct = b.progressPct || 0;
    const highlightCount = (b.highlights || []).length;
    const initial = b.title ? b.title.charAt(0).toUpperCase() : '📖';

    let coverHtml = '';
    if (b.cover) {
      coverHtml = `<img src="${b.cover}" class="book-cover-img" alt="Portada de ${escapeHtml(b.title)}">`;
    } else {
      coverHtml = `
        <div class="book-cover-fallback">
          <div class="fallback-initial">${initial}</div>
          <div class="fallback-title">${escapeHtml(b.title)}</div>
        </div>
      `;
    }

    card.innerHTML = `
      <button class="btn-delete-book" data-id="${id}" title="Eliminar libro">&times;</button>
      <div class="book-cover-wrapper">
        ${coverHtml}
        <div class="book-card-pct-badge">${pct}% leído</div>
      </div>

      <div class="book-card-info">
        <div class="book-card-title">${escapeHtml(b.title)}</div>
        <div class="book-card-notes-count">📝 ${highlightCount} notas</div>
        <div class="book-progress-bar-bg">
          <div class="book-progress-bar-fill" style="width: ${pct}%;"></div>
        </div>
      </div>
    `;

    card.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-delete-book')) return;
      loadEpubFromPath(b.path, b.cover);
    });

    card.querySelector('.btn-delete-book').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (confirm(`¿Estás seguro de eliminar "${b.title}" de tu biblioteca?`)) {
        if (window.pywebview && window.pywebview.api) {
          await window.pywebview.api.delete_book_from_library(id, b.path);
        }
        delete libraryState.books[id];
        saveLibraryData();
        renderLibraryGrid();
      }
    });

    libraryGrid.appendChild(card);
  });
}

async function loadEpubFromPath(filePath, existingCoverB64 = null) {
  try {
    showGlobalLoading("📖 Abriendo Libro", "Cargando contenido y marcadores...", 60);

    pageLocationText.textContent = "Abriendo libro y cargando portada...";
    
    let res = await window.pywebview.api.read_epub_base64(filePath);
    if (res.error) {
      hideGlobalLoading();
      alert("No se pudo abrir el libro: " + res.error);
      return;
    }

    const binaryString = atob(res.data);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    currentBookId = btoa(unescape(encodeURIComponent(res.file_name))).replace(/=/g, '');
    currentBookTitle = res.file_name.replace('.epub', '');
    bookTitleDisplay.textContent = currentBookTitle;

    const coverB64 = existingCoverB64 || res.cover_b64 || null;

    if (!libraryState.books[currentBookId]) {
      libraryState.books[currentBookId] = {
        title: currentBookTitle,
        path: res.file_path,
        cover: coverB64,
        cfi: null,
        progressPct: 0,
        highlights: []
      };
    } else if (coverB64 && !libraryState.books[currentBookId].cover) {
      libraryState.books[currentBookId].cover = coverB64;
    }

    if (currentBook) {
      currentBook.destroy();
      document.getElementById('viewer').innerHTML = '';
    }

    currentBook = ePub(bytes.buffer);
    
    if (!libraryState.books[currentBookId].cover) {
      currentBook.loaded.cover.then(coverUrl => {
        if (coverUrl) {
          currentBook.archive.createUrl(coverUrl).then(url => {
            fetch(url).then(r => r.blob()).then(blob => {
              const reader = new FileReader();
              reader.onloadend = () => {
                libraryState.books[currentBookId].cover = reader.result;
                saveLibraryData();
              };
              reader.readAsDataURL(blob);
            });
          });
        }
      });
    }

    const spreadMode = (currentLayoutMode === 'single') ? 'none' : 'always';

    currentRendition = currentBook.renderTo("viewer", {
      width: "100%",
      height: "100%",
      spread: spreadMode,
      flow: "paginated"
    });

    applyCurrentThemeToRendition();
    if (currentFontSize !== 100) {
      currentRendition.themes.fontSize(currentFontSize + '%');
    }

    const savedCfi = libraryState.books[currentBookId].cfi;
    if (savedCfi) {
      currentRendition.display(savedCfi);
    } else {
      currentRendition.display();
    }

    libraryScreen.style.display = 'none';
    readerContainer.style.display = 'flex';

    // Ocultar botones de biblioteca al estar en el modo de lectura
    btnOpenFile.style.display = 'none';
    if (btnGithubUpdate) btnGithubUpdate.style.display = 'none';
    if (btnOpenSyncModal) btnOpenSyncModal.style.display = 'none';

    // Mostrar botones propios de la lectura
    btnBackLibrary.style.display = 'inline-flex';
    btnToggleToc.style.display = 'inline-flex';
    btnToggleNotes.style.display = 'inline-flex';
    btnExportNotes.style.display = 'inline-flex';
    btnToggleLayout.style.display = 'inline-flex';
    if (btnSaveBookmark) btnSaveBookmark.style.display = 'inline-flex';
    fontControls.style.display = 'flex';
    if (headerHighlighterTools) headerHighlighterTools.style.display = 'flex';

    currentBook.ready.then(() => {
      return currentBook.locations.generate(1000);
    }).then(() => {
      updateProgressDisplay();
    });

    currentBook.loaded.navigation.then(nav => {
      renderToc(nav.toc);
    });

    setupRenditionEvents();
    renderNotesList();

  } catch (err) {
    alert("Ocurrió un error al procesar el libro EPUB: " + err);
  } finally {
    hideGlobalLoading();
  }
}

/**
 * Inspecciona el DOM del libro dentro del Iframe para hallar el párrafo superior exactamente visible
 */
function getVisibleTopParagraphInfo() {
  if (!currentRendition) return null;
  try {
    const contents = currentRendition.getContents();
    if (!contents || contents.length === 0) return null;

    for (const content of contents) {
      const doc = content.document;
      if (!doc) continue;

      const elements = doc.querySelectorAll('p, h1, h2, h3, h4, section, blockquote');
      for (const el of elements) {
        const rect = el.getBoundingClientRect();
        const txt = el.textContent ? el.textContent.trim().replace(/\s+/g, ' ') : '';
        if (rect.top >= -30 && rect.bottom > 20 && txt.length > 15) {
          const nodeCfi = content.cfiFromNode(el);
          return {
            cfi: nodeCfi || currentVisibleCfi,
            textSnippet: txt.substring(0, 50)
          };
        }
      }
    }
  } catch (e) {
    console.log("Notice inspecting visible paragraph:", e);
  }
  return null;
}

function setupRenditionEvents() {
  if (!currentRendition) return;

  currentRendition.on("started", () => {
    applySavedHighlightsToViewer();
  });

  currentRendition.on("relocated", location => {
    if (location && location.start) {
      const cfi = location.start.cfi;
      currentVisibleCfi = cfi;

      const paraInfo = getVisibleTopParagraphInfo();
      if (paraInfo) {
        currentVisibleCfi = paraInfo.cfi;
        currentVisibleTextSnippet = paraInfo.textSnippet;
      }

      const bookData = libraryState.books[currentBookId];
      if (bookData) {
        bookData.cfi = currentVisibleCfi;
        if (currentVisibleTextSnippet) {
          bookData.anchorText = currentVisibleTextSnippet;
        }

        if (currentBook.locations && currentBook.locations.length() > 0) {
          const pct = Math.round((currentBook.locations.percentageFromCfi(currentVisibleCfi) || 0) * 100);
          bookData.progressPct = pct;
        }

        saveLibraryData();
      }

      updateProgressDisplay(location);
    }
  });

  currentRendition.on("selected", (cfiRange, contents) => {
    currentSelectedCfi = cfiRange;
    currentBook.getRange(cfiRange).then(range => {
      currentSelectedText = range.toString().trim();
      if (currentSelectedText.length > 0) {
        highlightToolbar.style.display = 'flex';
      }
    });
  });

  currentRendition.on("click", () => {
    highlightToolbar.style.display = 'none';
  });
}

if (btnSaveBookmark) {
  btnSaveBookmark.addEventListener('click', async () => {
    if (!currentBookId) return;

    const paraInfo = getVisibleTopParagraphInfo();
    const finalCfi = paraInfo ? paraInfo.cfi : currentVisibleCfi;
    const finalSnippet = paraInfo ? paraInfo.textSnippet : currentVisibleTextSnippet;

    if (!finalCfi) return;

    const bookData = libraryState.books[currentBookId];
    if (bookData) {
      bookData.cfi = finalCfi;
      if (finalSnippet) {
        bookData.anchorText = finalSnippet;
      }
      await saveLibraryData();

      if (bookmarkLabelText) bookmarkLabelText.textContent = "✓ Punto Exacto Guardado";
      btnSaveBookmark.style.backgroundColor = "#10b981";
      btnSaveBookmark.style.color = "white";

      setTimeout(() => {
        if (bookmarkLabelText) bookmarkLabelText.textContent = "Guardar Punto Exacto";
        btnSaveBookmark.style.backgroundColor = "";
        btnSaveBookmark.style.color = "";
      }, 2000);
    }
  });
}

function applySavedHighlightsToViewer() {
  if (!currentRendition || !currentBookId) return;
  const bookData = libraryState.books[currentBookId];
  if (!bookData || !bookData.highlights) return;

  bookData.highlights.forEach(h => {
    try {
      currentRendition.annotations.highlight(h.cfi, {}, () => {
        notesSidebar.classList.remove('collapsed');
      }, 'hl-class', { fill: h.color, 'fill-opacity': '0.35' });
    } catch (e) {}
  });
}

function updateProgressDisplay(location) {
  if (!currentRendition || !currentBook) return;
  
  let pctVal = 0;
  if (location && location.start && currentBook.locations) {
    const percentage = currentBook.locations.percentageFromCfi(currentVisibleCfi || location.start.cfi);
    pctVal = Math.round((percentage || 0) * 100);
  } else if (currentBookId && libraryState.books[currentBookId]) {
    pctVal = libraryState.books[currentBookId].progressPct || 0;
  }

  progressBarFill.style.width = pctVal + '%';
  progressPercent.textContent = pctVal + '%';
  
  if (location && location.start) {
    const pageNum = location.start.displayed.page || (location.start.index + 1);
    let snippetLabel = currentVisibleTextSnippet ? ` | 📍 Párrafo: "${currentVisibleTextSnippet}..."` : '';
    pageLocationText.textContent = `Progreso: ${pctVal}% ${snippetLabel} | Sec. ${pageNum}`;
  }
}

btnPrevPage.addEventListener('click', () => {
  if (currentRendition) currentRendition.prev();
});

btnNextPage.addEventListener('click', () => {
  if (currentRendition) currentRendition.next();
});

document.addEventListener('keydown', (e) => {
  if (currentRendition && readerContainer.style.display !== 'none') {
    if (e.key === 'ArrowLeft') currentRendition.prev();
    if (e.key === 'ArrowRight') currentRendition.next();
  }
});

btnFontInc.addEventListener('click', () => {
  if (currentFontSize < 180) {
    currentFontSize += 10;
    fontSizeVal.textContent = currentFontSize + '%';
    if (currentRendition) currentRendition.themes.fontSize(currentFontSize + '%');
    
    libraryState.settings.fontSize = currentFontSize;
    saveLibraryData();
  }
});

btnFontDec.addEventListener('click', () => {
  if (currentFontSize > 70) {
    currentFontSize -= 10;
    fontSizeVal.textContent = currentFontSize + '%';
    if (currentRendition) currentRendition.themes.fontSize(currentFontSize + '%');
    
    libraryState.settings.fontSize = currentFontSize;
    saveLibraryData();
  }
});

btnToggleLayout.addEventListener('click', () => {
  const label = document.getElementById('layout-label-text');
  if (currentLayoutMode === 'single') {
    currentLayoutMode = 'double';
    label.textContent = '2 Páginas';
    readerFrameCenter.classList.remove('single-page-mode');
    readerFrameCenter.classList.add('double-page-mode');
  } else {
    currentLayoutMode = 'single';
    label.textContent = '1 Página';
    readerFrameCenter.classList.remove('double-page-mode');
    readerFrameCenter.classList.add('single-page-mode');
  }

  libraryState.settings.layoutMode = currentLayoutMode;
  saveLibraryData();

  if (currentRendition) {
    const savedCfi = libraryState.books[currentBookId].cfi;
    const spreadMode = (currentLayoutMode === 'single') ? 'none' : 'always';
    
    currentRendition.clear();
    currentRendition.destroy();
    document.getElementById('viewer').innerHTML = '';

    currentRendition = currentBook.renderTo("viewer", {
      width: "100%",
      height: "100%",
      spread: spreadMode,
      flow: "paginated"
    });

    applyCurrentThemeToRendition();
    if (currentFontSize !== 100) {
      currentRendition.themes.fontSize(currentFontSize + '%');
    }
    setupRenditionEvents();

    if (savedCfi) currentRendition.display(savedCfi);
    else currentRendition.display();
  }
});

document.querySelectorAll('.theme-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    const theme = btn.getAttribute('data-theme');
    document.body.className = theme;

    libraryState.settings.theme = theme;
    saveLibraryData();

    applyCurrentThemeToRendition();
  });
});

function applyCurrentThemeToRendition() {
  if (!currentRendition) return;

  const currentTheme = document.body.className;
  let bg = '#fdfbf7', fg = '#2c251e';

  if (currentTheme === 'theme-white') { bg = '#ffffff'; fg = '#0f172a'; }
  if (currentTheme === 'theme-sepia') { bg = '#fbf0d9'; fg = '#2c2217'; }
  if (currentTheme === 'theme-dark')  { bg = '#161822'; fg = '#e2e8f0'; }

  currentRendition.themes.register('activeTheme', {
    'body': { 'background': bg + ' !important', 'color': fg + ' !important' },
    'p': { 'color': fg + ' !important', 'line-height': '1.7 !important' },
    'h1, h2, h3, h4, h5, h6': { 'color': fg + ' !important' }
  });
  currentRendition.themes.select('activeTheme');
}

function renderToc(tocItems) {
  tocContainer.innerHTML = '';
  if (!tocItems || tocItems.length === 0) {
    tocContainer.innerHTML = '<p class="empty-msg">No hay tabla de contenidos</p>';
    return;
  }

  tocItems.forEach(item => {
    const el = document.createElement('div');
    el.className = 'toc-item';
    el.textContent = item.label ? item.label.trim() : 'Capítulo';
    el.addEventListener('click', () => {
      if (currentRendition) currentRendition.display(item.href);
      tocSidebar.classList.add('collapsed');
    });
    tocContainer.appendChild(el);
  });
}

btnToggleToc.addEventListener('click', () => tocSidebar.classList.toggle('collapsed'));
btnCloseToc.addEventListener('click', () => tocSidebar.classList.add('collapsed'));

document.querySelectorAll('.color-dot').forEach(dot => {
  dot.addEventListener('click', () => {
    const color = dot.getAttribute('data-color');
    currentActiveColor = color;
    libraryState.settings.activeHighlightColor = color;
    saveLibraryData();

    if (currentSelectedCfi && currentSelectedText) {
      createHighlight(color);
    }
  });
});

document.getElementById('btn-add-note-action').addEventListener('click', () => {
  createHighlight(currentActiveColor || '#fce83a');
});

function createHighlight(color) {
  if (!currentRendition || !currentSelectedCfi || !currentSelectedText) return;

  const bookData = libraryState.books[currentBookId];
  const newHighlight = {
    id: 'hl_' + Date.now(),
    cfi: currentSelectedCfi,
    text: currentSelectedText,
    color: color,
    comment: '',
    date: new Date().toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' })
  };

  bookData.highlights.unshift(newHighlight);
  saveLibraryData();

  try {
    currentRendition.annotations.highlight(currentSelectedCfi, {}, () => {
      notesSidebar.classList.remove('collapsed');
    }, 'hl-class', { fill: color, 'fill-opacity': '0.35' });
  } catch(e) {}

  highlightToolbar.style.display = 'none';
  notesSidebar.classList.remove('collapsed');
  renderNotesList();

  currentSelectedCfi = null;
  currentSelectedText = "";
}

function renderNotesList() {
  notesListContainer.innerHTML = '';
  if (!currentBookId || !libraryState.books[currentBookId]) {
    notesBadge.textContent = '0';
    notesListContainer.innerHTML = '<p class="empty-msg">No hay notas registradas.</p>';
    return;
  }

  const highlights = libraryState.books[currentBookId].highlights || [];
  const filtered = activeColorFilter === 'all' 
    ? highlights 
    : highlights.filter(h => h.color === activeColorFilter);

  notesBadge.textContent = highlights.length;

  if (filtered.length === 0) {
    notesListContainer.innerHTML = '<p class="empty-msg">No se encontraron subrayados con este filtro.</p>';
    return;
  }

  filtered.forEach(h => {
    const card = document.createElement('div');
    card.className = 'note-card';
    card.style.borderLeftColor = h.color;

    card.innerHTML = `
      <div class="note-quote" title="Haz clic para saltar a esta frase en el libro">"${escapeHtml(h.text)}"</div>
      <div class="note-meta">
        <span>📅 ${h.date}</span>
      </div>
      <textarea class="note-comment-box" placeholder="Escribe un comentario personal aquí...">${escapeHtml(h.comment || '')}</textarea>
      <div class="note-actions">
        <button class="btn-save-note" data-id="${h.id}">💾 Guardar Comentario</button>
        <button class="btn-delete-note" data-id="${h.id}">Eliminar</button>
      </div>
    `;

    card.querySelector('.note-quote').addEventListener('click', () => {
      if (currentRendition) currentRendition.display(h.cfi);
    });

    const textarea = card.querySelector('.note-comment-box');
    const saveBtn = card.querySelector('.btn-save-note');

    textarea.addEventListener('input', (e) => {
      h.comment = e.target.value;
      saveBtn.textContent = "💾 Guardar *";
      saveBtn.style.backgroundColor = "var(--accent-primary)";
    });

    saveBtn.addEventListener('click', async () => {
      h.comment = textarea.value;
      await saveLibraryData();
      saveBtn.textContent = "✓ Guardado";
      saveBtn.style.backgroundColor = "#10b981";
      setTimeout(() => {
        saveBtn.textContent = "💾 Guardar Comentario";
        saveBtn.style.backgroundColor = "var(--accent-primary)";
      }, 1800);
    });

    card.querySelector('.btn-delete-note').addEventListener('click', () => {
      deleteHighlight(h.id, h.cfi);
    });

    notesListContainer.appendChild(card);
  });
}

function deleteHighlight(id, cfi) {
  if (!currentBookId) return;
  const bookData = libraryState.books[currentBookId];
  bookData.highlights = bookData.highlights.filter(h => h.id !== id);
  saveLibraryData();

  if (currentRendition) {
    try { currentRendition.annotations.remove(cfi, 'highlight'); } catch(e) {}
  }
  renderNotesList();
}

document.querySelectorAll('.filter-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    activeColorFilter = pill.getAttribute('data-filter');
    renderNotesList();
  });
});

btnToggleNotes.addEventListener('click', () => notesSidebar.classList.toggle('collapsed'));
btnCloseNotes.addEventListener('click', () => notesSidebar.classList.add('collapsed'));

btnExportNotes.addEventListener('click', openExportModal);
btnCloseExportModal.addEventListener('click', () => exportModal.style.display = 'none');

function openExportModal() {
  if (!currentBookId || !libraryState.books[currentBookId]) {
    alert("Abre un libro primero para exportar sus notas.");
    return;
  }
  updateExportPreview();
  exportModal.style.display = 'flex';
}

function generateExportText(format) {
  const bookData = libraryState.books[currentBookId];
  const highlights = bookData.highlights || [];

  if (format === 'md') {
    let md = `# Notas y Frases Subrayadas\n\n`;
    md += `**Libro:** ${currentBookTitle}\n`;
    md += `**Total de Frases:** ${highlights.length}\n`;
    md += `**Fecha de Exportación:** ${new Date().toLocaleDateString('es-ES')}\n\n`;
    md += `---\n\n`;

    highlights.forEach((h, index) => {
      md += `### ${index + 1}. Frase Subrayada (${h.date})\n\n`;
      md += `> "${h.text}"\n\n`;
      if (h.comment && h.comment.trim().length > 0) {
        md += `**Comentario Personal:**\n${h.comment.trim()}\n\n`;
      }
      md += `---\n\n`;
    });
    return md;
  } else {
    let txt = `==================================================\n`;
    txt += `NOTAS Y FRASES SUBRAYADAS\n`;
    txt += `Libro: ${currentBookTitle}\n`;
    txt += `Total: ${highlights.length} subrayados\n`;
    txt += `==================================================\n\n`;

    highlights.forEach((h, index) => {
      txt += `[${index + 1}] (${h.date})\n`;
      txt += `FRASE: "${h.text}"\n`;
      if (h.comment && h.comment.trim().length > 0) {
        txt += `COMENTARIO: ${h.comment.trim()}\n`;
      }
      txt += `--------------------------------------------------\n\n`;
    });
    return txt;
  }
}

function updateExportPreview() {
  const selectedFormat = document.querySelector('input[name="export-format"]:checked').value;
  exportPreviewText.value = generateExportText(selectedFormat);
}

document.querySelectorAll('input[name="export-format"]').forEach(radio => {
  radio.addEventListener('change', updateExportPreview);
});

btnCopyClipboard.addEventListener('click', () => {
  const text = exportPreviewText.value;
  navigator.clipboard.writeText(text).then(() => {
    alert("¡Notas copiadas al portapapeles con éxito!");
  }).catch(err => alert("Error al copiar: " + err));
});

btnSaveExportFile.addEventListener('click', async () => {
  const selectedFormat = document.querySelector('input[name="export-format"]:checked').value;
  const content = exportPreviewText.value;
  const defaultName = `${currentBookTitle.replace(/[^a-z0-9]/gi, '_')}_notas.${selectedFormat}`;

  if (window.pywebview && window.pywebview.api) {
    const res = await window.pywebview.api.export_notes_file(defaultName, content, selectedFormat);
    if (res.success) {
      alert(`¡Archivo guardado con éxito en:\n${res.path}`);
      exportModal.style.display = 'none';
    }
  }
});

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
