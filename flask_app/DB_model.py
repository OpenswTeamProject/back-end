import os
import subprocess
from sqlalchemy import create_engine, Column, Integer, String, DOUBLE
from sqlalchemy.orm import declarative_base, sessionmaker
import pandas as pd
'''
db_password = '1234' # 본인의 MySQL DB root password 넣기

# init.sql 파일 실행
def execute_init_sql():
    init_sql_path = "../input_DB/init.sql"  # init.sql 파일 경로
    mysql_command = [
        "mysql", "-u", "root", f'$-p{db_password}',  # MySQL root 사용자와 비밀번호 입력
        "-e", f"source {init_sql_path}"
    ]
    try:
        subprocess.run(mysql_command, check=True)
        print("init.sql 스크립트가 성공적으로 실행되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"init.sql 실행 중 오류 발생: {e}")

execute_init_sql()
'''
# 데이터베이스 기본 설정
Base = declarative_base()

class Admin(Base):
    __tablename__ = 'admin'  # 테이블 이름
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String(100), nullable=False, unique=True)
    admin_passwd = Column(String(100), nullable=False)

class BikeStation(Base):
    __tablename__ = 'bike_station'  # 테이블 이름
    station_id = Column(Integer, primary_key=True, autoincrement=True)  # 고유 ID(PK)
    station_number = Column(Integer, nullable=False)                    # 대여소번호
    station_name = Column(String(255), nullable=False)                  # 보관소(대여소)명
    district = Column(String(100), nullable=False)                      # 자치구
    address_detail = Column(String(255), nullable=False)                # 상세주소
    latitude = Column(DOUBLE, nullable=False)                           # 위도
    longitude = Column(DOUBLE, nullable=False)                          # 경도
    total_slots = Column(Integer, nullable=False)                       # 거치대수 합계

# 데이터베이스 연결
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:1234@mysql:3306/bike?charset=utf8mb4')
engine = create_engine(DATABASE_URL, connect_args={"local_infile": True})
Base.metadata.create_all(engine)  # 테이블 생성
Session = sessionmaker(bind=engine)
session = Session()

# CSV 파일 읽기
csv_file = 'input_DB/bike_station.csv'
data = pd.read_csv(csv_file)

# 데이터 삽입
for index, row in data.iterrows():
    new_station = BikeStation(
        station_number=row['대여소번호'],
        station_name=row['보관소(대여소)명'],
        district=row['자치구'],
        address_detail=row['상세주소'],
        latitude=row['위도'],
        longitude=row['경도'],
        total_slots=row['거치대수 합계']
    )
    session.add(new_station)

session.commit()
print("데이터 삽입 완료!")
