FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# MySQL 클라이언트 도구 설치
RUN apt-get update && apt-get install -y default-mysql-client

# 종속성 복사 및 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Flask 애플리케이션 실행
CMD ["bash", "-c", "until mysqladmin ping -h mysql --silent; do echo 'Waiting for MySQL...'; sleep 2; done && python flask_app/DB_model.py && python flask_app/app.py"]
