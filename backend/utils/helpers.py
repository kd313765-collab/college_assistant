import json
import re
from datetime import datetime, timedelta, timezone

import config
from db import query_df

try:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo(config.TIMEZONE)
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))   # tzdata na ho tab bhi chale

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# sawal mein jo shabd mile -> subject code
SUBJECT_WORDS = {
    "daa": "BCS503", "algorithm": "BCS503",
    "dbms": "BCS501", "database": "BCS501",
    "oosd": "BCS054", "c++": "BCS054", "object oriented": "BCS054",
    "nlp": "BCAI052", "natural language": "BCAI052",
    "idav": "BCDS501", "data analytics": "BCDS501", "analytics": "BCDS501",
    "constitution": "BNC501", "aptitude": "APT501", "employability": "ET501",
    "technical training": "TT501",
}


def now_ist():
    return datetime.now(IST)


def records(df):
    # to_dict mein kabhi kabhi numpy types aa jate hain jo jsonify nahi kar pata
    return json.loads(df.to_json(orient="records"))


def find_subject(q):
    q = q.lower()
    for word, code in SUBJECT_WORDS.items():
        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", q):
            return code
    return None


def subject_name(code):
    df = query_df("SELECT subject_name FROM timetable WHERE subject_code = :c LIMIT 1", {"c": code})
    return df.iloc[0]["subject_name"] if not df.empty else code


def find_day(q):
    """(din, label) wapas deta hai, jaise ('Monday', 'Kal'). Kuch na mile to None."""
    now = now_ist()
    words = set(re.findall(r"[a-z]+", q.lower()))
    if words & {"kal", "tomorrow", "tmrw"}:
        return DAY_NAMES[(now + timedelta(days=1)).weekday()], "Kal"
    if words & {"aaj", "aj", "today"}:
        return DAY_NAMES[now.weekday()], "Aaj"
    for name in DAY_NAMES:
        if name.lower() in words:
            return name, None
    return None
