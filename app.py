import os, json
from datetime import datetime, timedelta
from flask import Flask, request, redirect, render_template_string, session, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "innercircle-wuse2-final-v3"
DB_FILE = "/tmp/db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "messages": [], "circles": {}, "moments": []}
    try:
        import json as js
        with open(DB_FILE, "r") as f:
            return js.load(f)
    except:
        return {"users": {}, "messages": [], "circles": {}, "moments": []}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

PAGE = """
<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Inner Circle</title>
<link rel="icon" href="/icon.png"><link rel="apple-touch-icon" href="/icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#000000">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto}
body{background:#000;color:#fff;min-height:100vh}
.top{position:sticky;top:0;background:#000;border-bottom:1px solid #222;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;z-index:10}
.logo{font-weight:800;font-size:22px;letter-spacing:-1px}
.btn{background:#fff;color:#000;border:0;padding:10px 16px;border-radius:20px;font-weight:700;cursor:pointer}
.card{background:#111;border:1px solid #222;border-radius:16px;padding:12px;margin:10px 0}
.avatar{width:40px;height:40px;border-radius:50%;background:#333;display:flex;align-items:center;justify-content:center;font-weight:700;overflow:hidden}
.avatar img{width:100%;height:100%;object-fit:cover}
.dot{width:10px;height:10px;border-radius:50%;position:absolute;bottom:0;right:0;border:2px solid #000}
.online{background:#00ff66}.offline{background:#555}
input,textarea{width:100%;background:#111;border:1px solid #333;color:#fff;padding:12px;border-radius:12px;margin:6px 0}
.nav{position:fixed;bottom:0;left:0;right:0;background:#000;border-top:1px solid #222;display:flex;justify-content:space-around;padding:10px 0}
.nav a{color:#777;text-decoration:none;font-size:22px}.nav a.active{color:#fff}
.msg{max-width:70%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:15px}
.me{background:#fff;color:#000;margin-left:auto;border-bottom-right-radius:4px}
.them{background:#222;color:#fff;border-bottom-left-radius:4px}
.tick{font-size:11px;opacity:.7}
</style></head><body>
<div class="top"><div class="logo">inner.circle</div>
{% if me %}<div style="display:flex;gap:10px;align-items:center"><div style="position:relative"><div class="avatar">{% if me.photo %}<img src="{{me.photo}}">{% else %}{{me.name[0]}}{% endif %}</div><div class="dot online"></div></div><a href="/logout" style="color:#777;text-decoration:none">Logout</a></div>{% endif %}</div>
<div style="padding:16px;padding-bottom:80px;max-width:500px;margin:auto">{{content|safe}}</div>
{% if me %}<div class="nav"><a href="/" class="{{'active' if tab=='home'}}">⌂</a><a href="/circles" class="{{'active' if tab=='circles'}}">◍</a><a href="/moments" class="{{'active' if tab=='moments'}}">♡</a><a href="/profile" class="{{'active' if tab=='profile'}}">☺</a></div>{% endif %}
<script>setInterval(()=>{fetch('/ping',{method:'POST'})},30000);</script>
</body></html>
"""

@app.route("/icon.png")
def icon():
    # Minimal black circle with white i - SVG converted to PNG-like SVG response for PWA
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" rx="120" fill="#000"/><circle cx="256" cy="256" r="160" fill="none" stroke="white" stroke-width="6"/><text x="256" y="340" font-family="Georgia" font-size="210" fill="white" text-anchor="middle" font-weight="700">i</text></svg>'''
    return Response(svg, mimetype="image/svg+xml")

@app.route("/manifest.json")
def manifest():
    return jsonify({"name":"Inner Circle","short_name":"inner.circle","start_url":"/","display":"standalone","background_color":"#000000","theme_color":"#000000","icons":[{"src":"/icon.png","sizes":"512x512","type":"image/svg+xml"}]})

@app.route("/sw.js")
def sw(): return "self.addEventListener('fetch', e=>{});", 200, {'Content-Type':'application/javascript'}

@app.route("/ping", methods=["POST"])
def ping():
    if "user" not in session: return ""
    db=load_db(); u=db["users"].get(session["user"])
    if u: u["last_seen"]=datetime.utcnow().isoformat(); save_db(db)
    return ""

def is_online(s):
    try:
        from datetime import datetime as dt
        t=dt.fromisoformat(s); return dt.utcnow()-t < timedelta(minutes=2)
    except: return False

@app.route("/")
def home():
    if "user" not in session: return render_template_string(PAGE, content="""
    <h1 style="font-size:42px;line-height:0.9;margin:20px 0">Your<br>Inner<br>Circle.</h1>
    <p style="color:#888;margin-bottom:20px">Private social for Wuse 2. No algorithm. Just your people.</p>
    <form method="post" action="/login"><input name="username" placeholder="Username"><input name="password" type="password" placeholder="Password"><button class="btn" style="width:100%;margin-top:10px">Login</button></form>
    <div style="text-align:center;margin-top:16px"><a href="/signup" style="color:#fff">Create account</a></div>
    """, me=None, tab="home")
    db=load_db(); me=db["users"][session["user"]]
    html="<h3>People — 🟢 online now</h3>"
    for uid,u in db["users"].items():
        if uid==session["user"]: continue
        online=is_online(u.get("last_seen",""))
        photo=f'<img src="{u.get("photo","")}">' if u.get('photo') else u['name'][0]
        html+=f"""<div class="card" style="display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;gap:10px;align-items:center"><div style="position:relative"><div class="avatar">{photo}</div><div class="dot {'online' if online else 'offline'}"></div></div>
        <div><b>{u['name']}</b><br><small style="color:{'#0f6' if online else '#666'}">{'online • Wuse 2' if online else 'offline'}</small></div></div>
        <a href="/chat/{uid}" class="btn">Chat</a></div>"""
    return render_template_string(PAGE, content=html, me=me, tab="home")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        db=load_db(); uname=request.form["username"].lower()
        if uname in db["users"]: return "Taken <a href=/signup>back</a>"
        db["users"][uname]={"name":request.form["name"],"username":uname,"password":generate_password_hash(request.form["password"]),"photo":"","last_seen":datetime.utcnow().isoformat()}
        save_db(db); session["user"]=uname; session.permanent=True; return redirect("/")
    return render_template_string(PAGE, content="""<h2>Join</h2><form method="post"><input name="name" placeholder="Full Name" required><input name="username" placeholder="username" required><input name="password" type="password" placeholder="Password" required><button class="btn" style="width:100%">Create</button></form>""", me=None, tab="home")

