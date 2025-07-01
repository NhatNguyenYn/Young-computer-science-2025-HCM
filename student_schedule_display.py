# student_schedule_display.py
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from datetime import datetime, date # Thêm date
import pandas as pd
try:
    from tkcalendar import Calendar
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False
    Calendar = None

# Không import utils trực tiếp, nhận qua tham số

def create_student_schedule_view(parent_frame, student_class, utils_module, root_window):
    """
    Tạo và hiển thị khung lịch trình cho học sinh, bao gồm cả sự kiện Toàn trường.
    """
    print(f"\n--- DEBUG (student_schedule_display.py) ---") # DEBUG START
    print(f"Gọi create_student_schedule_view cho lớp: '{student_class}'") # DEBUG LỚP

    # Lấy các hằng số và hàm từ utils_module để tránh lỗi nếu không có
    # --- THAY THẾ KHỐI NÀY Ở ĐẦU HÀM create_student_schedule_view ---
    # Lấy các hằng số và hàm từ utils_module
    FONT_NORMAL = getattr(utils_module, 'FONT_NORMAL', ('Arial', 10))
    FONT_MEDIUM = getattr(utils_module, 'FONT_MEDIUM', ('Arial', 11))
    FONT_MEDIUM_BOLD = getattr(utils_module, 'FONT_MEDIUM_BOLD', ('Arial', 11, 'bold'))
    FONT_SMALL = getattr(utils_module, 'FONT_SMALL', ('Arial', 9)) # Tuple (font, size)
    COLOR_BG_FRAME = getattr(utils_module, 'COLOR_BG_FRAME', 'white')
    COLOR_TEXT_LIGHT = getattr(utils_module, 'COLOR_TEXT_LIGHT', '#666666')
    COLOR_LISTBOX_EVEN_ROW = getattr(utils_module, 'COLOR_LISTBOX_EVEN_ROW', '#F9F9F9')
    COLOR_LISTBOX_ODD_ROW = getattr(utils_module, 'COLOR_LISTBOX_ODD_ROW', 'white')
    FONT_FAMILY = getattr(utils_module, 'FONT_FAMILY', 'Arial')
    FONT_SIZE_NORMAL = getattr(utils_module, 'FONT_SIZE_NORMAL', 10)
    FONT_SIZE_SMALL = getattr(utils_module, 'FONT_SIZE_SMALL', 9) # Chỉ lấy size
    EVENT_TYPE_COLORS = getattr(utils_module, 'EVENT_TYPE_COLORS', {}) # Lấy màu sự kiện
    COLOR_PRIMARY = getattr(utils_module, 'COLOR_PRIMARY', '#0078D4')
    load_schedule = getattr(utils_module, 'load_schedule', lambda: []) # Hàm load
    # --- HẾT KHỐI THAY THẾ ---

    if not TKCALENDAR_AVAILABLE:
        ttk.Label(parent_frame, text="Lịch không khả dụng (thiếu tkcalendar).").pack(pady=20)
        print("DEBUG (student_schedule_display): tkcalendar không khả dụng.")
        return

    if not student_class or student_class == "N/A":
        ttk.Label(parent_frame, text="Lịch trình không khả dụng (chưa có lớp hợp lệ).").pack(pady=20)
        print(f"DEBUG (student_schedule_display): Lớp không hợp lệ ('{student_class}'), không hiển thị lịch.")
        return

    # Xóa widget cũ nếu có
    for widget in parent_frame.winfo_children():
        widget.destroy()

    # Khung bao ngoài
    schedule_display_frame = ttk.LabelFrame(parent_frame, text="Lịch trình Lớp học", padding="10")
    schedule_display_frame.pack(fill=tk.BOTH, expand=True) # Bỏ padx, pady để nó fill hết parent
    print(f"DEBUG: Đã tạo schedule_display_frame cho student.")

    student_cal_selected_date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    student_events_treeview = None # Tham chiếu Treeview
    student_cal = None # Tham chiếu Calendar
    tag_colors_ref = {} # Lưu tag màu cho calendar

    # --- Hàm logic cục bộ ---
    def update_student_calendar_events():
        """Cập nhật màu sắc sự kiện trên lịch của học sinh."""
        nonlocal student_cal, tag_colors_ref
        if not student_cal: return

        # Xóa sự kiện và tag cũ
        student_cal.calevent_remove('all')
        for tag in student_cal.tag_names():
            if tag.startswith("st_type_") or tag == 'st_event_default':
                try: student_cal.tag_delete(tag)
                except: pass

        all_events = load_schedule()
        events_for_student_or_all = [
            evt for evt in all_events
            if evt.get("target_class") == student_class or evt.get("target_class") == "__ALL__"
        ]

        # Định nghĩa lại tag màu (chỉ cần cho các loại có sự kiện liên quan)
        event_colors = EVENT_TYPE_COLORS
        defined_tags = {}
        default_color = event_colors.get("Khác", "#EEEEEE")
        try: student_cal.tag_config('st_event_default', background=default_color, foreground='black')
        except: pass

        unique_types_in_view = set(evt.get("type", "Khác") for evt in events_for_student_or_all)
        for ev_type in unique_types_in_view:
            color = event_colors.get(ev_type, default_color)
            tag_name = f"st_type_{ev_type.lower().replace(' ', '_').replace('/', '_')}"
            try:
                student_cal.tag_config(tag_name, background=color, foreground='black')
                defined_tags[ev_type] = tag_name
            except Exception as e_tag: print(f"HS Sched: Lỗi tag {tag_name}: {e_tag}")
        tag_colors_ref = defined_tags # Cập nhật ref

        # Thêm sự kiện vào lịch
        for event in events_for_student_or_all:
            try:
                event_date_obj = datetime.strptime(event['date'], '%Y-%m-%d').date()
                event_type = event.get("type", "Khác")
                tag_name_to_apply = tag_colors_ref.get(event_type, 'st_event_default')
                title = event.get("title", "...")
                student_cal.calevent_create(event_date_obj, title, tags=tag_name_to_apply)
            except ValueError: pass
            except Exception as e: print(f"HS Sched: Lỗi thêm event calendar: {e}")
        student_cal.update_idletasks()
        print(f"DEBUG: Đã cập nhật {len(events_for_student_or_all)} sự kiện trên lịch HS.")


    # --- Thay thế hàm này trong student_schedule_display.py ---
    def load_student_events_treeview(target_date_str):
        """Cập nhật Treeview với sự kiện cho ngày đã chọn, bao gồm cả Toàn trường."""
        nonlocal student_events_treeview, student_class # Đảm bảo student_class có thể truy cập
        if not student_events_treeview:
            print("LỖI (student_schedule_display): Treeview không tồn tại!")
            return
        if not student_class or student_class == "N/A":
             print("LỖI (student_schedule_display): student_class không hợp lệ!")
             student_events_treeview.insert("", tk.END, values=("", "Lỗi: Lớp không xác định", "", ""), tags=('error',))
             try: student_events_treeview.tag_configure('error', foreground='red')
             except: pass
             return

        print(f"\nDEBUG (student_schedule_display): Bắt đầu load_student_events_treeview...")
        print(f"  -> Ngày mục tiêu: '{target_date_str}'")
        print(f"  -> Lớp của HS: '{student_class}'")

        student_events_treeview.delete(*student_events_treeview.get_children()) # Xóa dữ liệu cũ
        all_events = load_schedule() # Gọi hàm load từ utils_module đã truyền vào
        print(f"  -> Đã load {len(all_events)} sự kiện từ file.")

        events_for_student_day = []
        print("  -> Bắt đầu lọc sự kiện:")
        for idx, event in enumerate(all_events):
            event_date = event.get("date")
            target_class = event.get("target_class") # Lấy lớp mục tiêu của sự kiện
            event_title = event.get("title", "Không có tiêu đề") # Lấy tiêu đề để debug

            # print(f"    Xét event {idx+1}: Date='{event_date}', Target='{target_class}', Title='{event_title}'") # Bỏ comment để debug siêu chi tiết

            # 1. Kiểm tra ngày khớp
            date_match = (event_date == target_date_str)
            if not date_match:
                # print(f"      -> Ngày không khớp.")
                continue # Bỏ qua nếu ngày không đúng

            # 2. Kiểm tra lớp khớp HOẶC là Toàn trường
            # Đảm bảo so sánh không phân biệt chữ hoa/thường và khoảng trắng (nếu cần)
            # nhưng ở đây ta giả định dữ liệu đã chuẩn hóa khi lưu
            is_specific_class_match = (target_class == student_class)
            is_all_class_match = (target_class == "__ALL__")
            class_match = is_specific_class_match or is_all_class_match

            # print(f"      -> Kiểm tra lớp: Target='{target_class}', HS Class='{student_class}' -> class_match={class_match} (Specific={is_specific_class_match}, All={is_all_class_match})")

            if class_match:
                events_for_student_day.append(event)
                print(f"      -> KHỚP! Thêm event ID: {event.get('id')}")

        # Sắp xếp theo thời gian
        events_for_student_day.sort(key=lambda x: (x.get("time") if x.get("time") else "99:99"))
        print(f"  -> Tìm thấy tổng cộng {len(events_for_student_day)} sự kiện phù hợp cho ngày này.")

        # Hiển thị lên Treeview
        if not events_for_student_day:
             student_events_treeview.insert("", tk.END, values=("", "Không có sự kiện", "", ""), tags=('italic',))
             try: student_events_treeview.tag_configure('italic', font=(FONT_FAMILY, FONT_SIZE_NORMAL, 'italic'), foreground=COLOR_TEXT_LIGHT)
             except: pass
        else:
            for i, event in enumerate(events_for_student_day):
                 target_cls = event.get("target_class", "")
                 display_cls = "Toàn trường" if target_cls == "__ALL__" else target_cls
                 event_type = event.get("type", "Khác")
                 title_with_type = f"({event_type}) {event.get('title', 'N/A')}"

                 student_events_treeview.insert("", tk.END, values=(
                    event.get("time", "--:--"),
                    title_with_type,
                    display_cls,
                    event.get("description", "")
                 ))
        print(f"DEBUG (student_schedule_display): Hoàn thành load Treeview.\n") # DEBUG LOAD END


    def on_student_cal_select(event=None):
         nonlocal student_cal, student_cal_selected_date
         if not student_cal: return
         try:
            selected_date = student_cal.selection_get() # Lấy date object
            if selected_date:
                 formatted_date = selected_date.strftime('%Y-%m-%d')
                 if student_cal_selected_date.get() != formatted_date:
                     print(f"DEBUG: HS Ngày đổi thành '{formatted_date}'. Load Treeview.")
                     student_cal_selected_date.set(formatted_date)
                     load_student_events_treeview(formatted_date)
                 # else: print(f"DEBUG: HS Ngày không đổi.") # Bỏ bớt log
         except Exception as e: print(f"HS Lỗi xử lý ngày: {e}")

    # --- Layout bằng PanedWindow ---
    sched_pane = ttk.PanedWindow(schedule_display_frame, orient=tk.HORIZONTAL)
    sched_pane.pack(fill=tk.BOTH, expand=True)

    # Khung chứa Lịch
    student_cal_frame = ttk.Frame(sched_pane, padding=5)
    sched_pane.add(student_cal_frame, weight=1)

    student_cal = Calendar(student_cal_frame, selectmode='day', locale='vi_VN',
                           date_pattern='yyyy-mm-dd',
                           font=(FONT_FAMILY, FONT_SIZE_SMALL),
                           borderwidth=1, relief="solid",
                           selectbackground=COLOR_PRIMARY, selectforeground='white')
    student_cal.pack(fill=tk.BOTH, expand=True)
    student_cal.bind("<<CalendarSelected>>", on_student_cal_select)
    print("DEBUG: Đã tạo và bind Calendar widget cho HS.")

    # Khung chứa danh sách sự kiện
    student_events_frame = ttk.Frame(sched_pane, padding=5)
    sched_pane.add(student_events_frame, weight=2) # Cho phần này rộng hơn

    ttk.Label(student_events_frame, text="Sự kiện trong ngày:", font=FONT_MEDIUM).pack(pady=(0, 5), anchor=tk.W)

    events_tree_container = ttk.Frame(student_events_frame)
    events_tree_container.pack(fill=tk.BOTH, expand=True)

    cols_stud_ev = ("time", "title_type", "class", "desc") # Sửa tên cột nội bộ
    student_events_treeview = ttk.Treeview(events_tree_container, columns=cols_stud_ev, show="headings", height=8)

    student_events_treeview.heading("time", text="Giờ"); student_events_treeview.column("time", width=50, stretch=tk.NO, anchor=tk.CENTER)
    student_events_treeview.heading("title_type", text="Sự kiện (Loại)"); student_events_treeview.column("title_type", width=200) # Sửa heading
    student_events_treeview.heading("class", text="Phạm vi"); student_events_treeview.column("class", width=80, stretch=tk.NO) # Đổi heading lớp
    student_events_treeview.heading("desc", text="Mô tả"); student_events_treeview.column("desc", width=200)

    ev_stud_vsb = ttk.Scrollbar(events_tree_container, orient="vertical", command=student_events_treeview.yview)
    student_events_treeview.configure(yscrollcommand=ev_stud_vsb.set)
    student_events_treeview.grid(row=0, column=0, sticky="nsew"); ev_stud_vsb.grid(row=0, column=1, sticky="ns")
    events_tree_container.rowconfigure(0, weight=1); events_tree_container.columnconfigure(0, weight=1)
    print("DEBUG: Đã tạo Treeview sự kiện cho HS.")

    # Load dữ liệu ban đầu
    schedule_display_frame.after(100, update_student_calendar_events) # Load màu lịch
    schedule_display_frame.after(150, on_student_cal_select) # Load treeview cho ngày hiện tại

    print(f"--- KẾT THÚC DEBUG create_student_schedule_view ---")