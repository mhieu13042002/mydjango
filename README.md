# 🤖 Smart Expense Manager — Quản lý chi tiêu cá nhân tích hợp AI

Web app Django + MySQL, AI phân loại chi tiêu, nhận diện ảnh offline, phát hiện
chi tiêu bất thường, dự báo cuối tháng, quản lý ngân sách & mục tiêu tiết kiệm,
thông báo, giao diện Bootstrap 5 hiện đại (dark/light mode, AOS animation).

## ✨ Tính năng

- **Xác thực đầy đủ**: đăng ký, đăng nhập, đăng xuất, quên mật khẩu (qua email),
  đổi mật khẩu, cập nhật hồ sơ + ảnh đại diện.
- **Dashboard**: tổng thu/chi/số dư/tỉ lệ tiết kiệm, biểu đồ tròn theo danh mục,
  biểu đồ đường theo ngày, nhận xét AI, dự báo cuối tháng, cảnh báo bất thường.
- **Thêm chi tiêu 2 cách**:
  1. Nhập thủ công, AI gợi ý danh mục theo tên khoản chi (gõ tới đâu gợi ý tới đó).
  2. **Chụp/tải ảnh** → AI nhận diện vật thể (offline, mã nguồn mở) → gợi ý danh
     mục → xác nhận số tiền → hệ thống dùng Pillow ghi số tiền + ngày lên ảnh.
- **Lịch sử chi tiêu** dạng Card: tìm kiếm, lọc theo loại/danh mục/ngày/tháng/năm/
  khoảng tiền, phân trang, sửa/xoá không reload trang.
- **Phát hiện bất thường**: so sánh khoản chi mới với trung bình lịch sử cùng
  danh mục, cảnh báo ngay khi lưu.
- **Ngân sách theo danh mục/tháng**: thanh tiến trình, tự động thông báo khi đạt
  80% / 100% / vượt ngân sách.
- **Mục tiêu tiết kiệm**: tự tính số tiền cần tiết kiệm mỗi tháng/ngày, theo dõi
  tiến độ, lịch sử nạp tiền.
- **Gợi ý tối ưu chi tiêu**: tối thiểu 5 gợi ý cụ thể dựa trên thói quen chi tiêu
  thực tế (ví dụ: "Nếu giảm Grab từ 12 xuống 8 lần/tháng, tiết kiệm ~320.000đ").
- **Trung tâm thông báo**: vượt ngân sách, đạt mục tiêu, chi tiêu bất thường...
- **Audit log**: ghi nhận các thao tác thay đổi dữ liệu quan trọng.

## 🧠 Về AI trong dự án này

| Tính năng | Công nghệ | Ghi chú |
|---|---|---|
| Gợi ý danh mục từ tên khoản chi | Bộ từ khóa tiếng Việt | Tức thời, chính xác cao với mô tả rõ ràng |
| Nhận diện vật thể trong ảnh | OpenCV DNN + MobileNet-SSD (Caffe, huấn luyện sẵn trên PASCAL VOC — 20 lớp) | **Miễn phí, offline hoàn toàn**, không cần API key |
| Phát hiện bất thường | Thống kê z-score theo lịch sử từng danh mục | |
| Dự báo cuối tháng | Ngoại suy tốc độ chi tiêu từ đầu tháng | |
| Gợi ý tối ưu | Phân tích tần suất & tổng chi theo từng khoản lặp lại | |

**Về độ chính xác nhận diện ảnh**: bộ 20 lớp VOC (xe cộ, người, đồ nội thất,
động vật, chai lọ...) khá tổng quát, không chuyên biệt cho hoá đơn Việt Nam như
OpenAI Vision. Vì vậy giao diện luôn hiển thị độ tin cậy và cho phép đổi danh
mục ngay nếu AI đoán sai (đúng như hành vi một trợ lý AI thật, không giả vờ
chính xác tuyệt đối). Nếu bạn có OpenAI API key và muốn nâng cấp độ chính xác,
xem mục "Nâng cấp lên OpenAI Vision" bên dưới.

## 🚀 Cài đặt

