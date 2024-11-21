import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import io
import base64
from flask import Flask, jsonify, request
from flask_restx import Api, Resource
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 한글 글꼴 설정
font_path = "C:/Windows/Fonts/malgun.ttf"  # Windows의 경우 "맑은 고딕" 경로
font = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font)

# Flask 앱 초기화
app = Flask(__name__)

# CORS 설정
CORS(app)

# Flask-RESTx API 초기화
api = Api(
    app,
    version='1.0',
    title='Bike Station API',
    description='자치구 기반 대여소 정보를 제공하는 API',
)

# 네임스페이스 생성
bike_ns = api.namespace('bike', description='자치구 검색 API')

# SQLAlchemy 데이터베이스 연결
DATABASE_URL = 'mysql+pymysql://admin_bike:1234@localhost/bike?charset=utf8mb4'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

@bike_ns.route('/chart')
class Chart(Resource):
    @api.doc(params={'district': '자치구 이름'})
    def get(self):
        """
        자치구 이름으로 대여소 거치대수를 차트로 반환합니다.
        """
        district = request.args.get('district')
        if not district:
            return {"message": "자치구 이름을 입력해야 합니다."}, 400

        # 데이터베이스에서 자치구 데이터 가져오기
        query = text("SELECT station_name, total_slots FROM bike_station WHERE district = :district")
        result = session.execute(query, {"district": district}).fetchall()

        if not result:
            return {"message": "해당 자치구에 대한 데이터가 없습니다."}, 404

        # 데이터 시각화 준비
        station_names = [row.station_name for row in result]
        total_slots = [row.total_slots for row in result]

        # 차트 생성
        plt.figure(figsize=(10, 6))
        plt.barh(station_names, total_slots, color='skyblue')
        plt.title(f"{district} 거치대수 통계")
        plt.xlabel("거치대수")
        plt.ylabel("대여소 이름")

        # y축 레이블 회전 및 간격 조정
        plt.yticks(rotation=45)

        # y축 레이블 간격 조정
        plt.gca().yaxis.set_major_locator(plt.MaxNLocator(integer=True, prune='both', nbins=10))

        # 여백 조정
        plt.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=0.1)

        # 레이아웃 조정
        plt.tight_layout(pad=5.0)

        # 차트를 이미지로 변환
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        chart_data = base64.b64encode(img.getvalue()).decode('utf-8')
        img.close()

        return {"chart": chart_data}, 200


if __name__ == '__main__':
    app.run(debug=True)
