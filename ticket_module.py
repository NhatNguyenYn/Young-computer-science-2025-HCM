import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar, Toplevel # Frame, Label, Entry, Button thay bằng ttk
import os
import json
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from datetime import datetime
import pandas as pd # Để check pd.notna

import utils
import qr_module

DEFAULT_OUTPUT_FOLDER = "GiayBaoThi_Output"
FONT_PATH = "Arial.ttf" # Nên dùng font từ utils nếu có thể, hoặc đảm bảo font này có sẵn
FONT_NAME = "ArialCustomGBT" # Đổi tên để tránh xung đột nếu Arial đã được đăng ký khác
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_TOP = 2.5 * cm; MARGIN_BOTTOM = 2.5 * cm
MARGIN_LEFT = 2.5 * cm; MARGIN_RIGHT = 2.5 * cm
LINE_SPACING_SMALL = 0.5 * cm; LINE_SPACING_NORMAL = 0.8 * cm
LINE_SPACING_LARGE = 1.1 * cm; QR_DISPLAY_SIZE = 4.0 * cm
QR_PADDING = 0.2 * cm

TEMPLATE_FIELDS_MAP = {
    "cum_thi": "Cụm thi (Mẫu chung):", "ky_thi": "Kỳ thi (Mẫu chung):",
    "ngay_thi_footer": "Địa danh, ngày tháng (Footer):"
}

try:
    if os.path.exists(FONT_PATH): pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
    else: FONT_NAME = "Helvetica" # Fallback
except Exception: FONT_NAME = "Helvetica"
FONT_NAME_BOLD = FONT_NAME + "-Bold" if FONT_NAME == "Helvetica" else FONT_NAME # ReportLab tự tìm bold cho Helvetica

def format_date_dmy(date_string):
    if not date_string or not isinstance(date_string, str) or pd.isna(date_string): return ""
    possible_formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y"] # Thêm format ISO
    date_str_cleaned = date_string.split(" ")[0] # Lấy phần ngày nếu có cả giờ
    for fmt in possible_formats:
        try: date_obj = datetime.strptime(date_str_cleaned.strip(), fmt); return date_obj.strftime("%d-%m-%Y")
        except ValueError: continue
    return date_string.strip().replace('/', '-').replace('.', '-') # Trả lại nếu không parse được

