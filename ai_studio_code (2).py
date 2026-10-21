#!/usr/bin/env python3
"""
MAGA AI — Скрипти худкори эҷод ва бастабандии лоиҳа ба ZIP
Иҷро: python3 setup_maga_ai.py
"""

import os
import zipfile
import subprocess

PROJECT_DIR = "maga-ai"
ZIP_NAME = "maga-ai.zip"

FILES = {}

# 1. package.json
FILES["package.json"] = """{
  "name": "maga-ai",
  "version": "1.0.0",
  "description": "MAGA AI — Веб-барномаи мукаммали зеҳни сунъӣ бо забони тоҷикӣ",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "engines": {
    "node": ">=18.0.0"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.4.7",
    "express": "^4.21.2",
    "multer": "^1.4.5-lts.1"
  }
}
"""

# 2. .env.example
FILES[".env.example"] = """PORT=3000
GEMINI_API_KEY=карори_калиди_шумо_аз_aistudio.google.com
ADMIN_SECRET=maga_admin_2026
"""

# 3. .gitignore
FILES[".gitignore"] = """node_modules/
.env
.DS_Store
*.log
"""

# 4. render.yaml
FILES["render.yaml"] = """services:
  - type: web
    name: maga-ai
    env: node
    plan: free
    buildCommand: npm install
    startCommand: node server.js
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: ADMIN_SECRET
        generateValue: true
"""

# 5. README.md
FILES["README.md"] = """# MAGA AI — Веб-барномаи Зеҳни Сунъӣ

Платформаи муосири чати зеҳни сунъӣ бо забони тоҷикӣ, русӣ ва англисӣ.
Бо истифода аз Google Gemini API, таҳлили файлҳо, тавлиди расми ройгон ва мутобиқ ба телефонҳои Android.

## 🚀 Нашри сайт дар Render (Free Tier):
1. Ин ҷузвдон ё файли `maga-ai.zip`-ро кушода, ба GitHub бор кунед.
2. Ба [dashboard.render.com](https://dashboard.render.com) рафта, **New +** -> **Web Service**-ро интихоб кунед.
3. Танзимот:
   - **Environment:** `Node`
   - **Build Command:** `npm install`
   - **Start Command:** `node server.js`
   - **Plan:** `Free`
4. Дар бахши **Environment Variables** калиди `GEMINI_API_KEY`-ро илова намоед.
5. Тугмаи **Deploy Web Service**-ро пахш кунед.
"""

