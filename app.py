from flask import Flask, request, jsonify, render_template_string, send_file
import sqlite3
from textblob import TextBlob
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            rating INTEGER,
            comment TEXT,
            sentiment TEXT,
            recommendation TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- QUESTIONS ----------
questions = [
    "May we have your name?",
    "How would you rate your experience?",
    "Please share your experience with us",
    "Would you recommend us? (yes / no)"
]

sessions = {}

# ---------- MAIN UI ----------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AURELIUS — Client Sentiment Ledger</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Poppins:wght@300;400&display=swap" rel="stylesheet">
<style>
body { background:#0f2a1d; font-family:Poppins; margin:0; }
h1 { color:#f7f4ef; text-align:center; font-family:Playfair Display; }
.subtitle { text-align:center; color:#c6a664; }
.container { display:flex; justify-content:center; gap:40px; }
.testimonials { width:35%; }
.quote { background:#f7f4ef; padding:16px; border-radius:12px; margin-bottom:18px; border-left:5px solid #c6a664; }
.author { text-align:right; font-size:13px; }
.chat-box { width:390px; background:#f7f4ef; padding:20px; border-radius:18px; }
.chat { max-height:320px; overflow-y:auto; }
.bot { background:#ece8df; padding:12px; border-radius:14px; margin:8px 0; }
.user { background:#0f2a1d; color:#fff; padding:12px; border-radius:14px; margin:8px 0 8px auto; }
input, button { width:100%; padding:12px; margin-top:10px; border-radius:12px; }
button { background:#0f2a1d; color:#c6a664; border:1px solid #c6a664; }
.stars { text-align:center; }
.star { font-size:28px; cursor:pointer; color:#bbb; }
.star.active { color:#c6a664; }
.admin { text-align:center; display:block; margin-top:14px; font-weight:600; }
</style>
</head>

<body>
<h1>AURELIUS</h1>
<div class="subtitle">Client Sentiment Ledger</div>

<div class="container">
<div class="testimonials">
{% for q in quotes %}
<div class="quote">“{{q[0]}}”<div class="author">— {{q[1]}}</div></div>
{% endfor %}
</div>

<div class="chat-box">
<div class="chat" id="chat"><div class="bot">{{question}}</div></div>

<div class="stars" id="stars" style="display:none;">
<span class="star" onclick="rate(1)">★</span>
<span class="star" onclick="rate(2)">★</span>
<span class="star" onclick="rate(3)">★</span>
<span class="star" onclick="rate(4)">★</span>
<span class="star" onclick="rate(5)">★</span>
</div>

<input id="msg" placeholder="Your response...">
<button onclick="send()">SUBMIT</button>
<a class="admin" href="/admin">ADMIN CONSOLE</a>
</div>
</div>

<script>
let rating=null;
function rate(v){rating=v;document.querySelectorAll('.star').forEach((s,i)=>s.classList.toggle('active',i<v));}
function send(){
 let input=document.getElementById("msg");
 let text=rating!==null?rating:input.value;
 if(!text)return;
 document.getElementById("chat").innerHTML+=`<div class='user'>${text}</div>`;
 input.value=""; rating=null; stars.style.display="none";
 fetch("/reply",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({msg:text})})
 .then(r=>r.json()).then(d=>{
 document.getElementById("chat").innerHTML+=`<div class='bot'>${d.reply}</div>`;
 if(d.showStars)stars.style.display="block";
 });
}
</script>
</body>
</html>
"""

# ---------- ROUTES ----------
@app.route("/")
def home():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("SELECT comment, username FROM feedback WHERE sentiment='Positive' ORDER BY id DESC LIMIT 5")
    quotes = cur.fetchall()
    conn.close()
    sessions["data"] = []
    return render_template_string(HTML, question=questions[0], quotes=quotes)

@app.route("/admin")
def admin():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM feedback")
    total = cur.fetchone()[0]

    cur.execute("SELECT AVG(rating) FROM feedback")
    avg_rating = cur.fetchone()[0] or 0

    cur.execute("SELECT sentiment, COUNT(*) FROM feedback GROUP BY sentiment")
    sentiments = cur.fetchall()
    sentiment_labels = [s for s,_ in sentiments]
    sentiment_counts = [c for _,c in sentiments]

    cur.execute("SELECT username, rating, comment FROM feedback ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>AURELIUS — Admin Console</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0f2a1d;color:#f5f2eb;font-family:Georgia;}
.panel{background:#f5f2eb;color:#000;margin:25px auto;padding:25px;width:85%;border-radius:18px;}
a{color:#d4af37;font-weight:bold;}
table{width:100%;border-collapse:collapse;}
th,td{padding:10px;border-bottom:1px solid #ccc;}
</style>
</head>

<body>
<h2 style="padding:30px">AURELIUS — Admin Console<br>
<a href="/admin/pdf">📄 Download PDF Report</a></h2>

<div class="panel">
📥 Total Feedback: <b>{{total}}</b> |
⭐ Average Rating: <b>{{avg_rating}}</b>
</div>

<div class="panel" style="max-width:420px;">
    <canvas id="sentimentChart" height="220"></canvas>
</div>


<div class="panel">
<table>
<tr><th>User</th><th>Rating</th><th>Comment</th></tr>
{% for u,r,c in rows %}
<tr><td>{{u}}</td><td>{{r}}</td><td>{{c}}</td></tr>
{% endfor %}
</table>
</div>

<script>
new Chart(document.getElementById("sentimentChart"),{
 type:"doughnut",
 data:{
   labels: {{ sentiment_labels | tojson }},
   datasets:[{data: {{ sentiment_counts | tojson }}, backgroundColor:["#1f6f54","#c2a14d","#8b2f2f"]}]
 }
});
</script>
</body>
</html>
""", total=total, avg_rating=round(avg_rating,2),
sentiment_labels=sentiment_labels, sentiment_counts=sentiment_counts, rows=rows)

@app.route("/admin/pdf")
def pdf():
    conn = sqlite3.connect("feedback.db")
    cur = conn.cursor()
    cur.execute("SELECT username, rating, comment, sentiment FROM feedback")
    rows = cur.fetchall()
    conn.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    pdf.setFont("Helvetica-Bold",16)
    pdf.drawString(50,y,"AURELIUS — Feedback Report")
    y-=40
    pdf.setFont("Helvetica",10)

    for u,r,c,s in rows:
        pdf.drawString(50,y,f"{u} | Rating:{r} | {s}")
        y-=14
        pdf.drawString(60,y,c)
        y-=22
        if y<60: pdf.showPage(); y=800

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="AURELIUS_Report.pdf")

@app.route("/reply", methods=["POST"])
def reply():
    msg=request.json["msg"]
    data=sessions.get("data",[])
    data.append(msg)
    sessions["data"]=data
    step=len(data)

    if step==1: return jsonify({"reply":questions[step],"showStars":True})
    if step<len(questions): return jsonify({"reply":questions[step],"showStars":False})

    u,r,c,rec=data
    pol=TextBlob(c).sentiment.polarity
    s="Positive" if pol>0 else "Negative" if pol<0 else "Neutral"

    conn=sqlite3.connect("feedback.db")
    cur=conn.cursor()
    cur.execute("INSERT INTO feedback (username,rating,comment,sentiment,recommendation) VALUES (?,?,?,?,?)",(u,r,c,s,rec))
    conn.commit(); conn.close()
    sessions["data"]=[]
    return jsonify({"reply":"Thank you. Your feedback has been formally recorded.","showStars":False})

if __name__=="__main__":
    app.run(debug=True)
