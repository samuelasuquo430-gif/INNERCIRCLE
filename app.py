import os, json
from datetime import datetime, timedelta
from flask import Flask, request, redirect, render_template_string, session, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "light-fixed-v6"
DB_FILE = "/tmp/db.json"

# CACHE DB IN MEMORY TO STOP OVERLOAD
CACHE = {"data": None, "time": None}

def load_db():
    global CACHE
    # use memory cache for 5 seconds
    if CACHE["data"] and CACHE["time"] and (datetime.utcnow() - CACHE["time"]).seconds < 5:
        return CACHE["data"]
    if not os.path.exists(DB_FILE):
        data = {"users": {}, "messages": [], "circles": {}, "moments": []}
    else:
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {"users": {}, "messages": [], "circles": {}, "moments": []}
    # ensure keys
    for u in data.get("users",{}).values():
        u.setdefault("bio",""); u.setdefault("followers",[]); u.setdefault("following",[]); u.setdefault("friends",[]); u.setdefault("requests",[]); u.setdefault("photo",""); u.setdefault("last_seen","")
    CACHE = {"data": data, "time": datetime.utcnow()}
    return data

def save_db(db):
    global CACHE
    CACHE = {"data": db, "time": datetime.utcnow()}
    try:
        with open(DB_FILE, "w") as f:
            json.dump(db, f)
    except:
        pass

PAGE = """
<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>inner.circle</title>
<link rel="icon" href="/icon.png">
<meta name="theme-color" content="#000000">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto}
body{background:#000;color:#fff;display:flex;min-height:100vh}
.sidebar{width:68px;background:#000;border-right:1px solid #222;position:fixed;left:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;padding:18px 0;gap:16px;z-index:20}
.sidebar a{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:20px;color:#666}
.sidebar a.active{background:#fff;color:#000}
.main{margin-left:68px;flex:1;max-width:600px;width:100%}
.top{font-weight:900;padding:14px 16px;border-bottom:1px solid #222;position:sticky;top:0;background:#000}
.content{padding:14px}
.btn{background:#fff;color:#000;border:0;padding:10px 16px;border-radius:20px;font-weight:700;cursor:pointer}
.card{background:#111;border:1px solid #222;border-radius:16px;padding:12px;margin:8px 0}
.avatar{width:42px;height:42px;border-radius:50%;background:#222;display:flex;align-items:center;justify-content:center;font-weight:800;overflow:hidden}
.avatar img{width:100%;height:100%;object-fit:cover}
input,textarea{width:100%;background:#111;border:1px solid #333;color:#fff;padding:12px;border-radius:12px;margin:5px 0}
.msg{max-width:76%;padding:10px 14px;border-radius:18px;margin:6px 0;font-size:14px}
.me{background:#fff;color:#000;margin-left:auto}
.them{background:#1e1e1e;color:#fff}
@media(max-width:700px){.sidebar{flex-direction:row;bottom:0;top:auto;width:100%;height:58px;border-top:1px solid #222;justify-content:space-around}.main{margin-left:0;margin-bottom:58px}}
</style></head><body>
<div class="sidebar">
<a href="/chats" class="{% if tab=='chats' %}active{% endif %}">💬</a>
<a href="/circles" class="{% if tab=='groups' %}active{% endif %}">👥</a>
<a href="/moments" class="{% if tab=='posts' %}active{% endif %}">⊞</a>
<a href="/calls" class="{% if tab=='calls' %}active{% endif %}">📞</a>
<a href="/profile" class="{% if tab=='profile' %}active{% endif %}">☺</a>
</div>
<div class="main">
<div class="top">inner.circle <span style="color:#666;font-weight:400;font-size:11px;margin-left:6px">ABUJA CONNECT / LIFESTYLE</span></div>
<div class="content">{{content|safe}}</div>
</div>
<script>
// PING ONLY EVERY 2 MINUTES NOW - STOPS OVERLOAD
setInterval(()=>{fetch('/ping',{method:'POST'})}, 120000);
</script>
</body></html>
"""