def load_ticket_template_data():
    try:
        if os.path.exists(utils.TICKET_TEMPLATE_FILE):
            with open(utils.TICKET_TEMPLATE_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            return {k: data.get(k, "") for k in TEMPLATE_FIELDS_MAP}
        return {k: "" for k in TEMPLATE_FIELDS_MAP}
    except Exception as e: print(f"Lỗi tải mẫu GBT: {e}"); return {k: "" for k in TEMPLATE_FIELDS_MAP}

def save_ticket_template_data(template_data_dict):
    try:
        with open(utils.TICKET_TEMPLATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(template_data_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Lỗi Lưu", f"Không thể lưu dữ liệu mẫu:\n{e}"); return False

def create_gbt_pdf_page(c, data, qr_path):
    # ... (Nội dung hàm create_gbt_pdf_page giữ nguyên logic vẽ, chỉ cần đảm bảo font FONT_NAME và FONT_NAME_BOLD đã được xử lý)
    # Sử dụng FONT_NAME và FONT_NAME_BOLD đã định nghĩa ở trên
    c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 11) 
    c.drawString(MARGIN_LEFT, PAGE_HEIGHT - MARGIN_TOP, "BỘ GIÁO DỤC VÀ ĐÀO TẠO")
    # ... và tương tự cho các lần setFont khác
    try:
        y = PAGE_HEIGHT - MARGIN_TOP; header_right_x = PAGE_WIDTH - MARGIN_RIGHT
        c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 11); c.drawString(MARGIN_LEFT, y, "BỘ GIÁO DỤC VÀ ĐÀO TẠO"); tr_text = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"; c.drawRightString(header_right_x, y, tr_text)
        tr_width = pdfmetrics.stringWidth(tr_text, FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 11); tr_center_x = header_right_x - tr_width / 2
        y -= LINE_SPACING_SMALL; c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 10); c.drawString(MARGIN_LEFT, y, f"CỤM THI: {data.get('cum_thi', '...')}"); br_text = "Độc lập - Tự do - Hạnh phúc"; c.drawCentredString(tr_center_x, y, br_text)
        y -= LINE_SPACING_SMALL * 0.8; line_l = 6*cm; c.line(MARGIN_LEFT, y, MARGIN_LEFT + line_l, y); br_width = pdfmetrics.stringWidth(br_text, FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 10); line_sx = tr_center_x - br_width / 2; line_ex = tr_center_x + br_width / 2; c.line(line_sx, y, line_ex, y)
        y -= LINE_SPACING_NORMAL; c.setLineWidth(1); c.line(MARGIN_LEFT, y, PAGE_WIDTH - MARGIN_RIGHT, y)
        
        y -= LINE_SPACING_LARGE * 1.5; c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 18); title = f"GIẤY BÁO DỰ THI KỲ THI: {data.get('ky_thi', '...')}"; c.drawCentredString(PAGE_WIDTH / 2, y, title.upper())
        
        y -= LINE_SPACING_LARGE * 1.8; content_y = y; left_x = MARGIN_LEFT + 0.5 * cm; qr_fw = QR_DISPLAY_SIZE + 2*QR_PADDING; qr_dx = PAGE_WIDTH - MARGIN_RIGHT - qr_fw
        c.setFont(FONT_NAME, 12); label_w = 5.2*cm; y_left = content_y # Tăng label_w
        
        c.drawString(left_x, y_left, f"Họ và tên thí sinh:"); c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 12); c.drawString(left_x + label_w, y_left, data.get('ho_ten', '').upper()); c.setFont(FONT_NAME, 12)
        y_left -= LINE_SPACING_NORMAL; c.drawString(left_x, y_left, f"Số báo danh:"); c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 12); c.drawString(left_x + label_w, y_left, data.get('sbd', '')); c.setFont(FONT_NAME, 12)
        y_left -= LINE_SPACING_NORMAL; c.drawString(left_x, y_left, f"Ngày, tháng, năm sinh:"); c.drawString(left_x + label_w, y_left, data.get('ngay_sinh', ''))
        y_left -= LINE_SPACING_NORMAL * 1.1; c.setFont(FONT_NAME, 10); c.drawString(left_x, y_left, "(Các thông tin khác sẽ được thông báo tại phòng thi)")

        if os.path.exists(qr_path):
            try:
                qr_img=Image.open(qr_path); img_w_orig,img_h_orig=qr_img.size
                ratio=min(QR_DISPLAY_SIZE/img_w_orig, QR_DISPLAY_SIZE/img_h_orig)
                qr_w_draw,qr_h_draw = img_w_orig*ratio, img_h_orig*ratio
                qr_final_x=qr_dx + (qr_fw-qr_w_draw)/2
                qr_final_y=content_y - qr_h_draw # Y tính từ dưới lên của ảnh QR
                
                qr_reader_obj=ImageReader(qr_img)
                c.drawImage(qr_reader_obj, qr_final_x, qr_final_y, width=qr_w_draw, height=qr_h_draw, mask='auto')
                c.setLineWidth(0.5); fr_border_x,fr_border_y=qr_final_x-QR_PADDING, qr_final_y-QR_PADDING
                fr_border_w,fr_border_h=qr_w_draw+2*QR_PADDING, qr_h_draw+2*QR_PADDING
                c.rect(fr_border_x, fr_border_y, fr_border_w, fr_border_h)
                c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 10); c.drawCentredString(fr_border_x+fr_border_w/2, fr_border_y-0.5*cm, "MÃ ĐIỂM DANH")
            except Exception as qre_draw: print(f"Lỗi vẽ QR lên PDF: {qre_draw}")
        else: print(f"File QR không tồn tại: {qr_path}")
        
        y_left -= LINE_SPACING_LARGE*1.5 # Thêm khoảng cách
        c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 12); c.drawString(left_x, y_left, "Lưu ý quan trọng:")
        y_left -= LINE_SPACING_NORMAL * 0.8; c.setFont(FONT_NAME, 10); 
        c.drawString(left_x, y_left, "- Thí sinh có mặt tại địa điểm thi trước giờ thi ít nhất 30 phút.")
        y_left -= LINE_SPACING_SMALL; c.drawString(left_x, y_left, "- Mang theo Giấy Báo Dự Thi này và Căn cước công dân (hoặc giấy tờ tùy thân hợp lệ).")
        y_left -= LINE_SPACING_SMALL; c.drawString(left_x, y_left, "- Không mang các vật dụng bị cấm vào phòng thi theo quy chế.")

        foot_y_base = MARGIN_BOTTOM + 3*cm
        c.setFont(FONT_NAME, 11); foot_date_text=f"{data.get('ngay_thi_footer','Địa danh, .....')}, ngày ..... tháng ..... năm 20....."
        foot_right_x = PAGE_WIDTH-MARGIN_RIGHT-0.5*cm
        c.drawRightString(foot_right_x, foot_y_base, foot_date_text)
        foot_y_base -= LINE_SPACING_NORMAL*1.2
        c.setFont(FONT_NAME_BOLD if FONT_NAME != "Helvetica" else "Helvetica-Bold", 11); c.drawRightString(foot_right_x, foot_y_base, "CHỦ TỊCH HỘI ĐỒNG THI")
        foot_y_base -= LINE_SPACING_NORMAL
        c.setFont(FONT_NAME, 10); c.drawRightString(foot_right_x, foot_y_base, "(Ký, đóng dấu và ghi rõ họ, tên)")
    except Exception as e_page: print(f"Lỗi tạo trang PDF GBT: {e_page}"); raise