# 6. server.js
FILES["server.js"] = """const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');
const multer = require('multer');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';
const ADMIN_SECRET = process.env.ADMIN_SECRET || 'maga_admin_2026';

const stats = {
  startTime: Date.now(),
  chatRequests: 0,
  fileRequests: 0,
  imageRequests: 0,
  errors: 0
};

app.use(cors());
app.use(express.json({ limit: '25mb' }));
app.use(express.urlencoded({ extended: true, limit: '25mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 20 * 1024 * 1024 }
});

// Ёрирасон барои Gemini API
async function callGemini(contents, systemInstruction, config = {}) {
  if (!GEMINI_API_KEY) {
    throw new Error('NO_API_KEY');
  }

  const model = config.model || 'gemini-1.5-flash';
  const temperature = config.temperature !== undefined ? parseFloat(config.temperature) : 0.7;
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${GEMINI_API_KEY}`;

  const payload = {
    contents: contents,
    generationConfig: {
      temperature: temperature,
      maxOutputTokens: 2048
    }
  };

  if (systemInstruction) {
    payload.systemInstruction = {
      parts: [{ text: systemInstruction }]
    };
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(`GEMINI_API_ERROR: ${message}`);
  }

  const data = await response.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) {
    throw new Error('Модел ҷавоби холӣ баргардонд.');
  }
  return text;
}

// 1. Чат бо AI
app.post('/api/chat', async (req, res) => {
  stats.chatRequests++;
  try {
    const { message, history = [], systemInstruction, model, temperature } = req.body;

    if (!message || typeof message !== 'string') {
      return res.status(400).json({ success: false, error: 'Паём холӣ аст.' });
    }

    const defaultSystem = 'Шумо MAGA AI ҳастед — ёвари ҳушманди касбии зеҳни сунъӣ. Ба саволҳо бо забони адабӣ, равон, дӯстона ва илмии тоҷикӣ посух диҳед. Агар бо русӣ ё англисӣ муроҷиат кунанд, бо ҳамон забон ҷавоб гардонед. Дар фанҳои риёзиёт, физика, химия ва барномасозӣ мисолҳои равшан оред.';

    const contents = [];
    for (const item of history) {
      if (item.role && item.content) {
        contents.push({
          role: item.role === 'assistant' ? 'model' : 'user',
          parts: [{ text: item.content }]
        });
      }
    }

    contents.push({
      role: 'user',
      parts: [{ text: message }]
    });

    const reply = await callGemini(contents, systemInstruction || defaultSystem, { model, temperature });

    res.json({
      success: true,
      reply: reply,
      modelUsed: model || 'gemini-1.5-flash'
    });
  } catch (err) {
    stats.errors++;
    if (err.message === 'NO_API_KEY') {
      return res.status(503).json({
        success: false,
        error: 'Калиди GEMINI_API_KEY дар сервер танзим нашудааст. Лутфан онро дар бахши Environment Variables дар Render ворид кунед.',
        code: 'NO_API_KEY'
      });
    }
    res.status(500).json({ success: false, error: err.message });
  }
});

// 2. Таҳлили файл (Тасвирҳо ва Ҳуҷҷатҳо)
app.post('/api/analyze-file', upload.single('file'), async (req, res) => {
  stats.fileRequests++;
  try {
    const file = req.file;
    const prompt = req.body.prompt || 'Лутфан ин файлро ба таври муфассал ба забони тоҷикӣ таҳлил намоед.';
    const model = req.body.model || 'gemini-1.5-flash';

    if (!file) {
      return res.status(400).json({ success: false, error: 'Ҳеҷ файле бор карда нашудааст.' });
    }

    const mime = file.mimetype;
    const contents = [];

    if (mime.startsWith('image/')) {
      contents.push({
        role: 'user',
        parts: [
          { text: prompt },
          {
            inlineData: {
              mimeType: mime,
              data: file.buffer.toString('base64')
            }
          }
        ]
      });
    } else {
      const textContent = file.buffer.toString('utf-8');
      contents.push({
        role: 'user',
        parts: [
          { text: `[Файл: ${file.originalname}, Навъ: ${mime}]\\\\n[Мундариҷа]:\\\\n${textContent.slice(0, 50000)}\\\\n\\\\n[Супориш]: ${prompt}` }
        ]
      });
    }

    const reply = await callGemini(contents, 'Шумо мутахассиси таҳлили файлҳои MAGA AI ҳастед.', { model });

    res.json({
      success: true,
      reply: reply,
      fileName: file.originalname
    });
  } catch (err) {
    stats.errors++;
    res.status(500).json({ success: false, error: err.message });
  }
});

// 3. Тавлиди ройгони тасвир (Flux)
app.post('/api/generate-image', (req, res) => {
  stats.imageRequests++;
  try {
    const { prompt } = req.body;
    if (!prompt) return res.status(400).json({ success: false, error: 'Тавсифи расм лозим аст.' });

    const encoded = encodeURIComponent(prompt.trim());
    const seed = Math.floor(Math.random() * 1000000);
    const imageUrl = `https://image.pollinations.ai/prompt/${encoded}?width=1024&height=1024&seed=${seed}&nologo=true&model=flux`;

    res.json({ success: true, imageUrl, prompt });
  } catch (err) {
    res.status(500).json({ success: false, error: 'Хато дар тавлиди тасвир.' });
  }
});

// 4. Санҷиши саломатӣ
app.get('/api/health', (req, res) => {
  const uptimeSeconds = Math.floor((Date.now() - stats.startTime) / 1000);
  res.json({
    status: 'ok',
    app: 'MAGA AI',
    uptime: `${uptimeSeconds} сония`,
    geminiConfigured: Boolean(GEMINI_API_KEY)
  });
});

// 5. Омори маъмурӣ
app.post('/api/admin/stats', (req, res) => {
  const secret = req.headers['x-admin-key'] || req.body.adminSecret;
  if (!secret || secret !== ADMIN_SECRET) {
    return res.status(401).json({ success: false, error: 'Рамзи нодуруст.' });
  }

  const uptimeSeconds = Math.floor((Date.now() - stats.startTime) / 1000);
  res.json({
    success: true,
    stats: {
      uptimeSeconds,
      uptimeFormatted: `${Math.floor(uptimeSeconds / 60)} дақиқа`,
      chatRequests: stats.chatRequests,
      fileRequests: stats.fileRequests,
      imageRequests: stats.imageRequests,
      geminiConfigured: Boolean(GEMINI_API_KEY)
    }
  });
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Сервери MAGA AI дар порти ${PORT} фаъол шуд!`);
});
"""

