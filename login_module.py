import tkinter as tk
from tkinter import ttk, messagebox
from utils import USER_CREDENTIALS, get_student_info, FONT_APP_TITLE, FONT_NORMAL, FONT_MEDIUM_BOLD
import utils
def show_login_screen(parent_frame, on_success_callback, df_students):
    # Xóa widget cũ trong frame cha (parent_frame là self.login_frame từ main_app)
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # --- Cấu hình style nền (nếu cần màu khác biệt) ---
    # Bạn có thể định nghĩa style "Login.TFrame" trong main_app __init__
    # nếu muốn màu nền khác biệt cho màn hình login
    # parent_frame.config(style="Login.TFrame")

    # Tạo frame chứa nội dung chính, căn giữa màn hình
    login_content_frame = ttk.Frame(parent_frame) #, style="Login.TFrame") # Dùng style nếu có
    login_content_frame.pack(expand=True, anchor=tk.CENTER) # expand=True và anchor=tk.CENTER để căn giữa

    # --- Tiêu đề ---
    ttk.Label(login_content_frame, text="Đăng nhập Hệ thống", font=utils.FONT_APP_TITLE).pack(pady=(10, 30)) # Tăng pady dưới

    # --- Frame chứa ô nhập liệu ---
    field_frame = ttk.Frame(login_content_frame)
    field_frame.pack(pady=5, padx=20, fill=tk.X) # Thêm padx và fill X

    ttk.Label(field_frame, text="Tên đăng nhập:", font=utils.FONT_NORMAL).grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
    username_entry = ttk.Entry(field_frame, width=35, font=utils.FONT_NORMAL) # Tăng width
    username_entry.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)
    username_entry.focus_set()

    ttk.Label(field_frame, text="Mật khẩu:", font=utils.FONT_NORMAL).grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
    password_entry = ttk.Entry(field_frame, width=35, show="*", font=utils.FONT_NORMAL) # Tăng width
    password_entry.grid(row=1, column=1, padx=5, pady=8, sticky=tk.EW)

    field_frame.columnconfigure(1, weight=1) # Cho phép ô entry giãn ra

    # --- Chọn vai trò ---
    role_var = tk.StringVar(value="student")
    role_frame = ttk.Frame(login_content_frame)
    role_frame.pack(pady=(15,10))
    ttk.Label(role_frame, text="Vai trò:", font=utils.FONT_NORMAL).pack(side=tk.LEFT, padx=(0,10))
    ttk.Radiobutton(role_frame, text="Giáo viên", variable=role_var, value="teacher").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(role_frame, text="Học sinh", variable=role_var, value="student").pack(side=tk.LEFT, padx=5)

    # --- Nút Đăng nhập ---
    login_button = ttk.Button(login_content_frame, text="Đăng nhập", command=lambda: attempt_login(), style="Accent.TButton", width=18)
    login_button.pack(pady=25, ipady=6) # Tăng pady và ipady

    # --- Đường kẻ phân cách ---
    ttk.Separator(login_content_frame, orient='horizontal').pack(fill='x', padx=30, pady=(10, 15))

    # --- Thông tin liên hệ (Ví dụ) ---
    contact_frame = ttk.Frame(login_content_frame)
    contact_frame.pack(pady=5)
    ttk.Label(contact_frame, text="Hỗ trợ kỹ thuật:", font=utils.FONT_SMALL, foreground=utils.COLOR_TEXT_LIGHT).pack()
    ttk.Label(contact_frame, text="Email: ngonhatnguyen.developer@gmail.com | ĐT: 0966.04.3003", font=utils.FONT_SMALL, foreground=utils.COLOR_TEXT_LIGHT).pack()


    # --- Hàm xử lý đăng nhập (giữ nguyên logic, đảm bảo tham chiếu đúng widget) ---
    def attempt_login(event=None):
        username = username_entry.get().strip()
        password = password_entry.get()
        role = role_var.get()

        if not username or not password:
            messagebox.showwarning("Lỗi", "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.", parent=parent_frame.winfo_toplevel()) # Lấy cửa sổ gốc
            return

        login_successful = False; user_id = None; is_valid_sbd_check = True

        if role == "teacher":
            if username == utils.USER_CREDENTIALS["teacher"]["username"] and password == utils.USER_CREDENTIALS["teacher"]["password"]:
                login_successful = True; user_id = username
        elif role == "student":
            is_valid_sbd_check = False
            if df_students is not None and username in df_students.index: is_valid_sbd_check = True
            correct_password = password == utils.USER_CREDENTIALS["student"]["password"]
            if is_valid_sbd_check and correct_password:
                login_successful = True; user_id = username

        if login_successful:
            # Không cần messagebox thành công ở đây vì sẽ chuyển màn hình ngay
            parent_frame.pack_forget() # Ẩn frame login đi
            on_success_callback(role, user_id) # Gọi callback để hiển thị dashboard tương ứng
        else:
            error_message = "Sai Tên đăng nhập hoặc Mật khẩu."
            if role == "student" and not is_valid_sbd_check: error_message = "SBD không tồn tại hoặc sai Mật khẩu."
            messagebox.showerror("Lỗi Đăng nhập", error_message, parent=parent_frame.winfo_toplevel())
            password_entry.delete(0, tk.END); password_entry.focus_set()

    # Bind phím Enter
    password_entry.bind("<Return>", attempt_login)
    username_entry.bind("<Return>", lambda event: password_entry.focus_set())