from flask import Flask, request
from flask_restx import Api, Resource
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

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


@bike_ns.route('/stations')
class Stations(Resource):
    @api.doc(params={'district': '자치구 이름'})
    def get(self):
        """
        자치구 이름으로 해당 자치구의 모든 대여소 목록을 반환합니다.
        """
        district = request.args.get('district')
        if not district:
            return {"message": "자치구 이름을 입력해야 합니다."}, 400

        try:
            # 데이터베이스에서 자치구 데이터 가져오기
            query = text("SELECT station_name FROM bike_station WHERE district = :district")
            result = session.execute(query, {"district": district}).fetchall()

            if not result:
                return {"message": "해당 자치구에 대한 대여소 데이터가 없습니다."}, 404

            # 대여소 이름 목록 추출
            station_names = [row.station_name for row in result]

            return {"stations": station_names}, 200

        except SQLAlchemyError as e:
            return {"message": f"데이터베이스 오류: {str(e)}"}, 500


@bike_ns.route('/station_info')
class StationInfo(Resource):
    @api.doc(params={'station': '대여소 이름'})
    def get(self):
        """
        대여소 이름으로 대여소 거치대수와 근처 대여소 정보를 반환합니다.
        """
        station = request.args.get('station')
        if not station:
            return {"message": "대여소 이름을 입력해야 합니다."}, 400

        try:
            # 대여소 정보 가져오기
            query = text("""
                SELECT station_name, total_slots
                FROM bike_station
                WHERE station_name = :station
                LIMIT 1
            """)
            result = session.execute(query, {"station": station}).fetchone()

            if not result:
                return {"message": "해당 대여소에 대한 데이터가 없습니다."}, 404

            # 대여소 이름과 거치대 수 추출
            station_name = result.station_name
            total_slots = result.total_slots

            # 근처 대여소 데이터 가져오기
            nearby_query = text("""
                SELECT station_name, total_slots
                FROM bike_station
                WHERE district = (
                    SELECT district
                    FROM bike_station
                    WHERE station_name = :station
                    LIMIT 1
                )
                AND station_name != :station
                LIMIT 3
            """)
            nearby_result = session.execute(nearby_query, {"station": station}).fetchall()

            nearby_stations = [
                {"station_name": row.station_name, "total_slots": row.total_slots}
                for row in nearby_result
            ]

            return {
                "station_name": station_name,
                "total_slots": total_slots,
                "nearby_stations": nearby_stations
            }, 200

        except SQLAlchemyError as e:
            return {"message": f"데이터베이스 오류: {str(e)}"}, 500


if __name__ == '__main__':
    app.run(debug=True)
