from flask import Flask, request, jsonify, send_from_directory
import mysql.connector
from mysql.connector import pooling
import os
import sys

app = Flask(__name__)

# Cấu hình Database từ môi trường
db_config = {
    "host": os.environ.get("MYSQLHOST", "localhost"),
    "user": os.environ.get("MYSQLUSER", "root"),
    "password": os.environ.get("MYSQLPASSWORD", ""),
    "database": os.environ.get("MYSQLDATABASE", "database_cf"),
    "port": int(os.environ.get("MYSQLPORT", 3306))
}

# Khởi tạo Pool toàn cục
db_pool = None
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=10,
        **db_config
    )
    
    def init_db():
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            if os.path.exists('database.sql'):
                with open('database.sql', 'r', encoding='utf-8') as f:
                    sql_commands = f.read().split(';')
                    for cmd in sql_commands:
                        clean_cmd = cmd.strip()
                        # Bỏ qua các lệnh tạo DB/chuyển DB trên Cloud
                        if clean_cmd and not clean_cmd.upper().startswith(('CREATE DATABASE', 'USE')):
                            try:
                                cursor.execute(clean_cmd)
                            except Exception as e:
                                print(f"Bỏ qua lệnh SQL lỗi: {e}")
                conn.commit()
            cursor.close()
            conn.close()
            print("✅ Database initialized.")
        except Exception as e:
            print(f"❌ DB Init Error: {e}")
            
    init_db()
except Exception as e:
    print(f"❌ Failed to setup DB Pool: {e}")

def get_db_connection():
    if db_pool:
        try:
            return db_pool.get_connection()
        except Exception as e:
            print(f"❌ Get Connection Error: {e}")
            return None
    return None

# --- API HELPERS ---
def error_json(msg, code=500):
    return jsonify({"success": False, "message": str(msg)}), code

# ==========================================
# --- CÁC ROUTE API (PHẢI ĐẶT TRƯỚC) ---
# ==========================================

@app.route('/api/login', methods=['POST'])
def login():
    conn = None
    try:
        data = request.get_json(silent=True)
        if not data: return error_json("Dữ liệu không hợp lệ", 400)
        
        tk = data.get('tk')
        mk = data.get('mk')
        
        conn = get_db_connection()
        if not conn: return error_json("Không thể kết nối Database", 500)
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, role, status FROM users WHERE username = %s AND password = %s", (tk, mk))
        user = cursor.fetchone()
        
        if user:
            if user['status'] == 'cho_duyet':
                return error_json("Tài khoản đang chờ duyệt", 401)
            return jsonify({
                "success": True, 
                "user": {"tk": user['username'], "quyen": user['role']}
            })
        
        return error_json("Sai tài khoản hoặc mật khẩu", 401)
    except Exception as e:
        return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/register', methods=['POST'])
def register():
    conn = None
    try:
        d = request.get_json(silent=True)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, status, role) VALUES (%s, %s, 'cho_duyet', 'nhan_vien')", (d['tk'], d['mk']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/khach-hang')
def get_kh():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, ho_ten, so_dt, email, DATE_FORMAT(Ngay_rao, '%d/%m/%Y') as Ngay_rao FROM khach_hang ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    except Exception as e: return jsonify([])
    finally:
        if conn: conn.close()

@app.route('/api/khach-hang/add', methods=['POST'])
def add_kh():
    conn = None
    try:
        d = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO khach_hang (ho_ten, so_dt, email) VALUES (%s, %s, %s)", (d['hoten'], d['sdt'], d.get('email', '')))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/khach-hang/delete', methods=['POST'])
def delete_kh():
    conn = None
    try:
        d = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chi_tiet_don_hang WHERE id_don_hang IN (SELECT id FROM don_hang WHERE id_khach_hang = %s)", (d['id'],))
        cursor.execute("DELETE FROM don_hang WHERE id_khach_hang = %s", (d['id'],))
        cursor.execute("DELETE FROM khach_hang WHERE id = %s", (d['id'],))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/san-pham')
