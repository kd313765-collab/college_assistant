"""Pehli baar chalao:  python seed.py
Tables banata hai aur demo data bhar deta hai (dobara chalaoge to sab reset ho jayega)."""
from datetime import datetime, date
import pandas as pd
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from db import engine, metadata, init_db
import config


def main():
    metadata.drop_all(engine)
    init_db()

    # timetable
    tt = pd.read_csv("data/timetable.csv")
    tt.to_sql("timetable", engine, if_exists="append", index=False)

    # results (pass/fail yahin nikal lete hain)
    res = pd.read_csv("data/sample_results.csv")
    res["status"] = (res["marks"] * 100 / res["max_marks"]).apply(
        lambda p: "pass" if p >= config.PASS_PERCENT else "fail")
    res.to_sql("results", engine, if_exists="append", index=False)

    with engine.begin() as conn:
        # demo users
        conn.execute(text("INSERT INTO users (name, email, password_hash, role, roll_no) VALUES (:n, :e, :p, :r, :roll)"), [
            {"n": "Dr. Shalini Gupta", "e": "teacher@college.test", "p": generate_password_hash("teacher123"),
             "r": "teacher", "roll": None},
            {"n": "Aarav Singh", "e": "student@college.test", "p": generate_password_hash("student123"),
             "r": "student", "roll": "R001"},
        ])

        # abhi kaunsa topic chal raha hai (sample)
        conn.execute(text("INSERT INTO current_topics (subject_code, unit, topic, updated_on) VALUES (:c, :u, :t, :n)"), [
            {"c": "BCS503", "u": "3", "t": "Greedy methods - Prim's and Kruskal's algorithms", "n": datetime.now()},
            {"c": "BCS501", "u": "3", "t": "Normalization - 2NF, 3NF and BCNF", "n": datetime.now()},
            {"c": "BCS054", "u": "4", "t": "C++ functions - function overloading", "n": datetime.now()},
            {"c": "BCDS501", "u": "2", "t": "Regression modeling", "n": datetime.now()},
            {"c": "BCAI052", "u": "2", "t": "Context free grammars and parsing", "n": datetime.now()},
            {"c": "BNC501", "u": "1", "t": "Fundamental rights and duties", "n": datetime.now()},
        ])

        # ek sample assignment (college portal wala DAA Assignment-3)
        conn.execute(text(
            "INSERT INTO assignments (subject_code, subject_name, title, description, posted_by, posted_on, due_date, max_marks) "
            "VALUES (:c, :sn, :t, :d, :p, :po, :due, :m)"),
            {"c": "BCS503", "sn": "Design and Analysis of Algorithm", "t": "DAA Assignment-3",
             "d": "Dijkstra, Prim and Kruskal algorithms par questions solve karo. Har algorithm ka time complexity bhi likho.",
             "p": "Dr. Shalini Gupta", "po": datetime(2026, 9, 24, 15, 10), "due": date(2026, 10, 18), "m": 10})

    print("Done. Demo login:")
    print("  teacher@college.test / teacher123")
    print("  student@college.test / student123")


if __name__ == "__main__":
    main()