@app.route("/login", methods=["POST"])
def login():
    db=load_db(); u=db["users"].get(request.form["username"].lower())
    if u and check_password_hash(u["password"], request.form["password"]):
        session["user"]=u["username"]; session.permanent=True; u["last_seen"]=datetime.utcnow().isoformat(); save_db(db); return redirect("/")
    return "Wrong <a href=/>back</a>"

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    if request.method=="POST":
        if "photo" in request.files and request.files["photo"].filename!="":
            f=request.files["photo"]; data=f.read()
            import base64; b64=base64.b64encode(data).decode()
            me["photo"]=f"data:{f.mimetype};base64,{b64}"
        if request.form.get("name"): me["name"]=request.form["name"]
        save_db(db); return redirect("/profile")
    pic=f'<img src="{me.get("photo","")}">' if me.get('photo') else me['name'][0]
    return render_template_string(PAGE, content=f"""
    <h2>Profile</h2><div class="card" style="text-align:center"><div class="avatar" style="width:80px;height:80px;margin:auto;font-size:30px">{pic}</div><h3 style="margin-top:10px">{me['name']}</h3><small>@{me['username']}</small></div>
    <form method="post" enctype="multipart/form-data"><input name="name" value="{me['name']}"><input type="file" name="photo" accept="image/*"><button class="btn" style="width:100%">Save ✓ Photo saves permanently</button></form>
    <p style="color:#666;font-size:12px;margin-top:12px">Add to Home Screen: Share > Add to Home Screen. Now your icon will be this new i logo.</p>
    """, me=me, tab="profile")

@app.route("/chat/<uid>")
def chat(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]; other=db["users"].get(uid)
    if not other: return "Not found"
    for m in db["messages"]:
        if m["to"]==session["user"] and m["from"]==uid: m["read"]=True
    save_db(db)
    msgs=[m for m in db["messages"] if (m["from"]==session["user"] and m["to"]==uid) or (m["from"]==uid and m["to"]==session["user"])]
    html=f"<a href='/'>‹ Back</a><h3 style='margin:10px 0'>{other['name']} {'🟢' if is_online(other.get('last_seen','')) else '⚪'}</h3><div>"
    for m in msgs[-50:]:
        who="me" if m["from"]==session["user"] else "them"
        tick="✓✓" if m.get("read") else "✓" if who=="me" else ""
        html+=f"<div class='msg {who}'>{m['text']}<br><span class='tick'>{tick} {m['time'][11:16]}</span></div>"
    html+=f"</div><form method='post' action='/send/{uid}' style='display:flex;gap:8px;margin-top:12px'><input name='text' placeholder='Message...' required style='flex:1'><button class='btn'>Send</button></form>"
    return render_template_string(PAGE, content=html, me=me, tab="home")

@app.route("/send/<uid>", methods=["POST"])
def send(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); db["messages"].append({"from":session["user"],"to":uid,"text":request.form["text"],"time":datetime.utcnow().isoformat(),"read":False}); save_db(db); return redirect(f"/chat/{uid}")

@app.route("/circles")
def circles():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]; html="<h3>Your Circles</h3><form method='post' action='/create_circle' style='display:flex;gap:8px'><input name='name' placeholder='New Circle (e.g. Wuse 2 Boys)' required><button class='btn'>Create</button></form>"
    for cid,c in db["circles"].items():
        if session["user"] in c["members"]: html+=f"<div class='card'><b>{c['name']}</b><br><small>{len(c['members'])} members</small></div>"
    return render_template_string(PAGE, content=html, me=me, tab="circles")

@app.route("/create_circle", methods=["POST"])
def create_circle():
    db=load_db(); cid=str(len(db["circles"])+1); db["circles"][cid]={"name":request.form["name"],"members":[session["user"]]}; save_db(db); return redirect("/circles")

@app.route("/moments", methods=["GET","POST"])
def moments():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    if request.method=="POST":
        db["moments"].insert(0,{"user":session["user"],"text":request.form["text"],"time":datetime.utcnow().isoformat()}); save_db(db); return redirect("/moments")
    html="<h3>Moments</h3><form method='post'><textarea name='text' placeholder=\"What's happening?\" required></textarea><button class='btn' style='width:100%'>Post</button></form>"
    for m in db["moments"][:20]:
        u=db["users"].get(m["user"],{"name":m["user"]}); html+=f"<div class='card'><b>{u['name']}</b> <small style='color:#666'>@{m['user']} • {m['time'][11:16]}</small><p style='margin-top:8px'>{m['text']}</p></div>"
    return render_template_string(PAGE, content=html, me=me, tab="moments")

if __name__=="__main__": app.run()
