import os, json
from datetime import datetime, timedelta
from flask import Flask, request, redirect, render_template_string, session, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "innercircle-wuse2-hybrid-v4"
DB_FILE = "/tmp/db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "messages": [], "circles": {}, "moments": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
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
*{margin:0;padding:0;box-sizing:border-box;font-family:Inter,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto}
body{background:#fafafa;color:#000;min-height:100vh}
.top{position:sticky;top:0;background:#fff;border-bottom:1px solid #eee;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;z-index:10}
.logo{font-weight:900;font-size:22px;letter-spacing:-1px}
.btn{background:#000;color:#fff;border:0;padding:10px 18px;border-radius:24px;font-weight:700;cursor:pointer}
.card{background:#fff;border:1px solid #eee;border-radius:16px;padding:14px;margin:10px 0;box-shadow:0 1px 2px rgba(0,0,0,0.03)}
.avatar{width:44px;height:44px;border-radius:50%;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;overflow:hidden}
.avatar img{width:100%;height:100%;object-fit:cover}
input,textarea{width:100%;background:#fff;border:1px solid #ddd;color:#000;padding:14px;border-radius:14px;margin:6px 0;font-size:16px}
.search{position:relative;margin:12px 0}
.search input{padding-left:40px;background:#f0f0f0;border:0;border-radius:20px}
.search span{position:absolute;left:14px;top:14px;color:#888}
.msg{max-width:75%;padding:12px 16px;border-radius:20px;margin:8px 0;font-size:15px}
.me{background:#000;color:#fff;margin-left:auto;border-bottom-right-radius:4px}
.them{background:#eee;color:#000;border-bottom-left-radius:4px}
</style></head><body>
<div class="top"><div class="logo">inner.circle</div>
{% if me %}<a href="/profile" style="text-decoration:none"><div class="avatar" style="width:36px;height:36px">{% if me.photo %}<img src="{{me.photo}}">{% else %}{{me.name[0]}}{% endif %}</div></a>{% endif %}</div>
<div style="padding:16px;max-width:500px;margin:auto">{{content|safe}}</div>
<script>setInterval(()=>{fetch('/ping',{method:'POST'})},30000);</script>
</body></html>
"""

@app.route("/icon.png")
def icon():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" rx="120" fill="#000"/><circle cx="256" cy="256" r="160" fill="none" stroke="white" stroke-width="6"/><text x="256" y="340" font-family="Georgia" font-size="210" fill="white" text-anchor="middle" font-weight="700">i</text></svg>'''
    return Response(svg, mimetype="image/svg+xml")

@app.route("/manifest.json")
def manifest():
    return jsonify({"name":"Inner Circle","short_name":"inner.circle","start_url":"/","display":"standalone","background_color":"#ffffff","theme_color":"#000000","icons":[{"src":"/icon.png","sizes":"512x512","type":"image/svg+xml"}]})

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
    if "user" not in session:
        return render_template_string(PAGE, content="""
        <h1 style="font-size:48px;font-weight:900;line-height:0.9;margin:30px 0">Your<br>Inner<br>Circle.</h1>
        <p style="color:#666;margin-bottom:24px;font-size:17px">Private social for Wuse 2. No algorithm. Just your people.</p>
        <form method="post" action="/login"><input name="username" placeholder="Username"><input name="password" type="password" placeholder="Password"><button class="btn" style="width:100%;margin-top:12px;padding:16px">Login</button></form>
        <div style="text-align:center;margin-top:20px"><a href="/signup" style="color:#000;font-weight:700">Create account →</a></div>
        """, me=None)
    db=load_db(); me=db["users"][session["user"]]
    q = request.args.get("q","").lower()
    html = f"""<div class="search"><span>⌕</span><form method="get"><input name="q" value="{q}" placeholder="Search people in Wuse 2..." onchange="this.form.submit()"></form></div>"""
    html += f"<h3 style='margin:12px 0'>People</h3>"
    for uid,u in db["users"].items():
        if uid==session["user"]: continue
        if q and q not in u['name'].lower() and q not in uid.lower(): continue
        online = is_online(u.get("last_seen",""))
        photo = f'<img src="{u.get("photo","")}">' if u.get('photo') else u['name'][0].upper()
        status = "🟢 online" if online else ""
        html+=f"""<div class="card" style="display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;gap:12px;align-items:center"><div class="avatar">{photo}</div><div><b>{u['name']}</b> <small style="color:#0a0">{status}</small><br><small style="color:#888">@{uid}</small></div></div>
        <a href="/chat/{uid}"><button class="btn">Chat</button></a></div>"""
    if not html: html += "<p style='color:#888'>No people found. Invite friends!</p>"
    html += """<div style="margin-top:24px;display:flex;gap:10px"><a href="/circles" style="color:#000">Circles</a> • <a href="/moments" style="color:#000">Moments</a> • <a href="/logout" style="color:#888">Logout</a></div>"""
    return render_template_string(PAGE, content=html, me=me)

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        db=load_db(); uname=request.form["username"].lower()
        if uname in db["users"]: return "Username taken <a href=/signup>back</a>"
        db["users"][uname]={"name":request.form["name"],"username":uname,"password":generate_password_hash(request.form["password"]),"photo":"","last_seen":datetime.utcnow().isoformat()}
        save_db(db); session["user"]=uname; session.permanent=True; return redirect("/")
    return render_template_string(PAGE, content="""<h2 style="margin:20px 0">Join Inner Circle</h2><form method="post"><input name="name" placeholder="Full Name" required><input name="username" placeholder="username" required><input name="password" type="password" placeholder="Password" required><button class="btn" style="width:100%;padding:16px">Create Account</button></form>""", me=None)

@app.route("/login", methods=["POST"])
def login():
    db=load_db(); u=db["users"].get(request.form["username"].lower())
    if u and check_password_hash(u["password"], request.form["password"]):
        session["user"]=u["username"]; session.permanent=True; u["last_seen"]=datetime.utcnow().isoformat(); save_db(db); return redirect("/")
    return "Wrong login <a href=/>back</a>"

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
    pic=f'<img src="{me.get("photo","")}">' if me.get('photo') else me['name'][0].upper()
    return render_template_string(PAGE, content=f"""
    <a href="/">‹ Back to People</a>
    <h2 style="margin:16px 0">Profile</h2><div class="card" style="text-align:center;padding:24px"><div class="avatar" style="width:80px;height:80px;margin:auto;font-size:30px">{pic}</div><h3 style="margin-top:12px">{me['name']}</h3><small>@{me['username']}</small></div>
    <form method="post" enctype="multipart/form-data"><label style="font-weight:700">Full Name</label><input name="name" value="{me['name']}"><label style="font-weight:700">Profile Photo</label><input type="file" name="photo" accept="image/*"><button class="btn" style="width:100%;padding:16px;margin-top:8px">Save Photo ✓</button></form>
    """, me=me)

@app.route("/chat/<uid>")
def chat(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]; other=db["users"].get(uid)
    if not other: return "User not found"
    for m in db["messages"]:
        if m["to"]==session["user"] and m["from"]==uid: m["read"]=True
    save_db(db)
    msgs=[m for m in db["messages"] if (m["from"]==session["user"] and m["to"]==uid) or (m["from"]==uid and m["to"]==session["user"])]
    html=f"<a href='/'>‹ Back</a><h3 style='margin:16px 0'>{other['name']} {'🟢' if is_online(other.get('last_seen','')) else ''}</h3><div style='min-height:60vh'>"
    for m in msgs[-100:]:
        who="me" if m["from"]==session["user"] else "them"
        tick=" ✓✓" if m.get("read") else " ✓" if who=="me" else ""
        html+=f"<div class='msg {who}'>{m['text']}<small style='opacity:.6;display:block;margin-top:4px;font-size:11px'>{m['time'][11:16]}{tick}</small></div>"
    html+=f"</div><form method='post' action='/send/{uid}' style='display:flex;gap:8px;margin-top:16px;position:sticky;bottom:10px'><input name='text' placeholder='Message...' required style='flex:1'><button class='btn'>Send</button></form>"
    return render_template_string(PAGE, content=html, me=me)

@app.route("/send/<uid>", methods=["POST"])
def send(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); db["messages"].append({"from":session["user"],"to":uid,"text":request.form["text"],"time":datetime.utcnow().isoformat(),"read":False}); save_db(db); return redirect(f"/chat/{uid}")

@app.route("/circles")
def circles():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    html="<a href='/'>‹ Back</a><h3 style='margin:16px 0'>Your Circles</h3><form method='post' action='/create_circle' style='display:flex;gap:8px'><input name='name' placeholder='New Circle (e.g. Wuse 2 Boys)' required><button class='btn'>Create</button></form>"
    for cid,c in db["circles"].items():
        if session["user"] in c["members"]: html+=f"<div class='card'><b>{c['name']}</b><br><small>{len(c['members'])} members</small></div>"
    return render_template_string(PAGE, content=html, me=me)

@app.route("/create_circle", methods=["POST"])
def create_circle():
    db=load_db(); cid=str(len(db["circles"])+1); db["circles"][cid]={"name":request.form["name"],"members":[session["user"]]}; save_db(db); return redirect("/circles")

@app.route("/moments", methods=["GET","POST"])
def moments():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    if request.method=="POST":
        db["moments"].insert(0,{"user":session["user"],"text":request.form["text"],"time":datetime.utcnow().isoformat()}); save_db(db); return redirect("/moments")
    html="<a href='/'>‹ Back</a><h3 style='margin:16px 0'>Moments</h3><form method='post'><textarea name='text' placeholder=\"What's happening in Wuse 2?\" required></textarea><button class='btn' style='width:100%'>Post Moment</button></form>"
    for m in db["moments"][:30]:
        u=db["users"].get(m["user"],{"name":m["user"]}); html+=f"<div class='card'><b>{u['name']}</b> <small style='color:#888'>@{m['user']} • {m['time'][11:16]}</small><p style='margin-top:8px'>{m['text']}</p></div>"
    return render_template_string(PAGE, content=html, me=me)

if __name__=="__main__": app.run()
