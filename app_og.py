import os
import datetime
import jwt                                   # PyJWT
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()                                # reads the .env file

app = Flask(__name__)

LEVELS = ["Freshman", "Sophomore", "Junior", "Senior", "Master's"]

# ---------- Tokens ----------
REPORTS_TOKEN = "reports-token-123"          # fixed token
SECRET_KEY = os.environ["SECRET_KEY"]        # signs student tokens (from .env)
STUDENTS_SECRET = os.environ["STUDENTS_SECRET"]
STUDENT_TOKEN_SECONDS = 15 * 60       # student tokens live 15 minutes

def get_bearer():
    """Return the token from the Authorization header, or None."""
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):]
    return None

def check_reports_token():
    token = get_bearer()
    if token is None:
        return jsonify({"error": "missing token"}), 401
    if token == REPORTS_TOKEN:
        return None
    return jsonify({"error": "invalid token"}), 401

def check_students_token():
    token = get_bearer()
    if token is None:
        return jsonify({"error": "missing token"}), 401
    if token == REPORTS_TOKEN:
        return jsonify({"error": "this token is not allowed here"}), 403
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid token"}), 401
    return None

@app.route("/auth/student-token", methods=["POST"])
def student_token():
    data = request.get_json(silent=True) or {}
    if data.get("secret") != STUDENTS_SECRET:
        return jsonify({"error": "invalid secret"}), 401
    payload = {
        "scope": "students",
        "exp": datetime.datetime.now(datetime.timezone.utc)
               + datetime.timedelta(seconds=STUDENT_TOKEN_SECONDS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "expires_in_seconds": STUDENT_TOKEN_SECONDS}), 200

# ---------- Classes ----------
class Student:
    def __init__(self, ID_S, first_name, last_name, DMaj, level):
        self.ID_S = ID_S
        self.first_name = first_name
        self.last_name = last_name
        self.DMaj = DMaj
        self.level = level

    def to_dict(self):
        return {"ID_S": self.ID_S, "first_name": self.first_name,
                "last_name": self.last_name, "DMaj": self.DMaj,
                "level": self.level}

class Report:
    def __init__(self, ID_R, title, type, K1, K2, K3, publishing_date, ID_S):
        self.ID_R = ID_R
        self.title = title
        self.type = type
        self.K1 = K1
        self.K2 = K2
        self.K3 = K3
        self.publishing_date = publishing_date
        self.ID_S = ID_S

    def to_dict(self):
        return {"ID_R": self.ID_R, "title": self.title, "type": self.type,
                "K1": self.K1, "K2": self.K2, "K3": self.K3,
                "publishing_date": self.publishing_date, "ID_S": self.ID_S}

# ---------- Storage (version 1: lists) ----------
students = []
reports = []
next_ID_S = 1
next_ID_R = 1

# ---------- Validation helper ----------
def missing_fields(data, required):
    if not isinstance(data, dict):
        return required
    return [f for f in required if f not in data or data[f] in ("", None)]

# ---------- Endpoints ----------
@app.route("/students", methods=["POST"])
def add_student():
    global next_ID_S
    data = request.get_json(silent=True)

    missing = missing_fields(data, ["first_name", "last_name", "DMaj", "level"])
    if missing:
        return jsonify({"error": "missing fields: " + ", ".join(missing)}), 400
    if data["DMaj"] not in (0, 1):
        return jsonify({"error": "DMaj must be 0 or 1"}), 400
    if data["level"] not in LEVELS:
        return jsonify({"error": "level must be one of: " + ", ".join(LEVELS)}), 400

    student = Student(next_ID_S, data["first_name"], data["last_name"],
                      data["DMaj"], data["level"])
    students.append(student)
    next_ID_S += 1
    return jsonify(student.to_dict()), 201

@app.route("/students/<int:ID_S>", methods=["GET"])
def get_student(ID_S):
    error = check_students_token()           # time-limited token required
    if error:
        return error
    for s in students:
        if s.ID_S == ID_S:
            return jsonify(s.to_dict()), 200
    return jsonify({"error": "student not found"}), 404

@app.route("/reports", methods=["POST"])
def add_report():
    global next_ID_R
    data = request.get_json(silent=True)

    missing = missing_fields(data, ["title", "type", "K1", "K2", "K3",
                                    "publishing_date", "ID_S"])
    if missing:
        return jsonify({"error": "missing fields: " + ", ".join(missing)}), 400

    student = None
    for s in students:
        if s.ID_S == data["ID_S"]:
            student = s
    if student is None:
        return jsonify({"error": "student not found"}), 404

    count = sum(1 for r in reports if r.ID_S == student.ID_S)
    max_reports = 2 if student.DMaj == 1 else 1
    if count >= max_reports:
        return jsonify({"error": "this student has reached their report limit"}), 400

    report = Report(next_ID_R, data["title"], data["type"],
                    data["K1"], data["K2"], data["K3"],
                    data["publishing_date"], student.ID_S)
    reports.append(report)
    next_ID_R += 1
    return jsonify(report.to_dict()), 201

@app.route("/reports", methods=["GET"])
def get_reports():
    error = check_reports_token()            # fixed token required
    if error:
        return error
    return jsonify([r.to_dict() for r in reports]), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)