def get_sp():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM san_pham ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    except Exception as e: return jsonify([])
    finally:
        if conn: conn.close()

@app.route('/api/san-pham/add', methods=['POST'])
def add_sp():
    conn = None
    try:
        d = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO san_pham (ten_san_pham, loai_cf, gia_ban, don_vi) VALUES (%s, %s, %s, %s)", (d['ten'], d['loai'], d['gia'], d['donvi']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/san-pham/delete', methods=['POST'])
def delete_sp():
    conn = None
    try:
        d = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chi_tiet_don_hang WHERE id_san_pham = %s", (d['id'],))
        cursor.execute("DELETE FROM san_pham WHERE id = %s", (d['id'],))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/don-hang')
def get_don_hang():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT d.id, k.ho_ten as khach_hang, DATE_FORMAT(d.ngay_mua, '%d/%m/%Y %H:%i') as ngay, d.tong_tien, d.trang_thai FROM don_hang d JOIN khach_hang k ON d.id_khach_hang = k.id ORDER BY d.id DESC")
        return jsonify(cursor.fetchall())
    except Exception as e: return jsonify([])
    finally:
        if conn: conn.close()

@app.route('/api/don-hang/add', methods=['POST'])
def add_don_hang():
    conn = None
    try:
        d = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO don_hang (id_khach_hang, id_cua_hang, tong_tien, trang_thai) VALUES (%s, 1, %s, 'hoan_thanh')", (d['id_khach'], d['tong_tien']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/kho')
def get_kho():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, ma_hang as ma, ten_nguyen_lieu as ten, ton_kho as ton, muc_bao_dong as min FROM nguon_nguyen_lieu ORDER BY id DESC")
        return jsonify(cursor.fetchall())
    except Exception as e: return jsonify([])
    finally:
        if conn: conn.close()

@app.route('/api/kho/add', methods=['POST'])
def add_kho_direct():
    conn = None
    try:
        d = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO nguon_nguyen_lieu (ma_hang, ten_nguyen_lieu, ton_kho, muc_bao_dong) VALUES (%s, %s, %s, %s)", (d['ma'], d['ten'], d['ton'], d['min']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/kho/delete', methods=['POST'])
def delete_kho_item():
    conn = None
    try:
        d = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM nguon_nguyen_lieu WHERE ma_hang = %s", (d['ma'],))
        res = cursor.fetchone()
        if res:
            cursor.execute("DELETE FROM kho_nguyen_lieu WHERE id_nguyen_lieu = %s", (res[0],))
            cursor.execute("DELETE FROM chi_tiet_san_xuat WHERE id_nguyen_lieu = %s", (res[0],))
            cursor.execute("DELETE FROM nguon_nguyen_lieu WHERE id = %s", (res[0],))
            conn.commit()
        return jsonify({"success": True})
    except Exception as e: return error_json(e)
    finally:
        if conn: conn.close()

@app.route('/api/doanh-thu')
def get_doanh_thu():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DATE_FORMAT(ngay_mua, '%d/%m/%Y') as ngay, SUM(tong_tien) as tien FROM don_hang WHERE trang_thai = 'hoan_thanh' GROUP BY ngay ORDER BY ngay DESC")
        res = cursor.fetchall()
        for r in res: r['tien'] = float(r['tien']) if r['tien'] else 0
        return jsonify(res)
    except Exception as e: return jsonify([])
    finally:
        if conn: conn.close()

# ==========================================
# --- PHỤC VỤ FILE TĨNH (PHẢI NẰM Ở CUỐI) ---
# ==========================================

@app.route('/')
def h(): return send_from_directory('.', 'index.html')

@app.route('/<path:p>')
def s(p):
    # Đảm bảo không phục vụ file tĩnh nếu đường dẫn bắt đầu bằng api/
    if p.startswith('api/'):
        return error_json("API endpoint not found", 404)
    return send_from_directory('.', p)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)#   V e r s i o n :   1 . 0 . 1  
 