import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Listbox, Scrollbar, Toplevel, Entry, StringVar, Radiobutton, simpledialog
import os
import sys # Thêm import sys để kiểm tra platform khi mở file PDF
from datetime import datetime
import pandas as pd
try:
    import xlsxwriter # Thêm để hỗ trợ định dạng Excel tốt hơn
except ImportError:
    xlsxwriter = None # Đặt là None nếu chưa cài
from tkcalendar import DateEntry, Calendar
TKCALENDAR_AVAILABLE = True

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Thiếu thư viện", "Vui lòng cài đặt thư viện Pillow để xử lý ảnh:\n pip install Pillow")
    Image = None
    ImageTk = None

# Import các module chức năng và utils đã cập nhật
import utils
import login_module
import qr_module
import scan_module
import seating_module
import ticket_module
import attendance_report_module
import student_card_module
import schedule_module
import student_schedule_display

class MainApplication:

    def _load_icon(self, icon_filename, size=(16, 16)):
        if not Image or not ImageTk: # Pillow not available
            return None
        # Cache icons to prevent them from being garbage collected and to avoid reloading
        if icon_filename in self.icons and self.icons[icon_filename].get(size):
            return self.icons[icon_filename][size]
        
        try:
            # Determine base path for icons (works for script and PyInstaller bundle)
            if hasattr(sys, '_MEIPASS'):
                # Running in a PyInstaller bundle
                base_path = sys._MEIPASS
            else:
                # Running as a normal script
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "icons", icon_filename)
            
            if not os.path.exists(icon_path):
                print(f"Icon not found: {icon_path}")
                # Try adding .png if not present
                if not icon_filename.lower().endswith('.png'):
                    icon_path_png = icon_path + ".png"
                    if os.path.exists(icon_path_png):
                        icon_path = icon_path_png
                        print(f"Found icon as: {icon_path}")
                    else:
                        return None # Still not found
                else:
                     return None # Not found even with .png

            pil_image = Image.open(icon_path)
            pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
            tk_image = ImageTk.PhotoImage(pil_image)
            
            # Store in cache
            if icon_filename not in self.icons:
                self.icons[icon_filename] = {}
            self.icons[icon_filename][size] = tk_image
            return tk_image
        except Exception as e:
            print(f"Error loading icon {icon_filename}: {e}")
            return None

    # Đặt on_closing lên đầu để đảm bảo nó được định nghĩa trước __init__
    def on_closing(self):
        """Xử lý sự kiện khi người dùng đóng cửa sổ chính."""
        print("DEBUG: Hàm on_closing được gọi.")
        if hasattr(self, 'scanner_window_instance') and self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
            print("DEBUG: Đang đóng cửa sổ quét...")
            try:
                self.scanner_window_instance.close_window()
            except Exception as e_close_scan:
                print(f"Lỗi khi đóng cửa sổ quét: {e_close_scan}")
            self.scanner_window_instance = None
        else:
            print("DEBUG: Không có cửa sổ quét nào đang mở để đóng.")

        if messagebox.askyesno("Xác nhận Thoát",
                               "Bạn có chắc chắn muốn thoát ứng dụng không?",
                               icon='question', parent=self.root):
            print("DEBUG: Người dùng xác nhận thoát. Đang đóng ứng dụng...")
            self.root.destroy()
        else:
            print("DEBUG: Người dùng hủy thoát.")

    # Các phương thức khác của lớp phải thụt vào cùng cấp với on_closing
    def __init__(self, root):
        self.root = root
        self.root.configure(bg=utils.COLOR_BG_MAIN)
        self.icons = {} # To store PhotoImage objects, {filename: {size_tuple: PhotoImage}}

        # --- Setup ttk Style ---
        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if 'clam' in available_themes: self.style.theme_use('clam')
        elif 'vista' in available_themes: self.style.theme_use('vista')
        elif 'xpnative' in available_themes: self.style.theme_use('xpnative')

        self.style.configure("Login.TFrame", background="#EAEAEA") # Màu xám rất nhạt
        self.style.configure('DateEntryStyle.TEntry', font=utils.FONT_NORMAL, padding=3)
        self.style.configure("TFrame", background=utils.COLOR_BG_FRAME)
        self.style.configure("TLabel", font=utils.FONT_NORMAL, background=utils.COLOR_BG_FRAME)
        self.style.configure("Header.TLabel", font=utils.FONT_HEADER, foreground=utils.COLOR_PRIMARY, background=utils.COLOR_BG_FRAME)
        self.style.configure("AppTitle.TLabel", font=utils.FONT_APP_TITLE, foreground=utils.COLOR_PRIMARY, background=utils.COLOR_BG_FRAME, padding=(0, 10, 0, 10))
        self.style.configure("TButton", font=utils.FONT_NORMAL, padding=6)
        self.style.configure("Accent.TButton", font=utils.FONT_BOLD, foreground="white", background=utils.COLOR_PRIMARY)
        self.style.map("Accent.TButton", background=[('active', utils.COLOR_PRIMARY)], relief=[('pressed', 'sunken')])
        self.style.configure("Red.TButton", font=utils.FONT_BOLD, foreground=utils.COLOR_ERROR)
        self.style.configure("TRadiobutton", font=utils.FONT_NORMAL, background=utils.COLOR_BG_FRAME)
        self.style.configure("TCombobox", font=utils.FONT_NORMAL, padding=3)
        self.style.configure("TEntry", font=utils.FONT_NORMAL, padding=3)
        self.style.configure("Treeview.Heading", font=utils.FONT_BOLD)
        self.style.configure("Treeview", font=utils.FONT_NORMAL, rowheight=25)
        self.style.map("Treeview", background=[('selected', utils.COLOR_PRIMARY)], foreground=[('selected', 'white')])
        self.style.configure("TLabelframe", font=utils.FONT_MEDIUM_BOLD, background=utils.COLOR_BG_FRAME, padding=10)
        self.style.configure("TLabelframe.Label", font=utils.FONT_MEDIUM_BOLD, background=utils.COLOR_BG_FRAME, foreground=utils.COLOR_PRIMARY)
        self.style.configure("Italic.TLabel", font=(utils.FONT_FAMILY, utils.FONT_SIZE_NORMAL, "italic"), background=utils.COLOR_BG_FRAME)
        self.style.configure("Link.TButton", foreground="blue", font=(utils.FONT_FAMILY, utils.FONT_SIZE_NORMAL, "underline"), padding=0, borderwidth=0, focuscolor=self.style.lookup("TButton", "background"), anchor="center")
        self.style.map("Link.TButton", foreground=[('active', utils.COLOR_PRIMARY), ('pressed', utils.COLOR_PRIMARY)], relief=[('pressed', 'flat'), ('active', 'flat')], underline=[('active', 1), ('!active', 0)], background=[('active', utils.COLOR_BG_FRAME), ('pressed', utils.COLOR_BG_FRAME)])
        
        try:
            self.style.layout("Link.TButton", [('Button.padding', {'sticky': 'nswe', 'children': [('Button.label', {'sticky': 'nswe'})]})])
        except tk.TclError:
            print("Warning: Không thể tùy chỉnh layout cho Link.TButton.")
            self.style.configure("Link.TButton", padding=(2,0))
        # --- End ttk Style ---

        self.root.title("Ứng dụng Quản lý Học sinh v4.0") # Đổi title ví dụ
        win_width = 900
        win_height = 750
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_center = int((screen_width / 2) - (win_width / 2))
        y_center = int((screen_height / 2) - (win_height / 2))
        self.root.geometry(f'{win_width}x{win_height}+{x_center}+{y_center}')

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) 

        self.current_user_role = None; self.current_user_id = None
        self.student_data = None; self.class_list = []
        self.attendance_data = []; self.scanner_window_instance = None
        self.last_added_record = None
        self.selected_class = StringVar(); self.selected_context = StringVar(value="regular")
        self.selected_date_str = datetime.now().strftime('%Y-%m-%d')

        self.main_content_wrapper = ttk.Frame(root, style="TFrame", padding="10 10 10 10")
        self.main_content_wrapper.pack(fill=tk.BOTH, expand=True)

        self.student_data = utils.load_student_data()
        if self.student_data is None:
             messagebox.showerror("Lỗi", f"Không tải được {utils.STUDENT_DATA_FILE}. Ứng dụng sẽ đóng."); self.root.destroy(); return
        if 'Lớp' in self.student_data.columns:
            self.class_list = utils.get_classes(self.student_data)
            if self.class_list: self.selected_class.set(self.class_list[0])
        else:
            print("Warning: Cột 'Lớp' không tồn tại.")
            self.class_list = []

        self.attendance_data = utils.load_attendance_data()
        print(f"Tải {len(self.attendance_data)} bản ghi điểm danh.")

        self.login_frame = ttk.Frame(self.main_content_wrapper, style="TFrame", padding="20")
        self.student_frame = ttk.Frame(self.main_content_wrapper, style="TFrame", padding="20")
        self.teacher_frame = ttk.Frame(self.main_content_wrapper, style="TFrame", padding="10")

        self.show_login()

    def show_announcement_management_ui(self):
        if self.current_user_role != "teacher":
            messagebox.showwarning("Truy cập bị hạn chế", "Chức năng này chỉ dành cho giáo viên.", parent=self.root)
            return

        announce_win = Toplevel(self.root)
        announce_win.title("Quản lý Thông báo Lớp học")
        announce_win.geometry("800x750")
        announce_win.transient(self.root); announce_win.grab_set()
        announce_win.configure(bg=utils.COLOR_BG_FRAME)

        selected_class_var = tk.StringVar()
        target_type_var = tk.StringVar(value="single_class")
        selected_announcement_id_var = tk.StringVar()

        content_text_widget_ref = {"widget": None}
        announcements_tree_widget_ref = {"widget": None}
        single_class_combobox_ref = {"widget": None}
        multi_class_listbox_ref = {"widget": None}
        student_sbd_entry_ref = {"widget": None}
        delete_ann_button_ref = {"button": None}

        def update_target_input_widget(event=None):
            sc_widget = single_class_combobox_ref.get("widget")
            mc_listbox_widget = multi_class_listbox_ref.get("widget")
            mc_listbox_frame = mc_listbox_widget.master if mc_listbox_widget else None
            ss_widget = student_sbd_entry_ref.get("widget")

            if sc_widget and sc_widget.winfo_exists(): sc_widget.grid_remove()
            if mc_listbox_frame and mc_listbox_frame.winfo_exists(): mc_listbox_frame.grid_remove()
            if ss_widget and ss_widget.winfo_exists(): ss_widget.grid_remove()

            target_type = target_type_var.get()
            widget_to_focus = None
            if target_type == "single_class":
                if sc_widget: sc_widget.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=2); widget_to_focus = sc_widget
            elif target_type == "multi_class":
                if mc_listbox_frame: mc_listbox_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=2); widget_to_focus = mc_listbox_widget
            elif target_type == "specific_student":
                if ss_widget: ss_widget.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=2); widget_to_focus = ss_widget

            content_widget = content_text_widget_ref.get("widget")
            if widget_to_focus and widget_to_focus.winfo_exists() and widget_to_focus.winfo_ismapped():
                 announce_win.after(50, lambda w=widget_to_focus: w.focus_set())
            elif content_widget and content_widget.winfo_exists():
                 announce_win.after(50, lambda w=content_widget: w.focus_set())

        def load_and_display_announcements():
            current_tree = announcements_tree_widget_ref.get("widget")
            if not current_tree or not current_tree.winfo_exists(): return
            current_tree.delete(*current_tree.get_children())
            all_announcements = utils.load_announcements()
            all_announcements.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            for i, ann in enumerate(all_announcements):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                content_preview = ann.get("content", "")[:100] + ("..." if len(ann.get("content", "")) > 100 else "")
                display_target = "Chung"; target_sbd = ann.get("target_sbd"); class_name_field = ann.get("class_name")
                if target_sbd: display_target = f"HS: {target_sbd}"
                elif isinstance(class_name_field, list): display_target = (", ".join(class_name_field[:2]) + ("..." if len(class_name_field)>2 else "")) if class_name_field else "(Nhiều lớp)"
                elif isinstance(class_name_field, str) and class_name_field.strip(): display_target = class_name_field.strip()
                try:
                    current_tree.insert("", tk.END, iid=ann.get("id"), values=(ann.get("id", ""), ann.get("timestamp", ""), display_target, content_preview, ann.get("author", "")), tags=(tag,))
                except Exception as e_insert: print(f"Lỗi insert Treeview: {e_insert}")
            try:
                current_tree.tag_configure('evenrow', background=utils.COLOR_LISTBOX_EVEN_ROW); current_tree.tag_configure('oddrow', background=utils.COLOR_LISTBOX_ODD_ROW)
            except: pass
            selected_announcement_id_var.set("")
            delete_button = delete_ann_button_ref.get("button");
            if delete_button and delete_button.winfo_exists(): delete_button.config(state=tk.DISABLED)
            current_tree.selection_set([])

        def post_new_announcement():
            content_widget = content_text_widget_ref.get("widget")
            if not content_widget: messagebox.showerror("Lỗi chương trình", "Không tìm thấy ô nhập nội dung.", parent=announce_win); return
            content = content_widget.get("1.0", tk.END).strip()
            if not content: messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập nội dung thông báo.", parent=announce_win); content_widget.focus_set(); return

            target_type = target_type_var.get(); class_name_data = None; target_sbd_data = None
            if target_type == "single_class":
                sc_widget = single_class_combobox_ref.get("widget")
                if sc_widget:
                    selected_single_class = selected_class_var.get()
                    if not selected_single_class or selected_single_class == "(Chưa có lớp)": messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn lớp.", parent=announce_win); sc_widget.focus_set(); return
                    class_name_data = selected_single_class
                else: messagebox.showerror("Lỗi UI", "Lỗi Combobox chọn lớp.", parent=announce_win); return
            elif target_type == "multi_class":
                mc_widget = multi_class_listbox_ref.get("widget")
                if mc_widget:
                    selected_indices = mc_widget.curselection()
                    if not selected_indices: messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn ít nhất một lớp.", parent=announce_win); mc_widget.focus_set(); return
                    class_name_data = [mc_widget.get(i) for i in selected_indices]
                else: messagebox.showerror("Lỗi UI", "Lỗi Listbox chọn lớp.", parent=announce_win); return
            elif target_type == "specific_student":
                ss_widget = student_sbd_entry_ref.get("widget")
                if ss_widget:
                    sbd_val = ss_widget.get().strip()
                    if not sbd_val: messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập SBD.", parent=announce_win); ss_widget.focus_set(); return
                    hs_name, _ = utils.get_student_info(sbd_val, self.student_data)
                    if hs_name is None: messagebox.showwarning("SBD không hợp lệ", f"Không tìm thấy SBD: {sbd_val}", parent=announce_win); ss_widget.focus_set(); return
                    target_sbd_data = sbd_val; class_name_data = None
                else: messagebox.showerror("Lỗi UI", "Lỗi ô nhập SBD.", parent=announce_win); return
            else: messagebox.showerror("Lỗi Logic", "Loại mục tiêu không xác định.", parent=announce_win); return

            new_ann_id = utils.generate_announcement_id(self.current_user_id)
            new_ann = {"id": new_ann_id, "class_name": class_name_data, "target_sbd": target_sbd_data, "content": content, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "author": self.current_user_id}
            print(f"DEBUG: Chuẩn bị lưu thông báo: {new_ann}")
            current_announcements = utils.load_announcements()
            current_announcements.append(new_ann)
            if utils.save_announcements(current_announcements):
                messagebox.showinfo("Thành công", "Đã đăng thông báo!", parent=announce_win); content_widget.delete("1.0", tk.END)
                target_type_var.set("single_class"); update_target_input_widget()
                if student_sbd_entry_ref.get("widget"): student_sbd_entry_ref["widget"].delete(0, tk.END)
                if multi_class_listbox_ref.get("widget"): multi_class_listbox_ref["widget"].selection_clear(0, tk.END)
                load_and_display_announcements()
            else: messagebox.showerror("Lỗi Lưu", "Không thể lưu thông báo.", parent=announce_win)

        def delete_selected_announcement():
            ann_id_to_delete = selected_announcement_id_var.get()
            if not ann_id_to_delete: messagebox.showwarning("Chưa chọn", "Vui lòng chọn thông báo để xóa.", parent=announce_win); return
            current_tree = announcements_tree_widget_ref.get("widget")
            if not current_tree or not current_tree.exists(ann_id_to_delete): messagebox.showerror("Lỗi", "Thông báo đã chọn không còn tồn tại.", parent=announce_win); load_and_display_announcements(); return

            try:
                item_values = current_tree.item(ann_id_to_delete, "values")
                content_to_confirm = str(item_values[3])[:50] + "..." if len(str(item_values[3])) > 50 else str(item_values[3])
                confirm_msg = f"Bạn có chắc muốn xóa thông báo này không?\n\nNội dung: \"{content_to_confirm}\""
            except Exception: confirm_msg = "Bạn có chắc chắn muốn xóa thông báo đã chọn không?"

            if messagebox.askyesno("Xác nhận Xóa", confirm_msg, icon='warning', parent=announce_win):
                current_announcements = utils.load_announcements()
                initial_len = len(current_announcements)
                updated_announcements = [ann for ann in current_announcements if ann.get("id") != ann_id_to_delete]
                if len(updated_announcements) < initial_len:
                    if utils.save_announcements(updated_announcements): messagebox.showinfo("Thành công", "Đã xóa thông báo.", parent=announce_win); load_and_display_announcements()
                    else: messagebox.showerror("Lỗi", "Không thể lưu sau khi xóa.", parent=announce_win)
                else: messagebox.showerror("Lỗi", f"Không tìm thấy ID '{ann_id_to_delete}' để xóa.", parent=announce_win); load_and_display_announcements()

        def on_tree_select(event=None):
             current_tree = announcements_tree_widget_ref.get("widget")
             if not current_tree: return
             selected_items = current_tree.selection()
             delete_button = delete_ann_button_ref.get("button")
             if selected_items:
                 item_iid = selected_items[0]; selected_announcement_id_var.set(item_iid)
                 if delete_button and delete_button.winfo_exists(): delete_button.config(state=tk.NORMAL)
             else:
                 selected_announcement_id_var.set("")
                 if delete_button and delete_button.winfo_exists(): delete_button.config(state=tk.DISABLED)

        post_frame = ttk.LabelFrame(announce_win, text="Đăng thông báo mới", padding="10"); post_frame.pack(pady=10, padx=10, fill=tk.X)
        target_type_frame = ttk.Frame(post_frame); target_type_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=(5,10), sticky=tk.W)
        ttk.Label(target_type_frame, text="Gửi tới:", font=utils.FONT_NORMAL).pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(target_type_frame, text="Một Lớp", variable=target_type_var, value="single_class", command=update_target_input_widget).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(target_type_frame, text="Nhiều Lớp", variable=target_type_var, value="multi_class", command=update_target_input_widget).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(target_type_frame, text="HS Cụ thể (SBD)", variable=target_type_var, value="specific_student", command=update_target_input_widget).pack(side=tk.LEFT, padx=5)

        target_input_container = ttk.Frame(post_frame); target_input_container.grid(row=1, column=0, columnspan=3, padx=0, pady=5, sticky=tk.NSEW); target_input_container.columnconfigure(0, weight=1)
        class_options = self.class_list if self.class_list else ["(Chưa có lớp)"]
        if self.class_list and not selected_class_var.get(): selected_class_var.set(self.class_list[0])
        sc_combo = ttk.Combobox(target_input_container, textvariable=selected_class_var, values=class_options, state="readonly" if self.class_list else "disabled", width=30, font=utils.FONT_NORMAL); single_class_combobox_ref["widget"] = sc_combo

        multi_class_frame_for_listbox = ttk.Frame(target_input_container)
        mc_listbox = tk.Listbox(multi_class_frame_for_listbox, selectmode=tk.EXTENDED, height=4, width=30, font=utils.FONT_NORMAL, exportselection=False, relief=tk.SOLID, borderwidth=1)
        if self.class_list: [mc_listbox.insert(tk.END, cls_item) for cls_item in self.class_list]
        else: mc_listbox.insert(tk.END, "(Chưa có lớp để chọn)"); mc_listbox.config(state=tk.DISABLED)
        mc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); multi_class_listbox_ref["widget"] = mc_listbox
        mc_scrollbar = ttk.Scrollbar(multi_class_frame_for_listbox, orient=tk.VERTICAL, command=mc_listbox.yview); mc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y); mc_listbox.config(yscrollcommand=mc_scrollbar.set)

        ss_entry = ttk.Entry(target_input_container, width=30, font=utils.FONT_NORMAL); student_sbd_entry_ref["widget"] = ss_entry

        ttk.Label(post_frame, text="Nội dung (*):", font=utils.FONT_NORMAL).grid(row=2, column=0, padx=5, pady=5, sticky=tk.NW)
        temp_text_widget = tk.Text(post_frame, height=5, width=60, font=utils.FONT_NORMAL, relief=tk.SOLID, borderwidth=1, wrap=tk.WORD)
        temp_text_widget.grid(row=2, column=1, padx=5, pady=5, sticky=tk.NSEW); content_text_widget_ref["widget"] = temp_text_widget
        content_scrollbar = ttk.Scrollbar(post_frame, orient=tk.VERTICAL, command=temp_text_widget.yview); content_scrollbar.grid(row=2, column=2, sticky=tk.NS, pady=5); temp_text_widget.config(yscrollcommand=content_scrollbar.set)

        post_button = ttk.Button(post_frame, text="Đăng thông báo", style="Accent.TButton", command=post_new_announcement); post_button.grid(row=3, column=1, padx=5, pady=10, sticky=tk.E)
        if not self.class_list and target_type_var.get() != "specific_student": post_button.config(state=tk.DISABLED)
        post_frame.columnconfigure(1, weight=1); post_frame.rowconfigure(2, weight=1)

        history_frame = ttk.LabelFrame(announce_win, text="Lịch sử thông báo", padding="10"); history_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        tree_view_container = ttk.Frame(history_frame); tree_view_container.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        cols = ("ID", "Ngày đăng", "Đối tượng", "Nội dung", "Người đăng")
        announcements_tree = ttk.Treeview(tree_view_container, columns=cols, show="headings", style="Treeview"); announcements_tree_widget_ref["widget"] = announcements_tree
        announcements_tree.heading("ID", text="ID"); announcements_tree.column("ID", width=0, stretch=tk.NO)
        announcements_tree.heading("Ngày đăng", text="Ngày đăng"); announcements_tree.column("Ngày đăng", width=140, anchor=tk.W, stretch=tk.NO)
        announcements_tree.heading("Đối tượng", text="Đối tượng"); announcements_tree.column("Đối tượng", width=120, anchor=tk.W, stretch=tk.NO)
        announcements_tree.heading("Nội dung", text="Nội dung"); announcements_tree.column("Nội dung", width=280, anchor=tk.W)
        announcements_tree.heading("Người đăng", text="Người đăng"); announcements_tree.column("Người đăng", width=100, anchor=tk.W, stretch=tk.NO)
        tree_vsb = ttk.Scrollbar(tree_view_container, orient="vertical", command=announcements_tree.yview); tree_hsb = ttk.Scrollbar(tree_view_container, orient="horizontal", command=announcements_tree.xview)
        announcements_tree.configure(yscrollcommand=tree_vsb.set, xscrollcommand=tree_hsb.set)
        announcements_tree.grid(row=0, column=0, sticky="nsew"); tree_vsb.grid(row=0, column=1, sticky="ns"); tree_hsb.grid(row=1, column=0, sticky="ew")
        tree_view_container.rowconfigure(0, weight=1); tree_view_container.columnconfigure(0, weight=1)
        announcements_tree.bind("<<TreeviewSelect>>", on_tree_select)

        actual_delete_button = ttk.Button(history_frame, text="Xóa Thông báo Đã chọn", style="Red.TButton", state=tk.DISABLED, command=delete_selected_announcement)
        actual_delete_button.pack(side=tk.RIGHT, pady=(5,0), padx=5); delete_ann_button_ref["button"] = actual_delete_button
        ttk.Button(announce_win, text="Đóng", command=announce_win.destroy, style="Accent.TButton").pack(pady=(10,15), side=tk.BOTTOM, anchor=tk.E, padx=10)

        update_target_input_widget()
        load_and_display_announcements()
        content_widget_to_focus = content_text_widget_ref.get("widget")
        if content_widget_to_focus and content_widget_to_focus.winfo_exists():
            announce_win.after(150, lambda: content_widget_to_focus.focus_set())
        pass

    def clear_window(self):
        for widget in self.main_content_wrapper.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.pack_forget()
        pass

    def show_login(self):
        self.clear_window(); self.current_user_role = None; self.current_user_id = None
        if self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
            self.scanner_window_instance.close_window(); self.scanner_window_instance = None
        self.last_added_record = None; self.root.title("Ứng dụng Tổng hợp - Đăng nhập")
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        login_module.show_login_screen(self.login_frame, self.on_login_success, self.student_data)
        pass

    def on_login_success(self, role, user_id):
        self.current_user_role = role; self.current_user_id = user_id
        self.attendance_data = utils.load_attendance_data(); self.last_added_record = None

        if role == "student":
            name, dob = utils.get_student_info(user_id, self.student_data)
            if name is None:
                 messagebox.showerror("Lỗi", f"SBD '{user_id}' không hợp lệ.", parent=self.root); self.show_login(); return
            self.show_student_dashboard()
        elif role == "teacher":
            self.selected_context.set("regular")
            if self.class_list: self.selected_class.set(self.class_list[0])
            else: self.selected_class.set("")
            self.show_teacher_dashboard()
        pass

    def show_student_dashboard(self):
        self.clear_window()
        self.student_frame.pack(fill=tk.BOTH, expand=True)
        for widget in self.student_frame.winfo_children():
            widget.destroy()

        name, dob = utils.get_student_info(self.current_user_id, self.student_data)
        student_class = "N/A"
        if self.student_data is not None and 'Lớp' in self.student_data.columns:
            try:
                class_val = self.student_data.loc[self.current_user_id, 'Lớp']
                student_class = str(class_val).strip() if pd.notna(class_val) and str(class_val).strip() else "N/A"
            except KeyError: student_class = "N/A"
        else: student_class = "N/A"

        top_bar_frame_std = ttk.Frame(self.student_frame, style="TFrame")
        top_bar_frame_std.pack(side=tk.TOP, fill=tk.X, pady=(0, 10), padx=5)
        ttk.Label(top_bar_frame_std, text=f"Chào mừng, {name if name else 'Khách'} ({self.current_user_id})", style="Header.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        logout_icon = self._load_icon("logout.png")
        ttk.Button(top_bar_frame_std, text="Đăng Xuất", command=self.logout, style="Accent.TButton", width=15, image=logout_icon, compound=tk.LEFT).pack(side=tk.RIGHT)
        self.root.title(f"Thông tin Học sinh - {self.current_user_id}")

        main_content_area_std = ttk.Frame(self.student_frame, style="TFrame")
        main_content_area_std.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        info_display_frame = ttk.Frame(main_content_area_std)
        info_display_frame.pack(pady=(0, 10), anchor='w')
        row_idx_info = 0
        if student_class != "N/A":
            ttk.Label(info_display_frame, text="Lớp:", font=utils.FONT_MEDIUM_BOLD).grid(row=row_idx_info, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_display_frame, text=student_class, font=utils.FONT_MEDIUM).grid(row=row_idx_info, column=1, sticky=tk.W, padx=5, pady=2); row_idx_info += 1
        if dob:
            ttk.Label(info_display_frame, text="Ngày sinh:", font=utils.FONT_MEDIUM_BOLD).grid(row=row_idx_info, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_display_frame, text=utils.format_date_dmy(dob), font=utils.FONT_MEDIUM).grid(row=row_idx_info, column=1, sticky=tk.W, padx=5, pady=2); row_idx_info += 1
        if row_idx_info > 0: info_display_frame.columnconfigure(1, weight=1)

        action_buttons_frame_std = ttk.Frame(main_content_area_std)
        action_buttons_frame_std.pack(pady=(5, 15), fill=tk.X)

        managment_icon = self._load_icon("managment.png")
        student_card_icon = self._load_icon("student_card.png")
        scan_qr_icon = self._load_icon("scan_qr.png") 
        upload_icon = self._load_icon("upload.png") # Load the new icon

        buttons_std_defs = [
            ("Xem Mã QR Điểm Danh", self.show_my_qr, scan_qr_icon), 
            ("Xem/Xuất Giấy Báo Thi", self.student_view_ticket, managment_icon),
            ("Xem/Xuất Thẻ Học Sinh", self.student_view_own_card, student_card_icon),
            ("Cập nhật Ảnh Cá nhân", self.show_student_photo_upload_ui, upload_icon) # Assign icon here
        ]
        for i, (text, command, icon) in enumerate(buttons_std_defs):
            btn = ttk.Button(action_buttons_frame_std, text=text, command=command, width=22, image=icon, compound=tk.LEFT if icon else tk.NONE)
            btn.grid(row=0, column=i, padx=5, pady=0, sticky="ew")
            action_buttons_frame_std.columnconfigure(i, weight=1)

        info_pane_std = ttk.PanedWindow(main_content_area_std, orient=tk.HORIZONTAL)
        info_pane_std.pack(fill=tk.BOTH, expand=True)

        announcement_pane_frame = ttk.Frame(info_pane_std, padding=5)
        info_pane_std.add(announcement_pane_frame, weight=1)
        announcements_frame = ttk.LabelFrame(announcement_pane_frame, text="Thông báo mới", padding="10")
        announcements_frame.pack(fill=tk.BOTH, expand=True)

        all_announcements = utils.load_announcements()
        student_announcements_filtered = []
        my_sbd = self.current_user_id
        for ann in all_announcements:
            is_for_student = False; target_sbd_ann = ann.get("target_sbd"); class_name_field_ann = ann.get("class_name")
            if target_sbd_ann and target_sbd_ann == my_sbd: is_for_student = True
            if not is_for_student and student_class != "N/A" and student_class:
                if isinstance(class_name_field_ann, str) and class_name_field_ann.strip() == student_class: is_for_student = True
                elif isinstance(class_name_field_ann, list) and student_class in class_name_field_ann: is_for_student = True
            if not is_for_student:
                 is_general_ann = (class_name_field_ann is None) or (isinstance(class_name_field_ann, str) and not class_name_field_ann.strip()) or (isinstance(class_name_field_ann, list) and not class_name_field_ann)
                 if not target_sbd_ann and is_general_ann: is_for_student = True
            if is_for_student: student_announcements_filtered.append(ann)
        student_announcements_filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        if not student_announcements_filtered:
             ttk.Label(announcements_frame, text="Chưa có thông báo nào.", font=utils.FONT_NORMAL, style="Italic.TLabel").pack(pady=10, padx=5, anchor='nw')
        else:
             max_ann_to_show = 3; content_labels_list = []
             scrollable_content_frame = ttk.Frame(announcements_frame); scrollable_content_frame.pack(fill=tk.BOTH, expand=True)
             for i, ann_item in enumerate(student_announcements_filtered[:max_ann_to_show]):
                 ann_item_frame_inner = ttk.Frame(scrollable_content_frame); ann_item_frame_inner.pack(fill=tk.X, pady=(5,3))
                 ts_author_text = f"[{ann_item.get('timestamp', '')[:16]}] GV: {ann_item.get('author', 'N/A')}"
                 ttk.Label(ann_item_frame_inner, text=ts_author_text, font=utils.FONT_SMALL, foreground=utils.COLOR_TEXT_LIGHT).pack(anchor=tk.W, padx=5)
                 content_preview = ann_item.get("content", ""); content_label = ttk.Label(ann_item_frame_inner, text=content_preview, font=utils.FONT_NORMAL, wraplength=100)
                 content_label.pack(anchor=tk.W, padx=5, pady=(0,5), fill=tk.X); content_labels_list.append(content_label)
                 if i < len(student_announcements_filtered[:max_ann_to_show]) - 1: ttk.Separator(scrollable_content_frame, orient='horizontal').pack(fill='x', pady=(5,2), padx=5)

             def update_all_wraplengths_student(event=None):
                 if announcements_frame.winfo_exists() and announcements_frame.winfo_width() > 20:
                     new_wraplength = announcements_frame.winfo_width() - 40 
                     if new_wraplength < 10: new_wraplength = 10
                     for lbl in content_labels_list:
                         if lbl.winfo_exists(): lbl.config(wraplength=new_wraplength)

             if content_labels_list: announcements_frame.bind("<Configure>", update_all_wraplengths_student, add='+'); announcements_frame.after(50, update_all_wraplengths_student)
             if len(student_announcements_filtered) > max_ann_to_show:
                 def show_all_student_announcements_ui(parent_win, announcements_list_all, current_student_class_name_display): pass 
                 search_icon_small = self._load_icon("search.png", size=(12,12)) 
                 ttk.Button(announcements_frame, text="Xem tất cả...", command=lambda: show_all_student_announcements_ui(self.root, student_announcements_filtered, student_class), style="Link.TButton", image=search_icon_small, compound=tk.LEFT).pack(pady=(5,0), side=tk.BOTTOM, anchor=tk.E, padx=5)

        schedule_pane_frame = ttk.Frame(info_pane_std, padding=5)
        info_pane_std.add(schedule_pane_frame, weight=2) 

        if student_class != "N/A" and student_class:
            student_schedule_display.create_student_schedule_view(
                parent_frame=schedule_pane_frame, 
                student_class=student_class,
                utils_module=utils,
                root_window=self.root
            )
        else:
            ttk.Label(schedule_pane_frame, text="Lịch trình không khả dụng (chưa có lớp).", style="Italic.TLabel").pack(expand=True)
        pass

# --- Thay thế TOÀN BỘ hàm show_teacher_dashboard trong main_app.py ---

    # Trong class MainApplication
    def show_teacher_dashboard(self):
        self.clear_window()
        self.teacher_frame.pack(fill="both", expand=True)
        for widget in self.teacher_frame.winfo_children():
            widget.destroy()

        # --- Thanh trên cùng ---
        top_bar_frame = ttk.Frame(self.teacher_frame, style="TFrame")
        top_bar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 15), padx=5)
        ttk.Label(top_bar_frame, text="Bảng Điều Khiển Giáo Viên", style="AppTitle.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        logout_icon = self._load_icon("logout.png") # Giả sử hàm _load_icon tồn tại và hoạt động
        ttk.Button(top_bar_frame, text=" Đăng Xuất", command=self.logout, style="Accent.TButton", width=15, image=logout_icon, compound=tk.LEFT).pack(side=tk.RIGHT)
        self.root.title(f"Giáo viên: {self.current_user_id} | Ngày: {self.selected_date_str}")

        # --- Khung lựa chọn chung ---
        selection_group = ttk.LabelFrame(self.teacher_frame, text="Tùy chọn chung", padding="10")
        selection_group.pack(fill=tk.X, pady=(0,10), padx=5)
        col_idx = 0

        # <<< PHẦN QUAN TRỌNG: Tạo lại Combobox Lớp >>>
        ttk.Label(selection_group, text="Lớp:", font=utils.FONT_MEDIUM_BOLD).grid(row=0, column=col_idx, padx=(5,2), pady=5, sticky=tk.W); col_idx += 1
        
        # Tạo danh sách lựa chọn bao gồm "Toàn Trường"
        class_options_with_all = ["Toàn Trường"] + (self.class_list if self.class_list else []) # Đảm bảo self.class_list là list
        
        # Đặt giá trị mặc định nếu giá trị hiện tại không hợp lệ hoặc chưa có
        if not self.selected_class.get() or self.selected_class.get() not in class_options_with_all:
            self.selected_class.set(class_options_with_all[0]) # Mặc định là "Toàn Trường"

        # Tạo Combobox
        class_combobox_dash = ttk.Combobox(
            selection_group, 
            textvariable=self.selected_class, 
            values=class_options_with_all, 
            state="readonly", # Chỉ cho chọn, không cho gõ
            width=15, # Điều chỉnh độ rộng nếu cần
            font=utils.FONT_NORMAL
        )
        class_combobox_dash.grid(row=0, column=col_idx, padx=5, pady=5, sticky=tk.EW); col_idx += 1
        selection_group.columnconfigure(col_idx - 1, weight=1) # Cho phép combobox giãn nở
        # <<< KẾT THÚC PHẦN COMBOBOX LỚP >>>

        # Phần Loại ngày và Ngày (giữ nguyên)
        ttk.Label(selection_group, text="Loại ngày:", font=utils.FONT_MEDIUM_BOLD).grid(row=0, column=col_idx, padx=(15, 2), pady=5, sticky=tk.W); col_idx += 1
        ttk.Radiobutton(selection_group, text="Ngày thường", variable=self.selected_context, value="regular").grid(row=0, column=col_idx, padx=2, pady=5, sticky=tk.W); col_idx += 1
        ttk.Radiobutton(selection_group, text="Ngày thi", variable=self.selected_context, value="exam").grid(row=0, column=col_idx, padx=(0, 5), pady=5, sticky=tk.W); col_idx += 1
        selection_group.columnconfigure(col_idx - 3, weight=0); selection_group.columnconfigure(col_idx - 2, weight=0); selection_group.columnconfigure(col_idx - 1, weight=0)
        ttk.Label(selection_group, text=f"Ngày: {self.selected_date_str}", font=utils.FONT_MEDIUM_BOLD).grid(row=0, column=col_idx, padx=(10,5), pady=5, sticky=tk.E)
        selection_group.columnconfigure(col_idx, weight=2)

        # --- Khung chính chứa các nhóm chức năng ---
        functions_area = ttk.Frame(self.teacher_frame)
        functions_area.pack(fill=tk.BOTH, expand=True, padx=5)

        # --- Các Nhóm Chức năng (Group 1, 2, 3 và Actions phụ) ---
        # (Giữ nguyên code các nhóm này như phiên bản đã có icon và CHỈ CÓ 1 NÚT XẾP CHỖ)
        # Ví dụ cho Group 1:
        group1 = ttk.LabelFrame(functions_area, text="Điểm danh & Xếp chỗ", padding="10")
        group1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        btn_width_group = 25
        scan_qr_icon = self._load_icon("scan_qr.png"); manual_type_icon = self._load_icon("manual_type.png")
        attendence_list_icon = self._load_icon("attendence_list.png"); statistics_icon = self._load_icon("statistics.png")
        print_icon = self._load_icon("print.png"); seating_icon = self._load_icon("seating.png")
        ttk.Button(group1, text=" Quét Điểm Danh QR", command=self.start_scan_attendance_teacher, width=btn_width_group, image=scan_qr_icon, compound=tk.LEFT).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(group1, text=" Điểm Danh Thủ Công", command=self.manual_check_in, width=btn_width_group, image=manual_type_icon, compound=tk.LEFT).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(group1, text=" Xem DS Điểm Danh", command=self.view_attendance_list, width=btn_width_group, image=attendence_list_icon, compound=tk.LEFT).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(group1, text=" Xem Thống Kê Điểm Danh", command=self.show_attendance_stats, width=btn_width_group, image=statistics_icon, compound=tk.LEFT).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(group1, text=" Xuất Báo cáo Điểm danh", command=lambda: attendance_report_module.show_export_attendance_report_ui(self.root, self), width=btn_width_group, image=print_icon, compound=tk.LEFT).grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        btn_seating_generic = ttk.Button(group1, text=" Xếp Chỗ Thi", command=self.show_seating_ui, width=btn_width_group, image=seating_icon, compound=tk.LEFT) # Chỉ còn 1 nút, gọi show_seating_ui
        btn_seating_generic.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        group1.columnconfigure(0, weight=1); group1.columnconfigure(1, weight=1)
        
        # Dán code cho group2, group3, extra_actions_group từ phiên bản trước của bạn vào đây...
        # --- Nhóm 2: Quản lý HS & Tài liệu ---
        group2 = ttk.LabelFrame(functions_area, text="Quản lý Học sinh & Tài liệu", padding="10")
        group2.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        search_icon = self._load_icon("search.png"); managment_icon = self._load_icon("managment.png"); student_card_icon = self._load_icon("student_card.png")
        ttk.Button(group2, text=" Tìm kiếm HS Toàn Trường", command=self.show_advanced_student_search_ui, width=btn_width_group, image=search_icon, compound=tk.LEFT).grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(group2, text=" QL Mẫu / Xem / Xuất GBT", command=self.show_teacher_ticket_options, width=btn_width_group, image=managment_icon, compound=tk.LEFT).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(group2, text=" Tạo Thẻ tên Học sinh (PDF)", command=lambda: student_card_module.show_student_card_generator_ui(self.root, self), width=btn_width_group, image=student_card_icon, compound=tk.LEFT).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        group2.columnconfigure(0, weight=1); group2.columnconfigure(1, weight=1)

        # --- Nhóm 3: Quản lý Lớp & Hệ thống ---
        group3 = ttk.LabelFrame(functions_area, text="Quản lý Lớp & Hệ thống", padding="10")
        group3.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        announcement_icon = self._load_icon("announcement.png"); calendar_icon = self._load_icon("calendar.png"); format_icon = self._load_icon("format.png") # or settings.png
        ttk.Button(group3, text=" Đăng/Xem Thông báo Lớp", command=self.show_announcement_management_ui, width=btn_width_group, image=announcement_icon, compound=tk.LEFT).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(group3, text=" Quản lý Lịch trình Sự kiện", command=lambda: schedule_module.show_schedule_manager_ui(self.root, self), width=btn_width_group, image=calendar_icon, compound=tk.LEFT).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(group3, text=" Cấu hình Thông tin Trường", command=self.show_school_config_ui, width=btn_width_group, image=format_icon, compound=tk.LEFT).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        group3.columnconfigure(0, weight=1); group3.columnconfigure(1, weight=1)

        # --- Cấu hình giãn nở ---
        functions_area.columnconfigure(0, weight=1); functions_area.columnconfigure(1, weight=1)
        functions_area.rowconfigure(0, weight=0); functions_area.rowconfigure(1, weight=0)

        # --- Khung Actions phụ ---
        extra_actions_group = ttk.LabelFrame(self.teacher_frame, text="Tác vụ khác", padding="10")
        extra_actions_group.pack(fill=tk.X, pady=(10, 5), padx=5)
        undo_icon = self._load_icon("undo.png"); clean_memory_icon = self._load_icon("clean_memory.png") # or delete_all.png
        self.undo_button = ttk.Button(extra_actions_group, text=" Hoàn tác Điểm danh cuối", command=self.undo_last_attendance, state=tk.DISABLED, image=undo_icon, compound=tk.LEFT)
        self.undo_button.pack(side=tk.LEFT, padx=15, expand=True, fill=tk.X)
        clear_button = ttk.Button(extra_actions_group, text=" Xóa TOÀN BỘ Điểm Danh", command=self.clear_all_attendance_data, style="Red.TButton", image=clean_memory_icon, compound=tk.LEFT)
        clear_button.pack(side=tk.RIGHT, padx=15, expand=True, fill=tk.X)
        self.update_undo_button_state()
        pass

    def show_school_config_ui(self):
        if self.current_user_role != "teacher":
            messagebox.showwarning("Truy cập bị hạn chế", "Chức năng này chỉ dành cho giáo viên.", parent=self.root)
            return

        config_win = tk.Toplevel(self.root)
        config_win.title("Cấu hình Thông tin Trường học & Thẻ")
        config_win.geometry("750x470")
        config_win.transient(self.root); config_win.grab_set()
        config_win.configure(bg=utils.COLOR_BG_FRAME)

        current_config = utils.load_school_config()

        dept_name_var = tk.StringVar(value=current_config.get("dept_name", ""))
        school_name_var = tk.StringVar(value=current_config.get("school_name", ""))
        logo_header_path_var = tk.StringVar(value=os.path.abspath(current_config.get("logo_path", "")) if current_config.get("logo_path") else "")
        logo_card_path_var = tk.StringVar(value=os.path.abspath(current_config.get("school_logo_on_card_path", "")) if current_config.get("school_logo_on_card_path") else "")
        school_year_var = tk.StringVar(value=current_config.get("school_year", f"{datetime.now().year}-{datetime.now().year+1}"))
        card_issuing_place_var = tk.StringVar(value=current_config.get("card_issuing_place", ""))
        card_issuer_name_var = tk.StringVar(value=current_config.get("card_issuer_name", ""))

        main_frame_cfg = ttk.Frame(config_win, padding="15")
        main_frame_cfg.pack(fill=tk.BOTH, expand=True)
        notebook = ttk.Notebook(main_frame_cfg)
        tab_general = ttk.Frame(notebook, padding="10")
        tab_card = ttk.Frame(notebook, padding="10")
        notebook.add(tab_general, text='Thông tin chung')
        notebook.add(tab_card, text='Thông tin Thẻ HS')
        notebook.pack(expand=True, fill='both')

        def browse_logo_file(target_var, description):
            filepath = filedialog.askopenfilename(
                title=f"Chọn file Logo {description}",
                filetypes=[("Ảnh PNG/JPG", "*.png;*.jpg;*.jpeg"), ("Tất cả file", "*.*")],
                parent=config_win
            )
            if filepath:
                try:
                    img_test = Image.open(filepath)
                    img_test.verify()
                    img_test.close()

                    os.makedirs(utils.UPLOADED_LOGO_FOLDER, exist_ok=True)
                    filename = os.path.basename(filepath)
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    new_filename = filename
                    new_path_abs = os.path.abspath(os.path.join(utils.UPLOADED_LOGO_FOLDER, new_filename))
                    while os.path.exists(new_path_abs):
                        new_filename = f"{base}_{counter}{ext}"
                        new_path_abs = os.path.abspath(os.path.join(utils.UPLOADED_LOGO_FOLDER, new_filename))
                        counter += 1

                    import shutil
                    shutil.copy(filepath, new_path_abs)
                    target_var.set(new_path_abs)
                    print(f"DEBUG: Đã chọn và sao chép logo {description} vào: {new_path_abs}")
                    messagebox.showinfo("Đã chọn ảnh", f"Đã chọn logo:\n{new_path_abs}\n\nNhấn 'Lưu Cấu hình' để xác nhận.", parent=config_win)

                except (FileNotFoundError, IsADirectoryError) as e_path:
                     messagebox.showerror("Lỗi File", f"Đường dẫn file không hợp lệ:\n{filepath}\n{e_path}", parent=config_win)
                except ImportError: 
                     messagebox.showerror("Lỗi Thư viện", "Thiếu thư viện Pillow để kiểm tra ảnh.", parent=config_win)
                except Exception as e_copy:
                    messagebox.showerror("Lỗi Xử lý Ảnh", f"Không thể xử lý hoặc sao chép file logo:\n{filepath}\nLỗi: {e_copy}", parent=config_win)
                    print(f"ERROR processing/copying logo: {e_copy}")
                    import traceback
                    traceback.print_exc()

        row_gen = 0 
        ttk.Label(tab_general, text="Sở GD&ĐT:", font=utils.FONT_NORMAL).grid(row=row_gen, column=0, padx=5, pady=8, sticky=tk.W)
        dept_entry = ttk.Entry(tab_general, textvariable=dept_name_var, width=60, font=utils.FONT_NORMAL)
        dept_entry.grid(row=row_gen, column=1, columnspan=2, padx=5, pady=8, sticky=tk.EW)
        row_gen += 1 

        ttk.Label(tab_general, text="Tên Trường:", font=utils.FONT_NORMAL).grid(row=row_gen, column=0, padx=5, pady=8, sticky=tk.W)
        school_entry = ttk.Entry(tab_general, textvariable=school_name_var, width=60, font=utils.FONT_NORMAL)
        school_entry.grid(row=row_gen, column=1, columnspan=2, padx=5, pady=8, sticky=tk.EW)
        row_gen += 1 

        ttk.Label(tab_general, text="Logo trên Header (nhỏ):", font=utils.FONT_NORMAL).grid(row=row_gen, column=0, padx=5, pady=8, sticky=tk.W)
        logo_header_entry = ttk.Entry(tab_general, textvariable=logo_header_path_var, width=50, font=utils.FONT_NORMAL, state='readonly')
        logo_header_entry.grid(row=row_gen, column=1, padx=5, pady=8, sticky=tk.EW)
        ttk.Button(tab_general, text="Chọn...", command=lambda: browse_logo_file(logo_header_path_var, "Header"), width=10).grid(row=row_gen, column=2, padx=5, pady=8)
        row_gen += 1
        tab_general.columnconfigure(1, weight=1)

        row_card = 0
        ttk.Label(tab_card, text="Logo chính trên Thẻ (vuông):", font=utils.FONT_NORMAL).grid(row=row_card, column=0, padx=5, pady=8, sticky=tk.W)
        logo_card_entry = ttk.Entry(tab_card, textvariable=logo_card_path_var, width=50, font=utils.FONT_NORMAL, state='readonly')
        logo_card_entry.grid(row=row_card, column=1, padx=5, pady=8, sticky=tk.EW)
        ttk.Button(tab_card, text="Chọn...", command=lambda: browse_logo_file(logo_card_path_var, "Thẻ HS"), width=10).grid(row=row_card, column=2, padx=5, pady=8)
        row_card += 1

        ttk.Label(tab_card, text="Niên khóa (vd: 2024-2025):", font=utils.FONT_NORMAL).grid(row=row_card, column=0, padx=5, pady=8, sticky=tk.W)
        year_entry = ttk.Entry(tab_card, textvariable=school_year_var, width=60, font=utils.FONT_NORMAL)
        year_entry.grid(row=row_card, column=1, columnspan=2, padx=5, pady=8, sticky=tk.EW)
        row_card += 1

        ttk.Label(tab_card, text="Nơi cấp thẻ (vd: TP. HCM):", font=utils.FONT_NORMAL).grid(row=row_card, column=0, padx=5, pady=8, sticky=tk.W)
        place_entry = ttk.Entry(tab_card, textvariable=card_issuing_place_var, width=60, font=utils.FONT_NORMAL)
        place_entry.grid(row=row_card, column=1, columnspan=2, padx=5, pady=8, sticky=tk.EW)
        row_card += 1

        ttk.Label(tab_card, text="Người ký (Hiệu trưởng):", font=utils.FONT_NORMAL).grid(row=row_card, column=0, padx=5, pady=8, sticky=tk.W)
        issuer_entry = ttk.Entry(tab_card, textvariable=card_issuer_name_var, width=60, font=utils.FONT_NORMAL)
        issuer_entry.grid(row=row_card, column=1, columnspan=2, padx=5, pady=8, sticky=tk.EW)
        row_card += 1
        tab_card.columnconfigure(1, weight=1)

        button_frame_cfg = ttk.Frame(config_win)
        button_frame_cfg.pack(pady=20, padx=15, fill=tk.X, side=tk.BOTTOM)

        def save_config_action():
            logo_header_abs = logo_header_path_var.get().strip()
            logo_card_abs = logo_card_path_var.get().strip()
            logo_header_to_save = logo_header_abs
            logo_card_to_save = logo_card_abs

            new_config_data = {
                "dept_name": dept_name_var.get().strip(),
                "school_name": school_name_var.get().strip(),
                "logo_path": logo_header_to_save,
                "school_logo_on_card_path": logo_card_to_save,
                "school_year": school_year_var.get().strip(),
                "card_issuing_place": card_issuing_place_var.get().strip(),
                "card_issuer_name": card_issuer_name_var.get().strip()
            }
            if utils.save_school_config(new_config_data):
                messagebox.showinfo("Thành công", "Đã lưu cấu hình.", parent=config_win)
                config_win.destroy()

        save_btn_cfg = ttk.Button(button_frame_cfg, text="Lưu Cấu hình", style="Accent.TButton", command=save_config_action)
        save_btn_cfg.pack(side=tk.RIGHT)
        cancel_btn_cfg = ttk.Button(button_frame_cfg, text="Hủy", command=config_win.destroy)
        cancel_btn_cfg.pack(side=tk.RIGHT, padx=10)

        dept_entry.focus_set()
        pass

    def update_undo_button_state(self):
        if hasattr(self, 'undo_button') and self.undo_button.winfo_exists():
            if self.last_added_record: self.undo_button.config(state=tk.NORMAL)
            else: self.undo_button.config(state=tk.DISABLED)
        pass

    def manual_check_in(self):
        if self.current_user_role != "teacher": return
        context = self.selected_context.get(); date_str = self.selected_date_str
        sbd_input = simpledialog.askstring("Điểm danh thủ công", f"Nhập SBD điểm danh [{context.upper()}] ngày {date_str}:", parent=self.root)
        if not sbd_input: return
        sbd = sbd_input.strip(); name, dob = utils.get_student_info(sbd, self.student_data); student_class = "N/A"
        if 'Lớp' in self.student_data.columns:
            try: student_class = self.student_data.loc[sbd, 'Lớp']
            except KeyError: pass
        if name is None: messagebox.showerror("Lỗi SBD", f"Không tìm thấy SBD '{sbd}'.", parent=self.root); return
        self.attendance_data = utils.load_attendance_data()
        if utils.is_student_already_attended(sbd, context, date_str, self.attendance_data):
            messagebox.showwarning("Đã điểm danh", f"HS {sbd} ({name}) đã điểm danh.", parent=self.root); self.last_added_record = None; self.update_undo_button_state(); return
        ts = datetime.now().isoformat(sep=' ', timespec='seconds')
        new_rec = {"sbd": sbd, "class": student_class, "timestamp": ts, "date": date_str, "context": context, "type": "manual"}
        self.attendance_data.append(new_rec)
        if utils.save_attendance_data(self.attendance_data):
            messagebox.showinfo("Thành công", f"Điểm danh thủ công thành công:\nSBD: {sbd}\nTên: {name}", parent=self.root)
            self.last_added_record = new_rec.copy(); self.update_undo_button_state()
        else:
            self.attendance_data.pop(); messagebox.showerror("Lỗi", "Không lưu được điểm danh.", parent=self.root)
            self.last_added_record = None; self.update_undo_button_state()
        pass

    def undo_last_attendance(self):
        if not self.last_added_record: messagebox.showinfo("Thông báo", "Không có thao tác để hoàn tác.", parent=self.root); return
        sbd = self.last_added_record.get('sbd'); name, _ = utils.get_student_info(sbd, self.student_data)
        msg = f"Hoàn tác điểm danh cho SBD: {sbd} ({name or 'N/A'})?"
        if messagebox.askyesno("Xác nhận", msg, parent=self.root, icon='warning'):
            self.attendance_data = utils.load_attendance_data(); init_len = len(self.attendance_data)
            self.attendance_data = [ r for r in self.attendance_data if not (r.get('sbd') == self.last_added_record.get('sbd') and r.get('timestamp') == self.last_added_record.get('timestamp') and r.get('context') == self.last_added_record.get('context') and r.get('date') == self.last_added_record.get('date') and r.get('type') == self.last_added_record.get('type')) ]
            if len(self.attendance_data) < init_len:
                if utils.save_attendance_data(self.attendance_data): messagebox.showinfo("OK", f"Đã hoàn tác điểm danh SBD: {sbd}", parent=self.root); self.last_added_record = None; self.update_undo_button_state()
                else: messagebox.showerror("Lỗi", "Không lưu được sau hoàn tác."); self.attendance_data = utils.load_attendance_data()
            else: messagebox.showerror("Lỗi", "Không tìm thấy bản ghi cuối để hoàn tác."); self.last_added_record = None; self.update_undo_button_state()
        pass

    def clear_all_attendance_data(self):
        if messagebox.askyesno("XÁC NHẬN XÓA", "!!! CẢNH BÁO !!!\nXóa TOÀN BỘ dữ liệu điểm danh?\nKHÔNG thể hoàn tác!", icon='error', default='no', parent=self.root):
            if utils.save_attendance_data([]): self.attendance_data = []; self.last_added_record = None; self.update_undo_button_state(); messagebox.showinfo("OK", "Đã xóa toàn bộ điểm danh.", parent=self.root)
            else: messagebox.showerror("Lỗi", "Xóa thất bại.", parent=self.root)
        pass

    def show_my_qr(self):
        if self.current_user_role == "student" and self.current_user_id: qr_module.show_student_qr_code(self.root, self.current_user_id, self.student_data)
        else: messagebox.showwarning("Lỗi", "Chỉ cho học sinh đã đăng nhập.", parent=self.root)
        pass

    def start_scan_attendance_teacher(self):
        if self.current_user_role != "teacher": messagebox.showwarning("Hạn chế", "Chức năng chỉ dành cho giáo viên.", parent=self.root); return
        context = self.selected_context.get(); date_str = self.selected_date_str
        if self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists(): self.scanner_window_instance.window.lift(); messagebox.showinfo("Thông báo", "Cửa sổ quét đang mở.", parent=self.root); return
        print(f"DEBUG: Mở cửa sổ quét cho Context: {context}, Date: {date_str}")
        self.scanner_window_instance = scan_module.QRCodeScannerWindow(
            parent_window=self.root,
            df_students=self.student_data,
            on_scan_success_callback=self.handle_scan_result,
            photo_folder_path=utils.PHOTO_FOLDER, 
            default_avatar_filename="default_avatar.png" 
        )
        pass

    def handle_scan_result(self, sbd):
        sbd = str(sbd).strip()
        context = self.selected_context.get()
        date_str = self.selected_date_str
        student_name_display = "N/A"
        student_class_display = "N/A"
        photo_path_display = None 
        status_for_scanner = "info" 
        message_for_scanner = ""    

        if not sbd: 
            message_for_scanner = "Mã QR rỗng hoặc không hợp lệ."
            status_for_scanner = "error"
            if self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
                self.scanner_window_instance.update_info(
                    message=message_for_scanner, status=status_for_scanner,
                    student_sbd=sbd 
                )
                self.scanner_window_instance.play_error_sound()
            return

        name_from_df, dob_from_df = utils.get_student_info(sbd, self.student_data) 
        student_name_display = name_from_df if name_from_df else "Không rõ tên"

        class_from_df_val = "N/A"
        if 'Lớp' in self.student_data.columns:
            try:
                class_temp = self.student_data.loc[sbd, 'Lớp']
                class_from_df_val = str(class_temp).strip() if pd.notna(class_temp) else "N/A"
            except KeyError:
                class_from_df_val = "N/A" 
        student_class_display = class_from_df_val

        path_png = os.path.join(utils.PHOTO_FOLDER, f"{sbd}.png")
        path_jpg = os.path.join(utils.PHOTO_FOLDER, f"{sbd}.jpg") 

        if os.path.exists(path_png):
            photo_path_display = path_png
        elif os.path.exists(path_jpg):
            photo_path_display = path_jpg
        else:
            photo_path_display = None 
            
        if name_from_df is None:
            message_for_scanner = f"SBD '{sbd}' không tồn tại trong danh sách."
            status_for_scanner = "error"
            if self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
                self.scanner_window_instance.update_info(
                    message=message_for_scanner, status=status_for_scanner,
                    student_name="N/A", student_sbd=sbd, student_class="N/A",
                    photo_path=None 
                )
                self.scanner_window_instance.play_error_sound()
            return

        self.attendance_data = utils.load_attendance_data() 
        if utils.is_student_already_attended(sbd, context, date_str, self.attendance_data):
            message_for_scanner = f"HS {sbd} ({student_name_display}) ĐÃ ĐIỂM DANH cho buổi {context}."
            status_for_scanner = "warning"
            self.last_added_record = None 
            self.update_undo_button_state()
            if self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
                self.scanner_window_instance.update_info(
                    message=message_for_scanner, status=status_for_scanner,
                    student_name=student_name_display, student_sbd=sbd, student_class=student_class_display,
                    photo_path=photo_path_display
                )
                self.scanner_window_instance.play_duplicate_sound()
            return

        timestamp_iso = datetime.now().isoformat(sep=' ', timespec='seconds')
        new_attendance_record = {
            "sbd": sbd,
            "class": student_class_display, 
            "timestamp": timestamp_iso,
            "date": date_str,
            "context": context,
            "type": "scan"
        }
        self.attendance_data.append(new_attendance_record)

        if utils.save_attendance_data(self.attendance_data):
            self.last_added_record = new_attendance_record.copy()
            self.update_undo_button_state()
            message_for_scanner = f"Điểm danh THÀNH CÔNG: {sbd} ({student_name_display})"
            status_for_scanner = "success"
            if self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
                self.scanner_window_instance.update_info(
                    message=message_for_scanner, status=status_for_scanner,
                    student_name=student_name_display, student_sbd=sbd, student_class=student_class_display,
                    photo_path=photo_path_display
                )
                self.scanner_window_instance.play_success_sound() 
        else:
            self.attendance_data.pop() 
            messagebox.showerror("Lỗi Lưu Trữ", "Không thể lưu dữ liệu điểm danh.", parent=self.root) 
            self.last_added_record = None
            self.update_undo_button_state()
            
            message_for_scanner = f"LỖI HỆ THỐNG khi lưu điểm danh cho {sbd}."
            status_for_scanner = "error"
            if self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
                self.scanner_window_instance.update_info(
                    message=message_for_scanner, status=status_for_scanner,
                    student_name=student_name_display, student_sbd=sbd, student_class=student_class_display,
                    photo_path=photo_path_display 
                )
                self.scanner_window_instance.play_error_sound()
        pass

    # Trong class MainApplication
    def view_attendance_list(self):
        if self.current_user_role != "teacher": return
        
        selected_option = self.selected_class.get() # Lấy giá trị từ Combobox
        s_ctx = self.selected_context.get()
        s_date = self.selected_date_str
        
        class_to_filter = None # Mặc định là không lọc theo lớp (toàn trường)
        window_title_class_part = "Toàn Trường"
        
        if selected_option != "Toàn Trường":
            class_to_filter = selected_option # Lọc theo lớp cụ thể
            window_title_class_part = f"Lớp {selected_option}"
            # Không cần kiểm tra selected_option rỗng vì combobox là readonly và có default
            
        self.attendance_data = utils.load_attendance_data()
        # Gọi hàm lọc với class_to_filter (có thể là None)
        filt_recs = utils.get_attendance_records(self.attendance_data, class_to_filter, s_ctx, s_date)
        filt_recs.sort(key=lambda r: r.get('timestamp', ''))

        view_win = Toplevel(self.root)
        # <<< Cập nhật tiêu đề cửa sổ >>>
        view_win.title(f"DS Điểm danh - {window_title_class_part} ({s_ctx}) - {s_date}")
        view_win.geometry("750x600"); view_win.transient(self.root); view_win.grab_set()
        view_win.configure(bg=utils.COLOR_BG_FRAME)

        top_fr = ttk.Frame(view_win, padding=10); top_fr.pack(pady=5, padx=10, fill=tk.X)
        ttk.Label(top_fr, text="Tìm (SBD/Tên):").pack(side=tk.LEFT, padx=(0,5))
        search_e = ttk.Entry(top_fr); search_e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Nút Xuất CSV với icon
        print_icon_view = self._load_icon("print.png", size=(16,16)) # Load icon nhỏ hơn
        # <<< class_n được truyền vào lambda dựa trên lựa chọn >>>
        export_class_name_param = 'ToanTruong' if selected_option == "Toàn Trường" else selected_option
        ttk.Button(top_fr, text="Xuất CSV", command=lambda current_recs=filt_recs, cn=export_class_name_param: self.export_attendance_to_csv(current_recs, cn, s_ctx, s_date), width=12, image=print_icon_view, compound=tk.LEFT).pack(side=tk.LEFT)

        ttk.Label(view_win, text=f"Tổng số bản ghi: {len(filt_recs)}", font=utils.FONT_MEDIUM_BOLD).pack(pady=(5, 5)) # Sửa text

        list_fr = ttk.Frame(view_win, padding=(10,0,10,10)); list_fr.pack(fill="both", expand=True)
        cols = ("STT", "SBD", "Họ và tên", "Lớp", "Thời gian", "Loại")
        attendance_tree = ttk.Treeview(list_fr, columns=cols, show="headings", style="Treeview")

        for col_name in cols:
            attendance_tree.heading(col_name, text=col_name)
            # Điều chỉnh độ rộng cột nếu cần
            if col_name == "STT": attendance_tree.column(col_name, width=50, anchor=tk.CENTER, stretch=tk.NO)
            elif col_name == "SBD": attendance_tree.column(col_name, width=100, anchor=tk.W)
            elif col_name == "Họ và tên": attendance_tree.column(col_name, width=200, anchor=tk.W)
            elif col_name == "Lớp": attendance_tree.column(col_name, width=100, anchor=tk.W)
            elif col_name == "Thời gian": attendance_tree.column(col_name, width=150, anchor=tk.CENTER)
            elif col_name == "Loại": attendance_tree.column(col_name, width=80, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(list_fr, orient="vertical", command=attendance_tree.yview)
        hsb = ttk.Scrollbar(list_fr, orient="horizontal", command=attendance_tree.xview)
        attendance_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Populate Treeview
        original_data_for_tree = []
        for i, r in enumerate(filt_recs):
            sbd_val=r.get('sbd','')
            # Lấy tên và lớp từ student_data để đảm bảo nhất quán
            name_val, class_val_from_df = utils.get_student_info(sbd_val, self.student_data)
            name_val = name_val or "N/A"
            # Ưu tiên lớp từ student_data nếu có, nếu không thì lấy từ record điểm danh
            class_val_display = str(class_val_from_df).strip() if pd.notna(class_val_from_df) else r.get('class','N/A')

            timestamp_val = r.get('timestamp','')
            type_val = "TC" if r.get('type')=='manual' else "Scan"
            original_data_for_tree.append((i+1, sbd_val, name_val, class_val_display, timestamp_val, type_val))

        def update_treeview_search(event=None): # Đổi tên hàm để tránh trùng
            search_term = search_e.get().lower().strip()
            attendance_tree.delete(*attendance_tree.get_children()) # Clear existing items
            if not original_data_for_tree: return
            shown_count = 0
            for item_data in original_data_for_tree:
                sbd_str = str(item_data[1]).lower()
                name_str = str(item_data[2]).lower()
                if search_term in sbd_str or search_term in name_str:
                    tag = 'evenrow' if shown_count % 2 == 0 else 'oddrow'
                    attendance_tree.insert("", tk.END, values=item_data, tags=(tag,))
                    shown_count += 1
            attendance_tree.tag_configure('evenrow', background=utils.COLOR_LISTBOX_EVEN_ROW)
            attendance_tree.tag_configure('oddrow', background=utils.COLOR_LISTBOX_ODD_ROW)

        update_treeview_search() # Initial population
        search_e.bind("<KeyRelease>", update_treeview_search) # Bind sự kiện tìm kiếm
        search_e.focus_set()

        def update_treeview(event=None):
            search_term = search_e.get().lower().strip()
            attendance_tree.delete(*attendance_tree.get_children()) 
            
            if not original_data_for_tree: return

            shown_count = 0
            for item_data in original_data_for_tree:
                sbd_str = str(item_data[1]).lower()
                name_str = str(item_data[2]).lower()
                
                if search_term in sbd_str or search_term in name_str:
                    tag = 'evenrow' if shown_count % 2 == 0 else 'oddrow'
                    attendance_tree.insert("", tk.END, values=item_data, tags=(tag,))
                    shown_count += 1
            
            attendance_tree.tag_configure('evenrow', background=utils.COLOR_LISTBOX_EVEN_ROW)
            attendance_tree.tag_configure('oddrow', background=utils.COLOR_LISTBOX_ODD_ROW)

        update_treeview() 
        search_e.bind("<KeyRelease>", update_treeview)
        search_e.focus_set()
        
        ttk.Button(view_win, text="Đóng", command=view_win.destroy, style="Accent.TButton").pack(pady=10)
        pass

    # Trong class MainApplication
    def show_attendance_stats(self):
        if self.current_user_role != "teacher": return

        selected_option = self.selected_class.get() # Lấy giá trị từ Combobox
        s_ctx = self.selected_context.get()
        s_date = self.selected_date_str
        
        self.attendance_data = utils.load_attendance_data()
        title_suffix = f"({s_ctx}) - {s_date}"
        
        # Khởi tạo các biến thống kê
        total_students_display = 0
        num_valid_attended = 0
        num_invalid_attended = 0 # Chỉ có ý nghĩa khi xem theo lớp
        num_absent = 0
        absent_sbd_list = []
        percent_attended = 0.0
        window_title = f"Thống Kê Điểm Danh {title_suffix}"
        class_context_for_display = ""
        class_param_for_export = "Unknown" # Giá trị cho tên file export

        if selected_option == "Toàn Trường":
            window_title = f"Thống Kê Chung {title_suffix}"
            class_context_for_display = "(Toàn Trường)"
            class_param_for_export = "ToanTruong"

            if self.student_data is not None:
                total_students_display = len(self.student_data)
                all_sbd_in_school = set(self.student_data.index.astype(str))
                
                attended_sbd_set_all = utils.get_attended_sbd_set(self.attendance_data, None, s_ctx, s_date)
                num_valid_attended = len(attended_sbd_set_all)
                
                # Vắng = Tổng HS trong trường - Số SBD hợp lệ đã điểm danh
                absent_sbd_in_school = all_sbd_in_school - attended_sbd_set_all
                absent_sbd_list = sorted(list(absent_sbd_in_school))
                try: absent_sbd_list.sort(key=lambda x: int(x) if x.isdigit() else x)
                except ValueError: pass
                num_absent = len(absent_sbd_list)
                
                percent_attended = (num_valid_attended / total_students_display * 100) if total_students_display > 0 else 0
            else:
                messagebox.showerror("Lỗi", "Không thể tải dữ liệu học sinh để thống kê.", parent=self.root)
                return

        elif selected_option: # Nếu chọn một lớp cụ thể
             window_title = f"Thống Kê - Lớp {selected_option} {title_suffix}"
             class_context_for_display = f"(Lớp {selected_option})"
             class_param_for_export = selected_option

             if self.student_data is not None and 'Lớp' in self.student_data.columns:
                 class_students_df = self.student_data[self.student_data['Lớp'] == selected_option]
                 all_sbd_in_class = set(class_students_df.index.astype(str))
                 total_students_display = len(all_sbd_in_class)

                 if total_students_display == 0:
                     messagebox.showinfo("Thông báo", f"Không có học sinh nào trong lớp {selected_option} để thống kê.", parent=self.root)
                     # Có thể return hoặc hiển thị cửa sổ trống
                 else:
                     attended_sbd_set_for_context = utils.get_attended_sbd_set(self.attendance_data, None, s_ctx, s_date) # Lấy tất cả điểm danh trong context/ngày

                     # Điểm danh hợp lệ = Những người thuộc lớp VÀ đã điểm danh
                     valid_attended_sbd = all_sbd_in_class.intersection(attended_sbd_set_for_context)
                     num_valid_attended = len(valid_attended_sbd)

                     # Điểm danh không hợp lệ = Những người đã điểm danh NHƯNG không thuộc lớp này
                     # Lấy tất cả SBD đã điểm danh cho lớp này (theo record điểm danh)
                     attended_sbd_in_records_for_class = utils.get_attended_sbd_set(self.attendance_data, selected_option, s_ctx, s_date)
                     invalid_attended_sbd = attended_sbd_in_records_for_class - all_sbd_in_class # Lấy phần dư ra
                     num_invalid_attended = len(invalid_attended_sbd) # Có thể có SBD lạ quét nhầm vào lớp này

                     # Vắng mặt = Những người thuộc lớp NHƯNG không có trong danh sách điểm danh hợp lệ
                     absent_sbd_list = sorted(list(all_sbd_in_class - valid_attended_sbd))
                     try: absent_sbd_list.sort(key=lambda x: int(x) if x.isdigit() else x)
                     except ValueError: pass
                     num_absent = len(absent_sbd_list)

                     percent_attended = (num_valid_attended / total_students_display * 100) if total_students_display > 0 else 0
             else:
                 messagebox.showerror("Lỗi", "Không thể tải dữ liệu học sinh hoặc thiếu cột 'Lớp'.", parent=self.root)
                 return
        else:
            # Trường hợp không có lựa chọn nào (không nên xảy ra)
            return

        # --- Phần hiển thị giao diện thống kê (giữ nguyên cấu trúc, chỉ cập nhật giá trị) ---
        stats_win = Toplevel(self.root); stats_win.title(window_title); stats_win.geometry("700x650"); stats_win.transient(self.root); stats_win.grab_set()
        stats_win.configure(bg=utils.COLOR_BG_FRAME)
        stats_main_frame = ttk.Frame(stats_win, padding=15); stats_main_frame.pack(fill=tk.BOTH, expand=True)
        summary_frame = ttk.LabelFrame(stats_main_frame, text="Tóm tắt Số liệu"); summary_frame.pack(fill=tk.X, pady=(0,15))
        row_idx = 0
        ttk.Label(summary_frame, text=f"Tổng số HS {class_context_for_display}:", font=utils.FONT_MEDIUM).grid(row=row_idx, column=0, sticky=tk.W, pady=4, padx=5)
        ttk.Label(summary_frame, text=f"{total_students_display}", font=utils.FONT_MEDIUM_BOLD).grid(row=row_idx, column=1, sticky=tk.W, pady=4, padx=5); row_idx += 1
        ttk.Label(summary_frame, text=f"Đã điểm danh ({s_ctx}):", font=utils.FONT_MEDIUM).grid(row=row_idx, column=0, sticky=tk.W, pady=4, padx=5)
        valid_label = ttk.Label(summary_frame, text=f"{num_valid_attended}", font=utils.FONT_MEDIUM_BOLD, foreground=utils.COLOR_SUCCESS); valid_label.grid(row=row_idx, column=1, sticky=tk.W, pady=4, padx=5)
        if num_invalid_attended > 0 and selected_option != "Toàn Trường": # Chỉ hiển thị mã ngoài lớp khi xem lớp cụ thể
             ttk.Label(summary_frame, text=f"(+{num_invalid_attended} mã ngoài lớp)", font=utils.FONT_SMALL, foreground=utils.COLOR_WARNING).grid(row=row_idx, column=2, sticky=tk.W, padx=5); row_idx += 1
        else: row_idx += 1 # Tăng dòng dù không hiển thị mã ngoài lớp
        ttk.Label(summary_frame, text=f"Vắng mặt ({s_ctx}):", font=utils.FONT_MEDIUM).grid(row=row_idx, column=0, sticky=tk.W, pady=4, padx=5)
        ttk.Label(summary_frame, text=f"{num_absent}", font=utils.FONT_MEDIUM_BOLD, foreground=utils.COLOR_ERROR).grid(row=row_idx, column=1, sticky=tk.W, pady=4, padx=5); row_idx += 1
        ttk.Label(summary_frame, text=f"Tỷ lệ điểm danh ({s_ctx}):", font=utils.FONT_MEDIUM).grid(row=row_idx, column=0, sticky=tk.W, pady=4, padx=5)
        ttk.Label(summary_frame, text=f"{percent_attended:.2f}%", font=utils.FONT_MEDIUM_BOLD).grid(row=row_idx, column=1, sticky=tk.W, pady=4, padx=5)

        # Phần hiển thị danh sách vắng mặt
        abs_frame_text = f"Danh sách Học sinh Vắng mặt {class_context_for_display}"
        abs_frame = ttk.LabelFrame(stats_main_frame, text=abs_frame_text); abs_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        abs_top_frame = ttk.Frame(abs_frame); abs_top_frame.pack(fill=tk.X, pady=(5,0))
        
        if absent_sbd_list: # Chỉ hiển thị nút xuất nếu có HS vắng
            print_icon_abs = self._load_icon("print.png", size=(16,16))
            ttk.Button(abs_top_frame, text="Xuất CSV DS Vắng", command=lambda: self.export_absent_to_csv(absent_sbd_list, class_param_for_export, s_ctx, s_date), width=20, image=print_icon_abs, compound=tk.LEFT).pack(side=tk.RIGHT, padx=10, pady=5)

        abs_list_frame = ttk.Frame(abs_frame); abs_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        abs_cols = ("STT", "SBD", "Họ và tên", "Lớp") # Thêm cột lớp
        abs_tree = ttk.Treeview(abs_list_frame, columns=abs_cols, show="headings", style="Treeview")
        for col_name in abs_cols:
            abs_tree.heading(col_name, text=col_name)
            if col_name == "STT": abs_tree.column(col_name, width=50, anchor=tk.CENTER, stretch=tk.NO)
            elif col_name == "SBD": abs_tree.column(col_name, width=120, anchor=tk.W)
            elif col_name == "Họ và tên": abs_tree.column(col_name, width=250, anchor=tk.W)
            elif col_name == "Lớp": abs_tree.column(col_name, width=100, anchor=tk.W) # Thêm cột lớp

        abs_vsb = ttk.Scrollbar(abs_list_frame, orient="vertical", command=abs_tree.yview); abs_tree.configure(yscrollcommand=abs_vsb.set)
        abs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); abs_vsb.pack(side=tk.RIGHT, fill=tk.Y)

        if not absent_sbd_list:
            abs_tree.insert("", tk.END, values=("", "Không có học sinh nào vắng mặt.", "", "")) # Thêm giá trị rỗng cho cột Lớp
        else:
            for i, sbd_val in enumerate(absent_sbd_list):
                name_val, class_val_abs = utils.get_student_info(sbd_val, self.student_data)
                class_display_abs = str(class_val_abs).strip() if pd.notna(class_val_abs) else "N/A"
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                abs_tree.insert("", tk.END, values=(i + 1, sbd_val, name_val or "N/A", class_display_abs), tags=(tag,)) # Thêm lớp vào values
            abs_tree.tag_configure('evenrow', background=utils.COLOR_LISTBOX_EVEN_ROW)
            abs_tree.tag_configure('oddrow', background=utils.COLOR_LISTBOX_ODD_ROW)

        ttk.Button(stats_main_frame, text="Đóng", command=stats_win.destroy, style="Accent.TButton").pack(pady=10)
        pass
# Trong class MainApplication (main_app.py)
    def export_attendance_to_csv(self, records, class_n, context, date_s): # Đổi tên thành export_attendance_to_excel
        """Xuất danh sách điểm danh chi tiết ra file Excel được định dạng."""
        if not records:
            messagebox.showinfo("Thông báo", "Không có dữ liệu điểm danh để xuất.", parent=self.root)
            return

        # Đổi phần mở rộng file và tiêu đề dialog
        default_filename = f"ChiTietDiemDanh_{class_n.replace(' ', '_')}_{context}_{date_s}.xlsx"
        filepath = filedialog.asksaveasfilename(
            title="Xuất Excel Chi tiết Điểm danh",
            initialfile=default_filename,
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            parent=self.root
        )
        if not filepath: return

        try:
            # Tạo DataFrame chi tiết
            report_data_details = []
            for i, r in enumerate(records):
                sbd = str(r.get('sbd', ''))
                name, s_cls_orig = utils.get_student_info(sbd, self.student_data)
                current_class = r.get('class', 'N/A')
                if current_class == 'N/A' and pd.notna(s_cls_orig): current_class = s_cls_orig

                report_data_details.append({
                    'STT': i + 1, 'SBD': sbd, 'Họ và tên': name or 'N/A', 'Lớp': current_class,
                    'Thời gian': r.get('timestamp', ''), 'Loại': "TC" if r.get('type') == 'manual' else "Scan",
                    'Ngữ cảnh': r.get('context', ''), 'Ngày': r.get('date', '')
                })
            details_df = pd.DataFrame(report_data_details)

            # Xuất ra Excel dùng xlsxwriter
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                sheet_name_detail = 'ChiTietDiemDanh'
                details_df.to_excel(writer, sheet_name=sheet_name_detail, index=False, startrow=1) # Bắt đầu từ dòng 1

                workbook = writer.book
                worksheet = writer.sheets[sheet_name_detail]

                # Tạo định dạng
                header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
                title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
                cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})

                # Ghi tiêu đề
                title_text = f"CHI TIẾT ĐIỂM DANH - {class_n.upper()} ({context.upper()}) - NGÀY {date_s}"
                worksheet.merge_range(0, 0, 0, len(details_df.columns) - 1, title_text, title_format)
                worksheet.set_row(0, 30)

                # Ghi header và định dạng cột
                for col_num, value in enumerate(details_df.columns.values):
                    worksheet.write(1, col_num, value, header_format)

                worksheet.set_column('A:A', 5, cell_format)  # STT
                worksheet.set_column('B:B', 12, cell_format) # SBD
                worksheet.set_column('C:C', 25, cell_format) # Ho ten
                worksheet.set_column('D:D', 10, cell_format) # Lop
                worksheet.set_column('E:E', 19, cell_format) # Thoi gian
                worksheet.set_column('F:F', 8, cell_format)  # Loai
                worksheet.set_column('G:G', 10, cell_format) # Ngu canh
                worksheet.set_column('H:H', 12, cell_format) # Ngay

                # (Tùy chọn) Freeze hàng header
                worksheet.freeze_panes(2, 0)

            messagebox.showinfo("Thành công", f"Đã xuất file chi tiết điểm danh:\n{filepath}", parent=self.root)
            # Tự động mở file
            try:
                if sys.platform == "win32": os.startfile(filepath)
                elif sys.platform == "darwin": os.system(f'open "{filepath}"')
                else: os.system(f'xdg-open "{filepath}"')
            except Exception as e_open: print(f"Không thể tự động mở file Excel: {e_open}")

        except ImportError:
            messagebox.showerror("Thiếu thư viện", "Vui lòng cài đặt 'xlsxwriter' để định dạng Excel:\n pip install xlsxwriter", parent=self.root)
        except PermissionError:
            messagebox.showerror("Lỗi Quyền Ghi", f"Không có quyền ghi file tại:\n{filepath}\nVui lòng chọn vị trí khác.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Lỗi Xuất Excel", f"Không thể xuất file Excel: {e}", parent=self.root)
            import traceback; traceback.print_exc()
    pass

    def export_absent_to_csv(self, absent_list, class_n, context, date_s): # Đổi tên thành export_absent_to_excel
        """Xuất danh sách học sinh vắng mặt ra file Excel được định dạng."""
        if not absent_list:
            messagebox.showinfo("Thông báo", "Không có học sinh vắng mặt để xuất.", parent=self.root)
            return

        # Đổi phần mở rộng file và tiêu đề dialog
        default_filename = f"DS_VangMat_{class_n.replace(' ', '_')}_{context}_{date_s}.xlsx"
        filepath = filedialog.asksaveasfilename(
            title="Xuất Excel DS Vắng mặt",
            initialfile=default_filename,
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            parent=self.root
        )
        if not filepath: return

        try:
            # Tạo DataFrame DS vắng
            report_data_absent = []
            for i, sbd in enumerate(absent_list):
                name, s_cls = utils.get_student_info(sbd, self.student_data)
                report_data_absent.append({
                    'STT': i + 1, 'SBD': sbd, 'Họ và tên': name or 'N/A', 'Lớp': s_cls or 'N/A'
                })
            absent_df = pd.DataFrame(report_data_absent)

            # Xuất ra Excel dùng xlsxwriter
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                sheet_name_absent = 'DanhSachVangMat'
                absent_df.to_excel(writer, sheet_name=sheet_name_absent, index=False, startrow=1) # Bắt đầu từ dòng 1

                workbook = writer.book
                worksheet = writer.sheets[sheet_name_absent]

                # Tạo định dạng
                header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#FFC7CE', 'border': 1, 'align': 'center'}) # Màu hồng nhạt cho header vắng
                title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
                cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})

                # Ghi tiêu đề
                title_text = f"DANH SÁCH VẮNG MẶT - {class_n.upper()} ({context.upper()}) - NGÀY {date_s}"
                worksheet.merge_range(0, 0, 0, len(absent_df.columns) - 1, title_text, title_format)
                worksheet.set_row(0, 30)

                # Ghi header và định dạng cột
                for col_num, value in enumerate(absent_df.columns.values):
                    worksheet.write(1, col_num, value, header_format)

                worksheet.set_column('A:A', 5, cell_format)  # STT
                worksheet.set_column('B:B', 12, cell_format) # SBD
                worksheet.set_column('C:C', 25, cell_format) # Ho ten
                worksheet.set_column('D:D', 10, cell_format) # Lop

                # Freeze hàng header
                worksheet.freeze_panes(2, 0)

            messagebox.showinfo("Thành công", f"Đã xuất file danh sách vắng mặt:\n{filepath}", parent=self.root)
            # Tự động mở file
            try:
                if sys.platform == "win32": os.startfile(filepath)
                elif sys.platform == "darwin": os.system(f'open "{filepath}"')
                else: os.system(f'xdg-open "{filepath}"')
            except Exception as e_open: print(f"Không thể tự động mở file Excel: {e_open}")

        except ImportError:
            messagebox.showerror("Thiếu thư viện", "Vui lòng cài đặt 'xlsxwriter' để định dạng Excel:\n pip install xlsxwriter", parent=self.root)
        except PermissionError:
            messagebox.showerror("Lỗi Quyền Ghi", f"Không có quyền ghi file tại:\n{filepath}\nVui lòng chọn vị trí khác.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Lỗi Xuất Excel", f"Không thể xuất file Excel: {e}", parent=self.root)
            import traceback; traceback.print_exc()
    pass

