from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

api = Api(app, version="1.0", title="Weather API", description="REST API for Weather Data using OpenWeather API")

weather_ns = api.namespace("weather", description="Weather API")

# OpenWeather API Key (공통 사용)
API_KEY = os.getenv("b185176d52c5df5dd2b8d5ed23d1a75c", "b185176d52c5df5dd2b8d5ed23d1a75c")  # 환경 변수 또는 기본 값

# RESTx 모델 정의 (현재 날씨)
current_weather_model = api.model("CurrentWeather", {
    "latitude": fields.Float(description="위도"),
    "longitude": fields.Float(description="경도"),
    "city": fields.String(description="도시 이름"),
    "temperature": fields.Float(description="현재 온도 (°C)"),
    "humidity": fields.Float(description="습도 (%)"),
    "wind_speed": fields.Float(description="풍속 (m/s)"),
    "description": fields.String(description="날씨 설명"),
})

# RESTx 모델 정의 (5일/3시간 예보)
forecast_model = api.model("Forecast", {
    "datetime": fields.String(description="예보 시간"),
    "temperature": fields.Float(description="온도 (°C)"),
    "humidity": fields.Float(description="습도 (%)"),
    "wind_speed": fields.Float(description="풍속 (m/s)"),
    "description": fields.String(description="날씨 설명"),
})


@weather_ns.route('/current')
class CurrentWeather(Resource):
    @api.doc(params={"lat": "위도", "lon": "경도"})
    @api.marshal_with(current_weather_model, skip_none=True)
    def get(self):
        """
        현재 날씨 정보를 반환합니다 (위도, 경도 기준).
        """
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if not lat or not lon:
            return {"error": "위도(lat)와 경도(lon)를 모두 제공해야 합니다."}, 400

        try:
            # OpenWeather API 호출
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            response = requests.get(url)

            if response.status_code == 401:
                return {"error": "API 키가 유효하지 않습니다. 올바른 API 키를 설정하세요."}, 401
            elif response.status_code != 200:
                return {"error": f"OpenWeather API 호출 실패: {response.status_code}"}, response.status_code

            # API 응답 데이터 처리
            data = response.json()
            weather_info = {
                "latitude": float(lat),
                "longitude": float(lon),
                "city": data.get("name", "Unknown"),
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"],
            }

            return weather_info, 200

        except requests.exceptions.RequestException as e:
            return {"error": f"요청 오류: {str(e)}"}, 500
        except Exception as e:
            return {"error": f"서버 오류: {str(e)}"}, 500


@weather_ns.route('/forecast')
class WeatherForecast(Resource):
    @api.doc(params={"lat": "위도", "lon": "경도"})
    @api.marshal_list_with(forecast_model, skip_none=True)
    def get(self):
        """
        5일/3시간 날씨 예보 데이터를 반환합니다 (위도, 경도 기준).
        """
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if not lat or not lon:
            return {"error": "위도(lat)와 경도(lon)를 모두 제공해야 합니다."}, 400

        try:
            # OpenWeather API 호출
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
            response = requests.get(url)

            if response.status_code == 401:
                return {"error": "API 키가 유효하지 않습니다. 올바른 API 키를 설정하세요."}, 401
            elif response.status_code != 200:
                return {"error": f"OpenWeather API 호출 실패: {response.status_code}"}, response.status_code

            # API 응답 데이터 처리
            data = response.json()

            forecast_data = [
                {
                    "datetime": forecast["dt_txt"],
                    "temperature": forecast["main"]["temp"],
                    "humidity": forecast["main"]["humidity"],
                    "wind_speed": forecast["wind"]["speed"],
                    "description": forecast["weather"][0]["description"]
                }
                for forecast in data["list"]
            ]

            return forecast_data, 200

        except requests.exceptions.RequestException as e:
            return {"error": f"요청 오류: {str(e)}"}, 500
        except Exception as e:
            return {"error": f"서버 오류: {str(e)}"}, 500


if __name__ == '__main__':
    app.run(debug=True)
