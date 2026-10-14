import re
import pandas as pd
from sqlalchemy import text
from db import engine
from utils import llm

# in words wali query kabhi nahi chalegi
BAD_WORDS = ["insert", "update", "delete", "drop", "alter", "create", "truncate",
             "replace", "grant", "revoke", "pragma", "attach", "exec", "outfile"]


def clean_sql(raw):
    s = raw.strip()
    s = re.sub(r"^```(?:sql)?", "", s, flags=re.I).strip()
    s = re.sub(r"```$", "", s).strip()
    return s


def is_safe_select(sql, allowed_tables):
    s = sql.strip().rstrip(";").strip()
    low = s.lower()

    if not low.startswith("select"):
        return False
    if ";" in s or "--" in s or "/*" in s:
        return False
    for w in BAD_WORDS:
        if re.search(r"\b" + w + r"\b", low):
            return False

    used = re.findall(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", low)
    if not used:
        return False
    for t in used:
        if t not in allowed_tables:
            return False
    return True


def run_select(sql, allowed_tables, limit=50):
    if not is_safe_select(sql, allowed_tables):
        raise ValueError("Ye query allowed nahi hai: " + sql)
    s = sql.strip().rstrip(";")
    if " limit " not in s.lower():
        s += " LIMIT %d" % limit
    with engine.connect() as conn:
        return pd.read_sql(text(s), conn)


def question_to_df(question, system_prompt, allowed_tables):
    """LLM se SQL banwata hai, check karke chalata hai. Ek baar retry bhi karta hai."""
    sql = clean_sql(llm.ask(system_prompt, question, temperature=0))
    try:
        return sql, run_select(sql, allowed_tables)
    except Exception as e:
        # ek baar error batake dobara try
        retry_msg = "%s\n\nPichli SQL: %s\nError: %s\nSahi SQL likho (sirf SELECT)." % (question, sql, e)
        sql = clean_sql(llm.ask(system_prompt, retry_msg, temperature=0))
        return sql, run_select(sql, allowed_tables)
