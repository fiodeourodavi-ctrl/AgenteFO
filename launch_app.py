import os
import subprocess
import time
import threading
import json
import shutil
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

try:
    from google.colab import output
    from IPython.display import display, HTML
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
    output = None
    display = None
    HTML = None

TERMINAL_PORT = 8000
WRAPPER_PORT  = 8001
WRAPPER_DIR   = "/tmp/agentefo-wrapper"

_opencode_bin = None
_env          = None
_drive_url    = "https://drive.google.com/drive/my-drive"
_folder_path  = "/content"


def set_drive_info(folder_path, drive_url):
    global _drive_url, _folder_path
    _drive_url   = drive_url
    _folder_path = folder_path


def resolve_opencode():
    global _opencode_bin, _env

    if "OPENCODE_BIN" in os.environ and os.path.isfile(os.environ["OPENCODE_BIN"]):
        _opencode_bin = os.environ["OPENCODE_BIN"]
    else:
        _candidates = [
            os.path.expanduser("~/.local/bin/opencode"),
            os.path.expanduser("~/bin/opencode"),
            "/root/.local/bin/opencode",
            "/root/bin/opencode",
            "/usr/local/bin/opencode",
            "/usr/bin/opencode",
        ]
        _found = next((p for p in _candidates if os.path.isfile(p)), None)

        if _found is None:
            _which = shutil.which("opencode")
            if _which:
                _found = _which
            else:
                result = subprocess.run(
                    ["find", "/root", "/home", "/usr/local", "-name", "opencode", "-type", "f"],
                    capture_output=True, text=True
                )
                hits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
                _found = hits[0] if hits else "opencode"

        _opencode_bin = _found

    _extra_path = (
        os.path.dirname(_opencode_bin)
        if os.path.isfile(_opencode_bin)
        else os.path.expanduser("~/.local/bin")
    )

    _env = {
        **os.environ,
        "OPENCODE_EXPERIMENTAL_DISABLE_COPY_ON_SELECT": "1",
        "PATH": os.environ.get("PATH", "") + ":" + _extra_path,
    }

    print(f"🔍 OpenCode binário: {_opencode_bin}")
    return _opencode_bin, _env


