import os
from flask import Flask, request, redirect, session, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'inner_circle_final_v5'
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.permanent_session_lifetime = timedelta(days=365)
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_COOKIE_AGE'] = 60*60*24*365
db_path = '/tmp/inner_circle.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
os.makedirs('/tmp/uploads', exist_ok=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100))
    display_name = db.Column(db.String(100))
    bio = db.Column(db.Text, default="just vibing ✨")
    profile_pic = db.Column(db.String(200), default="default.png")
    last_typing = db.Column(db.DateTime, default=datetime.utcnow)

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    image = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.Integer)
    to_user = db.Column(db.Integer)
    status = db.Column(db.String(20))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user = db.Column(db.Integer)
    to_user = db.Column(db.Integer)
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer)
    image = db.Column(db.String(200), default="default.png")

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

STYLE=":root{--bg:#FEFCF9;--dark:#1E1E2F;--violet:#7B61FF;--peach:#FFD6BA;--card:#fff;--muted:#8E8EA0;--line:#F0EDE8}*{box-sizing:border-box}body{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--dark);margin:0}.top{background:var(--dark);color:#fff;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}.btn{background:var(--violet);color:#fff;border:none;padding:10px 18px;border-radius:100px;font-weight:600;cursor:pointer;text-decoration:none}.btn-peach{background:var(--peach);color:var(--dark)}.card{background:var(--card);border:1px solid var(--line);padding:18px;border-radius:22px;margin:12px;box-shadow:0 8px 30px rgba(30,30,47,0.06)}.pic{width:46px;height:46px;border-radius:50%;object-fit:cover}.input{width:100%;padding:14px 16px;border-radius:14px;border:1.5px solid #EDE8E2;background:#FFFEFD}.user-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #F6F1EB}"

INDEX_HTML=f"<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>inner.circle</title><style>{STYLE}body{{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;background:radial-gradient(900px at 10% -10%, #FFD6BA 0%, transparent 55%),radial-gradient(800px at 100% 100%, #C9C3FF 0%, #FEFCF9 55%)}}.card{{max-width:420px;width:100%;padding:28px;border-radius:28px}}</style></head><body><div class='card'><h1 style='font-size:30px;margin:0'>inner<span style='color:var(--violet)'>.circle</span></h1><p style='color:var(--muted);font-size:13px'>1 year login - no stress</p><form action='/login' method='POST'><input class='input' name='username' placeholder='email / phone / username' required><input class='input' type='password' name='password' placeholder='password' required style='margin-top:10px'><button class='btn' style='width:100%;margin-top:12px;padding:14px'>log in</button></form><hr style='margin:20px 0;border:none;border-top:1px dashed var(--line)'><form action='/signup' method='POST' enctype='multipart/form-data'><input class='input' name='new_username' placeholder='username' required><input class='input' name='email' type='email' placeholder='email' required style='margin-top:8px'><input class='input' name='phone' placeholder='phone' required style='margin-top:8px'><textarea class='input' name='bio' placeholder='bio'></textarea><input type='file' name='profile_pic' accept='image/*' style='margin:8px 0'><input class='input' type='password' name='new_password' placeholder='create password' required><button class='btn btn-peach' style='width:100%;margin-top:10px;padding:14px'>create account</button></form></div></body></html>"

