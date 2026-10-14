import os
import uuid
from datetime import datetime
import pandas as pd
from flask import Flask, request, jsonify, g, send_from_directory, Response
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler

import config
from db import engine, init_db, query_df
from utils.auth import make_token, login_required
from utils import voice
from utils.helpers import records, subject_name
from utils.importer import import_results
from agents import task_manager, assignment_agent

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024   # 15 MB

os.makedirs(config.UPLOAD_DIR, exist_ok=True)
init_db()


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


# ---------- login / register ----------

@app.post("/api/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    df = query_df("SELECT * FROM users WHERE email = :e", {"e": email})
    if df.empty:
        return jsonify({"error": "Email ya password galat hai"}), 401
    user = df.iloc[0].to_dict()
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Email ya password galat hai"}), 401

    roll = user["roll_no"] if isinstance(user["roll_no"], str) else None
    user_small = {"id": int(user["id"]), "name": user["name"], "role": user["role"], "roll_no": roll}
    return jsonify({"token": make_token(user_small), "user": user_small})


@app.post("/api/register")
def register():
    # sirf student register ho sakte hain, teacher seed se banate hain
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    roll_no = (data.get("roll_no") or "").strip()

    if not name or not email or len(password) < 6 or not roll_no:
        return jsonify({"error": "Naam, email, roll no aur 6+ letter ka password chahiye"}), 400
    if not query_df("SELECT id FROM users WHERE email = :e", {"e": email}).empty:
        return jsonify({"error": "Ye email pehle se registered hai"}), 409

    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users (name, email, password_hash, role, roll_no) "
                          "VALUES (:n, :e, :p, 'student', :r)"),
                     {"n": name, "e": email, "p": generate_password_hash(password), "r": roll_no})
    return jsonify({"ok": True})


# ---------- chat ----------

@app.post("/api/chat")
@login_required()
def chat():
    message = ((request.get_json() or {}).get("message") or "").strip()
    if not message:
        return jsonify({"error": "Kuch likho to sahi"}), 400
    return jsonify(task_manager.handle(message, g.user))


@app.get("/api/subjects")
@login_required()
def subjects():
    df = query_df("SELECT DISTINCT subject_code, subject_name FROM timetable ORDER BY subject_code")
    return jsonify(df.to_dict("records"))


# ---------- assignments ----------

@app.get("/api/assignments")
@login_required()
def list_assignments():
    rows = assignment_agent.get_assignments()
    for r in rows:
        r["id"] = int(r["id"])
        r["posted_on"] = str(r["posted_on"])[:16]
        r["due_date"] = assignment_agent.fmt_date(r["due_date"])
        r["description"] = assignment_agent.clean(r.get("description"), "")
        r["max_marks"] = None if pd.isna(r.get("max_marks")) else int(r["max_marks"])
        fn = r.pop("file_name", None)
        r["has_file"] = isinstance(fn, str) and bool(fn)
        r["file_label"] = fn.split("_", 1)[-1] if r["has_file"] else None
    return jsonify(rows)


@app.post("/api/assignments/<int:aid>/solve")
@login_required()
def solve_assignment(aid):
    df = query_df("SELECT * FROM assignments WHERE id = :i", {"i": aid})
    if df.empty:
        return jsonify({"error": "Assignment nahi mila"}), 404
    try:
        solution = assignment_agent.solve(df.iloc[0].to_dict())
    except Exception as e:
        print("solve error:", repr(e))
        return jsonify({"error": "Solution nahi ban paya: " + str(e)[:200]}), 502
    return jsonify({"solution": solution})


@app.post("/api/assignments")
@login_required("teacher")
def post_assignment():
    f = request.form
    code = (f.get("subject_code") or "").strip()
    title = (f.get("title") or "").strip()
    if not code or not title:
        return jsonify({"error": "Subject aur title zaruri hain"}), 400

    sub = query_df("SELECT subject_name FROM timetable WHERE subject_code = :c LIMIT 1", {"c": code})
    subject_name = sub.iloc[0]["subject_name"] if not sub.empty else code

    saved_name = None
    file = request.files.get("file")
    if file and file.filename:
        saved_name = uuid.uuid4().hex[:8] + "_" + secure_filename(file.filename)
        file.save(os.path.join(config.UPLOAD_DIR, saved_name))

    due = f.get("due_date") or None
    if due:
        due = datetime.strptime(due, "%Y-%m-%d").date()

    with engine.begin() as conn:
        res = conn.execute(text(
            "INSERT INTO assignments (subject_code, subject_name, title, description, posted_by, posted_on, due_date, max_marks, file_name) "
            "VALUES (:c, :sn, :t, :d, :p, :po, :due, :m, :fn)"),
            {"c": code, "sn": subject_name, "t": title, "d": f.get("description", ""), "p": g.user["name"],
             "po": datetime.now(), "due": due, "m": int(f.get("max_marks") or 10), "fn": saved_name})
        new_id = res.lastrowid

    assignment_agent.notify_new_assignment(new_id, title, subject_name)
    return jsonify({"ok": True, "id": new_id})


