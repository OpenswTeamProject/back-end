-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS bike CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 생성 (존재하지 않을 경우)
CREATE USER IF NOT EXISTS 'admin_bike'@'%' IDENTIFIED BY '1234';

-- 권한 부여
GRANT ALL PRIVILEGES ON bike.* TO 'admin_bike'@'%';

-- 권한 변경 사항 적용
FLUSH PRIVILEGES;
