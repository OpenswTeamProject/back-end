from flask import Flask, request, Response
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import json  # JSON 처리 모듈 추가

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
bike_ns = api.namespace('stations', description='Bike Station API')

# SQLAlchemy 데이터베이스 연결
DATABASE_URL = 'mysql+pymysql://root:1234@localhost/bike?charset=utf8mb4'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# RESTx 모델 정의
station_model = api.model("Station", {
    "station_id": fields.Integer(description="Station ID"),
    "station_name": fields.String(description="Station Name"),
    "region": fields.String(description="Region"),
    "address": fields.String(description="Address")
})


@bike_ns.route('/')
class StationList(Resource):
    @api.doc(params={"search": "검색어"})
    def get(self):
        search = request.args.get("search", "")
        session = Session()
        try:
            # SQLAlchemy를 사용한 SQL 쿼리
            query = text("""
                SELECT station_id, station_name, district AS region, address_detail AS address
                FROM bike_station
                WHERE station_name LIKE :search OR district LIKE :search OR address_detail LIKE :search
            """)
            result = session.execute(query, {"search": f"%{search}%"}).fetchall()

            # 결과를 JSON 형태로 변환
            stations = [
                {
                    "station_id": row.station_id,
                    "station_name": row.station_name,
                    "region": row.region,
                    "address": row.address
                }
                for row in result
            ]

            return Response(
                json.dumps({"stations": stations}, ensure_ascii=False),
                content_type="application/json; charset=utf-8"
            )
        except SQLAlchemyError as e:
            api.abort(500, f"SQLAlchemy 데이터베이스 오류: {str(e)}")
        finally:
            session.close()


@bike_ns.route('/<int:station_id>')
class SingleStation(Resource):
    @api.doc(description="특정 대여소 정보를 반환합니다.")
    @api.marshal_with(station_model)
    def get(self, station_id):
        session = Session()
        try:
            # SQLAlchemy를 사용한 SQL 쿼리
            query = text("""
                SELECT station_id, station_name, district AS region, address_detail AS address
                FROM bike_station
                WHERE station_id = :station_id
            """)
            result = session.execute(query, {"station_id": station_id}).fetchone()

            if not result:
                api.abort(404, f"대여소 ID {station_id}에 해당하는 데이터가 없습니다.")

            return {
                "station_id": result.station_id,
                "station_name": result.station_name,
                "region": result.region,
                "address": result.address
            }
        except SQLAlchemyError as e:
            api.abort(500, f"SQLAlchemy 데이터베이스 오류: {str(e)}")
        finally:
            session.close()


@bike_ns.route('/stations')
class Stations(Resource):
    @api.doc(params={'district': '자치구 이름'})
    def get(self):
        district = request.args.get('district')
        if not district:
            return {"message": "자치구 이름을 입력해야 합니다."}, 400

        session = Session()
        try:
            query = text("""
                SELECT station_name
                FROM bike_station
                WHERE district = :district
            """)
            result = session.execute(query, {"district": district}).fetchall()

            if not result:
                return {"message": "해당 자치구에 대한 대여소 데이터가 없습니다."}, 404

            station_names = [row.station_name for row in result]

            return {"stations": station_names}, 200
        except SQLAlchemyError as e:
            return {"message": f"SQLAlchemy 데이터베이스 오류: {str(e)}"}, 500
        finally:
            session.close()


@bike_ns.route('/station_info')
class StationInfo(Resource):
    @api.doc(params={'station': '대여소 이름'})
    def get(self):
        station = request.args.get('station')
        if not station:
            return {"message": "대여소 이름을 입력해야 합니다."}, 400

        session = Session()
        try:
            query = text("""
                SELECT station_name, total_slots
                FROM bike_station
                WHERE station_name = :station
                LIMIT 1
            """)
            result = session.execute(query, {"station": station}).fetchone()

            if not result:
                return {"message": "해당 대여소에 대한 데이터가 없습니다."}, 404

            station_name = result.station_name
            total_slots = result.total_slots

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
            return {"message": f"SQLAlchemy 데이터베이스 오류: {str(e)}"}, 500
        finally:
            session.close()


if __name__ == '__main__':
    app.run(debug=True)
