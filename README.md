## 📊 Thống kê GitHub

![GitHub Stats](https://github-readme-stats.vercel.app/api?username=ttranvannam124-stack&show_icons=true&theme=tokyonight&locale=vi)

## 💻 Ngôn ngữ sử dụng

![Top Languages](https://github-readme-stats.vercel.app/api/top-langs/?username=ttranvannam124-stack&layout=compact&theme=tokyonight&locale=vi)
# Waste Reports — Quản lý phản ánh rác thải

Mini-project fullstack cá nhân giúp tiếp nhận phản ánh về rác thải,
phân công nhân viên xử lý và theo dõi kết quả.

## 1. Bài toán

Phản ánh về rác tồn đọng qua tin nhắn dễ bị bỏ sót,
khó theo dõi người phụ trách và tiến độ xử lý.

Ứng dụng tập trung các phản ánh vào một hệ thống với quy trình:

Chờ tiếp nhận → Đang xử lý → Hoàn thành.

## 2. Chức năng

| Vai trò   | Chức năng                                                    |
| --------- | ------------------------------------------------------------ |
| Người dân | Tạo phản ánh; xem danh sách và chi tiết phản ánh của mình    |
| Quản lý   | Xem tất cả; sửa, xóa phản ánh đang chờ; phân công nhân viên  |
| Nhân viên | Xem công việc được giao; nhập kết quả và xác nhận hoàn thành |

Chức năng chung:

- Đăng nhập và đăng xuất.
- Lọc phản ánh theo trạng thái.
- Thống kê số lượng theo trạng thái trong phạm vi được phép xem.
- Kiểm tra quyền truy cập ở backend.
- Lưu mật khẩu dưới dạng băm.

## 3. Công nghệ và kiến trúc

- Backend: Python, Flask.
- Database: PostgreSQL.
- Kết nối database: Psycopg 3.
- Frontend: HTML, CSS, JavaScript và Fetch API.
- Đăng nhập: Flask session.
- Cấu hình: python-dotenv.

Trình duyệt gửi yêu cầu tới REST API của Flask.
Flask kiểm tra dữ liệu, quyền truy cập và đọc/ghi PostgreSQL.
Giao diện và API được phục vụ bởi cùng ứng dụng Flask.

## 4. Các file chính

| File                 | Vai trò                                 |
| -------------------- | --------------------------------------- |
| app.py               | Backend, REST API và phân quyền         |
| templates/index.html | Giao diện và JavaScript gọi API         |
| schema.sql           | Tạo bảng dữ liệu                        |
| seed.py              | Tạo tài khoản mẫu với mật khẩu băm      |
| requirements.txt     | Các thư viện và phiên bản               |
| .env.example         | Cấu hình mẫu                            |
| .gitignore           | Loại trừ file riêng tư và môi trường ảo |

## 5. Hướng dẫn cài đặt trên Windows

### Bước 1: Chuẩn bị

Cài Python, PostgreSQL và Git.
Đảm bảo PostgreSQL đang chạy.

### Bước 2: Tải mã nguồn

Trên trang repository, chọn Code → Download ZIP.
Giải nén và mở PowerShell tại thư mục chứa app.py.

### Bước 3: Tạo môi trường và cài thư viện

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Bước 4: Tạo database và bảng

Trong pgAdmin:

1. Kết nối PostgreSQL.
2. Nhấp chuột phải Databases → Create → Database.
3. Đặt tên waste_reports và lưu.
4. Mở Query Tool của database waste_reports.
5. Mở file schema.sql và chạy toàn bộ.

Chạy schema.sql một lần trên database mới, chưa có các bảng
users và reports.

### Bước 5: Cấu hình kết nối

```powershell
Copy-Item .env.example .env
```

Sửa .env theo cấu hình PostgreSQL trên máy:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=waste_reports
DB_USER=postgres
DB_PASSWORD="your_postgresql_password"
SECRET_KEY=replace_with_a_random_secret
```

Tạo SECRET_KEY bằng lệnh:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Dán kết quả vào SECRET_KEY trong .env.
Không đưa file .env lên GitHub.

### Bước 6: Tạo tài khoản mẫu

```powershell
.\.venv\Scripts\python.exe seed.py
```

Script giữ nguyên tài khoản nếu username đã tồn tại.

| Vai trò   | Tên đăng nhập | Mật khẩu demo    |
| --------- | ------------- | ---------------- |
| Người dân | nguoidan      | DanDemo@123      |
| Quản lý   | quanly        | QuanLyDemo@123   |
| Nhân viên | nhanvien      | NhanVienDemo@123 |

Các tài khoản này chỉ dành cho chạy thử.

### Bước 7: Khởi động

```powershell
.\.venv\Scripts\python.exe app.py
```

Mở http://127.0.0.1:5000 trên trình duyệt.
Giữ terminal chạy trong lúc sử dụng ứng dụng.
Nhấn Ctrl + C để dừng.

Kiểm tra kết nối database tại:
http://127.0.0.1:5000/api/health

## 6. Kịch bản chạy thử

1. Đăng nhập bằng nguoidan và tạo một phản ánh.
2. Đăng xuất, đăng nhập bằng quanly.
3. Mở chi tiết và phân công nhân viên.
4. Đăng xuất, đăng nhập bằng nhanvien.
5. Mở công việc, nhập kết quả và xác nhận hoàn thành.
6. Đăng nhập lại bằng nguoidan để xem kết quả.
7. Tạo phản ánh khác để thử sửa và xóa bằng tài khoản quản lý
   khi phản ánh còn chờ tiếp nhận.

## 7. REST API

| Phương thức | Đường dẫn                    | Chức năng                |
| ----------- | ---------------------------- | ------------------------ |
| GET         | /api/health                  | Kiểm tra database        |
| POST        | /api/login                   | Đăng nhập                |
| POST        | /api/logout                  | Đăng xuất                |
| GET         | /api/me                      | Tài khoản đang đăng nhập |
| GET         | /api/reports                 | Danh sách theo quyền     |
| POST        | /api/reports                 | Tạo phản ánh             |
| GET         | /api/reports/{id}            | Chi tiết phản ánh        |
| PATCH       | /api/reports/{id}            | Sửa phản ánh đang chờ    |
| DELETE      | /api/reports/{id}            | Xóa phản ánh đang chờ    |
| GET         | /api/workers                 | Danh sách nhân viên      |
| PATCH       | /api/reports/{id}/assignment | Phân công                |
| PATCH       | /api/reports/{id}/completion | Hoàn thành               |

API nhận và trả JSON. Các API nghiệp vụ yêu cầu phiên đăng nhập.

## 8. Thiết kế dữ liệu

- users: tài khoản, tên hiển thị, mật khẩu băm, vai trò.
- reports: nội dung, địa điểm, người gửi, người xử lý,
  trạng thái, kết quả và thời gian cập nhật.

citizen_id và worker_id tham chiếu users.id.
Backend kiểm tra vai trò tương ứng trước khi thao tác.

## 9. Phạm vi và giới hạn

- Mini-project chạy thử trên máy cá nhân.
- Tài khoản được tạo bằng seed.py; chưa có đăng ký.
- Chưa có ảnh, bản đồ, thông báo hoặc lịch sử xử lý.
- Danh sách chưa phân trang.
- Máy chủ Flask hiện tại phục vụ phát triển, chưa phải cấu hình
  triển khai công khai trên Internet.
