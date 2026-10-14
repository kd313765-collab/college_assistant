# Multi-Agent College Assistant

Student ya teacher ka sawal **Task Manager** samajhta hai aur sahi agent ko bhej deta hai.

| Agent | Kaun use karta hai | Kya karta hai |
|-------|--------------------|---------------|
| Result agent | Teacher (student sirf apna result dekh sakta hai) | Marks, pass/fail, topper, Excel/CSV upload |
| Timetable agent | Student | Din ka timetable, subjects, teacher, abhi ka topic, syllabus |
| Assignment agent | Student | Assignments ki list, reminder, assignment solve karna |

## Folder structure

```
college_assistant/
  backend/
    app.py               Flask routes + scheduler
    config.py, db.py     settings aur MySQL/SQLite tables
    seed.py              demo data bharta hai
    rag.py               syllabus ke liye chhota TF-IDF RAG
    agents/              task_manager, result, timetable, assignment
    utils/               llm (Groq), sql_helper, voice (ElevenLabs), auth, mailer, importer
    data/                timetable.csv, sample_results.csv, syllabus/*.txt
  frontend/              React + Vite (chat, login, teacher panel)
```

## Backend chalane ke steps

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # Mac/Linux: cp .env.example .env
```

`.env` mein `GROQ_API_KEY` daalo (console.groq.com se free key milti hai).

**MySQL (SQL Workbench) use karna hai to:**
1. Workbench mein `CREATE DATABASE college_assistant;` chalao
2. `.env` mein likho: `DATABASE_URL=mysql+pymysql://root:PASSWORD@localhost:3306/college_assistant`

DATABASE_URL blank chhodoge to apne aap sqlite file ban jayegi (testing ke liye theek hai).

```bash
python seed.py     # tables + demo data (dobara chalaoge to reset ho jayega)
python app.py      # http://localhost:5000
```

**Dikkat aaye to pehle:** `python check.py` chalao. Ye batata hai ki Groq key/model chal raha hai ya nahi aur router kis sawal ko kaunse agent ko bhej raha hai.

## Frontend chalane ke steps

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

## Demo login

- Student: `student@college.test` / `student123` (roll no R001)
- Teacher: `teacher@college.test` / `teacher123`

## App ke pages

- **Chat:** timetable, result, topic ke common sawal bina Groq ke bhi chalte hain (rules pehle, LLM baad mein).
- **Assignments tab:** description, last date, file download aur "Solve karke samjhao" (isme Groq chahiye).
- **Results tab (teacher):** subject-wise pass/fail, topper aur sabke marks.
- **Teacher panel:** result CSV upload, assignment post, current topic set karna aur list dekhna.

## Kuch zaruri baatein

- **Result data dummy hai** (sample_results.csv). Asli data teacher panel se upload karo.
- **Timetable** photo dekh ke banaya hai, ek baar `data/timetable.csv` mein check kar lena.
- Syllabus mein NLP ka code `KC072` hai par timetable mein `BCAI052`. Maine timetable wala code use kiya hai.
- Result aur timetable ke liye LLM sirf **SELECT** query banata hai. `sql_helper.py` har query check karta hai (sirf allowed tables, koi insert/delete nahi).
- Student ko doosre ke marks nahi dikhte, uske liye alag code path hai (LLM SQL nahi chalta).
- Reminders roz subah 8 baje (IST) chalte hain. Email ke liye `.env` mein SMTP daalo, warna sirf app ke andar dikhenge.
- Voice ke liye `ELEVEN_API_KEY` chahiye. Bina key ke chat normal chalti hai.
- Groq ke model naam badalte rehte hain. Agar error aaye to `.env` mein `GROQ_MODEL` console se check karke badal do.

## Main API routes

```
POST /api/login            POST /api/register
POST /api/chat             GET  /api/subjects
GET  /api/assignments      POST /api/assignments        (teacher)
POST /api/results/upload   (teacher)
POST /api/topics           (teacher)
GET  /api/notifications    POST /api/notifications/read
POST /api/voice/stt        POST /api/voice/tts
```
