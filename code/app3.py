import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# 1. 페이지 기본 설정 및 디자인
# =========================================================
st.set_page_config(
    page_title="청소년 수면 및 스마트폰 사용 분석 대시보드",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. 데이터 자동 로드 및 정제 함수 (@st.cache_data)
# =========================================================
@st.cache_data
def load_and_clean_data(file_path="survey_data_100.csv"):
    # 2-1. CSV 파일 읽기
    df = pd.read_csv(file_path)

    # 2-2. 텍스트 데이터 양끝 공백 제거 및 빈 문자열 NaN 변환
    object_cols = df.select_dtypes(include=["object"]).columns
    for col in object_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("", np.nan)

    # 2-3. 수치형 데이터 이상치(0 이하 또는 24 이상/999 이상)를 NaN으로 변환
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        if col in ["주중_평균_수면시간", "수면시간", "스마트폰_사용시간"]:
            df[col] = df[col].apply(
                lambda x: (
                    np.nan if (pd.isna(x) or x <= 0 or x >= 24 or x >= 999) else x
                )
            )

    # 2-4. 학년 컬럼 결측치 보정 (있을 경우 전체 중앙값)
    if "학년" in df.columns and df["학년"].isna().sum() > 0:
        df["학년"] = df["학년"].fillna(df["학년"].median())

    # 2-5. '학년' 그룹별 중앙값(Median)으로 결측치 자동 대치
    for col in numeric_cols:
        if col != "학년":
            df[col] = df.groupby("학년")[col].transform(
                lambda x: x.fillna(x.median())
            )
            # 그룹 내 모두 NaN인 경우 전체 중앙값으로 보완
            df[col] = df[col].fillna(df[col].median())

    return df


# 데이터 로드
try:
    df_raw = load_and_clean_data("survey_data_100.csv")
except Exception as e:
    st.error(
        f"⚠️ `survey_data_100.csv` 파일을 읽어오는 중 오류가 발생했습니다: {e}\n\n"
        "파일이 `app.py`와 같은 폴더에 위치해 있는지 확인해 주세요!"
    )
    st.stop()


# =========================================================
# 3. 사이드바 (Sidebar) 컨트롤러
# =========================================================
st.sidebar.header("🔍 데이터 필터링")

# 학년 선택 옵션 생성
grade_options = ["전체"] + sorted([f"{g}학년" for g in df_raw["학년"].unique()])
selected_grade = st.sidebar.selectbox("학년을 선택하세요", grade_options)

# 사이드바 데이터 필터링 적용
if selected_grade == "전체":
    df_filtered = df_raw.copy()
else:
    grade_num = int(selected_grade.replace("학년", ""))
    df_filtered = df_raw[df_raw["학년"] == grade_num].copy()

# 사이드바 요약 정보
st.sidebar.markdown("---")
st.sidebar.subheader("📌 필터링 요약")
st.sidebar.write(f"• 선택된 학년: **{selected_grade}**")
st.sidebar.write(f"• 해당 데이터 건수: **{len(df_filtered)}명**")


# =========================================================
# 4. 메인 화면 헤더 및 타이틀
# =========================================================
st.title("🌙 수면 부족 대한민국 청소년: 폰 때문일까, 학원 때문일까?")
st.subheader("📱 청소년 건강 실태 survey_data_100.csv 데이터 자동 정제 & 분석 대시보드")
st.markdown(
    "본 대시보드는 대한민국 청소년들의 수면시간과 스마트폰 사용시간 간의 관계를 탐구하고 "
    "실제 데이터 속 숨겨진 패턴을 찾아보기 위해 제작되었습니다."
)
st.markdown("---")


# =========================================================
# 5. 메인 탭(st.tabs) 구성
# =========================================================
tab1, tab2, tab3 = st.tabs(
    [
        "📋 탭 1: 정제된 데이터",
        "📊 탭 2: 요약 통계량 & 핵심 지표",
        "📈 탭 3: 반응형 차트 & 멘토링 분석",
    ]
)


# ---------------------------------------------------------
# [탭 1] 정제된 전체 데이터 테이블
# ---------------------------------------------------------
with tab1:
    st.markdown("### 📋 자동 정제 완료 데이터셋")
    st.caption(
        "이상치(0 이하/24 이상) 및 결측치가 학년별 중앙값으로 보정된 데이터입니다."
    )
    st.dataframe(df_filtered, use_container_width=True)

    # CSV 다운로드 버튼
    csv_data = df_filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Filtered Data CSV 다운로드",
        data=csv_data,
        file_name=f"cleaned_survey_data_{selected_grade}.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------
# [탭 2] 주요 요약 통계량 & 핵심 지표
# ---------------------------------------------------------
with tab2:
    st.markdown("### 📌 핵심 지표 요약 (st.metric)")

    # 선택된 그룹의 평균 계산
    avg_sleep = (
        df_filtered["주중_평균_수면시간"].mean()
        if "주중_평균_수면시간" in df_filtered.columns
        else 0
    )
    avg_phone = (
        df_filtered["스마트폰_사용시간"].mean()
        if "스마트폰_사용시간" in df_filtered.columns
        else 0
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="👥 데이터 분석 대상 수", value=f"{len(df_filtered)} 명")
    with col2:
        st.metric(label="💤 평균 주중 수면시간", value=f"{avg_sleep:.2f} 시간")
    with col3:
        st.metric(label="📱 평균 스마트폰 사용시간", value=f"{avg_phone:.2f} 시간")

    st.markdown("---")
    st.markdown("### 📊 주요 기술통계량 (.describe())")
    st.dataframe(df_filtered.describe().round(2), use_container_width=True)


# ---------------------------------------------------------
# [탭 3] 반응형 차트 & 데이터 분석 멘토링
# ---------------------------------------------------------
with tab3:
    st.markdown("### 🔍 1. 학년별 평균 수면시간 vs 스마트폰 사용시간 (막대 그래프)")

    # 학년별 평균 비교 데이터
    grade_grouped = (
        df_raw.groupby("학년")[["주중_평균_수면시간", "스마트폰_사용시간"]]
        .mean()
        .round(2)
    )
    st.bar_chart(grade_grouped)

    st.markdown("---")
    st.markdown("### 💡 2. 스마트폰 사용시간 vs 수면시간 관계 (Plotly 산점도)")

    # Plotly 인터랙티브 Scatter Plot
    fig = px.scatter(
        df_filtered,
        x="스마트폰_사용시간",
        y="주중_평균_수면시간",
        color="학년",
        hover_data=[
            col
            for col in ["학년", "주중_평균_수면시간", "수면시간", "스마트폰_사용시간"]
            if col in df_filtered.columns
        ],
        title=f"<b>[{selected_grade}] 스마트폰 사용시간 vs 주중 평균 수면시간 산점도</b>",
        labels={
            "스마트폰_사용시간": "스마트폰 사용시간 (시간)",
            "주중_평균_수면시간": "주중 평균 수면시간 (시간)",
            "학년": "학년",
        },
        template="plotly_white",
    )

    fig.update_layout(
        font=dict(
            family="Malgun Gothic, Apple Gothic, NanumGothic, sans-serif",
            size=13,
        ),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_traces(marker=dict(size=12, opacity=0.85))

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------
    # 데이터 분석 멘토의 3단계 유도 질문 세션
    # -----------------------------------------------------
    st.markdown("---")
    st.markdown("### 🧑‍🏫 [데이터 탐구 세션] 멘토와 함께하는 3단계 질문!")

    # 상관계수 계산
    corr_value = df_raw["스마트폰_사용시간"].corr(df_raw["주중_평균_수면시간"])

    st.info(
        f"✨ **현재 100명 전체 데이터의 상관계수**: `{corr_value:.3f}` (0에 가까울수록 두 변수 간의 선형 상관관계가 거의 없음을 의미합니다)"
    )

    with st.expander("💬 1단계: 그래프의 모양과 점들의 밀집 구역 관찰하기", expanded=True):
        st.write(
            "🙋‍♂️ **멘토 질문**: 위 Plotly 산점도를 가만히 살피어 보세요!\n"
            "- 점들이 어느 구역(스마트폰 사용시간 3~4.5시간, 수면시간 6~7.5시간)에 주로 모여 있나요?\n"
            "- 오른쪽 아래로 우하향하는 뚜렷한 직선 형태가 보이나요, 아니면 뭉쳐 있나요?"
        )

    with st.expander("💬 2단계: 통설 vs 실제 데이터 결과 비교하기"):
        st.write(
            f"🙋‍♂️ **멘토 질문**: 보통 '스마트폰을 많이 쓰면 무조건 잠을 적게 잘 것이다'라고 생각하기 쉽죠?\n"
            f"- 하지만 실제 계산된 상관계수는 **{corr_value:.3f}**로 거의 0에 가깝습니다!\n"
            "- 왜 우리의 일반적인 생각(통설)과 데이터 분석 결과 사이에 이러한 차이가 발생했을까요?"
        )

    with st.expander("💬 3단계: 숨은 제3의 변수 탐색하기"):
        st.write(
            "🙋‍♂️ **멘토 질문**: 수면시간을 결정짓는 진짜 범인은 혹시 따로 있지 않을까요?\n"
            "- 학원 수강 시간, 과제/시험공부 시간, 스트레스, 취침 전 유튜브 시청 등이 수면시간에 더 결정적인 영향을 미치지 않을지 함께 고민해 봅시다! 💡"
        )