from flask import Flask, jsonify, request, Response
from flask_restx import Api, Resource, fields
from flask_cors import CORS
import requests
import json  # JSON 처리 모듈 추가

app = Flask(__name__)
CORS(app)

api = Api(app, version="1.0", title="Weather API", description="REST API for Weather Data using OpenWeather API")

weather_ns = api.namespace("weather", description="Weather API")

# OpenWeather API Key
API_KEY = "b"  # OpenWeather API 키를 입력하세요

# RESTx 모델 정의
weather_model = api.model("Weather", {
    "latitude": fields.Float(description="위도"),
    "longitude": fields.Float(description="경도"),
    "city": fields.String(description="도시 이름"),
    "temperature": fields.Float(description="현재 온도 (°C)"),
    "humidity": fields.Float(description="습도 (%)"),
    "wind_speed": fields.Float(description="풍속 (m/s)"),
    "description": fields.String(description="날씨 설명"),
})


@weather_ns.route('/')
class Weather(Resource):
    @api.doc(params={"lat": "위도", "lon": "경도"})
    @api.marshal_with(weather_model, skip_none=True)
    def get(self):
        """
        위도(lat)와 경도(lon)를 기반으로 날씨 정보를 반환합니다.
        """
        lat = request.args.get("lat")
        lon = request.args.get("lon")

        if not lat or not lon:
            api.abort(400, "위도(lat)와 경도(lon)를 모두 제공해야 합니다.")

        try:
            # OpenWeather API 호출
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}"
            response = requests.get(url)

            if response.status_code != 200:
                api.abort(response.status_code, f"OpenWeather API 호출 실패: {response.status_code}")

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

            return weather_info

        except Exception as e:
            api.abort(500, f"서버 오류: {str(e)}")


if __name__ == '__main__':
    app.run(debug=True)
