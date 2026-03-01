import os, ssl, gzip, urllib.request, urllib.parse, urllib.error
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory, Response

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "amazonsellertool2024xk9!")

PORT = int(os.environ.get("PORT", 8080))
DIR  = os.path.dirname(os.path.abspath(__file__))

# ── CREDENCIAIS DE ACESSO ─────────────────────────────────────────────────────
ACCESS_USER     = os.environ.get("ACCESS_USER", "gisele")
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "Amazon2024!")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode    = ssl.CERT_NONE

PROXY_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection":      "keep-alive",
}

# ── LOGIN PAGE ────────────────────────────────────────────────────────────────
LOGIN_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amazon Seller Tool — Login</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Segoe UI',sans-serif;background:#0a0f1e;min-height:100vh;display:flex;align-items:center;justify-content:center}
  .card{background:#0d1527;border:1px solid #1e2d4a;border-radius:16px;padding:48px 40px;width:100%;max-width:400px}
  .logo{color:#ff9900;font-size:26px;font-weight:900;text-align:center;margin-bottom:8px;letter-spacing:1px}
  .sub{color:#546e7a;text-align:center;font-size:13px;margin-bottom:32px}
  label{color:#90caf9;font-size:13px;display:block;margin-bottom:6px}
  input{width:100%;padding:12px 14px;border-radius:8px;border:1px solid #37474f;background:#0a0f1e;color:#e0e0e0;font-size:15px;margin-bottom:18px}
  input:focus{outline:none;border-color:#ff9900}
  .btn{width:100%;padding:14px;background:#ff9900;color:#000;border:none;border-radius:8px;font-size:17px;font-weight:800;cursor:pointer;letter-spacing:.5px}
  .btn:hover{background:#ffb347}
  .error{background:#b71c1c22;border:1px solid #b71c1c55;color:#ef9a9a;padding:11px 14px;border-radius:8px;font-size:13px;margin-bottom:18px;text-align:center}
</style>
</head>
<body>
<div class="card">
  <div class="logo">&#9670; AmazonSellerTool</div>
  <p class="sub">Ferramenta de analise para vendedores Amazon</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <label>Usuario</label>
    <input type="text" name="username" required autofocus placeholder="Seu usuario">
    <label>Senha</label>
    <input type="password" name="password" required placeholder="Sua senha">
    <button type="submit" class="btn">Entrar</button>
  </form>
</div>
</body>
</html>"""

# ── ROTAS ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","")
        if u == ACCESS_USER and p == ACCESS_PASSWORD:
            session["ok"] = True
            return redirect(url_for("tool"))
        return render_template_string(LOGIN_HTML, error="Usuario ou senha incorretos.")
    if session.get("ok"):
        return redirect(url_for("tool"))
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/tool")
def tool():
    if not session.get("ok"):
        return redirect(url_for("login"))
    return send_from_directory(DIR, "amazon-asin-checker.html")

@app.route("/proxy")
def proxy():
    if not session.get("ok"):
        return jsonify({"error": "nao autorizado"}), 401
    url = request.args.get("url","")
    if not url:
        return jsonify({"error":"URL ausente"}), 400
    try:
        req = urllib.request.Request(url, headers=PROXY_HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding","") == "gzip":
                data = gzip.decompress(data)
        return Response(data, content_type="text/html; charset=utf-8",
                        headers={"Access-Control-Allow-Origin":"*"})
    except urllib.error.HTTPError as e:
        return jsonify({"error": f"BLOCKED:{e.code}", "blocked": e.code in (403,503,429)})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    print(f"Servidor na porta {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
