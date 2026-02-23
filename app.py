"""
Resume Parser AI — Flask Application
=====================================
Main entry point for the web application.

Run with:
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""

import os
import io
import json
import sqlite3
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, jsonify, send_file, flash
)
from werkzeug.utils import secure_filename

# Import our custom resume parser
from utils.parser import parse_resume

# ==============================================================
#  APP CONFIGURATION
# ==============================================================

app = Flask(__name__)
app.secret_key = "resume_parser_ai_secret_2024"   # Change in production!

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
MAX_FILE_SIZE_MB = 16

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024  # 16 MB limit

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================================================
#  DATABASE HELPERS
# ==============================================================

DB_PATH = "database.db"


def get_db() -> sqlite3.Connection:
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # Allows dict-style column access
    return conn


def init_db() -> None:
    """
    Create the `resumes` table if it doesn't already exist.
    Called once at startup.
    """
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            filename         TEXT,
            name             TEXT,
            email            TEXT,
            phone            TEXT,
            linkedin         TEXT,
            github           TEXT,
            skills           TEXT,      -- stored as JSON string
            education        TEXT,
            experience       TEXT,
            projects         TEXT,
            skill_match      TEXT,      -- stored as JSON string
            raw_text_preview TEXT,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration-safe: add github column for existing databases
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(resumes)").fetchall()
    }
    if "github" not in columns:
        conn.execute("ALTER TABLE resumes ADD COLUMN github TEXT")

    conn.commit()
    conn.close()


def save_to_db(parsed: dict, filename: str) -> int:
    """
    Save parsed resume data to SQLite and return the new row ID.
    Skills and skill_match dicts are serialized to JSON strings.
    """
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO resumes
            (filename, name, email, phone, linkedin, github,
             skills, education, experience, projects,
             skill_match, raw_text_preview)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            parsed["name"],
            parsed["email"],
            parsed["phone"],
            parsed["linkedin"],
            parsed.get("github", "Not Found"),
            json.dumps(parsed["skills"]),
            parsed["education"],
            parsed["experience"],
            parsed["projects"],
            json.dumps(parsed["skill_match"]),
            parsed["raw_text_preview"],
        ),
    )
    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return resume_id


# ==============================================================
#  HELPER FUNCTIONS
# ==============================================================

def allowed_file(filename: str) -> bool:
    """Return True if the file extension is in the allowed list."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ==============================================================
#  ROUTES
# ==============================================================

@app.route("/")
def index():
    """
    Home page — shows the resume upload form.
    """
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_resume():
    """
    Handle the resume upload:
    1. Validate the uploaded file
    2. Save temporarily to disk
    3. Run the parser
    4. Delete the temp file
    5. Save results to SQLite
    6. Render the result page
    """

    # -- Validate file presence --
    if "resume" not in request.files:
        flash("No file part in the request. Please select a file.", "error")
        return redirect(url_for("index"))

    file = request.files["resume"]
    job_description = request.form.get("job_description", "").strip()

    if not file or file.filename == "":
        flash("No file selected. Please choose a PDF or DOCX resume.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash(
            "Unsupported file type. Only PDF and DOCX files are accepted.",
            "error",
        )
        return redirect(url_for("index"))

    # -- Save file to uploads/ folder temporarily --
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    temp_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    try:
        file.save(temp_path)

        # -- Parse the resume --
        parsed_data = parse_resume(temp_path, file_ext, job_description)

    except ValueError as ve:
        # Known parsing errors (bad file, empty content, etc.)
        flash(f"Parsing error: {str(ve)}", "error")
        return redirect(url_for("index"))

    except Exception as ex:
        # Unexpected errors
        flash(f"An unexpected error occurred: {str(ex)}", "error")
        return redirect(url_for("index"))

    finally:
        # Always delete the temp file, even if parsing failed
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # -- Save results to database --
    resume_id = save_to_db(parsed_data, filename)

    # -- Render result page --
    return render_template(
        "result.html",
        data=parsed_data,
        resume_id=resume_id,
        filename=filename,
    )