@app.route("/icon.png")
def icon():
    return Response('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" rx="120" fill="#000"/><circle cx="256" cy="256" r="160" fill="none" stroke="white" stroke-width="6"/><text x="256" y="340" font-family="Georgia" font-size="210" fill="white" text-anchor="middle" font-weight="700">i</text></svg>',mimetype="image/svg+xml")

@app.route("/ping",methods=["POST"])
def ping():
    if "user" not in session: return ""
    # DON'T SAVE EVERY TIME - ONLY IF 2 MIN OLD
    db=load_db(); u=db["users"].get(session["user"])
    if not u: return ""
    try:
        last = datetime.fromisoformat(u.get("last_seen","2000-01-01"))
        if datetime.utcnow() - last > timedelta(minutes=2):
            u["last_seen"]=datetime.utcnow().isoformat()
            save_db(db)
    except:
        pass
    return ""

def is_online(s):
    try: return datetime.utcnow()-datetime.fromisoformat(s) < timedelta(minutes=4)
    except: return False

@app.route("/")
def home():
    if "user" not in session:
        return render_template_string(PAGE, content="""
        <h1 style="font-size:40px;font-weight:900;line-height:0.9;margin:16px 0 8px">Your<br>Inner<br>Circle.</h1>
        <p style="color:#888;margin-bottom:20px;font-size:14px">Abuja Connect / Lifestyle<br><span style="color:#555">Sign up and meet the community.</span></p>
        <form method="post" action="/login"><input name="username" placeholder="Username"><input name="password" type="password" placeholder="Password"><button class="btn" style="width:100%;padding:14px;margin-top:8px">Login</button></form>
        <div style="text-align:center;margin-top:14px"><a href="/signup" style="color:#fff;text-decoration:none;font-weight:700">Create account →</a></div>
        """, tab="home")
    return redirect("/chats")

@app.route("/chats")
def chats():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    html=f"<h3>Chats • {len(me.get('friends',[]))} friends</h3>"
    if me.get("requests"):
        html+="<div class='card' style='border-color:#333'><b>Requests</b>"
        for req in me["requests"][:5]:
            u=db["users"].get(req)
            if u: html+=f"<div style='display:flex;justify-content:space-between;margin-top:8px'><span>{u['name']}</span><a href='/accept/{req}'><button class='btn' style='padding:4px 10px;font-size:12px'>Accept</button></a></div>"
        html+="</div>"
    # LIMIT TO 50 USERS TO STOP OVERLOAD
    count=0
    for uid,u in list(db["users"].items())[:50]:
        if uid==session["user"]: continue
        if count>20: break
        count+=1
        is_friend = uid in me.get("friends",[])
        photo = u['name'][0].upper() # NO PHOTO IN LIST TO SAVE RAM
        btn = f"<a href='/chat/{uid}'><button class='btn' style='padding:5px 10px;font-size:12px'>Chat</button></a>" if is_friend else f"<a href='/add/{uid}'><button class='btn' style='padding:5px 10px;font-size:12px;background:transparent;color:#fff;border:1px solid #333'>Add</button></a>"
        html+=f"<div class='card' style='display:flex;justify-content:space-between;align-items:center'><div style='display:flex;gap:10px;align-items:center'><div class='avatar'>{photo}</div><div><b style='font-size:14px'>{u['name']}</b><br><small style='color:#666'>@{uid}</small></div></div>{btn}</div>"
    return render_template_string(PAGE, content=html, tab="chats")

@app.route("/add/<uid>")
def add_friend(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); other=db["users"].get(uid)
    if other and session["user"] not in other.get("requests",[]) and session["user"] not in other.get("friends",[]):
        other.setdefault("requests",[]).append(session["user"]); save_db(db)
    return redirect("/chats")