HOME_HTML = """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>home</title><style>""" + STYLE + """.layout{max-width:680px;margin:0 auto}</style></head><body>
<div class='top'><div style='display:flex;align-items:center;gap:10px'><div style='width:46px;height:46px;background:var(--peach);border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:bold'>{{ me.display_name[0] }}</div><div><b>{{ me.display_name }}</b></div></div><a href='/profile' style='color:#fff;text-decoration:none;background:rgba(255,255,255,.15);padding:7px 14px;border-radius:100px'>profile</a></div>
<div class='layout'>
<div class='card'><h3>moments</h3><form action='/post_status' method='POST' enctype='multipart/form-data'><textarea class='input' name='status_text' placeholder='share a moment...'></textarea><input type='file' name='status_image' accept='image/*' style='margin:8px 0'><button class='btn' style='width:100%'>post</button></form>
{% for s in statuses %}{% set u = users_dict.get(s.user_id) %}<div style='padding:10px 0;border-bottom:1px solid var(--line)'><b>{{ u.display_name if u else 'User' }}</b> <small>{{ s.timestamp.strftime('%H:%M') }}</small><p>{{ s.text }}</p></div>{% endfor %}</div>
<div class='card' style='background:var(--dark);color:#fff'><h3>create a circle</h3><form action='/create_group' method='POST' enctype='multipart/form-data'><input class='input' name='group_name' placeholder='Wuse 2 Link Up' required><input class='input' name='group_desc' placeholder='about?' style='margin-top:8px'><button class='btn btn-peach' style='width:100%;margin-top:10px'>create circle</button></form></div>
<div class='card'><h3>your circles</h3>{% for g in my_groups %}<div class='user-row'><div style='width:46px;height:46px;background:var(--violet);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center'>{{ g.name[0] }}</div><div style='flex:1'><b>{{ g.name }}</b></div><a href='/group_chat/{{ g.id }}' class='btn'>open</a></div>{% endfor %}</div>
<div class='card'><h3>find people</h3><input class='input' id='searchBox' placeholder='search...' onkeyup='filter()'><div id='userList'>{% for u in all_users %}<div class='user-row user-item'><div style='width:46px;height:46px;background:#eee;border-radius:50%;display:flex;align-items:center;justify-content:center'>{{ u.display_name[0] }}</div><div style='flex:1'><b>{{ u.display_name }}</b></div><a href='/add_friend/{{ u.id }}' class='btn btn-peach'>add</a></div>{% endfor %}</div></div>
<div class='card'><h3>requests</h3>{% for fr in pending %}{% set sender = users_dict.get(fr.from_user) %}<div class='user-row'><span>{{ sender.display_name if sender else 'User' }}</span><a href='/accept/{{ fr.id }}' class='btn' style='margin-left:auto'>accept</a></div>{% endfor %}</div>
<div class='card'><h3>direct messages</h3>{% for f in accepted %}{% set other_id = f.to_user if f.from_user==me.id else f.from_user %}{% set other = users_dict.get(other_id) %}<div class='user-row'><div style='flex:1'><b>{{ other.display_name if other else 'User' }}</b></div><a href='/chat/{{ other_id }}' class='btn'>chat</a></div>{% endfor %}</div>
</div><script>function filter(){let q=document.getElementById('searchBox').value.toLowerCase();document.querySelectorAll('.user-item').forEach(e=>{e.style.display=e.innerText.toLowerCase().includes(q)?'flex':'none'})}</script></body></html>
"""

CHAT_HTML = """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>chat</title><style>""" + STYLE + """body{max-width:680px;margin:0 auto;height:100vh;display:flex;flex-direction:column}.header{background:var(--dark);color:#fff;padding:12px 16px;display:flex;align-items:center;gap:12px}.msgs{flex:1;padding:18px;overflow-y:auto;display:flex;flex-direction:column;gap:8px}.bubble{max-width:70%;padding:12px 16px;border-radius:20px;font-size:14px}.me{background:var(--dark);color:#fff;margin-left:auto}.them{background:#fff;border:1px solid var(--line);margin-right:auto}.input-bar{background:#fff;border-top:1px solid var(--line);padding:12px;display:flex;gap:10px}</style></head><body><div class='header'><a href='/home' style='color:#fff;text-decoration:none;font-size:22px'>←</a><div><b>{{ other.display_name }}</b><div id='typing' style='font-size:11px;color:var(--peach)'></div></div></div><div class='msgs' id='msgs'></div><div class='input-bar'><input class='input' id='msgInput' placeholder='write...'><button class='btn' onclick='sendMsg()'>↑</button></div><script>
let otherId={{ other.id }},myId={{ me.id }},msgsDiv=document.getElementById('msgs'),typingDiv=document.getElementById('typing'),input=document.getElementById('msgInput');
async function loadMsgs(){let res=await fetch(`/api/messages/${otherId}`);let data=await res.json();msgsDiv.innerHTML='';data.messages.forEach(m=>{let d=document.createElement('div');d.className='bubble '+(m.from==myId?'me':'them');d.innerText=m.text;msgsDiv.appendChild(d)});typingDiv.innerText=data.typing?data.other_name+' is typing...':'';msgsDiv.scrollTop=msgsDiv.scrollHeight}
async function sendMsg(){if(!input.value.trim())return;await fetch(`/send/${otherId}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:input.value})});input.value='';loadMsgs()}
input.addEventListener('keydown',e=>{if(e.key==='Enter')sendMsg();fetch(`/api/typing/${otherId}`,{method:'POST'})});setInterval(loadMsgs,1500);loadMsgs();</script></body></html>
"""

