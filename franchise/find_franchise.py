import pandas as pd

# 기존 가게 목록 CSV 경로 (예: '점'으로 끝나는 가게들이 들어 있음)
input_csv_path = "C:\\Cprogram\\SAI_FALCON\\foodsnap\\프랜차이즈_정리.csv"

# 브랜드 목록 저장할 CSV 경로
output_csv_path = "C:\\Cprogram\\SAI_FALCON\\foodsnap\\프랜차이즈_가게명_정리.csv"

# CSV 불러오기
df = pd.read_csv(input_csv_path, encoding='utf-8-sig')

# '점'으로 끝나는 가게명에서 브랜드명(첫 단어) 추출
def extract_brand(name):
    if isinstance(name, str) and name.endswith("점"):
        words = name.split()
        return words[0] if words else None
    return None

# 브랜드 추출 컬럼 추가
df['브랜드'] = df['이름'].apply(extract_brand)

# 고유 브랜드명만 추출 후 정렬
brand_df = df[['브랜드']].dropna().drop_duplicates().sort_values(by='브랜드').reset_index(drop=True)

# 결과 CSV로 저장
brand_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

print(f"✅ 저장 완료: {output_csv_path} ({len(brand_df)}개 브랜드)")

