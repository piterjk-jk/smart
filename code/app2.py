import numpy as np
import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="설문조사 데이터 분석 대시보드", page_icon="📊", layout="wide"
)


# 2. 데이터 정제 및 캐싱 함수 (@st.cache_data 적용)
@st.cache_data
def load_and_clean_data(file_path):
  # 2-1. CSV 파일 읽기
  df = pd.read_csv(file_path)

  # 2-2. 텍스트 데이터 양끝 공백 제거 및 빈 문자열 결측치(NaN) 변환
  object_cols = df.select_dtypes(include=['object', 'string']).columns
  for col in object_cols:
    df[col] = df[col].astype(str).str.strip().replace('', np.nan)

  # 2-3. 수치형 데이터 이상치(-999, 0 이하, 999 이상 등)를 결측치(NaN)로 변환
  numeric_cols = df.select_dtypes(include=[np.number]).columns
  for col in numeric_cols:
    df.loc[(df[col] <= 0) | (df[col] >= 999), col] = np.nan

  # 2-4. 결측치는 '학년' 그룹별 중앙값(Median)으로 대체
  target_cols = [col for col in df.columns if col != '학년']
  for col in target_cols:
    df[col] = df[col].fillna(df.groupby('학년')[col].transform('median'))

  # '학년' 데이터 타입 변환 (정수형)
  if '학년' in df.columns:
    df['학년'] = df['학년'].astype(int)

  return df


# 3. 앱 메인 화면 구성
try:
  # 데이터 읽기 및 정제 함수 실행
  df_cleaned = load_and_clean_data('survey_data_100.csv')

  # 대시보드 상단 타이틀
  st.title('📊 학생 수면 및 스마트폰 사용 패턴 분석 대시보드')
  st.caption(
      '`survey_data_100.csv` 데이터를 자동으로 정제하고 요약한 반응형'
      ' 대시보드입니다.'
  )
  st.markdown('---')

  # 4. st.tabs를 이용한 3가지 탭 구성
  tab1, tab2, tab3 = st.tabs(
      ['📋 정제된 전체 데이터', '📈 주요 요약 통계량', '📊 학년별 비교 차트']
  )

  # 탭 1: 정제된 전체 데이터 테이블
  with tab1:
    st.subheader('📋 정제 완료된 데이터셋')
    st.write(
        '이상치 보정 및 결측치가 학년별 중앙값으로 자동 대체된 데이터입니다.'
    )
    st.dataframe(df_cleaned, use_container_width=True)

  # 탭 2: 주요 요약 통계량 및 st.metric 카드
  with tab2:
    st.subheader('📌 주요 요약 지표 (Key Metrics)')

    # 핵심 요약 지표 카드 (st.metric)
    col1, col2, col3, col4 = st.columns(4)

    sleep_col = (
        '수면시간' if '수면시간' in df_cleaned.columns else '주중_평균_수면시간'
    )
    avg_sleep = df_cleaned[sleep_col].mean()
    avg_phone = df_cleaned['스마트폰_사용시간'].mean()
    total_count = len(df_cleaned)
    grade_count = df_cleaned['학년'].nunique()

    with col1:
      st.metric(label='총 응답자 수', value=f'{total_count} 명')
    with col2:
      st.metric(label='조사 학년 수', value=f'{grade_count} 개 학년')
    with col3:
      st.metric(label='평균 수면시간', value=f'{avg_sleep:.2f} 시간')
    with col4:
      st.metric(label='평균 스마트폰 사용시간', value=f'{avg_phone:.2f} 시간')

    st.markdown('---')

    # describe() 기술통계량 표
    st.subheader('📊 주요 기술통계량 (describe)')
    st.dataframe(df_cleaned.describe(), use_container_width=True)

  # 탭 3: 학년별 수면시간 및 스마트폰 사용시간 비교 반응형 막대 그래프
  with tab3:
    st.subheader('📊 학년별 수면시간 및 스마트폰 사용시간 비교')

    # 학년별 그룹 평균 계산
    sleep_col = (
        '수면시간' if '수면시간' in df_cleaned.columns else '주중_평균_수면시간'
    )
    grade_summary = df_cleaned.groupby('학년')[
        [sleep_col, '스마트폰_사용시간']
    ].mean()

    st.markdown('##### 1️⃣ 학년별 평균 수면시간 vs 스마트폰 사용시간 비교')
    st.bar_chart(grade_summary)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
      st.markdown('##### 2️⃣ 학년별 평균 수면시간 (시간)')
      st.bar_chart(grade_summary[[sleep_col]])

    with col_chart2:
      st.markdown('##### 3️⃣ 학년별 평균 스마트폰 사용시간 (시간)')
      st.bar_chart(grade_summary[['스마트폰_사용시간']])

except FileNotFoundError:
  st.error(
      '❌ `survey_data_100.csv` 파일을 찾을 수 없습니다. 소스 코드와 동일한 위치에'
      ' 파일이 있는지 확인해 주세요.'
  )