def _export_single_ticket_pdf(data_dict, qr_path, output_filepath):
    try:
        original_dob = data_dict.get('ngay_sinh', '')
        data_dict['ngay_sinh'] = format_date_dmy(original_dob)
        c = pdfcanvas.Canvas(output_filepath, pagesize=A4)
        create_gbt_pdf_page(c, data_dict, qr_path)
        c.save()
        return True
    except Exception as e:
        messagebox.showerror("Lỗi Xuất PDF", f"Không thể tạo file PDF:\n{e}"); return False

def show_teacher_ticket_management_ui(parent_window):
    mgmt_window = Toplevel(parent_window)
    mgmt_window.title("Quản lý Mẫu Giấy Báo Thi")
    mgmt_window.geometry("600x280") # Rộng hơn
    mgmt_window.transient(parent_window); mgmt_window.grab_set()
    mgmt_window.configure(bg=utils.COLOR_BG_FRAME)

    template_vars = {}
    current_template_data = load_ticket_template_data()

    main_frame = ttk.Frame(mgmt_window, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="Thông tin chung cho Giấy Báo Thi", font=utils.FONT_MEDIUM_BOLD, anchor=tk.CENTER).pack(pady=(0, 15), fill=tk.X)

    form_frame = ttk.Frame(main_frame)
    form_frame.pack(fill=tk.X)

    for i, (key, label_text) in enumerate(TEMPLATE_FIELDS_MAP.items()):
        template_vars[key] = StringVar(value=current_template_data.get(key, ""))
        ttk.Label(form_frame, text=label_text, font=utils.FONT_NORMAL).grid(row=i, column=0, padx=5, pady=6, sticky=tk.W)
        entry = ttk.Entry(form_frame, textvariable=template_vars[key], width=45, font=utils.FONT_NORMAL)
        entry.grid(row=i, column=1, padx=5, pady=6, sticky=tk.EW)
    form_frame.columnconfigure(1, weight=1) # Cho phép Entry giãn ra

    def save_action():
        data_to_save = {key: var.get().strip() for key, var in template_vars.items()}
        if save_ticket_template_data(data_to_save):
            messagebox.showinfo("Thành công", "Đã lưu thông tin mẫu.", parent=mgmt_window)
            mgmt_window.destroy()

    button_frame = ttk.Frame(main_frame) # Không cần padding ở đây
    button_frame.pack(pady=(20,0), fill=tk.X)
    ttk.Button(button_frame, text="Lưu Thông Tin Mẫu", command=save_action, width=22, style="Accent.TButton").pack(side=tk.LEFT, padx=10, expand=True)
    ttk.Button(button_frame, text="Hủy", command=mgmt_window.destroy, width=12).pack(side=tk.RIGHT, padx=10, expand=True)

