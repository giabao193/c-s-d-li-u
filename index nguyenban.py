import mysql.connector

def import_sql():
    # Cấu hình kết nối (HÃY ĐẢM BẢO USER/PASSWORD ĐÚNG)
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": ""
    }

    try:
        print("Đang kết nối tới MySQL...")
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
        print("Hãy đảm bảo bạn đã bật XAMPP (MySQL) trước khi chạy!")

if __name__ == "__main__":
    import_sql()
