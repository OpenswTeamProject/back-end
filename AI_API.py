from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from prediction import predict_bike_rental  # 예측 함수 임포트

# Flask 앱 초기화
app = Flask(__name__)
api = Api(app, version="1.0", title="Bike Rental Prediction API",
          description="API for predicting bike rental count based on various features.")

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
    'predicted_rental': fields.Float(description='Predicted bike rental count')
})

# 예측 엔드포인트 정의
@ns.route('/')
class Predict(Resource):
    @ns.expect(prediction_input_model)  # 입력 모델 연결
    @ns.response(200, 'Success', model=prediction_output_model)  # 출력 모델 연결
    @ns.response(400, 'Validation Error')
    def post(self):
        """
        다양한 입력값을 기반으로 자전거 대여 건수를 예측합니다.
        """
        try:
            # 요청 데이터 가져오기
            input_data = request.json

            # 예측 실행
            predicted_rental = predict_bike_rental(input_data)
            predicted_rental = float(predicted_rental)

            # 결과 반환
            return {
                'status': 'success',
                'predicted_rental': round(predicted_rental, 2)
            }, 200
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 400


# 메인 실행
if __name__ == '__main__':
    app.run(debug=True)


'''
{
    "대여소번호": 302,
    "대여일자": "2024-07-12",
    "주말": false,
    "대중교통": true,
    "도심_외곽": false,
    "강수량 합산": 12.0,
    "강수 지속시간 합산": 5.0,
    "평균 기온 평균": 32.7,
    "최고 기온 평균": 37.8,
    "최저 기온 평균": 30.4,
    "평균 습도 평균": 80.6,
    "최저 습도 평균": 60.6,
    "평균 풍속 평균": 1.3,
    "최대 풍속 평균": 2.7,
    "최대 순간 풍속 평균": 3.3,
    "계절": "여름"
}
test_data
'''