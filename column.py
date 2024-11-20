import pandas as pd

# 엑셀 파일 읽기
file_path = r"C:\Users\choho\Desktop\back-end\back-end\공공자전거 대여소 정보(24.6월 기준).csv"
df = pd.read_csv(file_path, header=0)  # 첫 번째 행을 컬럼 이름으로 사용

# 데이터프레임의 컬럼 확인
print("컬럼 이름 확인:", df.columns)

# null 값을 0으로 대체
df = df.fillna(0)

# 새 컬럼 추가 (기존 컬럼 유지)
df['거치대수 합계'] = df['거치대수1'] + df['거치대수2']  # 거치대수1과 거치대수2 컬럼 이름은 확인 후 수정

# CSV 파일로 저장
output_csv_path = r"C:\Users\choho\Desktop\back-end\back-end\공공자전거 대여소 정보(24.6월 기준).csv"
df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

print(f"CSV 파일이 성공적으로 저장되었습니다: {output_csv_path}")
