import pandas as pd
import json
import os
from tkinter import messagebox
from datetime import datetime # Đảm bảo có import

SCHEDULE_FILE = "schedule.json"
ANNOUNCEMENTS_FILE = "announcements.json"
STUDENT_DATA_FILE = "students.xlsx"
ATTENDANCE_FILE = "attendance.json"
QR_CODE_FOLDER = "QR_Codes"
TICKET_TEMPLATE_FILE = "ticket_template.json" # Thêm tên file mẫu vé
UNUSABLE_SEATS_FILE = "unusable_seats.json"
EDUCATION_DEPT_NAME = "PHÒNG GIÁO DỤC VÀ ĐÀO TẠO MẪU" # Giá trị mặc định
SCHOOL_NAME = "TRƯỜNG MẪU XYZ" # Giá trị mặc định
LOGO_PATH = "logo_truong.png" # Đường dẫn mặc định, có thể là None nếu không có logo mặc định
PHOTO_FOLDER = "Student_Photos" # Thư mục chứa ảnh HS
SCHOOL_CONFIG_FILE = "school_config.json" # File lưu cấu hình
UPLOADED_LOGO_FOLDER = "school_assets" # <<< THÊM DÒNG NÀY
PHOTO_FOLDER = "Student_Photos" # Hoặc đường dẫn tuyệt đối nếu cần
EVENT_TYPE_COLORS = {
    "Học tập": "#A0D2EB",    # Light Blue
    "Kiểm tra": "#FFB3BA",   # Light Red/Pink
    "Ngoại khóa": "#C1E1C1", # Light Green
    "Họp": "#FFDFBA",       # Light Orange
    "Nghỉ lễ": "#E6E6FA",    # Lavender
    "Khác": "#EEEEEE",       # Light Grey (Default)
    # Thêm các màu khác nếu bạn có thêm loại sự kiện
}


os.makedirs(QR_CODE_FOLDER, exist_ok=True)

USER_CREDENTIALS = {
    "teacher": {"username": "admin", "password": "admin"},
    "student": {"password": "hs001"} # Mật khẩu chung cho học sinh
}

# --- UI Constants ---
FONT_FAMILY = "Arial" # Hoặc "Segoe UI" trên Windows
FONT_SIZE_SMALL = 9
FONT_SIZE_NORMAL = 10
FONT_SIZE_MEDIUM = 11
FONT_SIZE_LARGE = 12
FONT_SIZE_HEADER = 14
FONT_SIZE_APP_TITLE = 16

FONT_SMALL = (FONT_FAMILY, FONT_SIZE_SMALL)
FONT_NORMAL = (FONT_FAMILY, FONT_SIZE_NORMAL)
FONT_MEDIUM = (FONT_FAMILY, FONT_SIZE_MEDIUM)
FONT_BOLD = (FONT_FAMILY, FONT_SIZE_NORMAL, "bold")
FONT_MEDIUM_BOLD = (FONT_FAMILY, FONT_SIZE_MEDIUM, "bold")
FONT_LARGE_BOLD = (FONT_FAMILY, FONT_SIZE_LARGE, "bold")
FONT_HEADER = (FONT_FAMILY, FONT_SIZE_HEADER, "bold")
FONT_APP_TITLE = (FONT_FAMILY, FONT_SIZE_APP_TITLE, "bold")

COLOR_PRIMARY = "#0078D4"  # Xanh dương (ví dụ: Windows Blue)
COLOR_SUCCESS = "#107C10"  # Xanh lá
COLOR_WARNING = "#FF8C00"  # Cam
COLOR_ERROR = "#E81123"    # Đỏ
COLOR_TEXT_NORMAL = "black"
COLOR_TEXT_LIGHT = "#666666" # Xám nhạt
COLOR_BG_MAIN = "#F0F0F0" # Màu nền chính của ứng dụng (ví dụ)
COLOR_BG_FRAME = "white"  # Màu nền cho các frame nội dung
COLOR_BUTTON_HOVER = "#E1E1E1"
COLOR_LISTBOX_EVEN_ROW = "#F9F9F9"
COLOR_LISTBOX_ODD_ROW = "white"
# --- End UI Constants ---