def show_student_ticket_viewer(parent_window, student_sbd, df_students):
    name, dob_str = utils.get_student_info(student_sbd, df_students)
    if not name: messagebox.showerror("Lỗi", f"Không tìm thấy SBD {student_sbd}", parent=parent_window); return
    template_data = load_ticket_template_data()
    data_to_print = template_data.copy()
    data_to_print.update({'sbd': student_sbd, 'ho_ten': name, 'ngay_sinh': dob_str})

    qr_path = os.path.join(utils.QR_CODE_FOLDER, f"{student_sbd}.png")
    if not os.path.exists(qr_path):
        try: student_class = df_students.loc[student_sbd, 'Lớp'] if 'Lớp' in df_students.columns else "N/A"
        except KeyError: student_class = "N/A" # SBD not found or Lớp column missing
        actual_student_class = str(student_class) if pd.notna(student_class) else "N/A"
        qr_path = qr_module.generate_qr_code_file(student_sbd, name, actual_student_class)
        if not qr_path: messagebox.showerror("Lỗi QR", "Không thể tạo mã QR.", parent=parent_window); return

    viewer_window = Toplevel(parent_window)
    viewer_window.title(f"Giấy Báo Thi - {student_sbd}")
    viewer_window.geometry("500x350") # Rộng hơn
    viewer_window.transient(parent_window); viewer_window.grab_set()
    viewer_window.configure(bg=utils.COLOR_BG_FRAME)

    main_frame = ttk.Frame(viewer_window, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="Thông tin Giấy Báo Thi", font=utils.FONT_MEDIUM_BOLD, anchor=tk.CENTER).pack(pady=(0, 15), fill=tk.X)
    
    info_display_frame = ttk.Frame(main_frame)
    info_display_frame.pack(fill=tk.X)

    info_labels = [
        ("Kỳ thi:", data_to_print.get('ky_thi', '')),
        ("Họ tên:", data_to_print.get('ho_ten', '')),
        ("SBD:", data_to_print.get('sbd', '')),
        ("Ngày sinh:", format_date_dmy(data_to_print.get('ngay_sinh', ''))),
        ("Cụm thi:", data_to_print.get('cum_thi', '')),
        # ("Footer:", data_to_print.get('ngay_thi_footer', '')) # Có thể không cần hiển thị
    ]
    for i, (label_text, value_text) in enumerate(info_labels):
        ttk.Label(info_display_frame, text=label_text, font=utils.FONT_NORMAL + ("bold",)).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Label(info_display_frame, text=value_text, font=utils.FONT_NORMAL, wraplength=300).grid(row=i, column=1, sticky=tk.W, padx=5, pady=3)
    info_display_frame.columnconfigure(1, weight=1)

    def export_action():
        fname = f"GiayBaoThi_{student_sbd}.pdf"
        os.makedirs(DEFAULT_OUTPUT_FOLDER, exist_ok=True)
        fp = filedialog.asksaveasfilename(title="Lưu PDF Giấy Báo Thi", initialdir=DEFAULT_OUTPUT_FOLDER, initialfile=fname, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], parent=viewer_window)
        if fp and _export_single_ticket_pdf(data_to_print, qr_path, fp):
             messagebox.showinfo("Thành công", f"Đã lưu Giấy Báo Thi tại:\n{fp}", parent=viewer_window)

    button_bottom_frame = ttk.Frame(main_frame)
    button_bottom_frame.pack(pady=(20,0), fill=tk.X)
    ttk.Button(button_bottom_frame, text="Xuất ra PDF", command=export_action, width=18, style="Accent.TButton").pack(side=tk.LEFT, padx=10, expand=True)
    ttk.Button(button_bottom_frame, text="Đóng", command=viewer_window.destroy, width=12).pack(side=tk.RIGHT, padx=10, expand=True)