GROUP_CHAT_HTML = """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>circle</title><style>""" + STYLE + """body{max-width:680px;margin:0 auto;height:100vh;display:flex;flex-direction:column}.header{background:var(--dark);color:#fff;padding:12px 16px;display:flex;align-items:center;gap:12px}.msgs{flex:1;padding:18px;overflow-y:auto;display:flex;flex-direction:column;gap:10px}.bubble{max-width:75%;padding:12px 16px;border-radius:18px;background:#fff;border:1px solid var(--line)}.meta{font-size:11px;color:var(--muted)}.input-bar{background:#fff;border-top:1px solid var(--line);padding:12px;display:flex;gap:10px}</style></head><body><div class='header'><a href='/home' style='color:#fff;text-decoration:none'>←</a><div><b>{{ group.name }}</b></div></div><div class='msgs' id='msgs'></div><div class='input-bar'><input class='input' id='msgInput' placeholder='message the circle...'><button class='btn' onclick='sendMsg()'>↑</button></div><script>
let groupId={{ group.id }},myId={{ me.id }},msgsDiv=document.getElementById('msgs');
async function loadMsgs(){let res=await fetch(`/api/group_messages/${groupId}`);let data=await res.json();msgsDiv.innerHTML='';data.forEach(m=>{let w=document.createElement('div');w.innerHTML=`<div class='meta'>${m.name} • ${m.time}</div><div class='bubble' style='${m.user_id==myId?'background:#1E1E2F;color:#fff;margin-left:auto':''}'>${m.text}</div>`;msgsDiv.appendChild(w)});msgsDiv.scrollTop=msgsDiv.scrollHeight}
async function sendMsg(){let i=document.getElementById('msgInput');if(!i.value.trim())return;await fetch(`/send_group/${groupId}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:i.value})});i.value='';loadMsgs()}
document.getElementById('msgInput').addEventListener('keydown',e=>{if(e.key==='Enter')sendMsg()});setInterval(loadMsgs,1500);loadMsgs();</script></body></html>
"""

PROFILE_HTML = """
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>profile</title><style>""" + STYLE + """body{max-width:500px;margin:0 auto;padding:20px}</style></head><body><div class='card'><a href='/home' style='text-decoration:none;color:var(--muted)'>← back</a><h2 style='text-align:center'>your space</h2><div style='width:96px;height:96px;border-radius:50%;background:var(--peach);display:flex;align-items:center;justify-content:center;font-size:40px;margin:0 auto 12px auto'>{{ me.display_name[0] }}</div><form action='/update_profile' method='POST'><input class='input' name='display_name' value='{{ me.display_name }}'> <textarea class='input' name='bio' style='margin-top:8px'>{{ me.bio }}</textarea><button class='btn' style='width:100%;padding:14px;margin-top:8px'>save</button></form><a href='/logout' style='display:block;text-align:center;color:var(--muted);text-decoration:none;margin-top:10px'>log out</a></div></body></html>
"""

@app.route('/')
def index():
    if 'user_id' in session: return redirect('/home')
    return render_template_string(INDEX_HTML)

@app.route('/signup', methods=['POST'])
def signup():
    try:
        u = User(username=request.form['new_username'], email=request.form['email'], phone=request.form.get('phone',''), password=request.form['new_password'], display_name=request.form['new_username'], bio=request.form.get('bio','just vibing ✨'))
        db.session.add(u); db.session.commit()
        session.permanent = True; session['user_id'] = u.id
        return redirect('/home')
    except Exception as e:
        return f"Exists: {e} <a href='/'>Back</a>"

@app.route('/login', methods=['POST'])
def login():
    inp = request.form['username']
    u = User.query.filter((User.username==inp)|(User.email==inp)|(User.phone==inp)).filter_by(password=request.form['password']).first()
    if u:
        session.permanent = True; session['user_id'] = u.id
        return redirect('/home')
    return "Wrong login <a href='/'>Back</a>"

@app.route('/home')
def home():
    if 'user_id' not in session: return redirect('/')
    me = User.query.get(session['user_id'])
    all_users = User.query.filter(User.id!= me.id).all()
    pending = FriendRequest.query.filter_by(to_user=me.id, status='pending').all()
    accepted = FriendRequest.query.filter(((FriendRequest.from_user==me.id)|(FriendRequest.to_user==me.id)) & (FriendRequest.status=='accepted')).all()
    statuses = Status.query.order_by(Status.timestamp.desc()).limit(20).all()
    my_groups = db.session.query(Group).join(GroupMember, Group.id==GroupMember.group_id).filter(GroupMember.user_id==me.id).all()
    all_users_dict = {u.id: u for u in User.query.all()}
    return render_template_string(HOME_HTML, me=me, all_users=all_users, pending=pending, accepted=accepted, statuses=statuses, users_dict=all_users_dict, my_groups=my_groups)

