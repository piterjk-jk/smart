import numpy as np
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="청소년 수면 및 스마트폰 사용 분석",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------
# 요구사항 1 & 2: 데이터 로드 및 정제 함수 (@st.cache_data 적용)
# ---------------------------------------------------------
@st.cache_data
def load_and_clean_data(file_path="survey_data_100.csv"):
    # 1. 파일 읽기
    df = pd.read_csv(file_path)

    # 2. 텍스트 데이터 양끝 공백 제거 및 빈 문자열 NaN 변환
    object_cols = df.select_dtypes(include=["object"]).columns
    for col in object_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("", np.nan)

    # 3. 수치형 데이터 이상치(-999, 0 이하, 999/9999 이상 등)를 NaN으로 처리
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        # 비현실적인 값(-999, <=0, >=999 등)을 NaN으로 변환
        df[col] = df[col].apply(
            lambda x: np.nan if (pd.isna(x) or x <= 0 or x >= 999) else x
        )

    # 4. 요구사항 3: 학년별 중앙값으로 결측치 자동 보정
    if "학년" in df.columns and df["학년"].isna().sum() > 0:
        df["학년"] = df["학년"].fillna(df["학년"].median())

    for col in numeric_cols:
        if col != "학년":
            # 학년 그룹별 중앙값으로 결측치 보정
            df[col] = df.groupby("학년")[col].transform(
                lambda x: x.fillna(x.median())
            )
            # 만약 학년 그룹으로도 메꿔지지 않은 결측치가 있다면 전체 중앙값으로 보정
            df[col] = df[col].fillna(df[col].median())

    return df


# ---------------------------------------------------------
# 앱 화면 구성을 위한 데이터 로드
# ---------------------------------------------------------
try:
    df_cleaned = load_and_clean_data("survey_data_100.csv")
except Exception as e:
    st.error(
        f"데이터 파일을 불러오는 중 오류가 발생했습니다: {e}\n\n"
        "`survey_data_100.csv` 파일이 `app.py`와 같은 폴더에 위치해 있는지 확인해 주세요."
    )
    st.stop()

# 앱 상단 타이틀
st.title("📱 수면 부족 대한민국 청소년: 폰 때문일까, 학원 때문일까?")
st.subheader("청소년 건강 실태 survey_data_100.csv 자동 정제 대시보드")
st.markdown("---")


# ---------------------------------------------------------
# 요구사항 4: st.tabs를 활용한 3개 탭 구성
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "📋 탭 1: 정제된 전체 데이터",
        "📊 탭 2: 주요 요약 통계량 & 핵심 지표",
        "📈 탭 3: 학년별 비교 막대 그래프",
    ]
)


# === 탭 1: 정제된 전체 데이터 테이블 ===
with tab1:
    st.markdown("### 정제 완료된 데이터셋")
    st.caption("이상치 및 결측치가 학년별 중앙값으로 자동 보정된 데이터입니다.")
    st.dataframe(df_cleaned, use_container_width=True)


# === 탭 2: 주요 요약 통계량 & 요약 카드 ===
with tab2:
    st.markdown("### 핵심 수치 요약 (st.metric)")

    # 주요 데이터 평균값 계산
    avg_sleep = (
        df_cleaned["수면시간"].mean()
        if "수면시간" in df_cleaned.columns
        else 0
    )
    avg_phone = (
        df_cleaned["스마트폰_사용시간"].mean()
        if "스마트폰_사용시간" in df_cleaned.columns
        else 0
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="총 응답자 수", value=f"{len(df_cleaned)} 명")
    with col2:
        st.metric(label="전체 평균 수면시간", value=f"{avg_sleep:.2f} 시간")
    with col3:
        st.metric(label="전체 평균 스마트폰 사용시간", value=f"{avg_phone:.2f} 시간")

    st.markdown("---")
    st.markdown("### 주요 기술통계량 (.describe())")
    st.dataframe(df_cleaned.describe().round(2), use_container_width=True)


# === 탭 3: 학년별 수면시간 및 스마트폰 사용시간 비교 반응형 막대 그래프 ===
with tab3:
    st.markdown("### 학년별 평균 수면시간 vs 평균 스마트폰 사용시간 비교")

    # 학년별 평균 데이터 그룹화
    target_cols = [
        col
        for col in ["수면시간", "스마트폰_사용시간"]
        if col in df_cleaned.columns
    ]

    if "학년" in df_cleaned.columns and target_cols:
        grouped_df = df_cleaned.groupby("학년")[target_cols].mean().round(2)

        # Streamlit 반응형 막대 그래프 출력
        st.bar_chart(grouped_df)

        st.markdown("#### 학년별 상세 평균 데이터표")
        st.dataframe(grouped_df, use_container_width=True)
    else:
        st.warning(
            "그래프를 생성하기 위한 '학년', '수면시간', '스마트폰_사용시간' 컬럼을 찾을 수 없습니다."
        )