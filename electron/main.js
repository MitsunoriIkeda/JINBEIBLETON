const { app, BrowserWindow, systemPreferences, session, ipcMain, protocol } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// Register file scheme as privileged BEFORE app is ready to unlock secure browser APIs (like getUserMedia) in production
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'file',
    privileges: {
      standard: true,
      secure: true,
      bypassCSP: true,
      allowServiceWorkers: true,
      supportFetchAPI: true,
      corsEnabled: true,
      stream: true
    }
  }
]);

app.commandLine.appendSwitch('unsafely-treat-insecure-origin-as-secure', 'http://localhost:5173');
app.commandLine.appendSwitch('use-fake-ui-for-media-stream');
app.commandLine.appendSwitch('enable-speech-input');

let mainWindow;
let pythonProcess;
let nodeBridgeProcess;

const ASPECT_RATIO = 1280 / 800; // 16:10

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
const fs = require('fs');

// Helper to dynamically find the development workspace by traversing upwards to locate the directory containing 'server/venv'
function getWorkspace() {
  const checkDir = (startPath) => {
    if (!startPath) return null;
    let current = path.resolve(startPath);
    while (true) {
      const venvPath = process.platform === 'win32'
        ? path.join(current, 'server/venv/Scripts/python.exe')
        : path.join(current, 'server/venv/bin/python');
      if (fs.existsSync(venvPath)) {
        return current;
      }
      const parent = path.dirname(current);
      if (parent === current) break;
      current = parent;
    }
    return null;
  };
  
  // 1. Check upward traversal from app path / execution path
  let found = checkDir(__dirname) || checkDir(path.dirname(process.execPath));
  if (found) return found;

  // 2. Hardcoded original path (backward compatibility for standard setup)
  const originalPath = "/Volumes/ableton Project & 写真等/for ableton AI controller";
  const originalVenv = process.platform === 'win32'
    ? path.join(originalPath, 'server/venv/Scripts/python.exe')
    : path.join(originalPath, 'server/venv/bin/python');
  if (fs.existsSync(originalVenv)) {
    return originalPath;
  }

  // 3. Scan macOS /Volumes for any workspace folder containing server/venv (portable external SSD support)
  if (process.platform === 'darwin') {
    try {
      if (fs.existsSync('/Volumes')) {
        const volumes = fs.readdirSync('/Volumes');
        for (const vol of volumes) {
          if (vol.startsWith('.')) continue;
          
          // Check if it's inside a folder named 'for ableton AI controller' on that volume
          const candidate1 = path.join('/Volumes', vol, 'for ableton AI controller');
          if (fs.existsSync(path.join(candidate1, 'server/venv/bin/python'))) {
            return candidate1;
          }

          // Check if the root of the volume contains the project directly
          const candidate2 = path.join('/Volumes', vol);
          if (fs.existsSync(path.join(candidate2, 'server/venv/bin/python'))) {
            return candidate2;
          }
        }
      }
    } catch (err) {
      console.error("Error scanning /Volumes:", err);
    }
  }
  
  return null;
}

const workspacePath = getWorkspace();
const useDevWorkspace = !!workspacePath;
const fallbackWorkspace = workspacePath || path.resolve(__dirname, '..');
const baseDir = useDevWorkspace ? fallbackWorkspace : path.join(__dirname, '..');