@app.route('/post_status', methods=['POST'])
def post_status():
    text = request.form.get('status_text','')
    if text:
        db.session.add(Status(user_id=session['user_id'], text=text)); db.session.commit()
    return redirect('/home')

@app.route('/add_friend/<int:user_id>')
def add_friend(user_id):
    if user_id!= session['user_id']:
        if not FriendRequest.query.filter_by(from_user=session['user_id'], to_user=user_id).first():
            db.session.add(FriendRequest(from_user=session['user_id'], to_user=user_id, status='pending')); db.session.commit()
    return redirect('/home')

@app.route('/accept/<int:req_id>')
def accept(req_id):
    fr = FriendRequest.query.get(req_id)
    if fr and fr.to_user == session.get('user_id'):
        fr.status='accepted'; db.session.commit()
    return redirect('/home')

@app.route('/create_group', methods=['POST'])
def create_group():
    name = request.form.get('group_name'); desc = request.form.get('group_desc','')
    g = Group(name=name, description=desc, created_by=session['user_id'])
    db.session.add(g); db.session.commit()
    db.session.add(GroupMember(group_id=g.id, user_id=session['user_id'])); db.session.commit()
    return redirect('/home')

@app.route('/chat/<int:user_id>')
def chat(user_id):
    if 'user_id' not in session: return redirect('/')
    return render_template_string(CHAT_HTML, other=User.query.get(user_id), me=User.query.get(session['user_id']))

@app.route('/api/messages/<int:user_id>')
def api_messages(user_id):
    me = session['user_id']
    msgs = Message.query.filter(((Message.from_user==me)&(Message.to_user==user_id))|((Message.from_user==user_id)&(Message.to_user==me))).order_by(Message.timestamp.asc()).all()
    other = User.query.get(user_id)
    is_typing = other.last_typing and (datetime.utcnow() - other.last_typing).seconds < 3
    return jsonify({"messages": [{"from": m.from_user, "text": m.text, "time": m.timestamp.strftime('%H:%M')} for m in msgs], "typing": is_typing, "other_name": other.display_name})

@app.route('/send/<int:user_id>', methods=['POST'])
def send(user_id):
    data = request.get_json() if request.is_json else request.form
    if data.get('text'):
        db.session.add(Message(from_user=session['user_id'], to_user=user_id, text=data.get('text'))); db.session.commit()
    return jsonify({"ok": True})

@app.route('/api/typing/<int:user_id>', methods=['POST'])
def typing(user_id):
    me = User.query.get(session['user_id']); me.last_typing = datetime.utcnow(); db.session.commit()
    return jsonify({"ok": True})

@app.route('/group_chat/<int:group_id>')
def group_chat_page(group_id):
    if not GroupMember.query.filter_by(group_id=group_id, user_id=session['user_id']).first(): return redirect('/home')
    return render_template_string(GROUP_CHAT_HTML, group=Group.query.get(group_id), me=User.query.get(session['user_id']))

@app.route('/api/group_messages/<int:group_id>')
def api_group_messages(group_id):
    msgs = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.timestamp.asc()).all()
    res=[]
    for m in msgs:
        u = User.query.get(m.user_id)
        res.append({"user_id": m.user_id, "name": u.display_name if u else 'User', "text": m.text, "time": m.timestamp.strftime('%H:%M')})
    return jsonify(res)

@app.route('/send_group/<int:group_id>', methods=['POST'])
def send_group(group_id):
    data = request.get_json() if request.is_json else request.form
    if data.get('text'):
        db.session.add(GroupMessage(group_id=group_id, user_id=session['user_id'], text=data.get('text'))); db.session.commit()
    return jsonify({"ok": True})

@app.route('/profile')
def profile(): return render_template_string(PROFILE_HTML, me=User.query.get(session['user_id']))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    me = User.query.get(session['user_id'])
    me.display_name = request.form.get('display_name', me.display_name)
    me.bio = request.form.get('bio', me.bio)
    db.session.commit(); return redirect('/profile')

@app.route('/logout')
def logout(): session.clear(); return redirect('/')
