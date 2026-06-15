/**
 * 系统级桌面宠物 - Electron 主进程
 *
 * 核心能力：
 * - 透明无边框窗口，置顶但不拦截鼠标（点击穿透）
 * - 宠物在桌面自由行走，可爬窗口边缘、坐任务栏
 * - 点击宠物弹出对话气泡
 * - 拖拽移动宠物
 */

const { app, BrowserWindow, screen, Tray, Menu, ipcMain, globalShortcut } = require('electron');
const path = require('path');

let mainWindow = null;
let tray = null;
let petState = {
  x: 0, y: 0,
  direction: 1, // 1=右, -1=左
  state: 'idle', // idle/walk/sleep/happy/worry
  emotion: 'neutral',
  frameIndex: 0,
  frameTimer: 0,
  walkTimer: 0,
  walkDuration: 0,
  targetX: 0,
  dragging: false,
  dragOffsetX: 0,
  dragOffsetY: 0,
  chatOpen: false,
  messages: [],
  lastInteraction: Date.now(),
};

// 宠物尺寸（像素风 64x64）
const PET_WIDTH = 64;
const PET_HEIGHT = 64;
const BUBBLE_WIDTH = 280;
const BUBBLE_HEIGHT = 120;

function createWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;
  const taskbarHeight = screenHeight - primaryDisplay.workAreaSize.height + (screenHeight - primaryDisplay.workAreaSize.height > 50 ? 0 : 40);

  // 初始化位置：屏幕底部中间
  petState.x = Math.floor(screenWidth / 2 - PET_WIDTH / 2);
  petState.y = screenHeight - PET_HEIGHT - taskbarHeight;
  petState.targetX = petState.x;

  mainWindow = new BrowserWindow({
    width: PET_WIDTH,
    height: PET_HEIGHT,
    x: petState.x,
    y: petState.y,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    hasShadow: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // 关键：让窗口不拦截鼠标事件（点击穿透），但宠物本体区域可点击
  mainWindow.setIgnoreMouseEvents(true, { forward: true });

  mainWindow.loadFile('src/index.html');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 启动行为循环
  startBehaviorLoop(screenWidth, screenHeight, taskbarHeight);
}

function startBehaviorLoop(screenWidth, screenHeight, taskbarHeight) {
  const TICK = 50; // 50ms 一帧 = 20fps
  const WALK_SPEED = 2;

  setInterval(() => {
    if (!mainWindow || petState.dragging) return;

    petState.frameTimer++;
    petState.walkTimer++;

    // 状态机
    switch (petState.state) {
      case 'idle':
        // 随机决定下一步行为
        if (petState.walkTimer > 100 + Math.random() * 200) {
          const rand = Math.random();
          if (rand < 0.4) {
            petState.state = 'walk';
            petState.direction = Math.random() > 0.5 ? 1 : -1;
            petState.walkDuration = 50 + Math.random() * 100;
            petState.walkTimer = 0;
            petState.targetX = petState.x + petState.direction * petState.walkDuration * WALK_SPEED;
            // 边界限制
            petState.targetX = Math.max(0, Math.min(screenWidth - PET_WIDTH, petState.targetX));
          } else if (rand < 0.6) {
            petState.state = 'sleep';
            petState.walkTimer = 0;
          } else if (rand < 0.75) {
            petState.state = 'happy';
            petState.walkTimer = 0;
          }
        }
        break;

      case 'walk':
        const dx = petState.targetX - petState.x;
        if (Math.abs(dx) < WALK_SPEED) {
          petState.x = petState.targetX;
          petState.state = 'idle';
          petState.walkTimer = 0;
        } else {
          petState.x += Math.sign(dx) * WALK_SPEED;
          petState.direction = Math.sign(dx);
        }
        // 动画帧
        if (petState.frameTimer % 8 === 0) {
          petState.frameIndex = (petState.frameIndex + 1) % 4;
        }
        break;

      case 'sleep':
        if (petState.frameTimer % 30 === 0) {
          petState.frameIndex = (petState.frameIndex + 1) % 2;
        }
        if (petState.walkTimer > 200 + Math.random() * 200) {
          petState.state = 'idle';
          petState.walkTimer = 0;
          petState.frameIndex = 0;
        }
        break;

      case 'happy':
        if (petState.frameTimer % 10 === 0) {
          petState.frameIndex = (petState.frameIndex + 1) % 3;
        }
        if (petState.walkTimer > 60) {
          petState.state = 'idle';
          petState.walkTimer = 0;
          petState.frameIndex = 0;
        }
        break;

      case 'worry':
        if (petState.frameTimer % 20 === 0) {
          petState.frameIndex = (petState.frameIndex + 1) % 2;
        }
        if (petState.walkTimer > 120) {
          petState.state = 'idle';
          petState.walkTimer = 0;
          petState.frameIndex = 0;
        }
        break;
    }

    // 更新窗口位置
    if (mainWindow) {
      mainWindow.setBounds({
        x: Math.round(petState.x),
        y: Math.round(petState.y),
        width: PET_WIDTH,
        height: PET_HEIGHT,
      });

      // 通知渲染进程更新动画
      mainWindow.webContents.send('pet-update', {
        state: petState.state,
        direction: petState.direction,
        frameIndex: petState.frameIndex,
        emotion: petState.emotion,
      });
    }
  }, TICK);
}

// IPC：渲染进程 -> 主进程
ipcMain.on('pet-click', () => {
  petState.lastInteraction = Date.now();
  petState.state = 'happy';
  petState.walkTimer = 0;
  petState.frameTimer = 0;

  // 扩大窗口以显示对话气泡
  if (mainWindow) {
    const bounds = mainWindow.getBounds();
    mainWindow.setBounds({
      x: bounds.x - Math.floor((BUBBLE_WIDTH - PET_WIDTH) / 2),
      y: bounds.y - BUBBLE_HEIGHT,
      width: BUBBLE_WIDTH,
      height: BUBBLE_HEIGHT + PET_HEIGHT,
    });
    mainWindow.setIgnoreMouseEvents(false); // 气泡区域需要接收鼠标
    mainWindow.webContents.send('show-bubble', true);
    petState.chatOpen = true;
  }
});

ipcMain.on('pet-drag-start', (event, offsetX, offsetY) => {
  petState.dragging = true;
  petState.dragOffsetX = offsetX;
  petState.dragOffsetY = offsetY;
  if (mainWindow) {
    mainWindow.setIgnoreMouseEvents(false);
  }
});

ipcMain.on('pet-drag-move', (event, screenX, screenY) => {
  if (petState.dragging && mainWindow) {
    petState.x = screenX - petState.dragOffsetX;
    petState.y = screenY - petState.dragOffsetY;
    mainWindow.setBounds({
      x: Math.round(petState.x),
      y: Math.round(petState.y),
      width: PET_WIDTH,
      height: PET_HEIGHT,
    });
  }
});

ipcMain.on('pet-drag-end', () => {
  petState.dragging = false;
  if (mainWindow) {
    mainWindow.setIgnoreMouseEvents(true, { forward: true });
  }
});

ipcMain.on('close-bubble', () => {
  if (mainWindow && petState.chatOpen) {
    mainWindow.setBounds({
      x: Math.round(petState.x),
      y: Math.round(petState.y),
      width: PET_WIDTH,
      height: PET_HEIGHT,
    });
    mainWindow.setIgnoreMouseEvents(true, { forward: true });
    mainWindow.webContents.send('show-bubble', false);
    petState.chatOpen = false;
  }
});

ipcMain.on('send-message', async (event, message) => {
  // 调用后端 API
  try {
    const http = require('http');
    const postData = JSON.stringify({
      student_id: 'demo-001',
      message: message,
    });

    const options = {
      hostname: '127.0.0.1',
      port: 8000,
      path: '/api/v1/chat',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': Buffer.byteLength(postData),
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          mainWindow.webContents.send('chat-reply', result.reply || '...');
          petState.emotion = 'happy';
          petState.state = 'happy';
          petState.walkTimer = 0;
        } catch {
          mainWindow.webContents.send('chat-reply', '嗯嗯，我在听呢~');
        }
      });
    });

    req.on('error', () => {
      mainWindow.webContents.send('chat-reply', '我现在有点累，等会儿再聊吧~ (后端未启动)');
    });

    req.write(postData);
    req.end();
  } catch {
    mainWindow.webContents.send('chat-reply', '嗯嗯，我在听呢~');
  }
});