# 7. public/favicon.svg
FILES["public/favicon.svg"] = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4" />
      <stop offset="100%" stop-color="#6366f1" />
    </linearGradient>
  </defs>
  <rect width="100" height="100" rx="24" fill="url(#g)" />
  <path d="M25 70 L25 30 L40 50 L50 36 L60 50 L75 30 L75 70" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" />
</svg>
"""

# 8. public/style.css
FILES["public/style.css"] = """:root {
  --bg-primary: #090d16;
  --bg-secondary: #0f172a;
  --bg-card: #1e293b;
  --border: #334155;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --accent-cyan: #06b6d4;
  --accent-indigo: #6366f1;
  --accent-gradient: linear-gradient(135deg, #06b6d4, #6366f1);
  --bubble-user: #4f46e5;
  --bubble-bot: #1e293b;
  --danger: #ef4444;
}

[data-theme="light"] {
  --bg-primary: #f8fafc;
  --bg-secondary: #ffffff;
  --bg-card: #e2e8f0;
  --border: #cbd5e1;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --accent-cyan: #0284c7;
  --accent-indigo: #4f46e5;
  --bubble-user: #4f46e5;
  --bubble-bot: #ffffff;
  --danger: #dc2626;
}

* { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
body {
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  height: 100vh;
  display: flex;
  overflow: hidden;
  transition: background-color 0.2s, color 0.2s;
}

#app { display: flex; width: 100%; height: 100%; position: relative; }

.sidebar {
  width: 280px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: transform 0.25s ease;
  z-index: 50;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0; left: 0; bottom: 0;
    transform: translateX(-100%);
    box-shadow: 4px 0 20px rgba(0,0,0,0.5);
  }
  .sidebar.open { transform: translateX(0); }
}

.sidebar-backdrop {
  display: none;
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 40;
}
.sidebar-backdrop.active { display: block; }

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--bg-primary);
}