# Trong class MainApplication (main_app.py)

    def show_seating_ui(self): # <<< Sử dụng tên hàm gốc
        """Hiển thị giao diện xếp chỗ dựa trên lựa chọn Lớp hoặc Toàn Trường,
        LUÔN MỞ CỬA SỔ NGAY CẢ KHI DANH SÁCH ĐIỂM DANH RỖNG."""
        if self.current_user_role != "teacher":
            messagebox.showwarning("Hạn chế", "Chức năng chỉ dành cho giáo viên.", parent=self.root)
            return

        selected_option = self.selected_class.get() # Lấy giá trị từ Combobox
        s_date = self.selected_date_str
        s_ctx = "exam" # Mặc định context là 'exam'

        self.attendance_data = utils.load_attendance_data()
        att_sbd_list = [] # Khởi tạo danh sách rỗng
        class_name_for_module = ""
        att_sbd_set = set() # Khởi tạo set rỗng

        if selected_option == "Toàn Trường":
            # Lấy SBD của TẤT CẢ học sinh đã điểm danh
            att_sbd_set = utils.get_attended_sbd_set(self.attendance_data, None, s_ctx, s_date)
            class_name_for_module = "ToanTruong" # Gửi tín hiệu đặc biệt
            # <<< BỎ KIỂM TRA VÀ RETURN KHI RỖNG >>>
            # if not att_sbd_set:
            #      messagebox.showinfo("Thông báo", f"Chưa có học sinh nào điểm danh cho ngữ cảnh '{s_ctx}' vào ngày {s_date}.", parent=self.root)
            #      # return # << BỎ RETURN

        elif selected_option: # Nếu là một lớp cụ thể được chọn
            # Lấy SBD của học sinh trong lớp đã chọn
            att_sbd_set = utils.get_attended_sbd_set(self.attendance_data, selected_option, s_ctx, s_date)
            class_name_for_module = selected_option # Gửi tên lớp cụ thể
            # <<< BỎ KIỂM TRA VÀ RETURN KHI RỖNG >>>
            # if not att_sbd_set:
            #      messagebox.showinfo("Thông báo", f"Chưa có học sinh nào thuộc lớp '{selected_option}' điểm danh cho ngữ cảnh '{s_ctx}' vào ngày {s_date}.", parent=self.root)
            #      # return # << BỎ RETURN

        else: # Trường hợp không có gì được chọn (ít khi xảy ra)
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn 'Toàn Trường' hoặc một lớp cụ thể.", parent=self.root)
            return # Trường hợp này vẫn nên return

        # Chuyển set thành list và sắp xếp (ngay cả khi set rỗng)
        att_sbd_list = sorted(list(att_sbd_set))
        try:
            att_sbd_list.sort(key=lambda x: int(x) if x.isdigit() else x)
        except ValueError:
            pass # Sắp xếp chữ nếu không phải số

        # <<< LUÔN GỌI MODULE XẾP CHỖ >>>
        # Ngay cả khi att_sbd_list rỗng, cửa sổ vẫn sẽ mở
        seating_module.show_arrangement_ui(
            parent_window=self.root,
            attended_sbd_list_for_class=att_sbd_list, # Có thể là list rỗng
            df_students_global=self.student_data,
            selected_class_name=class_name_for_module, # "ToanTruong" hoặc tên lớp
            context=s_ctx,
            date_str=s_date
        )

