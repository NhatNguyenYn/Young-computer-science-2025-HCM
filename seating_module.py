import tkinter as tk
# Thay thế các import tk bằng ttk khi có thể
from tkinter import ttk, messagebox, Toplevel, Frame, Label, Entry, Button, Checkbutton, BooleanVar, Scrollbar, filedialog, simpledialog
import pandas as pd
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os
import json # <<<< THÊM DÒNG NÀY
import utils # Import utils đã cập nhật

EMPTY_SEAT_MARKER = "--- Trống ---"
UNUSABLE_SEAT_MARKER = "[Không SD]"
ARIAL_FONT_PATH = "Arial.ttf" # Nên đặt trong utils hoặc là một hằng số có thể cấu hình
HIGHLIGHT_COLOR = "yellow" # Có thể đưa vào utils.py
UNUSABLE_BG_COLOR = "salmon" # Có thể đưa vào utils.py

def register_arial_font():
    font_path_to_check = ARIAL_FONT_PATH
    # Check if running as a script or bundled by PyInstaller
    if hasattr(sys, '_MEIPASS'):
        # In PyInstaller bundle, font might be in the root temp directory
        font_path_to_check = os.path.join(sys._MEIPASS, os.path.basename(ARIAL_FONT_PATH))
        if not os.path.exists(font_path_to_check):
             # Fallback to original relative path just in case
             font_path_to_check = os.path.join(os.path.dirname(sys.executable), ARIAL_FONT_PATH)

    if os.path.exists(font_path_to_check):
        try:
            pdfmetrics.registerFont(TTFont("Arial", font_path_to_check))
            print(f"Registered font: Arial from {font_path_to_check}")
            return "Arial"
        except Exception as e:
            print(f"Warn: Arial font register failed from {font_path_to_check}: {e}")
            return "Helvetica" # Fallback font
    else:
        print(f"Warn: Arial font file not found at expected path: {font_path_to_check}. Using Helvetica.")
        return "Helvetica" # Fallback font

# Ensure sys is imported if not already
import sys
REGISTERED_FONT_NAME = register_arial_font()

# <<<< HÀM MỚI ĐỂ TẢI TRẠNG THÁI GHẾ KHÔNG SỬ DỤNG >>>>
def load_unusable_seats(config_key):
    try:
        if os.path.exists(utils.UNUSABLE_SEATS_FILE):
            with open(utils.UNUSABLE_SEATS_FILE, 'r', encoding='utf-8') as f:
                # Check if file is empty before attempting to load JSON
                if os.path.getsize(utils.UNUSABLE_SEATS_FILE) > 0:
                     data = json.load(f)
                     # Convert list of lists to set of tuples
                     return set(tuple(coord) for coord in data.get(config_key, []))
                else:
                     print(f"Warning: {utils.UNUSABLE_SEATS_FILE} is empty. No unusable seats loaded for {config_key}.")
                     return set()

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading unusable seats for {config_key}: {e}")
    except Exception as e_generic:
         print(f"Unexpected error loading unusable seats for {config_key}: {e_generic}")
    return set()

