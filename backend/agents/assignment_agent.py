import os
import re
from datetime import datetime, timedelta
from sqlalchemy import text
from db import engine, query_df
from utils import llm
from utils.mailer import send_mail
import config

SHORT = {
    "daa": "BCS503", "dbms": "BCS501", "oosd": "BCS054", "c++": "BCS054",
    "nlp": "BCAI052", "data analytics": "BCDS501", "idav": "BCDS501",
}
SOLVE_WORDS = ["solve", "solution", "hal ", "answer", "bata do", "likh do", "samjha"]


def clean(v, default="-"):
    # DB ka khali (NaN/None) text "nan" ban ke na dikhe
    return v if isinstance(v, str) and v.strip() else default


def fmt_date(d):
    if d is None or str(d) in ("NaT", "None", "nan"):
        return "-"
    return str(d)[:10]


def get_assignments():
    df = query_df("SELECT * FROM assignments ORDER BY posted_on DESC")
    return df.to_dict("records")


def pick_assignment(question, rows):
    q = question.lower()

    # "assignment 3" jaisa kuch likha hai?
    m = re.search(r"assignment[\s\-_]*(\d+)", q)
    if m:
        n = m.group(1)
        for r in rows:
            if re.search(r"assignment[\s\-_]*%s\b" % n, r["title"].lower()):
                return r

    # subject ka naam / short form
    for short, code in SHORT.items():
        if short in q:
            for r in rows:
                if r["subject_code"] == code:
                    return r
    for r in rows:
        if r["subject_code"].lower() in q:
            return r

    return rows[0] if rows else None   # warna latest wala


def read_file_text(file_name):
    if not isinstance(file_name, str) or not file_name:
        return ""
    path = os.path.join(config.UPLOAD_DIR, file_name)
    if not os.path.exists(path):
        return ""
    try:
        if path.lower().endswith(".pdf"):
            from pypdf import PdfReader
            pages = [p.extract_text() or "" for p in PdfReader(path).pages]
            return "\n".join(pages)[:6000]
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()[:6000]
    except Exception:
        return ""


def describe(a):
    return ("%s (%s)\nPosted by: %s\nMax marks: %s\nLast date: %s\nDetails: %s"
            % (a["title"], a["subject_name"], a["posted_by"], a["max_marks"], fmt_date(a["due_date"]), clean(a["description"])))


def solve(a):
    content = read_file_text(a.get("file_name"))
    system = ("Tum ek helpful teaching assistant ho. Assignment ko step by step solve karo aur har step ka "
              "chhota reason bhi likho taaki student samajh sake. Code ho to clean code do. "
              "Student ki bhasha (Hindi/English/Hinglish) mein likho.")
    user = "Subject: %s\nTitle: %s\nDescription: %s\n\nFile ka text:\n%s" % (
        a["subject_name"], a["title"], clean(a["description"]), content or "(file nahi mili)")
    return llm.ask(system, user, temperature=0.3, max_tokens=1500)


def answer(question, user):
    rows = get_assignments()
    if not rows:
        return {"answer": "Abhi koi assignment post nahi hua hai.", "rows": []}

    q = question.lower()
    if any(w in q for w in SOLVE_WORDS):
        a = pick_assignment(question, rows)
        solution = solve(a)
        return {"answer": "%s ka solution:\n\n%s\n\n(Pehle khud try karo, phir isse check karo.)" % (a["title"], solution),
                "rows": []}

    # warna assignments ki list + due dates
    lines = []
    for a in rows[:6]:
        lines.append("- %s | %s | last date: %s" % (a["title"], a["subject_name"], fmt_date(a["due_date"])))
    table = [{"title": a["title"], "subject": a["subject_name"], "last_date": fmt_date(a["due_date"]),
              "max_marks": a["max_marks"]} for a in rows[:6]]
    return {"answer": "Ye assignments mile:\n" + "\n".join(lines) +
            "\n\nKisi ka solution chahiye to bolo, jaise \"assignment 3 solve karo\".", "rows": table}


# ---- teacher ke liye / reminders ----

def add_note(conn, user_id, message, key):
    exists = conn.execute(text("SELECT 1 FROM notifications WHERE user_id = :u AND note_key = :k"),
                          {"u": user_id, "k": key}).first()
    if exists:
        return False
    conn.execute(text("INSERT INTO notifications (user_id, message, created_on, is_read, note_key) "
                      "VALUES (:u, :m, :c, :r, :k)"),
                 {"u": user_id, "m": message, "c": datetime.now(), "r": False, "k": key})
    return True


def notify_new_assignment(assignment_id, title, subject_name):
    students = query_df("SELECT id, email FROM users WHERE role = 'student'").to_dict("records")
    msg = "Naya assignment aaya: %s (%s)" % (title, subject_name)
    with engine.begin() as conn:
        for s in students:
            add_note(conn, s["id"], msg, "new-%s-%s" % (assignment_id, s["id"]))
    for s in students:
        send_mail(s["email"], "Naya assignment", msg)


def send_due_reminders():
    """Roz subah chalta hai. Jinki last date 2 din ke andar hai unke liye reminder."""
    today = datetime.now().date()
    last = today + timedelta(days=2)
    due = query_df("SELECT id, title, subject_name, due_date FROM assignments "
                   "WHERE due_date >= :a AND due_date <= :b", {"a": today, "b": last}).to_dict("records")
    students = query_df("SELECT id, email FROM users WHERE role = 'student'").to_dict("records")
    count = 0
    with engine.begin() as conn:
        for a in due:
            msg = "Reminder: %s ki last date %s hai" % (a["title"], str(a["due_date"])[:10])
            for s in students:
                key = "due-%s-%s-%s" % (a["id"], s["id"], today)
                if add_note(conn, s["id"], msg, key):
                    count += 1
                    send_mail(s["email"], "Assignment reminder", msg)
    print("reminders bheje:", count)
    return count
