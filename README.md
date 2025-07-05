# 🏆 Young Computer Science 2025 – HCM

> 🇻🇳 Dự án nộp thi Tin học trẻ TP.HCM năm 2025
> 🇬🇧 A submission project for the 2025 Ho Chi Minh City Young Computer Science Contest

---

## 🎯 Overview | Tổng quan

**Young Computer Science 2025 – HCM** là một hệ thống quản lý sự kiện học sinh hiện đại, giúp tổ chức và vận hành các hoạt động trong trường học một cách trực quan, chính xác và chuyên nghiệp. Hệ thống kết hợp mã QR, giao diện đồ họa thân thiện và quản lý dữ liệu đa định dạng để tăng tính tự động hóa và hiệu quả.

This project is a modern school event management system designed to support student participation, attendance, and logistics using a blend of technologies like QR scanning, visual GUI, and structured data models.

---

## ✅ Features | Tính năng chính

| Tính năng               | Mô tả                                                      |
| ----------------------- | ---------------------------------------------------------- |
| 📸 QR Attendance        | Scan mã QR bằng webcam để điểm danh học sinh               |
| 🪑 Seat Map Manager     | Quản lý sơ đồ chỗ ngồi và cập nhật trạng thái ghế          |
| 🎟️ QR Ticket Generator | Tạo vé tham dự có mã QR và thông tin chi tiết sự kiện      |
| 📅 Personal Schedule    | Hiển thị thời khóa biểu cá nhân theo từng học sinh         |
| 🗂️ Data Management     | Lưu trữ và quản lý học sinh, vé, lịch trình, thông báo,... |

---

## ⚙️ Technologies Used | Công nghệ sử dụng

| Technology | Purpose                           |
| ---------- | --------------------------------- |
| Python 3.x | Ngôn ngữ lập trình chính          |
| Tkinter    | Giao diện đồ họa người dùng (GUI) |
| OpenCV     | Xử lý hình ảnh webcam, quét mã QR |
| Pillow     | Xử lý ảnh như logo, ảnh học sinh  |
| Pandas     | Đọc dữ liệu từ file Excel         |
| JSON       | Cấu hình và dữ liệu mẫu           |

---

## 🚀 How to Run | Cách chạy chương trình

### 1. Cài đặt thư viện cần thiết:

```bash
pip install opencv-python pillow pandas
```

### 2. Chạy chương trình:

```bash
python main_app.py
```

Ensure that your webcam and necessary data files are available.

---

## 📁 Folder Structure | Cấu trúc thư mục

```
Young-Computer-Science-2025-HCM/
├── main_app.py               # 🇬🇧 Main launcher / 🇻🇳 File chạy chính
├── student_manager.py        # 🇬🇧 Student CRUD logic / 🇻🇳 Quản lý học sinh
├── qr_attendance.py          # 🇬🇧 Webcam QR scanner / 🇻🇳 Quét mã QR điểm danh
├── seat_map.py               # 🇬🇧 Seat layout UI / 🇻🇳 Giao diện sơ đồ chỗ ngồi
├── ticket_generator.py       # 🇬🇧 Create QR event tickets / 🇻🇳 Sinh vé tham dự
├── schedule_viewer.py        # 🇬🇧 Display student schedules / 🇻🇳 Hiển thị thời khóa biểu
│
├── templates/                # 🇬🇧 Ticket & layout templates / 🇻🇳 Template vé & sơ đồ
│
├── data/
│   ├── students.xlsx         # 🇬🇧 Student list / 🇻🇳 Danh sách học sinh
│   ├── schedule.xlsx         # 🇬🇧 Event schedules / 🇻🇳 Thời khóa biểu
│   ├── config.json           # 🇬🇧 App settings / 🇻🇳 Cấu hình hệ thống
│   └── seats.json            # 🇬🇧 Seat status map / 🇻🇳 Dữ liệu sơ đồ chỗ ngồi
│
├── school_assets/
│   └── school_logo.png       # 🇬🇧 School logo / 🇻🇳 Logo trường học
│
├── Student_Photos/
│   └── default_avatar.png    # 🇬🇧 Default profile / 🇻🇳 Ảnh mặc định học sinh
│
├── icons/
│   ├── qr_icon.png           # 🇬🇧 QR icon / 🇻🇳 Icon mã QR
│   ├── seat_icon.png         # 🇬🇧 Seat icon / 🇻🇳 Icon ghế
│   └── schedule_icon.png     # 🇬🇧 Schedule icon / 🇻🇳 Icon thời khóa biểu
│
├── README.md                 # 📄 Project overview
└── .gitignore                # 🚫 Ignore venv, cache, etc.
```

---

## 📌 Notes & Author

Developed by **Ngô Nhật Nguyên (nnYunaXYZ)** 🇻🇳
Built for the 2025 HCMC Young Computer Science Contest. The project showcases real-world applications of Python, computer vision, and interface design tailored to the education domain.

---

## 🪪 License

Licensed under the **MIT License** – Free for academic and learning use.
