from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# 데이터베이스 기본 설정
Base = declarative_base()

class Admin(Base):
    __tablename__ = 'admin'  # 테이블 이름
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String(100), nullable=False, unique=True)
    admin_passwd = Column(String(100), nullable=False)

# 데이터베이스 연결
engine = create_engine('mysql+pymysql://admin_bike:1234@localhost/bike?charset=utf8mb4')  # DB 연결 문자열
Base.metadata.create_all(engine)  # 테이블 생성
Session = sessionmaker(bind=engine)
session = Session()
