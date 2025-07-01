import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Toplevel
import os
import pandas as pd
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import landscape, A5
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from datetime import datetime

import utils
import qr_module # Cần để tạo QR

from reportlab.platypus import Paragraph # <<< THÊM IMPORT NÀY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # <<< THÊM IMPORT NÀY
from reportlab.lib.enums import TA_LEFT # <<< THÊM IMPORT NÀY

# Ensure sys is imported if not already
import sys

print("DEBUG: student_card_module.py được load.")

# --- Font Registration ---
ARIAL_FONT_PATH_CARD = "Arial.ttf"
FONT_NAME_CARD = "StudentCardArial"
FONT_NAME_CARD_BOLD = "StudentCardArialBold"
CUSTOM_FONT_LOADED = False
try:
    # Determine base path for font (works for script and PyInstaller bundle)
    if hasattr(sys, '_MEIPASS'):
        base_path_font = sys._MEIPASS
    else:
        base_path_font = os.path.dirname(os.path.abspath(__file__))

    font_path_to_check = os.path.join(base_path_font, ARIAL_FONT_PATH_CARD)
    # Sometimes PyInstaller puts data files in the root of _MEIPASS
    if not os.path.exists(font_path_to_check) and hasattr(sys, '_MEIPASS'):
         font_path_to_check = os.path.join(sys._MEIPASS, os.path.basename(ARIAL_FONT_PATH_CARD))

    if os.path.exists(font_path_to_check):
        pdfmetrics.registerFont(TTFont(FONT_NAME_CARD, font_path_to_check))
        print(f"DEBUG: Đã đăng ký font thường '{FONT_NAME_CARD}' từ '{font_path_to_check}'.")
        CUSTOM_FONT_LOADED = True

        # Try to find bold font variations
        font_bold_path_candidates = [
            os.path.join(base_path_font, "Arialbd.ttf"),
            os.path.join(base_path_font, "arialbd.ttf"),
            os.path.join(base_path_font, "Arial Bold.ttf"),
            os.path.join(base_path_font, "arialb.ttf"),
            os.path.join(base_path_font, "arialbi.ttf"),
            os.path.join(base_path_font, "Arial Bold Italic.ttf"),
            # Check in _MEIPASS root as well
            os.path.join(sys._MEIPASS, "Arialbd.ttf") if hasattr(sys, '_MEIPASS') else "",
            os.path.join(sys._MEIPASS, "arialbd.ttf") if hasattr(sys, '_MEIPASS') else "",
        ]
        found_bold = False
        for bold_path_candidate in font_bold_path_candidates:
            if bold_path_candidate and os.path.exists(bold_path_candidate):
                try:
                    pdfmetrics.registerFont(TTFont(FONT_NAME_CARD_BOLD, bold_path_candidate))
                    print(f"DEBUG: Đã đăng ký font Bold '{FONT_NAME_CARD_BOLD}' từ file '{bold_path_candidate}'.")
                    found_bold = True; break
                except Exception as e_reg_bold:
                    print(f"DEBUG: Lỗi khi đăng ký font bold '{bold_path_candidate}': {e_reg_bold}")

        if not found_bold:
            FONT_NAME_CARD_BOLD = FONT_NAME_CARD # Fallback to regular if bold not found
            print(f"DEBUG: Không tìm thấy file font Bold cho Arial. '{FONT_NAME_CARD_BOLD}' sẽ dùng font thường.")
    else:
        print(f"Warning: Font tùy chỉnh '{ARIAL_FONT_PATH_CARD}' không tìm thấy tại '{font_path_to_check}', dùng Helvetica.")
        FONT_NAME_CARD = "Helvetica"; FONT_NAME_CARD_BOLD = "Helvetica-Bold"

except Exception as e_font:
    print(f"Lỗi đăng ký font toàn cục: {e_font}")
    FONT_NAME_CARD = "Helvetica"; FONT_NAME_CARD_BOLD = "Helvetica-Bold"
    CUSTOM_FONT_LOADED = False # Ensure this is false if registration fails

# --- Hàm vẽ một trang thẻ học sinh (A5 ngang) ---

