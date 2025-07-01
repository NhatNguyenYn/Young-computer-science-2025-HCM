import tkinter as tk
from tkinter import ttk, messagebox, Toplevel # ttk.Label, ttk.Button
import qrcode
import os
from PIL import Image, ImageTk
# from utils import QR_CODE_FOLDER, get_student_info, FONT_HEADER, FONT_MEDIUM, FONT_NORMAL, COLOR_BG_FRAME # Import constants
import utils # <<< THÊM DÒNG NÀY
import pandas as pd # <<< THÊM DÒNG NÀY VÌ BẠN CÓ SỬ DỤNG pd.notna

def generate_qr_code_file(student_sbd, name, student_class):
    if not student_sbd or not name: # student_class có thể không cần thiết cho QR content
        return None
    qr_content = str(student_sbd) # Chỉ lưu SBD vào QR
    qr = qrcode.make(qr_content)
    os.makedirs(utils.QR_CODE_FOLDER, exist_ok=True) # Sử dụng utils.QR_CODE_FOLDER
    file_path = os.path.join(utils.QR_CODE_FOLDER, f"{student_sbd}.png") # Sử dụng utils.QR_CODE_FOLDER
    try:
        qr.save(file_path)
        return file_path
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể lưu file QR code: {e}")
        return None

def show_student_qr_code(parent_window, student_sbd, df_students):
    # Bây giờ utils đã được import, bạn có thể gọi các hàm/biến của nó
    name, student_class_from_df = utils.get_student_info(student_sbd, df_students)

    # Đảm bảo student_class_from_df là một string, ngay cả khi nó là None hoặc NaN
    actual_student_class = str(student_class_from_df) if pd.notna(student_class_from_df) else "N/A" # pd.notna cần import pandas

    if not name: # Chỉ cần kiểm tra tên, vì lớp có thể N/A
        messagebox.showerror("Lỗi", f"Không tìm thấy thông tin cho SBD: {student_sbd}", parent=parent_window)
        return

    # Sử dụng actual_student_class (đã xử lý) để tạo QR
    qr_path = generate_qr_code_file(student_sbd, name, actual_student_class)

    if not qr_path or not os.path.exists(qr_path):
        messagebox.showerror("Lỗi", f"Không thể tạo hoặc tìm thấy file QR cho SBD: {student_sbd}", parent=parent_window)
        return

    qr_window = Toplevel(parent_window)
    qr_window.title(f"Mã QR - {student_sbd}")
    qr_window.geometry("380x450") # Kích thước có thể điều chỉnh
    qr_window.transient(parent_window); qr_window.grab_set()
    qr_window.configure(bg=utils.COLOR_BG_FRAME) # Sử dụng utils.COLOR_BG_FRAME

    main_frame = ttk.Frame(qr_window, padding="15")
    main_frame.pack(expand=True, fill=tk.BOTH)

    ttk.Label(main_frame, text=f"SBD: {student_sbd}", font=utils.FONT_HEADER).pack(pady=(0,10)) # utils.FONT_HEADER
    ttk.Label(main_frame, text=f"Họ và tên: {name}", font=utils.FONT_MEDIUM).pack(pady=5) # utils.FONT_MEDIUM
    ttk.Label(main_frame, text=f"Lớp: {actual_student_class}", font=utils.FONT_MEDIUM).pack(pady=5) # utils.FONT_MEDIUM

    try:
        qr_img_pil = Image.open(qr_path)
        qr_img_pil = qr_img_pil.resize((220, 220), Image.Resampling.LANCZOS) # Kích thước lớn hơn, dùng Lanczos
        qr_photo = ImageTk.PhotoImage(qr_img_pil)

        qr_label = ttk.Label(main_frame) # Dùng ttk.Label
        qr_label.pack(pady=20)
        qr_label.config(image=qr_photo)
        qr_label.image = qr_photo
    except Exception as e:
        ttk.Label(main_frame, text=f"Lỗi hiển thị ảnh QR: {e}", foreground=utils.COLOR_ERROR, font=utils.FONT_NORMAL).pack(pady=10) # utils.COLOR_ERROR, utils.FONT_NORMAL

    ttk.Button(main_frame, text="Đóng", command=qr_window.destroy, style="Accent.TButton").pack(pady=(15,0))