def install_ttyd():
    print("📦 Instalando ttyd...")
    subprocess.run(
        "apt-get update -qq && apt-get install -y -qq ttyd",
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    print("✅ ttyd instalado.")


def kill_previous():
    subprocess.run("pkill -f ttyd 2>/dev/null || true", shell=True)
    subprocess.run(f"pkill -f 'python3.*{WRAPPER_PORT}' 2>/dev/null || true", shell=True)
    time.sleep(0.5)


def start_ttyd():
    opencode_bin, env = resolve_opencode()
    subprocess.Popen(
        ["ttyd", "-p", str(TERMINAL_PORT), "bash", "-i", "-c",
         f"{opencode_bin}; exec bash"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    print("🚀 Terminal iniciado.")
    time.sleep(2)


def create_wrapper_html(terminal_url, drive_url):
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgenteFO — Fio de Ouro</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;0,500;1,400&family=Syne:wght@700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --ink:         #f0e8d0;
      --ink-muted:   #9a8f78;
      --surface:     #0c0b09;
      --rail:        #141210;
      --line:        rgba(212,175,55,.10);
      --gold:        #d4af37;
      --gold-dim:    rgba(212,175,55,.12);
      --gold-glow:   rgba(212,175,55,.25);
      --green:       #6dbf7e;
      --green-dim:   rgba(109,191,126,.12);
      --amber:       #e8b84b;
      --amber-dim:   rgba(232,184,75,.12);
      --red:         #e07070;
      --red-dim:     rgba(224,112,112,.12);
      --radius:      5px;
    }}

    html, body {{
      height: 100%;
      background: var(--surface);
      color: var(--ink);
      font-family: "DM Mono", monospace;
      overflow: hidden;
    }}

    /* ── TOP BAR ── */
    #topbar {{
      position: fixed; inset: 0 0 auto 0;
      height: 50px;
      background: var(--rail);
      border-bottom: 1px solid var(--line);
      display: flex; align-items: center;
      padding: 0 18px; gap: 14px;
      z-index: 9999;
    }}

    .logo {{ display: flex; align-items: baseline; gap: 2px; }}
    .logo-a  {{ font-family:"Syne",sans-serif; font-weight:800; font-size:17px;
                color:var(--ink); letter-spacing:-.5px; }}
    .logo-fo {{ font-family:"Syne",sans-serif; font-weight:700; font-size:17px;
                color:var(--gold); letter-spacing:-.5px; }}
    .logo-tag {{
      margin-left:9px; font-size:10px; color:var(--ink-muted);
      letter-spacing:.07em; padding:1px 6px;
      border:1px solid var(--line); border-radius:3px; align-self:center;
    }}
    .logo-brand {{
      margin-left: 6px; font-size: 11px; color: var(--ink-muted);
      letter-spacing: .06em; align-self: center;
    }}

    .status {{ display:flex; align-items:center; gap:7px;
               font-size:11px; color:var(--ink-muted); }}
    .status-dot {{
      width:7px; height:7px; border-radius:50%; background:var(--green);
      animation: pulse 2.4s ease infinite;
    }}
    @keyframes pulse {{
      0%,100% {{ box-shadow:0 0 0 0 rgba(109,191,126,.5); }}
      50%      {{ box-shadow:0 0 0 5px rgba(109,191,126,0); }}
    }}

    .sep {{ flex: 1; }}

    .tb-btn {{
      display: inline-flex; align-items: center; gap: 7px;
      padding: 0 13px; height: 30px;
      font-family: "DM Mono", monospace; font-size: 11px;
      font-weight: 500; letter-spacing: .04em;
      border-radius: var(--radius); cursor: pointer;
      border: 1px solid; transition: background .15s, transform .1s;
      text-decoration: none; white-space: nowrap;
    }}
    .tb-btn:active {{ transform: scale(.96); }}
    .tb-btn svg {{ width:13px; height:13px; stroke:currentColor; fill:none;
                   stroke-width:2; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0; }}

    .btn-drive  {{ color:var(--gold);  background:var(--gold-dim);
                   border-color:rgba(212,175,55,.25); }}
    .btn-drive:hover  {{ background:var(--gold-glow); border-color:rgba(212,175,55,.5); }}

    .btn-backup {{ color:var(--green); background:var(--green-dim);
                   border-color:rgba(109,191,126,.25); }}
    .btn-backup:hover {{ background:rgba(109,191,126,.2); border-color:rgba(109,191,126,.5); }}

    .btn-restore {{ color:var(--amber); background:var(--amber-dim);
                    border-color:rgba(232,184,75,.25); }}
    .btn-restore:hover {{ background:rgba(232,184,75,.2); border-color:rgba(232,184,75,.5); }}

    /* ── TERMINAL IFRAME ── */
    #terminal-frame {{
      position: absolute;
      inset: 50px 0 40px 0;
      width: 100%; height: calc(100% - 10px);
      border: none;
    }}

    /* ── FOOTER ── */
    #footer {{
      position: fixed; inset: auto 0 0 0;
      height: 40px;
      background: var(--rail);
      border-top: 1px solid var(--line);
      display: flex; align-items: center;
      padding: 0 18px; gap: 0;
      font-size: 10.5px; color: var(--ink-muted);
      z-index: 9999;
    }}
    .footer-brand {{
      font-family: "Syne", sans-serif; font-weight: 700;
      font-size: 11px; color: var(--gold); margin-right: 14px;
    }}
    .footer-sep {{ width:1px; height:16px; background:var(--line); margin:0 12px; flex-shrink:0; }}
    .footer-link {{
      color: var(--ink-muted); text-decoration: none; letter-spacing: .03em;
      transition: color .15s;
    }}
    .footer-link:hover {{ color: var(--gold); }}
    .footer-right {{ margin-left:auto; display:flex; align-items:center; gap:12px; }}

    .btn-provider {{
      display: inline-flex; align-items: center; gap: 5px;
      padding: 0 10px; height: 24px;
      font-family: "DM Mono", monospace; font-size: 10px;
      font-weight: 500; letter-spacing: .03em;
      border-radius: var(--radius); cursor: pointer;
      border: 1px solid rgba(212,175,55,.18);
      color: rgba(212,175,55,.55);
      background: transparent;
      transition: background .15s, color .15s, border-color .15s;
      white-space: nowrap;
    }}
    .btn-provider:hover {{
      background: var(--gold-dim);
      color: var(--gold);
      border-color: rgba(212,175,55,.4);
    }}

    /* ── TOAST ── */
    #toast {{
      position: fixed; bottom: 58px; right: 18px;
      padding: 9px 16px; border-radius: var(--radius);
      font-size: 12px; font-family: "DM Mono", monospace;
      display: flex; align-items: center; gap: 8px;
      opacity: 0; transform: translateY(6px);
      transition: opacity .22s, transform .22s;
      pointer-events: none; z-index: 9998; max-width: 340px;
      border: 1px solid;
    }}
    #toast.show  {{ opacity: 1; transform: translateY(0); }}
    #toast.ok    {{ background:rgba(109,191,126,.15); border-color:rgba(109,191,126,.35); color:var(--green); }}
    #toast.err   {{ background:rgba(224,112,112,.15); border-color:rgba(224,112,112,.35); color:var(--red);   }}
    #toast.info  {{ background:var(--gold-dim);       border-color:rgba(212,175,55,.35);  color:var(--gold);  }}

    /* ── MODAL BACKUP/RESTORE ── */
    #modal-overlay {{
      position: fixed; inset: 0;
      background: rgba(0,0,0,.65); backdrop-filter: blur(3px);
      display: flex; align-items: center; justify-content: center;
      z-index: 99999; opacity: 0; pointer-events: none;
      transition: opacity .2s;
    }}
    #modal-overlay.open {{ opacity: 1; pointer-events: all; }}
    #modal {{
      background: #181510; border: 1px solid rgba(212,175,55,.15);
      border-radius: 8px; padding: 24px; width: 400px; max-width: 90vw;
      box-shadow: 0 24px 64px rgba(0,0,0,.7);
    }}
    .modal-title {{
      font-family: "Syne", sans-serif; font-weight: 800;
      font-size: 15px; color: var(--gold); margin-bottom: 16px;
    }}
    .backup-list {{
      max-height: 260px; overflow-y: auto;
      border: 1px solid var(--line); border-radius: var(--radius);
      margin-bottom: 16px;
    }}
    .backup-item {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 9px 12px; font-size: 11.5px; color: var(--ink-muted);
      border-bottom: 1px solid var(--line); cursor: pointer;
      transition: background .12s;
    }}
    .backup-item:last-child {{ border-bottom: none; }}
    .backup-item:hover {{ background: rgba(212,175,55,.05); color: var(--ink); }}
    .backup-item .restore-lbl {{
      font-size: 10px; padding: 2px 8px;
      background: var(--amber-dim); color: var(--amber);
      border: 1px solid rgba(232,184,75,.3); border-radius: 3px;
    }}
    .modal-empty {{ padding:20px; text-align:center; font-size:12px; color:var(--ink-muted); }}
    .modal-close {{
      display: block; width: 100%; padding: 8px;
      background: rgba(255,255,255,.04); border: 1px solid var(--line);
      border-radius: var(--radius); color: var(--ink-muted);
      font-family: "DM Mono", monospace; font-size: 12px;
      cursor: pointer; transition: background .15s;
    }}
    .modal-close:hover {{ background: rgba(212,175,55,.08); color: var(--gold); }}

    /* ── MODAL PROVEDOR ── */
    #provider-overlay {{
      position: fixed; inset: 0;
      background: rgba(0,0,0,.65); backdrop-filter: blur(3px);
      display: flex; align-items: center; justify-content: center;
      z-index: 99999; opacity: 0; pointer-events: none;
      transition: opacity .2s;
    }}
    #provider-modal {{
      background: #181510; border: 1px solid rgba(212,175,55,.15);
      border-radius: 8px; padding: 24px; width: 440px; max-width: 92vw;
      box-shadow: 0 24px 64px rgba(0,0,0,.7);
    }}
  </style>
