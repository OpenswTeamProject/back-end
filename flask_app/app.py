import traceback
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
import re
import pytz
from collections import defaultdict
from datetime import datetime
from prediction import predict_bike_rental

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)

# Flask-RESTx API 초기화
api = Api(app, version="1.0", title="Bike & Weather API", description="통합된 자전거 대여소 및 날씨 API")

# 환경 변수에서 데이터베이스 URL 읽기
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:1234@mysql:3306/bike?charset=utf8mb4')
engine = create_engine(DATABASE_URL,
                       connect_args={"local_infile": True},
                       pool_size=50,  # 기본 연결 풀 크기
                       max_overflow=100,  # 오버플로우 연결 수
                       pool_timeout=100,  # 연결 대기 시간
                       )
Session = sessionmaker(bind=engine)

# OpenWeather API 키 설정 (환경 변수에서 가져오기)
API_KEY = os.getenv("", "") # API_KEY 입력
API_KEY = 'b185176d52c5df5dd2b8d5ed23d1a75c' # API_KEY 입력

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

# --------------------
# AI API 모델 정의    |
# --------------------

# 네임스페이스 정의
ns = api.namespace('predict', description='Prediction operations')

# 입력 모델 정의 (Swagger 문서화에 사용)
prediction_input_model = ns.model('PredictionInput', {
    '대여소번호': fields.Integer(required=True, description='대여소 번호'),
    '대여일자': fields.String(required=True, description='대여 일자 (YYYY-MM-DD)'),
    '주말': fields.Boolean(required=True, description='주말 여부'),
    '대중교통': fields.Boolean(required=True, description='대중교통 여부'),
    '도심_외곽': fields.Boolean(required=True, description='도심 외곽 여부'),
    '강수량 합산': fields.Float(required=True, description='강수량 합산 (mm)'),
    '강수 지속시간 합산': fields.Float(required=True, description='강수 지속시간 합산 (시간)'),
    '평균 기온 평균': fields.Float(required=True, description='평균 기온 (°C)'),
    '최고 기온 평균': fields.Float(required=True, description='최고 기온 (°C)'),
    '최저 기온 평균': fields.Float(required=True, description='최저 기온 (°C)'),
    '평균 습도 평균': fields.Float(required=True, description='평균 습도 (%)'),
    '최저 습도 평균': fields.Float(required=True, description='최저 습도 (%)'),
    '평균 풍속 평균': fields.Float(required=True, description='평균 풍속 (m/s)'),
    '최대 풍속 평균': fields.Float(required=True, description='최대 풍속 (m/s)'),
    '최대 순간 풍속 평균': fields.Float(required=True, description='최대 순간 풍속 (m/s)'),
    '계절': fields.String(required=True, description='계절 (봄, 여름, 가을, 겨울)')
})