.app-header {
  height: 60px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: opacity 0.2s;
}
.btn-primary { background: var(--accent-gradient); color: #fff; }
.btn-secondary { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border); }
.btn-icon {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-primary);
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.55;
  word-break: break-word;
}
@media (max-width: 640px) { .bubble { max-width: 94%; font-size: 13.5px; } }
.bubble-user { align-self: flex-end; background: var(--bubble-user); color: #fff; border-top-right-radius: 4px; }
.bubble-bot { align-self: flex-start; background: var(--bubble-bot); color: var(--text-primary); border: 1px solid var(--border); border-top-left-radius: 4px; }
.bubble-error { align-self: flex-start; background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }

pre { background: #000; color: #38bdf8; padding: 10px; border-radius: 8px; margin: 8px 0; overflow-x: auto; font-family: monospace; font-size: 12px; }
code { background: rgba(0,0,0,0.25); padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 12px; }

.input-bar {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 8px;
}
.input-box:focus-within { border-color: var(--accent-cyan); }
.input-box textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-family: inherit;
  font-size: 14px;
  resize: none;
  max-height: 120px;
}

.modal {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.65);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
  padding: 16px;
}
.modal.hidden { display: none; }
.modal-box {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 18px;
  width: 100%; max-width: 500px;
  max-height: 85vh;
  overflow-y: auto;
  padding: 20px;
}
"""

# 9. public/index.html
FILES["public/index.html"] = """<!DOCTYPE html>
<html lang="tg">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>MAGA AI — Ёвари Ҳушманди Сунъӣ</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="app">
    <div id="sidebarBackdrop" class="sidebar-backdrop" onclick="toggleSidebar()"></div>

    <aside id="sidebar" class="sidebar">
      <div style="padding: 16px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border);">
        <div style="display: flex; align-items: center; gap: 8px;">
          <img src="/favicon.svg" width="30" height="30" alt="Logo">
          <b style="font-size: 16px; letter-spacing: 0.5px;">MAGA AI</b>
        </div>
        <button class="btn-icon" onclick="toggleSidebar()" style="display: none;" id="sidebarCloseBtn"><i class="fa-solid fa-xmark"></i></button>
      </div>

      <div style="padding: 12px 16px;">
        <button class="btn btn-primary" onclick="newChat()" style="width: 100%;"><i class="fa-solid fa-plus"></i> <span data-i18n="newChat">Чати нав</span></button>
      </div>

      <div style="flex: 1; overflow-y: auto; padding: 0 10px;" id="chatList"></div>

      <div style="padding: 12px 16px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
        <select id="langSelect" onchange="changeLang(this.value)" style="background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border); border-radius: 8px; padding: 4px 6px; font-size: 11px;">
          <option value="tg">🇹🇯 Тоҷикӣ</option>
          <option value="ru">🇷🇺 Русский</option>
          <option value="en">🇬🇧 English</option>
        </select>
        <div style="display: flex; gap: 6px;">
          <button class="btn-icon" onclick="toggleTheme()"><i class="fa-solid fa-moon" id="themeIcon"></i></button>
          <button class="btn-icon" onclick="openModal('settingsModal')"><i class="fa-solid fa-gear"></i></button>
        </div>
      </div>
    </aside>

    <main class="chat-container">
      <header class="app-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <button class="btn-icon" onclick="toggleSidebar()"><i class="fa-solid fa-bars"></i></button>
          <span style="font-weight: 700; font-size: 14px;">MAGA AI <span style="font-size: 10px; color: var(--accent-cyan); background: rgba(6,182,212,0.15); padding: 2px 6px; border-radius: 6px;">Gemini Core</span></span>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary" onclick="openModal('toolsModal')"><i class="fa-solid fa-wand-magic-sparkles"></i> <span data-i18n="tools">Абзорҳо</span></button>
        </div>
      </header>

      <div class="messages" id="messagesBox">
        <div id="welcomeCard" style="margin: auto; max-width: 500px; text-align: center; padding: 20px;">
          <div style="width: 56px; height: 56px; border-radius: 18px; background: var(--accent-gradient); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 14px;">
            <i class="fa-solid fa-brain" style="font-size: 26px; color: #fff;"></i>
          </div>
          <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 6px;" data-i18n="welcomeTitle">Хуш омадед ба MAGA AI!</h2>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 20px;" data-i18n="welcomeDesc">Ёвари зеҳни сунъии шумо бо забони тоҷикӣ. Савол диҳед ё аз кортҳои зерин оғоз кунед:</p>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; text-align: left;">
            <div class="btn btn-secondary" onclick="sendQuickPrompt('Муодилаи квадратӣ 2x^2 + 5x - 3 = 0-ро қадам ба қадам шарҳ деҳ.')" style="font-size: 11px; padding: 10px; height: auto;">📐 Риёзиёт ва физика</div>
            <div class="btn btn-secondary" onclick="sendQuickPrompt('Як функсияи JavaScript барои санҷидани палиндром навис.')" style="font-size: 11px; padding: 10px; height: auto;">💻 Барномасозӣ</div>
            <div class="btn btn-secondary" onclick="sendQuickPrompt('Дар бораи таърихи Исмоили Сомонӣ мақолаи зебо навис.')" style="font-size: 11px; padding: 10px; height: auto;">📚 Шеър ва мақола</div>
            <div class="btn btn-secondary" onclick="sendQuickPrompt('Се идеяи эҷодӣ барои видеои кӯтоҳи TikTok пешниҳод кун.')" style="font-size: 11px; padding: 10px; height: auto;">🎬 Идеяҳои TikTok</div>
          </div>
        </div>
      </div>

      <div class="input-bar">
        <div id="fileBadge" style="display: none; align-items: center; gap: 6px; font-size: 11px; padding: 4px 10px; background: var(--bg-card); border-radius: 8px; border: 1px solid var(--border); width: fit-content;">
          <i class="fa-solid fa-file"></i> <span id="fileName"></span> <i class="fa-solid fa-xmark" style="cursor: pointer; color: var(--danger);" onclick="removeFile()"></i>
        </div>

        <form class="input-box" onsubmit="handleSubmit(event)">
          <input type="file" id="fileInput" style="display: none;" onchange="handleFileSelect(event)">
          <button type="button" class="btn-icon" onclick="document.getElementById('fileInput').click()"><i class="fa-solid fa-paperclip"></i></button>
          <textarea id="chatInput" rows="1" placeholder="Саволи худро нависед..." onkeydown="handleKeyDown(event)"></textarea>
          <button type="button" class="btn-icon" id="micBtn" onclick="toggleVoice()"><i class="fa-solid fa-microphone"></i></button>
          <button type="submit" class="btn btn-primary" id="sendBtn" style="width: 38px; height: 38px; padding: 0;"><i class="fa-solid fa-paper-plane"></i></button>
        </form>
      </div>
    </main>
  </div>

  <div id="toolsModal" class="modal hidden">
    <div class="modal-box">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
        <h3 style="font-size: 16px; font-weight: 700;"><i class="fa-solid fa-wand-magic-sparkles" style="color: var(--accent-cyan);"></i> Тавлиди ройгони тасвир (Flux)</h3>
        <button class="btn-icon" onclick="closeModal('toolsModal')"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">Тавсифи расмро ворид кунед (100% ройгон бо модели Flux):</p>
      <input type="text" id="imagePrompt" placeholder="Масалан: Табиати зебои Тоҷикистон, кӯҳҳои осмонбӯс..." style="width: 100%; background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); padding: 10px; border-radius: 10px; font-size: 13px; margin-bottom: 10px; outline: none;">
      <button class="btn btn-primary" onclick="generateImage()" id="genImgBtn" style="width: 100%;">Эҷод кардан</button>
      <div id="imageResult" style="margin-top: 14px; text-align: center;"></div>
    </div>
  </div>

  <div id="settingsModal" class="modal hidden">
    <div class="modal-box">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
        <h3 style="font-size: 16px; font-weight: 700;"><i class="fa-solid fa-gear" style="color: var(--accent-indigo);"></i> Танзимот ва Маъмурият</h3>
        <button class="btn-icon" onclick="closeModal('settingsModal')"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <div style="margin-bottom: 12px;">
        <label style="display: block; font-size: 12px; margin-bottom: 4px; font-weight: 600;">Модели Gemini:</label>
        <select id="modelSelect" style="width: 100%; background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); padding: 8px; border-radius: 8px; font-size: 12px;">
          <option value="gemini-1.5-flash">Gemini 1.5 Flash (Суръати тез, тарофаи ройгон)</option>
          <option value="gemini-1.5-pro">Gemini 1.5 Pro (Мантиқи амиқтар)</option>
        </select>
      </div>
      <div style="margin-bottom: 12px;">
        <label style="display: block; font-size: 12px; margin-bottom: 4px; font-weight: 600;">Ҳарорати эҷодкорӣ (Temperature):</label>
        <input type="range" id="tempRange" min="0" max="1" step="0.1" value="0.7" style="width: 100%;" oninput="document.getElementById('tempVal').innerText = this.value">
        <span id="tempVal" style="font-size: 11px; color: var(--accent-cyan);">0.7</span>
      </div>
      <div style="border-top: 1px solid var(--border); padding-top: 10px; margin-top: 10px;">
        <b style="font-size: 12px; color: var(--accent-indigo);">Санҷиши омори маъмур:</b>
        <div style="display: flex; gap: 6px; margin-top: 6px;">
          <input type="password" id="adminSecretInput" placeholder="Рамзи маъмур (maga_admin_2026)" style="flex: 1; background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); padding: 6px 10px; border-radius: 8px; font-size: 11px;">
          <button class="btn btn-secondary" onclick="checkAdminStats()" style="font-size: 11px;">Санҷидан</button>
        </div>
        <div id="adminStatsBox" style="margin-top: 8px; font-size: 11px; color: var(--text-secondary);"></div>
      </div>
    </div>
  </div>

  <script src="app.js"></script>
