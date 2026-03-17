from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
from mysql.connector import pooling
import os

app = Flask(__name__)

# Cấu hình Database
db_config = {
    "host": os.environ.get("MYSQLHOST", "localhost"),
    "user": os.environ.get("MYSQLUSER", "root"),
    "password": os.environ.get("MYSQLPASSWORD", ""),
    "database": os.environ.get("MYSQLDATABASE", "database_cf"),
    "port": int(os.environ.get("MYSQLPORT", 3306))
}

# Tạo Connection Pool
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=10,
        **db_config
    )
    print("✅ Đã khởi tạo Connection Pool thành công!")
    
    # Tự động khởi tạo database nếu chưa có bảng
    def init_db():
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        try:
            with open('database.sql', 'r', encoding='utf-8') as f:
                sql_commands = f.read().split(';')
                for cmd in sql_commands:
                    if cmd.strip():
                        cursor.execute(cmd)
            conn.commit()
            print("✅ Đã khởi tạo/cập nhật Database thành công!")
        except Exception as e:
            print(f"⚠️ Cảnh báo khởi tạo DB: {e}")
        finally:
            cursor.close()
            conn.close()
    
    init_db()

except mysql.connector.Error as err:
    print(f"❌ Lỗi khởi tạo DB Pool: {err}")
    db_pool = None

def get_db_connection():
    if db_pool:
        try:
            return db_pool.get_connection()
        except:
            return None
    return None

# --- API TÀI KHOẢN ---
@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"message": "Lỗi DB"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (d['tk'], d['mk']))
        u = cursor.fetchone()
        if u:
            if u.get('status') == 'cho_duyet': return jsonify({"message": "Chờ duyệt"}), 401
            return jsonify({"success": True, "user": {"tk": u['username'], "quyen": u['role']}})
        return jsonify({"success": False}), 401
    finally: conn.close()

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, status, role) VALUES (%s, %s, 'cho_duyet', 'nhan_vien')", (d['tk'], d['mk']))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

# --- API KHÁCH HÀNG (Đã sửa Khach_hang -> khach_hang) ---
@app.route('/api/khach-hang')
def get_kh():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        # Sửa lỗi viết hoa Khach_hang thành viết thường
        cursor.execute("SELECT id, ho_ten, so_dt, email, DATE_FORMAT(Ngay_rao, '%d/%m/%Y') as Ngay_rao FROM khach_hang ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    finally: conn.close()

@app.route('/api/khach-hang/add', methods=['POST'])
def add_kh():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Sửa lỗi viết hoa Khach_hang
        cursor.execute("INSERT INTO khach_hang (ho_ten, so_dt, email) VALUES (%s, %s, %s)", 
                       (d['hoten'], d['sdt'], d.get('email', '')))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 400
    finally: conn.close()

@app.route('/api/khach-hang/delete', methods=['POST'])
def delete_kh():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 1. Xóa chi tiết đơn hàng của các đơn hàng thuộc khách này
        cursor.execute("""
            DELETE FROM chi_tiet_don_hang 
            WHERE id_don_hang IN (SELECT id FROM don_hang WHERE id_khach_hang = %s)
        """, (d['id'],))
        
        # 2. Xóa các đơn hàng của khách này
        cursor.execute("DELETE FROM don_hang WHERE id_khach_hang = %s", (d['id'],))
        
        # 3. Cuối cùng mới xóa khách hàng
        cursor.execute("DELETE FROM khach_hang WHERE id = %s", (d['id'],))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}), 400
    finally: conn.close()

# --- API SẢN PHẨM (Đã sửa loại_cf -> loai_cf) ---
@app.route('/api/san-pham')
def get_sp():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM san_pham ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    finally: conn.close()

