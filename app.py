import os
import re
import csv
import sqlite3
import joblib
import pandas as pd

from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "spam_model.pkl"
)

DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(
    DATABASE_DIR,
    "smartspam.db"
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app = Flask(__name__)

app.secret_key = "smartspam_secret_key_2026"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Load trained model
model = None

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully!")
else:
    print("WARNING: Model not found.")
    print("Run: python train_model.py")


# ---------------- DATABASE ---------------- #

def get_db_connection():

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL,
            risk_level TEXT,
            urls_found INTEGER,
            suspicious_words TEXT,
            created_at TEXT
        )
    """)

    connection.commit()

    connection.close()


initialize_database()


# ---------------- HELPER FUNCTIONS ---------------- #

SUSPICIOUS_WORDS = [
    "free",
    "winner",
    "won",
    "prize",
    "claim",
    "urgent",
    "offer",
    "cash",
    "click",
    "congratulations",
    "limited",
    "reward",
    "money",
    "bonus",
    "call now",
    "guaranteed"
]


def find_urls(message):

    pattern = r"https?://[^\s]+|www\.[^\s]+"

    urls = re.findall(pattern, message)

    return urls


def find_suspicious_words(message):

    message_lower = message.lower()

    found_words = []

    for word in SUSPICIOUS_WORDS:

        if word in message_lower:

            found_words.append(word)

    return found_words


def analyze_message(message):

    global model

    if model is None:

        return None

    prediction_value = model.predict([message])[0]

    probabilities = model.predict_proba([message])[0]

    confidence = round(max(probabilities) * 100, 2)

    prediction = "SPAM" if prediction_value == 1 else "HAM"

    urls = find_urls(message)

    suspicious_words = find_suspicious_words(message)

    # Risk calculation
    risk_score = 0

    if prediction == "SPAM":
        risk_score += 60

    risk_score += min(len(urls) * 10, 20)

    risk_score += min(len(suspicious_words) * 3, 20)

    if risk_score >= 70:
        risk_level = "High"

    elif risk_score >= 40:
        risk_level = "Medium"

    else:
        risk_level = "Low"


    return {
        "prediction": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "urls": urls,
        "suspicious_words": suspicious_words,
        "word_count": len(message.split()),
        "character_count": len(message)
    }


def save_prediction(message, result):

    connection = get_db_connection()

    connection.execute("""
        INSERT INTO predictions
        (
            message,
            prediction,
            confidence,
            risk_level,
            urls_found,
            suspicious_words,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        message,
        result["prediction"],
        result["confidence"],
        result["risk_level"],
        len(result["urls"]),
        ", ".join(result["suspicious_words"]),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    connection.commit()

    connection.close()


# ---------------- HOME ---------------- #

@app.route("/", methods=["GET", "POST"])
def index():

    result = None
    message = ""

    if request.method == "POST":

        message = request.form.get("message", "").strip()

        if not message:

            flash("Please enter a message.")

        elif model is None:

            flash("Model not found. Please run train_model.py first.")

        else:

            result = analyze_message(message)

            save_prediction(message, result)

    return render_template(
        "index.html",
        result=result,
        message=message
    )


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    connection = get_db_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM predictions"
    ).fetchone()[0]

    spam = connection.execute(
        "SELECT COUNT(*) FROM predictions WHERE prediction = 'SPAM'"
    ).fetchone()[0]

    ham = connection.execute(
        "SELECT COUNT(*) FROM predictions WHERE prediction = 'HAM'"
    ).fetchone()[0]

    recent = connection.execute("""
        SELECT *
        FROM predictions
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        total=total,
        spam=spam,
        ham=ham,
        recent=recent
    )


# ---------------- HISTORY ---------------- #

@app.route("/history")
def history():

    search = request.args.get("search", "")

    connection = get_db_connection()

    if search:

        records = connection.execute("""
            SELECT *
            FROM predictions
            WHERE message LIKE ?
               OR prediction LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        records = connection.execute("""
            SELECT *
            FROM predictions
            ORDER BY id DESC
        """).fetchall()

    connection.close()

    return render_template(
        "history.html",
        records=records,
        search=search
    )


# ---------------- DELETE HISTORY ---------------- #

@app.route("/delete/<int:prediction_id>")
def delete_prediction(prediction_id):

    connection = get_db_connection()

    connection.execute(
        "DELETE FROM predictions WHERE id = ?",
        (prediction_id,)
    )

    connection.commit()

    connection.close()

    flash("Prediction deleted successfully.")

    return redirect(url_for("history"))


# ---------------- BATCH ANALYSIS ---------------- #

@app.route("/batch", methods=["GET", "POST"])
def batch_analysis():

    results = []

    if request.method == "POST":

        if "file" not in request.files:

            flash("Please upload a CSV file.")

            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":

            flash("Please select a CSV file.")

            return redirect(request.url)

        if file:

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                file.filename
            )

            file.save(filepath)

            try:

                df = pd.read_csv(filepath)

                # Find text column
                if "message" in df.columns:

                    messages = df["message"]

                else:

                    messages = df.iloc[:, 0]


                for message in messages.dropna():

                    result = analyze_message(str(message))

                    results.append({
                        "message": str(message),
                        "prediction": result["prediction"],
                        "confidence": result["confidence"],
                        "risk_level": result["risk_level"]
                    })

            except Exception as error:

                flash(f"Error reading CSV: {error}")

    return render_template(
        "batch_analysis.html",
        results=results
    )


# ---------------- EXPORT CSV ---------------- #

@app.route("/export")
def export_history():

    connection = get_db_connection()

    records = connection.execute("""
        SELECT *
        FROM predictions
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    export_path = os.path.join(
        UPLOAD_FOLDER,
        "smartspam_report.csv"
    )

    with open(
        export_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "ID",
            "Message",
            "Prediction",
            "Confidence",
            "Risk Level",
            "URLs Found",
            "Suspicious Words",
            "Date"
        ])

        for record in records:

            writer.writerow([
                record["id"],
                record["message"],
                record["prediction"],
                record["confidence"],
                record["risk_level"],
                record["urls_found"],
                record["suspicious_words"],
                record["created_at"]
            ])

    return send_file(
        export_path,
        as_attachment=True
    )


# ---------------- ABOUT ---------------- #

@app.route("/about")
def about():

    return render_template("about.html")


# ---------------- RUN ---------------- #

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )