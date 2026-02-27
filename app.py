import os, json, sqlite3, bcrypt, stripe, ssl, gzip, urllib.request, urllib.parse, urllib.error
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory, Response
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "amazonsellertool2024xk9!")

PORT = int(os.environ.get("PORT", 8080))
DIR = os.path.dirname(os.path.abspath(__file__))

ADMIN_EMAIL = "profgiseleenf@gmail.com"
GMAIL_USER = os.environ.get("GMAIL_USER", "profgiseleenf@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_MONTHLY = os.environ.get("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_ANNUAL = os.environ.get("STRIPE_PRICE_ANNUAL", "")
BASE_URL = os.environ.get("BASE_URL", "https://amazon-seller-tool.onrender.com")

DB = os.path.join(DIR, "users.db")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                subscription_end TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Adiciona coluna status se nao existir (migracao)
        try:
            db.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'pending'")
        except Exception:
            pass
        db.commit()

init_db()

def send_email(to, subject, html_body):
    if not GMAIL_APP_PASSWORD:
        print(f"[EMAIL] Para: {to} | Assunto: {subject}")
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
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")

def notify_admin_new_user(user_id, name, email, plan, registered_at):
    approve_url = f"{BASE_URL}/admin/approve/{user_id}"
    reject_url  = f"{BASE_URL}/admin/reject/{user_id}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0d1527;color:#e0e0e0;border-radius:12px;padding:32px">
      <h2 style="color:#ff9900;margin-bottom:4px">Novo cadastro aguardando aprovacao</h2>
      <p style="color:#78909c;margin-bottom:24px">Amazon Seller Tool</p>
      <table style="width:100%;border-collapse:collapse;margin-bottom:28px">
        <tr><td style="padding:8px;color:#90caf9;width:120px">Nome</td><td style="padding:8px;color:#fff"><strong>{name}</strong></td></tr>
        <tr style="background:#1a2744"><td style="padding:8px;color:#90caf9">E-mail</td><td style="padding:8px;color:#fff">{email}</td></tr>
        <tr><td style="padding:8px;color:#90caf9">Plano</td><td style="padding:8px;color:#ff9900"><strong>{plan.upper()}</strong></td></tr>
        <tr style="background:#1a2744"><td style="padding:8px;color:#90caf9">Data</td><td style="padding:8px;color:#fff">{registered_at}</td></tr>
      </table>
      <div style="display:flex;gap:16px">
        <a href="{approve_url}" style="background:#2e7d32;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;display:inline-block">APROVAR ACESSO</a>
        <a href="{reject_url}" style="background:#b71c1c;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;display:inline-block;margin-left:12px">REJEITAR</a>
      </div>
    </div>"""
    send_email(ADMIN_EMAIL, f"[AmazonSellerTool] Novo usuario: {name} ({email})", html)

def notify_user_approved(name, email):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0d1527;color:#e0e0e0;border-radius:12px;padding:32px;text-align:center">
      <h2 style="color:#ff9900">Seu acesso foi aprovado!</h2>
      <p style="color:#b0bec5;margin:16px 0">Ola, <strong style="color:#fff">{name}</strong>! Sua conta foi aprovada com sucesso.</p>
      <a href="{BASE_URL}/login" style="background:#ff9900;color:#000;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;display:inline-block;margin-top:8px">Acessar agora</a>
    </div>"""
    send_email(email, "[AmazonSellerTool] Acesso aprovado!", html)

def notify_user_rejected(name, email):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0d1527;color:#e0e0e0;border-radius:12px;padding:32px;text-align:center">
      <h2 style="color:#ef9a9a">Cadastro nao aprovado</h2>
      <p style="color:#b0bec5;margin:16px 0">Ola, <strong style="color:#fff">{name}</strong>. Infelizmente seu cadastro nao foi aprovado.<br>Entre em contato: {ADMIN_EMAIL}</p>
    </div>"""
    send_email(email, "[AmazonSellerTool] Sobre seu cadastro", html)

# ── AUTH HELPERS ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def subscription_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not user:
            session.clear()
            return redirect(url_for("login_page"))
        if user["plan"] == "free":
            return redirect(url_for("pricing_page"))
        if user["subscription_end"]:
            end = datetime.fromisoformat(user["subscription_end"])
            if datetime.utcnow() > end:
                return redirect(url_for("pricing_page"))
        return f(*args, **kwargs)
    return decorated

# ── LANDING PAGE ──────────────────────────────────────────────────────────────
LANDING_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amazon Seller Tool — Encontre Produtos Lucrativos</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0}
nav{display:flex;justify-content:space-between;align-items:center;padding:16px 40px;background:#0d1527;border-bottom:1px solid #1e2d4a}
.logo{color:#ff9900;font-size:22px;font-weight:800;letter-spacing:1px}
.nav-links a{color:#90caf9;text-decoration:none;margin-left:24px;font-size:14px}
.nav-links a:hover{color:#fff}
.hero{text-align:center;padding:80px 20px 60px}
.hero h1{font-size:48px;font-weight:900;color:#fff;line-height:1.2;max-width:700px;margin:0 auto 20px}
.hero h1 span{color:#ff9900}
.hero p{font-size:18px;color:#90caf9;max-width:560px;margin:0 auto 40px}
.cta-btn{background:#ff9900;color:#000;padding:16px 40px;border-radius:8px;font-size:18px;font-weight:800;text-decoration:none;display:inline-block;transition:.2s}
.cta-btn:hover{background:#ffb347;transform:scale(1.04)}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;max-width:1100px;margin:0 auto;padding:0 20px 80px}
.feat{background:#0d1527;border:1px solid #1e2d4a;border-radius:12px;padding:28px;text-align:center}
.feat-icon{font-size:40px;margin-bottom:16px}
.feat h3{color:#fff;margin-bottom:8px;font-size:18px}
.feat p{color:#78909c;font-size:14px;line-height:1.6}
.pricing{max-width:900px;margin:0 auto;padding:0 20px 100px;text-align:center}
.pricing h2{font-size:36px;font-weight:800;color:#fff;margin-bottom:12px}
.pricing p{color:#78909c;margin-bottom:48px}
.plans{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.plan{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:36px;position:relative}
.plan.popular{border-color:#ff9900;box-shadow:0 0 30px rgba(255,153,0,.2)}
.popular-badge{position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#ff9900;color:#000;font-size:12px;font-weight:800;padding:4px 16px;border-radius:20px}
.plan h3{font-size:22px;font-weight:700;color:#fff;margin-bottom:8px}
.plan .price{font-size:48px;font-weight:900;color:#ff9900;margin:16px 0 4px}
.plan .price span{font-size:18px;color:#78909c}
.plan ul{list-style:none;text-align:left;margin:20px 0 32px}
.plan ul li{color:#b0bec5;padding:6px 0;font-size:14px}
.plan ul li::before{content:"✓ ";color:#ff9900;font-weight:700}
.plan-btn{display:block;width:100%;padding:14px;border-radius:8px;font-size:16px;font-weight:700;text-align:center;text-decoration:none;cursor:pointer;border:none;transition:.2s}
.plan-btn.primary{background:#ff9900;color:#000}
.plan-btn.primary:hover{background:#ffb347}
.plan-btn.secondary{background:transparent;color:#ff9900;border:2px solid #ff9900}
.plan-btn.secondary:hover{background:#ff990022}
@media(max-width:600px){.plans{grid-template-columns:1fr}.hero h1{font-size:32px}}
</style>
</head>
<body>
<nav>
  <div class="logo">&#9670; AmazonSellerTool</div>
  <div class="nav-links">
    <a href="#features">Recursos</a>
    <a href="#pricing">Planos</a>
    <a href="/login">Entrar</a>
    <a href="/register" style="background:#ff9900;color:#000;padding:8px 18px;border-radius:6px;font-weight:700">Comecar Gratis</a>
  </div>
</nav>

<section class="hero">
  <h1>Encontre produtos <span>lucrativos</span> para vender na Amazon</h1>
  <p>Analise qualquer produto de fornecedores, verifique elegibilidade, calcule taxas FBA e veja o lucro real antes de comprar.</p>
  <a href="/register" class="cta-btn">Testar Gratis por 7 Dias</a>
</section>

<section id="features">
  <div class="features">
    <div class="feat"><div class="feat-icon">🔍</div><h3>Busca por URL</h3><p>Cole a URL de qualquer fornecedor e encontramos o produto na Amazon automaticamente.</p></div>
    <div class="feat"><div class="feat-icon">📊</div><h3>Calculadora FBA</h3><p>Calcule taxas Amazon, custo de prep, frete e veja a margem e ROI real do produto.</p></div>
    <div class="feat"><div class="feat-icon">🏆</div><h3>Deal Score</h3><p>Score de 0 a 100 baseado em BSR, margem, competicao e alertas de IP/Hazmat.</p></div>
    <div class="feat"><div class="feat-icon">📈</div><h3>Grafico Keepa</h3><p>Historico de preco e rank do produto nos ultimos 12 meses.</p></div>
    <div class="feat"><div class="feat-icon">✅</div><h3>Verificar Elegibilidade</h3><p>Link direto para checar se voce pode vender o produto na sua conta Amazon.</p></div>
    <div class="feat"><div class="feat-icon">🏭</div><h3>Melhores Fornecedores</h3><p>Lista curada das principais distribuidoras USA para casa, jardim e pet.</p></div>
  </div>
</section>

<section id="pricing" class="pricing">
  <h2>Planos e Precos</h2>
  <p>Comece gratis por 7 dias. Cancele quando quiser.</p>
  <div class="plans">
    <div class="plan">
      <h3>Mensal</h3>
      <div class="price">$29<span>/mes</span></div>
      <ul>
        <li>Buscas ilimitadas</li>
        <li>Calculadora FBA completa</li>
        <li>Deal Score & Alertas</li>
        <li>Grafico Keepa</li>
        <li>Lista de fornecedores</li>
        <li>Suporte por email</li>
      </ul>
      <a href="/register?plan=monthly" class="plan-btn secondary">Assinar Mensal</a>
    </div>
    <div class="plan popular">
      <div class="popular-badge">MAIS POPULAR</div>
      <h3>Anual</h3>
      <div class="price">$19<span>/mes</span></div>
      <p style="color:#81c784;font-size:13px;margin-bottom:8px">Economize $120/ano · Cobrado $228/ano</p>
      <ul>
        <li>Tudo do plano Mensal</li>
        <li>2 meses gratis</li>
        <li>Prioridade no suporte</li>
        <li>Novos recursos primeiro</li>
        <li>Acesso a Prep Centers</li>
        <li>Relatorios exportaveis</li>
      </ul>
      <a href="/register?plan=annual" class="plan-btn primary">Assinar Anual</a>
    </div>
  </div>
</section>
</body>
</html>"""

LOGIN_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Entrar — Amazon Seller Tool</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:40px;width:100%;max-width:420px}
.logo{color:#ff9900;font-size:22px;font-weight:800;text-align:center;margin-bottom:28px}
h2{color:#fff;font-size:24px;text-align:center;margin-bottom:24px}
.field{margin-bottom:18px}
label{color:#90caf9;font-size:13px;display:block;margin-bottom:6px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #37474f;background:#0a0f1e;color:#e0e0e0;font-size:15px}
input:focus{outline:none;border-color:#ff9900}
.btn{width:100%;padding:14px;background:#ff9900;color:#000;border:none;border-radius:8px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.btn:hover{background:#ffb347}
.error{background:#b71c1c22;border:1px solid #b71c1c;color:#ef9a9a;padding:10px;border-radius:8px;font-size:13px;margin-bottom:16px}
.links{text-align:center;margin-top:20px;font-size:14px;color:#78909c}
.links a{color:#ff9900;text-decoration:none}
</style>
</head>
<body>
<div class="card">
  <div class="logo">&#9670; AmazonSellerTool</div>
  <h2>Entrar na sua conta</h2>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <div class="field"><label>E-mail</label><input type="email" name="email" required placeholder="seu@email.com"></div>
    <div class="field"><label>Senha</label><input type="password" name="password" required placeholder="Sua senha"></div>
    <button type="submit" class="btn">Entrar</button>
  </form>
  <div class="links">Nao tem conta? <a href="/register">Cadastre-se</a> &nbsp;|&nbsp; <a href="/">Inicio</a></div>
</div>
</body>
</html>"""

REGISTER_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cadastro — Amazon Seller Tool</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:40px;width:100%;max-width:440px}
.logo{color:#ff9900;font-size:22px;font-weight:800;text-align:center;margin-bottom:28px}
h2{color:#fff;font-size:24px;text-align:center;margin-bottom:8px}
.sub{color:#78909c;text-align:center;font-size:14px;margin-bottom:24px}
.field{margin-bottom:16px}
label{color:#90caf9;font-size:13px;display:block;margin-bottom:6px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #37474f;background:#0a0f1e;color:#e0e0e0;font-size:15px}
input:focus{outline:none;border-color:#ff9900}
.btn{width:100%;padding:14px;background:#ff9900;color:#000;border:none;border-radius:8px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.btn:hover{background:#ffb347}
.error{background:#b71c1c22;border:1px solid #b71c1c;color:#ef9a9a;padding:10px;border-radius:8px;font-size:13px;margin-bottom:16px}
.trial{background:#1b2a1b;border:1px solid #2e7d32;color:#81c784;padding:10px 14px;border-radius:8px;font-size:13px;margin-bottom:20px;text-align:center}
.links{text-align:center;margin-top:20px;font-size:14px;color:#78909c}
.links a{color:#ff9900;text-decoration:none}
</style>
</head>
<body>
<div class="card">
  <div class="logo">&#9670; AmazonSellerTool</div>
  <h2>Criar sua conta</h2>
  <div class="sub">Plano: <strong style="color:#ff9900">{{ plan_label }}</strong></div>
  <div class="trial">7 dias gratis — cancele quando quiser</div>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <input type="hidden" name="plan" value="{{ plan }}">
    <div class="field"><label>Nome completo</label><input type="text" name="name" required placeholder="Seu nome"></div>
    <div class="field"><label>E-mail</label><input type="email" name="email" required placeholder="seu@email.com"></div>
    <div class="field"><label>Senha</label><input type="password" name="password" required placeholder="Minimo 6 caracteres" minlength="6"></div>
    <button type="submit" class="btn">Continuar para Pagamento</button>
  </form>
  <div class="links">Ja tem conta? <a href="/login">Entrar</a> &nbsp;|&nbsp; <a href="/">Inicio</a></div>
</div>
</body>
</html>"""

PRICING_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Escolha seu plano — Amazon Seller Tool</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 20px}
h1{color:#fff;font-size:32px;font-weight:800;margin-bottom:8px;text-align:center}
p{color:#78909c;margin-bottom:40px;text-align:center}
.plans{display:grid;grid-template-columns:1fr 1fr;gap:24px;max-width:700px;width:100%}
.plan{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:32px;position:relative}
.plan.popular{border-color:#ff9900}
.popular-badge{position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#ff9900;color:#000;font-size:12px;font-weight:800;padding:4px 16px;border-radius:20px}
.plan h3{font-size:20px;color:#fff;margin-bottom:8px}
.plan .price{font-size:42px;font-weight:900;color:#ff9900;margin:12px 0 4px}
.plan .price span{font-size:16px;color:#78909c}
.plan ul{list-style:none;margin:16px 0 28px}
.plan ul li{color:#b0bec5;padding:5px 0;font-size:14px}
.plan ul li::before{content:"✓ ";color:#ff9900}
.plan-btn{display:block;width:100%;padding:13px;border-radius:8px;font-size:15px;font-weight:700;text-align:center;text-decoration:none;border:none;cursor:pointer;transition:.2s}
.plan-btn.primary{background:#ff9900;color:#000}
.plan-btn.secondary{background:transparent;color:#ff9900;border:2px solid #ff9900}
@media(max-width:600px){.plans{grid-template-columns:1fr}}
</style>
</head>
<body>
<h1>Escolha seu plano</h1>
<p>Sua assinatura expirou ou voce esta no plano gratuito.</p>
<div class="plans">
  <div class="plan">
    <h3>Mensal</h3>
    <div class="price">$29<span>/mes</span></div>
    <ul>
      <li>Buscas ilimitadas</li>
      <li>Calculadora FBA</li>
      <li>Deal Score</li>
      <li>Grafico Keepa</li>
    </ul>
    <form method="POST" action="/create-checkout"><input type="hidden" name="plan" value="monthly"><button type="submit" class="plan-btn secondary">Assinar Mensal</button></form>
  </div>
  <div class="plan popular">
    <div class="popular-badge">MAIS POPULAR</div>
    <h3>Anual</h3>
    <div class="price">$19<span>/mes</span></div>
    <p style="color:#81c784;font-size:12px;margin-bottom:4px">Economize $120/ano</p>
    <ul>
      <li>Tudo do mensal</li>
      <li>2 meses gratis</li>
      <li>Suporte prioritario</li>
      <li>Novos recursos</li>
    </ul>
    <form method="POST" action="/create-checkout"><input type="hidden" name="plan" value="annual"><button type="submit" class="plan-btn primary">Assinar Anual</button></form>
  </div>
</div>
</body>
</html>"""

PENDING_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aguardando aprovacao</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:48px 40px;width:100%;max-width:460px;text-align:center}
.icon{font-size:56px;margin-bottom:20px}
h2{color:#ff9900;font-size:26px;margin-bottom:12px}
p{color:#90caf9;line-height:1.7;margin-bottom:8px}
.sub{color:#546e7a;font-size:13px;margin-top:20px}
a{color:#ff9900;text-decoration:none}
</style>
</head>
<body>
<div class="card">
  <div class="icon">&#9203;</div>
  <h2>Cadastro enviado!</h2>
  <p>Ola, <strong style="color:#fff">{{ name }}</strong>!</p>
  <p>Seu cadastro foi recebido e esta aguardando <strong style="color:#ff9900">aprovacao manual</strong>.</p>
  <p>Voce recebera um e-mail assim que seu acesso for liberado.</p>
  <p class="sub">Duvidas? Fale com <a href="mailto:profgiseleenf@gmail.com">profgiseleenf@gmail.com</a></p>
</div>
</body>
</html>"""

# ── ROTAS ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(LANDING_HTML)

@app.route("/login", methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email","").lower().strip()
        password = request.form.get("password","")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return render_template_string(LOGIN_HTML, error="E-mail ou senha incorretos.")
        if user["status"] == "pending":
            return render_template_string(LOGIN_HTML, error="Seu cadastro esta aguardando aprovacao. Voce recebera um e-mail quando for aprovado.")
        if user["status"] == "rejected":
            return render_template_string(LOGIN_HTML, error="Seu cadastro nao foi aprovado. Entre em contato: " + ADMIN_EMAIL)
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("tool"))
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/register", methods=["GET","POST"])
def register_page():
    plan = request.args.get("plan", request.form.get("plan", "monthly"))
    plan_label = "Anual — $19/mes ($228/ano)" if plan == "annual" else "Mensal — $29/mes"
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").lower().strip()
        password = request.form.get("password","")
        if len(password) < 6:
            return render_template_string(REGISTER_HTML, error="Senha deve ter pelo menos 6 caracteres.", plan=plan, plan_label=plan_label)
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            with get_db() as db:
                db.execute("INSERT INTO users (name,email,password,plan,status) VALUES (?,?,?,'free','pending')", (name, email, pw_hash))
                db.commit()
                user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["pending_plan"] = plan
            # Notifica admin por e-mail
            notify_admin_new_user(user["id"], name, email, plan, user["created_at"])
        except sqlite3.IntegrityError:
            return render_template_string(REGISTER_HTML, error="Este e-mail ja esta cadastrado.", plan=plan, plan_label=plan_label)
        # Mostra pagina de aguardo
        return render_template_string(PENDING_HTML, name=name)
    return render_template_string(REGISTER_HTML, error=None, plan=plan, plan_label=plan_label)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/pricing")
@login_required
def pricing_page():
    return render_template_string(PRICING_HTML)

@app.route("/create-checkout", methods=["GET","POST"])
@login_required
def create_checkout():
    plan = request.form.get("plan") or request.args.get("plan", "monthly")
    if not stripe.api_key:
        with get_db() as db:
            end = (datetime.utcnow() + timedelta(days=30)).isoformat()
            db.execute("UPDATE users SET plan='active',subscription_end=? WHERE id=?", (end, session["user_id"]))
            db.commit()
        return redirect(url_for("tool"))
    price_id = STRIPE_PRICE_ANNUAL if plan == "annual" else STRIPE_PRICE_MONTHLY
    checkout = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=BASE_URL + "/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=BASE_URL + "/pricing",
        client_reference_id=str(session["user_id"]),
        subscription_data={"trial_period_days": 7},
    )
    return redirect(checkout.url)

@app.route("/success")
@login_required
def success():
    session_id = request.args.get("session_id")
    if session_id and stripe.api_key:
        try:
            cs = stripe.checkout.Session.retrieve(session_id)
            sub = stripe.Subscription.retrieve(cs.subscription)
            end = datetime.fromtimestamp(sub.current_period_end).isoformat()
            with get_db() as db:
                db.execute("UPDATE users SET plan='active',stripe_customer_id=?,stripe_subscription_id=?,subscription_end=? WHERE id=?",
                    (cs.customer, cs.subscription, end, session["user_id"]))
                db.commit()
        except Exception as e:
            print("Stripe error:", e)
    return redirect(url_for("tool"))

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature","")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return jsonify({"error": "invalid"}), 400
    if event["type"] == "invoice.paid":
        sub_id = event["data"]["object"]["subscription"]
        sub = stripe.Subscription.retrieve(sub_id)
        end = datetime.fromtimestamp(sub.current_period_end).isoformat()
        with get_db() as db:
            db.execute("UPDATE users SET plan='active',subscription_end=? WHERE stripe_subscription_id=?", (end, sub_id))
            db.commit()
    elif event["type"] in ("customer.subscription.deleted","customer.subscription.paused"):
        sub_id = event["data"]["object"]["id"]
        with get_db() as db:
            db.execute("UPDATE users SET plan='free' WHERE stripe_subscription_id=?", (sub_id,))
            db.commit()
    return jsonify({"status": "ok"})

@app.route("/tool")
@subscription_required
def tool():
    return send_from_directory(DIR, "amazon-asin-checker.html")

@app.route("/proxy")
@login_required
def proxy():
    url = request.args.get("url","")
    if not url:
        return jsonify({"error": "URL ausente"}), 400
    try:
        req = urllib.request.Request(url, headers=PROXY_HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding","") == "gzip":
                data = gzip.decompress(data)
        return Response(data, content_type="text/html; charset=utf-8", headers={"Access-Control-Allow-Origin":"*"})
    except urllib.error.HTTPError as e:
        blocked = e.code in (403, 503, 429)
        return jsonify({"error": f"BLOCKED:{e.code}", "blocked": blocked})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/admin/approve/<int:user_id>")
def admin_approve(user_id):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return "Usuario nao encontrado.", 404
        plan = session.get("pending_plan", "monthly")
        end = (datetime.utcnow() + timedelta(days=30)).isoformat()
        db.execute("UPDATE users SET status='approved',plan='active',subscription_end=? WHERE id=?", (end, user_id))
        db.commit()
    notify_user_approved(user["name"], user["email"])
    return f"""<html><body style="font-family:Arial;background:#0a0f1e;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
    <div style="text-align:center;background:#0d1527;padding:40px;border-radius:12px;border:1px solid #2e7d32">
    <h2 style="color:#81c784">Acesso APROVADO!</h2>
    <p style="color:#90caf9;margin:12px 0">Usuario: <strong>{user['name']}</strong> ({user['email']})</p>
    <p style="color:#546e7a;font-size:13px">E-mail de confirmacao enviado ao usuario.</p>
    </div></body></html>"""

@app.route("/admin/reject/<int:user_id>")
def admin_reject(user_id):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return "Usuario nao encontrado.", 404
        db.execute("UPDATE users SET status='rejected' WHERE id=?", (user_id,))
        db.commit()
    notify_user_rejected(user["name"], user["email"])
    return f"""<html><body style="font-family:Arial;background:#0a0f1e;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
    <div style="text-align:center;background:#0d1527;padding:40px;border-radius:12px;border:1px solid #b71c1c">
    <h2 style="color:#ef9a9a">Cadastro REJEITADO</h2>
    <p style="color:#90caf9;margin:12px 0">Usuario: <strong>{user['name']}</strong> ({user['email']})</p>
    <p style="color:#546e7a;font-size:13px">E-mail de notificacao enviado ao usuario.</p>
    </div></body></html>"""

if __name__ == "__main__":
    print(f"Servidor iniciado na porta {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