function createWindow() {

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "JINBEIBLETON",
    icon: path.join(__dirname, '../electron_assets/icon.png'),
    titleBarStyle: 'hiddenInset', // Keeps traffic lights (red/yellow/green) visible
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false,
      allowRunningInsecureContent: true,
      autoplayPolicy: 'no-user-gesture-required'
    }
  });

  // Intercept window.open calls (like download links) to open in the system default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http:') || url.startsWith('https:')) {
      const { shell } = require('electron');
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  // Only open DevTools in development mode to keep production clean
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // IPC: Toggle fullscreen from renderer
  ipcMain.on('toggle-fullscreen', () => {
    if (mainWindow) {
      mainWindow.setFullScreen(!mainWindow.isFullScreen());
    }
  });

  // IPC: Support native drag & drop of generated audio/MIDI files
  ipcMain.on('ondragstart', (event, filePath) => {
    const os = require('os');
    let absolutePath = '';

    let cleanPath = filePath;
    // Strip HTTP/HTTPS protocols and hostnames to extract the pure relative pathname
    if (typeof cleanPath === 'string' && (cleanPath.startsWith('http://') || cleanPath.startsWith('https://'))) {
      try {
        const { URL } = require('url');
        const urlObj = new URL(cleanPath);
        cleanPath = urlObj.pathname;
      } catch (urlErr) {
        console.error("❌ [Electron Drag] Failed to parse URL, falling back to regex replacement:", urlErr);
        cleanPath = cleanPath.replace(/^https?:\/\/[^\/]+/, '');
      }
    }

    if (path.isAbsolute(cleanPath) && fs.existsSync(cleanPath)) {
      absolutePath = cleanPath;
    } else {
      const relativePath = cleanPath.replace(/^\/+/, '');
      const filename = path.basename(relativePath);
      if (useDevWorkspace) {
        absolutePath = path.join(fallbackWorkspace, 'client/public/samples', filename);
      } else {
        const homeDir = os.homedir();
        absolutePath = path.join(homeDir, '.jinbeibleton', 'samples', filename);
      }
    }

    console.log("🎛 [Electron Drag] Native drag start for:", absolutePath);

    if (fs.existsSync(absolutePath)) {
      let dragIcon = '';
      
      // Determine appropriate icon based on file type (MIDI or Audio)
      const isMidi = absolutePath.endsWith('.mid') || absolutePath.endsWith('.midi');
      const iconFilename = isMidi ? 'midi-key.png' : 'cassette.png';
      
      const potentialIconPath = path.join(baseDir, 'client/public/assets', iconFilename);
      if (fs.existsSync(potentialIconPath)) {
        dragIcon = potentialIconPath;
      } else {
        // Fallback to dog.png if specific assets are not found
        const fallbackIcon = path.join(baseDir, 'client/public/assets/dog.png');
        if (fs.existsSync(fallbackIcon)) {
          dragIcon = fallbackIcon;
        }
      }

      console.log("🎛 [Electron Drag] Starting drag with icon:", dragIcon);

      const dragConfig = {
        file: absolutePath
      };

      // Only attach icon if it is verified to exist on disk to prevent process crashes
      if (dragIcon) {
        dragConfig.icon = dragIcon;
      }

      event.sender.startDrag(dragConfig);
    } else {
      console.error("❌ [Electron Drag] File not found for dragging:", absolutePath);
    }
  });

  // Aspect ratio lock (16:10) — skips during fullscreen
  let resizeTimeout;
  mainWindow.on('resize', () => {
    if (mainWindow.isFullScreen()) return;
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      if (!mainWindow || mainWindow.isDestroyed() || mainWindow.isFullScreen()) return;
      const [width, height] = mainWindow.getSize();
      const targetHeight = Math.round(width / ASPECT_RATIO);
      if (Math.abs(height - targetHeight) > 3) {
        mainWindow.setSize(width, targetHeight);
      }
    }, 150);
  });

  // In development, load from Vite
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173').catch(() => {
      console.log("Vite not ready yet, retrying...");
    });
  } else {
    mainWindow.loadFile(path.join(__dirname, '../client/dist/index.html'));
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function ensureRemoteScriptInstalled(bridgePath) {
  try {
    const os = require('os');
    if (process.platform !== 'darwin') return; // macOS only auto-installation

    const userRemoteScriptsDir = path.join(os.homedir(), "Music/Ableton/User Library/Remote Scripts");
    const targetDir = path.join(userRemoteScriptsDir, "AbletonJS");

    // Resolve source midi-script folder
    let midiScriptSrc = "";
    // Candidate 1: Workspace root midi-script (development)
    const devSrc = path.join(fallbackWorkspace, 'midi-script');
    // Candidate 2: Bundled node_modules ableton-js midi-script (packaged)
    const prodSrc = path.join(bridgePath, 'node_modules/ableton-js/midi-script');

    if (fs.existsSync(devSrc)) {
      midiScriptSrc = devSrc;
    } else if (fs.existsSync(prodSrc)) {
      midiScriptSrc = prodSrc;
    }

    if (!midiScriptSrc) {
      console.warn("⚠️ [Electron-Setup] midi-script source directory not found. Skipping auto-installation.");
      return;
    }

    console.log(`📦 [Electron-Setup] Auto-installing AbletonJS Remote Script from ${midiScriptSrc} to ${targetDir}`);
    
    if (fs.existsSync(targetDir)) {
      fs.rmSync(targetDir, { recursive: true, force: true });
    }
    
    fs.mkdirSync(userRemoteScriptsDir, { recursive: true });
    fs.cpSync(midiScriptSrc, targetDir, { recursive: true });
    
    console.log("✅ [Electron-Setup] AbletonJS Remote Script auto-installed successfully!");
  } catch (err) {
    console.error("❌ [Electron-Setup] Failed to auto-install AbletonJS Remote Script:", err);
  }
}

function startBackends() {
  try {
    const logDir = useDevWorkspace 
      ? path.join(fallbackWorkspace, "dist-app") 
      : path.join(app.getPath("userData"), "logs");
    if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });

    const bridgeLog = fs.createWriteStream(path.join(logDir, "bridge.log"), { flags: 'w' });
    const pythonLog = fs.createWriteStream(path.join(logDir, "python.log"), { flags: 'w' });

    bridgeLog.write(`[Electron] Starting backends. Workspace priority: ${useDevWorkspace ? 'Source Workspace' : 'App Resources'}\n`);
    pythonLog.write(`[Electron] Starting backends. Workspace priority: ${useDevWorkspace ? 'Source Workspace' : 'App Resources'}\n`);

    let bridgePath;
    let pythonPath;
    let serverPath;

    if (useDevWorkspace) {
      console.log("💡 [Electron] Development workspace detected. Booting directly from local source paths!");
      bridgeLog.write("💡 [Electron] Development workspace detected. Booting directly from local source paths!\n");
      pythonLog.write("💡 [Electron] Development workspace detected. Booting directly from local source paths!\n");

      bridgePath = path.join(fallbackWorkspace, 'server/node_bridge');
      pythonPath = process.platform === 'win32'
        ? path.join(fallbackWorkspace, 'server/venv/Scripts/python.exe')
        : path.join(fallbackWorkspace, 'server/venv/bin/python');
      serverPath = path.join(fallbackWorkspace, 'server');
    } else {
      // PACKAGED MODE: Use resources inside app.asar.unpacked for native binaries
      const appBaseDir = path.join(__dirname, '..');
      // asarUnpack places files at app.asar.unpacked/ alongside app.asar
      const unpackedDir = appBaseDir.replace('app.asar', 'app.asar.unpacked');
      bridgePath = path.join(unpackedDir, 'server/node_bridge');
      // In packaged mode, we use the PyInstaller binary directly (no venv)
      pythonPath = null; // Will be resolved below
      serverPath = path.join(unpackedDir, 'server');
    }

    // Call our auto-installer helper
    ensureRemoteScriptInstalled(bridgePath);

    // Resolve node path for GUI launches (which lack standard terminal PATH)
    let nodePath = 'node';
    if (process.platform === 'darwin') {
      if (fs.existsSync('/usr/local/bin/node')) {
        nodePath = '/usr/local/bin/node';
      } else if (fs.existsSync('/opt/homebrew/bin/node')) {
        nodePath = '/opt/homebrew/bin/node';
      }
    }

    // --- START NODE BRIDGE ---
    // In packaged mode, use Electron's own node if system node isn't available
    let bridgeStarted = false;
    if (fs.existsSync(path.join(bridgePath, 'index.js'))) {
      let bridgeNodePath = nodePath;
      if (!useDevWorkspace && !fs.existsSync(nodePath)) {
        // Use Electron's bundled node via process.execPath with --no-sandbox
        bridgeNodePath = process.execPath;
      }

      console.log("🚀 Starting Node Bridge at:", bridgePath, "using", bridgeNodePath);
      bridgeLog.write(`🚀 Starting Node Bridge at: ${bridgePath} using ${bridgeNodePath}\n`);

      if (bridgeNodePath === process.execPath) {
        // Running via Electron binary: need ELECTRON_RUN_AS_NODE=1
        nodeBridgeProcess = spawn(bridgeNodePath, [path.join(bridgePath, 'index.js')], {
          cwd: bridgePath,
          env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' }
        });
      } else {
        nodeBridgeProcess = spawn(bridgeNodePath, ['index.js'], { cwd: bridgePath });
      }

      nodeBridgeProcess.on('error', (err) => {
        console.error("❌ Node Bridge Spawn Error:", err);
        bridgeLog.write(`❌ Node Bridge Spawn Error: ${err.message}\n`);
      });
      
      nodeBridgeProcess.stdout.pipe(bridgeLog);
      nodeBridgeProcess.stderr.pipe(bridgeLog);
      bridgeStarted = true;
    } else {
      console.warn("⚠️ [Electron] Node bridge not found at:", bridgePath);
      bridgeLog.write(`⚠️ Node bridge not found at: ${bridgePath}\n`);
    }

    // --- START PYTHON SERVER ---
    // Determine samples directory for the server
    const os = require('os');
    const samplesDir = useDevWorkspace
      ? path.join(fallbackWorkspace, 'client/public/samples')
      : path.join(os.homedir(), '.jinbeibleton', 'samples');

    // Ensure samples directory exists for packaged mode
    if (!useDevWorkspace && !fs.existsSync(samplesDir)) {
      fs.mkdirSync(samplesDir, { recursive: true });
    }

    if (useDevWorkspace && pythonPath && fs.existsSync(pythonPath)) {
      // Mode 1: Development workspace with Python venv
      console.log("🚀 Starting Python Server (DEV MODE):", pythonPath);
      pythonLog.write(`🚀 Starting Python Server (DEV): ${pythonPath}\n`);

      pythonProcess = spawn(pythonPath, ['main.py'], {
        cwd: serverPath,
        env: { ...process.env, JINBEIBLETON_SAMPLES_DIR: samplesDir }
      });
      
      pythonProcess.on('error', (err) => {
        console.error("❌ Python Server Spawn Error:", err);
        pythonLog.write(`❌ Python Server Spawn Error: ${err.message}\n`);
      });
      
      pythonProcess.stdout.pipe(pythonLog);
      pythonProcess.stderr.pipe(pythonLog);
    } else {
      // Mode 2: Packaged — use the bundled PyInstaller binary
      const bundledBinary = path.join(serverPath, 'dist', 'jinbeibleton-server', 'jinbeibleton-server');
      
      if (fs.existsSync(bundledBinary)) {
        console.log("📦 [Electron] Using bundled Python server binary:", bundledBinary);
        pythonLog.write(`📦 Using bundled binary: ${bundledBinary}\n`);
        
        pythonProcess = spawn(bundledBinary, [], {
          cwd: path.dirname(bundledBinary),
          env: { ...process.env, JINBEIBLETON_SAMPLES_DIR: samplesDir }
        });
        
        pythonProcess.on('error', (err) => {
          console.error("❌ Bundled Server Spawn Error:", err);
          pythonLog.write(`❌ Bundled Server Spawn Error: ${err.message}\n`);
        });
        
        pythonProcess.stdout.pipe(pythonLog);
        pythonProcess.stderr.pipe(pythonLog);
      } else {
        const errorMsg = `❌ CRITICAL: No Python server found. Checked:\n  bundled: ${bundledBinary}\n  This app requires the PyInstaller-built server binary.\n`;
        console.error(errorMsg);
        pythonLog.write(errorMsg);
      }
    }
  } catch (e) {
    console.error("❌ Unexpected Error in startBackends:", e);
  }
}

app.on('ready', async () => {
  // Request microphone access on macOS
  if (process.platform === 'darwin') {
    const micAccess = await systemPreferences.askForMediaAccess('microphone');
    console.log('🎤 Microphone access:', micAccess ? 'GRANTED' : 'DENIED');
  }

  // Allow media + MIDI permissions automatically in renderer
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    if (permission === 'media' || permission === 'midi' || permission === 'midi-sysex') {
      callback(true);
    } else {
      callback(false);
    }
  });

  session.defaultSession.setPermissionCheckHandler((webContents, permission, origin) => {
    if (permission === 'media' || permission === 'midi' || permission === 'midi-sysex') return true;
    return false;
  });

  startBackends();
  createWindow();
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('quit', () => {
  if (pythonProcess) pythonProcess.kill();
  if (nodeBridgeProcess) nodeBridgeProcess.kill();
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});