</body>
</html>
"""

# 10. public/app.js
FILES["public/app.js"] = """let currentLang = 'tg';
let currentTheme = 'dark';
let activeChatId = 'chat_1';
let chats = [];
let attachedFile = null;
let recognition = null;
let isListening = false;

const i18n = {
  tg: {
    newChat: 'Чати нав',
    tools: 'Абзорҳо',
    welcomeTitle: 'Хуш омадед ба MAGA AI!',
    welcomeDesc: 'Ёвари зеҳни сунъии шумо бо забони тоҷикӣ. Савол диҳед ё аз кортҳо оғоз кунед:',
    placeholder: 'Саволи худро нависед...',
    thinking: 'MAGA AI дар ҳоли фикрронӣ...'
  },
  ru: {
    newChat: 'Новый чат',
    tools: 'Инструменты',
    welcomeTitle: 'Добро пожаловать в MAGA AI!',
    welcomeDesc: 'Ваш умный ИИ-помощник. Задайте вопрос или выберите карточку:',
    placeholder: 'Задайте вопрос...',
    thinking: 'MAGA AI думает...'
  },
  en: {
    newChat: 'New Chat',
    tools: 'Tools',
    welcomeTitle: 'Welcome to MAGA AI!',
    welcomeDesc: 'Your intelligent AI assistant. Ask a question or start with a card:',
    placeholder: 'Ask anything...',
    thinking: 'MAGA AI is thinking...'
  }
};