# Lấy đường dẫn thư mục gốc dự án (ví dụ)
ROOT_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__)) # Giả sử utils.py ở gốc

# Thư mục chứa dữ liệu (nếu bạn có)
DATA_DIR = os.path.join(ROOT_PROJECT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True) # Tạo thư mục data nếu chưa có

# Thư mục chứa file đính kèm (bên trong data)
ATTACHMENTS_DIR = os.path.join(DATA_DIR, "attachments")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True) # Tạo thư mục attachments nếu chưa có

# Đường dẫn đến các file dữ liệu (có thể đặt trong data)
STUDENT_DATA_FILE = os.path.join(ROOT_PROJECT_DIR, "students.xlsx") # Giữ ở gốc hoặc chuyển vào data
ANNOUNCEMENTS_FILE = os.path.join(DATA_DIR, "announcements.json")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.json")
TICKET_TEMPLATE_FILE = os.path.join(DATA_DIR, "ticket_template.json")
UNUSABLE_SEATS_FILE = os.path.join(DATA_DIR, "unusable_seats.json")
SCHOOL_CONFIG_FILE = os.path.join(DATA_DIR, "school_config.json")

# Thư mục chứa ảnh HS và logo (có thể cũng nên trong assets hoặc data)
PHOTO_FOLDER = os.path.join(ROOT_PROJECT_DIR, "Student_Photos")
UPLOADED_LOGO_FOLDER = os.path.join(ROOT_PROJECT_DIR, "school_assets")
ICONS_DIR = os.path.join(ROOT_PROJECT_DIR, "icons") # Giả sử thư mục icons ở gốc
# --- KẾT THÚC PHẦN THÊM MỚI/SỬA ĐỔI ---

def load_student_data():
    """Tải dữ liệu HS từ Excel, yêu cầu SBD, Họ và tên, Ngày sinh."""
    try:
        required_columns = ['SBD', 'Họ và tên', 'Ngày sinh']
        dtype_spec = {col: str for col in required_columns}
        df = pd.read_excel(STUDENT_DATA_FILE, engine="openpyxl", dtype=dtype_spec)

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
             messagebox.showerror("Lỗi Excel", f"Thiếu cột: {', '.join(missing_columns)}")
             return None

        df.dropna(subset=required_columns, inplace=True)
        if df.empty:
             messagebox.showerror("Lỗi Excel", "Không có dữ liệu hợp lệ.")
             return None

        df['SBD'] = df['SBD'].astype(str).str.strip()
        if df['SBD'].duplicated().any():
            duplicates = df[df['SBD'].duplicated()]['SBD'].tolist()
            messagebox.showwarning("SBD trùng", f"SBD trùng lặp:\n{', '.join(duplicates)}")

        df.set_index('SBD', inplace=True, verify_integrity=False)
        print(f"Loaded {len(df)} students from {STUDENT_DATA_FILE}")
        return df

    except FileNotFoundError:
        messagebox.showerror("Lỗi", f"Không tìm thấy file: {STUDENT_DATA_FILE}")
        return None
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi đọc file Excel '{STUDENT_DATA_FILE}':\n{e}")
        return None

def get_student_info(student_sbd, df_students):
    """Lấy Họ và tên, Ngày sinh từ DataFrame."""
    if df_students is None or student_sbd not in df_students.index:
        return None, None
    try:
        record = df_students.loc[student_sbd]
        if isinstance(record, pd.DataFrame): record = record.iloc[0]
        name = record.get('Họ và tên', None)
        dob = record.get('Ngày sinh', None)
        # Trả về dob dạng string gốc từ Excel, xử lý NaT thành None
        return name, str(dob) if pd.notna(dob) else None
    except Exception as e:
        print(f"Lỗi lấy thông tin SBD {student_sbd}: {e}")
        return None, None

