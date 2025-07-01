# scan_module.py
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, BooleanVar
import time
import os # Thêm import os
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk
# Import constants - Giả sử các hằng số này được định nghĩa đúng trong utils.py
from utils import FONT_NORMAL, FONT_MEDIUM, FONT_BOLD, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_TEXT_NORMAL, COLOR_BG_FRAME

class QRCodeScannerWindow:
    def __init__(self, parent_window, df_students, on_scan_success_callback, photo_folder_path, default_avatar_filename="default_avatar.png"): # Thêm tham số
        self.parent = parent_window
        self.df_students = df_students
        self.on_scan_success = on_scan_success_callback
        self.photo_folder = photo_folder_path
        self.default_avatar_path = os.path.join(self.photo_folder, default_avatar_filename)
        self.displayed_photo_image = None # Giữ tham chiếu TkImage cho ảnh học sinh

        self.window = Toplevel(parent_window)
        self.window.title("Quét Mã QR Điểm Danh")
        # Tăng chiều rộng cửa sổ để chứa thêm vùng thông tin
        self.window.geometry("950x680") # Ví dụ: 640 (video) + 10 (padding) + 250 (info) + 20 (padding) ~ 920
        self.window.transient(parent_window); self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.window.configure(bg=COLOR_BG_FRAME)

        # --- Main Frame ---
        main_container_frame = ttk.Frame(self.window, padding="10")
        main_container_frame.pack(fill=tk.BOTH, expand=True)

        # --- Frame cho Camera (bên trái) ---
        camera_area_frame = ttk.Frame(main_container_frame)
        camera_area_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.video_label = ttk.Label(camera_area_frame, background="black")
        self.video_label.pack(pady=(0,10), fill=tk.BOTH, expand=True) # Video chiếm phần lớn

        self.status_label = ttk.Label(camera_area_frame, text="Trạng thái: Sẵn sàng", font=FONT_MEDIUM)
        self.status_label.pack(pady=5)

        self.info_label = ttk.Label(camera_area_frame, text="", font=FONT_NORMAL, wraplength=630, justify=tk.CENTER) # wraplength cho camera area
        self.info_label.pack(pady=5, fill=tk.X)

        # --- Frame cho Thông tin Học sinh (bên phải) ---
        self.student_info_display_frame = ttk.Frame(main_container_frame, width=260, padding="10")
        self.student_info_display_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.student_info_display_frame.pack_propagate(False) # Ngăn frame co lại

        ttk.Label(self.student_info_display_frame, text="Thông tin Học sinh:", font=FONT_BOLD).pack(pady=(0,10), anchor='w')

        # Frame con cho ảnh để kiểm soát kích thước
        self.actual_photo_frame = ttk.Frame(self.student_info_display_frame, width=200, height=250, relief=tk.GROOVE, borderwidth=1) # Kích thước mong muốn cho ảnh
        self.actual_photo_frame.pack(pady=5, anchor='center')
        self.actual_photo_frame.pack_propagate(False)
        self.current_photo_widget = ttk.Label(self.actual_photo_frame, text="(Ảnh HS)", anchor=tk.CENTER)
        self.current_photo_widget.pack(expand=True, fill=tk.BOTH)

        self.name_label_display = ttk.Label(self.student_info_display_frame, text="Họ tên: N/A", font=FONT_MEDIUM, wraplength=240)
        self.name_label_display.pack(pady=5, anchor='w')

        self.sbd_label_display = ttk.Label(self.student_info_display_frame, text="SBD: N/A", font=FONT_NORMAL)
        self.sbd_label_display.pack(pady=3, anchor='w')

        self.class_label_display = ttk.Label(self.student_info_display_frame, text="Lớp: N/A", font=FONT_NORMAL)
        self.class_label_display.pack(pady=3, anchor='w')
        
        # Thông báo trạng thái chi tiết cho học sinh cụ thể (nếu cần)
        self.student_specific_status_label = ttk.Label(self.student_info_display_frame, text="", font=FONT_NORMAL, wraplength=240, foreground=COLOR_TEXT_NORMAL)
        self.student_specific_status_label.pack(pady=(10,0), anchor='w', fill=tk.X)


        # --- Controls Frame (ở dưới Camera Area) ---
        controls_frame = ttk.Frame(camera_area_frame) # Đặt controls_frame dưới camera_area_frame
        controls_frame.pack(pady=10, fill=tk.X, anchor='s') # anchor='s' để nó ở cuối

        self.start_button = ttk.Button(controls_frame, text="Bắt đầu quét", command=self.start_scan, width=15)
        self.start_button.pack(side=tk.LEFT, padx=10, ipady=3, expand=True)
        self.stop_button = ttk.Button(controls_frame, text="Dừng quét", command=self.stop_scan, width=15, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10, ipady=3, expand=True)
        self.close_button = ttk.Button(controls_frame, text="Đóng", command=self.close_window, width=15, style="Accent.TButton") # Bỏ "Cửa sổ"
        self.close_button.pack(side=tk.LEFT, padx=10, ipady=3, expand=True)

        self.auto_stop_var = BooleanVar(value=False)
        self.auto_stop_check = ttk.Checkbutton(camera_area_frame, text="Tự động dừng sau khi quét thành công", variable=self.auto_stop_var)
        self.auto_stop_check.pack(pady=(5,10), anchor='s')

        self.cap = None; self.running = False
        self.last_qr_data = None; self.last_scan_time = 0
        self._after_id = None
        self.update_info(message="", status="info", student_name=None, student_sbd=None, student_class=None, photo_path=None) # Khởi tạo vùng thông tin


    def start_scan(self):
        if self.running: return
        try:
            indices_to_try = [0, 1, -1, 2] # Thử các camera index phổ biến
            for index in indices_to_try:
                self.cap = cv2.VideoCapture(index)
                if self.cap and self.cap.isOpened(): break
                if self.cap: self.cap.release(); self.cap = None # Giải phóng nếu không mở được
            if not self.cap or not self.cap.isOpened():
                raise ValueError("Không thể mở camera nào. Hãy kiểm tra kết nối camera.")

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.status_label.config(text="Trạng thái: Đang chạy...", foreground=COLOR_SUCCESS)
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.info_label.config(text="Đưa mã QR vào vùng camera...") # Hướng dẫn chung
            self._update_frame()
        except Exception as e:
            messagebox.showerror("Lỗi Camera", f"Không thể khởi động camera:\n{e}", parent=self.window)
            if self.cap: self.cap.release(); self.cap = None
            self.status_label.config(text="Lỗi: Không mở được camera", foreground=COLOR_ERROR)
            self.start_button.config(state=tk.NORMAL); self.stop_button.config(state=tk.DISABLED)

    def stop_scan(self):
        if not self.running: return
        self.running = False
        if self._after_id:
            try: self.window.after_cancel(self._after_id)
            except tk.TclError: pass # Bỏ qua lỗi nếu window đã bị destroy
            self._after_id = None
        if self.cap and self.cap.isOpened(): self.cap.release(); self.cap = None
        
        # Chỉ cập nhật UI nếu window còn tồn tại
        if hasattr(self, 'window') and self.window.winfo_exists():
            self.video_label.config(image=''); self.video_label.imgtk = None # Xóa ảnh khỏi label
            self.status_label.config(text="Trạng thái: Đã dừng", foreground=COLOR_TEXT_NORMAL)
            # self.info_label.config(text="") # Có thể giữ lại thông tin HS cuối cùng hoặc xóa
            self.start_button.config(state=tk.NORMAL); self.stop_button.config(state=tk.DISABLED)

