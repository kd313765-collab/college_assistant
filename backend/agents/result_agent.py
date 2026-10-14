import re
import config
from db import query_df
from utils import llm
from utils.sql_helper import question_to_df
from utils.helpers import records, find_subject, subject_name

TABLES = {"results"}

SCHEMA_PROMPT = """Tum ek SQL expert ho. Teacher ke sawal ke liye SIRF ek SELECT query likho. Koi explanation nahi, koi markdown nahi.

Table:
results(roll_no, student_name, subject_code, subject_name, marks, max_marks, status)

Rules:
- status ki value 'pass' ya 'fail' (lowercase) hoti hai. {pass_percent}% se kam = fail
- Percentage = marks * 100.0 / max_marks
- Naam ke liye LIKE use karo
- Short forms: DAA = Design and Analysis of Algorithm, DBMS = Database Management System, NLP = Natural Language Processing, OOSD = Object Oriented System Design
- Top / topper / sabse zyada ka matlab ORDER BY marks DESC
- Total ya average chahiye to GROUP BY roll_no use karo
"""


def student_own_result(user):
    # student sirf apna result dekh sakta hai, isliye yahan LLM SQL nahi chalate
    df = query_df(
        "SELECT subject_code, subject_name, marks, max_marks, status FROM results WHERE roll_no = :r",
        {"r": user.get("roll_no") or ""},
    )
    if df.empty:
        return {"answer": "Aapke roll number ka koi result abhi upload nahi hua hai.", "rows": []}

    total = df["marks"].sum()
    out_of = df["max_marks"].sum()
    failed = df[df["status"] == "fail"]["subject_name"].tolist()
    lines = ["Aapke total marks: %d / %d (%.1f%%)" % (total, out_of, total * 100 / out_of)]
    if failed:
        lines.append("Fail subjects: " + ", ".join(failed))
    else:
        lines.append("Sab subjects mein pass hain.")
    return {"answer": "\n".join(lines), "rows": records(df)}


# ---------- teacher ke common sawal, bina LLM ke ----------

def teacher_rules(question):
    q = question.lower()
    words = set(re.findall(r"[a-z+]+", q))
    wants_top = bool(words & {"top", "topper", "toppers", "highest", "rank"})
    wants_fail = any(w.startswith("fail") for w in words)
    wants_pass = any(w.startswith("pass") for w in words)
    if not (wants_top or wants_fail or wants_pass):
        return None

    df = query_df("SELECT roll_no, student_name, subject_code, subject_name, marks, max_marks, status FROM results")
    if df.empty:
        return {"answer": "Abhi koi result upload nahi hua hai. Teacher panel se CSV upload karo.", "rows": []}

    code = find_subject(q)
    name = None
    if code:
        sub = df[df["subject_code"] == code]
        if sub.empty:
            return {"answer": "Is subject ka result abhi upload nahi hua hai.", "rows": []}
        name = sub.iloc[0]["subject_name"]

    # --- top / topper ---
    if wants_top:
        m = re.search(r"\b(\d+)\b", q)
        n = int(m.group(1)) if m else (1 if "topper" in words else 3)
        n = max(1, min(n, 20))

        if code:
            sub = sub.copy()
            sub["percent"] = (sub["marks"] * 100 / sub["max_marks"]).round(1)
            top = sub.sort_values("percent", ascending=False).head(n)
            lines = ["%s ke top %d:" % (name, len(top))]
            for i, r in enumerate(top.to_dict("records"), 1):
                lines.append("%d. %s (%s) - %d/%d (%.1f%%)" % (i, r["student_name"], r["roll_no"], r["marks"], r["max_marks"], r["percent"]))
            return {"answer": "\n".join(lines), "rows": records(top[["student_name", "roll_no", "marks", "max_marks", "percent"]])}

        total = df.groupby(["roll_no", "student_name"], as_index=False).agg(total=("marks", "sum"), out_of=("max_marks", "sum"))
        total["percent"] = (total["total"] * 100 / total["out_of"]).round(1)
        top = total.sort_values("percent", ascending=False).head(n)
        lines = ["Poori class mein top %d (sab subjects ke total se):" % len(top)]
        for i, r in enumerate(top.to_dict("records"), 1):
            lines.append("%d. %s (%s) - %d/%d (%.1f%%)" % (i, r["student_name"], r["roll_no"], r["total"], r["out_of"], r["percent"]))
        return {"answer": "\n".join(lines), "rows": records(top)}

    # --- fail ---
    if wants_fail:
        f = df[df["status"] == "fail"]
        if code:
            f = f[f["subject_code"] == code]
            if f.empty:
                return {"answer": "%s mein koi student fail nahi hua." % name, "rows": []}
            lines = ["%s mein %d students fail hue:" % (name, len(f))]
            for r in f.to_dict("records"):
                lines.append("- %s (%s): %d/%d" % (r["student_name"], r["roll_no"], r["marks"], r["max_marks"]))
            return {"answer": "\n".join(lines), "rows": records(f[["student_name", "roll_no", "marks", "max_marks"]])}

        if f.empty:
            return {"answer": "Kisi subject mein koi student fail nahi hua.", "rows": []}
        per = f.groupby("subject_name").size().reset_index(name="fail_students")
        lines = ["%d students kam se kam ek subject mein fail hue." % f["roll_no"].nunique(), "Subject ke hisaab se:"]
        for r in per.to_dict("records"):
            lines.append("- %s: %d" % (r["subject_name"], r["fail_students"]))
        return {"answer": "\n".join(lines), "rows": records(per)}

    # --- pass ---
    if code:
        sub = df[df["subject_code"] == code]
        passed = int((sub["status"] == "pass").sum())
        return {"answer": "%s mein %d students pass hue (kul %d mein se)." % (name, passed, len(sub)), "rows": []}

    everyone = df["roll_no"].nunique()
    failed_any = df[df["status"] == "fail"]["roll_no"].nunique()
    return {"answer": "%d students sab subjects mein pass hue, %d students kisi na kisi subject mein fail hue (kul %d)."
                      % (everyone - failed_any, failed_any, everyone), "rows": []}


def teacher_query(question):
    try:
        out = teacher_rules(question)
    except Exception as e:
        print("result rules fail:", repr(e))
        out = None
    if out:
        return out

    prompt = SCHEMA_PROMPT.format(pass_percent=config.PASS_PERCENT)
    sql, df = question_to_df(question, prompt, TABLES)
    if df.empty:
        return {"answer": "Is sawal ka koi data nahi mila.", "rows": [], "sql": sql}

    system = ("Tum college ke teacher ke assistant ho. Sirf diye gaye data se jawab do, apni taraf se numbers mat banao. "
              "Teacher ki bhasha (Hindi/English/Hinglish) mein chhota jawab do.")
    answer = llm.ask(system, "Sawal: %s\n\nData:\n%s" % (question, df.head(40).to_string(index=False)))
    return {"answer": answer, "rows": records(df.head(20)), "sql": sql}


def answer(question, user):
    if user["role"] == "student":
        return student_own_result(user)
    return teacher_query(question)
