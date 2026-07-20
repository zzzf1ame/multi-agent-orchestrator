"""
FastAPI application entry point for Multi-Agent Orchestrator.
Includes a single-page frontend for interactive research tasks.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .api import router, ws_router

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Multi-Agent Orchestrator v2.0")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Multi-Agent Orchestrator",
    description="Autonomous AI research agent powered by LangGraph 1.x",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(ws_router)


@app.get("/", response_class=HTMLResponse)
async def frontend():
    """Single-page frontend: submit topic → watch agents work → read report."""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Multi-Agent Orchestrator</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
.container { max-width: 900px; margin: 0 auto; padding: 2rem 1.5rem; }
h1 { font-size: 1.8rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }
.input-group { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
input[type="text"] { flex: 1; min-width: 250px; padding: 0.75rem 1rem; border-radius: 0.75rem; border: 1px solid #334155; background: #1e293b; color: #f1f5f9; font-size: 0.95rem; outline: none; transition: border-color 0.2s; }
input[type="text"]:focus { border-color: #60a5fa; }
select { padding: 0.75rem 1rem; border-radius: 0.75rem; border: 1px solid #334155; background: #1e293b; color: #f1f5f9; font-size: 0.9rem; }
button { padding: 0.75rem 1.5rem; border-radius: 0.75rem; border: none; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
button:hover { opacity: 0.9; }
button:disabled { opacity: 0.4; cursor: not-allowed; }
.status-bar { display: flex; align-items: center; gap: 0.75rem; padding: 1rem; background: #1e293b; border-radius: 0.75rem; margin-bottom: 1.5rem; border: 1px solid #334155; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: #475569; }
.status-dot.active { background: #22c55e; animation: pulse 1.5s infinite; }
.status-dot.working { background: #f59e0b; animation: pulse 1s infinite; }
.status-dot.error { background: #ef4444; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.status-text { font-size: 0.85rem; color: #94a3b8; }
.progress-steps { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.step { padding: 0.4rem 0.8rem; border-radius: 2rem; font-size: 0.75rem; background: #1e293b; border: 1px solid #334155; color: #64748b; }
.step.done { border-color: #22c55e; color: #22c55e; }
.step.active { border-color: #f59e0b; color: #f59e0b; }
.result { background: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; padding: 1.5rem; margin-top: 1rem; }
.result h2 { font-size: 1.2rem; color: #f1f5f9; margin-bottom: 1rem; }
.result .meta { font-size: 0.8rem; color: #64748b; margin-bottom: 1rem; }
.article-content { line-height: 1.7; color: #cbd5e1; font-size: 0.9rem; white-space: pre-wrap; max-height: 500px; overflow-y: auto; }
.article-content h1,.article-content h2,.article-content h3 { color: #f1f5f9; margin: 1rem 0 0.5rem; }
.sources { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #334155; }
.sources a { color: #60a5fa; text-decoration: none; font-size: 0.85rem; display: block; margin: 0.3rem 0; }
.sources a:hover { text-decoration: underline; }
.hidden { display: none; }
</style>
</head>
<body>
<div class="container">
  <h1>Multi-Agent Orchestrator</h1>
  <p class="subtitle">LangGraph 1.x · Tavily Search · LLM Report Generation</p>

  <div class="input-group">
    <input type="text" id="topic" placeholder="输入研究主题，如：2025年大语言模型的发展趋势" />
    <select id="depth">
      <option value="brief">简要</option>
      <option value="detailed" selected>详细</option>
      <option value="comprehensive">全面</option>
    </select>
    <button id="startBtn" onclick="startResearch()">开始研究</button>
  </div>

  <div class="status-bar">
    <div class="status-dot" id="statusDot"></div>
    <span class="status-text" id="statusText">就绪 — 输入主题后点击开始</span>
  </div>

  <div class="progress-steps" id="steps">
    <span class="step" id="step-research">🔍 搜索</span>
    <span class="step" id="step-validate">✅ 校验</span>
    <span class="step" id="step-write">✍️ 撰写</span>
    <span class="step" id="step-done">📄 完成</span>
  </div>

  <div class="result hidden" id="resultPanel">
    <h2 id="articleTitle"></h2>
    <div class="meta" id="articleMeta"></div>
    <div class="article-content" id="articleContent"></div>
    <div class="sources" id="articleSources"></div>
  </div>
</div>

<script>
let polling = null;

function setStep(name, state) {
  const el = document.getElementById('step-' + name);
  el.className = 'step ' + state;
}

function setStatus(dotClass, text) {
  document.getElementById('statusDot').className = 'status-dot ' + dotClass;
  document.getElementById('statusText').textContent = text;
}

async function startResearch() {
  const topic = document.getElementById('topic').value.trim();
  if (!topic) return alert('请输入研究主题');

  const depth = document.getElementById('depth').value;
  const btn = document.getElementById('startBtn');
  btn.disabled = true;

  // Reset UI
  ['research','validate','write','done'].forEach(s => setStep(s, ''));
  document.getElementById('resultPanel').classList.add('hidden');
  setStatus('working', '正在创建任务...');
  setStep('research', 'active');

  try {
    const res = await fetch('/api/v1/research', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ topic, depth, max_sources: 5 })
    });
    const data = await res.json();
    const taskId = data.task_id;
    setStatus('working', `任务已创建 (${taskId})，Agent 正在工作...`);
    pollTask(taskId);
  } catch (e) {
    setStatus('error', '请求失败: ' + e.message);
    btn.disabled = false;
  }
}

function pollTask(taskId) {
  polling = setInterval(async () => {
    try {
      const res = await fetch(`/api/v1/research/${taskId}`);
      const data = await res.json();

      if (data.status === 'researching') {
        setStep('research', 'active');
        setStatus('working', 'Researcher Agent 正在搜索和分析...');
      }

      if (data.status === 'completed') {
        clearInterval(polling);
        setStep('research', 'done');
        setStep('validate', 'done');
        setStep('write', 'done');
        setStep('done', 'done');
        setStatus('active', `完成！耗时 ${data.duration_seconds?.toFixed(1) || '?'}s`);
        showResult(data);
        document.getElementById('startBtn').disabled = false;
      }

      if (data.status === 'failed') {
        clearInterval(polling);
        setStatus('error', '任务失败: ' + (data.error || '未知错误'));
        document.getElementById('startBtn').disabled = false;
      }
    } catch (e) { /* retry next tick */ }
  }, 1500);
}

function showResult(data) {
  const panel = document.getElementById('resultPanel');
  panel.classList.remove('hidden');

  if (data.article) {
    document.getElementById('articleTitle').textContent = data.article.title;
    document.getElementById('articleMeta').textContent =
      `${data.article.word_count} 字 · ${data.article.sections?.join(' / ') || ''}`;
    document.getElementById('articleContent').textContent = data.article.content;
  }

  if (data.research?.sources?.length) {
    const srcHtml = data.research.sources.map(s =>
      `<a href="${s.url}" target="_blank">${s.title || s.url}</a>`
    ).join('');
    document.getElementById('articleSources').innerHTML = '<strong>参考来源：</strong>' + srcHtml;
  }
}
</script>
</body>
</html>"""


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multi-agent-orchestrator", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
