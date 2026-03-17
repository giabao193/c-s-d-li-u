from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
from mysql.connector import pooling
import os

app = Flask(__name__)

# Cấu hình Database - Tự động lấy từ Railway
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
except mysql.connector.Error as err:
    print(f"❌ Lỗi khởi tạo DB Pool: {err}")
    db_pool = None

def get_db_connection():
    if db_pool:
        try:
            return db_pool.get_connection()
        except mysql.connector.Error:
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
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally: conn.close()

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"success": False}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, status, role) VALUES (%s, %s, 'cho_duyet', 'nhan_vien')", (d['tk'], d['mk']))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

# --- API ADMIN ---
@app.route('/api/admin/users')
def get_users():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username as tk, role as quyen, status as trangThai FROM users WHERE username != 'admin'")
        res = cursor.fetchall()
        return jsonify(res)
    except: return jsonify([]), 500
    finally: conn.close()

@app.route('/api/admin/approve', methods=['POST'])
def approve():
    tk = request.json['tk']
    conn = get_db_connection()
    if not conn: return jsonify({"success": False}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'da_duyet' WHERE username = %s", (tk,))
        conn.commit()
        return jsonify({"success": True})
    finally: conn.close()

@app.route('/api/admin/delete-user', methods=['POST'])
def delete_user():
    tk = request.json['tk']
    conn = get_db_connection()
    if not conn: return jsonify({"success": False}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = %s", (tk,))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 400
    finally: conn.close()

# --- API KHÁCH HÀNG ---
@app.route('/api/khach-hang')
def get_kh():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, ho_ten, so_dt, email, DATE_FORMAT(Ngay_rao, '%d/%m/%Y') as Ngay_rao FROM Khach_hang ORDER BY id DESC")
        res = cursor.fetchall()
        return jsonify(res)
    finally: conn.close()

@app.route('/api/khach-hang/add', methods=['POST'])
def add_kh():
    d = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"success": False, "message": "Không thể kết nối Database"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Khach_hang (ho_ten, so_dt, email) VALUES (%s, %s, %s)", 
                       (d['hoten'], d['sdt'], d.get('email', '')))
        conn.commit()
        return jsonify({"success": True})
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return jsonify({"success": False, "message": "Số điện thoại hoặc Email đã tồn tại!"}), 400
        return jsonify({"success": False, "message": str(err)}), 400
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}), 500
    finally: conn.close()

@app.route('/api/khach-hang/delete', methods=['POST'])
def delete_kh():
    d = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"success": False, "message": "Không thể kết nối Database"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Khach_hang WHERE id = %s", (d['id'],))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 400
    finally: conn.close()

# --- API SẢN PHẨM ---
@app.route('/api/san-pham')
def get_sp():
    conn = get_db_connection()
    if not conn: return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM san_pham ORDER BY id DESC")
        res = cursor.fetchall()
        return jsonify(res)
    finally: conn.close()

@app.route('/api/san-pham/add', methods=['POST'])
def add_sp():
    d = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"success": False, "message": "Không thể kết nối Database"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO san_pham (ten_san_pham, loại_cf, gia_ban, don_vi) VALUES (%s, %s, %s, %s)", 
                       (d['ten'], d['loai'], d['gia'], d['donvi']))
        conn.commit()
        return jsonify({"success": True})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": str(err)}), 400
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}), 500
    finally: conn.close()

@app.route('/api/san-pham/delete', methods=['POST'])
def delete_sp():
    d = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"success": False, "message": "Không thể kết nối Database"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM san_pham WHERE id = %s", (d['id'],))
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
            JOIN Khach_hang k ON d.id_khach_hang = k.id
            ORDER BY d.id DESC
        """
        cursor.execute(query)
        res = cursor.fetchall()
        return jsonify(res)
    finally: conn.close()

@app.route('/api/don-hang/add', methods=['POST'])
def add_don_hang():
    d = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"success": False, "message": "Không thể kết nối Database"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO don_hang (id_khach_hang, id_cua_hang, tong_tien, trang_thai) 
            VALUES (%s, 1, %s, 'hoan_thanh')
        """, (d['id_khach'], d['tong_tien']))
        
        don_id = cursor.lastrowid
        
        if 'items' in d:
            for item in d['items']:
                cursor.execute("""
                    INSERT INTO chi_tiet_don_hang (id_don_hang, id_san_pham, so_luong, gia_ban)
                    VALUES (%s, %s, %s, %s)
                """, (don_id, item['id_sp'], item['sl'], item['gia']))
        
        conn.commit()
        return jsonify({"success": True})
    except mysql.connector.Error as err:
        if err.errno == 1452:
            return jsonify({"success": False, "message": "Lỗi: Không tìm thấy Khách hàng hoặc Cửa hàng (ID: 1)"}), 400
        return jsonify({"success": False, "message": str(err)}), 400
    except Exception as e: 
        return jsonify({"success": False, "message": str(e)}), 500
    finally: conn.close()


# --- PHỤC VỤ FILE ---
@app.route('/')
def h(): return send_from_directory('.', 'index.html')

@app.route('/<path:p>')
def s(p): return send_from_directory('.', p)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