@app.route("/history")
def history():
    """
    Show a table of all previously parsed resumes.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, email, filename, created_at "
        "FROM resumes ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("history.html", resumes=rows)


@app.route("/view/<int:resume_id>")
def view_resume(resume_id: int):
    """
    Re-display a previously parsed resume by ID.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM resumes WHERE id = ?", (resume_id,)
    ).fetchone()
    conn.close()

    if not row:
        flash("Resume not found.", "error")
        return redirect(url_for("history"))

    # Rebuild the dict that result.html expects
    data = {
        "name":       row["name"],
        "email":      row["email"],
        "phone":      row["phone"],
        "linkedin":   row["linkedin"],
        "github":     row["github"] if "github" in row.keys() else "Not Found",
        "skills":     json.loads(row["skills"]) if row["skills"] else [],
        "education":  row["education"],
        "experience": row["experience"],
        "projects":   row["projects"],
        "skill_match": json.loads(row["skill_match"]) if row["skill_match"] else {
            "percentage": 0, "matched_skills": [], "missing_skills": [],
            "total_jd_skills": 0, "matched_count": 0
        },
        "raw_text_preview": row["raw_text_preview"],
    }
    return render_template(
        "result.html", data=data, resume_id=resume_id, filename=row["filename"]
    )


@app.route("/download/<int:resume_id>")
def download_json(resume_id: int):
    """
    Stream the parsed resume data as a downloadable JSON file.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM resumes WHERE id = ?", (resume_id,)
    ).fetchone()
    conn.close()

    if not row:
        flash("Resume not found.", "error")
        return redirect(url_for("history"))

    export = {
        "id":            row["id"],
        "filename":      row["filename"],
        "name":          row["name"],
        "email":         row["email"],
        "phone":         row["phone"],
        "linkedin":      row["linkedin"],
        "github":        row["github"] if "github" in row.keys() else "Not Found",
        "skills":        json.loads(row["skills"]) if row["skills"] else [],
        "education":     row["education"],
        "experience":    row["experience"],
        "projects":      row["projects"],
        "skill_match":   json.loads(row["skill_match"]) if row["skill_match"] else {},
        "parsed_at":     row["created_at"],
    }

    # Build a clean display name for the download file
    safe_name = re.sub(r"[^\w\s\-]", "", row["name"]).replace(" ", "_") if row["name"] else "resume"
    download_name = f"resume_{resume_id}_{safe_name}.json"

    json_bytes = json.dumps(export, indent=2, ensure_ascii=False).encode("utf-8")
    buffer = io.BytesIO(json_bytes)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/json",
    )


@app.route("/delete/<int:resume_id>", methods=["POST"])
def delete_resume(resume_id: int):
    """
    Delete a record from the database.
    """
    conn = get_db()
    conn.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
    conn.commit()
    conn.close()
    flash(f"Resume #{resume_id} deleted successfully.", "success")
    return redirect(url_for("history"))


@app.route("/api/resume/<int:resume_id>")
def api_get_resume(resume_id: int):
    """
    JSON API endpoint — returns parsed resume data for a given ID.
    Useful for integrations or frontend JS fetch calls.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM resumes WHERE id = ?", (resume_id,)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Resume not found"}), 404

    data = dict(row)
    data["skills"]      = json.loads(data["skills"])      if data["skills"]      else []
    data["skill_match"] = json.loads(data["skill_match"]) if data["skill_match"] else {}
    return jsonify(data)


@app.route("/api/resumes")
def api_list_resumes():
    """
    JSON API endpoint — returns a summary list of all parsed resumes.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, email, filename, created_at FROM resumes ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ==============================================================
#  ERROR HANDLERS
# ==============================================================

@app.errorhandler(413)
def file_too_large(e):
    flash(f"File is too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB.", "error")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ==============================================================
#  STARTUP
# ==============================================================

import re   # imported here to avoid circular issues at module top

if __name__ == "__main__":
    # Initialize the database on first run
    init_db()

    banner = """
+----------------------------------------------+
|       Resume Parser AI  -- Ready!            |
|                                              |
|  Open browser:  http://127.0.0.1:5000        |
|  Press Ctrl+C to stop the server.            |
+----------------------------------------------+
"""
    print(banner)
    app.run(debug=True, host="127.0.0.1", port=5000)
