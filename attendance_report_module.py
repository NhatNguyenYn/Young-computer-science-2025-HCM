# attendance_report_module.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import pandas as pd
import sys  # <<< THÊM DÒNG NÀY
import os   # <<< THÊM DÒNG NÀY
# Giả sử tkcalendar được cài đặt và utils.py ở cùng cấp
try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False
    # Không cần messagebox ở đây, sẽ xử lý trong UI

import utils # Module utils của bạn

# Hàm này sẽ chứa UI chọn tiêu chí
def show_export_attendance_report_ui(parent_root, main_app_instance):
    # (Code UI giữ nguyên như bạn đã gửi)
    if main_app_instance.current_user_role != "teacher":
        messagebox.showwarning("Truy cập bị hạn chế", "Chức năng này chỉ dành cho giáo viên.", parent=parent_root)
        return

    report_win = tk.Toplevel(parent_root)
    report_win.title("Xuất Báo cáo Điểm danh Tổng hợp")
    report_win.geometry("550x320")
    report_win.transient(parent_root)
    report_win.grab_set()
    report_win.configure(bg=utils.COLOR_BG_FRAME)

    criteria_frame = ttk.LabelFrame(report_win, text="Chọn Tiêu chí Báo cáo", padding="15")
    criteria_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    # 1. Chọn Lớp
    ttk.Label(criteria_frame, text="Chọn Lớp:", font=utils.FONT_NORMAL).grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
    report_selected_class_var = tk.StringVar()
    base_class_options = main_app_instance.class_list if main_app_instance.class_list else []
    report_class_options = ["Tất cả các lớp"] + base_class_options
    
    class_combobox_state = "disabled"
    if not main_app_instance.class_list: report_selected_class_var.set("(Không có lớp để chọn)")
    elif report_class_options:
         # Ưu tiên giá trị đang chọn trên dashboard nếu nó hợp lệ
         current_dash_selection = main_app_instance.selected_class.get()
         # Chuyển "ToanTruong" thành "Tất cả các lớp" để khớp options
         if current_dash_selection == "ToanTruong": 
             current_dash_selection_display = "Tất cả các lớp"
         else:
             current_dash_selection_display = current_dash_selection
         
         if current_dash_selection_display in report_class_options:
              report_selected_class_var.set(current_dash_selection_display)
         else: # Nếu không hợp lệ thì chọn mặc định
             report_selected_class_var.set(report_class_options[0]) 
         class_combobox_state = "readonly"
    else: report_selected_class_var.set("(Lỗi tải danh sách lớp)")

    report_class_combobox = ttk.Combobox(criteria_frame, textvariable=report_selected_class_var, 
                                         values=report_class_options, # Luôn hiển thị options đầy đủ
                                         state=class_combobox_state, width=30, font=utils.FONT_NORMAL)
    report_class_combobox.grid(row=0, column=1, columnspan=2, padx=5, pady=8, sticky=tk.EW)

    # 2. Chọn Khoảng Thời gian
    ttk.Label(criteria_frame, text="Từ ngày:", font=utils.FONT_NORMAL).grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
    # Đặt ngày bắt đầu mặc định là ngày đầu tiên của tháng hiện tại
    today = datetime.now()
    default_start_date = today.replace(day=1)
    if TKCALENDAR_AVAILABLE:
        start_date_entry = DateEntry(criteria_frame, width=18, background=utils.COLOR_PRIMARY, 
                                     foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', 
                                     locale='vi_VN', firstweekday='monday', date=default_start_date,
                                     font=utils.FONT_NORMAL, style='DateEntryStyle.TEntry')
    else:
        start_date_entry = ttk.Entry(criteria_frame, width=20, font=utils.FONT_NORMAL)
        start_date_entry.insert(0, default_start_date.strftime('%Y-%m-%d'))
    start_date_entry.grid(row=1, column=1, padx=5, pady=8, sticky=tk.EW)

    ttk.Label(criteria_frame, text="Đến ngày:", font=utils.FONT_NORMAL).grid(row=2, column=0, padx=5, pady=8, sticky=tk.W)
    default_end_date = today # Mặc định là ngày hiện tại
    if TKCALENDAR_AVAILABLE:
        end_date_entry = DateEntry(criteria_frame, width=18, background=utils.COLOR_PRIMARY, 
                                   foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', 
                                   locale='vi_VN', firstweekday='monday', date=default_end_date,
                                   font=utils.FONT_NORMAL, style='DateEntryStyle.TEntry')
    else:
        end_date_entry = ttk.Entry(criteria_frame, width=20, font=utils.FONT_NORMAL)
        end_date_entry.insert(0, default_end_date.strftime('%Y-%m-%d'))
    end_date_entry.grid(row=2, column=1, padx=5, pady=8, sticky=tk.EW)
    
    criteria_frame.columnconfigure(1, weight=1)

    # 3. Chọn Loại Ngày (Ngữ cảnh)
    ttk.Label(criteria_frame, text="Ngữ cảnh:", font=utils.FONT_NORMAL).grid(row=3, column=0, padx=5, pady=8, sticky=tk.W)
    report_context_var = tk.StringVar(value="Tất cả") # Mặc định lấy tất cả ngữ cảnh
    # Lấy các ngữ cảnh đã có trong dữ liệu điểm danh + "Tất cả"
    all_records_for_contexts = utils.load_attendance_data() # Tải lại để lấy contexts
    unique_contexts = set(r.get('context') for r in all_records_for_contexts if r.get('context'))
    context_options = ["Tất cả"] + sorted(list(unique_contexts)) # Sắp xếp contexts
    
    report_context_combobox = ttk.Combobox(criteria_frame, textvariable=report_context_var, values=context_options, state="readonly", width=30, font=utils.FONT_NORMAL)
    report_context_combobox.grid(row=3, column=1, columnspan=2, padx=5, pady=8, sticky=tk.EW)

    button_frame = ttk.Frame(report_win)
    button_frame.pack(pady=(15, 10), padx=10, fill=tk.X, side=tk.BOTTOM)

    # Load icon cho nút Xuất
    export_icon = main_app_instance._load_icon("excel.png") if hasattr(main_app_instance, '_load_icon') else None

    export_button = ttk.Button(button_frame, text=" Xuất Excel", style="Accent.TButton", width=15,
                               image=export_icon, compound=tk.LEFT,
                               command=lambda: generate_and_export_report(
                                   main_app_instance,
                                   report_selected_class_var.get(),
                                   start_date_entry.get_date().strftime('%Y-%m-%d') if TKCALENDAR_AVAILABLE and isinstance(start_date_entry, DateEntry) else start_date_entry.get(),
                                   end_date_entry.get_date().strftime('%Y-%m-%d') if TKCALENDAR_AVAILABLE and isinstance(end_date_entry, DateEntry) else end_date_entry.get(),
                                   report_context_var.get(),
                                   report_win
                               ))
    export_button.pack(side=tk.RIGHT, padx=(5,0))
    close_button = ttk.Button(button_frame, text="Đóng", width=10, command=report_win.destroy)
    close_button.pack(side=tk.RIGHT)
    
    report_class_combobox.focus_set()