function loadState() {
  const savedChats = localStorage.getItem('maga_chats');
  if (savedChats) {
    try { chats = JSON.parse(savedChats); } catch (e) { chats = []; }
  }
  if (!chats.length) {
    chats = [{ id: 'chat_' + Date.now(), title: 'Чати аввал', messages: [] }];
  }
  activeChatId = chats[0].id;

  const savedTheme = localStorage.getItem('maga_theme') || 'dark';
  setTheme(savedTheme);

  const savedLang = localStorage.getItem('maga_lang') || 'tg';
  changeLang(savedLang);

  renderChatList();
  renderMessages();
}

function saveChats() {
  localStorage.setItem('maga_chats', JSON.stringify(chats));
}

function getActiveChat() {
  return chats.find(c => c.id === activeChatId) || chats[0];
}

function renderChatList() {
  const list = document.getElementById('chatList');
  list.innerHTML = '';
  chats.forEach(c => {
    const item = document.createElement('div');
    item.style.cssText = `padding: 8px 10px; border-radius: 8px; margin-bottom: 4px; font-size: 12px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: ${c.id === activeChatId ? 'var(--border)' : 'transparent'}`;
    item.innerHTML = `<span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"><i class="fa-regular fa-message" style="margin-right: 6px;"></i>${c.title}</span><i class="fa-solid fa-trash" style="opacity: 0.5; font-size: 11px;" onclick="deleteChat('${c.id}', event)"></i>`;
    item.onclick = () => selectChat(c.id);
    list.appendChild(item);
  });
}

function selectChat(id) {
  activeChatId = id;
  renderChatList();
  renderMessages();
  if (window.innerWidth <= 768) toggleSidebar();
}

function newChat() {
  const newId = 'chat_' + Date.now();
  chats.unshift({ id: newId, title: 'Чати нав', messages: [] });
  activeChatId = newId;
  saveChats();
  renderChatList();
  renderMessages();
  if (window.innerWidth <= 768) toggleSidebar();
}

function deleteChat(id, e) {
  e.stopPropagation();
  chats = chats.filter(c => c.id !== id);
  if (!chats.length) newChat();
  else {
    activeChatId = chats[0].id;
    saveChats();
    renderChatList();
    renderMessages();
  }
}