@app.route('/api/san-pham/add', methods=['POST'])
def add_sp():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Sửa lỗi loại_cf (có dấu) thành loai_cf (không dấu)
        cursor.execute("INSERT INTO san_pham (ten_san_pham, loai_cf, gia_ban, don_vi) VALUES (%s, %s, %s, %s)", 
                       (d['ten'], d['loai'], d['gia'], d['donvi']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 400
    finally: conn.close()

# --- API ĐƠN HÀNG ---
@app.route('/api/don-hang')
def get_don_hang():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT d.id, k.ho_ten as khach_hang, DATE_FORMAT(d.ngay_mua, '%d/%m/%Y %H:%i') as ngay, 
                   d.tong_tien, d.trang_thai 
            FROM don_hang d
            JOIN khach_hang k ON d.id_khach_hang = k.id
            ORDER BY d.id DESC
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall())
    finally: conn.close()

@app.route('/api/don-hang/add', methods=['POST'])
def add_don_hang():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Mặc định id_cua_hang = 1 (Samba Coffee Central)
        cursor.execute("""
            INSERT INTO don_hang (id_khach_hang, id_cua_hang, tong_tien, trang_thai) 
            VALUES (%s, 1, %s, 'hoan_thanh')
        """, (d['id_khach'], d['tong_tien']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}), 400
    finally: conn.close()

# --- PHỤC VỤ FILE ---
@app.route('/')
def h(): return send_from_directory('.', 'index.html')
@app.route('/<path:p>')
def s(p): return send_from_directory('.', p)

# --- API DOANH THU ---
@app.route('/api/doanh-thu')
def get_doanh_thu():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        # Lấy doanh thu theo ngày để hiển thị dạng mảng
        cursor.execute("""
            SELECT DATE_FORMAT(ngay_mua, '%d/%m/%Y') as ngay, SUM(tong_tien) as tien 
            FROM don_hang 
            WHERE trang_thai = 'hoan_thanh'
            GROUP BY ngay ORDER BY ngay DESC
        """)
        res = cursor.fetchall()
        # Chuyển đổi Decimal sang float để JSON có thể serialize
        for r in res:
            r['tien'] = float(r['tien']) if r['tien'] else 0
        return jsonify(res)
    finally: conn.close()

@app.route('/api/doanh-thu/bieu-do')
def get_bieu_do():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Thống kê doanh thu theo ngày
        cursor.execute("""
            SELECT DATE_FORMAT(ngay_mua, '%d/%m') as ngay, SUM(tong_tien) as doanh_thu 
            FROM don_hang 
            WHERE trang_thai = 'hoan_thanh'
            GROUP BY ngay ORDER BY ngay ASC LIMIT 7
        """)
        return jsonify(cursor.fetchall())
    finally: conn.close()

# --- API KHO HÀNG (Lưu trực tiếp) ---
@app.route('/api/kho')
def get_kho():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Lấy trực tiếp từ bảng nguon_nguyen_lieu
        cursor.execute("SELECT id, ma_hang as ma, ten_nguyen_lieu as ten, ton_kho as ton, muc_bao_dong as min FROM nguon_nguyen_lieu ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    finally: conn.close()

@app.route('/api/kho/add', methods=['POST'])
def add_kho_direct():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Lưu thẳng: mã, tên, tồn, mức báo động
        cursor.execute("""
            INSERT INTO nguon_nguyen_lieu (ma_hang, ten_nguyen_lieu, ton_kho, muc_bao_dong) 
            VALUES (%s, %s, %s, %s)
        """, (d['ma'], d['ten'], d['ton'], d['min']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: 
        return jsonify({"success": False, "error": str(e)}), 400
    finally: conn.close()

@app.route('/api/kho/delete', methods=['POST'])
def delete_kho_item():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 1. Tìm ID của nguyên liệu dựa trên mã hàng
        cursor.execute("SELECT id FROM nguon_nguyen_lieu WHERE ma_hang = %s", (d['ma'],))
        res = cursor.fetchone()
        if res:
            # 2. Xóa các giao dịch liên quan trong kho_nguyen_lieu
            cursor.execute("DELETE FROM kho_nguyen_lieu WHERE id_nguyen_lieu = %s", (res[0],))
            # 3. Xóa các chi tiết sản xuất liên quan
            cursor.execute("DELETE FROM chi_tiet_san_xuat WHERE id_nguyen_lieu = %s", (res[0],))
            # 4. Cuối cùng mới xóa trong nguon_nguyen_lieu
            cursor.execute("DELETE FROM nguon_nguyen_lieu WHERE id = %s", (res[0],))
            conn.commit()
        return jsonify({"success": True})
    except Exception as e: 
        return jsonify({"success": False, "error": str(e)}), 400
    finally: conn.close()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)