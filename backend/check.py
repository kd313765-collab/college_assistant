"""Pehle ye chalao:  python check.py
Batata hai ki Groq key/model chal raha hai ya nahi, aur router kis sawal ko kaunse agent ko bhej raha hai."""
import config
from utils import llm
from agents import task_manager

print("GROQ key mili:", bool(config.GROQ_API_KEY))
print("Model:", config.GROQ_MODEL)

try:
    print("Groq reply:", llm.ask("Ek shabd mein jawab do.", "hello bolo"))
except Exception as e:
    print("Groq ERROR:", repr(e))

print()
tests = [
    "Aaj kaun kaun si class hai?",
    "Monday ka timetable batao",
    "DAA mein abhi kaunsa topic chal raha hai?",
    "Mere marks kitne aaye?",
    "Kitne students fail hue?",
    "Koi naya assignment aaya?",
    "Assignment 3 solve karo",
    "hello",
]
for q in tests:
    print("%-45s -> %s" % (q, task_manager.decide_agent(q)))
