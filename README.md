# Resume Parser AI

A production-ready AI-powered resume parsing web application built with **Python**, **Flask**, **spaCy**, and **Bootstrap 5**.

---

## Features

| Feature | Details |
|---|---|
| File Support | PDF and DOCX/DOC |
| Extracts | Name, Email, Phone, LinkedIn, Skills, Education, Experience, Projects |
| LinkedIn | Full URL extraction (not truncated) |
| Skill Matching | Match % against a job description |
| Database | SQLite — all results stored & retrievable |
| Download | Export any parsed resume as JSON |
| History | View and manage all parsed resumes |
| Error Handling | Friendly messages for bad files, empty content, wrong formats |

---

## Project Structure

```
resume-parser/
├── app.py                     ← Flask application (main entry point)
├── requirements.txt           ← Python dependencies
├── database.db                ← SQLite database (auto-created on first run)
├── create_sample_resume.py    ← Script to generate a test resume
├── README.md
│
├── utils/
│   ├── __init__.py
│   └── parser.py              ← All NLP/parsing logic
│
├── templates/
│   ├── index.html             ← Upload page
│   ├── result.html            ← Parsed results display
│   ├── history.html           ← History of all parses
│   └── 404.html               ← Custom 404 page
│
├── static/
│   └── style.css              ← Custom CSS
│
└── uploads/                   ← Temporary file storage (auto-created)
```

---

## Setup Instructions (Anaconda / VS Code)

### Step 1 — Create a Conda Environment

Open **Anaconda Prompt** or the VS Code terminal and run:

```bash
conda create -n resume_parser python=3.10 -y
conda activate resume_parser
```

### Step 2 — Navigate to the Project Folder

```bash
cd "C:\Users\Navee\OneDrive\Desktop\first task_pinnacle lab"
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Download the spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

### Step 5 — (Optional) Generate a Sample Resume for Testing

```bash
python create_sample_resume.py
```

This creates `sample_resume.docx` in the project folder — ready to upload.

### Step 6 — Run the Application

```bash
python app.py
```

### Step 7 — Open in Browser

```
http://127.0.0.1:5000
```

---

## Quick Start (All-in-one commands)

```bash
conda create -n resume_parser python=3.10 -y
conda activate resume_parser
cd "C:\Users\Navee\OneDrive\Desktop\first task_pinnacle lab"
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python create_sample_resume.py
python app.py
```

---

## How to Use

1. Go to `http://127.0.0.1:5000`
2. Click **Browse** or drag & drop a **PDF** or **DOCX** resume
3. *(Optional)* Paste a job description to get a **skill-match score**
4. Click **Parse Resume**
5. View the extracted details on the results page
6. Click **Download JSON** to export the data

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Upload form |
| POST | `/upload` | Parse a resume |
| GET | `/history` | All parsed resumes |
| GET | `/view/<id>` | View a specific result |
| GET | `/download/<id>` | Download JSON |
| POST | `/delete/<id>` | Delete a record |
| GET | `/api/resume/<id>` | JSON API for single resume |
| GET | `/api/resumes` | JSON API list of all resumes |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'spacy'` | Run `pip install spacy` |
| `OSError: [E050] Can't find model 'en_core_web_sm'` | Run `python -m spacy download en_core_web_sm` |
| `ModuleNotFoundError: No module named 'PyPDF2'` | Run `pip install PyPDF2` |
| `ModuleNotFoundError: No module named 'docx'` | Run `pip install python-docx` |
| PDF shows no text extracted | The PDF is likely image-based (scanned). Use OCR tools like Tesseract first. |
| Port 5000 already in use | Change port in `app.py`: `app.run(port=5001)` |

---

## Tech Stack

- **Python 3.10+**
- **Flask 2.3** — Web framework
- **spaCy 3.7** — Named Entity Recognition (NER)
- **PyPDF2 3.0** — PDF text extraction
- **python-docx 0.8** — Word document parsing
- **SQLite** — Lightweight embedded database
- **Bootstrap 5** — Responsive UI
- **Jinja2** — HTML templating

---

## Sample Job Description (for skill-match testing)

Paste this into the Job Description box:

```
We are looking for a Python backend developer with strong experience in:
Flask or Django, REST API design, PostgreSQL, Redis, Docker, and AWS.
Familiarity with CI/CD pipelines, Git, and Agile/Scrum methodology is required.
Knowledge of machine learning with Scikit-Learn or TensorFlow is a plus.
```
