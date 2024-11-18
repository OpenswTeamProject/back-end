from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields
from flask_cors import CORS

app = Flask(__name__)

# CORS 설정
CORS(app)

# Flask-RESTx API 초기화
api = Api(
    app,
    version='1.0',
    title='Sample API',
    description='Flask RESTx를 사용한 Swagger UI 예제',
)

# 네임스페이스 생성
greet_ns = api.namespace('greet', description='인사 API')

# 모델 정의 (Swagger 문서에서 사용)
greet_model = api.model('Greet', {
    'name': fields.String(required=False, description='인사할 이름', example='John')
})

@greet_ns.route('/')
class Greet(Resource):
    @api.doc(params={'name': '인사할 이름 (옵션)'})
    @api.response(200, '성공', greet_model)
    def get(self):
        """
        이름에 따라 인사 메시지를 반환합니다.
        """
        name = request.args.get('name', 'World')
        return {"message": f"Hello, {name}!"}

if __name__ == '__main__':
    app.run(debug=True)
