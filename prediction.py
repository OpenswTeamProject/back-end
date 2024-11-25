import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

# 모델 및 데이터 로드
model = load_model('lstm_model_epoch100_batch64.h5')
data = pd.read_csv('../test/demand_bike_dataset_2022_2024.csv', parse_dates=['대여일자'])

# 데이터 전처리 및 스케일러 설정
data['대여소번호'] = data['대여소번호'].astype('category').cat.codes
data['주말'] = data['주말'].astype(int)
data['대중교통'] = data['대중교통'].astype(int)
data['도심_외곽'] = data['도심_외곽'].astype(int)
data['계절'] = data['계절'].astype('category').cat.codes

usage_scaler = MinMaxScaler()
data['이용건수_scaled'] = usage_scaler.fit_transform(data[['이용건수']])

input_scaler = MinMaxScaler()
scaled_data = input_scaler.fit_transform(data.drop(['대여일자', '이용건수'], axis=1))


class BikeRentalInput:
    """
    대여 건수 예측을 위한 사용자 입력 클래스
    """

    def __init__(self, input_data):
        self.data = input_data

    def preprocess(self):
        """
        사용자 입력 데이터를 전처리하여 모델에 적합한 형식으로 반환
        """
        # 입력 데이터를 DataFrame으로 변환
        user_input_df = pd.DataFrame([self.data])
        user_input_df['대여소번호'] = user_input_df['대여소번호'].astype('category').cat.codes
        user_input_df['주말'] = user_input_df['주말'].astype(int)
        user_input_df['대중교통'] = user_input_df['대중교통'].astype(int)
        user_input_df['도심_외곽'] = user_input_df['도심_외곽'].astype(int)
        user_input_df['계절'] = user_input_df['계절'].astype('category').cat.codes

        # 불필요한 컬럼 제거
        user_input_df = user_input_df.drop(['대여일자'], axis=1, errors='ignore')

        # 누락된 열 추가 및 기본값 설정
        missing_cols = set(input_scaler.feature_names_in_) - set(user_input_df.columns)
        for col in missing_cols:
            user_input_df[col] = 0

        # 컬럼 순서 정렬
        user_input_df = user_input_df[input_scaler.feature_names_in_]

        # 스케일링
        return input_scaler.transform(user_input_df)


def predict_bike_rental(input_data, sequence_length=7):
    """
    주어진 사용자 입력 값을 바탕으로 대여 건수를 예측하는 함수.

    Args:
        input_data (dict): 사용자 입력 데이터.
        sequence_length (int): 모델 입력 시퀀스 길이 (기본값: 7).

    Returns:
        float: 예측된 대여 건수.
    """
    # 사용자 입력 처리
    user_input = BikeRentalInput(input_data)
    user_scaled_input = user_input.preprocess()

    # 최근 데이터와 결합
    recent_data = scaled_data[-sequence_length:]
    prediction_input = np.vstack([recent_data, user_scaled_input])[-sequence_length:]

    # 모델 입력 형식 변환
    prediction_input = prediction_input[np.newaxis, ...]

    # 예측
    predicted_scaled_usage = model.predict(prediction_input)
    predicted_usage = usage_scaler.inverse_transform(predicted_scaled_usage)

    return predicted_usage[0, 0]

'''
# 사용자 입력값 정의
user_input = {
    '대여소번호': 201,        # 대여소 번호
    '대여일자':'2024-07-12',
    '주말': False,            # 주말 여부
    '대중교통': False,        # 대중교통 여부
    '도심_외곽': True,       # 도심 외곽 여부
    '강수량 합산': 12.0,       # 강수량 합산
    '강수 지속시간 합산': 5.0, # 강수 지속시간 합산
    '평균 기온 평균': 32.7,   # 평균 기온
    '최고 기온 평균': 36.8,    # 최고 기온
    '최저 기온 평균': 28.4,   # 최저 기온
    '평균 습도 평균': 75.6,   # 평균 습도
    '최저 습도 평균': 60.6,   # 최저 습도
    '평균 풍속 평균': 1.3,    # 평균 풍속
    '최대 풍속 평균': 2.7,    # 최대 풍속
    '최대 순간 풍속 평균': 3.3, # 최대 순간 풍속
    '계절': '여름'           # 계절
}
'''