CREATE DATABASE IF NOT EXISTS database_cf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE database_cf;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'nhan_vien') DEFAULT 'nhan_vien',
    status ENUM('cho_duyet', 'da_duyet') DEFAULT 'cho_duyet',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Khach_hang (
    id int auto_increment primary key,
    ho_ten varchar(100) not null,
    so_dt varchar(20) unique not null,
    email varchar(100) unique,
    dia_chi text,
    lat_khach_hang float,
    long_khach_hang float,
    Ngay_rao datetime default current_timestamp
);

CREATE TABLE IF NOT EXISTS cua_hang (
    id int auto_increment primary key,
    ten_cua_hang varchar(50) not NULL,
    dia_chi TEXT,
    lat_cua_hang float,
    long_cua_hang float
);

CREATE TABLE IF NOT EXISTS san_pham (
    id int auto_increment primary key,
    ten_san_pham varchar(100) not null,
    loại_cf varchar(50),
    gia_ban decimal(10, 2),
    trang_thai enum('con_hang', 'het_hang') default 'con_hang',
    don_vi varchar(10) default 'kg'
);

CREATE TABLE IF NOT EXISTS don_hang (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_khach_hang int not null,
    id_cua_hang int not null,
    ngay_mua datetime default current_timestamp,
    trang_thai enum(
        'cho_xac_nhan',
        'dang_giao',
        'hoan_thanh',
        'huy'
    ) default 'cho_xac_nhan',
    tong_tien decimal(10, 2) not null,
    foreign key (id_khach_hang) references khach_hang (id),
    foreign key (id_cua_hang) references cua_hang (id)
);

CREATE TABLE IF NOT EXISTS chi_tiet_don_hang (
    id int auto_increment primary key,
    id_don_hang int not null,
    id_san_pham int not null,
    so_luong int not null,
    gia_ban decimal(10, 2) not null,
    foreign key (id_don_hang) references don_hang (id),
    foreign key (id_san_pham) references san_pham (id)
);

CREATE TABLE IF NOT EXISTS nguon_nguyen_lieu (
    id int auto_increment primary key,
    ten_nguyen_lieu varchar(100) not null,
    don_vi_tinh varchar(10)
);

CREATE TABLE IF NOT EXISTS kho_nguyen_lieu (
    id int auto_increment primary key,
    id_nguyen_lieu int not null,
    loai_giao_dich enum('nhap', 'xuat') not null,
    so_luong decimal(10, 2) not null,
    ngay_giao_dich datetime default current_timestamp,
    foreign key (id_nguyen_lieu) references nguon_nguyen_lieu (id)
);

CREATE TABLE IF NOT EXISTS san_xuat (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ten_lo varchar(100) not null,
    ngay_san_xuat DATE not null,
    san_luong decimal(10, 2) not null,
    trang_thai enum(
        'dang_sx',
        'hoan_thanh',
        'huy'
    ) default 'dang_sx'
);

CREATE TABLE IF NOT EXISTS chi_tiet_san_xuat (
    id int auto_increment primary key,
    id_san_xuat int not null,
    id_nguyen_lieu int not null,
    so_luong_dung decimal(10, 2) not null,
    don_vi_tinh varchar(10),
    foreign key (id_san_xuat) references san_xuat (id),
    foreign key (id_nguyen_lieu) references nguon_nguyen_lieu (id)
);

-- Dữ liệu khởi tạo mặc định
INSERT IGNORE INTO users (username, password, role, status) VALUES ('admin', '123456', 'admin', 'da_duyet');
INSERT IGNORE INTO cua_hang (id, ten_cua_hang, dia_chi) VALUES (1, 'Samba Coffee Central', 'Hà Nội');

DROP VIEW IF EXISTS ton_kho;
CREATE VIEW ton_kho AS
SELECT
    n.id as nguyen_lieu_id,
    n.ten_nguyen_lieu,
    n.don_vi_tinh,
    coalesce(
        sum(
            CASE
                WHEN k.loai_giao_dich = 'nhap' THEN k.so_luong
                WHEN k.loai_giao_dich = 'xuat' THEN - k.so_luong
            END
        ),
        0
    ) as ton_hien_tai
from
    nguon_nguyen_lieu n
    left join kho_nguyen_lieu k on n.id = k.id_nguyen_lieu
group by
    n.id,
    n.ten_nguyen_lieu,
    n.don_vi_tinh;