</head>
<body>

  <div id="topbar">
    <div class="logo">
      <span class="logo-a">Agente</span><span class="logo-fo">FO</span>
      <span class="logo-tag">v1.0</span>
      <span class="logo-brand">· Fio de Ouro</span>
    </div>

    <div class="status">
      <span class="status-dot"></span>
      agente ativo
    </div>

    <div class="sep"></div>

    <button class="tb-btn btn-backup" onclick="doBackup()">
      <svg viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
      <polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
      Salvar sessão
    </button>

    <button class="tb-btn btn-restore" onclick="openRestore()">
      <svg viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/>
      <path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>
      Restaurar
    </button>

    <a href="{drive_url}" target="_blank" class="tb-btn btn-drive">
      <svg viewBox="0 0 24 24"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
      Drive
    </a>
  </div>

  <iframe
    id="terminal-frame"
    src="{terminal_url}"
    allow="clipboard-read; clipboard-write"
    tabindex="0"
    autofocus
    style="width:100%;height:calc(100% - 90px);border:none;outline:none;">
  </iframe>

  <div id="footer">
    <span class="footer-brand">🧵 Fio de Ouro</span>
    <span class="footer-sep"></span>
    <span style="color:var(--ink-muted);font-size:10.5px;">Gestão de Representantes</span>
    <div class="footer-right">
      <button class="btn-provider" onclick="connectProvider()">
        <svg viewBox="0 0 24 24" style="width:10px;height:10px;stroke:currentColor;fill:none;stroke-width:2;">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M2 12h3M19 12h3"/>
        </svg>
        + provedor IA
      </button>
      <span class="footer-sep"></span>
      <span style="color:var(--ink-muted)">Powered by <a href="https://opencode.ai" target="_blank"
        style="color:var(--ink-muted);text-decoration:none;">OpenCode</a></span>
    </div>
  </div>

  <div id="toast"></div>

  <!-- Modal restaurar sessão -->
  <div id="modal-overlay" onclick="if(event.target===this)closeModal()">
    <div id="modal">
      <div class="modal-title">🔄 Restaurar Sessão</div>
      <div class="backup-list" id="backup-list">
        <div class="modal-empty">Carregando backups…</div>
      </div>
      <button class="modal-close" onclick="closeModal()">Fechar</button>
    </div>
  </div>

  <!-- Modal provedor -->
  <div id="provider-overlay" onclick="if(event.target===this)closeProvider()">
    <div id="provider-modal">
      <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:15px;
                  color:var(--gold);margin-bottom:16px;">🔌 Conectar Provedor de IA</div>

      <div id="prov-step1">
        <div style="font-size:11px;color:var(--ink-muted);margin-bottom:12px;">
          Selecione o provedor:
        </div>
        <div id="prov-list" style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:16px;"></div>
        <button onclick="closeProvider()" style="
          display:block;width:100%;padding:8px;
          background:rgba(255,255,255,.04);border:1px solid var(--line);
          border-radius:var(--radius);color:var(--ink-muted);
          font-family:'DM Mono',monospace;font-size:12px;cursor:pointer;">
          Cancelar
        </button>
      </div>

      <div id="prov-step2" style="display:none;">
        <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:13px;
                    color:var(--ink);margin-bottom:6px;" id="prov-name-title"></div>
        <div style="font-size:10.5px;color:var(--ink-muted);margin-bottom:12px;">
          Variável de ambiente: <code id="prov-env-code"
            style="color:var(--gold);background:var(--gold-dim);
                   padding:1px 5px;border-radius:3px;"></code>
        </div>
        <input id="prov-key-input" type="password"
          placeholder="Cole sua API key aqui…"
          style="width:100%;padding:9px 11px;background:var(--surface);
          border:1px solid var(--line);border-radius:var(--radius);
          color:var(--ink);font-family:'DM Mono',monospace;font-size:12px;
          outline:none;margin-bottom:14px;transition:border-color .15s;"
          onfocus="this.style.borderColor='rgba(212,175,55,.4)'"
          onblur="this.style.borderColor='var(--line)'"
          onkeydown="if(event.key==='Enter')confirmProvider()"/>
        <div style="display:flex;gap:8px;">
          <button onclick="provBack()" style="
            padding:9px 14px;background:rgba(255,255,255,.04);border:1px solid var(--line);
            border-radius:var(--radius);color:var(--ink-muted);
            font-family:'DM Mono',monospace;font-size:12px;cursor:pointer;">
            ← Voltar
          </button>
          <button onclick="confirmProvider()" style="
            flex:1;padding:9px;background:var(--gold-dim);
            border:1px solid rgba(212,175,55,.3);
            border-radius:var(--radius);color:var(--gold);
            font-family:'DM Mono',monospace;font-size:12px;cursor:pointer;">
            Salvar e Conectar
          </button>
          <button onclick="closeProvider()" style="
            padding:9px 14px;background:rgba(255,255,255,.04);border:1px solid var(--line);
            border-radius:var(--radius);color:var(--ink-muted);
            font-family:'DM Mono',monospace;font-size:12px;cursor:pointer;">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  </div>

  <script>
    const BASE = location.origin;

    let _toastT;
    function toast(msg, type = "info") {{
      const el = document.getElementById("toast");
      el.className = "show " + type;
      el.textContent = msg;
      clearTimeout(_toastT);
      _toastT = setTimeout(() => el.classList.remove("show"), 3800);
    }}

    // ── Backup ──
    async function doBackup() {{
      toast("⏳ Exportando sessão…", "info");
      try {{
        const r = await fetch(BASE + "/api/backup", {{
          method: "POST", headers: {{"Content-Type":"application/json"}},
          body: JSON.stringify({{}})
        }});
        const d = await r.json();
        if (d.ok) toast("✅ Backup salvo: " + d.file, "ok");
        else      toast("❌ " + (d.error || "Erro"), "err");
      }} catch(e) {{ toast("❌ Falha: " + e.message, "err"); }}
    }}

    // ── Restore modal ──
    async function openRestore() {{
      document.getElementById("modal-overlay").classList.add("open");
      const list = document.getElementById("backup-list");
      list.innerHTML = '<div class="modal-empty">Carregando backups…</div>';
      try {{
        const r = await fetch(BASE + "/api/backups");
        const d = await r.json();
        if (!d.backups || !d.backups.length) {{
          list.innerHTML = '<div class="modal-empty">Nenhum backup encontrado.</div>';
          return;
        }}
        list.innerHTML = d.backups.map(f => `
          <div class="backup-item" onclick="doRestore('${{f}}')">
            <span>${{f}}</span><span class="restore-lbl">restaurar</span>
          </div>`).join("");
      }} catch(e) {{
        list.innerHTML = '<div class="modal-empty">Erro ao carregar backups.</div>';
      }}
    }}
    function closeModal() {{
      document.getElementById("modal-overlay").classList.remove("open");
    }}

    async function doRestore(file) {{
      closeModal();
      toast("⏳ Importando " + file + "…", "info");
      try {{
        const r = await fetch(BASE + "/api/restore", {{
          method: "POST", headers: {{"Content-Type":"application/json"}},
          body: JSON.stringify({{ file }})
        }});
        const d = await r.json();
        if (d.ok) {{
          const cmd = d.session_id ? "opencode -s " + d.session_id : "opencode";
          toast("✅ Importado!", "ok");
          setTimeout(() => {{
            if (window.confirm("Sessão restaurada! Reiniciar terminal agora?")) {{
              fetch(BASE + "/api/run_terminal", {{
                method: "POST", headers: {{"Content-Type":"application/json"}},
                body: JSON.stringify({{ command: cmd, no_fallback: true }})
              }}).then(() => {{
                const fr = document.getElementById("terminal-frame");
                const src = fr.src.split("?")[0];
                fr.src = "about:blank";
                setTimeout(() => {{ fr.src = src + "?t=" + Date.now(); }}, 3500);
              }});
            }}
          }}, 600);
        }} else {{
          toast("❌ " + (d.error || "Erro ao importar"), "err");
        }}
      }} catch(e) {{ toast("❌ " + e.message, "err"); }}
    }}

    // ── Providers ──
    const PROVIDERS = [
      {{ id:"groq",      name:"Groq (Grátis)",    env:"GROQ_API_KEY",                      hint:"gsk_…"   }},
      {{ id:"google",    name:"Google Gemini",     env:"GOOGLE_GENERATIVE_AI_API_KEY",      hint:"AIza…"   }},
      {{ id:"anthropic", name:"Anthropic Claude",  env:"ANTHROPIC_API_KEY",                 hint:"sk-ant-…"}},
      {{ id:"openai",    name:"OpenAI",            env:"OPENAI_API_KEY",                    hint:"sk-…"    }},
      {{ id:"deepseek",  name:"DeepSeek",          env:"DEEPSEEK_API_KEY",                  hint:"sk-…"    }},
      {{ id:"openrouter",name:"OpenRouter",        env:"OPENROUTER_API_KEY",                hint:"sk-or-…" }},
      {{ id:"mistral",   name:"Mistral",           env:"MISTRAL_API_KEY",                   hint:"…"       }},
      {{ id:"together",  name:"Together AI",       env:"TOGETHER_API_KEY",                  hint:"…"       }},
    ];

    let _selProv = null;

    function connectProvider() {{
      const grid = document.getElementById("prov-list");
      grid.innerHTML = PROVIDERS.map(p => `
        <button onclick="selectProvider('${{p.id}}')" style="
          display:flex;align-items:center;gap:8px;padding:9px 12px;
          background:rgba(255,255,255,.03);border:1px solid var(--line);
          border-radius:var(--radius);color:var(--ink-muted);
          font-family:'DM Mono',monospace;font-size:11px;cursor:pointer;
          text-align:left;transition:all .12s;"
          onmouseover="this.style.background='var(--gold-dim)';this.style.color='var(--gold)';this.style.borderColor='rgba(212,175,55,.35)'"
          onmouseout="this.style.background='rgba(255,255,255,.03)';this.style.color='var(--ink-muted)';this.style.borderColor='var(--line)'">
          ${{p.name}}
        </button>`).join("");
      document.getElementById("prov-step1").style.display = "block";
      document.getElementById("prov-step2").style.display = "none";
      const overlay = document.getElementById("provider-overlay");
      overlay.style.opacity = "1";
      overlay.style.pointerEvents = "all";
    }}

    function selectProvider(id) {{
      _selProv = PROVIDERS.find(p => p.id === id);
      if (!_selProv) return;
      document.getElementById("prov-name-title").textContent = _selProv.name;
      document.getElementById("prov-env-code").textContent  = _selProv.env;
      document.getElementById("prov-key-input").placeholder = _selProv.hint || "Cole sua key…";
      document.getElementById("prov-key-input").value = "";
      fetch(BASE + "/api/apikey?provider=" + _selProv.id)
        .then(r => r.json())
        .then(d => {{ if (d.apikey) document.getElementById("prov-key-input").value = d.apikey; }})
        .catch(() => {{}});
      document.getElementById("prov-step1").style.display = "none";
      document.getElementById("prov-step2").style.display = "block";
      setTimeout(() => document.getElementById("prov-key-input").focus(), 80);
    }}

    function provBack() {{
      document.getElementById("prov-step1").style.display = "block";
      document.getElementById("prov-step2").style.display = "none";
    }}

    function closeProvider() {{
      const overlay = document.getElementById("provider-overlay");
      overlay.style.opacity = "0";
      overlay.style.pointerEvents = "none";
      _selProv = null;
    }}

    async function confirmProvider() {{
      const key = document.getElementById("prov-key-input").value.trim();
      if (!key) {{ toast("⚠️ Insira a API key.", "err"); return; }}
      if (!_selProv) {{ toast("⚠️ Selecione um provedor.", "err"); return; }}
      const prov = _selProv;
      closeProvider();
      toast("💾 Salvando key…", "info");
      try {{
        const sr = await fetch(BASE + "/api/apikey", {{
          method: "POST", headers: {{"Content-Type":"application/json"}},
          body: JSON.stringify({{ provider: prov.id, env: prov.env, apikey: key }})
        }});
        const sd = await sr.json();
        if (!sd.ok) {{ toast("❌ Erro ao salvar: " + (sd.error||""), "err"); return; }}
        toast("✅ Key salva!", "ok");
      }} catch(e) {{ toast("❌ Falha ao salvar key.", "err"); return; }}

      const cmd = `export ${{prov.env}}="${{key}}" && opencode`;
      try {{
        await fetch(BASE + "/api/run_terminal", {{
          method: "POST", headers: {{"Content-Type":"application/json"}},
          body: JSON.stringify({{ command: cmd, no_fallback: true }})
        }});
        const fr = document.getElementById("terminal-frame");
        const src = fr.src.split("?")[0];
        fr.src = "about:blank";
        setTimeout(() => {{
          fr.src = src + "?t=" + Date.now();
          toast("✅ " + prov.name + " configurado!", "ok");
        }}, 3500);
      }} catch(e) {{ toast("❌ Erro ao reiniciar terminal.", "err"); }}
    }}

    window.addEventListener("load", () => {{
      fetch(BASE + "/api/apikey/apply", {{ method: "POST" }}).catch(() => {{}});
    }});
  </script>
