/**
 * RiddlerChat - Electron Main Process (Client Only)
 * Connects to a remote RiddlerChat backend server.
 *
 * 1337_TECH DBA, Austin Texas - 2026
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

const BACKEND_HOST = process.env.RIDDLER_SERVER || '127.0.0.1';
const BACKEND_PORT = process.env.RIDDLER_PORT || '7576';

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    frame: false,
    transparent: false,
    backgroundColor: '#0a0f0a',
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, '..', 'chatclient', 'TheRiddlerChatSystem',
      'Views', 'images', 'DarkKnight_logo.png'),
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Pass backend connection info to renderer
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.executeJavaScript(
      `window.__RIDDLER_SERVER__ = "${BACKEND_HOST}:${BACKEND_PORT}";`
    );
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();
});

app.on('window-all-closed', () => {
  app.quit();
});

// IPC handlers for window controls
ipcMain.on('window-minimize', () => mainWindow?.minimize());
ipcMain.on('window-maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
});
ipcMain.on('window-close', () => mainWindow?.close());
