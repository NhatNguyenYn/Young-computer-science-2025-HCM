# schedule_module.py
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from datetime import datetime, date # Thêm date
import pandas as pd
try:
    from tkcalendar import Calendar, DateEntry
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False
    Calendar = None
    DateEntry = None

# Import utils nhưng không dùng trực tiếp, nhận qua tham số
import utils # Cần để dùng utils.FONT_* etc.

# ----- HÀM HIỂN THỊ DIALOG THÊM/SỬA SỰ KIỆN -----
# (Nằm ngoài hàm chính để dễ quản lý)
def show_add_edit_event_dialog(parent_window, main_app_instance, event_id, selected_date_on_calendar, on_save_callback):
    """
    Hiển thị dialog để thêm hoặc sửa sự kiện, bao gồm Loại sự kiện VÀ Lớp áp dụng.
    """
    is_edit_mode = event_id is not None
    dialog_title = "Sửa Sự kiện" if is_edit_mode else "Thêm Sự kiện Mới"

    event_dialog = tk.Toplevel(parent_window)
    event_dialog.title(dialog_title)
    event_dialog.geometry("500x480") # Kích thước có ô Lớp
    event_dialog.transient(parent_window); event_dialog.grab_set()
    event_dialog.configure(bg=utils.COLOR_BG_FRAME)

    # --- Biến lưu trữ ---
    title_var = tk.StringVar()
    date_var_str = tk.StringVar()
    time_var = tk.StringVar()
    event_type_var = tk.StringVar()
    target_class_display_var = tk.StringVar() # Biến cho giá trị hiển thị của Combobox Lớp

    # Lấy danh sách loại sự kiện và màu sắc (nếu có)
    event_types = list(getattr(utils, 'EVENT_TYPE_COLORS', {}).keys())
    if not event_types: # Fallback nếu không có màu
        event_types = ["Học tập", "Kiểm tra", "Ngoại khóa", "Họp", "Nghỉ lễ", "Khác"]

    # Lấy danh sách lớp từ main_app và tạo options cho Combobox Lớp
    class_list_from_main = getattr(main_app_instance, 'class_list', [])
    class_display_options = ["Toàn trường"] + class_list_from_main
    # Mapping giữa giá trị hiển thị và giá trị lưu trữ ("Toàn trường" -> "__ALL__")
    class_value_map = {"Toàn trường": "__ALL__"}
    for cls in class_list_from_main:
        class_value_map[cls] = cls # Lớp cụ thể giữ nguyên tên

    # --- Load dữ liệu cũ nếu sửa ---
    original_event_data = None
    initial_date_obj = None
    if is_edit_mode:
        all_events = utils.load_schedule()
        original_event_data = next((evt for evt in all_events if evt.get("id") == event_id), None)
        if original_event_data:
            title_var.set(original_event_data.get("title", ""))
            date_str_saved = original_event_data.get("date", "")
            date_var_str.set(date_str_saved)
            if date_str_saved:
                try: initial_date_obj = datetime.strptime(date_str_saved, '%Y-%m-%d').date()
                except ValueError: pass
            time_var.set(original_event_data.get("time", ""))
            event_type_var.set(original_event_data.get("type", event_types[0]))

            # Xác định giá trị hiển thị ban đầu cho Combobox Lớp
            saved_target_class_value = original_event_data.get("target_class", "__ALL__")
            initial_class_display = "Toàn trường" # Mặc định
            for display_key, stored_value in class_value_map.items():
                if stored_value == saved_target_class_value:
                    initial_class_display = display_key
                    break
            target_class_display_var.set(initial_class_display)

        else:
            messagebox.showerror("Lỗi", f"Không tìm thấy sự kiện ID: {event_id}", parent=event_dialog)
            event_dialog.destroy(); return
    else: # Thêm mới
        if selected_date_on_calendar:
            date_var_str.set(selected_date_on_calendar)
            try: initial_date_obj = datetime.strptime(selected_date_on_calendar, '%Y-%m-%d').date()
            except ValueError: initial_date_obj = date.today()
        else:
            initial_date_obj = date.today()
            date_var_str.set(initial_date_obj.strftime('%Y-%m-%d'))
        event_type_var.set(event_types[0]) # Mặc định loại sự kiện
        target_class_display_var.set("Toàn trường") # Mặc định lớp là Toàn trường

    # --- Form nhập liệu ---
    form_frame = ttk.Frame(event_dialog, padding="15")
    form_frame.pack(fill=tk.BOTH, expand=True)
    row_idx = 0

    # Tiêu đề
    ttk.Label(form_frame, text="Tiêu đề (*):", font=utils.FONT_NORMAL).grid(row=row_idx, column=0, padx=5, pady=6, sticky=tk.W)
    title_entry = ttk.Entry(form_frame, textvariable=title_var, width=45, font=utils.FONT_NORMAL); title_entry.grid(row=row_idx, column=1, columnspan=3, padx=5, pady=6, sticky=tk.EW); row_idx += 1

    # Ngày
    ttk.Label(form_frame, text="Ngày (*):", font=utils.FONT_NORMAL).grid(row=row_idx, column=0, padx=5, pady=6, sticky=tk.W)
    date_entry_widget = None
    if DateEntry: date_entry_widget = DateEntry(form_frame, width=18, background=utils.COLOR_PRIMARY, foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', locale='vi_VN', firstweekday='monday', date=initial_date_obj, font=utils.FONT_NORMAL, style='DateEntryStyle.TEntry')
    else: date_entry_widget = ttk.Entry(form_frame, textvariable=date_var_str, width=20, font=utils.FONT_NORMAL) # Fallback
    date_entry_widget.grid(row=row_idx, column=1, padx=5, pady=6, sticky=tk.W)

    # Thời gian
    ttk.Label(form_frame, text="Thời gian (HH:MM):", font=utils.FONT_NORMAL).grid(row=row_idx, column=2, padx=(10,5), pady=6, sticky=tk.W); time_entry = ttk.Entry(form_frame, textvariable=time_var, width=8, font=utils.FONT_NORMAL); time_entry.grid(row=row_idx, column=3, padx=5, pady=6, sticky=tk.W); row_idx += 1

    # <<< LỚP ÁP DỤNG >>>
    ttk.Label(form_frame, text="Lớp áp dụng:", font=utils.FONT_NORMAL).grid(row=row_idx, column=0, padx=5, pady=6, sticky=tk.W)
    class_combo_dialog = ttk.Combobox(form_frame, textvariable=target_class_display_var,
                                      values=class_display_options, state="readonly",
                                      width=43, font=utils.FONT_NORMAL)
    class_combo_dialog.grid(row=row_idx, column=1, columnspan=3, padx=5, pady=6, sticky=tk.EW); row_idx += 1

    # Loại sự kiện
    ttk.Label(form_frame, text="Loại sự kiện:", font=utils.FONT_NORMAL).grid(row=row_idx, column=0, padx=5, pady=6, sticky=tk.W); type_combo = ttk.Combobox(form_frame, textvariable=event_type_var, values=event_types, state="readonly", width=43, font=utils.FONT_NORMAL); type_combo.grid(row=row_idx, column=1, columnspan=3, padx=5, pady=6, sticky=tk.EW); row_idx += 1

    # Mô tả
    ttk.Label(form_frame, text="Mô tả:", font=utils.FONT_NORMAL).grid(row=row_idx, column=0, padx=5, pady=6, sticky=tk.NW); desc_text = tk.Text(form_frame, height=5, width=40, font=utils.FONT_NORMAL, relief=tk.SOLID, borderwidth=1, wrap=tk.WORD); desc_text.grid(row=row_idx, column=1, columnspan=3, padx=5, pady=6, sticky=tk.NSEW); desc_scrollbar = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=desc_text.yview); desc_scrollbar.grid(row=row_idx, column=4, padx=(0,5), pady=6, sticky=tk.NS); desc_text.config(yscrollcommand=desc_scrollbar.set); row_idx += 1
    if is_edit_mode and original_event_data: desc_text.insert("1.0", original_event_data.get("description", ""))

    form_frame.columnconfigure(1, weight=1); form_frame.columnconfigure(3, weight=0); form_frame.rowconfigure(row_idx -1, weight=1)

    # --- Nút Lưu và Hủy ---
    button_dialog_frame = ttk.Frame(event_dialog); button_dialog_frame.pack(pady=15, padx=15, fill=tk.X, side=tk.BOTTOM)
    # --- Logic Lưu ---
    def save_event_action():
        title = title_var.get().strip();
        if not title: messagebox.showerror("Thiếu thông tin", "Vui lòng nhập Tiêu đề.", parent=event_dialog); title_entry.focus_set(); return
        event_date_str = "";
        try:
            if DateEntry and isinstance(date_entry_widget, DateEntry): event_date_str = date_entry_widget.get_date().strftime('%Y-%m-%d')
            elif isinstance(date_entry_widget, ttk.Entry): event_date_str = date_entry_widget.get().strip(); datetime.strptime(event_date_str, '%Y-%m-%d')
            else: raise ValueError("Không thể lấy ngày.")
        except Exception as e: messagebox.showerror("Lỗi định dạng", "Ngày không hợp lệ (YYYY-MM-DD).", parent=event_dialog); return
        event_time_str = time_var.get().strip()
        if event_time_str:
            try: datetime.strptime(event_time_str, '%H:%M')
            except ValueError: messagebox.showerror("Lỗi định dạng", "Thời gian sai định dạng (HH:MM).", parent=event_dialog); return
        description = desc_text.get("1.0", tk.END).strip(); event_type = event_type_var.get()
        
        # <<< LẤY GIÁ TRỊ LỚP TỪ COMBOBOX VÀ CHUYỂN ĐỔI >>>
        selected_display_class = target_class_display_var.get()
        target_class_to_save = class_value_map.get(selected_display_class, "__ALL__") # Lấy giá trị lưu trữ

        event_data_to_save = {"title": title, "date": event_date_str, "time": event_time_str, "description": description, "type": event_type, "target_class": target_class_to_save} # Lưu giá trị đúng
        
        all_events = utils.load_schedule()
        if is_edit_mode:
            event_data_to_save["id"] = event_id; event_data_to_save["creator_id"] = original_event_data.get("creator_id", main_app_instance.current_user_id); event_data_to_save["timestamp_created"] = original_event_data.get("timestamp_created", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            found_index = next((i for i, evt in enumerate(all_events) if evt.get("id") == event_id), -1)
            if found_index != -1: all_events[found_index] = event_data_to_save
            else: messagebox.showerror("Lỗi", "Không tìm thấy sự kiện gốc.", parent=event_dialog); return
        else:
            event_data_to_save["id"] = utils.generate_event_id(main_app_instance.current_user_id); event_data_to_save["creator_id"] = main_app_instance.current_user_id; event_data_to_save["timestamp_created"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            all_events.append(event_data_to_save)
            
        if utils.save_schedule(all_events):
            messagebox.showinfo("Thành công", f"Đã lưu sự kiện!", parent=parent_window)
            event_dialog.destroy();
            if on_save_callback: on_save_callback()
        else: messagebox.showerror("Lỗi Lưu", "Không thể lưu lịch trình.", parent=event_dialog)

    save_button = ttk.Button(button_dialog_frame, text="Lưu", style="Accent.TButton", command=save_event_action); save_button.pack(side=tk.RIGHT, padx=5)
    cancel_button = ttk.Button(button_dialog_frame, text="Hủy", command=event_dialog.destroy); cancel_button.pack(side=tk.RIGHT, padx=10)
    title_entry.focus_set()


# ----- HÀM CHÍNH HIỂN THỊ GIAO DIỆN QUẢN LÝ LỊCH TRÌNH -----
# <<< ĐÂY LÀ HÀM CHÍNH BỊ THIẾU TRONG FILE TRƯỚC >>>
# ----- THAY THẾ TOÀN BỘ HÀM NÀY TRONG schedule_module.py -----

# ----- HÀM CHÍNH HIỂN THỊ GIAO DIỆN QUẢN LÝ LỊCH TRÌNH -----
def show_schedule_manager_ui(parent_root, main_app_instance):
    """Tạo và hiển thị giao diện quản lý lịch trình chính."""

    if not TKCALENDAR_AVAILABLE:
        messagebox.showerror("Thiếu thư viện",
                             "Vui lòng cài đặt thư viện 'tkcalendar' để sử dụng chức năng này.\n"
                             "(Chạy: pip install tkcalendar)",
                             parent=parent_root)
        return

    schedule_win = tk.Toplevel(parent_root)
    schedule_win.title("Quản lý Lịch trình Sự kiện")
    schedule_win.geometry("950x650")
    schedule_win.transient(parent_root)
    schedule_win.grab_set()
    schedule_win.configure(bg=utils.COLOR_BG_FRAME)

    # --- Biến lưu trữ và Tham chiếu Widget ---
    selected_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    selected_event_id_var = tk.StringVar()
    events_tree_ref = {"widget": None}
    edit_button_ref = {"button": None}
    delete_button_ref = {"button": None}
    calendar_ref = {"widget": None}
    # tag_colors_ref không cần thiết nữa

    # ===================================================================
    # PHẦN 1: ĐỊNH NGHĨA CÁC HÀM LOGIC LỒNG NHAU
    # ===================================================================

# Trong schedule_module.py

    def update_calendar_events_with_tags():
        """Cập nhật các sự kiện trên Calendar với màu sắc theo loại (ưu tiên loại quan trọng)."""
        cal = calendar_ref.get("widget")
        if not cal:
            print("Lỗi: Calendar widget không tồn tại.")
            return

        # 1. Xóa sự kiện và tag cũ
        cal.calevent_remove('all')
        # Lấy danh sách tag hiện có TRƯỚC khi xóa để tránh lỗi không cần thiết
        existing_tags = cal.tag_names()
        for tag in existing_tags:
            if tag.startswith("type_") or tag == 'event_default':
                try:
                    cal.tag_delete(tag)
                except tk.TclError: pass # Bỏ qua lỗi nếu tag không tồn tại (có thể do theme)

        # 2. Tải sự kiện và nhóm theo ngày
        all_events = utils.load_schedule()
        events_by_date = {}
        for event in all_events:
            try:
                # Chuyển đổi ngày từ string sang date object
                event_date_obj = datetime.strptime(event['date'], '%Y-%m-%d').date()
                if event_date_obj not in events_by_date:
                    events_by_date[event_date_obj] = []
                events_by_date[event_date_obj].append(event)
            except (ValueError, KeyError):
                # Bỏ qua các sự kiện có ngày không hợp lệ hoặc thiếu key 'date'
                # print(f"DEBUG: Bỏ qua sự kiện có ngày không hợp lệ: {event.get('id')}")
                pass

        # 3. Định nghĩa lại tất cả các tag màu cần thiết
        event_colors = getattr(utils, 'EVENT_TYPE_COLORS', {})
        tag_name_map = {} # Map từ loại sự kiện -> tên tag

        # Định nghĩa tag mặc định
        default_color = event_colors.get("Khác", "#EEEEEE")
        try: cal.tag_config('event_default', background=default_color, foreground='black')
        except Exception as e: print(f"Lỗi config tag default: {e}")

        # Định nghĩa các tag cho từng loại có màu
        for ev_type, color in event_colors.items():
            # Tạo tên tag hợp lệ (loại bỏ ký tự đặc biệt, khoảng trắng)
            safe_type_name = "".join(c for c in ev_type if c.isalnum() or c == '_').lower()
            tag_name = f"type_{safe_type_name}"
            tag_name_map[ev_type] = tag_name # Lưu mapping
            try:
                cal.tag_config(tag_name, background=color, foreground='black')
                # print(f"DEBUG: Configured tag '{tag_name}' for type '{ev_type}' with color {color}")
            except Exception as e_tag:
                print(f"Lỗi cấu hình tag '{tag_name}': {e_tag}")
                tag_name_map[ev_type] = 'event_default' # Dùng default nếu lỗi

        # 4. Xác định tag ưu tiên và tạo sự kiện trên lịch cho mỗi ngày
        # Thứ tự ưu tiên: Loại nào xuất hiện trước trong list này sẽ được ưu tiên tô màu
        priority_order = ["Kiểm tra", "Họp", "Nghỉ lễ", "Ngoại khóa", "Học tập", "Khác"]

        for event_date, events_on_day in events_by_date.items():
            primary_tag = 'event_default' # Tag mặc định
            primary_title = "..." # Text hiển thị mặc định ngắn gọn
            highest_priority_found = len(priority_order) # Index càng nhỏ càng ưu tiên cao

            # Tìm loại sự kiện có ưu tiên cao nhất trong ngày
            for event in events_on_day:
                ev_type = event.get("type", "Khác")
                try:
                    current_priority = priority_order.index(ev_type)
                    if current_priority < highest_priority_found:
                        highest_priority_found = current_priority
                        primary_tag = tag_name_map.get(ev_type, 'event_default')
                        primary_title = event.get("title", "...")[:15] + ('...' if len(event.get("title", "")) > 15 else '') # Lấy title ngắn gọn
                except ValueError: # Nếu loại sự kiện không có trong priority_order, coi là thấp nhất
                    if len(priority_order) < highest_priority_found: # Chỉ cập nhật nếu chưa có tag nào khác ngoài default
                        highest_priority_found = len(priority_order)
                        primary_tag = tag_name_map.get("Khác", 'event_default')
                        primary_title = event.get("title", "...")[:15] + ('...' if len(event.get("title", "")) > 15 else '')


            # Chỉ tạo MỘT sự kiện ảo trên lịch cho ngày đó với tag ưu tiên
            # Nội dung text không quá quan trọng nếu chỉ muốn hiển thị màu nền
            try:
                cal.calevent_create(event_date, primary_title, tags=primary_tag)
                # print(f"DEBUG: Created event on {event_date} with primary tag: {primary_tag}")
            except Exception as e:
                print(f"Lỗi tạo calendar event cho ngày {event_date}: {e}")

        # Cập nhật lại giao diện lịch
        cal.update_idletasks()
        print(f"DEBUG: Đã cập nhật calendar events với màu ưu tiên.")

    def load_events_for_selected_date_treeview():
        """Cập nhật Treeview với các sự kiện cho ngày đã chọn."""
        current_events_tree = events_tree_ref.get("widget");
        if not current_events_tree: return
        target_date = selected_date_var.get(); current_events_tree.delete(*current_events_tree.get_children())
        all_events = utils.load_schedule()
        events_on_selected_date = [evt for evt in all_events if evt.get("date") == target_date]
        events_on_selected_date.sort(key=lambda x: (x.get("time") if x.get("time") else "99:99"))
        if not events_on_selected_date:
            current_events_tree.insert("", tk.END, values=("", "--:--", "Không có sự kiện", "", ""), tags=('italic',))
            try: current_events_tree.tag_configure('italic', font=utils.FONT_SMALL + ('italic',), foreground=utils.COLOR_TEXT_LIGHT)
            except: pass
        else:
            for i, event in enumerate(events_on_selected_date):
                event_type_display = f"({event.get('type', 'Khác')}) "; event_title = event.get('title', 'N/A'); full_title_with_type = event_type_display + event_title
                target_cls = event.get("target_class", ""); display_cls = "Toàn trường" if target_cls == "__ALL__" else target_cls
                current_events_tree.insert("", tk.END, iid=event.get("id"), values=(event.get("id", ""), event.get("time", "--:--"), full_title_with_type, display_cls, event.get("description", "")))
        reset_edit_delete_buttons()

    def on_date_select(event=None):
         cal = calendar_ref.get("widget");
         if not cal: return
         try:
            selected_date = cal.selection_get();
            if selected_date: formatted_date = selected_date.strftime('%Y-%m-%d'); selected_date_var.set(formatted_date); load_events_for_selected_date_treeview()
         except Exception as e: print(f"Date select error: {e}")

    def on_event_tree_select(event=None):
        current_tree = events_tree_ref.get("widget"); edit_button = edit_button_ref.get("button"); delete_button = delete_button_ref.get("button")
        if not current_tree or not current_tree.winfo_exists(): return
        selected_items = current_tree.selection()
        if selected_items: item_iid = selected_items[0]; selected_event_id_var.set(item_iid);
        if edit_button: edit_button.config(state=tk.NORMAL);
        if delete_button: delete_button.config(state=tk.NORMAL);
        else: reset_edit_delete_buttons()

    def refresh_all_views():
        """Load lại dữ liệu và cập nhật cả Calendar và Treeview."""
        print("DEBUG: Refreshing all schedule views...")
        update_calendar_events_with_tags()      # Cập nhật màu sắc trên lịch
        load_events_for_selected_date_treeview() # Cập nhật danh sách trong Treeview
        print("DEBUG: Refresh complete.")

    def add_event_action(): show_add_edit_event_dialog(schedule_win, main_app_instance, None, selected_date_var.get(), refresh_all_views)
    
    def edit_event_action(): 
        event_id = selected_event_id_var.get(); # Lấy ID đã lưu khi chọn trên Treeview
        if not event_id: 
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một sự kiện để sửa.", parent=schedule_win); 
            return; 
        # Gọi dialog sửa với event_id
        show_add_edit_event_dialog(schedule_win, main_app_instance, event_id, None, refresh_all_views)
    
    # --- HÀM DELETE ĐÃ SỬA LỖI NAME ERROR ---
    def delete_event_action():
        # Hàm này cần truy cập: selected_event_id_var, events_tree_ref, schedule_win
        event_id = selected_event_id_var.get() # Lấy ID từ biến StringVar
        if not event_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một sự kiện để xóa.", parent=schedule_win)
            return

        current_tree = events_tree_ref.get("widget")
        confirm_title = "sự kiện đã chọn"
        try:
            # Cố gắng lấy tiêu đề từ Treeview để hiển thị trong hộp thoại xác nhận
            if current_tree and current_tree.exists(event_id):
                 # values=(id, time, title_type, class, desc) -> index 2 là title_type
                 confirm_title = str(current_tree.item(event_id, "values")[2])
        except Exception as e_get_title:
             print(f"Lỗi khi lấy tiêu đề sự kiện để xóa: {e_get_title}")
             confirm_title = f"sự kiện ID: {event_id}" # Fallback nếu không lấy được tiêu đề

        # Hỏi xác nhận trước khi xóa
        if messagebox.askyesno("Xác nhận Xóa", f"Bạn có chắc muốn xóa:\n'{confirm_title}' không?", icon='warning', parent=schedule_win):
            all_events = utils.load_schedule() # Tải danh sách hiện tại
            initial_len = len(all_events)
            
            # Tạo danh sách mới, loại bỏ sự kiện có ID trùng khớp
            # Biến event_id đã được định nghĩa ở đầu hàm này và có thể truy cập ở đây
            updated_events = [evt for evt in all_events if evt.get("id") != event_id] 
            
            # Kiểm tra xem có thực sự xóa được sự kiện nào không
            if len(updated_events) < initial_len:
                # Lưu lại danh sách đã cập nhật
                if utils.save_schedule(updated_events):
                    messagebox.showinfo("Thành công", "Đã xóa sự kiện.", parent=schedule_win)
                    refresh_all_views() # Cập nhật lại giao diện
                else:
                    messagebox.showerror("Lỗi", "Không thể lưu lịch trình sau khi xóa.", parent=schedule_win)
            else:
                 # Trường hợp này ít xảy ra nếu ID được lấy từ Treeview
                 messagebox.showerror("Lỗi", f"Không tìm thấy sự kiện ID '{event_id}' trong dữ liệu để xóa.", parent=schedule_win)
                 refresh_all_views() # Vẫn cập nhật lại giao diện phòng trường hợp dữ liệu không đồng bộ
    # --- Hết hàm delete_event_action ---

    def reset_edit_delete_buttons():
        selected_event_id_var.set(""); edit_button = edit_button_ref.get("button"); delete_button = delete_button_ref.get("button")
        if edit_button: edit_button.config(state=tk.DISABLED);
        if delete_button: delete_button.config(state=tk.DISABLED);

    # ===================================================================
    # TẠO WIDGET GIAO DIỆN
    # ===================================================================
    main_pane = ttk.PanedWindow(schedule_win, orient=tk.HORIZONTAL); main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    calendar_frame = ttk.Frame(main_pane, padding=5); main_pane.add(calendar_frame, weight=1)
    if Calendar: cal = Calendar(calendar_frame, selectmode='day', locale='vi_VN', date_pattern='yyyy-mm-dd', font=utils.FONT_NORMAL, headersfont=utils.FONT_BOLD, borderwidth=1, relief="solid", selectbackground=utils.COLOR_PRIMARY, selectforeground='white'); cal.pack(fill=tk.BOTH, expand=True); cal.bind("<<CalendarSelected>>", on_date_select); calendar_ref["widget"] = cal
    else: ttk.Label(calendar_frame, text="Lịch không khả dụng.").pack(expand=True)
    events_frame = ttk.Frame(main_pane, padding=5); main_pane.add(events_frame, weight=2)
    selected_date_label = ttk.Label(events_frame, textvariable=selected_date_var, font=utils.FONT_MEDIUM_BOLD); selected_date_label.pack(pady=(0, 5))
    events_tree_frame = ttk.Frame(events_frame); events_tree_frame.pack(fill=tk.BOTH, expand=True)
    cols_events = ("ID", "Thời gian", "Tiêu đề và Loại", "Phạm vi", "Mô tả"); actual_events_tree = ttk.Treeview(events_tree_frame, columns=cols_events, show="headings", style="Treeview", selectmode="browse"); events_tree_ref["widget"] = actual_events_tree
    actual_events_tree.heading("ID", text="ID"); actual_events_tree.column("ID", width=0, stretch=tk.NO); actual_events_tree.heading("Thời gian", text="Giờ"); actual_events_tree.column("Thời gian", width=60, anchor=tk.CENTER, stretch=tk.NO); actual_events_tree.heading("Tiêu đề và Loại", text="Sự kiện (Loại)"); actual_events_tree.column("Tiêu đề và Loại", width=250, anchor=tk.W); actual_events_tree.heading("Phạm vi", text="Phạm vi"); actual_events_tree.column("Phạm vi", width=80, anchor=tk.W, stretch=tk.NO); actual_events_tree.heading("Mô tả", text="Mô tả"); actual_events_tree.column("Mô tả", width=200, anchor=tk.W)
    ev_vsb = ttk.Scrollbar(events_tree_frame, orient="vertical", command=actual_events_tree.yview); ev_hsb = ttk.Scrollbar(events_tree_frame, orient="horizontal", command=actual_events_tree.xview); actual_events_tree.configure(yscrollcommand=ev_vsb.set, xscrollcommand=ev_hsb.set); actual_events_tree.grid(row=0, column=0, sticky="nsew"); ev_vsb.grid(row=0, column=1, sticky="ns"); ev_hsb.grid(row=1, column=0, sticky="ew"); events_tree_frame.rowconfigure(0, weight=1); events_tree_frame.columnconfigure(0, weight=1); actual_events_tree.bind("<<TreeviewSelect>>", on_event_tree_select); actual_events_tree.bind("<Double-Button-1>", lambda e: edit_event_action())
    button_area = ttk.Frame(events_frame); button_area.pack(fill=tk.X, pady=(10, 0))
    add_icon = main_app_instance._load_icon("add.png", size=(16,16)) if hasattr(main_app_instance, '_load_icon') else None; edit_icon = main_app_instance._load_icon("edit.png", size=(16,16)) if hasattr(main_app_instance, '_load_icon') else None; delete_icon = main_app_instance._load_icon("delete.png", size=(16,16)) if hasattr(main_app_instance, '_load_icon') else None
    add_button = ttk.Button(button_area, text=" Thêm", image=add_icon, compound=tk.LEFT, command=add_event_action, style="Accent.TButton"); add_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X, ipady=2)
    actual_edit_button = ttk.Button(button_area, text=" Sửa", image=edit_icon, compound=tk.LEFT, state=tk.DISABLED, command=edit_event_action); actual_edit_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X, ipady=2); edit_button_ref["button"] = actual_edit_button
    actual_delete_button = ttk.Button(button_area, text=" Xóa", image=delete_icon, compound=tk.LEFT, style="Red.TButton", state=tk.DISABLED, command=delete_event_action); actual_delete_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X, ipady=2); delete_button_ref["button"] = actual_delete_button
    close_icon_main = main_app_instance._load_icon("close.png", size=(16,16)) if hasattr(main_app_instance, '_load_icon') else None; ttk.Button(schedule_win, text=" Đóng", image=close_icon_main, compound=tk.LEFT, command=schedule_win.destroy, style="Accent.TButton").pack(pady=(10, 15), side=tk.BOTTOM, anchor=tk.E, padx=10)

    # ===================================================================
    # GỌI HÀM LOGIC BAN ĐẦU
    # ===================================================================
    schedule_win.after(50, refresh_all_views) # Load dữ liệu và cập nhật UI

# --- HẾT HÀM show_schedule_manager_ui ---

# --- HÀM show_add_edit_event_dialog (Đã được định nghĩa ở trên) ---