# Trong class MainApplication
    def show_seating_ui_all_students(self):
        """Hiển thị giao diện xếp chỗ cho TẤT CẢ học sinh đã điểm danh (không theo lớp)."""
        # --- Đảm bảo thụt lề đúng ---
        if self.current_user_role != "teacher":
            messagebox.showwarning("Hạn chế", "Chức năng chỉ dành cho giáo viên.", parent=self.root)
            return

        s_date = self.selected_date_str
        s_ctx = "exam" # Mặc định context là 'exam' cho việc xếp chỗ thi toàn trường

        self.attendance_data = utils.load_attendance_data() # Tải dữ liệu điểm danh mới nhất

        # Lấy danh sách SBD đã điểm danh của TẤT CẢ HỌC SINH (class_name=None)
        # trong context và ngày đã chọn
        att_sbd_set_all = utils.get_attended_sbd_set(self.attendance_data, None, s_ctx, s_date)

        if not att_sbd_set_all:
             messagebox.showinfo("Thông báo", f"Không có học sinh nào điểm danh cho ngữ cảnh '{s_ctx}' vào ngày {s_date}.", parent=self.root)
             return

        # Sắp xếp danh sách SBD
        att_sbd_list_all = sorted(list(att_sbd_set_all))
        try: # Cố gắng sắp xếp theo số nếu SBD là số
            att_sbd_list_all.sort(key=lambda x: int(x) if x.isdigit() else x)
        except ValueError:
            pass # Nếu không phải số thì giữ nguyên sắp xếp chữ cái

        # Gọi module xếp chỗ, truyền đánh dấu "ToanTruong" và danh sách SBD đầy đủ
        seating_module.show_arrangement_ui(
            parent_window=self.root,
            attended_sbd_list_for_class=att_sbd_list_all, # Danh sách SBD của toàn trường
            df_students_global=self.student_data,
            selected_class_name="ToanTruong", # Đánh dấu đặc biệt cho chế độ toàn trường
            context=s_ctx,
            date_str=s_date
        )

    def student_view_ticket(self):
        if self.current_user_role == "student" and self.current_user_id:
            ticket_module.show_student_ticket_viewer(self.root, self.current_user_id, self.student_data)
        else:
            messagebox.showwarning("Lỗi", "Chức năng chỉ dành cho học sinh đã đăng nhập.", parent=self.root)
        pass

    def show_teacher_ticket_options(self):
        if self.current_user_role != "teacher": return
        options_window = Toplevel(self.root)
        options_window.title("Tùy chọn Giấy Báo Thi")
        options_window.geometry("480x320") 
        options_window.transient(self.root); options_window.grab_set()
        options_window.configure(bg=utils.COLOR_BG_FRAME)

        main_frame = ttk.Frame(options_window, padding="20 20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Chọn chức năng Giấy Báo Thi:", font=utils.FONT_MEDIUM_BOLD, anchor=tk.CENTER).pack(pady=(0, 20))

        btn_width = 38
        managment_icon = self._load_icon("managment.png")
        search_icon = self._load_icon("search.png")
        print_icon = self._load_icon("print.png")

        ttk.Button(main_frame, text="1. Quản lý Thông tin Mẫu chung", width=btn_width, image=managment_icon, compound=tk.LEFT,
                   command=lambda: [options_window.destroy(), ticket_module.show_teacher_ticket_management_ui(self.root)]).pack(pady=8, ipady=6)
        ttk.Button(main_frame, text="2. Xem/Xuất GBT (Từng Thí sinh)", width=btn_width, image=search_icon, compound=tk.LEFT,
                   command=lambda: [options_window.destroy(), ticket_module.show_teacher_ticket_viewer(self.root, self.student_data)]).pack(pady=8, ipady=6)
        ttk.Button(main_frame, text="3. Xuất GBT Hàng loạt (Tất cả HS)", width=btn_width, image=print_icon, compound=tk.LEFT,
                   command=lambda: [options_window.destroy(), ticket_module.export_all_tickets_pdf(self.root, self.student_data)]).pack(pady=8, ipady=6)
        ttk.Button(main_frame, text="Hủy", command=options_window.destroy, width=15, style="Accent.TButton").pack(pady=(15,0))
        pass

    def show_advanced_student_search_ui(self):
        if self.current_user_role != "teacher": messagebox.showwarning("Truy cập bị hạn chế", "Chức năng này chỉ dành cho giáo viên.", parent=self.root); return
        search_win = Toplevel(self.root); search_win.title("Tìm kiếm Học sinh Nâng cao"); search_win.geometry("850x650"); search_win.transient(self.root); search_win.grab_set(); search_win.configure(bg=utils.COLOR_BG_FRAME)
        main_search_frame = ttk.Frame(search_win, padding="10"); main_search_frame.pack(fill=tk.BOTH, expand=True)
        criteria_group = ttk.LabelFrame(main_search_frame, text="Tiêu chí tìm kiếm"); criteria_group.pack(fill=tk.X, pady=5)
        ttk.Label(criteria_group, text="SBD:").grid(row=0, column=0, padx=5, pady=8, sticky=tk.W); sbd_entry = ttk.Entry(criteria_group, width=18); sbd_entry.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)
        ttk.Label(criteria_group, text="Tên HS:").grid(row=0, column=2, padx=(10,5), pady=8, sticky=tk.W); name_entry = ttk.Entry(criteria_group, width=25); name_entry.grid(row=0, column=3, padx=5, pady=8, sticky=tk.EW)
        ttk.Label(criteria_group, text="Lớp:").grid(row=0, column=4, padx=(10,5), pady=8, sticky=tk.W); search_class_var = StringVar(); search_class_list = ["Tất cả"] + (self.class_list if self.class_list else []); search_class_var.set(search_class_list[0])
        class_combo = ttk.Combobox(criteria_group, textvariable=search_class_var, values=search_class_list, state="readonly", width=15); class_combo.grid(row=0, column=5, padx=5, pady=8, sticky=tk.EW);
        if not self.class_list: class_combo.config(state=tk.DISABLED)
        criteria_group.columnconfigure(1, weight=1); criteria_group.columnconfigure(3, weight=2); criteria_group.columnconfigure(5, weight=1)
        button_frame_criteria = ttk.Frame(criteria_group); button_frame_criteria.grid(row=1, column=0, columnspan=6, pady=(10,5))
        results_group = ttk.LabelFrame(main_search_frame, text="Kết quả tìm kiếm"); results_group.pack(fill=tk.BOTH, expand=True, pady=(10,5))
        count_label_search = ttk.Label(results_group, text="Số lượng: 0", font=utils.FONT_NORMAL); count_label_search.pack(pady=(5,5), anchor=tk.W, padx=5)
        tree_frame = ttk.Frame(results_group); tree_frame.pack(fill=tk.BOTH, expand=True)
        cols = ("STT", "SBD", "Họ và tên", "Ngày sinh", "Lớp"); results_tree_search = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Treeview")
        for col in cols:
            results_tree_search.heading(col, text=col)
            if col == "STT": results_tree_search.column(col, width=40, anchor=tk.CENTER, stretch=tk.NO)
            elif col == "SBD": results_tree_search.column(col, width=100, anchor=tk.W)
            elif col == "Họ và tên": results_tree_search.column(col, width=220, anchor=tk.W)
            elif col == "Ngày sinh": results_tree_search.column(col, width=100, anchor=tk.CENTER)
            elif col == "Lớp": results_tree_search.column(col, width=120, anchor=tk.W)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=results_tree_search.yview); hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=results_tree_search.xview)
        results_tree_search.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set); results_tree_search.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); vsb.pack(side=tk.RIGHT, fill=tk.Y); hsb.pack(side=tk.BOTTOM, fill=tk.X)
        bottom_buttons_frame = ttk.Frame(main_search_frame); bottom_buttons_frame.pack(fill=tk.X, pady=(10,0))
        
        print_icon = self._load_icon("print.png")
        export_button_search = ttk.Button(bottom_buttons_frame, text="Xuất kết quả ra CSV", command=lambda: export_search_results(), state=tk.DISABLED, image=print_icon, compound=tk.LEFT); export_button_search.pack(side=tk.LEFT, padx=10)
        ttk.Button(bottom_buttons_frame, text="Đóng", command=search_win.destroy, style="Accent.TButton").pack(side=tk.RIGHT, padx=10)
        current_results_df_search = pd.DataFrame() 
        def perform_search(event=None):
            nonlocal current_results_df_search 
            sbd_query = sbd_entry.get().strip().lower(); name_query = name_entry.get().strip().lower(); class_query = search_class_var.get()
            if not sbd_query and not name_query and (class_query == "Tất cả" or not self.class_list): messagebox.showinfo("Thông báo", "Vui lòng nhập ít nhất một tiêu chí.", parent=search_win); return
            temp_df = self.student_data.copy()
            if sbd_query: temp_df = temp_df[temp_df.index.astype(str).str.lower().str.contains(sbd_query, na=False)]
            if name_query:
                if 'Họ và tên' in temp_df.columns: temp_df = temp_df[temp_df['Họ và tên'].astype(str).str.lower().str.contains(name_query, na=False)]
            if self.class_list and class_query != "Tất cả":
                if 'Lớp' in temp_df.columns: temp_df = temp_df[temp_df['Lớp'].astype(str).str.strip() == class_query]
                else: temp_df = pd.DataFrame(columns=self.student_data.columns) 
            results_tree_search.delete(*results_tree_search.get_children()); current_results_df_search = temp_df.reset_index() 
            for i, row in current_results_df_search.iterrows():
                sbd_val = row.get('SBD', ''); name_val = row.get('Họ và tên', ''); 
                dob_val_raw = row.get('Ngày sinh')
                dob_val = utils.format_date_dmy(dob_val_raw) if pd.notna(dob_val_raw) else ''
                class_val = str(row.get('Lớp', 'N/A')) if 'Lớp' in current_results_df_search.columns and pd.notna(row.get('Lớp')) else 'N/A'
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'; results_tree_search.insert("", tk.END, values=(i + 1, sbd_val, name_val, dob_val, class_val), tags=(tag,))
            results_tree_search.tag_configure('evenrow', background=utils.COLOR_LISTBOX_EVEN_ROW); results_tree_search.tag_configure('oddrow', background=utils.COLOR_LISTBOX_ODD_ROW)
            count_label_search.config(text=f"Số lượng: {len(current_results_df_search)}"); export_button_search.config(state=tk.NORMAL if not current_results_df_search.empty else tk.DISABLED)
        def reset_search_fields():
            nonlocal current_results_df_search 
            sbd_entry.delete(0, tk.END); name_entry.delete(0, tk.END); search_class_var.set(search_class_list[0])
            results_tree_search.delete(*results_tree_search.get_children()); count_label_search.config(text="Số lượng: 0"); export_button_search.config(state=tk.DISABLED)
            current_results_df_search = pd.DataFrame(); sbd_entry.focus_set()
        def export_search_results():
            nonlocal current_results_df_search 
            if current_results_df_search.empty: messagebox.showinfo("Thông báo", "Không có kết quả để xuất.", parent=search_win); return
            filename_suggestion = "ket_qua_tim_kiem_hoc_sinh.csv"
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile=filename_suggestion, title="Lưu kết quả tìm kiếm", parent=search_win )
            if not filepath: return
            try:
                df_to_export = current_results_df_search.copy()
                if 'STT' not in df_to_export.columns: 
                    df_to_export.insert(0, 'STT', range(1, len(df_to_export) + 1))
                
                export_cols_ordered = ['STT', 'SBD', 'Họ và tên', 'Ngày sinh']
                if 'Lớp' in df_to_export.columns: export_cols_ordered.append('Lớp')
                
                final_df_to_export = df_to_export[[col for col in export_cols_ordered if col in df_to_export.columns]]

                final_df_to_export.to_csv(filepath, index=False, encoding='utf-8-sig')
                messagebox.showinfo("Thành công", f"Đã xuất kết quả ra file:\n{filepath}", parent=search_win)
            except Exception as e: messagebox.showerror("Lỗi xuất file", f"Không thể lưu file CSV: {e}", parent=search_win)
        
        search_icon = self._load_icon("search.png")
        search_button = ttk.Button(button_frame_criteria, text="Tìm kiếm", command=perform_search, image=search_icon, compound=tk.LEFT); search_button.pack(side=tk.LEFT, padx=10)
        reset_button = ttk.Button(button_frame_criteria, text="Đặt lại", command=reset_search_fields); reset_button.pack(side=tk.LEFT, padx=10)
        sbd_entry.bind("<Return>", perform_search); name_entry.bind("<Return>", perform_search)
        reset_search_fields()
        pass

    def logout(self):
        print("DEBUG: Gọi hàm logout.")
        if hasattr(self, 'scanner_window_instance') and self.scanner_window_instance and self.scanner_window_instance.window.winfo_exists():
            print("DEBUG: Đóng cửa sổ quét trong logout.")
            try: self.scanner_window_instance.close_window()
            except Exception as e_close_scan: print(f"Lỗi khi đóng cửa sổ quét trong logout: {e_close_scan}")
            self.scanner_window_instance = None
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?", parent=self.root, icon=messagebox.QUESTION):
            print("DEBUG: Người dùng xác nhận đăng xuất.")
            self.show_login()
        else: print("DEBUG: Người dùng hủy đăng xuất.")
        pass

    def student_view_own_card(self):
        if not (self.current_user_role == "student" and self.current_user_id): messagebox.showwarning("Lỗi", "Chức năng chỉ dành cho học sinh đã đăng nhập.", parent=self.root); return
        sbd = self.current_user_id; name, dob_str = utils.get_student_info(sbd, self.student_data); student_class_val = "N/A"
        if self.student_data is not None and 'Lớp' in self.student_data.columns:
            try: student_class_val = self.student_data.loc[sbd, 'Lớp']
            except KeyError: pass
        actual_student_class = str(student_class_val).strip() if pd.notna(student_class_val) else 'N/A'
        if not name: messagebox.showerror("Lỗi", f"Không tìm thấy thông tin cho SBD: {sbd}", parent=self.root); return
        default_filename = f"TheHocSinh_{sbd}.pdf"; output_folder_student_card = "Student_Cards_Output"; os.makedirs(output_folder_student_card, exist_ok=True)
        filepath = filedialog.asksaveasfilename(title="Lưu PDF Thẻ học sinh", initialdir=output_folder_student_card, initialfile=default_filename, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], parent=self.root )
        if not filepath: return
        temp_status_var = tk.StringVar()
        success = student_card_module.generate_student_cards_pdf( main_app_instance=self, selected_sbds_list=[sbd], num_cols_ui=1, num_rows_ui=1, output_filepath=filepath, status_var=temp_status_var, parent_win=self.root )
        if success:
            messagebox.showinfo("Thành công", f"Đã xuất Thẻ Học Sinh của bạn tại:\n{filepath}", parent=self.root)
            try:
                if os.name == 'nt': os.startfile(filepath)
                elif sys.platform == "darwin": import subprocess; subprocess.call(('open', filepath))
                else: import subprocess; subprocess.call(('xdg-open', filepath))
            except Exception as e_open: print(f"Không thể tự động mở file PDF: {e_open}")
        pass

    def show_student_photo_upload_ui(self):
        if not (self.current_user_role == "student" and self.current_user_id):
            messagebox.showwarning("Lỗi", "Chức năng chỉ dành cho học sinh đã đăng nhập.", parent=self.root)
            return

        sbd = self.current_user_id
        name, _ = utils.get_student_info(sbd, self.student_data)

        upload_win = tk.Toplevel(self.root)
        upload_win.title(f"Cập nhật Ảnh - {sbd} ({name})")
        upload_win.geometry("450x550") 
        upload_win.transient(self.root); upload_win.grab_set()
        upload_win.configure(bg=utils.COLOR_BG_FRAME)

        main_frame_upload = ttk.Frame(upload_win, padding="15")
        main_frame_upload.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame_upload, text="Ảnh hiện tại:", font=utils.FONT_MEDIUM_BOLD).pack(pady=(0,5))

        photo_preview_frame = ttk.Frame(main_frame_upload, width=250, height=300, relief=tk.GROOVE, borderwidth=1)
        photo_preview_frame.pack(pady=10)
        photo_preview_frame.pack_propagate(False) 

        photo_preview_label = ttk.Label(photo_preview_frame, text="(Chưa có ảnh)", anchor=tk.CENTER)
        photo_preview_label.pack(expand=True, fill=tk.BOTH)

        selected_photo_path_var = tk.StringVar() 

        def display_preview_image(image_path=None):
            for widget in photo_preview_frame.winfo_children(): 
                widget.destroy()

            photo_label = ttk.Label(photo_preview_frame, text="(Chưa có ảnh)", anchor=tk.CENTER) 
            photo_label.pack(expand=True, fill=tk.BOTH)

            img_to_display_path = image_path 
            if not img_to_display_path: 
                photo_path_png = os.path.join(utils.PHOTO_FOLDER, f"{sbd}.png")
                photo_path_jpg = os.path.join(utils.PHOTO_FOLDER, f"{sbd}.jpg")
                if os.path.exists(photo_path_png): img_to_display_path = photo_path_png
                elif os.path.exists(photo_path_jpg): img_to_display_path = photo_path_jpg

            if img_to_display_path and os.path.exists(img_to_display_path) and Image and ImageTk:
                try:
                    pil_image = Image.open(img_to_display_path)
                    max_w, max_h = 245, 295 
                    pil_image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                    tk_image = ImageTk.PhotoImage(pil_image)

                    photo_label.config(image=tk_image, text="") 
                    photo_label.image = tk_image 
                except Exception as e_load:
                    print(f"Lỗi load ảnh preview '{img_to_display_path}': {e_load}")
                    photo_label.config(text="(Lỗi load ảnh)")
            else:
                print(f"DEBUG: Không tìm thấy ảnh cho SBD {sbd} để preview.")


        def browse_new_photo():
            filepath = filedialog.askopenfilename(
                title="Chọn ảnh cá nhân mới",
                filetypes=[("Ảnh JPG", "*.jpg;*.jpeg"), ("Ảnh PNG", "*.png"), ("Tất cả file", "*.*")],
                parent=upload_win
            )
            if filepath:
                selected_photo_path_var.set(filepath)
                display_preview_image(filepath) 

        def save_photo_action():
            source_path = selected_photo_path_var.get()
            if not source_path or not os.path.exists(source_path):
                messagebox.showwarning("Chưa chọn ảnh", "Vui lòng chọn một ảnh mới để lưu.", parent=upload_win)
                return

            os.makedirs(utils.PHOTO_FOLDER, exist_ok=True)
            target_filename_png = f"{sbd}.png"
            target_filename_jpg = f"{sbd}.jpg"
            target_path_png = os.path.join(utils.PHOTO_FOLDER, target_filename_png)
            target_path_jpg = os.path.join(utils.PHOTO_FOLDER, target_filename_jpg)

            if os.path.exists(target_path_png):
                try: os.remove(target_path_png); print(f"Đã xóa file cũ: {target_path_png}")
                except OSError as e_del: print(f"Lỗi xóa file cũ {target_path_png}: {e_del}")
            if os.path.exists(target_path_jpg):
                try: os.remove(target_path_jpg); print(f"Đã xóa file cũ: {target_path_jpg}")
                except OSError as e_del: print(f"Lỗi xóa file cũ {target_path_jpg}: {e_del}")

            final_target_path = target_path_png 
            try:
                if not Image: 
                    messagebox.showerror("Lỗi Thư viện", "Thiếu thư viện Pillow để lưu ảnh.", parent=upload_win)
                    return

                img_save = Image.open(source_path)
                img_save.save(final_target_path, "PNG") 

                messagebox.showinfo("Thành công", f"Đã cập nhật ảnh thành công!", parent=upload_win)
                selected_photo_path_var.set("") 
                display_preview_image() 
            except Exception as e_save:
                messagebox.showerror("Lỗi Lưu Ảnh", f"Không thể lưu ảnh mới:\n{e_save}", parent=upload_win)
                print(f"ERROR saving photo: {e_save}")


        button_frame_upload = ttk.Frame(main_frame_upload)
        button_frame_upload.pack(pady=15, fill=tk.X)
        
        upload_icon = self._load_icon("upload.png") # Load upload icon

        browse_btn = ttk.Button(button_frame_upload, text="Chọn ảnh mới...", command=browse_new_photo, width=18, image=upload_icon, compound=tk.LEFT) # Add icon here
        browse_btn.pack(side=tk.LEFT, padx=10, expand=True)

        save_btn = ttk.Button(button_frame_upload, text="Lưu ảnh", command=save_photo_action, style="Accent.TButton", width=12)
        save_btn.pack(side=tk.LEFT, padx=10, expand=True)

        close_btn = ttk.Button(button_frame_upload, text="Đóng", command=upload_win.destroy, width=12)
        close_btn.pack(side=tk.LEFT, padx=10, expand=True)

        display_preview_image()
        pass


