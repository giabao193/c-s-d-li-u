import os
import mysql.connector

def import_sql():
    # Railway sẽ tự động điền các thông số này thông qua tab Variables
    db_config = {
        "host": os.getenv("MYSQLHOST", "localhost"),
        "user": os.getenv("MYSQLUSER", "root"),
        "password": os.getenv("MYSQLPASSWORD", ""),
        "port": int(os.getenv("MYSQLPORT", 3306))
    }

    try:
        print(f"Đang kết nối tới MySQL tại {db_config['host']}...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        print("Đang đọc file database.sql...")
        with open('database.sql', 'r', encoding='utf-8') as f:
            sql_commands = f.read().split(';')

        print("Đang thực hiện các câu lệnh SQL...")
        for command in sql_commands:
            if command.strip():
                try:
                    cursor.execute(command)
                except Exception as e:
                    print(f"Bỏ qua câu lệnh lỗi: {e}")

        conn.commit()
        print("------------------------------------------")
        print("CHÚC MỪNG! Đã Import Database THÀNH CÔNG.")
        print("Tên Database của bạn là: database_cf")
        print("------------------------------------------")
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"LỖI: {e}")