### Yêu cầu
- Python 3.10+
- MySQL Server 5.7+ / MariaDB 10.4+ **đã cài và đang chạy** (XAMPP, MySQL
  Workbench, hoặc MySQL/MariaDB cài riêng đều được)
- Dự án dùng **PyMySQL** (thuần Python) thay cho `mysqlclient`, nên **không cần**
  cài thêm Visual C++ Build Tools hay MySQL Connector C trên Windows.

### Bước 1 — Tạo database MySQL

```sql
CREATE DATABASE smart_expense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'expense_user'@'localhost' IDENTIFIED BY 'mật_khẩu_của_bạn';
GRANT ALL PRIVILEGES ON smart_expense.* TO 'expense_user'@'localhost';
FLUSH PRIVILEGES;
```

### Bước 2 — Cài đặt Python

```powershell
cd smart_expense
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Bước 3 — Cấu hình `.env`

Mở file `.env` (đã có sẵn ở thư mục gốc) và điền thông tin MySQL của bạn:

```
DB_ENGINE=mysql
DB_NAME=smart_expense
DB_USER=expense_user
DB_PASSWORD=mật_khẩu_của_bạn
DB_HOST=127.0.0.1
DB_PORT=3306
```

> Muốn chạy nhanh không cần MySQL để xem thử giao diện? Đổi `DB_ENGINE=sqlite`.

### Bước 4 — Khởi tạo database & dữ liệu mặc định

```powershell
python manage.py migrate
python manage.py seed_categories
python manage.py createsuperuser
```

### Bước 5 — Chạy server

```powershell
python manage.py runserver
```

Mở trình duyệt: **http://127.0.0.1:8000**
Trang quản trị: **http://127.0.0.1:8000/admin**

## 📁 Cấu trúc dự án

```
smart_expense/
├── config/            # Settings, URL gốc
├── accounts/          # Đăng ký/đăng nhập/hồ sơ
├── core/               # Category, Expense, Dashboard, CRUD, upload ảnh AI
├── budgets/            # Ngân sách theo danh mục
├── goals/              # Mục tiêu tiết kiệm
├── notifications/      # Trung tâm thông báo
├── ai_engine/           # Lõi AI: categorizer, image_recognition, analytics, image_annotate
├── ai_models/           # Model MobileNet-SSD (Caffe) đã huấn luyện sẵn
├── templates/            # Toàn bộ giao diện Bootstrap 5
├── static/               # CSS/JS
└── requirements.txt
```

## 🔐 Bảo mật đã áp dụng

- CSRF protection (Django middleware mặc định, bật trên mọi form/AJAX POST)
- Password hashing (PBKDF2 mặc định của Django)
- Validation cả client-side (HTML5) lẫn server-side (Django Forms)
- Giới hạn định dạng ảnh (jpg/png/webp) và dung lượng (8MB) khi upload
- SQL Injection: dùng Django ORM, không raw SQL nối chuỗi
- `AuditLog` ghi lại các thao tác thay đổi dữ liệu

## ⚙️ Nâng cấp lên OpenAI Vision (tuỳ chọn)

Nếu bạn muốn độ chính xác nhận diện ảnh cao hơn, mở `ai_engine/image_recognition.py`
và thay hàm `recognize_image()` bằng lời gọi OpenAI Vision API (`gpt-4o` hoặc
tương đương) — truyền base64 ảnh, yêu cầu model trả về JSON `{label, category,
confidence}`. Phần còn lại của hệ thống (preview, lưu ảnh chú thích bằng Pillow,
cho phép đổi danh mục) không cần thay đổi gì.

## 🌐 Triển khai production

```powershell
pip install gunicorn whitenoise
python manage.py collectstatic
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```
Nhớ đặt `DEBUG=False` và điền `ALLOWED_HOSTS` thật trong `.env`, đồng thời cấu
hình `EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` thật để tính năng quên
mật khẩu gửi được email (mặc định đang dùng console backend — email sẽ chỉ in
ra terminal, không gửi thật).

## ☁️ Deploy lên Railway

Dự án đã có sẵn `Procfile` + `railway.json` để Railway tự động chạy migrate,
seed danh mục, collectstatic và khởi động gunicorn — bạn chỉ cần:

1. **Push code lên GitHub** (đảm bảo có đủ `Procfile`, `railway.json`, `requirements.txt` mới).
2. Trên Railway, tạo project mới từ repo GitHub này.
3. **Thêm database MySQL**: trong project Railway, bấm **"+ New"** → **"Database"** → **"Add MySQL"**.
4. **Gắn biến kết nối DB vào service web**: vào service web (Django) → tab **Variables**
   → **"+ New Variable"** → chọn **"Add Reference"** → chọn biến `MYSQL_URL` (hoặc
   `DATABASE_URL`) từ service MySQL vừa tạo. App đã tự đọc biến này, không cần
   cấu hình `DB_*` thủ công trên Railway.
5. Vào tab **Variables** của service web, thêm các biến sau (bấm "Raw Editor" để dán nhanh):
   ```
   SECRET_KEY=<tạo chuỗi ngẫu nhiên dài, ví dụ chạy: python -c "import secrets; print(secrets.token_urlsafe(50))">
   DEBUG=False
   ```
   (Railway tự cấp `PORT` và `RAILWAY_PUBLIC_DOMAIN`, app đã tự đọc 2 biến này, không cần thêm.)
6. Railway sẽ tự build & deploy. Vào tab **Deployments → xem log** nếu muốn theo dõi
   quá trình migrate/collectstatic/gunicorn khởi động.
7. Sau khi deploy xong, mở domain Railway cấp (dạng `xxx.up.railway.app`) để vào web.
8. Tạo tài khoản quản trị trên Railway (mở tab **Shell** của service, hoặc dùng nút
   "Deploy Command" chạy `python manage.py createsuperuser` một lần).

### ⚠️ Giới hạn cần biết khi deploy Railway (miễn phí)
- **Ảnh upload không tồn tại lâu dài**: ổ đĩa của Railway là *ephemeral* (bị xoá
  sạch mỗi lần deploy lại/khởi động lại container). Ảnh chi tiêu người dùng
  upload qua tính năng "Ảnh AI" sẽ mất khi Railway redeploy. Để lưu ảnh vĩnh
  viễn, cần gắn thêm **Railway Volume** (mount vào `MEDIA_ROOT`) hoặc dùng
  storage ngoài như AWS S3/Cloudinary — không nằm trong phạm vi bản demo này.
- Gói miễn phí Railway giới hạn giờ chạy/tháng — app có thể tự sleep nếu hết quota.
- Email quên mật khẩu mặc định chỉ in ra log (console backend) — cần điền
  `EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` thật vào Variables nếu
  muốn gửi email thật trên Railway.

### 🔍 Nếu vẫn gặp lỗi 500 sau khi deploy lại
Vào Railway → service web → tab **Deployments** → bấm vào lần deploy mới nhất
→ xem **"Deploy Logs"** hoặc **"HTTP Logs"**. Traceback lỗi thật (dòng cuối
cùng, kiểu `django.db.utils.OperationalError: ...` hoặc tương tự) sẽ nằm ở đó
— gửi mình đoạn log đó để mình xác định chính xác nguyên nhân.



## 🩹 Xử lý lỗi thường gặp trên Windows

- **Lỗi `MariaDB 10.5 or later is required`**: máy bạn đang dùng MariaDB cũ hơn
  (ví dụ XAMPP thường đi kèm MariaDB 10.4). Đảm bảo cài đúng version Django
  trong `requirements.txt` (`Django>=4.2,<5.0`) — bản này tương thích MariaDB
  10.4 trở lên. Nếu trước đó bạn lỡ cài Django mới hơn, chạy:
  `pip install "Django==4.2.17" --force-reinstall`.
- **`&&` không chạy trong PowerShell**: chạy từng lệnh trên một dòng riêng.
- **Lỗi `Access denied for user`**: kiểm tra lại `DB_USER`/`DB_PASSWORD` trong `.env`
  khớp với tài khoản MySQL đã tạo ở Bước 1 (hoặc `root` + mật khẩu rỗng nếu dùng XAMPP mặc định).

Chúc bạn triển khai thành công! 🎉