if __name__ == "__main__":
    required_files = [utils.STUDENT_DATA_FILE]
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing: messagebox.showerror("Thiếu File", f"Không tìm thấy các file cần thiết:\n" + "\n".join(missing)); exit()

    icons_dir = "icons"
    if not os.path.exists(icons_dir):
        try:
            os.makedirs(icons_dir)
            print(f"INFO: Đã tạo thư mục '{icons_dir}'. Vui lòng đặt các file icon (ví dụ: logout.png, calendar.png, ...) vào đây.")
        except OSError as e:
            print(f"WARNING: Không thể tạo thư mục '{icons_dir}': {e}. Các icon có thể không hiển thị.")


    if not os.path.exists(utils.ATTENDANCE_FILE): utils.save_attendance_data([])
    if not os.path.exists(utils.TICKET_TEMPLATE_FILE): ticket_module.save_ticket_template_data({})
    if not os.path.exists(utils.ANNOUNCEMENTS_FILE): utils.save_announcements([])
    if not os.path.exists(utils.SCHEDULE_FILE): utils.save_schedule([])
    if not os.path.exists(utils.SCHOOL_CONFIG_FILE): utils.save_school_config({})
    if not os.path.exists(utils.UNUSABLE_SEATS_FILE):
        try:
             import seating_module 
             seating_module.save_unusable_seats("dummy_key_init", set())
        except ImportError:
             print("Lỗi: Không thể import seating_module để tạo file unusable_seats.json")
        except Exception as e_init_seat:
             print(f"Lỗi khi tạo file unusable_seats.json: {e_init_seat}")


    root = tk.Tk()
    app = MainApplication(root) 

    if hasattr(app, 'student_data') and app.student_data is not None:
        print("Khởi tạo MainApplication thành công. Bắt đầu mainloop...")
        root.mainloop()
    else:
        print("Khởi tạo ứng dụng thất bại.")
