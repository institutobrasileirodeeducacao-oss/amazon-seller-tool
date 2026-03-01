import os, json, sqlite3, ssl, gzip, urllib.request, urllib.parse, urllib.error, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory, Response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "amazonsellertool2024xk9!")

PORT = int(os.environ.get("PORT", 8080))
DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_EMAIL = "profgiseleenf@gmail.com"
GMAIL_USER = os.environ.get("GMAIL_USER", "profgiseleenf@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
BASE_URL = os.environ.get("BASE_URL", "https://amazon-seller-tool.onrender.com")

DB = os.path.join(DIR, "users.db")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# ── DATABASE ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                status TEXT DEFAULT 'pending',
                subscription_end TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

init_db()

# ── EMAIL ─────────────────────────────────────────────────────────────────────
def send_email(to, subject, html_body):
    if not GMAIL_APP_PASSWORD:
        print(f"[EMAIL-SEM-CONFIG] Para:{to} | {subject}")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.sendmail(GMAIL_USER, to, msg.as_string())
        print(f"[EMAIL-OK] Para:{to}")
    except Exception as e:
        print(f"[EMAIL-ERRO] {e}")

def notify_admin(user_id, name, email, plan, created_at):
    approve = f"{BASE_URL}/admin/approve/{user_id}"
    reject  = f"{BASE_URL}/admin/reject/{user_id}"
    html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;background:#0d1527;color:#e0e0e0;border-radius:12px;padding:32px">
<h2 style="color:#ff9900">Novo cadastro aguardando aprovacao</h2>
<table style="width:100%;margin:20px 0">
<tr><td style="color:#90caf9;padding:8px">Nome</td><td style="color:#fff;padding:8px"><b>{name}</b></td></tr>
<tr style="background:#1a2744"><td style="color:#90caf9;padding:8px">E-mail</td><td style="color:#fff;padding:8px">{email}</td></tr>
<tr><td style="color:#90caf9;padding:8px">Plano</td><td style="color:#ff9900;padding:8px"><b>{plan.upper()}</b></td></tr>
<tr style="background:#1a2744"><td style="color:#90caf9;padding:8px">Data</td><td style="color:#fff;padding:8px">{created_at}</td></tr>
</table>
<a href="{approve}" style="background:#2e7d32;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px">APROVAR ACESSO</a>
<a href="{reject}" style="background:#b71c1c;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;margin-left:12px">REJEITAR</a>
</div>"""
    send_email(ADMIN_EMAIL, f"[AmazonSellerTool] Novo usuario: {name}", html)

def notify_approved(name, email):
    html = f"""<div style="font-family:Arial;text-align:center;background:#0d1527;color:#e0e0e0;padding:40px;border-radius:12px">
<h2 style="color:#ff9900">Acesso Aprovado!</h2>
<p style="color:#b0bec5;margin:16px 0">Ola <b style="color:#fff">{name}</b>, seu acesso foi liberado!</p>
<a href="{BASE_URL}/login" style="background:#ff9900;color:#000;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px">Acessar Agora</a>
</div>"""
    send_email(email, "[AmazonSellerTool] Acesso aprovado!", html)

def notify_rejected(name, email):
    html = f"""<div style="font-family:Arial;text-align:center;background:#0d1527;color:#e0e0e0;padding:40px;border-radius:12px">
<h2 style="color:#ef9a9a">Cadastro nao aprovado</h2>
<p style="color:#b0bec5;margin:16px 0">Ola <b style="color:#fff">{name}</b>, seu cadastro nao foi aprovado.<br>Contato: {ADMIN_EMAIL}</p>
</div>"""
    send_email(email, "[AmazonSellerTool] Sobre seu cadastro", html)

# ── AUTH ──────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def active_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not user or user["status"] != "approved":
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

# ── HTML PAGES ────────────────────────────────────────────────────────────────
LANDING = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amazon Seller Tool</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0}
nav{display:flex;justify-content:space-between;align-items:center;padding:16px 40px;background:#0d1527;border-bottom:1px solid #1e2d4a}
.logo{color:#ff9900;font-size:22px;font-weight:800}.nav-links a{color:#90caf9;text-decoration:none;margin-left:20px;font-size:14px}
.hero{text-align:center;padding:80px 20px 60px}.hero h1{font-size:46px;font-weight:900;color:#fff;max-width:680px;margin:0 auto 20px;line-height:1.2}
.hero h1 span{color:#ff9900}.hero p{font-size:18px;color:#90caf9;max-width:540px;margin:0 auto 40px}
.cta{background:#ff9900;color:#000;padding:16px 40px;border-radius:8px;font-size:18px;font-weight:800;text-decoration:none;display:inline-block}
.cta:hover{background:#ffb347}.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;max-width:1100px;margin:0 auto;padding:0 20px 80px}
.feat{background:#0d1527;border:1px solid #1e2d4a;border-radius:12px;padding:28px;text-align:center}
.feat-icon{font-size:38px;margin-bottom:14px}.feat h3{color:#fff;margin-bottom:8px}.feat p{color:#78909c;font-size:13px;line-height:1.6}
.plans{display:grid;grid-template-columns:1fr 1fr;gap:24px;max-width:800px;margin:0 auto;padding:0 20px 100px}
.plan{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:36px;position:relative}
.plan.pop{border-color:#ff9900}.badge{position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#ff9900;color:#000;font-size:11px;font-weight:800;padding:4px 14px;border-radius:20px}
.plan h3{font-size:20px;color:#fff;margin-bottom:8px}.price{font-size:46px;font-weight:900;color:#ff9900;margin:14px 0 4px}
.price span{font-size:16px;color:#78909c}.plan ul{list-style:none;margin:16px 0 28px}.plan ul li{color:#b0bec5;padding:5px 0;font-size:14px}
.plan ul li::before{content:"✓ ";color:#ff9900}.pbtn{display:block;width:100%;padding:13px;border-radius:8px;font-size:15px;font-weight:700;text-align:center;text-decoration:none;border:none;cursor:pointer}
.pbtn.p{background:#ff9900;color:#000}.pbtn.s{background:transparent;color:#ff9900;border:2px solid #ff9900}
.sec-title{text-align:center;font-size:34px;font-weight:800;color:#fff;margin-bottom:10px;padding-top:60px}
.sec-sub{text-align:center;color:#78909c;margin-bottom:48px}
@media(max-width:600px){.plans{grid-template-columns:1fr}.hero h1{font-size:30px}}</style></head><body>
<nav><div class="logo">&#9670; AmazonSellerTool</div>
<div class="nav-links"><a href="#features">Recursos</a><a href="#pricing">Planos</a><a href="/login">Entrar</a>
<a href="/register" style="background:#ff9900;color:#000;padding:8px 16px;border-radius:6px;font-weight:700">Cadastrar</a></div></nav>
<section class="hero">
  <h1>Encontre produtos <span>lucrativos</span> para vender na Amazon</h1>
  <p>Analise produtos de fornecedores, verifique elegibilidade, calcule taxas FBA e veja o lucro real antes de comprar.</p>
  <a href="/register" class="cta">Comecar Agora</a>
</section>
<section id="features"><div class="features">
  <div class="feat"><div class="feat-icon">🔍</div><h3>Busca por URL</h3><p>Cole a URL de qualquer fornecedor e encontramos o produto na Amazon automaticamente.</p></div>
  <div class="feat"><div class="feat-icon">📊</div><h3>Calculadora FBA</h3><p>Calcule taxas, custo de prep, frete e veja margem e ROI real do produto.</p></div>
  <div class="feat"><div class="feat-icon">🏆</div><h3>Deal Score</h3><p>Score de 0 a 100 baseado em BSR, margem, competicao e alertas IP/Hazmat.</p></div>
  <div class="feat"><div class="feat-icon">📈</div><h3>Grafico Keepa</h3><p>Historico de preco e rank do produto nos ultimos 12 meses.</p></div>
  <div class="feat"><div class="feat-icon">✅</div><h3>Elegibilidade</h3><p>Link direto para checar se voce pode vender na sua conta Amazon.</p></div>
  <div class="feat"><div class="feat-icon">🏭</div><h3>Fornecedores USA</h3><p>Lista curada das melhores distribuidoras para casa, jardim e pet.</p></div>
</div></section>
<h2 class="sec-title" id="pricing">Planos e Precos</h2>
<p class="sec-sub">Acesso liberado apos aprovacao manual.</p>
<div class="plans">
  <div class="plan"><h3>Mensal</h3><div class="price">$29<span>/mes</span></div>
    <ul><li>Buscas ilimitadas</li><li>Calculadora FBA completa</li><li>Deal Score & Alertas</li><li>Grafico Keepa</li><li>Lista de fornecedores</li></ul>
    <a href="/register?plan=monthly" class="pbtn s">Assinar Mensal</a></div>
  <div class="plan pop"><div class="badge">MAIS POPULAR</div><h3>Anual</h3><div class="price">$19<span>/mes</span></div>
    <p style="color:#81c784;font-size:12px;margin-bottom:8px">Economize $120/ano · $228 cobrado anualmente</p>
    <ul><li>Tudo do mensal</li><li>2 meses gratis</li><li>Suporte prioritario</li><li>Novos recursos primeiro</li></ul>
    <a href="/register?plan=annual" class="pbtn p">Assinar Anual</a></div>
</div></body></html>"""

LOGIN_PAGE = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Entrar</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:40px;width:100%;max-width:420px}
.logo{color:#ff9900;font-size:22px;font-weight:800;text-align:center;margin-bottom:28px}h2{color:#fff;font-size:24px;text-align:center;margin-bottom:24px}
.field{margin-bottom:16px}label{color:#90caf9;font-size:13px;display:block;margin-bottom:5px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #37474f;background:#0a0f1e;color:#e0e0e0;font-size:15px}
input:focus{outline:none;border-color:#ff9900}.btn{width:100%;padding:14px;background:#ff9900;color:#000;border:none;border-radius:8px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.btn:hover{background:#ffb347}.error{background:#b71c1c22;border:1px solid #b71c1c;color:#ef9a9a;padding:10px;border-radius:8px;font-size:13px;margin-bottom:16px}
.links{text-align:center;margin-top:20px;font-size:14px;color:#78909c}.links a{color:#ff9900;text-decoration:none}</style></head><body>
<div class="card"><div class="logo">&#9670; AmazonSellerTool</div><h2>Entrar na sua conta</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="POST">
  <div class="field"><label>E-mail</label><input type="email" name="email" required placeholder="seu@email.com"></div>
  <div class="field"><label>Senha</label><input type="password" name="password" required placeholder="Sua senha"></div>
  <button type="submit" class="btn">Entrar</button>
</form>
<div class="links">Sem conta? <a href="/register">Cadastre-se</a> &nbsp;|&nbsp; <a href="/">Inicio</a></div>
</div></body></html>"""

REGISTER_PAGE = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cadastro</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:40px;width:100%;max-width:440px}
.logo{color:#ff9900;font-size:22px;font-weight:800;text-align:center;margin-bottom:20px}h2{color:#fff;font-size:22px;text-align:center;margin-bottom:6px}
.sub{color:#78909c;text-align:center;font-size:14px;margin-bottom:20px}
.trial{background:#1b2a1b;border:1px solid #2e7d32;color:#81c784;padding:10px;border-radius:8px;font-size:13px;margin-bottom:18px;text-align:center}
.field{margin-bottom:16px}label{color:#90caf9;font-size:13px;display:block;margin-bottom:5px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #37474f;background:#0a0f1e;color:#e0e0e0;font-size:15px}
input:focus{outline:none;border-color:#ff9900}.btn{width:100%;padding:14px;background:#ff9900;color:#000;border:none;border-radius:8px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.error{background:#b71c1c22;border:1px solid #b71c1c;color:#ef9a9a;padding:10px;border-radius:8px;font-size:13px;margin-bottom:16px}
.links{text-align:center;margin-top:20px;font-size:14px;color:#78909c}.links a{color:#ff9900;text-decoration:none}</style></head><body>
<div class="card"><div class="logo">&#9670; AmazonSellerTool</div>
<h2>Criar sua conta</h2><p class="sub">Plano: <strong style="color:#ff9900">{{ plan_label }}</strong></p>
<div class="trial">Acesso liberado apos aprovacao manual</div>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="POST"><input type="hidden" name="plan" value="{{ plan }}">
  <div class="field"><label>Nome completo</label><input type="text" name="name" required placeholder="Seu nome"></div>
  <div class="field"><label>E-mail</label><input type="email" name="email" required placeholder="seu@email.com"></div>
  <div class="field"><label>Senha</label><input type="password" name="password" required placeholder="Minimo 6 caracteres" minlength="6"></div>
  <button type="submit" class="btn">Enviar Cadastro</button>
</form>
<div class="links">Ja tem conta? <a href="/login">Entrar</a> &nbsp;|&nbsp; <a href="/">Inicio</a></div>
</div></body></html>"""

PENDING_PAGE = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Aguardando aprovacao</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:48px;max-width:460px;text-align:center}
.icon{font-size:54px;margin-bottom:20px}h2{color:#ff9900;font-size:24px;margin-bottom:12px}p{color:#90caf9;line-height:1.7;margin-bottom:8px}
.sub{color:#546e7a;font-size:13px;margin-top:16px}a{color:#ff9900;text-decoration:none}</style></head><body>
<div class="card"><div class="icon">&#9203;</div><h2>Cadastro Recebido!</h2>
<p>Ola, <strong style="color:#fff">{{ name }}</strong>!</p>
<p>Seu cadastro esta <strong style="color:#ff9900">aguardando aprovacao manual</strong>.</p>
<p>Voce recebera um e-mail quando seu acesso for liberado.</p>
<p class="sub">Duvidas? <a href="mailto:profgiseleenf@gmail.com">profgiseleenf@gmail.com</a></p>
</div></body></html>"""

# ── ROTAS ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(LANDING)

@app.route("/login", methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email","").lower().strip()
        password = request.form.get("password","")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user or not check_password_hash(user["password"], password):
            return render_template_string(LOGIN_PAGE, error="E-mail ou senha incorretos.")
        if user["status"] == "pending":
            return render_template_string(LOGIN_PAGE, error="Seu cadastro esta aguardando aprovacao. Aguarde o e-mail de confirmacao.")
        if user["status"] == "rejected":
            return render_template_string(LOGIN_PAGE, error=f"Seu cadastro nao foi aprovado. Contato: {ADMIN_EMAIL}")
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("tool"))
    return render_template_string(LOGIN_PAGE, error=None)

@app.route("/register", methods=["GET","POST"])
def register_page():
    plan = request.args.get("plan", "monthly")
    plan_label = "Anual — $19/mes" if plan == "annual" else "Mensal — $29/mes"
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").lower().strip()
        password = request.form.get("password","")
        plan = request.form.get("plan","monthly")
        plan_label = "Anual — $19/mes" if plan == "annual" else "Mensal — $29/mes"
        if len(password) < 6:
            return render_template_string(REGISTER_PAGE, error="Senha deve ter pelo menos 6 caracteres.", plan=plan, plan_label=plan_label)
        pw_hash = generate_password_hash(password)
        try:
            with get_db() as db:
                db.execute("INSERT INTO users (name,email,password,plan,status) VALUES (?,?,?,'free','pending')", (name, email, pw_hash))
                db.commit()
                user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            notify_admin(user["id"], name, email, plan, user["created_at"])
        except sqlite3.IntegrityError:
            return render_template_string(REGISTER_PAGE, error="Este e-mail ja esta cadastrado.", plan=plan, plan_label=plan_label)
        return render_template_string(PENDING_PAGE, name=name)
    return render_template_string(REGISTER_PAGE, error=None, plan=plan, plan_label=plan_label)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin/approve/<int:uid>")
def admin_approve(uid):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        if not user:
            return "Usuario nao encontrado.", 404
        end = (datetime.utcnow() + timedelta(days=365)).isoformat()
        db.execute("UPDATE users SET status='approved',plan='active',subscription_end=? WHERE id=?", (end, uid))
        db.commit()
    notify_approved(user["name"], user["email"])
    return f"""<html><body style="font-family:Arial;background:#0a0f1e;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="background:#0d1527;padding:40px;border-radius:12px;border:1px solid #2e7d32;text-align:center">
<h2 style="color:#81c784">Acesso APROVADO!</h2>
<p style="color:#90caf9;margin:12px 0"><b>{user['name']}</b> ({user['email']})</p>
<p style="color:#546e7a;font-size:13px">E-mail enviado ao usuario.</p>
</div></body></html>"""

@app.route("/admin/reject/<int:uid>")
def admin_reject(uid):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        if not user:
            return "Usuario nao encontrado.", 404
        db.execute("UPDATE users SET status='rejected' WHERE id=?", (uid,))
        db.commit()
    notify_rejected(user["name"], user["email"])
    return f"""<html><body style="font-family:Arial;background:#0a0f1e;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="background:#0d1527;padding:40px;border-radius:12px;border:1px solid #b71c1c;text-align:center">
<h2 style="color:#ef9a9a">Cadastro REJEITADO</h2>
<p style="color:#90caf9;margin:12px 0"><b>{user['name']}</b> ({user['email']})</p>
</div></body></html>"""

@app.route("/tool")
@active_required
def tool():
    return send_from_directory(DIR, "amazon-asin-checker.html")

@app.route("/proxy")
@active_required
def proxy():
    url = request.args.get("url","")
    if not url:
        return jsonify({"error":"URL ausente"}), 400
    try:
        req = urllib.request.Request(url, headers=PROXY_HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding","") == "gzip":
                data = gzip.decompress(data)
        return Response(data, content_type="text/html; charset=utf-8", headers={"Access-Control-Allow-Origin":"*"})
    except urllib.error.HTTPError as e:
        return jsonify({"error":f"BLOCKED:{e.code}","blocked": e.code in (403,503,429)})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    print(f"Servidor na porta {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
