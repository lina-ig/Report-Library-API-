import os
import datetime
import jwt
import pymysql
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort

load_dotenv()

app = Flask(__name__)
app.config["API_TITLE"] = "PFE Reports API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
api = Api(app)          # makes abort() return clean JSON errors

LEVELS = ["Freshman", "Sophomore", "Junior", "Senior", "Master's"]

# ---------- Tokens ----------
REPORTS_TOKEN = "reports-token-123"
SECRET_KEY = os.environ["SECRET_KEY"]
STUDENTS_SECRET = os.environ["STUDENTS_SECRET"]
STUDENT_TOKEN_SECONDS = 15 * 60

def get_bearer():
    header = request.headers.get("Authorization", "")
    return header[7:] if header.startswith("Bearer ") else None

def require_reports_token():
    token = get_bearer()
    if token is None:
        abort(401, message="missing token")
    if token != REPORTS_TOKEN:
        abort(401, message="invalid token")

def require_students_token():
    token = get_bearer()
    if token is None:
        abort(401, message="missing token")
    if token == REPORTS_TOKEN:
        abort(403, message="this token is not allowed here")
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        abort(401, message="token expired")
    except jwt.InvalidTokenError:
        abort(401, message="invalid token")

@app.route("/auth/student-token", methods=["POST"])
def student_token():
    data = request.get_json(silent=True) or {}
    if data.get("secret") != STUDENTS_SECRET:
        abort(401, message="invalid secret")
    payload = {"scope": "students",
               "exp": datetime.datetime.now(datetime.timezone.utc)
                      + datetime.timedelta(seconds=STUDENT_TOKEN_SECONDS)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "expires_in_seconds": STUDENT_TOKEN_SECONDS}), 200

# ---------- Database ----------
def get_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor)

def query(sql, params=(), one=False, write=False):
    """Run one SQL statement. Reads return rows, writes return (new_id, rows_changed)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if write:
                conn.commit()
                return cur.lastrowid, cur.rowcount
            return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()

def init_db():
    query("""CREATE TABLE IF NOT EXISTS students (
        ID_S INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        DMaj TINYINT NOT NULL,
        level VARCHAR(20) NOT NULL)""", write=True)
    query("""CREATE TABLE IF NOT EXISTS reports (
        ID_R INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        ttype VARCHAR(50) NOT NULL,
        K1 VARCHAR(100) NOT NULL,
        K2 VARCHAR(100) NOT NULL,
        K3 VARCHAR(100) NOT NULL,
        publishing_date VARCHAR(10) NOT NULL,
        ID_S INT NOT NULL,
        FOREIGN KEY (ID_S) REFERENCES students(ID_S) ON DELETE CASCADE)""",
        write=True)

init_db()

# ---------- Validation ----------
def missing_fields(data, required):
    if not isinstance(data, dict):
        return required
    return [f for f in required if f not in data or data[f] in ("", None)]

def validate_student(data):
    missing = missing_fields(data, ["first_name", "last_name", "DMaj", "level"])
    if missing:
        abort(400, message="missing fields: " + ", ".join(missing))
    if data["DMaj"] not in (0, 1):
        abort(400, message="DMaj must be 0 or 1")
    if data["level"] not in LEVELS:
        abort(400, message="level must be one of: " + ", ".join(LEVELS))

def validate_report(data, with_student=False):
    required = ["title", "ttype", "K1", "K2", "K3", "publishing_date"]
    if with_student:
        required.append("ID_S")
    missing = missing_fields(data, required)
    if missing:
        abort(400, message="missing fields: " + ", ".join(missing))

def count_reports(ID_S):
    return query("SELECT COUNT(*) AS n FROM reports WHERE ID_S = %s",
                 (ID_S,), one=True)["n"]

def find_student(ID_S):
    student = query("SELECT * FROM students WHERE ID_S = %s", (ID_S,), one=True)
    if student is None:
        abort(404, message="student not found")
    return student

def find_report(ID_R):
    report = query("SELECT * FROM reports WHERE ID_R = %s", (ID_R,), one=True)
    if report is None:
        abort(404, message="report not found")
    return report

# ---------- Students ----------
students_blp = Blueprint("students", __name__, description="Students")

@students_blp.route("/students")
class StudentList(MethodView):
    def post(self):
        data = request.get_json(silent=True)
        validate_student(data)
        new_id, _ = query(
            "INSERT INTO students (first_name, last_name, DMaj, level) "
            "VALUES (%s, %s, %s, %s)",
            (data["first_name"], data["last_name"], data["DMaj"], data["level"]),
            write=True)
        return jsonify(find_student(new_id)), 201

@students_blp.route("/students/<int:ID_S>")
class StudentItem(MethodView):
    def get(self, ID_S):
        require_students_token()
        return jsonify(find_student(ID_S)), 200

    def put(self, ID_S):
        require_students_token()
        find_student(ID_S)
        data = request.get_json(silent=True)
        validate_student(data)
        max_reports = 2 if data["DMaj"] == 1 else 1
        if count_reports(ID_S) > max_reports:
            abort(400, message="student has more reports than this DMaj allows")
        query("UPDATE students SET first_name=%s, last_name=%s, DMaj=%s, level=%s "
              "WHERE ID_S=%s",
              (data["first_name"], data["last_name"], data["DMaj"],
               data["level"], ID_S), write=True)
        return jsonify(find_student(ID_S)), 200

    def delete(self, ID_S):
        require_students_token()
        find_student(ID_S)
        query("DELETE FROM students WHERE ID_S = %s", (ID_S,), write=True)
        return "", 204

# ---------- Reports ----------
reports_blp = Blueprint("reports", __name__, description="Reports")

@reports_blp.route("/reports")
class ReportList(MethodView):
    def get(self):
        require_reports_token()
        return jsonify(query("SELECT * FROM reports")), 200

    def post(self):
        data = request.get_json(silent=True)
        validate_report(data, with_student=True)
        student = find_student(data["ID_S"])
        max_reports = 2 if student["DMaj"] == 1 else 1
        if count_reports(student["ID_S"]) >= max_reports:
            abort(400, message="this student has reached their report limit")
        new_id, _ = query(
            "INSERT INTO reports (title, ttype, K1, K2, K3, publishing_date, ID_S) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (data["title"], data["ttype"], data["K1"], data["K2"], data["K3"],
             data["publishing_date"], student["ID_S"]), write=True)
        return jsonify(find_report(new_id)), 201

@reports_blp.route("/reports/<int:ID_R>")
class ReportItem(MethodView):
    def put(self, ID_R):
        require_reports_token()
        find_report(ID_R)
        data = request.get_json(silent=True)
        validate_report(data)
        query("UPDATE reports SET title=%s, ttype=%s, K1=%s, K2=%s, K3=%s, "
              "publishing_date=%s WHERE ID_R=%s",
              (data["title"], data["ttype"], data["K1"], data["K2"], data["K3"],
               data["publishing_date"], ID_R), write=True)
        return jsonify(find_report(ID_R)), 200

    def delete(self, ID_R):
        require_reports_token()
        find_report(ID_R)
        query("DELETE FROM reports WHERE ID_R = %s", (ID_R,), write=True)
        return "", 204

api.register_blueprint(students_blp)
api.register_blueprint(reports_blp)

if __name__ == "__main__":
    app.run(debug=True)