# Trong scan_module.py, lớp QRCodeScannerWindow, phương thức _update_frame

    def _update_frame(self):
        if not self.running or not self.cap or not self.cap.isOpened():
            if self.running and hasattr(self, 'window') and self.window.winfo_exists(): self.stop_scan()
            return
        try:
            success, frame = self.cap.read() # frame này là BGR
            if not success:
                if self.running and hasattr(self, 'window') and self.window.winfo_exists():
                    self._after_id = self.window.after(50, self._update_frame)
                return

            # Tạo một bản sao của frame gốc để vẽ lên, không ảnh hưởng đến frame dùng để giải mã QR
            frame_to_display_final = frame.copy() # Làm việc trên bản sao này để hiển thị

            frame_rgb_for_decode = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Chuyển sang RGB để pyzbar giải mã
            decoded_objects = decode(frame_rgb_for_decode)
            current_time = time.time()
            qr_processed_this_frame = False

            for obj in decoded_objects:
                # Vẽ hình chữ nhật/đa giác lên frame_to_display_final
                try:
                    points = obj.polygon
                    if points is not None and len(points) > 0:
                        # Chuyển đổi points sang numpy array đúng kiểu
                        pts_np = np.array([(p.x, p.y) for p in points], dtype=np.int32)
                        pts_np = pts_np.reshape((-1, 1, 2))
                        cv2.polylines(frame_to_display_final, [pts_np], isClosed=True, color=(0, 255, 0), thickness=2) # Màu xanh lá
                    else: # Nếu không có polygon, thử dùng rect
                        (x, y, w, h) = obj.rect
                        cv2.rectangle(frame_to_display_final, (x, y), (x + w, y + h), (0, 255, 0), 2)

                except Exception as e_draw:
                    print(f"Lỗi khi vẽ bounding box cho QR: {e_draw}")


                if qr_processed_this_frame: continue # Chỉ xử lý 1 QR mỗi frame

                try:
                    qr_data = obj.data.decode('utf-8', errors='ignore').strip()
                    if qr_data and (qr_data != self.last_qr_data or (current_time - self.last_scan_time > 2)):
                        self.last_qr_data = qr_data; self.last_scan_time = current_time
                        qr_processed_this_frame = True
                        
                        sbd_str = str(qr_data)
                        if self.on_scan_success:
                            self.on_scan_success(sbd_str)

                        if self.auto_stop_var.get() and (self.df_students is None or sbd_str in self.df_students.index):
                            # Dừng nếu SBD hợp lệ hoặc nếu không có df_students để kiểm tra (trường hợp test đơn giản)
                            self.stop_scan()
                            return
                except Exception as decode_err:
                    print(f"Lỗi xử lý dữ liệu QR: {decode_err}")
            
            # Chuyển frame đã vẽ (BGR) sang RGB để hiển thị trên Tkinter
            frame_pil_to_show = cv2.cvtColor(frame_to_display_final, cv2.COLOR_BGR2RGB)
            
            # --- Phần resize và hiển thị frame_pil_to_show lên video_label giữ nguyên như cũ ---
            label_w = self.video_label.winfo_width()
            label_h = self.video_label.winfo_height()
            if label_w > 1 and label_h > 1:
                img_h_orig, img_w_orig, _ = frame_pil_to_show.shape
                aspect_ratio_img = img_w_orig / img_h_orig
                aspect_ratio_label = label_w / label_h
                if aspect_ratio_label > aspect_ratio_img:
                    new_h = label_h
                    new_w = int(aspect_ratio_img * new_h)
                else:
                    new_w = label_w
                    new_h = int(new_w / aspect_ratio_img)
                if (new_w < img_w_orig or new_h < img_h_orig) and new_w > 0 and new_h > 0:
                    frame_display_resized_cv = cv2.resize(frame_pil_to_show, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    img_pil_resized = Image.fromarray(frame_display_resized_cv)
                else:
                    img_pil_resized = Image.fromarray(frame_pil_to_show)
            else:
                img_pil_resized = Image.fromarray(frame_pil_to_show)

            imgtk = ImageTk.PhotoImage(image=img_pil_resized)

            if hasattr(self, 'window') and self.window.winfo_exists():
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
                self._after_id = self.window.after(25, self._update_frame)
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong _update_frame: {e}")
            # ... (phần xử lý lỗi giữ nguyên) ...


    def play_sound(self, sound_type="success"):
        """Phát âm thanh dựa trên loại."""
        # Sử dụng winsound nếu có, nếu không thì dùng tiếng beep mặc định
        frequency, duration = 500, 100 # default
        if sound_type == "success": frequency, duration = 1300, 150
        elif sound_type == "error": frequency, duration = 400, 300
        elif sound_type == "warning": frequency, duration = 700, 200 # Duplicate/Warning
        try:
            import winsound
            winsound.Beep(frequency, duration)
        except ImportError: # Cho Linux/MacOS (có thể cần cài 'beep' hoặc tương tự)
            if os.name != 'nt': # Không phải Windows
                # Cố gắng dùng lệnh 'beep' nếu có
                # os.system(f'beep -f {frequency} -l {duration}') # Cần cài đặt tiện ích 'beep'
                print("\a", end="", flush=True) # Tiếng beep cơ bản
            else: # Windows nhưng winsound import lỗi (ít khi xảy ra)
                print("\a", end="", flush=True)
        except Exception as e_sound:
            print(f"Lỗi phát âm thanh: {e_sound}")
            print("\a", end="", flush=True) # Fallback

    def play_success_sound(self): self.play_sound("success")
    def play_error_sound(self): self.play_sound("error")
    def play_duplicate_sound(self): self.play_sound("warning")

    # Sửa đổi update_info để nhận nhiều tham số hơn
    def update_info(self, message, status="info", student_name=None, student_sbd=None, student_class=None, photo_path=None):
        """
        Cập nhật vùng thông tin học sinh và ảnh.
        status: "info", "success", "warning", "error"
        """
        # Cập nhật thông báo trạng thái chung (info_label dưới camera)
        # self.info_label.config(text=message) # Thông báo này có thể bị trùng với student_specific_status_label
        # Có thể dùng info_label cho trạng thái quét chung, và student_specific_status_label cho HS
        
        # Cập nhật các label thông tin học sinh
        self.name_label_display.config(text=f"Họ tên: {student_name if student_name else 'N/A'}")
        self.sbd_label_display.config(text=f"SBD: {student_sbd if student_sbd else 'N/A'}")
        self.class_label_display.config(text=f"Lớp: {student_class if student_class else 'N/A'}")

        # Cập nhật thông báo trạng thái cụ thể cho học sinh
        student_status_color = COLOR_TEXT_NORMAL
        if status == "success": student_status_color = COLOR_SUCCESS
        elif status == "warning": student_status_color = COLOR_WARNING
        elif status == "error": student_status_color = COLOR_ERROR
        self.student_specific_status_label.config(text=message, foreground=student_status_color)


        # Cập nhật ảnh học sinh
        path_to_load_img = photo_path
        # Nếu không có photo_path hoặc file không tồn tại, thử dùng ảnh placeholder
        if not path_to_load_img or not os.path.exists(path_to_load_img):
            if os.path.exists(self.default_avatar_path):
                path_to_load_img = self.default_avatar_path
            else: # Nếu cả ảnh HS và placeholder đều không có
                self.current_photo_widget.config(image='', text="(Không có ảnh)")
                self.displayed_photo_image = None
                # print(f"DEBUG scan_module: Không tìm thấy ảnh '{photo_path}' và placeholder.")
                return # Không làm gì thêm với ảnh

        if path_to_load_img:
            try:
                pil_img_hs = Image.open(path_to_load_img)
                # Kích thước của frame chứa ảnh là width=200, height=250
                target_w_photo, target_h_photo = 198, 248 # Trừ đi border/padding
                pil_img_hs.thumbnail((target_w_photo, target_h_photo), Image.Resampling.LANCZOS)
                
                tk_img_hs = ImageTk.PhotoImage(pil_img_hs)
                self.current_photo_widget.config(image=tk_img_hs, text="")
                self.displayed_photo_image = tk_img_hs # Quan trọng: Giữ tham chiếu
            except Exception as e:
                print(f"Lỗi load ảnh HS trong scan_module '{path_to_load_img}': {e}")
                self.current_photo_widget.config(image='', text="(Lỗi ảnh)")
                self.displayed_photo_image = None
        else: # Trường hợp cuối, path_to_load_img vẫn là None (ít khi xảy ra nếu placeholder được xử lý đúng)
            self.current_photo_widget.config(image='', text="(Chưa có ảnh)")
            self.displayed_photo_image = None


    def close_window(self):
        self.stop_scan() # Đảm bảo dừng camera và after_jobs
        if hasattr(self, 'window') and self.window.winfo_exists():
            # Không cần cancel _after_id ở đây nữa vì stop_scan đã làm
            self.window.destroy()
        # print("Cửa sổ quét đã đóng.")

# --- Phần Test (nếu chạy file này trực tiếp) ---
if __name__ == '__main__':
    # Tạo một root window giả để test
    root = tk.Tk()
    root.title("Test Root Window")
    root.geometry("300x200")

    # Tạo dữ liệu học sinh giả (DataFrame)
    data = {
        'SBD': ['HS001', 'HS002', 'HS003'],
        'Họ và tên': ['Nguyễn Văn A', 'Trần Thị B', 'Lê Văn C'],
        'Lớp': ['10A1', '11B2', '12C3'],
        'Ngày sinh': ['01/01/2005', '02/02/2004', '03/03/2003']
        # Thêm cột ImagePath nếu bạn có sẵn ảnh mẫu
        # 'ImagePath': ['student_photos/HS001.png', 'student_photos/HS002.png', 'student_photos/HS003.png']
    }
    import pandas as pd
    df_students_test = pd.DataFrame(data).set_index('SBD')

    # Tạo thư mục Student_Photos và ảnh placeholder giả để test
    PHOTO_FOLDER_TEST = "Student_Photos_Test"
    DEFAULT_AVATAR_TEST = "default_avatar.png"
    os.makedirs(PHOTO_FOLDER_TEST, exist_ok=True)
    try:
        # Tạo một ảnh placeholder giả (ảnh đen 100x100)
        img_placeholder = Image.new('RGB', (100, 100), color = 'black')
        img_placeholder.save(os.path.join(PHOTO_FOLDER_TEST, DEFAULT_AVATAR_TEST))
        print(f"Đã tạo placeholder: {os.path.join(PHOTO_FOLDER_TEST, DEFAULT_AVATAR_TEST)}")

        # Tạo ảnh mẫu cho HS001
        img_hs001 = Image.new('RGB', (100, 150), color = 'blue')
        img_hs001.save(os.path.join(PHOTO_FOLDER_TEST, "HS001.png"))
        print(f"Đã tạo ảnh mẫu: {os.path.join(PHOTO_FOLDER_TEST, 'HS001.png')}")

    except Exception as e:
        print(f"Không thể tạo ảnh mẫu/placeholder cho test: {e}")


    # Hàm callback giả
    def mock_on_scan_success(sbd):
        print(f"MAIN_APP_CALLBACK: SBD '{sbd}' đã được quét.")
        # Giả lập MainApp gọi lại update_info của scanner
        if hasattr(app_scanner, 'window') and app_scanner.window.winfo_exists():
            if sbd in df_students_test.index:
                student_info_test = df_students_test.loc[sbd]
                student_name_test = student_info_test.get('Họ và tên', 'N/A')
                student_class_test = student_info_test.get('Lớp', 'N/A')
                
                # Giả lập đường dẫn ảnh
                photo_file_test = os.path.join(PHOTO_FOLDER_TEST, f"{sbd}.png")
                if not os.path.exists(photo_file_test):
                    photo_file_test = None # Sẽ dùng placeholder

                app_scanner.update_info(
                    message=f"Điểm danh thành công: {sbd}",
                    status="success",
                    student_name=student_name_test,
                    student_sbd=sbd,
                    student_class=student_class_test,
                    photo_path=photo_file_test
                )
                app_scanner.play_success_sound()
            else:
                app_scanner.update_info(
                    message=f"SBD '{sbd}' không hợp lệ!",
                    status="error",
                    student_sbd=sbd, # Vẫn hiển thị SBD đã quét
                    photo_path=None # Không có ảnh cho SBD không hợp lệ
                )
                app_scanner.play_error_sound()

    # Hàm để mở cửa sổ scan từ root window
    def open_scanner_test():
        global app_scanner
        app_scanner = QRCodeScannerWindow(
            parent_window=root,
            df_students=df_students_test,
            on_scan_success_callback=mock_on_scan_success,
            photo_folder_path=PHOTO_FOLDER_TEST, # Đường dẫn thư mục ảnh test
            default_avatar_filename=DEFAULT_AVATAR_TEST
        )

    ttk.Button(root, text="Mở Cửa Sổ Quét (Test)", command=open_scanner_test).pack(pady=20, padx=20, ipady=10)
    
    # Biến toàn cục để giữ instance của scanner cho callback
    app_scanner = None

    root.mainloop()

    # Dọn dẹp thư mục test (tùy chọn)
    # import shutil
    # if os.path.exists(PHOTO_FOLDER_TEST):
    #     shutil.rmtree(PHOTO_FOLDER_TEST)
    #     print(f"Đã xóa thư mục test: {PHOTO_FOLDER_TEST}")