def get_classes(df_students):
    if df_students is None or 'Lớp' not in df_students.columns: return []
    try:
        classes = sorted([str(cls).strip() for cls in df_students['Lớp'].dropna().unique() if str(cls).strip()])
        return classes
    except Exception as e: print(f"Lỗi lấy danh sách lớp: {e}"); return []

def load_attendance_data():
    try:
        if not os.path.exists(ATTENDANCE_FILE) or os.path.getsize(ATTENDANCE_FILE) == 0: return []
        with open(ATTENDANCE_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        if isinstance(data, list):
            valid = [r for r in data if isinstance(r, dict) and all(k in r for k in ["sbd", "timestamp", "context", "date"])]
            if len(valid) != len(data): print(f"Warning: Invalid records found in {ATTENDANCE_FILE}")
            return valid
        else: print(f"Warning: {ATTENDANCE_FILE} không chứa list."); save_attendance_data([]); return []
    except json.JSONDecodeError: print(f"Error: {ATTENDANCE_FILE} sai JSON."); messagebox.showwarning("Lỗi Điểm danh", f"{ATTENDANCE_FILE} lỗi.\nTạo file mới."); save_attendance_data([]); return []
    except Exception as e: messagebox.showerror("Lỗi", f"Lỗi đọc điểm danh '{ATTENDANCE_FILE}':\n{e}"); return []

def save_attendance_data(records):
    if not isinstance(records, list): print("Error: Attendance data không phải list."); return False
    try:
        valid = [r for r in records if isinstance(r, dict)]
        with open(ATTENDANCE_FILE, 'w', encoding='utf-8') as f: json.dump(valid, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(valid)} records to {ATTENDANCE_FILE}"); return True
    except Exception as e: print(f"Lỗi lưu điểm danh '{ATTENDANCE_FILE}': {e}"); messagebox.showerror("Lỗi", f"Lỗi lưu file điểm danh:\n{e}"); return False

def get_attendance_records(data, class_name=None, context=None, date_str=None):
    if not isinstance(data, list): return []
    filt = data
    try:
        if date_str: filt = [r for r in filt if r.get('date') == date_str]
        if context: filt = [r for r in filt if r.get('context') == context]
        if class_name and data and isinstance(data[0], dict) and 'class' in data[0]: # Check if 'class' key exists in records
            cn_lower = class_name.strip().lower()
            filt = [r for r in filt if r.get('class') and str(r.get('class')).strip().lower() == cn_lower]
        return filt
    except Exception as e: print(f"Lỗi lọc điểm danh: {e}"); return []

def get_attended_sbd_set(data, class_name=None, context=None, date_str=None):
    filt = get_attendance_records(data, class_name, context, date_str)
    return set(r.get('sbd') for r in filt if r.get('sbd'))

def get_absent_students(df_stu, class_name, att_data, context, date_str):
    if df_stu is None or 'Lớp' not in df_stu.columns: return []
    if not class_name: return []
    cn_lower = class_name.strip().lower()
    try:
        in_class = set(df_stu[df_stu['Lớp'].astype(str).str.strip().str.lower() == cn_lower].index)
        if not in_class: print(f"Warning: Không có HS nào thuộc lớp '{class_name}'."); return []
        attended = get_attended_sbd_set(att_data, class_name, context, date_str)
        absent = sorted(list(in_class - attended))
        try: absent.sort(key=lambda x: int(x) if x.isdigit() else x) # Sắp xếp số và chữ
        except ValueError: pass
        return absent
    except Exception as e: print(f"Lỗi tìm HS vắng '{class_name}': {e}"); return []

def is_student_already_attended(sbd, context, date_str, data):
    if not sbd or not context or not date_str or not isinstance(data, list): return False
    sbd_str = str(sbd).strip()
    return any(isinstance(r, dict) and r.get('sbd') == sbd_str and r.get('context') == context and r.get('date') == date_str for r in data)
def load_announcements():
    """Tải danh sách thông báo từ file JSON."""
    try:
        if not os.path.exists(ANNOUNCEMENTS_FILE) or os.path.getsize(ANNOUNCEMENTS_FILE) == 0:
            return []
        with open(ANNOUNCEMENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            # Có thể thêm kiểm tra cấu trúc từng record nếu cần
            return data
        else:
            print(f"Warning: {ANNOUNCEMENTS_FILE} không chứa một danh sách JSON. Tạo file mới.")
            save_announcements([]) # Tạo file rỗng nếu cấu trúc sai
            return []
    except json.JSONDecodeError:
        print(f"Error: {ANNOUNCEMENTS_FILE} chứa JSON không hợp lệ. Tạo file mới.")
        messagebox.showwarning("Lỗi Dữ liệu Thông báo", 
                               f"File {ANNOUNCEMENTS_FILE} bị lỗi hoặc không đúng định dạng.\n"
                               "Sẽ tạo một file dữ liệu thông báo mới.",
                               parent=None) # Không có parent cụ thể ở đây
        save_announcements([]) # Tạo file rỗng
        return []
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi đọc file thông báo '{ANNOUNCEMENTS_FILE}':\n{e}", parent=None)
        return []

def save_announcements(announcements_list):
    """Lưu danh sách thông báo vào file JSON."""
    if not isinstance(announcements_list, list):
        print("Error: Dữ liệu thông báo để lưu không phải là một danh sách.")
        return False
    try:
        # Đảm bảo mọi record trong list là dict (có thể thêm kiểm tra sâu hơn)
        valid_records = [r for r in announcements_list if isinstance(r, dict)]
        with open(ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(valid_records, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu {len(valid_records)} thông báo vào {ANNOUNCEMENTS_FILE}")
        return True
    except Exception as e:
        print(f"Lỗi khi lưu file thông báo '{ANNOUNCEMENTS_FILE}': {e}")
        messagebox.showerror("Lỗi Lưu", f"Không thể lưu file thông báo:\n{e}", parent=None)
        return False

def generate_announcement_id(author_id):
    """Tạo ID duy nhất cho thông báo."""
    # Sử dụng timestamp kết hợp với author_id để tăng tính duy nhất
    # và thêm một chút ngẫu nhiên để tránh trùng lặp nếu đăng quá nhanh
    import random
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    random_suffix = random.randint(100, 999)
    return f"ann_{timestamp_ms}_{author_id}_{random_suffix}"
# Trong utils.py

def load_schedule():
    """Tải danh sách lịch trình sự kiện từ file JSON."""
    try:
        if not os.path.exists(SCHEDULE_FILE) or os.path.getsize(SCHEDULE_FILE) == 0:
            return [] # Trả về list rỗng nếu file không tồn tại hoặc rỗng
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            # Nên thêm kiểm tra cấu trúc từng record nếu cần độ chính xác cao
            # Ví dụ: kiểm tra sự tồn tại của các key bắt buộc như 'id', 'title', 'date'
            # valid_records = [r for r in data if isinstance(r, dict) and all(k in r for k in ['id', 'title', 'date'])]
            # if len(valid_records) != len(data):
            #     print(f"Warning: Một số bản ghi trong {SCHEDULE_FILE} không hợp lệ.")
            # return valid_records
            return data # Trả về dữ liệu đã load
        else:
            print(f"Warning: {SCHEDULE_FILE} không chứa một danh sách JSON. Tạo file mới.")
            save_schedule([]) # Tạo file rỗng nếu cấu trúc sai
            return []
    except json.JSONDecodeError:
        print(f"Error: {SCHEDULE_FILE} chứa JSON không hợp lệ. Tạo file mới.")
        # Không nên hiển thị messagebox từ utils mà nên để tầng gọi xử lý
        save_schedule([]) # Tạo file rỗng
        return [] # Trả về list rỗng để ứng dụng không crash
    except Exception as e:
        print(f"Error: Lỗi khi đọc file lịch trình '{SCHEDULE_FILE}': {e}")
        # Có thể raise lại lỗi hoặc trả về list rỗng tùy cách xử lý mong muốn
        return []

def save_schedule(schedule_list):
    """Lưu danh sách lịch trình sự kiện vào file JSON."""
    if not isinstance(schedule_list, list):
        print("Error: Dữ liệu lịch trình để lưu không phải là một danh sách.")
        return False
    try:
        # Đảm bảo mọi record trong list là dict (có thể thêm kiểm tra sâu hơn)
        valid_records = [r for r in schedule_list if isinstance(r, dict)]
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(valid_records, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu {len(valid_records)} sự kiện vào {SCHEDULE_FILE}")
        return True
    except Exception as e:
        print(f"Lỗi khi lưu file lịch trình '{SCHEDULE_FILE}': {e}")
        # Không nên hiển thị messagebox từ utils
        return False

def generate_event_id(creator_id):
    """Tạo ID duy nhất cho sự kiện."""
    import random
    timestamp_ms = int(datetime.now().timestamp() * 1000)
    random_suffix = random.randint(100, 999)
    # Thêm tiền tố 'evt_' để phân biệt với id của thông báo
    return f"evt_{timestamp_ms}_{creator_id}_{random_suffix}"

def load_school_config():
    default_config = {
        "dept_name": EDUCATION_DEPT_NAME, # Sử dụng hằng số làm mặc định
        "school_name": SCHOOL_NAME,
        "logo_path": LOGO_PATH 
    }
    try:
        if os.path.exists(SCHOOL_CONFIG_FILE):
            with open(SCHOOL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Đảm bảo tất cả các key đều có, nếu không thì dùng giá trị mặc định
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Lỗi tải school_config.json: {e}")
    return default_config # Trả về mặc định nếu có lỗi hoặc file không tồn tại

def save_school_config(config_data):
    try:
        with open(SCHOOL_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Lỗi Lưu", f"Không thể lưu cấu hình trường học:\n{e}")
        return False

# Hàm format ngày sinh (nếu chưa có hoặc muốn dùng chung)
def format_date_dmy(date_string):
    if not date_string or pd.isna(date_string): return ""
    # Cố gắng xử lý các định dạng phổ biến mà Pandas/Excel có thể đọc
    # (datetime objects, strings like 'YYYY-MM-DD HH:MM:SS', 'DD/MM/YYYY', etc.)
    if isinstance(date_string, datetime):
        return date_string.strftime("%d/%m/%Y")
    
    date_str_cleaned = str(date_string).split(" ")[0] # Lấy phần ngày nếu có cả giờ
    possible_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y", "%d-%B-%Y"]
    for fmt in possible_formats:
        try:
            date_obj = datetime.strptime(date_str_cleaned.strip(), fmt)
            return date_obj.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return str(date_string).strip() # Trả lại string gốc nếu không parse được

# Trong utils.py
# ... (các hằng số như EDUCATION_DEPT_NAME, SCHOOL_NAME vẫn giữ) ...
def load_school_config():
    default_config = {
        "dept_name": EDUCATION_DEPT_NAME,
        "school_name": SCHOOL_NAME,
        "logo_path": None,
        "school_logo_on_card_path": None,
        "school_address": "Địa chỉ: ....................................", # NEW Default
        "school_year": f"{datetime.now().year}-{datetime.now().year+1}", # NEW Default
        "card_issuing_place": ".........................", # NEW Default
        "card_issuer_name": "........................." # NEW Default
    }
    try:
        if os.path.exists(SCHOOL_CONFIG_FILE):
            with open(SCHOOL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Đảm bảo tất cả các key đều có, nếu không thì dùng giá trị mặc định
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Lỗi tải school_config.json: {e}. Sử dụng cấu hình mặc định.")
    return default_config # Trả về mặc định nếu có lỗi hoặc file không tồn tại