def draw_single_student_card_page(c: pdfcanvas.Canvas, page_w, page_h, student_info: dict, main_app_instance):
    """Vẽ nội dung cho một trang thẻ học sinh (A5 ngang) - Final Version."""
    print(f"DEBUG draw_single_student_card_page: Bắt đầu vẽ thẻ cho SBD {student_info.get('sbd')}")
    try:
        sbd = student_info.get('sbd', 'N/A'); name = student_info.get('name', 'N/A')
        dob_str = student_info.get('dob', ''); student_class = student_info.get('class', 'N/A')

        # --- Lấy cấu hình trường học ---
        school_config = utils.load_school_config()
        dept_name = school_config.get("dept_name", "PHÒNG GIÁO DỤC VÀ ĐÀO TẠO...")
        school_name_header = school_config.get("school_name", "TRƯỜNG...")
        logo_path_header_config = school_config.get("logo_path", None)
        logo_path_card_config = school_config.get("school_logo_on_card_path", None)
        current_school_year = school_config.get("school_year", f"{datetime.now().year}-{datetime.now().year+1}")
        card_issuing_place = school_config.get("card_issuing_place", "TP. Hồ Chí Minh")
        card_issuer_name = school_config.get("card_issuer_name", ".........................")

        photo_folder = utils.PHOTO_FOLDER
        header_color_hex = utils.COLOR_PRIMARY
        try: header_color = colors.HexColor(header_color_hex)
        except: header_color = colors.HexColor("#003366")

        # --- Kích thước, Lề và Khoảng cách Dòng ---
        margin = 1.0 * cm
        header_height = 2.0 * cm
        left_col_width = 4.5 * cm
        qr_area_height = 4.2 * cm
        photo_area_height = page_h - header_height - qr_area_height - margin * 2.2
        right_col_x = margin + left_col_width
        content_y_start_ref = page_h - header_height - margin
        line_spacing_main_info = 1.0 * cm # Khoảng cách dòng chính
        line_spacing_extra_info = 0.55 * cm
        signature_y_base = margin + 1.8 * cm # Base Y for signature block

        # --- Font Sizes ---
        title_font_size_card = 24
        label_font_size_card = 11
        value_font_size_card = 11 # Dùng cho cả tên, ngày sinh, lớp, sbd, niên khóa
        small_info_font_size = 8.5 # Dùng cho Ghi chú
        # year_font_size = 10 # Không cần nữa, dùng value_font_size_card
        signature_info_font_size = 9


        # --- Vẽ Header Xanh ---
        # (Code vẽ Header giữ nguyên)
        c.setFillColor(header_color)
        c.rect(margin, content_y_start_ref, page_w - 2*margin, header_height, stroke=0, fill=1)
        header_content_x_start = margin + 0.5*cm
        header_text_y_base = content_y_start_ref + header_height - 0.7*cm
        line_height_header = 0.5*cm
        logo_drawn_header = False
        max_logo_h_header = header_height - 0.6 * cm
        if logo_path_header_config and os.path.exists(logo_path_header_config):
            try:
                logo_img_reader_header = ImageReader(logo_path_header_config)
                img_w_h, img_h_h = logo_img_reader_header.getSize()
                ratio_h = max_logo_h_header / img_h_h if img_h_h > 0 else 1
                draw_logo_w_h = img_w_h * ratio_h; draw_logo_h_h = img_h_h * ratio_h
                logo_header_x = page_w - margin - 0.5*cm - draw_logo_w_h
                logo_header_y = content_y_start_ref + (header_height - draw_logo_h_h) / 2
                c.drawImage(logo_img_reader_header, logo_header_x, logo_header_y, width=draw_logo_w_h, height=draw_logo_h_h, mask='auto')
                logo_drawn_header = True
            except Exception as e_logo_header: print(f"Lỗi vẽ logo header: {e_logo_header}")
        c.setFillColor(colors.white); c.setFont(FONT_NAME_CARD_BOLD, 10)
        max_text_width_header = (page_w - 2*margin - (draw_logo_w_h + 0.5*cm if logo_drawn_header else 0) - 1*cm)
        def draw_limited_text(canvas_obj, text, x, y, font_name, font_size, max_w):
            text_w = canvas_obj.stringWidth(text, font_name, font_size)
            if text_w > max_w and max_w > 0:
                ratio_truncate = max_w / text_w if text_w > 0 else 1
                num_chars_to_show = int(len(text) * ratio_truncate) - 3
                if num_chars_to_show < 1 and len(text) > 3: num_chars_to_show = 1
                text_to_draw = text[:num_chars_to_show] + "..." if num_chars_to_show > 0 else "..."
            else: text_to_draw = text
            canvas_obj.drawString(x, y, text_to_draw)
        draw_limited_text(c, dept_name.upper(), header_content_x_start, header_text_y_base, FONT_NAME_CARD_BOLD, 10, max_text_width_header)
        draw_limited_text(c, school_name_header.upper(), header_content_x_start, header_text_y_base - line_height_header, FONT_NAME_CARD_BOLD, 10, max_text_width_header)


        # --- Vẽ Đường Kẻ Phân Chia ---
        # (Code vẽ đường kẻ giữ nguyên)
        c.setStrokeColor(colors.darkgrey); c.setLineWidth(0.3)
        c.line(margin + left_col_width, margin, margin + left_col_width, content_y_start_ref) # Dọc
        photo_bottom_y_line = margin + qr_area_height # Y của đường kẻ ngang
        c.line(margin, photo_bottom_y_line, margin + left_col_width, photo_bottom_y_line) # Ngang


        # --- Vẽ Cột Trái (Ảnh, QR) ---
        # (Code vẽ ảnh và QR giữ nguyên)
        inner_padding_left_col = 0.2 * cm
        # Photo Area
        photo_x_area_start = margin + inner_padding_left_col
        photo_y_area_start = photo_bottom_y_line + inner_padding_left_col
        photo_w_area_max = left_col_width - 2 * inner_padding_left_col
        photo_h_area_max = content_y_start_ref - photo_y_area_start - inner_padding_left_col 
        photo_drawn = False
        photo_path_png = os.path.join(photo_folder, f"{sbd}.png"); photo_path_jpg = os.path.join(photo_folder, f"{sbd}.jpg")
        actual_photo_path = photo_path_png if os.path.exists(photo_path_png) else (photo_path_jpg if os.path.exists(photo_path_jpg) else None)
        if actual_photo_path:
            try:
                photo_img = ImageReader(actual_photo_path); img_w_p, img_h_p = photo_img.getSize()
                ratio_p = min(photo_w_area_max / img_w_p if img_w_p > 0 else 1, photo_h_area_max / img_h_p if img_h_p > 0 else 1)
                draw_w_p, draw_h_p = img_w_p * ratio_p, img_h_p * ratio_p
                c.drawImage(photo_img, photo_x_area_start + (photo_w_area_max - draw_w_p) / 2, photo_y_area_start + (photo_h_area_max - draw_h_p) / 2, width=draw_w_p, height=draw_h_p, mask='auto'); photo_drawn = True
            except Exception as e_photo: print(f"Lỗi vẽ ảnh HS '{actual_photo_path}': {e_photo}")
        if not photo_drawn:
             c.setFont(FONT_NAME_CARD, 8); c.setFillColor(colors.grey)
             c.drawCentredString(margin + left_col_width / 2, photo_y_area_start + photo_h_area_max / 2 - 4, "Ảnh học sinh")
             c.setStrokeColor(colors.lightgrey); c.setLineWidth(0.5)
             c.rect(photo_x_area_start, photo_y_area_start, photo_w_area_max, photo_h_area_max, stroke=1, fill=0)

        # QR Code Area
        qr_x_area_start = margin + inner_padding_left_col
        qr_y_area_start = margin + inner_padding_left_col
        qr_w_area_max = left_col_width - 2 * inner_padding_left_col
        qr_h_area_total = qr_area_height - 2*inner_padding_left_col 
        sbd_text_height = 0.4*cm 
        qr_h_area_for_qr_image = qr_h_area_total - sbd_text_height 
        qr_size_actual = min(qr_w_area_max, qr_h_area_for_qr_image) 
        qr_image_x = qr_x_area_start + (qr_w_area_max - qr_size_actual) / 2
        qr_image_y = qr_y_area_start + sbd_text_height 

        qr_path_student = os.path.join(utils.QR_CODE_FOLDER, f"{sbd}.png")
        if not os.path.exists(qr_path_student): qr_path_student = qr_module.generate_qr_code_file(sbd, name, student_class)
        if qr_path_student and os.path.exists(qr_path_student):
            try:
                qr_img_reader = ImageReader(qr_path_student)
                c.drawImage(qr_img_reader, qr_image_x, qr_image_y, width=qr_size_actual, height=qr_size_actual, mask='auto')
            except Exception as e_qr: print(f"Lỗi vẽ QR cho SBD {sbd}: {e_qr}")
        else:
            c.setFont(FONT_NAME_CARD, 7); c.setFillColor(colors.grey)
            c.drawCentredString(margin + left_col_width / 2, qr_y_area_start + qr_h_area_total / 2 - 3, "[Mã QR]")

        # Draw SBD below QR
        c.setFont(FONT_NAME_CARD_BOLD, 9); c.setFillColor(colors.black)
        c.drawCentredString(margin + left_col_width / 2, qr_y_area_start + sbd_text_height / 2 - 4, sbd) 

        # Draw QR area border
        c.setStrokeColor(colors.darkgrey); c.setLineWidth(0.5)
        c.rect(qr_x_area_start, qr_y_area_start, qr_w_area_max, qr_h_area_total, stroke=1, fill=0)


        # --- Vẽ Cột Phải ---
        c.setFillColor(colors.black)
        text_block_start_x = right_col_x + 0.8 * cm
        label_width_info = 3.8 * cm
        value_start_x_info = text_block_start_x + label_width_info # X start for values

        # --- Phần Ký tên (Tính toán tọa độ X trước) ---
        # (Code tính toán ký tên giữ nguyên)
        signature_block_width_estimate = 7.0 * cm
        signature_block_x_start = page_w - margin - signature_block_width_estimate
        signature_block_x_center = signature_block_x_start + signature_block_width_estimate / 2
        signature_total_height_estimate = line_spacing_extra_info * (1.2 + 1 + 2.5) 


        # --- Logo chính của trường ---
        # (Code vẽ logo chính giữ nguyên)
        logo_square_size_max = 2.5 * cm
        logo_card_x = text_block_start_x
        logo_card_y_top = content_y_start_ref - 0.4 * cm
        logo_card_actual_y_bottom = logo_card_y_top - logo_square_size_max
        logo_card_drawn = False
        if logo_path_card_config and os.path.exists(logo_path_card_config):
            try:
                logo_img_card_reader = ImageReader(logo_path_card_config)
                img_w_lc, img_h_lc = logo_img_card_reader.getSize()
                if img_w_lc > img_h_lc: draw_w_lc = logo_square_size_max; draw_h_lc = img_h_lc * (logo_square_size_max / img_w_lc if img_w_lc > 0 else 1)
                else: draw_h_lc = logo_square_size_max; draw_w_lc = img_w_lc * (logo_square_size_max / img_h_lc if img_h_lc > 0 else 1)
                c.drawImage(logo_img_card_reader, logo_card_x + (logo_square_size_max - draw_w_lc)/2 , logo_card_actual_y_bottom + (logo_square_size_max - draw_h_lc)/2, width=draw_w_lc, height=draw_h_lc, mask='auto')
                logo_card_drawn = True
            except Exception as e_logo_card: print(f"Lỗi vẽ logo chính trên thẻ: {e_logo_card}")
        if not logo_card_drawn:
            c.setFont(FONT_NAME_CARD, 8); c.setFillColor(colors.grey)
            c.drawCentredString(logo_card_x + logo_square_size_max/2, logo_card_actual_y_bottom + logo_square_size_max/2 - 4, "Logo Trường")
        c.setStrokeColor(colors.lightgrey); c.setLineWidth(0.5); c.rect(logo_card_x, logo_card_actual_y_bottom, logo_square_size_max, logo_square_size_max, stroke=1, fill=0); c.setFillColor(colors.black)


        # --- Tiêu đề "THẺ HỌC SINH" ---
        # (Code vẽ tiêu đề giữ nguyên)
        title_y_card = logo_card_actual_y_bottom - 0.8*cm 
        c.setFont(FONT_NAME_CARD_BOLD, title_font_size_card)
        title_text_card = "THẺ HỌC SINH"
        title_available_width = page_w - margin - (logo_card_x + logo_square_size_max + 0.2*cm)
        title_start_x = logo_card_x + logo_square_size_max + 0.2*cm
        title_w_actual = c.stringWidth(title_text_card, FONT_NAME_CARD_BOLD, title_font_size_card)
        c.drawString(title_start_x + (title_available_width - title_w_actual) / 2 if title_available_width > title_w_actual else title_start_x, title_y_card, title_text_card)


        # --- Thông tin học sinh ---
        current_info_y = title_y_card - line_spacing_main_info * 2.0 
        # Họ và tên
        c.setFont(FONT_NAME_CARD, label_font_size_card); c.drawString(text_block_start_x, current_info_y, "Họ và tên:")
        c.setFont(FONT_NAME_CARD_BOLD, value_font_size_card); c.drawString(value_start_x_info, current_info_y, name.upper())
        current_info_y -= line_spacing_main_info
        # Ngày sinh
        dob_formatted = utils.format_date_dmy(dob_str)
        c.setFont(FONT_NAME_CARD, label_font_size_card); c.drawString(text_block_start_x, current_info_y, "Ngày sinh:")
        c.setFont(FONT_NAME_CARD, value_font_size_card); c.drawString(value_start_x_info, current_info_y, dob_formatted)
        current_info_y -= line_spacing_main_info
        # Lớp
        c.setFont(FONT_NAME_CARD, label_font_size_card); c.drawString(text_block_start_x, current_info_y, "Lớp:")
        c.setFont(FONT_NAME_CARD, value_font_size_card); c.drawString(value_start_x_info, current_info_y, student_class)
        current_info_y -= line_spacing_main_info
        # Mã học sinh
        c.setFont(FONT_NAME_CARD, label_font_size_card); c.drawString(text_block_start_x, current_info_y, "Mã học sinh:")
        c.setFont(FONT_NAME_CARD, value_font_size_card); c.drawString(value_start_x_info, current_info_y, sbd)
        
        # --- Vẽ Niên khóa (Sử dụng cùng khoảng cách dòng chính và căn lề giá trị) ---
        current_info_y -= line_spacing_main_info # <<<< MOVE DOWN USING MAIN SPACING >>>>
        c.setFont(FONT_NAME_CARD, label_font_size_card); c.drawString(text_block_start_x, current_info_y, "Niên khóa:")
        # <<<< USE SAME FONT SIZE AND STYLE AS OTHER VALUES (e.g., NAME) >>>>
        # <<<< DRAW VALUE AT value_start_x_info >>>>
        c.setFont(FONT_NAME_CARD, value_font_size_card); # Sử dụng font và size như các giá trị khác
        c.drawString(value_start_x_info, current_info_y, current_school_year) 
        
        # Cập nhật Y hiện tại là đáy của Niên khóa để vẽ Ghi chú bên dưới
        y_after_nien_khoa = current_info_y 
        current_info_y = y_after_nien_khoa - line_spacing_extra_info * 1.5 # Khoảng cách trước Ghi chú (có thể điều chỉnh)


        # --- Thông tin bổ sung (Chỉ còn Ghi chú) ---
        # (Code vẽ ghi chú giữ nguyên, nhưng Y bắt đầu đã thay đổi)
        styles = getSampleStyleSheet()
        note_style = ParagraphStyle(
            name='NoteStyle', parent=styles['Normal'], fontName=FONT_NAME_CARD,
            fontSize=small_info_font_size - 0.5, leading=(small_info_font_size - 0.5) * 1.2,
            alignment=TA_LEFT, wordWrap = 'CJK'
        )
        y_bottom_limit_extra = signature_y_base + signature_total_height_estimate + 0.3*cm 

        # --- Vẽ Ghi chú ---
        card_note = "Ghi chú: HS vui lòng giữ gìn thẻ cẩn thận và xuất trình khi được yêu cầu."
        note_para = Paragraph(card_note, note_style)
        available_width_extra = signature_block_x_start - text_block_start_x - 0.5*cm
        note_w, note_h = note_para.wrapOn(c, available_width_extra, current_info_y - y_bottom_limit_extra) 
        draw_y_note = current_info_y - note_h 

        if draw_y_note < y_bottom_limit_extra:
             print(f"Cảnh báo: Ghi chú quá dài có thể bị cắt bớt SBD: {sbd}")
             note_h = current_info_y - y_bottom_limit_extra 
             if note_h > 0: note_para.drawOn(c, text_block_start_x, y_bottom_limit_extra) 
        else:
             note_para.drawOn(c, text_block_start_x, draw_y_note) 

        # --- Phần Ký tên (Vẽ sau cùng) ---
        # (Code vẽ ký tên giữ nguyên)
        c.setFillColor(colors.black)
        signature_draw_y = signature_y_base 
        c.setFont(FONT_NAME_CARD_BOLD, signature_info_font_size)
        c.drawCentredString(signature_block_x_center, signature_draw_y, card_issuer_name.upper())
        signature_draw_y += line_spacing_extra_info * 2.5 

        c.setFont(FONT_NAME_CARD_BOLD, signature_info_font_size + 1)
        c.drawCentredString(signature_block_x_center, signature_draw_y, "HIỆU TRƯỞNG")
        signature_draw_y += line_spacing_extra_info * 1.2 

        c.setFont(FONT_NAME_CARD, signature_info_font_size)
        today = datetime.now()
        date_str_signature = f"{card_issuing_place}, ngày {today.day:02d} tháng {today.month:02d} năm {today.year}"
        c.drawCentredString(signature_block_x_center, signature_draw_y, date_str_signature)

        print(f"DEBUG draw_single_student_card_page: Đã vẽ xong thẻ cho SBD {sbd}")
    except Exception as e_draw_card:
        print(f"LỖI NGHIÊM TRỌNG KHI VẼ THẺ CHO SBD {student_info.get('sbd', 'N/A')}: {e_draw_card}")
        import traceback
        traceback.print_exc()
        if c:
            try: c.setFillColor(colors.red); c.setFont("Helvetica-Bold", 12); c.drawCentredString(page_w/2, page_h/2, "[LỖI VẼ THẺ]")
            except: pass