function renderMessages() {
  const chat = getActiveChat();
  const box = document.getElementById('messagesBox');
  const welcome = document.getElementById('welcomeCard');

  if (!chat.messages.length) {
    box.innerHTML = '';
    box.appendChild(welcome);
    welcome.style.display = 'block';
    return;
  }

  welcome.style.display = 'none';
  box.innerHTML = '';

  chat.messages.forEach(m => {
    const bubble = document.createElement('div');
    const isUser = m.role === 'user';
    bubble.className = `bubble ${isUser ? 'bubble-user' : (m.role === 'error' ? 'bubble-error' : 'bubble-bot')}`;

    let fileHtml = m.fileName ? `<div style="font-size: 11px; opacity: 0.8; margin-bottom: 4px;"><i class="fa-solid fa-paperclip"></i> ${m.fileName}</div>` : '';
    bubble.innerHTML = `${fileHtml}<div>${escapeHtml(m.content)}</div>`;

    if (!isUser && m.role !== 'error') {
      const copyBtn = document.createElement('button');
      copyBtn.className = 'btn-icon';
      copyBtn.style.cssText = 'width: 24px; height: 24px; font-size: 11px; margin-top: 6px;';
      copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i>';
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(m.content);
        copyBtn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--accent-cyan);"></i>';
        setTimeout(() => copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i>', 2000);
      };
      bubble.appendChild(copyBtn);
    }

    box.appendChild(bubble);
  });

  box.scrollTop = box.scrollHeight;
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function handleSubmit(e) {
  if (e) e.preventDefault();
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text && !attachedFile) return;

  const chat = getActiveChat();
  if (!chat.messages.length) {
    chat.title = text ? text.slice(0, 24) : (attachedFile ? attachedFile.name : 'Гуфтугӯ');
  }

  const userMsg = { role: 'user', content: text, fileName: attachedFile ? attachedFile.name : null };
  chat.messages.push(userMsg);
  input.value = '';

  const fileToSend = attachedFile;
  removeFile();

  renderMessages();
  saveChats();

  const box = document.getElementById('messagesBox');
  const loadingBubble = document.createElement('div');
  loadingBubble.className = 'bubble bubble-bot';
  loadingBubble.id = 'loadingIndicator';
  loadingBubble.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin" style="color: var(--accent-cyan); margin-right: 6px;"></i> ${i18n[currentLang].thinking}`;
  box.appendChild(loadingBubble);
  box.scrollTop = box.scrollHeight;

  try {
    let reply = '';
    const model = document.getElementById('modelSelect').value;
    const temperature = document.getElementById('tempRange').value;

    if (fileToSend) {
      const fd = new FormData();
      fd.append('file', fileToSend);
      fd.append('prompt', text || 'Ин файлро мукаммал таҳлил кунед.');
      fd.append('model', model);

      const res = await fetch('/api/analyze-file', { method: 'POST', body: fd });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      reply = data.reply;
    } else {
      const history = chat.messages.slice(-8).map(m => ({ role: m.role, content: m.content }));
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history, model, temperature })
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      reply = data.reply;
    }

    loadingBubble.remove();
    chat.messages.push({ role: 'assistant', content: reply });
  } catch (err) {
    loadingBubble.remove();
    chat.messages.push({ role: 'error', content: err.message || 'Хатогӣ рух дод.' });
  }

  renderMessages();
  saveChats();
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSubmit();
  }
}

function sendQuickPrompt(prompt) {
  document.getElementById('chatInput').value = prompt;
  handleSubmit();
}

function handleFileSelect(e) {
  if (e.target.files && e.target.files[0]) {
    attachedFile = e.target.files[0];
    document.getElementById('fileBadge').style.display = 'inline-flex';
    document.getElementById('fileName').innerText = attachedFile.name;
  }
}

function removeFile() {
  attachedFile = null;
  document.getElementById('fileBadge').style.display = 'none';
  document.getElementById('fileInput').value = '';
}

function toggleVoice() {
  const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Speech) return alert('Браузери шумо сабти овозро дастгирӣ намекунад.');
  const btn = document.getElementById('micBtn');

  if (isListening) {
    if (recognition) recognition.stop();
    return;
  }

  recognition = new Speech();
  recognition.lang = currentLang === 'tg' ? 'tg-TJ' : (currentLang === 'ru' ? 'ru-RU' : 'en-US');
  recognition.onstart = () => { isListening = true; btn.style.color = 'var(--danger)'; };
  recognition.onresult = (e) => {
    document.getElementById('chatInput').value = e.results[0][0].transcript;
  };
  recognition.onend = () => { isListening = false; btn.style.color = 'inherit'; };
  recognition.start();
}

async function generateImage() {
  const prompt = document.getElementById('imagePrompt').value.trim();
  const box = document.getElementById('imageResult');
  const btn = document.getElementById('genImgBtn');
  if (!prompt) return;

  btn.disabled = true;
  btn.innerText = 'Дар ҳоли эҷод...';
  box.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size: 20px; color: var(--accent-cyan);"></i>';

  try {
    const res = await fetch('/api/generate-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();
    if (data.imageUrl) {
      box.innerHTML = `<img src="${data.imageUrl}" style="max-width: 100%; border-radius: 12px; margin-bottom: 8px;"><br><a href="${data.i