// 系统托盘
function createTray() {
  // 用 Canvas 生成一个简单的托盘图标
  const { nativeImage } = require('electron');
  const icon = nativeImage.createFromBuffer(
    Buffer.from(createPetIconBuffer()),
    { width: 16, height: 16 }
  );

  tray = new Tray(icon);
  const contextMenu = Menu.buildFromTemplate([
    { label: '🐱 宠物状态: ' + petState.state, enabled: false },
    { type: 'separator' },
    { label: '让宠物开心', click: () => { petState.state = 'happy'; petState.walkTimer = 0; } },
    { label: '让宠物睡觉', click: () => { petState.state = 'sleep'; petState.walkTimer = 0; } },
    { label: '让宠物散步', click: () => { petState.state = 'walk'; petState.walkTimer = 0; } },
    { type: 'separator' },
    { label: '退出', click: () => app.quit() },
  ]);
  tray.setToolTip('AI 学习宠物');
  tray.setContextMenu(contextMenu);
}

function createPetIconBuffer() {
  // 16x16 像素的简单猫脸图标 (RGBA)
  const buf = Buffer.alloc(16 * 16 * 4);
  // 简单的橙色猫脸
  for (let y = 0; y < 16; y++) {
    for (let x = 0; x < 16; x++) {
      const i = (y * 16 + x) * 4;
      // 耳朵
      if ((y < 4 && (x < 5 || x > 10)) ||
        // 脸
        (y >= 3 && y < 13 && x >= 3 && x < 13)) {
        buf[i] = 255; buf[i + 1] = 165; buf[i + 2] = 0; buf[i + 3] = 255;
      }
      // 眼睛
      else if ((y === 7 || y === 8) && (x === 6 || x === 9)) {
        buf[i] = 0; buf[i + 1] = 0; buf[i + 2] = 0; buf[i + 3] = 255;
      }
      // 鼻子
      else if (y === 10 && x === 7) {
        buf[i] = 255; buf[i + 1] = 100; buf[i + 2] = 100; buf[i + 3] = 255;
      }
      else {
        buf[i + 3] = 0; // 透明
      }
    }
  }
  return buf;
}

app.whenReady().then(() => {
  createWindow();
  createTray();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
