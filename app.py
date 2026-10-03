import os, json
from datetime import datetime, timedelta
from flask import Flask, request, redirect, render_template_string, session, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "inner-circle-abuja-connect-final"
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
<title>inner.circle - Abuja Connect</title>
<link rel="icon" href="/icon.png"><link rel="apple-touch-icon" href="/icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#000000">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto}
body{background:#000;color:#fff;min-height:100vh}
.top{position:sticky;top:0;background:#000;border-bottom:1px solid #222;padding:14px 18px;display:flex;justify-content:space-between;align-items:center}
.logo{font-weight:900;font-size:20px;letter-spacing:-1px}
.btn{background:#fff;color:#000;border:0;padding:12px 20px;border-radius:24px;font-weight:700;cursor:pointer}
.card{background:#111;border:1px solid #222;border-radius:18px;padding:14px;margin:10px 0}
.avatar{width:46px;height:46px;border-radius:50%;background:#222;display:flex;align-items:center;justify-content:center;font-weight:800;overflow:hidden}
.avatar img{width:100%;height:100%;object-fit:cover}
input{width:100%;background:#111;border:1px solid #333;color:#fff;padding:14px;border-radius:14px;margin:6px 0;font-size:16px}
.search input{background:#111;border:1px solid #222;border-radius:22px;padding-left:42px}
.msg{max-width:76%;padding:12px 16px;border-radius:20px;margin:8px 0}
.me{background:#fff;color:#000;margin-left:auto}
.them{background:#1e1e1e;color:#fff}
</style></head><body>
<div class="top"><div class="logo">inner.circle</div>{% if me %}<a href="/profile"><div class="avatar" style="width:34px;height:34px">{% if me.photo %}<img src="{{me.photo}}">{% else %}{{me.name[0]}}{% endif %}</div></a>{% endif %}</div>
<div style="padding:16px;max-width:520px;margin:auto">{{content|safe}}</div>
<script>setInterval(()=>{fetch('/ping',{method:'POST'})},30000);</script>
</body></html>
"""

@app.route("/icon.png")
def icon():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" rx="120" fill="#000"/><circle cx="256" cy="256" r="160" fill="none" stroke="white" stroke-width="6"/><text x="256" y="340" font-family="Georgia" font-size="210" fill="white" text-anchor="middle" font-weight="700">i</text></svg>'''
    return Response(svg, mimetype="image/svg+xml")
@app.route("/manifest.json")
def manifest():
    return jsonify({"name":"inner.circle - Abuja Connect","short_name":"inner.circle","start_url":"/","display":"standalone","background_color":"#000000","theme_color":"#000000","icons":[{"src":"/icon.png","sizes":"512x512","type":"image/svg+xml"}]})
@app.route("/sw.js")
def sw(): return "", 200, {'Content-Type':'application/javascript'}
@app.route("/ping", methods=["POST"])
def ping():
    if "user" not in session: return ""
    db=load_db(); u=db["users"].get(session["user"])
    if u: u["last_seen"]=datetime.utcnow().isoformat(); save_db(db)
    return ""
def is_online(s):
    try:
        from datetime import datetime as dt
        t=dt.fromisoformat(s); return dt.utcnow()-t < timedelta(minutes=3)
    except: return False

@app.route("/")
def home():
    if "user" not in session:
        return render_template_string(PAGE, content="""
        <h1 style="font-size:44px;font-weight:900;line-height:0.9;margin:28px 0 12px 0">Your<br>Inner<br>Circle.</h1>
        <p style="color:#aaa;margin-bottom:26px;font-size:16px;line-height:1.4">Abuja Connect / Lifestyle<br><span style="color:#666">Sign up and meet the community.</span></p>
        <form method="post" action="/login"><input name="username" placeholder="Username"><input name="password" type="password" placeholder="Password"><button class="btn" style="width:100%;margin-top:12px;padding:16px">Login</button></form>
        <div style="text-align:center;margin-top:20px"><a href="/signup" style="color:#fff;font-weight:700;text-decoration:none">Create account →</a></div>
        """, me=None)
    db=load_db(); me=db["users"][session["user"]]; q=request.args.get("q","").lower()
    html=f"""<div style="position:relative;margin:14px 0"><span style="position:absolute;left:14px;top:15px;color:#666">⌕</span><form method="get"><input name="q" value="{q}" placeholder="Search people..." style="padding-left:42px"></form></div><h3 style="color:#555;font-size:13px;letter-spacing:1px;margin:12px 0">COMMUNITY</h3>"""
    for uid,u in db["users"].items():
        if uid==session["user"]: continue
        if q and q not in u['name'].lower() and q not in uid: continue
        photo=f'<img src="{u.get("photo","")}">' if u.get('photo') else u['name'][0].upper()
        online="🟢" if is_online(u.get("last_seen","")) else ""
        html+=f"""<div class="card" style="display:flex;justify-content:space-between;align-items:center"><div style="display:flex;gap:12px;align-items:center"><div class="avatar">{photo}</div><div><b>{u['name']}</b> {online}<br><small style="color:#666">@{uid}</small></div></div><a href="/chat/{uid}"><button class="btn">Chat</button></a></div>"""
    return render_template_string(PAGE, content=html, me=me)

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        db=load_db(); uname=request.form["username"].lower()
        if uname in db["users"]: return "Taken <a href=/signup>back</a>"
        db["users"][uname]={"name":request.form["name"],"username":uname,"password":generate_password_hash(request.form["password"]),"photo":"","last_seen":datetime.utcnow().isoformat()}
        save_db(db); session["user"]=uname; session.permanent=True; return redirect("/")
    return render_template_string(PAGE, content="""<h2 style="margin:20px 0">Join inner.circle</h2><p style="color:#888;margin-bottom:16px">Abuja Connect / Lifestyle</p><form method="post"><input name="name" placeholder="Full Name" required><input name="username" placeholder="username" required><input name="password" type="password" placeholder="Password" required><button class="btn" style="width:100%;padding:16px">Create Account</button></form>""", me=None)

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
    return render_template_string(PAGE, content=f"""<a href="/" style="color:#888;text-decoration:none">‹ Back</a><h2 style="margin:16px 0">Profile</h2><div class="card" style="text-align:center;padding:24px"><div class="avatar" style="width:80px;height:80px;margin:auto;font-size:32px">{pic}</div><h3 style="margin-top:12px">{me['name']}</h3></div><form method="post" enctype="multipart/form-data"><input name="name" value="{me['name']}"><input type="file" name="photo" accept="image/*"><button class="btn" style="width:100%;padding:16px">Save</button></form>""", me=me)
@app.route("/chat/<uid>")
def chat(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]; other=db["users"].get(uid)
    if not other: return "Not found"
    for m in db["messages"]:
        if m["to"]==session["user"] and m["from"]==uid: m["read"]=True
    save_db(db)
    msgs=[m for m in db["messages"] if (m["from"]==session["user"] and m["to"]==uid) or (m["from"]==uid and m["to"]==session["user"])]
    html=f"<a href='/' style='color:#888;text-decoration:none'>‹ Back</a><h3 style='margin:16px 0'>{other['name']}</h3><div>"
    for m in msgs[-100:]:
        who="me" if m["from"]==session["user"] else "them"
        html+=f"<div class='msg {who}'>{m['text']}</div>"
    html+=f"</div><form method='post' action='/send/{uid}' style='display:flex;gap:8px;margin-top:16px'><input name='text' placeholder='Message...' required style='flex:1'><button class='btn'>Send</button></form>"
    return render_template_string(PAGE, content=html, me=me)
@app.route("/send/<uid>", methods=["POST"])
def send(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); db["messages"].append({"from":session["user"],"to":uid,"text":request.form["text"],"time":datetime.utcnow().isoformat(),"read":False}); save_db(db); return redirect(f"/chat/{uid}")
@app.route("/circles")
def circles():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    html="<a href='/' style='color:#888;text-decoration:none'>‹ Back</a><h3 style='margin:16px 0'>Circles</h3><form method='post' action='/create_circle' style='display:flex;gap:8px'><input name='name' placeholder='New Circle' required><button class='btn'>Create</button></form>"
    for cid,c in db["circles"].items():
        if session["user"] in c["members"]: html+=f"<div class='card'><b>{c['name']}</b></div>"
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
    html="<a href='/' style='color:#888;text-decoration:none'>‹ Back</a><h3 style='margin:16px 0'>Moments</h3><form method='post'><textarea name='text' placeholder=\"What's happening in Abuja?\" style='width:100%;background:#111;border:1px solid #333;color:#fff;padding:14px;border-radius:14px' required></textarea><button class='btn' style='width:100%;margin-top:8px'>Post</button></form>"
    for m in db["moments"][:30]:
        u=db["users"].get(m["user"],{"name":m["user"]}); html+=f"<div class='card'><b>{u['name']}</b><p style='margin-top:8px'>{m['text']}</p></div>"
    return render_template_string(PAGE, content=html, me=me)

if __name__=="__main__": app.run()