def show_teacher_ticket_viewer(parent_window, df_students):
    if df_students is None or df_students.empty:
        messagebox.showerror("Lỗi", "Chưa tải dữ liệu học sinh.", parent=parent_window); return
    sbd_list = sorted(df_students.index.astype(str).tolist())
    if not sbd_list:
        messagebox.showinfo("Thông báo", "Không có SBD nào trong dữ liệu.", parent=parent_window); return

    viewer_window = Toplevel(parent_window)
    viewer_window.title("Xem/Xuất Giấy Báo Thi (Giáo viên)")
    viewer_window.geometry("550x380") # Rộng hơn
    viewer_window.transient(parent_window); viewer_window.grab_set()
    viewer_window.configure(bg=utils.COLOR_BG_FRAME)

    selected_sbd_var = StringVar()
    student_info_vars = {'ho_ten': StringVar(value='---'), 'ngay_sinh': StringVar(value='---'), 'lop': StringVar(value='---')}
    current_qr_path_var = StringVar()

    main_frame = ttk.Frame(viewer_window, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    select_frame = ttk.Frame(main_frame)
    select_frame.pack(fill=tk.X, pady=(0, 15))
    ttk.Label(select_frame, text="Chọn SBD:", font=utils.FONT_NORMAL).pack(side=tk.LEFT, padx=(0, 5))
    sbd_combobox = ttk.Combobox(select_frame, textvariable=selected_sbd_var, values=sbd_list, state="readonly", width=20, font=utils.FONT_NORMAL)
    sbd_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

    info_group = ttk.LabelFrame(main_frame, text="Thông tin Thí sinh")
    info_group.pack(fill=tk.X, pady=5)
    ttk.Label(info_group, text="Họ tên:", font=utils.FONT_NORMAL).grid(row=0, column=0, sticky='w', padx=5, pady=3)
    ttk.Label(info_group, textvariable=student_info_vars['ho_ten'], font=utils.FONT_NORMAL).grid(row=0, column=1, sticky='w', padx=5)
    ttk.Label(info_group, text="Ngày sinh:", font=utils.FONT_NORMAL).grid(row=1, column=0, sticky='w', padx=5, pady=3)
    ttk.Label(info_group, textvariable=student_info_vars['ngay_sinh'], font=utils.FONT_NORMAL).grid(row=1, column=1, sticky='w', padx=5)
    ttk.Label(info_group, text="Lớp:", font=utils.FONT_NORMAL).grid(row=2, column=0, sticky='w', padx=5, pady=3)
    ttk.Label(info_group, textvariable=student_info_vars['lop'], font=utils.FONT_NORMAL).grid(row=2, column=1, sticky='w', padx=5)
    info_group.columnconfigure(1, weight=1)

    export_button = ttk.Button(main_frame, text="Xuất PDF cho SBD này", state=tk.DISABLED, command=lambda: export_selected(), style="Accent.TButton")
    export_button.pack(pady=(15,10), ipady=5)
    ttk.Button(main_frame, text="Đóng", command=viewer_window.destroy).pack(pady=5)

    def update_student_info(*args):
        sbd = selected_sbd_var.get()
        export_button.config(state=tk.DISABLED); current_qr_path_var.set("")
        if sbd:
            name, dob_str = utils.get_student_info(sbd, df_students)
            student_class_val = "N/A"
            if 'Lớp' in df_students.columns:
                try: student_class_val = df_students.loc[sbd, 'Lớp']
                except KeyError: pass # SBD not in index or Lớp column missing
            actual_student_class = str(student_class_val) if pd.notna(student_class_val) else "N/A"

            student_info_vars['ho_ten'].set(name if name else "Không tìm thấy")
            student_info_vars['ngay_sinh'].set(format_date_dmy(dob_str) if dob_str else "Không có")
            student_info_vars['lop'].set(actual_student_class)

            qr_path_check = os.path.join(utils.QR_CODE_FOLDER, f"{sbd}.png")
            if os.path.exists(qr_path_check):
                current_qr_path_var.set(qr_path_check); export_button.config(state=tk.NORMAL)
            else:
                new_qr_path = qr_module.generate_qr_code_file(sbd, name, actual_student_class)
                if new_qr_path: current_qr_path_var.set(new_qr_path); export_button.config(state=tk.NORMAL)
                else: student_info_vars['ho_ten'].set(f"{name or 'SBD Lỗi'} (LỖI TẠO QR)")
        else:
            for var in student_info_vars.values(): var.set('---')

    selected_sbd_var.trace_add("write", update_student_info)

    def export_selected():
        sbd = selected_sbd_var.get(); qr_path_sel = current_qr_path_var.get()
        if not sbd or not qr_path_sel: messagebox.showerror("Lỗi", "Thiếu SBD hoặc đường dẫn QR.", parent=viewer_window); return

        template_data_sel = load_ticket_template_data()
        data_to_print_sel = template_data_sel.copy()
        # Lấy lại ngày sinh gốc chưa format từ df_students cho _export_single_ticket_pdf
        _, dob_original = utils.get_student_info(sbd, df_students)
        data_to_print_sel.update({
            'sbd': sbd, 'ho_ten': student_info_vars['ho_ten'].get(), 
            'ngay_sinh': dob_original # Quan trọng: dùng ngày sinh gốc
        })

        fname = f"GiayBaoThi_{sbd}.pdf"
        os.makedirs(DEFAULT_OUTPUT_FOLDER, exist_ok=True)
        fp = filedialog.asksaveasfilename(title="Lưu PDF Giấy Báo Thi", initialdir=DEFAULT_OUTPUT_FOLDER, initialfile=fname, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], parent=viewer_window)
        if fp and _export_single_ticket_pdf(data_to_print_sel, qr_path_sel, fp):
             messagebox.showinfo("Thành công", f"Đã lưu Giấy Báo Thi tại:\n{fp}", parent=viewer_window)