@app.route("/accept/<uid>")
def accept(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    if uid in me.get("requests",[]):
        me["requests"].remove(uid)
        if uid not in me["friends"]: me["friends"].append(uid)
        if uid not in me["followers"]: me["followers"].append(uid)
        other=db["users"][uid]
        if session["user"] not in other["friends"]: other["friends"].append(session["user"])
        if session["user"] not in other["followers"]: other["followers"].append(session["user"])
        save_db(db)
    return redirect("/chats")

@app.route("/chat/<uid>")
def chat(uid):
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]; other=db["users"].get(uid)
    if not other: return "Not found"
    is_friend = uid in me.get("friends",[])
    msgs=[m for m in db["messages"] if (m["from"]==session["user"] and m["to"]==uid) or (m["from"]==uid and m["to"]==session["user"])]
    sent_by_me = sum(1 for m in msgs if m["from"]==session["user"])
    can_send = is_friend or sent_by_me < 1
    for m in db["messages"]:
        if m["to"]==session["user"] and m["from"]==uid: m["read"]=True
    if any(m["to"]==session["user"] and m["from"]==uid and not m.get("read") for m in db["messages"]):
        save_db(db)
    html=f"<a href='/chats' style='color:#888;text-decoration:none'>‹ Back</a><h3 style='margin:10px 0'>{other['name']}</h3><div>"
    for m in msgs[-30:]: # ONLY LAST 30 MESSAGES
        who="me" if m["from"]==session["user"] else "them"
        html+=f"<div class='msg {who}'>{m['text']}</div>"
    html+="</div>"
    if can_send:
        html+=f"<form method='post' action='/send/{uid}' style='display:flex;gap:6px;margin-top:12px'><input name='text' placeholder='Message...' required style='flex:1'><button class='btn'>Send</button></form>"
    else:
        html+=f"<p style='color:#666;text-align:center;margin-top:12px'>Wait for accept.</p>"
    return render_template_string(PAGE, content=html, tab="chats")

@app.route("/send/<uid>", methods=["POST"])
def send(uid):
    if "user" not in session: return redirect("/")
    db=load_db()
    # LIMIT MESSAGES TO 200 TOTAL TO STOP OVERLOAD
    if len(db["messages"]) > 200:
        db["messages"] = db["messages"][-150:]
    db["messages"].append({"from":session["user"],"to":uid,"text":request.form["text"][:200],"time":datetime.utcnow().isoformat(),"read":False})
    save_db(db); return redirect(f"/chat/{uid}")

@app.route("/circles")
def circles():
    if "user" not in session: return redirect("/")
    db=load_db()
    html="<h3>Groups</h3><form method='post' action='/create_circle' style='display:flex;gap:6px'><input name='name' placeholder='New Group' required><button class='btn'>Create</button></form>"
    for cid,c in db["circles"].items():
        if session["user"] in c["members"]:
            html+=f"<div class='card'><b>{c['name']}</b> <small>• {len(c['members'])} members</small><div style='margin-top:6px'><a href='/group/{cid}'><button class='btn' style='padding:4px 10px;font-size:12px'>Open</button></a></div></div>"
    return render_template_string(PAGE, content=html, tab="groups")

@app.route("/create_circle", methods=["POST"])
def create_circle():
    db=load_db(); cid=str(len(db["circles"])+1); db["circles"][cid]={"name":request.form["name"],"members":[session["user"]],"messages":[]}; save_db(db); return redirect("/circles")

@app.route("/group/<cid>", methods=["GET","POST"])
def group_chat(cid):
    if "user" not in session: return redirect("/")
    db=load_db(); g=db["circles"].get(cid)
    if not g or session["user"] not in g["members"]: return "Not in group"
    if request.method=="POST":
        g["messages"].append({"user":session["user"],"text":request.form["text"][:200],"time":datetime.utcnow().isoformat()}); save_db(db); return redirect(f"/group/{cid}")
    html=f"<a href='/circles' style='color:#888;text-decoration:none'>‹ Back</a><h3>{g['name']}</h3><div>"
    for m in g["messages"][-30:]:
        who="me" if m["user"]==session["user"] else "them"
        html+=f"<div class='msg {who}'><b style='font-size:11px'>@{m['user']}</b><br>{m['text']}</div>"
    html+=f"</div><form method='post' style='display:flex;gap:6px;margin-top:12px'><input name='text' placeholder='Message...' required style='flex:1'><button class='btn'>Send</button></form>"
    return render_template_string(PAGE, content=html, tab="groups")