# Hàm generate_student_cards_pdf (Giữ nguyên)
def generate_student_cards_pdf(main_app_instance, selected_sbds_list, num_cols_ui, num_rows_ui, output_filepath, status_var, parent_win):
    print(f"DEBUG generate_student_cards_pdf: Bắt đầu tạo PDF với {len(selected_sbds_list)} SBD.")
    page_size = landscape(A5); page_w, page_h = page_size
    try:
        c = pdfcanvas.Canvas(output_filepath, pagesize=page_size); generated_count = 0; skipped_count = 0
        for student_idx, sbd in enumerate(selected_sbds_list):
            status_var.set(f"Đang xử lý: {sbd} ({student_idx+1}/{len(selected_sbds_list)})..."); parent_win.update_idletasks()
            name, dob_str = utils.get_student_info(sbd, main_app_instance.student_data)
            student_class_val = "N/A"; df_students = main_app_instance.student_data
            if df_students is not None and 'Lớp' in df_students.columns:
                try:
                    if df_students.index.name == 'SBD':
                        student_class_val = df_students.loc[sbd, 'Lớp']
                    elif 'SBD' in df_students.columns:
                        student_class_val = df_students[df_students['SBD'] == sbd]['Lớp'].iloc[0]
                    else: # Fallback
                        student_class_val = df_students.iloc[student_idx]['Lớp']
                except (KeyError, IndexError): pass
            actual_student_class = str(student_class_val).strip() if pd.notna(student_class_val) else 'N/A'
            if not name: print(f"(!) Bỏ qua SBD {sbd}: Không tìm thấy tên."); skipped_count += 1; continue
            student_info = { 'sbd': sbd, 'name': name, 'dob': dob_str, 'class': actual_student_class }
            print(f"DEBUG: Chuẩn bị vẽ thẻ cho: {student_info}")
            draw_single_student_card_page(c, page_w, page_h, student_info, main_app_instance)
            generated_count += 1
            if student_idx < len(selected_sbds_list) - 1: c.showPage(); print(f"DEBUG: Đã tạo thẻ cho {sbd}, chuyển trang mới...")
        c.save(); final_msg = f"Đã tạo {generated_count} thẻ.";
        if skipped_count > 0: final_msg += f" (Bỏ qua {skipped_count})."
        status_var.set(final_msg); print(f"DEBUG generate_student_cards_pdf: Hoàn thành. {final_msg}"); return True
    except PermissionError: messagebox.showerror("Lỗi Quyền Ghi", f"Không có quyền ghi file tại:\n{output_filepath}", parent=parent_win); status_var.set("Lỗi quyền ghi."); return False
    except Exception as e_pdf:
        print(f"LỖI NGHIÊM TRỌNG KHI TẠO PDF THẺ: {e_pdf}"); import traceback; traceback.print_exc()
        messagebox.showerror("Lỗi Xuất PDF", f"Đã xảy ra lỗi nghiêm trọng khi tạo file PDF thẻ tên:\n{e_pdf}", parent=parent_win); status_var.set(f"Lỗi PDF nghiêm trọng."); return False


