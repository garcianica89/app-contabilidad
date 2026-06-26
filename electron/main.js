const { app, BrowserWindow, Menu, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow = null
let backendProcess = null

const BACKEND_PORT = 8000
const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('--dev')

function startBackend() {
  const backendDir = isDev
    ? path.join(__dirname, '..', 'backend')
    : path.join(process.resourcesPath, 'backend')

  const pythonCmd = isDev ? 'uvicorn' : path.join(backendDir, 'app.exe')
  const args = isDev
    ? ['app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)]
    : ['--host', '127.0.0.1', '--port', String(BACKEND_PORT)]

  backendProcess = spawn(pythonCmd, args, {
    cwd: backendDir,
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env },
  })

  backendProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data}`)
  })

  backendProcess.stderr.on('data', (data) => {
    console.error(`[backend] ${data}`)
  })

  backendProcess.on('error', (err) => {
    console.error('Failed to start backend:', err)
  })

  backendProcess.on('exit', (code) => {
    console.log(`Backend exited with code ${code}`)
  })
}

function waitForBackend(retries = 30) {
  return new Promise((resolve, reject) => {
    const check = (attempt) => {
      if (attempt >= retries) {
        reject(new Error('Backend did not start in time'))
        return
      }
      const http = require('http')
      const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/health`, (res) => {
        if (res.statusCode === 200) resolve()
        else setTimeout(() => check(attempt + 1), 1000)
      })
      req.on('error', () => setTimeout(() => check(attempt + 1), 1000))
      req.setTimeout(2000, () => { req.destroy(); setTimeout(() => check(attempt + 1), 1000) })
    }
    check(0)
  })
}

async function createWindow() {
  const { screen } = require('electron')
  const primaryDisplay = screen.getPrimaryDisplay()
  const { width, height } = primaryDisplay.workAreaSize

  mainWindow = new BrowserWindow({
    width: Math.min(1280, width),
    height: Math.min(800, height),
    minWidth: 1024,
    minHeight: 600,
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false,
  })

  if (isDev) {
    mainWindow.loadURL(`http://localhost:5173`)
    mainWindow.webContents.openDevTools()
  } else {
    const splash = new BrowserWindow({ width: 400, height: 300, frame: false, transparent: true })
    splash.loadURL(`data:text/html,<html><body style="display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#0f172a;color:#e2e8f0;font-family:sans-serif"><h2>Cargando App Contabilidad...</h2></body></html>`)
    splash.show()

    startBackend()
    try {
      await waitForBackend()
      splash.close()
      mainWindow.loadURL(`http://127.0.0.1:${BACKEND_PORT}`)
    } catch (err) {
      splash.close()
      dialog.showErrorBox('Error', 'No se pudo iniciar el servidor backend. Por favor reinicie la aplicacion.')
      app.quit()
    }
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  const menuTemplate = [
    {
      label: 'App Contabilidad',
      submenu: [
        { role: 'reload', label: 'Recargar' },
        { role: 'forceReload', label: 'Recargar forzado' },
        { type: 'separator' },
        { role: 'toggleDevTools', label: 'Herramientas de desarrollo' },
        { type: 'separator' },
        { role: 'quit', label: 'Salir' },
      ],
    },
    {
      label: 'Ver',
      submenu: [
        { role: 'zoomIn', label: 'Acercar' },
        { role: 'zoomOut', label: 'Alejar' },
        { role: 'resetZoom', label: 'Restablecer zoom' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Pantalla completa' },
      ],
    },
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate))
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
})

app.on('activate', () => {
  if (mainWindow === null) createWindow()
})
