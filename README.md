# 🏆 Young Computer Science 2025 - HCM

🎓 **Dự án nộp thi Tin học trẻ TP.HCM năm 2025.**  
> Một hệ thống quản lý sự kiện học sinh hiện đại, kết hợp mã QR, giao diện trực quan, lưu trữ dữ liệu đa định dạng.

---

## 🧠 Mô tả

Hệ thống này giúp tổ chức và quản lý sự kiện học đường với các chức năng chính:

- ✅ Điểm danh bằng mã QR (Scan bằng webcam)
- ✅ Quản lý sơ đồ chỗ ngồi và cập nhật ghế không khả dụng
- ✅ Sinh vé tham dự có mã QR và thông tin chi tiết
- ✅ Hiển thị thời khóa biểu cá nhân cho học sinh
- ✅ Lưu trữ & quản lý: học sinh, lịch trình, vé, thông báo...

---

## 🛠 Công nghệ sử dụng

| Công nghệ     | Mục đích                         |
|--------------|----------------------------------|
| Python 3     | Ngôn ngữ lập trình chính         |
| Tkinter      | Giao diện người dùng (GUI)       |
| OpenCV       | Quét mã QR qua webcam            |
| Pillow       | Xử lý ảnh (logo, thẻ học sinh)   |
| Pandas       | Đọc file Excel                   |
| JSON         | Lưu trữ cấu hình & dữ liệu mẫu   |

---

## 🚀 Cách chạy chương trình

1. Đảm bảo đã cài Python 3.x và pip.
2. Cài các thư viện cần thiết:
pip install opencv-python pillow pandas
3. Chạy ứng dụng.
python main_app.py


Cấu trúc thư mục:
Young computer science 2025 HCM/
├── main_app.py                 # File chạy chính
├── *.py                       # Các module chức năng
├── *.json, *.xlsx             # Dữ liệu mẫu
├── icons/                     # Biểu tượng giao diện
├── school_assets/             # Logo trường học
├── Student_Photos/            # Ảnh học sinh mặc định
├── data/                      # Dữ liệu cấu hình (nếu có)
├── README.md                  # File mô tả dự án
└── .gitignore                 # Bỏ qua file không cần push

Tác giả nnYunaXYZ