</body>
</html>"""

    os.makedirs(WRAPPER_DIR, exist_ok=True)
    with open(os.path.join(WRAPPER_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)


def start_wrapper_server():
    _agentefo_drive = "/content/drive/My Drive/AgenteFO"
    _base = _agentefo_drive if os.path.isdir(_agentefo_drive) else _folder_path
    DRIVE_BACKUP_DIR = os.path.join(_base, "backups")
    os.makedirs(DRIVE_BACKUP_DIR, exist_ok=True)
    print(f"📁 Backup dir: {DRIVE_BACKUP_DIR}")

    OPENCODE_CONFIG_CANDIDATES = [
        os.path.expanduser("~/.config/opencode/auth.json"),
        os.path.expanduser("~/.config/opencode/config.json"),
        os.path.expanduser("~/.opencode/auth.json"),
        "/root/.config/opencode/auth.json",
        "/root/.opencode/auth.json",
    ]
    DRIVE_CONFIG_BACKUP = os.path.join(DRIVE_BACKUP_DIR, "opencode_auth.json")
    _keys_file = os.path.join(DRIVE_BACKUP_DIR, ".keys.json")

    def find_opencode_config():
        for p in OPENCODE_CONFIG_CANDIDATES:
            if os.path.exists(p):
                return p
        return None

    def restore_opencode_config():
        if not os.path.exists(DRIVE_CONFIG_BACKUP):
            return False
        restored = False
        for dest in OPENCODE_CONFIG_CANDIDATES:
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(DRIVE_CONFIG_BACKUP, dest)
                restored = True
            except Exception:
                pass
        return restored

    if restore_opencode_config():
        print("🔑 Config do OpenCode restaurada do Drive.")

    # Auto-load saved keys
    if os.path.exists(_keys_file):
        try:
            with open(_keys_file) as kf:
                saved = json.load(kf)
            loaded = []
            for k, v in saved.items():
                if k.startswith("_env_"):
                    continue
                env_var = saved.get(f"_env_{k}", "")
                if env_var and v:
                    os.environ[env_var] = v
                    _env[env_var] = v
                    loaded.append(env_var)
            if loaded:
                print(f"🔑 Keys carregadas: {', '.join(loaded)}")
        except Exception:
            pass

    def _run(cmd, **kw):
        return subprocess.run(cmd, capture_output=True, text=True, env=_env, **kw)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _json(self, code, data):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            p = urlparse(self.path).path

            if p in ("/", "/index.html"):
                fpath = os.path.join(WRAPPER_DIR, "index.html")
                with open(fpath, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if p == "/api/backups":
                try:
                    files = sorted(
                        [f for f in os.listdir(DRIVE_BACKUP_DIR)
                         if f.startswith("backup_") and f.endswith(".json")],
                        reverse=True
                    )
                except Exception:
                    files = []
                self._json(200, {"backups": files})
                return

            if p == "/api/apikey":
                qs = parse_qs(urlparse(self.path).query)
                provider = qs.get("provider", [""])[0].strip()
                try:
                    with open(_keys_file) as f:
                        keys = json.load(f)
                except Exception:
                    keys = {}
                if provider:
                    self._json(200, {"apikey": keys.get(provider, "")})
                else:
                    self._json(200, {"keys": keys})
                return

            self.send_error(404)

        def do_POST(self):
            p = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}

            if p == "/api/apikey":
                provider = body.get("provider", "").strip()
                env_var  = body.get("env", "").strip()
                key      = body.get("apikey", "").strip()
                if not key or not provider:
                    self._json(400, {"error": "provider e apikey obrigatórios."})
                    return
                try:
                    try:
                        with open(_keys_file) as f:
                            keys = json.load(f)
                    except Exception:
                        keys = {}
                    keys[provider] = key
                    if env_var:
                        keys[f"_env_{provider}"] = env_var
                    with open(_keys_file, "w") as f:
                        json.dump(keys, f, indent=2)
                except Exception as e:
                    self._json(500, {"error": str(e)})
                    return
                if env_var:
                    os.environ[env_var] = key
                    _env[env_var] = key
                # Persist in bashrc
                bashrc = os.path.expanduser("~/.bashrc")
                try:
                    marker = f"# agentefo-key-{provider}"
                    lines = open(bashrc).readlines() if os.path.exists(bashrc) else []
                    lines = [l for l in lines if marker not in l]
                    lines.append(f'export {env_var}="{key}"  {marker}\n')
                    open(bashrc, "w").writelines(lines)
                except Exception:
                    pass
                self._json(200, {"ok": True})
                return

            if p == "/api/apikey/apply":
                applied = []
                try:
                    with open(_keys_file) as f:
                        keys = json.load(f)
                    for k, v in keys.items():
                        if k.startswith("_env_"):
                            continue
                        env_var = keys.get(f"_env_{k}", "")
                        if env_var and v:
                            os.environ[env_var] = v
                            _env[env_var] = v
                            applied.append(env_var)
                    self._json(200, {"ok": True, "applied": applied})
                except Exception:
                    self._json(200, {"ok": False, "reason": "no keys stored"})
                return

            if p == "/api/run_terminal":
                cmd = body.get("command", "").strip()
                no_fallback = body.get("no_fallback", False)
                if not cmd:
                    self._json(400, {"error": "Comando vazio."})
                    return
                # Reload keys
                try:
                    with open(_keys_file) as f:
                        saved = json.load(f)
                    for k, v in saved.items():
                        if k.startswith("_env_"):
                            continue
                        ev = saved.get(f"_env_{k}", "")
                        if ev and v:
                            _env[ev] = v
                            os.environ[ev] = v
                except Exception:
                    pass
                subprocess.run(
                    "pkill -9 -f ttyd 2>/dev/null; pkill -9 -f opencode 2>/dev/null; true",
                    shell=True
                )
                time.sleep(1.5)
                bash_cmd = f"{cmd}; exec bash" if no_fallback else f"{cmd}; {_opencode_bin}; exec bash"
                subprocess.Popen(
                    ["ttyd", "--writable", "-p", str(TERMINAL_PORT),
                     "bash", "-i", "-c", bash_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=_env,
                )
                self._json(200, {"ok": True})
                return

            if p == "/api/backup":
                os.makedirs(DRIVE_BACKUP_DIR, exist_ok=True)
                session_id = body.get("session_id", "")
                ts = time.strftime("%H-%M-%S_%d-%m-%Y")
                if not session_id:
                    r = _run([_opencode_bin, "session", "list", "--format", "json"])
                    try:
                        sessions = json.loads(r.stdout)
                        session_id = sessions[0].get("id", "") if sessions else ""
                    except Exception:
                        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
                        session_id = lines[0] if lines else ""
                if not session_id:
                    self._json(400, {"error": "Nenhuma sessão encontrada."})
                    return
                fname = f"backup_{session_id[:12]}_{ts}.json"
                outpath = os.path.join(DRIVE_BACKUP_DIR, fname)
                r = _run([_opencode_bin, "export", session_id, "--format", outpath])
                if r.returncode != 0 or not os.path.exists(outpath):
                    r2 = _run([_opencode_bin, "export", session_id])
                    if r2.returncode == 0 and r2.stdout.strip():
                        with open(outpath, "w") as f:
                            f.write(r2.stdout)
                    else:
                        self._json(500, {"error": "Falha ao exportar sessão."})
                        return
                # Also backup opencode config
                src = find_opencode_config()
                if src:
                    shutil.copy2(src, DRIVE_CONFIG_BACKUP)
                self._json(200, {"ok": True, "file": fname, "session_id": session_id})
                return

            if p == "/api/restore":
                fname = body.get("file", "")
                if not fname:
                    self._json(400, {"error": "Nome do arquivo não informado."})
                    return
                fpath = os.path.join(DRIVE_BACKUP_DIR, fname)
                if not os.path.exists(fpath):
                    self._json(404, {"error": f"Arquivo não encontrado: {fname}"})
                    return
                r = _run([_opencode_bin, "import", fpath])
                if r.returncode != 0:
                    self._json(500, {"error": r.stderr.strip() or "Falha ao importar."})
                    return
                session_id = ""
                try:
                    import re
                    with open(fpath, "r", encoding="utf-8") as jf:
                        raw = jf.read(4096)
                    m = re.search(r'"id"\s*:\s*"(ses_[a-zA-Z0-9]+)"', raw)
                    if m:
                        session_id = m.group(1)
                except Exception:
                    pass
                self._json(200, {"ok": True, "file": fname, "session_id": session_id})
                return

            self.send_error(404)

    threading.Thread(
        target=lambda: HTTPServer(("0.0.0.0", WRAPPER_PORT), Handler).serve_forever(),
        daemon=True,
    ).start()
    print(f"🚀 Servidor wrapper iniciado na porta {WRAPPER_PORT}")


def show_ready_message():
    if not IN_COLAB or not display or not HTML:
        print("\n✨ AgenteFO pronto!\n")
        return
    display(HTML("""