@app.route("/moments", methods=["GET","POST"])
def moments():
    if "user" not in session: return redirect("/")
    db=load_db()
    if request.method=="POST":
        if len(db["moments"]) > 50: db["moments"] = db["moments"][:40]
        db["moments"].insert(0,{"id":str(len(db["moments"])+1),"user":session["user"],"text":request.form["text"][:300],"time":datetime.utcnow().isoformat(),"likes":0,"comments":[]}); save_db(db); return redirect("/moments")
    html="<h3>Feed</h3><form method='post'><textarea name='text' placeholder='What is happening in Abuja?' required></textarea><button class='btn' style='width:100%'>Post</button></form>"
    for m in db["moments"][:15]: # ONLY 15 POSTS
        u=db["users"].get(m["user"],{"name":m["user"]})
        html+=f"<div class='card'><b>{u['name']}</b> <small style='color:#666'>@{m['user']}</small><p style='margin:8px 0;font-size:14px'>{m['text']}</p><div style='display:flex;gap:6px'><a href='/react/{m['id']}'><button style='background:#111;border:1px solid #222;border-radius:20px;padding:4px 10px;color:#fff;font-size:12px'>❤️ {m.get('likes',0)}</button></a><a href='/comment_page/{m['id']}'><button style='background:#111;border:1px solid #222;border-radius:20px;padding:4px 10px;color:#fff;font-size:12px'>💬 {len(m.get('comments',[]))}</button></a></div></div>"
    return render_template_string(PAGE, content=html, tab="posts")

@app.route("/react/<mid>")
def react(mid):
    db=load_db()
    for m in db["moments"]:
        if m["id"]==mid: m["likes"]=m.get("likes",0)+1; save_db(db); break
    return redirect("/moments")

@app.route("/comment_page/<mid>", methods=["GET","POST"])
def comment_page(mid):
    if "user" not in session: return redirect("/")
    db=load_db()
    post = next((x for x in db["moments"] if x["id"]==mid), None)
    if not post: return redirect("/moments")
    if request.method=="POST":
        post.setdefault("comments",[]).append({"user":session["user"],"text":request.form["text"][:150]}); save_db(db); return redirect(f"/comment_page/{mid}")
    html=f"<a href='/moments' style='color:#888;text-decoration:none'>‹ Back</a><div class='card'><b>@{post['user']}</b><p>{post['text']}</p></div><h4 style='margin:12px 0'>Comments</h4>"
    for c in post.get("comments",[]):
        html+=f"<div class='card'><b>@{c['user']}</b> {c['text']}</div>"
    html+=f"<form method='post' style='display:flex;gap:6px'><input name='text' placeholder='Comment...' required style='flex:1'><button class='btn'>Post</button></form>"
    return render_template_string(PAGE, content=html, tab="posts")

@app.route("/calls")
def calls():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    html="<h3>Calls</h3><p style='color:#666;font-size:13px'>Coming soon - voice & video.</p>"
    for uid in me.get("friends",[])[:20]:
        u=db["users"].get(uid)
        if u: html+=f"<div class='card' style='display:flex;justify-content:space-between'><span>{u['name']}</span><button class='btn' style='padding:4px 10px;font-size:12px'>📞</button></div>"
    return render_template_string(PAGE, content=html, tab="calls")

