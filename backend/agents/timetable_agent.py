import re
from db import query_df
from utils import llm
from utils.sql_helper import question_to_df
from utils.helpers import records, find_subject, find_day, subject_name, now_ist, DAY_NAMES
from rag import get_rag

TABLES = {"timetable", "current_topics"}

SCHEMA_PROMPT = """Tum ek SQL expert ho. Student ke sawal ke liye SIRF ek SELECT query likho. Koi explanation nahi, koi markdown nahi.

Tables:
timetable(day, start_time, end_time, subject_code, subject_name, teacher, kind, room)
current_topics(subject_code, unit, topic, updated_on)

Rules:
- day ki values: Monday, Tuesday, Wednesday, Thursday, Friday (English, pehla letter capital)
- start_time / end_time 24 ghante ke format mein text hain, jaise '09:00', '13:20'
- kind ya to 'Lecture' hota hai ya 'Lab'
- 12:30 se 13:20 lunch hai, koi class nahi
- Topic poochha jaye to current_topics ko subject_code par JOIN karo
- Subject ke naam ke liye LIKE use karo (jaise subject_name LIKE '%Database%'). Short forms: DAA = Design and Analysis of Algorithm, DBMS = Database Management System, NLP = Natural Language Processing, OOSD = Object Oriented System Design
- Order hamesha day ke baad start_time se karo
- Aaj ka din: {today}, abhi ka time: {now}
"""

SYLLABUS_WORDS = ["syllabus", "unit", "chapter", "curriculum", "kya kya padhna", "kya padhna", "course outcome"]

COLS = "start_time, end_time, subject_name, teacher, kind, room"


# ---------- bina LLM ke seedhe jawab (common sawal) ----------

def day_reply(day, label, code=None):
    sql = "SELECT %s FROM timetable WHERE day = :d" % COLS
    params = {"d": day}
    if code:
        sql += " AND subject_code = :c"
        params["c"] = code
    df = query_df(sql + " ORDER BY start_time", params)

    title = "%s (%s)" % (label, day) if label else day
    if df.empty:
        extra = " is subject ki" if code else ""
        return {"answer": "%s ko%s koi class nahi hai." % (title, extra), "rows": []}

    lines = ["%s ki classes:" % title]
    for r in df.to_dict("records"):
        line = "%s-%s  %s (%s)" % (r["start_time"], r["end_time"], r["subject_name"], r["kind"])
        if r["teacher"]:
            line += ", " + r["teacher"]
        lines.append(line)
    return {"answer": "\n".join(lines), "rows": records(df)}


def current_class_reply():
    now = now_ist()
    day = DAY_NAMES[now.weekday()]
    hhmm = now.strftime("%H:%M")
    df = query_df("SELECT %s FROM timetable WHERE day = :d AND start_time <= :t AND end_time > :t" % COLS,
                  {"d": day, "t": hhmm})
    if df.empty:
        return {"answer": "Abhi (%s, %s) koi class nahi chal rahi." % (day, hhmm), "rows": []}
    r = df.iloc[0]
    return {"answer": "Abhi %s chal rahi hai (%s, %s-%s)." % (r["subject_name"], r["kind"], r["start_time"], r["end_time"]),
            "rows": records(df)}


def topic_reply(code):
    if code:
        df = query_df("SELECT subject_code, unit, topic FROM current_topics WHERE subject_code = :c", {"c": code})
    else:
        df = query_df("SELECT subject_code, unit, topic FROM current_topics ORDER BY subject_code")

    if df.empty:
        return {"answer": "Is subject ka current topic teacher ne abhi set nahi kiya.", "rows": []}

    rows = []
    for r in df.to_dict("records"):
        rows.append({"subject": subject_name(r["subject_code"]), "unit": r["unit"], "topic": r["topic"]})

    if code:
        r = rows[0]
        return {"answer": "%s mein abhi Unit %s chal raha hai: %s" % (r["subject"], r["unit"], r["topic"]), "rows": rows}

    lines = ["Abhi ye topics chal rahe hain:"] + ["- %s: Unit %s, %s" % (r["subject"], r["unit"], r["topic"]) for r in rows]
    return {"answer": "\n".join(lines), "rows": rows}


def subject_week_reply(code):
    df = query_df("SELECT day, start_time, end_time, kind, teacher FROM timetable WHERE subject_code = :c", {"c": code})
    if df.empty:
        return {"answer": "Is subject ki class timetable mein nahi mili.", "rows": []}
    df["order"] = df["day"].apply(lambda d: DAY_NAMES.index(d))
    df = df.sort_values(["order", "start_time"]).drop(columns="order")
    lines = ["%s ki classes:" % subject_name(code)]
    for r in df.to_dict("records"):
        lines.append("%s %s-%s (%s)" % (r["day"], r["start_time"], r["end_time"], r["kind"]))
    return {"answer": "\n".join(lines), "rows": records(df)}


def rules(question):
    q = question.lower()
    words = set(re.findall(r"[a-z+]+", q))
    code = find_subject(q)
    day = find_day(q)

    if words & {"topic", "topics"} or "chal raha" in q:
        return topic_reply(code)

    if "abhi" in words and words & {"class", "lecture", "period"}:
        return current_class_reply()

    if day:
        return day_reply(day[0], day[1], code)

    if code and words & {"kab", "timing", "time", "schedule", "lecture", "class", "period"}:
        return subject_week_reply(code)

    return None   # samajh nahi aaya, LLM ko do


# ---------- LLM wala raasta ----------

def explain(question, df):
    system = ("Tum ek college assistant ho. Student ke sawal ka jawab sirf diye gaye data se do. "
              "Student jis style mein likhe (Hindi/English/Hinglish) usi mein reply karo. "
              "Chhota aur saaf jawab, zarurat ho to list banao. Data mein na ho to bolo ki info nahi mili.")
    user = "Sawal: %s\n\nData:\n%s" % (question, df.to_string(index=False))
    return llm.ask(system, user)


def syllabus_answer(question):
    chunks = get_rag().search(question, k=3)
    if not chunks:
        return {"answer": "Is sawal ka syllabus mujhe nahi mila. Subject ka naam likh ke dobara poochho.", "rows": []}
    try:
        system = ("Tum college assistant ho. Neeche syllabus ke tukde diye hain, unhi se jawab do. "
                  "Student ki bhasha mein reply karo. Kuch na mile to bol do.")
        answer = llm.ask(system, "Sawal: %s\n\nSyllabus:\n%s" % (question, "\n".join(chunks)))
    except Exception as e:
        print("syllabus llm fail, seedha syllabus de rahe:", repr(e))
        answer = "\n\n".join(chunks)
    return {"answer": answer, "rows": []}


def answer(question, user):
    q = question.lower()
    if any(w in q for w in SYLLABUS_WORDS):
        return syllabus_answer(question)

    try:
        out = rules(question)
    except Exception as e:
        print("timetable rules fail:", repr(e))
        out = None
    if out:
        return out

    now = now_ist()
    prompt = SCHEMA_PROMPT.format(today=now.strftime("%A"), now=now.strftime("%H:%M"))
    sql, df = question_to_df(question, prompt, TABLES)
    if df.empty:
        return {"answer": "Is sawal ke liye timetable mein kuch nahi mila.", "rows": [], "sql": sql}
    return {"answer": explain(question, df), "rows": records(df.head(15)), "sql": sql}
