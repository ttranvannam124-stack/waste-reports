import os
from functools import wraps

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask import Flask, request, session, g, render_template
from werkzeug.security import check_password_hash

load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=1024 * 1024,
)
app.json.ensure_ascii = True


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


def require_login(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = session.get("user_id")

            if user_id is None:
                return {"message": "Bạn cần đăng nhập."}, 401

            with get_connection() as conn:
                user = conn.execute(
                    """
                    SELECT id, full_name, username, role
                    FROM users WHERE id = %s
                    """,
                    (user_id,),
                ).fetchone()

            if user is None:
                session.clear()
                return {"message": "Tài khoản không còn tồn tại."}, 401

            if roles and user["role"] not in roles:
                return {"message": "Bạn không có quyền thao tác."}, 403

            g.user = user
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_report(data, partial=False):
    allowed = {"title", "location", "description"}

    if not isinstance(data, dict) or not data:
        return None, "Cần gửi dữ liệu JSON."

    if set(data) - allowed:
        return None, "Chỉ được gửi title, location, description."

    if not partial and set(data) != allowed:
        return None, "Cần nhập đủ tiêu đề, địa điểm và mô tả."

    cleaned = {}
    limits = {"title": 200, "location": 1000, "description": 5000}

    for key, value in data.items():
        if not isinstance(value, str) or not value.strip():
            return None, f"Trường {key} không được để trống."

        cleaned[key] = value.strip()

        if len(cleaned[key]) > limits[key]:
            return None, f"Trường {key} tối đa {limits[key]} ký tự."

    return cleaned, None


@app.errorhandler(psycopg.Error)
def database_error(error):
    app.logger.exception("Lỗi database")
    return {"message": "Lỗi database. Kiểm tra terminal chạy Flask."}, 500


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT current_database() AS name"
        ).fetchone()

    return {
        "status": "ok",
        "database": row["name"],
        "message": "Kết nối PostgreSQL thành công!",
    }


@app.post("/api/login")
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Dữ liệu phải là JSON."}, 400

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return {"message": "Vui lòng nhập tên đăng nhập và mật khẩu."}, 400

    if not username.strip() or not password:
        return {"message": "Vui lòng nhập tên đăng nhập và mật khẩu."}, 400

    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = %s",
            (username.strip(),),
        ).fetchone()

    if user is None or not check_password_hash(
        user["password_hash"], password
    ):
        return {"message": "Sai tên đăng nhập hoặc mật khẩu."}, 401

    session.clear()
    session["user_id"] = user["id"]

    return {
        "message": "Đăng nhập thành công!",
        "user": {
            key: user[key]
            for key in ("id", "full_name", "username", "role")
        },
    }


@app.post("/api/logout")
def logout():
    session.clear()
    return {"message": "Đã đăng xuất."}


@app.get("/api/me")
@require_login()
def me():
    return {"user": g.user}


@app.get("/api/reports")
@require_login("citizen", "manager", "worker")
def list_reports():
    query = "SELECT * FROM reports"
    params = ()

    if g.user["role"] == "citizen":
        query += " WHERE citizen_id = %s"
        params = (g.user["id"],)
    elif g.user["role"] == "worker":
        query += " WHERE worker_id = %s"
        params = (g.user["id"],)

    query += " ORDER BY created_at DESC, id DESC"

    with get_connection() as conn:
        reports = conn.execute(query, params).fetchall()

    return {"reports": reports}


@app.get("/api/reports/<int:report_id>")
@require_login("citizen", "manager", "worker")
def get_report(report_id):
    query = "SELECT * FROM reports WHERE id = %s"
    params = [report_id]

    if g.user["role"] == "citizen":
        query += " AND citizen_id = %s"
        params.append(g.user["id"])
    elif g.user["role"] == "worker":
        query += " AND worker_id = %s"
        params.append(g.user["id"])

    with get_connection() as conn:
        report = conn.execute(query, params).fetchone()

    if report is None:
        return {"message": "Không tìm thấy phản ánh được phép xem."}, 404

    return {"report": report}