@app.route("/profile", methods=["GET","POST"])
def profile():
    if "user" not in session: return redirect("/")
    db=load_db(); me=db["users"][session["user"]]
    if request.method=="POST":
        # SMALL PHOTO ONLY - COMPRESS
        if "photo" in request.files and request.files["photo"].filename!="":
            try:
                from PIL import Image
                import io, base64
                f=request.files["photo"]
                img=Image.open(f.stream)
                img.thumbnail((200,200))
                buf=io.BytesIO(); img.save(buf, format="JPEG", quality=60)
                b64=base64.b64encode(buf.getvalue()).decode()
                me["photo"]=f"data:image/jpeg;base64,{b64}"
            except:
                # fallback without PIL
                import base64
                f=request.files["photo"]; data=f.read(50000) # LIMIT 50KB
                b64=base64.b64encode(data).decode()
                me["photo"]=f"data:image/jpeg;base64,{b64}"
        me["name"]=request.form.get("name",me["name"])[:30]
        me["bio"]=request.form.get("bio","")[:100]
        save_db(db); return redirect("/profile")
    return render_template_string(PAGE, content=f"""
    <h3>Profile</h3><div class="card" style="text-align:center"><div style="width:70px;height:70px;background:#222;border-radius:50%;margin:auto;display:flex;align-items:center;justify-content:center;font-size:28px">{me['name'][0]}</div><h3 style="margin-top:8px">{me['name']}</h3><small style="color:#666">@{me['username']}</small><p style="color:#aaa;font-size:13px;margin-top:6px">{me.get('bio','No bio')}</p><div style="display:flex;justify-content:center;gap:16px;margin-top:10px"><div><b>{len(me.get('followers',[]))}</b><br><small style="color:#666;font-size:11px">Followers</small></div><div><b>{len(me.get('friends',[]))}</b><br><small style="color:#666;font-size:11px">Friends</small></div></div></div>
    <form method="post" enctype="multipart/form-data"><input name="name" value="{me['name']}" placeholder="Name"><textarea name="bio" placeholder="Bio (100 chars max)">{me.get('bio','')}</textarea><input type="file" name="photo" accept="image/*"><button class="btn" style="width:100%;padding:12px;margin-top:6px">Save</button></form>
    <a href="/logout" style="color:#666;text-decoration:none;font-size:13px"><div style="margin-top:12px">Logout</div></a>
    <a href="/clear_db" style="color:#500;text-decoration:none;font-size:11px"><div style="margin-top:20px">⚠️ Clear cache if overloaded (admin)</div></a>
    """, tab="profile")

@app.route("/clear_db")
def clear_db():
    if "user" not in session: return redirect("/")
    # Keep users but clear messages/moments
    db=load_db(); db["messages"]=db["messages"][-20:]; db["moments"]=db["moments"][:10]; save_db(db); return redirect("/profile")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        db=load_db(); uname=request.form["username"].lower()[:20]
        if uname in db["users"]: return "Taken <a href=/signup>back</a>"
        db["users"][uname]={"name":request.form["name"][:30],"username":uname,"password":generate_password_hash(request.form["password"]),"photo":"","bio":"","followers":[],"following":[],"friends":[],"requests":[],"last_seen":datetime.utcnow().isoformat()}
        save_db(db); session["user"]=uname; session.permanent=True; return redirect("/chats")
    return render_template_string(PAGE, content="""<h2>Join inner.circle</h2><p style="color:#888;font-size:13px">Abuja Connect / Lifestyle</p><form method="post"><input name="name" placeholder="Full Name" required><input name="username" placeholder="username" required><input name="password" type="password" placeholder="Password" required><button class="btn" style="width:100%;padding:14px">Create</button></form>""", tab="home")
@app.route("/login", methods=["POST"])
def login():
    db=load_db(); u=db["users"].get(request.form["username"].lower())
    if u and check_password_hash(u["password"], request.form["password"]):
        session["user"]=u["username"]; session.permanent=True; return redirect("/chats")
    return "Wrong <a href=/>back</a>"
@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__=="__main__": app.run()
