import os

import psycopg
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

# Tài khoản dùng thử cho project
accounts = [
    ("Người dân mẫu", "nguoidan", "DanDemo@123", "citizen"),
    ("Quản lý mẫu", "quanly", "QuanLyDemo@123", "manager"),
    ("Nhân viên mẫu", "nhanvien", "NhanVienDemo@123", "worker"),
]


def seed_accounts():
    with psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    ) as connection:
        with connection.cursor() as cursor:
            for full_name, username, password, role in accounts:
                password_hash = generate_password_hash(password)

                cursor.execute(
                    """
                    INSERT INTO users
                        (full_name, username, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id;
                    """,
                    (full_name, username, password_hash, role),
                )

                if cursor.fetchone():
                    print(f"Đã tạo: {username}")
                else:
                    print(f"Đã tồn tại, giữ nguyên: {username}")

    print("Hoàn tất tạo tài khoản mẫu.")


if __name__ == "__main__":
    seed_accounts()