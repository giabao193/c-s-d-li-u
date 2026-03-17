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
db_pool = None
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=10,
        **db_config
    )
    print("✅ Đã khởi tạo Connection Pool thành công!")
    
    def init_db():
        conn = db_pool.get_connection()
        cursor = conn.cursor()
        try:
            with open('database.sql', 'r', encoding='utf-8') as f:
                content = f.read()
                # Loại bỏ các lệnh CREATE DATABASE và USE để tránh lỗi trên Railway
                sql_commands = content.split(';')
                for cmd in sql_commands:
                    clean_cmd = cmd.strip()
                    if clean_cmd and not clean_cmd.upper().startswith(('CREATE DATABASE', 'USE')):
                        cursor.execute(clean_cmd)
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

def get_db_connection():
    if db_pool:
        try: return db_pool.get_connection()
        except: return None
    return None

# ==========================================
# --- TẤT CẢ API PHẢI NẰM Ở ĐÂY (TRÊN CÙNG) ---
# ==========================================

@app.route('/api/login', methods=['POST'])
def login():
    try:
        d = request.json
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "Lỗi DB"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (d['tk'], d['mk']))
        u = cursor.fetchone()
        if u:
            if u.get('status') == 'cho_duyet': return jsonify({"success": False, "message": "Chờ duyệt"}), 401
            return jsonify({"success": True, "user": {"tk": u['username'], "quyen": u['role']}})
        return jsonify({"success": False, "message": "Sai tài khoản hoặc mật khẩu"}), 401
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500
    finally: 
        if 'conn' in locals() and conn: conn.close()

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

@app.route('/api/khach-hang')
def get_kh():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, ho_ten, so_dt, email, DATE_FORMAT(Ngay_rao, '%d/%m/%Y') as Ngay_rao FROM khach_hang ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    finally: conn.close()

@app.route('/api/khach-hang/add', methods=['POST'])
def add_kh():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO khach_hang (ho_ten, so_dt, email) VALUES (%s, %s, %s)", (d['hoten'], d['sdt'], d.get('email', '')))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

@app.route('/api/khach-hang/delete', methods=['POST'])
def delete_kh():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chi_tiet_don_hang WHERE id_don_hang IN (SELECT id FROM don_hang WHERE id_khach_hang = %s)", (d['id'],))
        cursor.execute("DELETE FROM don_hang WHERE id_khach_hang = %s", (d['id'],))
        cursor.execute("DELETE FROM khach_hang WHERE id = %s", (d['id'],))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

@app.route('/api/san-pham')
def get_sp():
    conn = get_db_connection()
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
        cursor.execute("INSERT INTO san_pham (ten_san_pham, loai_cf, gia_ban, don_vi) VALUES (%s, %s, %s, %s)", (d['ten'], d['loai'], d['gia'], d['donvi']))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

@app.route('/api/san-pham/delete', methods=['POST'])
def delete_sp():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chi_tiet_don_hang WHERE id_san_pham = %s", (d['id'],))
        cursor.execute("DELETE FROM san_pham WHERE id = %s", (d['id'],))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

@app.route('/api/don-hang')
def get_don_hang():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT d.id, k.ho_ten as khach_hang, DATE_FORMAT(d.ngay_mua, '%d/%m/%Y %H:%i') as ngay, d.tong_tien, d.trang_thai FROM don_hang d JOIN khach_hang k ON d.id_khach_hang = k.id ORDER BY d.id DESC")
        return jsonify(cursor.fetchall())
    finally: conn.close()

@app.route('/api/don-hang/add', methods=['POST'])
def add_don_hang():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO don_hang (id_khach_hang, id_cua_hang, tong_tien, trang_thai) VALUES (%s, 1, %s, 'hoan_thanh')", (d['id_khach'], d['tong_tien']))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

@app.route('/api/kho')
def get_kho():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, ma_hang as ma, ten_nguyen_lieu as ten, ton_kho as ton, muc_bao_dong as min FROM nguon_nguyen_lieu ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    finally: conn.close()

@app.route('/api/kho/add', methods=['POST'])
def add_kho_direct():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO nguon_nguyen_lieu (ma_hang, ten_nguyen_lieu, ton_kho, muc_bao_dong) VALUES (%s, %s, %s, %s)", (d['ma'], d['ten'], d['ton'], d['min']))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

@app.route('/api/kho/delete', methods=['POST'])
def delete_kho_item():
    d = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM nguon_nguyen_lieu WHERE ma_hang = %s", (d['ma'],))
        res = cursor.fetchone()
        if res:
            cursor.execute("DELETE FROM kho_nguyen_lieu WHERE id_nguyen_lieu = %s", (res[0],))
            cursor.execute("DELETE FROM chi_tiet_san_xuat WHERE id_nguyen_lieu = %s", (res[0],))
            cursor.execute("DELETE FROM nguon_nguyen_lieu WHERE id = %s", (res[0],))
            conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

@app.route('/api/doanh-thu')
def get_doanh_thu():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DATE_FORMAT(ngay_mua, '%d/%m/%Y') as ngay, SUM(tong_tien) as tien FROM don_hang WHERE trang_thai = 'hoan_thanh' GROUP BY ngay ORDER BY ngay DESC")
        res = cursor.fetchall()
        for r in res: r['tien'] = float(r['tien']) if r['tien'] else 0
        return jsonify(res)
    finally: conn.close()

# ==========================================
# --- PHỤC VỤ FILE TĨNH (PHẢI NẰM Ở CUỐI) ---
# ==========================================

@app.route('/')
def h(): return send_from_directory('.', 'index.html')

@app.route('/<path:p>')
def s(p): return send_from_directory('.', p)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)