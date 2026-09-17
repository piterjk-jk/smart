import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =========================================================
# 1. 페이지 기본 설정 및 Custom CSS (고급 스타일링)
# =========================================================
st.set_page_config(
    page_title="대한민국 인구 구조 변화 분석 대시보드",
    page_icon="🇰🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 뽀대나는 대시보드를 위한 커스텀 CSS 스타일링
st.markdown(
    """
    <style>
    /* 메인 배경 및 폰트 설정 */
    .main {
        background-color: #f8f9fa;
    }
    
    /* 카드 형태 컨테이너 디자인 */
    .css-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
    
    /* st.metric 카스텀 버블 디자인 */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1e293b;
    }
    
    /* 탭 헤더 스타일링 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px 8px 0px 0px;
        border: 1px solid #e2e8f0;
        padding-left: 16px;
        padding-right: 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    
    /* 배지 스타일 */
    .badge-info {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 2. 데이터 자동 로드 및 정제 함수 (@st.cache_data)
# =========================================================
@st.cache_data
def load_and_clean_pop_data(file_path="pop_data.csv"):
    # 2-1. CSV 데이터 로드
    df = pd.read_csv(file_path)

    # 2-2. 텍스트 공백 제거 및 천 단위 콤마(,) 제거 후 수치형 변환
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(",", "")
                .str.replace(" ", "")
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2-3. 이상치 및 결측치 처리 (0 이하 값 처리 및 선형 보간/중앙값 대체)
    numeric_cols = [c for c in df.columns if c != "연도"]
    for col in numeric_cols:
        df[col] = df[col].apply(lambda x: np.nan if (pd.isna(x) or x <= 0) else x)
        df[col] = df[col].fillna(df[col].median())

    # 2-4. 파생 변수 생성 (인구 비율 및 고령화 지수 계산)
    df["유소년_비율(%)"] = (
        df["0-19세 (유소년/청소년)"] / df["총인구"] * 100
    ).round(2)
    df["청년층_비율(%)"] = (df["20-39세 (청년층)"] / df["총인구"] * 100).round(2)
    df["중장년층_비율(%)"] = (
        df["40-59세 (중장년층)"] / df["총인구"] * 100
    ).round(2)
    df["고령층_비율(%)"] = (
        df["60세 이상 (고령층)"] / df["총인구"] * 100
    ).round(2)

    # 고령화지수 = (60세 이상 인구 / 0-19세 인구) * 100
    df["고령화지수"] = (
        df["60세 이상 (고령층)"] / df["0-19세 (유소년/청소년)"] * 100
    ).round(2)

    return df


# 데이터 로딩
try:
    df_raw = load_and_clean_pop_data("pop_data.csv")
except Exception as e:
    st.error(
        f"⚠️ `pop_data.csv` 파일을 불러오는 중 오류가 발생했습니다: {e}\n\n"
        "파일이 `main.py`와 같은 폴더에 위치해 있는지 확인해 주세요."
    )
    st.stop()


# =========================================================
# 3. 사이드바 (Sidebar) 필터 컨트롤러
# =========================================================
st.sidebar.image(
    "https://img.icons8.com/isometric/100/bar-chart.png", width=70
)
st.sidebar.title("⚙️ 데이터 필터링")

# 연도 범위 선택 슬라이더
min_year = int(df_raw["연도"].min())
max_year = int(df_raw["연도"].max())

selected_years = st.sidebar.slider(
    "📅 분석 연도 범위 선택",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

# 필터링 적용
df_filtered = df_raw[
    (df_raw["연도"] >= selected_years[0])
    & (df_raw["연도"] <= selected_years[1])
].copy()

# 사이드바 요약 정보
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 선택 정보 요약")
st.sidebar.info(
    f"• **조회 기간**: {selected_years[0]}년 ~ {selected_years[1]}년\n"
    f"• **분석 연도 수**: 총 {len(df_filtered)}개 연도\n"
    f"• **최근 총인구**: {df_filtered['총인구'].iloc[-1]:,} 만 명"
)


# =========================================================
# 4. 메인 대시보드 헤더
# =========================================================
st.title("🇰🇷 대한민국 연도별 인구 구조 변화 대시보드")
st.markdown(
    "**`pop_data.csv`** 데이터를 정제하여 **유소년/청년/중장년/고령층의 인구 이동 추이**와 **고령화지수 변화**를 입체적으로 분석합니다."
)
st.markdown("---")


# =========================================================
# 5. 메인 탭(st.tabs) 구성
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📋 탭 1: 정제 데이터셋",
        "📊 탭 2: 핵심 지표 & 기술통계량",
        "📈 탭 3: 인구 구조 시각화 (Plotly)",
        "🧑‍🏫 탭 4: 데이터 탐구 멘토링",
    ]
)


# ---------------------------------------------------------
# [탭 1] 정제된 데이터셋
# ---------------------------------------------------------
with tab1:
    st.markdown("### 📋 자동 정제 및 파생변수가 추가된 인구 데이터셋")
    st.caption(
        "천 단위 콤마 제거 및 정수화 완료, 비율(%) 및 고령화지수 파생변수가 계산되었습니다."
    )

    st.dataframe(df_filtered, use_container_width=True)

    # CSV 다운로드 버튼
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 정제된 데이터 CSV 다운로드",
        data=csv_bytes,
        file_name=f"cleaned_pop_data_{selected_years[0]}_{selected_years[1]}.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------
# [탭 2] 주요 요약 통계량 & 핵심 지표
# ---------------------------------------------------------
with tab2:
    st.markdown("### 📌 핵심 대시보드 지표 (Selected Period)")

    # 시작 연도 대비 마지막 연도 변동량 계산
    first_row = df_filtered.iloc[0]
    last_row = df_filtered.iloc[-1]

    pop_change = int(last_row["총인구"] - first_row["총인구"])
    youth_ratio_change = round(
        last_row["유소년_비율(%)"] - first_row["유소년_비율(%)"], 2
    )
    senior_ratio_change = round(
        last_row["고령층_비율(%)"] - first_row["고령층_비율(%)"], 2
    )
    aging_index_change = round(
        last_row["고령화지수"] - first_row["고령화지수"], 2
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="👥 최근 총인구",
            value=f"{int(last_row['총인구']):,} 만명",
            delta=f"{pop_change:+} 만명 ({selected_years[0]}년 대비)",
        )
    with col2:
        st.metric(
            label="👶 유소년/청소년 비율",
            value=f"{last_row['유소년_비율(%)']:.2f} %",
            delta=f"{youth_ratio_change:+} %p",
            delta_color="inverse",
        )
    with col3:
        st.metric(
            label="🧓 60세 이상 고령층 비율",
            value=f"{last_row['고령층_비율(%)']:.2f} %",
            delta=f"{senior_ratio_change:+} %p",
        )
    with col4:
        st.metric(
            label="📈 고령화지수",
            value=f"{last_row['고령화지수']:.1f}",
            delta=f"{aging_index_change:+} pt",
        )

    st.markdown("---")
    st.markdown("### 📊 수치형 변수 기술통계 요약 (.describe())")
    st.dataframe(df_filtered.describe().round(2), use_container_width=True)


# ---------------------------------------------------------
# [탭 3] Plotly 인터랙티브 시각화
# ---------------------------------------------------------
with tab3:
    st.markdown("### 📈 1. 연령대별 인구 구성 변화 (누적 영역 차트)")

    # Plotly용 Melt 데이터 재구조화
    age_cols = [
        "0-19세 (유소년/청소년)",
        "20-39세 (청년층)",
        "40-59세 (중장년층)",
        "60세 이상 (고령층)",
    ]

    df_melted = df_filtered.melt(
        id_vars=["연도"],
        value_vars=age_cols,
        var_name="연령대",
        value_name="인구수(만명)",
    )

    # 영역 차트 (Stacked Area Chart)
    fig_area = px.area(
        df_melted,
        x="연도",
        y="인구수(만명)",
        color="연령대",
        title="<b>연도별 연령대별 인구수 변화 추이</b>",
        color_discrete_sequence=["#ef4444", "#3b82f6", "#10b981", "#f59e0b"],
        template="plotly_white",
    )
    fig_area.update_layout(
        font=dict(
            family="Malgun Gothic, Apple Gothic, NanumGothic, sans-serif",
            size=13,
        ),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig_area, use_container_width=True)

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📉 2. 유소년 vs 고령층 비율 비교 (%)")
        fig_line = px.line(
            df_filtered,
            x="연도",
            y=["유소년_비율(%)", "고령층_비율(%)"],
            title="<b>유소년/청소년 비율 vs 60세 이상 고령층 비율 추이</b>",
            markers=True,
            color_discrete_map={
                "유소년_비율(%)": "#ef4444",
                "고령층_비율(%)": "#f59e0b",
            },
            template="plotly_white",
        )
        fig_line.update_layout(
            font=dict(family="Malgun Gothic, Apple Gothic, sans-serif"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.markdown("### 🚀 3. 고령화지수 급증 추이")
        fig_bar = px.bar(
            df_filtered,
            x="연도",
            y="고령화지수",
            title="<b>연도별 고령화지수 (유소년 100명당 고령인구 수)</b>",
            text_auto=".1f",
            color="고령화지수",
            color_continuous_scale="Reds",
            template="plotly_white",
        )
        fig_bar.update_layout(
            font=dict(family="Malgun Gothic, Apple Gothic, sans-serif"),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# ---------------------------------------------------------
# [탭 4] 데이터 분석 멘토링
# ---------------------------------------------------------
with tab4:
    st.markdown("### 🧑‍🏫 멘토와 함께 파악하는 데이터 인사이트")

    st.info(
        "💡 **고령화지수**: 유소년 인구(0~19세) 100명당 고령 인구(60세 이상)의 비율을 나타내며, "
        "100을 넘어서면 고령인구가 유소년인구보다 많아졌음을 의미합니다."
    )

    with st.expander("💬 1단계: 그래프 형태 및 연령대별 교차점 관찰하기", expanded=True):
        st.write(
            "🙋‍♂️ **멘토 질문**: [유소년 vs 고령층 비율 차트]에서 두 선이 만나는 **교차점(2014~2015년경)**을 확인해 보세요!\n"
            "- 교차점 이전과 이후에 유소년 인구와 고령 인구의 역전 현상이 어떻게 진행되고 있나요?"
        )

    with st.expander("💬 2단계: 고령화지수의 폭발적 상승 추세 해석하기"):
        st.write(
            f"🙋‍♂️ **멘토 질문**: 2010년 고령화지수는 **{df_raw['고령화지수'].iloc[0]}**이었지만, "
            f"2024년에는 **{df_raw['고령화지수'].iloc[-1]}**로 약 3.2배 이상 급격히 상승했습니다.\n"
            "- 유소년 인구 감소와 고령 인구 증가가 동시에 일어날 때 지수 수치가 어떻게 가파라지는지 생각해 보세요!"
        )

    with st.expander("💬 3단계: 미래 사회 구조와 경제적 영향 탐구하기"):
        st.write(
            "🙋‍♂️ **멘토 질문**: 생산연령인구(20~59세)가 감당해야 할 부양 부담과 인구 절벽 현상에 대해 고민해 봅시다.\n"
            "- 학교/보육 시설의 변화, 연금 제도, 노동력 부족 문제 등에 이번 데이터 분석 결과가 어떤 시사점을 주나요?"
        )