# ----- THAY THẾ TOÀN BỘ HÀM NÀY -----
def generate_and_export_report(main_app_instance, selected_class_display, start_date_str, end_date_str, selected_context, parent_window_for_messages):
    """Tạo báo cáo điểm danh chi tiết và tổng hợp, xuất ra file Excel với định dạng."""
    print(f"\n--- Xuất Báo Cáo Điểm Danh ---")
    print(f"  Lựa chọn Lớp: {selected_class_display}")
    print(f"  Từ ngày: {start_date_str}, Đến ngày: {end_date_str}")
    print(f"  Ngữ cảnh: {selected_context}")

    # --- 1. Validate Inputs ---
    try:
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date() # Chỉ lấy phần ngày
        end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if start_date_obj > end_date_obj:
            messagebox.showerror("Lỗi ngày", "Ngày bắt đầu không thể lớn hơn ngày kết thúc.", parent=parent_window_for_messages); return
    except ValueError:
        messagebox.showerror("Lỗi định dạng ngày", "Định dạng ngày không hợp lệ (YYYY-MM-DD).", parent=parent_window_for_messages); return

    # --- 2. Lấy Dữ liệu ---
    student_data_df = main_app_instance.student_data
    all_attendance_records = utils.load_attendance_data() # Tải lại dữ liệu mới nhất

    if student_data_df is None:
        messagebox.showerror("Lỗi Dữ liệu", "Không thể tải dữ liệu học sinh.", parent=parent_window_for_messages); return

    # --- 3. Lọc Danh sách Học sinh theo Lớp đã chọn ---
    students_df_filtered = pd.DataFrame()
    is_all_classes = (selected_class_display == "Tất cả các lớp")
    
    # Đảm bảo DataFrame có cột SBD là index hoặc cột thường
    if 'SBD' not in student_data_df.columns and student_data_df.index.name != 'SBD':
        messagebox.showerror("Lỗi Dữ liệu", "Dữ liệu học sinh thiếu cột 'SBD'.", parent=parent_window_for_messages); return
    
    df_temp = student_data_df.reset_index() if student_data_df.index.name == 'SBD' else student_data_df.copy()
    df_temp['SBD'] = df_temp['SBD'].astype(str) # Đảm bảo SBD là string

    if is_all_classes:
        students_df_filtered = df_temp[['SBD', 'Họ và tên', 'Lớp']].copy()
    elif 'Lớp' in df_temp.columns:
        students_df_filtered = df_temp[df_temp['Lớp'] == selected_class_display][['SBD', 'Họ và tên', 'Lớp']].copy()
    else: # Chọn lớp cụ thể nhưng file không có cột Lớp
         messagebox.showwarning("Thiếu thông tin", "Dữ liệu không có cột 'Lớp'. Báo cáo sẽ bao gồm toàn bộ học sinh.", parent=parent_window_for_messages)
         students_df_filtered = df_temp[['SBD', 'Họ và tên']].copy()
         students_df_filtered['Lớp'] = "N/A" # Thêm cột lớp tạm

    if students_df_filtered.empty:
        messagebox.showinfo("Thông báo", "Không có học sinh nào thuộc phạm vi đã chọn.", parent=parent_window_for_messages); return

    # Sắp xếp danh sách học sinh theo lớp rồi đến SBD (nếu có lớp)
    if 'Lớp' in students_df_filtered.columns:
         # Cố gắng sắp xếp SBD theo số nếu có thể
         try: students_df_filtered['SBD_int'] = pd.to_numeric(students_df_filtered['SBD'], errors='coerce')
         except: students_df_filtered['SBD_int'] = float('inf') # Xử lý lỗi nếu không chuyển được
         students_df_filtered.sort_values(by=['Lớp', 'SBD_int', 'SBD'], inplace=True, na_position='last')
         students_df_filtered.drop(columns=['SBD_int'], inplace=True, errors='ignore')
    else: # Sắp xếp theo SBD nếu không có lớp
         try: students_df_filtered['SBD_int'] = pd.to_numeric(students_df_filtered['SBD'], errors='coerce')
         except: students_df_filtered['SBD_int'] = float('inf')
         students_df_filtered.sort_values(by=['SBD_int', 'SBD'], inplace=True, na_position='last')
         students_df_filtered.drop(columns=['SBD_int'], inplace=True, errors='ignore')

    list_sbd_in_report = students_df_filtered['SBD'].tolist() # Danh sách SBD cần báo cáo

    # --- 4. Lọc Bản ghi Điểm danh theo Ngày và Ngữ cảnh ---
    filtered_attendance_records = []
    unique_attendance_dates = set() # Set các ngày có điểm danh trong khoảng và ngữ cảnh
    
    # Xác định ngữ cảnh cần lọc
    context_to_filter = selected_context if selected_context != "Tất cả" else None

    for record in all_attendance_records:
        try: record_date_obj = datetime.strptime(record.get('date', ''), '%Y-%m-%d').date()
        except (ValueError, TypeError): continue

        # Lọc theo ngày
        if not (start_date_obj <= record_date_obj <= end_date_obj): continue

        # Lọc theo ngữ cảnh
        if context_to_filter and record.get('context') != context_to_filter: continue

        # Chỉ thêm vào nếu SBD thuộc danh sách cần báo cáo
        record_sbd = str(record.get('sbd',''))
        if record_sbd in list_sbd_in_report:
             filtered_attendance_records.append(record)
             unique_attendance_dates.add(record.get('date')) # Thêm ngày có điểm danh vào set

    # Sắp xếp các ngày có điểm danh
    sorted_unique_dates = sorted(list(unique_attendance_dates))
    total_sessions = len(sorted_unique_dates) # Tổng số buổi học/điểm danh thực tế
    print(f"  -> Số buổi có hoạt động điểm danh trong khoảng: {total_sessions}")

    # --- 5. Tính toán Dữ liệu Tổng hợp ---
    summary_data = []
    attendance_by_sbd_date = {} # Dict dạng {sbd: {date: True/False}}
    for record in filtered_attendance_records:
        sbd = str(record.get('sbd'))
        date_str = record.get('date')
        if sbd not in attendance_by_sbd_date: attendance_by_sbd_date[sbd] = {}
        attendance_by_sbd_date[sbd][date_str] = True # Đánh dấu có mặt

    for index, student_row in students_df_filtered.iterrows():
        sbd = str(student_row['SBD'])
        present_count = 0
        # Đếm số ngày có mặt trong những ngày CÓ ĐIỂM DANH
        for date_str_check in sorted_unique_dates:
            if attendance_by_sbd_date.get(sbd, {}).get(date_str_check, False):
                present_count += 1
        
        absent_count = total_sessions - present_count # Vắng = Tổng buổi - Có mặt
        attendance_rate = (present_count / total_sessions * 100) if total_sessions > 0 else 0

        summary_data.append({
            'STT': index + 1,
            'SBD': sbd,
            'Họ và tên': student_row['Họ và tên'],
            'Lớp': student_row.get('Lớp', 'N/A'),
            'Số buổi có mặt': present_count,
            'Số buổi vắng': absent_count,
            'Tổng số buổi': total_sessions,
            'Tỷ lệ chuyên cần (%)': round(attendance_rate, 2) # Làm tròn 2 chữ số
        })

    summary_df = pd.DataFrame(summary_data)

    # --- 6. Tạo DataFrame Chi tiết (Nếu cần) ---
    details_data = []
    # Sắp xếp filtered_attendance theo thời gian để sheet chi tiết dễ nhìn hơn
    filtered_attendance_records.sort(key=lambda r: r.get('timestamp', ''))
    for i, record in enumerate(filtered_attendance_records):
        sbd = str(record.get('sbd'))
        student_info = students_df_filtered[students_df_filtered['SBD'] == sbd]
        ho_ten = student_info['Họ và tên'].iloc[0] if not student_info.empty else "N/A"
        lop_detail = student_info['Lớp'].iloc[0] if not student_info.empty and 'Lớp' in student_info.columns else record.get('class', "N/A")
        details_data.append({
            'STT': i + 1, 'SBD': sbd, 'Họ và tên': ho_ten, 'Lớp': lop_detail,
            'Thời gian': record.get('timestamp'), 'Loại': "TC" if record.get('type') == 'manual' else "Scan",
            'Ngữ cảnh': record.get('context'), 'Ngày': record.get('date')
        })
    details_df = pd.DataFrame(details_data)

    # --- 7. Xuất ra file Excel với định dạng ---
    if summary_df.empty and details_df.empty:
        messagebox.showinfo("Không có dữ liệu", "Không có dữ liệu điểm danh phù hợp để xuất báo cáo.", parent=parent_window_for_messages); return

    safe_class_name = selected_class_display.replace(' ', '_').replace('/', '-')
    default_filename = f"BaoCaoDiemDanh_{safe_class_name}_{start_date_str}_den_{end_date_str}.xlsx"
    filepath = filedialog.asksaveasfilename(
        title="Lưu Báo cáo Điểm danh", initialfile=default_filename, defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")], parent=parent_window_for_messages)
    if not filepath: return

    try:
        # Sử dụng engine='xlsxwriter'
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            
            # --- Ghi Sheet Tổng hợp ---
            summary_df.to_excel(writer, sheet_name='TongHopChuyenCan', index=False, startrow=1) # Bắt đầu từ dòng 1 để chừa chỗ cho tiêu đề
            workbook = writer.book
            worksheet_summary = writer.sheets['TongHopChuyenCan']

            # Tạo các định dạng
            header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
            title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
            cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'}) # Định dạng chung cho các ô
            percent_format = workbook.add_format({'num_format': '0.00"%"', 'border': 1, 'valign': 'vcenter'}) # Định dạng phần trăm
            center_format = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter'}) # Căn giữa

            # Gộp ô và ghi Tiêu đề cho Sheet Tổng hợp
            merge_range_end_col = len(summary_df.columns) - 1
            worksheet_summary.merge_range(0, 0, 0, merge_range_end_col, 
                                        f"BÁO CÁO CHUYÊN CẦN - {'TOÀN TRƯỜNG' if is_all_classes else f'LỚP {selected_class_display}'} "
                                        f"({selected_context.upper()})", 
                                        title_format)
            worksheet_summary.set_row(0, 30) # Tăng chiều cao dòng tiêu đề

            # Ghi header với định dạng
            for col_num, value in enumerate(summary_df.columns.values):
                worksheet_summary.write(1, col_num, value, header_format) # Header ở dòng 1

            # Áp dụng định dạng cho các cột dữ liệu
            worksheet_summary.set_column('A:A', 5, cell_format) # STT
            worksheet_summary.set_column('B:B', 12, cell_format) # SBD
            worksheet_summary.set_column('C:C', 25, cell_format) # Ho ten
            worksheet_summary.set_column('D:D', 10, cell_format) # Lop
            worksheet_summary.set_column('E:G', 14, center_format) # Co mat, Vang, Tong
            worksheet_summary.set_column('H:H', 18, percent_format) # Ty le

            # Tự động điều chỉnh độ rộng cột (ước lượng)
            # for i, col in enumerate(summary_df.columns):
            #     column_len = max(summary_df[col].astype(str).map(len).max(), len(col)) + 2
            #     worksheet_summary.set_column(i, i, column_len)


            # --- Ghi Sheet Chi tiết (nếu có) ---
            if not details_df.empty:
                details_df.to_excel(writer, sheet_name='ChiTietDiemDanh', index=False, startrow=1)
                worksheet_details = writer.sheets['ChiTietDiemDanh']
                
                # Ghi tiêu đề cho Sheet Chi tiết
                merge_range_end_col_details = len(details_df.columns) - 1
                worksheet_details.merge_range(0, 0, 0, merge_range_end_col_details,
                                            f"CHI TIẾT ĐIỂM DANH - {'TOÀN TRƯỜNG' if is_all_classes else f'LỚP {selected_class_display}'} "
                                            f"({selected_context.upper()})",
                                            title_format)
                worksheet_details.set_row(0, 30)

                # Ghi header chi tiết
                for col_num, value in enumerate(details_df.columns.values):
                    worksheet_details.write(1, col_num, value, header_format)

                # Định dạng và tự động điều chỉnh độ rộng cột chi tiết
                worksheet_details.set_column('A:A', 5) # STT
                worksheet_details.set_column('B:B', 12) # SBD
                worksheet_details.set_column('C:C', 25) # Ho ten
                worksheet_details.set_column('D:D', 10) # Lop
                worksheet_details.set_column('E:E', 18) # Thoi gian
                worksheet_details.set_column('F:F', 8)  # Loai
                worksheet_details.set_column('G:G', 10) # Ngu canh
                worksheet_details.set_column('H:H', 12) # Ngay

                # Áp dụng định dạng border cho các ô dữ liệu chi tiết
                max_row_detail = len(details_df) + 1 # Số hàng dữ liệu + 1 hàng header
                worksheet_details.conditional_format(2, 0, max_row_detail, merge_range_end_col_details, {'type': 'no_blanks', 'format': cell_format})
                worksheet_details.conditional_format(2, 0, max_row_detail, merge_range_end_col_details, {'type': 'blanks',    'format': cell_format})


        messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công!\n{filepath}", parent=parent_window_for_messages)
        
        # Tùy chọn: Mở file sau khi xuất
        try:
            if sys.platform == "win32": os.startfile(filepath)
            elif sys.platform == "darwin": os.system(f'open "{filepath}"')
            else: os.system(f'xdg-open "{filepath}"')
        except Exception as e_open:
            print(f"Không thể tự động mở file Excel: {e_open}")

    except PermissionError:
        messagebox.showerror("Lỗi Quyền Ghi", f"Không có quyền ghi file tại:\n{filepath}\nVui lòng chọn vị trí khác hoặc đóng file nếu đang mở.", parent=parent_window_for_messages)
    except ImportError:
         messagebox.showerror("Thiếu thư viện", "Vui lòng cài đặt 'xlsxwriter' để định dạng file Excel:\n pip install xlsxwriter", parent=parent_window_for_messages)
    except Exception as e:
        messagebox.showerror("Lỗi Xuất Excel", f"Không thể tạo file Excel:\n{e}", parent=parent_window_for_messages)
        import traceback
        traceback.print_exc() # In chi tiết lỗi ra console

# --- HẾT FILE ---