@app.get("/api/assignments/<int:aid>/file")
@login_required()
def assignment_file(aid):
    df = query_df("SELECT file_name FROM assignments WHERE id = :i", {"i": aid})
    if df.empty or not isinstance(df.iloc[0]["file_name"], str):
        return jsonify({"error": "File nahi hai"}), 404
    return send_from_directory(config.UPLOAD_DIR, df.iloc[0]["file_name"], as_attachment=True)


# ---------- teacher: results aur current topic ----------

@app.get("/api/results")
@login_required("teacher")
def results_overview():
    df = query_df("SELECT roll_no, student_name, subject_code, subject_name, marks, max_marks, status "
                  "FROM results ORDER BY roll_no, subject_code")
    if df.empty:
        return jsonify({"summary": [], "overall_top": [], "rows": []})

    df["percent"] = (df["marks"] * 100 / df["max_marks"]).round(1)

    summary = []
    for code, g in df.groupby("subject_code"):
        best = g.sort_values("percent", ascending=False).iloc[0]
        summary.append({
            "subject_code": code,
            "subject_name": g.iloc[0]["subject_name"],
            "students": int(len(g)),
            "passed": int((g["status"] == "pass").sum()),
            "failed": int((g["status"] == "fail").sum()),
            "topper": best["student_name"],
            "topper_percent": float(best["percent"]),
        })

    total = df.groupby(["roll_no", "student_name"], as_index=False).agg(total=("marks", "sum"), out_of=("max_marks", "sum"))
    total["percent"] = (total["total"] * 100 / total["out_of"]).round(1)
    overall = total.sort_values("percent", ascending=False).head(3)

    return jsonify({"summary": summary, "overall_top": records(overall), "rows": records(df)})


@app.get("/api/topics")
@login_required()
def list_topics():
    df = query_df("SELECT subject_code, unit, topic, updated_on FROM current_topics ORDER BY subject_code")
    rows = []
    for r in df.to_dict("records"):
        rows.append({
            "subject_code": r["subject_code"],
            "subject_name": subject_name(r["subject_code"]),
            "unit": r["unit"],
            "topic": r["topic"],
            "updated_on": str(r["updated_on"])[:16],
        })
    return jsonify(rows)


@app.post("/api/results/upload")
@login_required("teacher")
def upload_results():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "File select karo"}), 400
    try:
        n = import_results(file)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True, "rows": n})


@app.post("/api/topics")
@login_required("teacher")
def set_topic():
    d = request.get_json() or {}
    code = (d.get("subject_code") or "").strip()
    topic = (d.get("topic") or "").strip()
    if not code or not topic:
        return jsonify({"error": "Subject aur topic likho"}), 400
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM current_topics WHERE subject_code = :c"), {"c": code})
        conn.execute(text("INSERT INTO current_topics (subject_code, unit, topic, updated_on) VALUES (:c, :u, :t, :n)"),
                     {"c": code, "u": d.get("unit", ""), "t": topic, "n": datetime.now()})
    return jsonify({"ok": True})


# ---------- notifications ----------

@app.get("/api/notifications")
@login_required()
def get_notifications():
    df = query_df("SELECT id, message, created_on, is_read FROM notifications "
                  "WHERE user_id = :u ORDER BY id DESC LIMIT 20", {"u": g.user["id"]})
    rows = df.to_dict("records")
    for r in rows:
        r["created_on"] = str(r["created_on"])[:16]
        r["is_read"] = bool(r["is_read"])
    return jsonify(rows)


@app.post("/api/notifications/read")
@login_required()
def mark_read():
    with engine.begin() as conn:
        conn.execute(text("UPDATE notifications SET is_read = :t WHERE user_id = :u"),
                     {"t": True, "u": g.user["id"]})
    return jsonify({"ok": True})


# ---------- voice (ElevenLabs) ----------

@app.post("/api/voice/stt")
@login_required()
def stt():
    audio = request.files.get("audio")
    if not audio:
        return jsonify({"error": "Audio nahi mila"}), 400
    try:
        txt = voice.speech_to_text(audio.read(), audio.filename or "voice.webm", audio.mimetype or "audio/webm")
    except Exception as e:
        print("stt error:", e)
        return jsonify({"error": "Voice samajh nahi aayi, type karke poochho"}), 502
    return jsonify({"text": txt})


@app.post("/api/voice/tts")
@login_required()
def tts():
    txt = ((request.get_json() or {}).get("text") or "").strip()
    if not txt:
        return jsonify({"error": "Text nahi mila"}), 400
    try:
        audio = voice.text_to_speech(txt)
    except Exception as e:
        print("tts error:", e)
        return jsonify({"error": "Voice generate nahi hui"}), 502
    return Response(audio, mimetype="audio/mpeg")


# ---------- roz subah reminders ----------

def start_scheduler():
    sched = BackgroundScheduler(timezone=config.TIMEZONE)
    sched.add_job(assignment_agent.send_due_reminders, "cron", hour=8, minute=0)
    sched.start()


if __name__ == "__main__":
    start_scheduler()
    # reloader band hai warna scheduler 2 baar start hota hai
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