@app.post("/api/reports")
@require_login("citizen")
def create_report():
    data, error = validate_report(request.get_json(silent=True))

    if error:
        return {"message": error}, 400

    with get_connection() as conn:
        report = conn.execute(
            """
            INSERT INTO reports
                (title, location, description, citizen_id)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["title"],
                data["location"],
                data["description"],
                g.user["id"],
            ),
        ).fetchone()

    return {
        "message": "Tạo phản ánh thành công!",
        "report": report,
    }, 201


@app.patch("/api/reports/<int:report_id>")
@require_login("manager")
def update_report(report_id):
    data, error = validate_report(
        request.get_json(silent=True), partial=True
    )

    if error:
        return {"message": error}, 400

    with get_connection() as conn:
        report = conn.execute(
            "SELECT * FROM reports WHERE id = %s FOR UPDATE",
            (report_id,),
        ).fetchone()

        if report is None:
            return {"message": "Không tìm thấy phản ánh."}, 404

        if report["status"] != "pending":
            return {"message": "Chỉ sửa phản ánh chờ tiếp nhận."}, 409

        updated = conn.execute(
            """
            UPDATE reports
            SET title = %s, location = %s, description = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
            """,
            (
                data.get("title", report["title"]),
                data.get("location", report["location"]),
                data.get("description", report["description"]),
                report_id,
            ),
        ).fetchone()

    return {"message": "Đã cập nhật.", "report": updated}


@app.delete("/api/reports/<int:report_id>")
@require_login("manager")
def delete_report(report_id):
    with get_connection() as conn:
        report = conn.execute(
            "SELECT status FROM reports WHERE id = %s FOR UPDATE",
            (report_id,),
        ).fetchone()

        if report is None:
            return {"message": "Không tìm thấy phản ánh."}, 404

        if report["status"] != "pending":
            return {"message": "Chỉ xóa phản ánh chờ tiếp nhận."}, 409

        conn.execute(
            "DELETE FROM reports WHERE id = %s", (report_id,)
        )

    return {"message": "Đã xóa phản ánh."}


@app.get("/api/workers")
@require_login("manager")
def list_workers():
    with get_connection() as conn:
        workers = conn.execute(
            """
            SELECT id, full_name FROM users
            WHERE role = 'worker'
            ORDER BY full_name, id
            """
        ).fetchall()

    return {"workers": workers}


@app.patch("/api/reports/<int:report_id>/assignment")
@require_login("manager")
def assign_report(report_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"message": "Cần gửi dữ liệu JSON."}, 400

    worker_id = data.get("worker_id")

    if type(worker_id) is not int or worker_id <= 0:
        return {"message": "Hãy chọn nhân viên hợp lệ."}, 400

    with get_connection() as conn:
        report = conn.execute(
            "SELECT status FROM reports WHERE id = %s FOR UPDATE",
            (report_id,),
        ).fetchone()

        if report is None:
            return {"message": "Không tìm thấy phản ánh."}, 404

        if report["status"] != "pending":
            return {"message": "Phản ánh đã được phân công."}, 409

        worker = conn.execute(
            "SELECT id FROM users WHERE id = %s AND role = 'worker'",
            (worker_id,),
        ).fetchone()

        if worker is None:
            return {"message": "Nhân viên không hợp lệ."}, 400

        updated = conn.execute(
            """
            UPDATE reports
            SET worker_id = %s, status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
            """,
            (worker_id, report_id),
        ).fetchone()

    return {"message": "Đã phân công xử lý.", "report": updated}


@app.patch("/api/reports/<int:report_id>/completion")
@require_login("worker")
def complete_report(report_id):
    data = request.get_json(silent=True)
    note = data.get("result_note") if isinstance(data, dict) else None

    if not isinstance(note, str) or not note.strip():
        return {"message": "Cần nhập kết quả xử lý."}, 400

    if len(note.strip()) > 5000:
        return {"message": "Kết quả tối đa 5000 ký tự."}, 400

    with get_connection() as conn:
        report = conn.execute(
            """
            SELECT status FROM reports
            WHERE id = %s AND worker_id = %s
            FOR UPDATE
            """,
            (report_id, g.user["id"]),
        ).fetchone()

        if report is None:
            return {"message": "Không tìm thấy công việc được giao."}, 404

        if report["status"] != "in_progress":
            return {"message": "Công việc không ở trạng thái đang xử lý."}, 409

        updated = conn.execute(
            """
            UPDATE reports
            SET result_note = %s, status = 'completed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
            """,
            (note.strip(), report_id),
        ).fetchone()

    return {"message": "Đã hoàn thành xử lý.", "report": updated}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)