# <<<< HÀM MỚI ĐỂ LƯU TRẠNG THÁI GHẾ KHÔNG SỬ DỤNG >>>>
def save_unusable_seats(config_key, unusable_coords_set):
    all_configs = {}
    try:
        if os.path.exists(utils.UNUSABLE_SEATS_FILE):
            # Check if file is empty before attempting to load JSON
            if os.path.getsize(utils.UNUSABLE_SEATS_FILE) > 0:
                with open(utils.UNUSABLE_SEATS_FILE, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
            else:
                 print(f"Warning: {utils.UNUSABLE_SEATS_FILE} was empty. Initializing new config.")
    except (json.JSONDecodeError, IOError) as e: # If file is corrupt or unreadable, start fresh
        print(f"Warning: Error reading {utils.UNUSABLE_SEATS_FILE} ({e}). Initializing new config.")
        pass # all_configs will remain empty or as loaded (if partially loaded before error)
    except Exception as e_generic:
         print(f"Warning: Unexpected error reading {utils.UNUSABLE_SEATS_FILE} ({e_generic}). Initializing new config.")


    # Convert set of tuples to list of lists for JSON
    all_configs[config_key] = [list(coord) for coord in unusable_coords_set]

    try:
        with open(utils.UNUSABLE_SEATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_configs, f, ensure_ascii=False, indent=2)
    except IOError as e:
        messagebox.showerror("Lỗi Lưu", f"Không thể lưu trạng thái ghế không sử dụng:\n{e}")
        print(f"Error saving unusable seats: {e}")


def create_seating_chart_logic(student_sbd_list, rows, cols, sort_by_sbd=False, unusable_seats=None):
    if unusable_seats is None: unusable_seats = set()
    available_seats = rows * cols - len(unusable_seats)
    valid_students = [str(sbd).strip() for sbd in student_sbd_list if sbd and str(sbd).strip()]
    chart = [[EMPTY_SEAT_MARKER for _ in range(cols)] for _ in range(rows)]
    for r_u, c_u in unusable_seats:
        if 0 <= r_u < rows and 0 <= c_u < cols: chart[r_u][c_u] = UNUSABLE_SEAT_MARKER
    if not valid_students: return chart, []
    if sort_by_sbd:
        try: valid_students.sort(key=lambda x: int(x) if x.isdigit() else x)
        except ValueError: valid_students.sort()
    student_index = 0; seated_count = 0
    for r in range(rows):
        for c in range(cols):
            if chart[r][c] == EMPTY_SEAT_MARKER and student_index < len(valid_students): # Only place if seat is marked EMPTY
                chart[r][c] = valid_students[student_index]
                student_index += 1; seated_count += 1
    unseated_students = valid_students[student_index:]
    return chart, unseated_students

def show_arrangement_ui(parent_window, attended_sbd_list_for_class, df_students_global, selected_class_name, context, date_str):
    arrange_window = Toplevel(parent_window)
    arrange_window.title(f"Xếp Chỗ Thi - Lớp {selected_class_name} ({context}) - {date_str}")
    arrange_window.geometry("1050x850") # Tăng kích thước cửa sổ
    arrange_window.transient(parent_window); arrange_window.grab_set()
    arrange_window.configure(bg=utils.COLOR_BG_FRAME)

    main_frame = ttk.Frame(arrange_window, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    current_list_for_arrangement = list(attended_sbd_list_for_class)
    current_source_description = f"DS Điểm danh ({context})"

    config_key = f"{selected_class_name}_{context}_{date_str}"
    unusable_seats_coords = load_unusable_seats(config_key)


    # --- Frame Thông tin PDF ---
    pdf_info_group = ttk.LabelFrame(main_frame, text="Thông tin File PDF (Tùy chọn)")
    pdf_info_group.pack(fill=tk.X, pady=5)
    ttk.Label(pdf_info_group, text="Kỳ thi:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3); exam_name_entry = ttk.Entry(pdf_info_group, width=30); exam_name_entry.grid(row=0, column=1, padx=5, pady=3, sticky=tk.EW)
    ttk.Label(pdf_info_group, text="Địa điểm:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=3); location_entry = ttk.Entry(pdf_info_group, width=30); location_entry.grid(row=0, column=3, padx=5, pady=3, sticky=tk.EW)
    ttk.Label(pdf_info_group, text="Phòng thi:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=3); room_entry = ttk.Entry(pdf_info_group, width=25); room_entry.grid(row=0, column=5, padx=5, pady=3, sticky=tk.EW)
    
    ttk.Label(pdf_info_group, text="Giám thị:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3); supervisor_entry = ttk.Entry(pdf_info_group, width=30); supervisor_entry.grid(row=1, column=1, padx=5, pady=3, sticky=tk.EW)
    pdf_info_group.columnconfigure(1, weight=1)
    pdf_info_group.columnconfigure(3, weight=1)
    pdf_info_group.columnconfigure(5, weight=1) 


    # --- Frame Điều khiển chính ---
    top_controls_group = ttk.LabelFrame(main_frame, text="Cấu hình Sơ đồ")
    top_controls_group.pack(pady=5, fill=tk.X)
    data_source_label = ttk.Label(top_controls_group, text=f"Lớp: {selected_class_name} | Nguồn: {current_source_description} ({len(current_list_for_arrangement)} HS)", font=utils.FONT_NORMAL, wraplength=700)
    data_source_label.grid(row=0, column=0, columnspan=6, pady=(5,8), padx=5, sticky=tk.W)

    ttk.Label(top_controls_group, text="Hàng:").grid(row=1, column=0, padx=(5,0), pady=5, sticky=tk.W); row_entry = ttk.Entry(top_controls_group, width=6); row_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W); row_entry.insert(0, "5")
    ttk.Label(top_controls_group, text="Cột:").grid(row=1, column=2, padx=(10,0), pady=5, sticky=tk.W); col_entry = ttk.Entry(top_controls_group, width=6); col_entry.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W); col_entry.insert(0, "6")
    sort_var = BooleanVar(value=True); sort_check = ttk.Checkbutton(top_controls_group, text="Sắp xếp SBD", variable=sort_var); sort_check.grid(row=1, column=4, padx=10, pady=5, sticky=tk.W)

    # --- Khung tìm kiếm và chú thích ---
    search_ui_group = ttk.LabelFrame(main_frame, text="Tìm kiếm & Tương tác")
    search_ui_group.pack(pady=5, fill=tk.X)
    ttk.Label(search_ui_group, text="Tìm SBD/Tên:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W); search_entry = ttk.Entry(search_ui_group, width=30); search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
    search_button = ttk.Button(search_ui_group, text="Tìm", width=10, command=lambda: search_and_highlight()); search_button.grid(row=0, column=2, padx=5, pady=5)
    clear_highlight_button = ttk.Button(search_ui_group, text="Xóa Highlight", width=14, command=lambda: clear_highlight()); clear_highlight_button.grid(row=0, column=3, padx=5, pady=5)
    ttk.Label(search_ui_group, text="(Chuột phải vào ô để đánh dấu Không sử dụng/Sử dụng)", font=utils.FONT_SMALL, foreground=utils.COLOR_TEXT_LIGHT).grid(row=0, column=4, padx=10, pady=5, sticky=tk.W)
    search_ui_group.columnconfigure(1, weight=1) 
    search_ui_group.columnconfigure(4, weight=1) 


    # --- Frame hiển thị kết quả xếp chỗ (Canvas vẫn là tk) ---
    result_group = ttk.LabelFrame(main_frame, text="Sơ đồ Chỗ ngồi")
    result_group.pack(pady=10, fill="both", expand=True)

    canvas_result = tk.Canvas(result_group, bg=utils.COLOR_BG_FRAME, highlightthickness=0) # Canvas gốc
    scrollbar_y = ttk.Scrollbar(result_group, orient="vertical", command=canvas_result.yview)
    scrollbar_x = ttk.Scrollbar(result_group, orient="horizontal", command=canvas_result.xview)
    result_frame_inner = Frame(canvas_result, bg=utils.COLOR_BG_FRAME) 

    result_frame_inner.bind("<Configure>", lambda e: canvas_result.configure(scrollregion=canvas_result.bbox("all")))
    canvas_result.create_window((0, 0), window=result_frame_inner, anchor="nw")
    canvas_result.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y) 
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X) 
    canvas_result.pack(side=tk.LEFT, fill="both", expand=True) 


    current_seating_chart_matrix = []; seat_labels_dict = {}; current_rows, current_cols = 0, 0

    def toggle_seat_usability(event, r, c):
        nonlocal unusable_seats_coords
        coord = (r, c)

        if current_seating_chart_matrix and 0 <= r < len(current_seating_chart_matrix) and \
           0 <= c < len(current_seating_chart_matrix[0]):
            seat_content = current_seating_chart_matrix[r][c]
            if seat_content not in [EMPTY_SEAT_MARKER, UNUSABLE_SEAT_MARKER]:
                messagebox.showwarning("Ghế có người", "Không thể thay đổi trạng thái ghế đang có HS.", parent=arrange_window)
                return

        if coord in unusable_seats_coords:
            unusable_seats_coords.remove(coord)
            save_unusable_seats(config_key, unusable_seats_coords) 
            messagebox.showinfo("Cập nhật", f"Ghế ({r+1},{c+1}) đã được đánh dấu CÓ THỂ SỬ DỤNG.\nSơ đồ đã cập nhật.", parent=arrange_window)
        else:
            unusable_seats_coords.add(coord)
            save_unusable_seats(config_key, unusable_seats_coords) 
            messagebox.showinfo("Cập nhật", f"Ghế ({r+1},{c+1}) đã được đánh dấu KHÔNG SỬ DỤNG.\nSơ đồ đã cập nhật.", parent=arrange_window)
        
        generate_chart_action() 


    def display_seating_chart_on_gui(chart_matrix, df_students_ref, current_class_ref):
        nonlocal current_seating_chart_matrix, current_rows, current_cols, seat_labels_dict
        current_seating_chart_matrix = chart_matrix; seat_labels_dict.clear()
        current_rows, current_cols = (len(chart_matrix), len(chart_matrix[0])) if chart_matrix and chart_matrix[0] else (0,0)

        for widget in result_frame_inner.winfo_children(): widget.destroy() 
        if current_rows == 0 or current_cols == 0: ttk.Label(result_frame_inner, text="Chưa có sơ đồ.").pack(); return

        for r, row_data in enumerate(chart_matrix):
            for c, seat_content in enumerate(row_data):
                bg_color, fg_color = utils.COLOR_BG_FRAME, utils.COLOR_TEXT_NORMAL
                coord = (r, c); display_text = ""

                if coord in unusable_seats_coords: 
                     bg_color, fg_color, display_text = UNUSABLE_BG_COLOR, "black", UNUSABLE_SEAT_MARKER
                elif seat_content == EMPTY_SEAT_MARKER:
                    bg_color, fg_color, display_text = utils.COLOR_LISTBOX_EVEN_ROW, utils.COLOR_TEXT_LIGHT, "Trống"
                else: 
                    sbd = str(seat_content).strip()
                    student_name, student_actual_class = utils.get_student_info(sbd, df_students_ref)
                    student_name = student_name or "(Không có tên)"
                    actual_class_str = str(student_actual_class) if pd.notna(student_actual_class) else ""

                    class_info = ""
                    if actual_class_str and current_class_ref and current_class_ref != "ToanTruong" and actual_class_str.strip() != str(current_class_ref).strip():
                        class_info = f"\n(Lớp: {actual_class_str})" 
                    display_text = f"{sbd}\n{student_name}{class_info}"

                label = Label(result_frame_inner, text=display_text, borderwidth=1, relief="solid", width=18, height=3,
                              wraplength=130, justify=tk.CENTER, background=bg_color, foreground=fg_color, font=utils.FONT_SMALL)
                label.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
                seat_labels_dict[coord] = label
                label.bind("<Button-3>", lambda event, row=r, col=c: toggle_seat_usability(event, row, col))

        for r_idx in range(current_rows): result_frame_inner.grid_rowconfigure(r_idx, weight=1)
        for c_idx in range(current_cols): result_frame_inner.grid_columnconfigure(c_idx, weight=1)
        result_frame_inner.update_idletasks(); canvas_result.configure(scrollregion=canvas_result.bbox("all"))

    def generate_chart_action():
        try:
            rows = int(row_entry.get()); cols = int(col_entry.get())
            if rows <= 0 or cols <= 0: raise ValueError("Hàng/cột phải dương.")
        except ValueError as e: messagebox.showwarning("Lỗi", f"Giá trị Hàng/Cột không hợp lệ: {e}", parent=arrange_window); return

        data_source_label.config(text=f"Lớp: {selected_class_name} | Nguồn: {current_source_description} ({len(current_list_for_arrangement)} HS)")
        seating_plan, unseated = create_seating_chart_logic(current_list_for_arrangement, rows, cols, sort_var.get(), unusable_seats_coords)
        display_seating_chart_on_gui(seating_plan, df_students_global, selected_class_name)

        if unseated:
            unseated_info = [f"{sbd} ({utils.get_student_info(sbd, df_students_global)[0] or 'N/A'})" for sbd in unseated]
            available_seats_count = rows * cols - len(unusable_seats_coords)
            msg = f"Số chỗ khả dụng: {available_seats_count}.\nSố HS cần xếp: {len(current_list_for_arrangement)}.\n\n"
            msg += f"{len(unseated)} HS không có chỗ:\n{', '.join(unseated_info[:10])}"
            if len(unseated_info) > 10: msg += "..."
            messagebox.showwarning("Không đủ chỗ", msg, parent=arrange_window)
        clear_highlight()

    def import_from_excel_action():
        nonlocal current_list_for_arrangement, current_source_description, unusable_seats_coords
        file_path=filedialog.askopenfilename(title="Chọn Excel SBD", filetypes=[("Excel files","*.xlsx;*.xls")], parent=arrange_window)
        if not file_path: return
        try:
            df = pd.read_excel(file_path, header=0, dtype=str)
            if df.empty: raise ValueError("File rỗng hoặc không có dữ liệu.")
            col_sbd = next((c for c in df.columns if str(c).strip().upper()=='SBD'), df.columns[0] if len(df.columns)>0 else None)
            if col_sbd is None: raise ValueError("Không tìm thấy cột SBD trong file Excel.")
            lst = [s for s in df[col_sbd].dropna().astype(str).str.strip().tolist() if s]
            if not lst: raise ValueError("Không có SBD hợp lệ trong file.")

            current_list_for_arrangement=lst
            current_source_description=f"File Excel: {os.path.basename(file_path)}"
            messagebox.showinfo("Nhập thành công", f"Đã nhập {len(lst)} SBD từ file.\nNhấn 'Xếp Chỗ' để cập nhật sơ đồ.", parent=arrange_window)
            unusable_seats_coords.clear() 
            save_unusable_seats(config_key, unusable_seats_coords) 
            generate_chart_action()
        except Exception as e: messagebox.showerror("Lỗi Đọc File", f"Lỗi khi đọc file Excel:\n{e}", parent=arrange_window)

    def use_original_attendance_list_action():
        nonlocal current_list_for_arrangement, current_source_description, unusable_seats_coords
        current_list_for_arrangement = list(attended_sbd_list_for_class)
        current_source_description = f"DS Điểm danh ({context})"
        messagebox.showinfo("Khôi phục Danh sách", f"Đã khôi phục danh sách gốc từ điểm danh ({len(current_list_for_arrangement)} HS).\nNhấn 'Xếp Chỗ' để cập nhật.", parent=arrange_window)
        unusable_seats_coords.clear()
        save_unusable_seats(config_key, unusable_seats_coords) 
        generate_chart_action()

    def clear_highlight():
        if not current_seating_chart_matrix: return
        for r in range(current_rows):
            for c in range(current_cols):
                 coord = (r,c)
                 if coord in seat_labels_dict:
                     label = seat_labels_dict[coord]
                     if coord in unusable_seats_coords: label.config(background=UNUSABLE_BG_COLOR)
                     elif current_seating_chart_matrix[r][c] == EMPTY_SEAT_MARKER: label.config(background=utils.COLOR_LISTBOX_EVEN_ROW)
                     else: label.config(background=utils.COLOR_BG_FRAME) 

    def search_and_highlight():
        term = search_entry.get().lower().strip(); clear_highlight(); found = False
        if not term or not current_seating_chart_matrix: return
        for r_idx, r_data in enumerate(current_seating_chart_matrix):
            for c_idx, sbd_in_seat in enumerate(r_data):
                coord = (r_idx, c_idx)
                if sbd_in_seat != EMPTY_SEAT_MARKER and sbd_in_seat != UNUSABLE_SEAT_MARKER and coord not in unusable_seats_coords:
                    name, _ = utils.get_student_info(sbd_in_seat, df_students_global)
                    if term in str(sbd_in_seat).lower() or (name and term in name.lower()):
                        if coord in seat_labels_dict: seat_labels_dict[coord].config(background=HIGHLIGHT_COLOR); found = True
        if not found: messagebox.showinfo("Thông báo", f"Không tìm thấy '{search_entry.get()}'.", parent=arrange_window)

    search_entry.bind("<Return>", lambda event: search_and_highlight())

    def export_to_pdf_action():
        if not current_seating_chart_matrix or current_rows == 0 or current_cols == 0: messagebox.showwarning("Chưa có dữ liệu", "Chưa có sơ đồ để xuất.", parent=arrange_window); return
        exam_val=exam_name_entry.get().strip(); loc_val=location_entry.get().strip(); sup_val=supervisor_entry.get().strip()
        room_val = room_entry.get().strip() 
        safe_class = "".join(c for c in selected_class_name if c.isalnum() or c in ('_', '-')).rstrip()
        safe_ctx = "".join(c for c in context if c.isalnum() or c in ('_', '-')).rstrip()
        safe_date = date_str.replace('-', '')
        fn = f"so_do_phong_thi_{safe_class}_{safe_ctx}_{safe_date}.pdf"
        fp = filedialog.asksaveasfilename(title="Lưu Sơ đồ PDF", defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialfile=fn, parent=arrange_window)
        if not fp: return
        try:
            c_pdf = canvas.Canvas(fp, pagesize=landscape(letter)); w_pdf, h_pdf = landscape(letter)
            # ---- START PDF LAYOUT ADJUSTMENTS ----
            margin_h, margin_v = 0.5*inch, 0.5*inch
            header_height = 1.25*inch # <<<< INCREASED HEADER HEIGHT FURTHER >>>>
            title_h_pdf = header_height 
            usable_w, usable_h = w_pdf - 2*margin_h, h_pdf - margin_v - header_height - margin_v 

            if current_cols <= 0 or current_rows <= 0: raise ValueError("Số cột/hàng trong sơ đồ không hợp lệ.")
            cell_w, cell_h = usable_w / current_cols, usable_h / current_rows
            grid_x0 = margin_h
            grid_y0_top = h_pdf - margin_v - header_height # Y coordinate of the TOP edge of the grid

            # --- Vẽ Header ---
            header_y_start = h_pdf - margin_v - 0.25*inch 
            c_pdf.setFont(REGISTERED_FONT_NAME, 16); c_pdf.drawCentredString(w_pdf/2, header_y_start, f"SƠ ĐỒ PHÒNG THI - LỚP {selected_class_name}")
            
            header_y_start -= 0.28*inch # <<<< INCREASED SPACING >>>>
            c_pdf.setFont(REGISTERED_FONT_NAME, 10) 

            col1_x = margin_h
            col2_x = margin_h + w_pdf * 0.35 
            col3_x = margin_h + w_pdf * 0.70 
            
            line_spacing = 0.22 * inch # <<<< INCREASED LINE SPACING >>>>

            # Line 1
            c_pdf.drawString(col1_x, header_y_start, f"Kỳ thi: {exam_val or '...................................'}")
            c_pdf.drawString(col2_x, header_y_start, f"Địa điểm: {loc_val or '...................................'}")
            header_y_start -= line_spacing

            # Line 2
            c_pdf.drawString(col1_x, header_y_start, f"Phòng thi: {room_val or '.......................'}")
            c_pdf.drawString(col2_x, header_y_start, f"Ngày thi: {date_str}")
            header_y_start -= line_spacing

            # Line 3
            c_pdf.drawString(col1_x, header_y_start, f"Giám thị: {sup_val or '...................................'}")
            # This line is now lower due to increased line_spacing and header_height

            # --- Vẽ Bảng tên cột và hàng ---
            c_pdf.setFont(REGISTERED_FONT_NAME, 9)
            # Y coordinate for drawing column names (slightly above the grid)
            col_name_y = grid_y0_top + 0.08*inch # Position relative to grid top edge
            for c_idx in range(current_cols):
                col_name = chr(ord('A') + c_idx)
                c_pdf.drawCentredString(grid_x0 + c_idx*cell_w + cell_w/2, col_name_y, col_name)
            # X coordinate for drawing row names (slightly to the left of the grid)
            row_name_x = grid_x0 - 0.15*inch
            for r_idx in range(current_rows):
                row_name_y = grid_y0_top - r_idx*cell_h - cell_h/2 + 3 
                c_pdf.drawCentredString(row_name_x, row_name_y, str(r_idx+1))

            # --- Vẽ Grid và Nội dung ---
            for r, row_list_data in enumerate(current_seating_chart_matrix):
                for c_idx_loop, content_in_cell in enumerate(row_list_data):
                    x_left, y_bottom = grid_x0 + c_idx_loop*cell_w, grid_y0_top - (r+1)*cell_h
                    c_pdf.setStrokeColorRGB(0.5,0.5,0.5); c_pdf.setLineWidth(0.5)
                    c_pdf.rect(x_left, y_bottom, cell_w, cell_h, stroke=1, fill=0)

                    text_center_x = x_left + cell_w/2
                    coord_tuple = (r, c_idx_loop)

                    if coord_tuple in unusable_seats_coords:
                         c_pdf.setLineWidth(1.5); c_pdf.setStrokeColorRGB(0.8, 0.1, 0.1) 
                         c_pdf.line(x_left + cell_w*0.1, y_bottom + cell_h*0.1, x_left + cell_w*0.9, y_bottom + cell_h*0.9)
                         c_pdf.line(x_left + cell_w*0.1, y_bottom + cell_h*0.9, x_left + cell_w*0.9, y_bottom + cell_h*0.1)
                         c_pdf.setFillColorRGB(0,0,0); c_pdf.setStrokeColorRGB(0,0,0) 
                    elif content_in_cell == EMPTY_SEAT_MARKER:
                         font_size_empty = max(6, min(8, int(cell_h*0.15))) # <<<< Slightly smaller font >>>>
                         c_pdf.setFont(REGISTERED_FONT_NAME, font_size_empty); c_pdf.setFillColorRGB(0.6,0.6,0.6)
                         c_pdf.drawCentredString(text_center_x, y_bottom + cell_h/2 - font_size_empty*0.3, "Trống")
                         c_pdf.setFillColorRGB(0,0,0) 
                    else:
                        sbd_val_pdf = str(content_in_cell).strip()
                        name_val_pdf, _ = utils.get_student_info(sbd_val_pdf, df_students_global)
                        display_name_pdf = name_val_pdf or "(Ngoài DS)"

                        # <<<< REDUCED MAX FONT SIZES AND ADJUSTED VERTICAL POSITIONING >>>>
                        font_size_sbd = max(6, min(10, int(cell_h * 0.20), int(cell_w / (len(sbd_val_pdf) * 0.6 + 1e-6))))
                        font_size_name = max(5, min(8, int(cell_h * 0.15), int(cell_w / (len(display_name_pdf) * 0.4 + 1e-6))))

                        # Adjust vertical positioning to compress text
                        text_y_sbd = y_bottom + cell_h * 0.65 - font_size_sbd * 0.3 # SBD slightly lower than before
                        text_y_name = y_bottom + cell_h * 0.35 - font_size_name * 0.3 # Name slightly higher than before

                        c_pdf.setFillColorRGB(0,0,0)
                        c_pdf.setFont(REGISTERED_FONT_NAME, font_size_sbd)
                        c_pdf.drawCentredString(text_center_x, text_y_sbd, sbd_val_pdf)
                        c_pdf.setFont(REGISTERED_FONT_NAME, font_size_name)
                        c_pdf.drawCentredString(text_center_x, text_y_name, display_name_pdf)
            # ---- END PDF LAYOUT ADJUSTMENTS ----

            c_pdf.save()
            messagebox.showinfo("Xuất thành công", f"Đã lưu sơ đồ PDF tại:\n{os.path.abspath(fp)}", parent=arrange_window)
        except PermissionError: messagebox.showerror("Lỗi Quyền Ghi", f"Không có quyền ghi file tại vị trí đã chọn:\n{fp}\nVui lòng chọn vị trí khác.", parent=arrange_window)
        except Exception as e_pdf: messagebox.showerror("Lỗi Xuất PDF", f"Đã xảy ra lỗi khi tạo file PDF:\n{e_pdf}\nFont used: {REGISTERED_FONT_NAME}", parent=arrange_window)


    # --- Nút bấm dưới cùng ---
    bottom_buttons_main = ttk.Frame(main_frame)
    bottom_buttons_main.pack(pady=(15, 5), fill=tk.X)

    btn_actions = [
        ("Dùng DS Điểm Danh Gốc", use_original_attendance_list_action, 22),
        ("Nhập DS từ Excel", import_from_excel_action, 18),
        ("Xếp Chỗ", generate_chart_action, 12, "Accent.TButton"), # Nút chính
        ("Xuất PDF", export_to_pdf_action, 12),
        ("Đóng", arrange_window.destroy, 10)
    ]

    for text, cmd, width, *style_arg in btn_actions:
        style = style_arg[0] if style_arg else "TButton"
        ttk.Button(bottom_buttons_main, text=text, command=cmd, width=width, style=style).pack(side=tk.LEFT, padx=7, ipady=4, expand=True, fill=tk.X)

    bottom_buttons_main.pack_configure(anchor=tk.CENTER) # Căn giữa frame chứa nút

    generate_chart_action() # Tự động tạo sơ đồ ban đầu
    row_entry.focus_set()
