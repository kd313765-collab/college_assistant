import pandas as pd
from sqlalchemy import text
from db import engine
import config

NEEDED = ["roll_no", "student_name", "subject_code", "subject_name", "marks", "max_marks"]


def import_results(file_storage):
    """Teacher ki CSV / Excel file se results table update karta hai."""
    name = (file_storage.filename or "").lower()
    if name.endswith(".csv"):
        df = pd.read_csv(file_storage)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(file_storage)
    else:
        raise ValueError("Sirf CSV ya Excel file upload karo")

    # column names ko saaf karo: "Roll No" -> roll_no
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    missing = [c for c in NEEDED if c not in df.columns]
    if missing:
        raise ValueError("Ye columns missing hain: " + ", ".join(missing))

    df = df[NEEDED].dropna()
    df["roll_no"] = df["roll_no"].astype(str).str.strip()
    df["subject_code"] = df["subject_code"].astype(str).str.strip().str.upper()
    df["marks"] = pd.to_numeric(df["marks"], errors="coerce")
    df["max_marks"] = pd.to_numeric(df["max_marks"], errors="coerce")
    df = df.dropna()

    pct = df["marks"] * 100 / df["max_marks"]
    df["status"] = pct.apply(lambda p: "pass" if p >= config.PASS_PERCENT else "fail")

    with engine.begin() as conn:
        # purane rows hata do (same student + subject)
        for _, r in df.iterrows():
            conn.execute(
                text("DELETE FROM results WHERE roll_no = :r AND subject_code = :s"),
                {"r": r["roll_no"], "s": r["subject_code"]},
            )
        df.to_sql("results", conn, if_exists="append", index=False)
    return len(df)