# Hàm show_student_card_generator_ui (Giữ nguyên)
def show_student_card_generator_ui(parent_root, main_app_instance):
    print("DEBUG: Gọi show_student_card_generator_ui từ main_app.")
    if main_app_instance.current_user_role != "teacher":
        messagebox.showwarning("Truy cập bị hạn chế", "Chức năng này chỉ dành cho giáo viên.", parent=parent_root)
        return
    card_gen_win = tk.Toplevel(parent_root)
    card_gen_win.title("Tạo Thẻ tên Học sinh")
    card_gen_win.geometry("900x700")
    card_gen_win.transient(parent_root); card_gen_win.grab_set()
    card_gen_win.configure(bg=utils.COLOR_BG_FRAME)
    student_selection_frame = ttk.LabelFrame(card_gen_win, text="Chọn Học sinh", padding="10")
    student_selection_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    filter_frame = ttk.Frame(student_selection_frame)
    filter_frame.pack(fill=tk.X, pady=(0, 5))
    ttk.Label(filter_frame, text="Lọc theo Lớp:", font=utils.FONT_NORMAL).pack(side=tk.LEFT, padx=(0,5))
    filter_class_var = tk.StringVar(value="Tất cả")
    class_options_filter = ["Tất cả"] + (main_app_instance.class_list if main_app_instance.class_list else [])
    filter_class_combobox = ttk.Combobox(filter_frame, textvariable=filter_class_var, values=class_options_filter, state="readonly", width=20, font=utils.FONT_NORMAL)
    filter_class_combobox.pack(side=tk.LEFT, padx=5)
    ttk.Label(filter_frame, text="Tìm SBD/Tên:", font=utils.FONT_NORMAL).pack(side=tk.LEFT, padx=(10,5))
    search_term_var = tk.StringVar()
    search_entry = ttk.Entry(filter_frame, textvariable=search_term_var, width=30, font=utils.FONT_NORMAL)
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    cols_student = ("SBD", "Họ và tên", "Lớp", "Ngày sinh")
    student_tree = ttk.Treeview(student_selection_frame, columns=cols_student, show="headings", style="Treeview", selectmode="extended")
    student_tree.heading("SBD", text="SBD"); student_tree.column("SBD", width=100, anchor=tk.W)
    student_tree.heading("Họ và tên", text="Họ và tên"); student_tree.column("Họ và tên", width=220, anchor=tk.W)
    student_tree.heading("Lớp", text="Lớp"); student_tree.column("Lớp", width=100, anchor=tk.W)
    student_tree.heading("Ngày sinh", text="Ngày sinh"); student_tree.column("Ngày sinh", width=120, anchor=tk.W)
    tree_vsb = ttk.Scrollbar(student_selection_frame, orient="vertical", command=student_tree.yview)
    tree_hsb = ttk.Scrollbar(student_selection_frame, orient="horizontal", command=student_tree.xview)
    student_tree.configure(yscrollcommand=tree_vsb.set, xscrollcommand=tree_hsb.set)
    student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(5,0))
    tree_vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=(5,0)); tree_hsb.pack(side=tk.BOTTOM, fill=tk.X)
    def populate_student_tree(filter_class="Tất cả", search_term=""):
        student_tree.delete(*student_tree.get_children())
        df = main_app_instance.student_data
        if df is None or df.empty: print("DEBUG populate_student_tree: student_data is None or empty."); return
        df_display = df.copy()
        if df_display.index.name == 'SBD': df_display = df_display.reset_index()
        elif 'SBD' not in df_display.columns:
            messagebox.showerror("Lỗi Dữ liệu", "Cột 'SBD' không tồn tại trong dữ liệu học sinh.", parent=card_gen_win);
            return
        sbd_col_name = 'SBD'; name_col_name = 'Họ và tên'; class_col_name = 'Lớp'; dob_col_name = 'Ngày sinh'
        if filter_class != "Tất cả" and class_col_name in df_display.columns:
             df_display = df_display[df_display[class_col_name].astype(str).str.strip() == str(filter_class).strip()]
        if search_term:
            search_term_lower = search_term.lower()
            conditions = pd.Series([False] * len(df_display), index=df_display.index)
            if sbd_col_name in df_display.columns:
                conditions |= df_display[sbd_col_name].astype(str).str.lower().str.contains(search_term_lower, na=False)
            if name_col_name in df_display.columns:
                conditions |= df_display[name_col_name].astype(str).str.lower().str.contains(search_term_lower, na=False)
            df_display = df_display[conditions]
        for idx, row in df_display.iterrows():
            sbd_str = str(row.get(sbd_col_name, 'N/A'))
            name_val_raw = row.get(name_col_name, 'N/A')
            name_val = str(name_val_raw).strip() if pd.notna(name_val_raw) and str(name_val_raw).strip().lower() != 'nan' else 'N/A'
            class_val_raw = row.get(class_col_name, 'N/A')
            class_val = str(class_val_raw).strip() if pd.notna(class_val_raw) and str(class_val_raw).strip().lower() != 'nan' else 'N/A'
            dob_raw = row.get(dob_col_name, '')
            dob_val = utils.format_date_dmy(dob_raw) if pd.notna(dob_raw) else 'N/A'
            student_tree.insert("", tk.END, iid=sbd_str, values=(sbd_str, name_val, class_val, dob_val))

    def on_filter_change(*args): populate_student_tree(filter_class_var.get(), search_term_var.get())
    filter_class_var.trace_add("write", on_filter_change); search_term_var.trace_add("write", on_filter_change)
    config_frame = ttk.LabelFrame(card_gen_win, text="Cấu hình PDF (Mỗi thẻ một trang A5 ngang)", padding="10")
    config_frame.pack(pady=10, padx=10, fill=tk.X)
    action_buttons_frame = ttk.Frame(card_gen_win)
    action_buttons_frame.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)
    status_label_var = tk.StringVar(value=""); status_label = ttk.Label(action_buttons_frame, textvariable=status_label_var, font=utils.FONT_SMALL, foreground=utils.COLOR_TEXT_LIGHT)
    status_label.pack(side=tk.LEFT, padx=5)
    def generate_cards_action():
        selected_iids = student_tree.selection()
        if not selected_iids: messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất một học sinh.", parent=card_gen_win); return
        num_cols_fixed = 1 ; num_rows_fixed = 1 # Each card is an A5 page
        default_filename = f"TheHocSinh_{datetime.now():%Y%m%d_%H%M}.pdf"
        filepath = filedialog.asksaveasfilename(title="Lưu PDF Thẻ học sinh", initialfile=default_filename, defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], parent=card_gen_win)
        if not filepath: return
        status_label_var.set("Đang tạo thẻ, vui lòng chờ..."); card_gen_win.update_idletasks()
        success = generate_student_cards_pdf(main_app_instance, list(selected_iids), num_cols_fixed, num_rows_fixed, filepath, status_label_var, card_gen_win)
        if success: messagebox.showinfo("Thành công", f"Đã tạo PDF thẻ tên tại:\n{filepath}", parent=card_gen_win)
        status_label_var.set("")

    generate_button = ttk.Button(action_buttons_frame, text="Tạo PDF Thẻ (A5/Thẻ)", style="Accent.TButton", width=25, command=generate_cards_action)
    generate_button.pack(side=tk.RIGHT, padx=5)
    close_button = ttk.Button(action_buttons_frame, text="Đóng", width=10, command=card_gen_win.destroy)
    close_button.pack(side=tk.RIGHT)
    populate_student_tree(); filter_class_combobox.focus_set()