# 출력 모델 정의
prediction_output_model = ns.model('PredictionOutput', {
    'status': fields.String(description='Response status'),
    'date' : fields.String(description='Response date'),
    'predicted_rental': fields.Float(description='Predicted bike rental count')
})
# ------------------
# 자전거 대여소 API  |
# ------------------

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
            # 대여소 정보 쿼리
            query = text("""
                SELECT station_name, total_slots, latitude, longitude
                FROM bike_station
                WHERE station_name = :station
                LIMIT 1
            """)
            result = session.execute(query, {"station": station}).fetchone()

            if not result:
                return {"message": "해당 대여소에 대한 데이터가 없습니다."}, 404

            station_name = result.station_name
            total_slots = result.total_slots
            latitude = result.latitude
            longitude = result.longitude

            # 근처 대여소 정보 쿼리
            nearby_query = text("""
                SELECT station_name, total_slots, latitude, longitude
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
                {
                    "station_name": row.station_name,
                    "total_slots": row.total_slots,
                    "latitude": row.latitude,
                    "longitude": row.longitude
                }
                for row in nearby_result
            ]

            return {
                "station_name": station_name,
                "total_slots": total_slots,
                "latitude": latitude,
                "longitude": longitude,
                "nearby_stations": nearby_stations
            }, 200
        except SQLAlchemyError as e:
            return {"message": f"SQLAlchemy 데이터베이스 오류: {str(e)}"}, 500
        finally:
            session.close()


# -------------------
# 날씨 API
# -------------------

@weather_ns.route('/current')
class CurrentWeather(Resource):
    @api.doc(params={"lat": "위도", "lon": "경도"})
    @api.marshal_with(current_weather_model, skip_none=True)
    def get(self):
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if not lat or not lon:
            return {"error": "위도(lat)와 경도(lon)를 모두 제공해야 합니다."}, 400

        data = get_current_weather(lat, lon)
        try:

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

# 오늘 날짜 날씨 불러오는 api 실행 함수
def get_current_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"OpenWeather API 호출 실패: {response.status_code}"}, response.status_code
    return response.json()



# ----------------
# 5일/3시간 예보 API
# ----------------
@weather_ns.route('/forecast')
class WeatherForecast(Resource):
    @api.doc(params={"lat": "위도", "lon": "경도"})
    @api.marshal_list_with(forecast_model, skip_none=True)
    def get(self):
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if not lat or not lon:
            return {"error": "위도(lat)와 경도(lon)를 모두 제공해야 합니다."}, 400

        try:
            data = get_forecast_weather(lat, lon)
            # # UTC -> KST 변환
            # kst = pytz.timezone('Asia/Seoul')
            # forecast_data = []
            # for forecast in data["list"]:
            #     utc_time = datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S")
            #     kst_time = utc_time + timedelta(hours=9)  # KST = UTC + 9
            #     formatted_time = kst_time.strftime("%Y-%m-%d %H:%M:%S")  # 원하는 출력 형식
            #
            #     # 강수량, 강설량 처리
            #     rain_volume = forecast.get("rain", {}).get("3h", 0.0)  # 3시간 동안의 강수량 (mm)
            #     snow_volume = forecast.get("snow", {}).get("3h", 0.0)  # 3시간 동안의 강설량 (mm)
            #
            #     # 예보 데이터 추가
            #     forecast_data.append({
            #         "datetime": formatted_time,
            #         "temperature": forecast["main"]["temp"],
            #         "humidity": forecast["main"]["humidity"],
            #         "wind_speed": forecast["wind"]["speed"],
            #         "description": forecast["weather"][0]["description"],
            #         "rain_volume": rain_volume,
            #         "snow_volume": snow_volume,
            #         "weather_icon": f"http://openweathermap.org/img/wn/{forecast['weather'][0]['icon']}@2x.png",
            #     })

            return data, 200
        except Exception as e:
            return {"error": f"서버 오류: {str(e)}", "traceback": traceback.format_exc()}, 500

# 5일 / 3시간 예보 예측 api 지공 함수
def get_forecast_weather(lat, lon):
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
    return forecast_data


@ns.route('')
class PredictByName(Resource):
    @api.doc(params={'station': '대여소 이름'})  # 역 데이터 입력 받음
    @ns.response(200, 'Success', model=prediction_output_model)  # 출력 모델 연결
    @ns.response(400, 'Validation Error')
    def post(self):
        station_name = request.args.get('station')
        if not station_name:
            return {"message": "대여소 이름을 입력해야 합니다."}, 400

        session = Session()
        try:
            # 대여소 정보 쿼리
            query = text("""
                SELECT station_number, station_name, district ,latitude, longitude
                FROM bike_station
                WHERE station_name = :station
                LIMIT 1
            """)

            result = session.execute(query, {"station": station_name}).fetchone()
            if not result:
                return {"message": "해당 대여소에 대한 데이터가 없습니다."}, 404

            station_number = result.station_number
            latitude = result.latitude
            longitude = result.longitude

            # 현재 날씨 데이터 가져오기
            today_weather = get_current_weather(latitude, longitude)
            today_datetime = datetime.today()
            today = today_datetime.strftime('%Y-%m-%d')
            is_weekend = today_datetime.weekday() > 4

            temperature = today_weather["main"]["temp"]
            humidity = today_weather["main"]["humidity"]
            wind_speed = today_weather["wind"]["speed"]

            description = today_weather["weather"][0]["description"]
            rain = 0
            if description == "light rain":
                rain = 10.0
            elif description == "rain":
                rain = 20.0

            input_data = {
                '대여소번호': station_number,
                '대여일자': today,
                '주말': is_weekend,
                '대중교통': get_transportation(result.station_name),
                '도심_외곽': is_district(result.district),  # 기본값 설정 (필요시 수정)
                '강수량 합산': rain,
                '강수 지속시간 합산': 12 if rain > 0 else 0,
                '평균 기온 평균': temperature,
                '최고 기온 평균': temperature,
                '최저 기온 평균': temperature,
                '평균 습도 평균': humidity,
                '최저 습도 평균': humidity,
                '평균 풍속 평균': wind_speed,
                '최대 풍속 평균': wind_speed,
                '최대 순간 풍속 평균': wind_speed + 5,
                '계절': get_season(today),
            }

            forecast_data = get_forecast_weather(latitude, longitude)

            results = get_forecast_input_data(forecast_data, station_number, result.station_name, result.district)
            # results.append(input_data)

            # 예측 실행
            predict_datas = []
            for result in results:
                predicted_rental = predict_bike_rental(result)
                predict_data = {
                    'status': 'success',
                    'date': result['대여일자'],
                    'predicted_rental': round(float(predicted_rental), 2)
                }
                predict_datas.append(predict_data)
            return predict_datas, 200
        except Exception as e:
            return {"message": f"Internal server error: {str(e)}"}, 500

def get_transportation(station_name):
    return bool(re.search(r"(역|정류장|버스|지하철|터미널|전철|환승)", station_name))

# 자치구 도심 외곽 파악하기
def is_district(district):
    return bool(re.search(r"(중구|종로구|용산구|강남구|서초구|영등포구|마포구|송파구|광진구|양천구)", district))


# 예보로 데이터 얻어오기
def get_forecast_input_data(data, station_number, station_name, district):
    grouped_data = defaultdict(list)
    for entry in data:
        # entry["datetime"]의 형식을 문자열로 변환
        if isinstance(entry["datetime"], str):
            date = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d')
        elif isinstance(entry["datetime"], datetime):
            date = entry["datetime"].strftime('%Y-%m-%d')
        elif isinstance(entry["datetime"], datetime.date):
            date = entry["datetime"].strftime('%Y-%m-%d')
        else:
            raise ValueError("Unsupported date format in 'datetime' field")

        grouped_data[date].append(entry)

    # 날짜별 결과 계산
    results = []
    for date, entries in grouped_data.items():
        temperatures = [entry["temperature"] for entry in entries]
        humidities = [entry["humidity"] for entry in entries]
        wind_speeds = [entry["wind_speed"] for entry in entries]
        rain_volumes = [entry.get("rain_volume", 0) for entry in entries]  # 강수량 기본값 0

        # 강수량이 있는지 여부를 확인
        has_rain = any(rain > 0 for rain in rain_volumes)

        result = {
            '대여소번호': station_number,
            '대여일자': date,  # 문자열 형식으로 유지
            '주말': datetime.strptime(date, '%Y-%m-%d').weekday() > 4,
            '대중교통': get_transportation(station_name),
            '도심_외곽': is_district(district),
            '강수량 합산': sum(rain_volumes),
            '강수 지속시간 합산': 12 if has_rain else 0,
            '평균 기온 평균': sum(temperatures) / len(temperatures),
            '최고 기온 평균': max(temperatures),
            '최저 기온 평균': min(temperatures),
            '평균 습도 평균': sum(humidities) / len(humidities),
            '최저 습도 평균': min(humidities),
            '평균 풍속 평균': sum(wind_speeds) / len(wind_speeds),
            '최대 풍속 평균': max(wind_speeds),
            '최대 순간 풍속 평균': max(wind_speeds),  # 데이터에 순간 풍속 정보 없음
            '계절': get_season(date),
        }
        results.append(result)
    return results

def get_season(date_str):
    """
        주어진 날짜 문자열을 기반으로 계절을 반환
        :param date_str: 날짜 문자열 (예: "2024-11-27")
        :return: 계절 (봄, 여름, 가을, 겨울)
    """
    # 날짜 문자열을 datetime 객체로 변환
    date = datetime.strptime(date_str, "%Y-%m-%d")
    # 날짜의 월과 일 추출
    month = date.month
    day = date.day

    # 계절 판단
    if (month == 3 and day >= 1) or (4 <= month <= 5):
        return "봄"
    elif (month == 6 and day >= 1) or (7 <= month <= 8):
        return "여름"
    elif (month == 9 and day >= 1) or (10 <= month <= 11):
        return "가을"
    else:
        return "겨울"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



"""
prediction_input_model = ns.model('PredictionInput', {
    '대여소번호': fields.Integer(required=True, description='대여소 번호'),
    '대여일자': fields.String(required=True, description='대여 일자 (YYYY-MM-DD)'),
    '주말': fields.Boolean(required=True, description='주말 여부'),
    '대중교통': fields.Boolean(required=True, description='대중교통 여부'),
    '도심_외곽': fields.Boolean(required=True, description='도심 외곽 여부'),
    '강수량 합산': fields.Float(required=True, description='강수량 합산 (mm)'),
    '강수 지속시간 합산': fields.Float(required=True, description='강수 지속시간 합산 (시간)'),
    '평균 기온 평균': fields.Float(required=True, description='평균 기온 (°C)'),
    '최고 기온 평균': fields.Float(required=True, description='최고 기온 (°C)'),
    '최저 기온 평균': fields.Float(required=True, description='최저 기온 (°C)'),
    '평균 습도 평균': fields.Float(required=True, description='평균 습도 (%)'),
    '최저 습도 평균': fields.Float(required=True, description='최저 습도 (%)'),
    '평균 풍속 평균': fields.Float(required=True, description='평균 풍속 (m/s)'),
    '최대 풍속 평균': fields.Float(required=True, description='최대 풍속 (m/s)'),
    '최대 순간 풍속 평균': fields.Float(required=True, description='최대 순간 풍속 (m/s)'),
    '계절': fields.String(required=True, description='계절 (봄, 여름, 가을, 겨울)')
})
"""