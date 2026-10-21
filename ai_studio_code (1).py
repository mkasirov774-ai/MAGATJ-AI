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
  z-index