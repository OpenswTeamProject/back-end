from flask import Flask, jsonify, request, Response
from flask_restx import Api, Resource, fields
from flask_cors import CORS
import pymysql
import json  # JSON 처리 모듈 추가

app = Flask(__name__)
CORS(app)

api = Api(app, version="1.0", title="Bike API", description="Flask RESTx API with MySQL")

db_config = {
    "host": "localhost",
    "user": "admin_bike",
    "password": "1234",
    "database": "bike",
    "charset": "utf8mb4"  # UTF-8 설정
}

bike_ns = api.namespace("stations", description="Bike Station API")

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
        try:
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()

            # SQL 쿼리
            query = """
                SELECT station_id, station_name, district AS region, address_detail AS address
                FROM bike_station
                WHERE station_name LIKE %s OR district LIKE %s OR address_detail LIKE %s
            """
            cursor.execute(query, (f"%{search}%", f"%{search}%", f"%{search}%"))
            result = cursor.fetchall()

            # 데이터 변환
            stations = [
                {
                    "station_id": row[0],
                    "station_name": row[1],
                    "region": row[2],
                    "address": row[3]
                }
                for row in result
            ]

            # JSON 반환 (ensure_ascii=False 추가)
            return Response(
                json.dumps({"stations": stations}, ensure_ascii=False),
                content_type="application/json; charset=utf-8"
            )
        except Exception as e:
            api.abort(500, f"MySQL 데이터베이스 오류: {str(e)}")
        finally:
            cursor.close()
            connection.close()




@bike_ns.route('/<int:station_id>')
class SingleStation(Resource):
    @api.doc(description="특정 대여소 정보를 반환합니다.")
    @api.marshal_with(station_model)
    def get(self, station_id):
        """
        주어진 대여소 ID에 해당하는 정보를 반환합니다.
        """
        try:
            # MySQL 연결
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()

            # SQL 쿼리 실행
            query = "SELECT station_id, station_name, district AS region, address_detail AS address FROM bike_station WHERE station_id = %s;"
            cursor.execute(query, (station_id,))
            row = cursor.fetchone()

            if not row:
                api.abort(404, f"대여소 ID {station_id}에 해당하는 데이터가 없습니다.")

            # 결과를 JSON 형태로 변환
            station = {
                "station_id": row[0],
                "station_name": row[1],
                "region": row[2],  # district -> region으로 매핑
                "address": row[3]  # address_detail -> address로 매핑
            }

            return station  # 반환
        except Exception as e:
            api.abort(500, f"MySQL 데이터베이스 오류: {str(e)}")
        finally:
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)
