import re
import config
from utils import llm
from agents import result_agent, timetable_agent, assignment_agent

KEYWORDS = {
    "result": ["result", "marks", "fail", "pass", "percentage", "topper", "top", "rank", "grade", "number kitne", "students"],
    "timetable": ["timetable", "time table", "lecture", "period", "schedule", "class", "lab", "monday", "tuesday",
                  "wednesday", "thursday", "friday", "topic", "syllabus", "unit", "teacher", "kab hai", "aaj", "aj", "kal",
                  "subject", "kaun kaun"],
    "assignment": ["assignment", "submit", "deadline", "due", "reminder", "solve", "solution", "homework"],
}

CLASSIFY_PROMPT = """Tum college assistant ka task manager ho. Student/teacher ka sawal padho aur batao kaunsa agent handle karega.
Sirf ek shabd likho:
result     -> marks, pass/fail, percentage, topper
timetable  -> lecture, periods, schedule, subjects, teacher, current topic, syllabus
assignment -> assignments, last date, reminder, assignment solve karna
other      -> baaki sab (hello, general baatein)"""

AGENTS = {
    "result": result_agent,
    "timetable": timetable_agent,
    "assignment": assignment_agent,
}

HELP_TEXT = ("Namaste! Main aapka college assistant hoon. Main ye kar sakta hoon:\n"
             "- Timetable: \"aaj kaun kaun si class hai?\"\n"
             "- Result: \"mere marks kitne aaye?\"\n"
             "- Assignment: \"koi naya assignment aaya?\"")


def matches(word, q):
    # chhote shabd (top, due, lab, kal...) poore shabd ki tarah match hon, warna "top" -> "topic" pakad leta hai
    # lambe shabd shuru se match hon (assignment -> assignments)
    if len(word) <= 3:
        return re.search(r"\b" + re.escape(word) + r"\b", q) is not None
    return re.search(r"\b" + re.escape(word), q) is not None


def keyword_scores(q):
    q = q.lower()
    scores = {}
    for name, words in KEYWORDS.items():
        scores[name] = sum(1 for w in words if matches(w, q))
    return scores


def decide_agent(question):
    scores = keyword_scores(question)
    best = max(scores.values())
    winners = [n for n, s in scores.items() if s == best]

    # saaf jeetne wala mil gaya to LLM ki zarurat nahi
    if best > 0 and len(winners) == 1:
        return winners[0]

    # confusion hai (tie ya koi keyword nahi) to LLM se pucho
    try:
        out = llm.ask(CLASSIFY_PROMPT, question, temperature=0, max_tokens=10).lower()
        for name in ["result", "timetable", "assignment", "other"]:
            if name in out:
                return name
    except Exception as e:
        print("classify fail:", repr(e))

    return winners[0] if best > 0 else "other"


def handle(question, user):
    agent_name = decide_agent(question)
    print("router ->", agent_name, "|", question)

    if agent_name == "other":
        return {"agent": "other", "answer": HELP_TEXT, "rows": []}

    try:
        out = AGENTS[agent_name].answer(question, user)
    except Exception as e:
        print("agent error:", agent_name, repr(e))
        text = "%s agent ko sawal mil gaya, par jawab banate waqt error aaya." % agent_name
        if config.SHOW_ERRORS:
            text += "\nReason: %s" % str(e)[:300]
        out = {"answer": text, "rows": []}
    out["agent"] = agent_name
    return out