<style>
@keyframes glow {
  0%,100% { box-shadow: 0 0 20px rgba(212,175,55,0.3); }
  50%      { box-shadow: 0 0 40px rgba(212,175,55,0.6); }
}
.ready-container { display:flex;flex-direction:column;align-items:center;padding:20px; }
.ready-badge {
  display:inline-flex;align-items:center;gap:12px;padding:16px 32px;
  background:rgba(212,175,55,0.10);border:2px solid rgba(212,175,55,0.35);
  border-radius:12px;animation:glow 2s ease-in-out infinite;
}
.ready-icon { font-size:28px; }
.ready-text { font-family:'DM Mono',monospace;font-size:18px;font-weight:600;color:#d4af37; }
</style>
<div class="ready-container">
  <div class="ready-badge">
    <span class="ready-icon">✨</span>
    <span class="ready-text">AgenteFO pronto!</span>
  </div>
</div>"""))


def show_launch_button(banner_url):
    if not IN_COLAB or not display or not HTML:
        print(f"\n🎉 Acesse: {banner_url}")
        return
    display(HTML(f"""
<style>
@keyframes pulse-glow {{
  0%,100% {{ box-shadow:0 0 20px rgba(212,175,55,0.3),0 4px 12px rgba(0,0,0,0.3); }}
  50%      {{ box-shadow:0 0 40px rgba(212,175,55,0.6),0 6px 20px rgba(0,0,0,0.4); }}
}}
.btn-container {{ display:flex;justify-content:center;padding:20px;margin-top:10px; }}
.fo-launch {{
  display:inline-flex;align-items:center;justify-content:center;gap:16px;
  padding:24px 56px;font-family:"Syne",sans-serif;font-size:22px;font-weight:800;
  letter-spacing:0.08em;color:#0c0b09;
  background:linear-gradient(135deg,#d4af37 0%,#f0c040 50%,#b8860b 100%);
  border:none;border-radius:14px;cursor:pointer;text-decoration:none;
  transition:all 0.2s ease;animation:pulse-glow 2.5s ease-in-out infinite;
  position:relative;overflow:hidden;
}}
.fo-launch::before {{
  content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);
  transition:left 0.5s;
}}
.fo-launch:hover::before {{ left:100%; }}
.fo-launch:hover {{ transform:translateY(-4px) scale(1.02);filter:brightness(1.1); }}
.fo-launch:active {{ transform:translateY(-1px) scale(0.99); }}
.btn-icon {{ font-size:28px; }}
.btn-text {{ display:flex;flex-direction:column;align-items:flex-start;gap:2px; }}
.btn-main {{ font-size:22px;font-weight:800; }}
.btn-sub  {{ font-family:"DM Mono",monospace;font-size:11px;font-weight:500;opacity:0.8;letter-spacing:0.1em; }}
.fo-launch .arrow {{ font-size:28px;transition:transform 0.2s ease; }}
.fo-launch:hover .arrow {{ transform:translateX(8px); }}
</style>
<div class="btn-container">
  <a href="{banner_url}" target="_blank" class="fo-launch">
    <span class="btn-icon">🧵</span>
    <span class="btn-text">
      <span class="btn-main">ABRIR O AGENTEFO</span>
      <span class="btn-sub">Fio de Ouro · Gestão Comercial</span>
    </span>
    <span class="arrow">→</span>
  </a>
</div>"""))


def launch():
    global _drive_url
    resolve_opencode()
    install_ttyd()
    kill_previous()
    start_ttyd()

    if IN_COLAB and output:
        terminal_url = output.eval_js(f"google.colab.kernel.proxyPort({TERMINAL_PORT})")
        banner_url   = output.eval_js(f"google.colab.kernel.proxyPort({WRAPPER_PORT})")
    else:
        terminal_url = f"http://localhost:{TERMINAL_PORT}"
        banner_url   = f"http://localhost:{WRAPPER_PORT}"

    create_wrapper_html(terminal_url, _drive_url)
    start_wrapper_server()

    time.sleep(1)
    show_ready_message()
    show_launch_button(banner_url)

    return banner_url


if __name__ == "__main__":
    launch()