def export_all_tickets_pdf(parent_window, df_students):
    if df_students is None or df_students.empty: messagebox.showerror("Lỗi", "Chưa tải dữ liệu học sinh.", parent=parent_window); return
    
    os.makedirs(DEFAULT_OUTPUT_FOLDER, exist_ok=True)
    fname = f"GiayBaoThi_HangLoat_{datetime.now():%Y%m%d_%H%M}.pdf"
    fp = filedialog.asksaveasfilename(title="Lưu PDF GBT Hàng loạt", initialdir=DEFAULT_OUTPUT_FOLDER, initialfile=fname, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], parent=parent_window)
    if not fp: return

    template_data_all = load_ticket_template_data()
    total = len(df_students); success_count, error_count, missing_qr_list = 0, 0, []

    prog_win = Toplevel(parent_window); prog_win.title("Đang xuất..."); prog_win.geometry("350x120"); prog_win.transient(parent_window); prog_win.grab_set(); prog_win.configure(bg=utils.COLOR_BG_FRAME)
    prog_main_frame = ttk.Frame(prog_win, padding=10)
    prog_main_frame.pack(expand=True, fill=tk.BOTH)
    prog_label = ttk.Label(prog_main_frame, text="Chuẩn bị..."); prog_label.pack(pady=5)
    prog_bar = ttk.Progressbar(prog_main_frame, orient="horizontal", length=300, mode="determinate"); prog_bar.pack(pady=10)
    prog_win.update()

    try:
        c_all = pdfcanvas.Canvas(fp, pagesize=A4)
        for idx, (sbd, row) in enumerate(df_students.iterrows()):
            sbd_str = str(sbd)
            prog_label.config(text=f"Xử lý {idx+1}/{total}: {sbd_str}")
            prog_bar['value'] = (idx+1)/total * 100
            prog_win.update_idletasks()

            student_name_val = str(row.get("Họ và tên", "")).strip()
            student_dob_val = str(row.get("Ngày sinh", "")).strip() # Ngày sinh gốc từ Excel
            
            try: student_class = df_students.loc[sbd_str, 'Lớp'] if 'Lớp' in df_students.columns else "N/A"
            except KeyError: student_class = "N/A"
            actual_student_class = str(student_class) if pd.notna(student_class) else "N/A"


            qr_path_all = os.path.join(utils.QR_CODE_FOLDER, f"{sbd_str}.png")
            if not os.path.exists(qr_path_all):
                 qr_path_all = qr_module.generate_qr_code_file(sbd_str, student_name_val, actual_student_class)
            if not qr_path_all or not os.path.exists(qr_path_all):
                missing_qr_list.append(sbd_str); error_count+=1; continue

            data_to_draw_all = template_data_all.copy()
            data_to_draw_all.update({'sbd': sbd_str, 'ho_ten': student_name_val, 'ngay_sinh': student_dob_val}) # Dùng ngày sinh gốc
            data_to_draw_all['ngay_sinh'] = format_date_dmy(data_to_draw_all.get('ngay_sinh', '')) # Format sau

            try:
                create_gbt_pdf_page(c_all, data_to_draw_all, qr_path_all); c_all.showPage(); success_count += 1
            except Exception as e1_page: print(f"Lỗi tạo trang SBD {sbd_str}: {e1_page}"); error_count += 1
        
        c_all.save()
        prog_win.destroy()

        msg_parts = [f"Hoàn tất: Xuất thành công {success_count}/{total} Giấy Báo Thi."]
        if error_count > 0: msg_parts.append(f"{error_count} giấy bị lỗi trong quá trình tạo.")
        if missing_qr_list: msg_parts.append(f"SBD thiếu/lỗi QR: {', '.join(missing_qr_list[:5])}{'...' if len(missing_qr_list)>5 else ''}")
        messagebox.showinfo("Hoàn thành", "\n".join(msg_parts) + f"\n\nFile lưu tại: {fp}", parent=parent_window)
    except Exception as e_main_export:
        if prog_win.winfo_exists(): prog_win.destroy()
        messagebox.showerror("Lỗi Xuất Hàng loạt", f"Đã có lỗi nghiêm trọng xảy ra: {e_main_export}", parent=parent_window)
