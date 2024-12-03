-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS bike CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자 생성 (존재하지 않을 경우)
CREATE USER IF NOT EXISTS 'admin_bike'@'%' IDENTIFIED BY '1234';

-- 권한 부여
GRANT ALL PRIVILEGES ON bike.* TO 'admin_bike'@'%';

-- 권한 변경 사항 적용
FLUSH PRIVILEGES;

USE bike;

-- 테이블 생성
CREATE TABLE IF NOT EXISTS bike_station (
    station_id INT NOT NULL AUTO_INCREMENT,      -- 고유 ID (PK)
    station_number INT NOT NULL,                -- 대여소번호
    station_name VARCHAR(255) NOT NULL,         -- 보관소(대여소)명
    district VARCHAR(100) NOT NULL,             -- 자치구
    address_detail VARCHAR(255) NOT NULL,       -- 상세주소
    latitude DOUBLE NOT NULL,                   -- 위도
    longitude DOUBLE NOT NULL,                  -- 경도
    total_slots INT NOT NULL,                   -- 거치대수 합계
    PRIMARY KEY (station_id)
);

-- CSV 데이터 로드
LOAD DATA LOCAL INFILE '/docker-entrypoint-initdb.d/bike_stations.csv'
INTO TABLE bike_station
FIELDS TERMINATED BY ','               -- 필드 구분자
ENCLOSED BY '"'                        -- 문자열 구분자
LINES TERMINATED BY '\n'               -- 행 구분자
IGNORE 1 ROWS                          -- 헤더 제외
(station_number, station_name, district, address_detail, latitude, longitude, total_slots);

