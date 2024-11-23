from flask import Flask, request, Response, jsonify
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import requests
import os
import json  # JSON 처리 모듈 추가
from datetime import datetime, timedelta
import pytz

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)

# Flask-RESTx API 초기화
api = Api(app, version="1.0", title="Bike & Weather API", description="통합된 자전거 대여소 및 날씨 API")

# SQLAlchemy 데이터베이스 연결
DATABASE_URL = 'mysql+pymysql://root:kkero0418@localhost/bike?charset=utf8mb4'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# OpenWeather API 키 설정 (환경 변수에서 가져오기)
API_KEY = os.getenv("b185176d52c5df5dd2b8d5ed23d1a75c", "b185176d52c5df5dd2b8d5ed23d1a75c")

# 네임스페이스 생성
bike_ns = api.namespace('stations', description='Bike Station API')
weather_ns = api.namespace('weather', description='Weather API')

# RESTx 모델 정의 (자전거 대여소)
station_model = api.model("Station", {
    "station_id": fields.Integer(description="Station ID"),
    "station_name": fields.String(description="Station Name"),
    "region": fields.String(description="Region"),
    "address": fields.String(description="Address")
})

# RESTx 모델 정의 (현재 날씨)
current_weather_model = api.model("CurrentWeather", {
    "latitude": fields.Float(description="위도"),
    "longitude": fields.Float(description="경도"),
    "city": fields.String(description="도시 이름"),
    "temperature": fields.Float(description="현재 온도 (°C)"),
    "humidity": fields.Float(description="습도 (%)"),
    "wind_speed": fields.Float(description="풍속 (m/s)"),
    "description": fields.String(description="날씨 설명"),
    "weather_icon": fields.String(description="날씨 아이콘 URL"),
})

# RESTx 모델 정의 (5일/3시간 예보)
forecast_model = api.model("Forecast", {
    "datetime": fields.String(description="예보 시간 (한국 시간)"),
    "temperature": fields.Float(description="온도 (°C)"),
    "humidity": fields.Float(description="습도 (%)"),
    "wind_speed": fields.Float(description="풍속 (m/s)"),
    "description": fields.String(description="날씨 설명"),
    "rain_volume": fields.Float(description="강수량 (mm)", default=0.0),
    "snow_volume": fields.Float(description="강설량 (mm)", default=0.0),
    "weather_icon": fields.String(description="날씨 아이콘 URL"),
})


# -------------------
# 자전거 대여소 API
# -------------------

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


# -------------------
# 날씨 API
# -------------------

@api.route('/weather/current')
class CurrentWeather(Resource):
    @api.doc(params={"lat": "위도", "lon": "경도"})
    @api.marshal_with(current_weather_model, skip_none=True)
    def get(self):
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if not lat or not lon:
            return {"error": "위도(lat)와 경도(lon)를 모두 제공해야 합니다."}, 400

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            response = requests.get(url)

            if response.status_code != 200:
                return {"error": f"OpenWeather API 호출 실패: {response.status_code}"}, response.status_code

            data = response.json()
            return {
                "latitude": float(lat),
                "longitude": float(lon),
                "city": data.get("name", "Unknown"),
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"],
                "weather_icon": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
            }, 200
        except Exception as e:
            return {"error": f"서버 오류: {str(e)}", "traceback": traceback.format_exc()}, 500


# ----------------
# 5일/3시간 예보 API
# ----------------
@api.route('/weather/forecast')
class WeatherForecast(Resource):
    @api.doc(params={"lat": "위도", "lon": "경도"})
    @api.marshal_list_with(forecast_model, skip_none=True)
    def get(self):
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if not lat or not lon:
            return {"error": "위도(lat)와 경도(lon)를 모두 제공해야 합니다."}, 400

        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            response = requests.get(url)

            if response.status_code != 200:
                return {"error": f"OpenWeather API 호출 실패: {response.status_code}"}, response.status_code

            data = response.json()

            # UTC -> KST 변환
            kst = pytz.timezone('Asia/Seoul')
            forecast_data = []
            for forecast in data["list"]:
                utc_time = datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
                kst_time = utc_time + timedelta(hours=9)  # KST = UTC + 9
                formatted_time = kst_time.strftime("%Y-%m-%d %H:%M:%S")  # 원하는 출력 형식

                # 강수량, 강설량 처리
                rain_volume = forecast.get("rain", {}).get("3h", 0.0)  # 3시간 동안의 강수량 (mm)
                snow_volume = forecast.get("snow", {}).get("3h", 0.0)  # 3시간 동안의 강설량 (mm)

                # 예보 데이터 추가
                forecast_data.append({
                    "datetime": formatted_time,
                    "temperature": forecast["main"]["temp"],
                    "humidity": forecast["main"]["humidity"],
                    "wind_speed": forecast["wind"]["speed"],
                    "description": forecast["weather"][0]["description"],
                    "rain_volume": rain_volume,
                    "snow_volume": snow_volume,
                    "weather_icon": f"http://openweathermap.org/img/wn/{forecast['weather'][0]['icon']}@2x.png",
                })

            return forecast_data, 200
        except Exception as e:
            return {"error": f"서버 오류: {str(e)}", "traceback": traceback.format_exc()}, 500



if __name__ == '__main__':
    app.run(debug=True)