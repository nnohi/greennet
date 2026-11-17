import os

import pandas as pd
import streamlit as st

st.set_page_config(page_title="GreenNet", page_icon="🌿", layout="wide")

# ------------------------------------------------------------
# 1. 데이터 불러오기
#   - welfare.csv 가 있으면 그 파일을 사용하고,
#   - 없으면 아래 예시(더미) 데이터를 사용합니다.
#   welfare.csv 칼럼: 시도, 위도, 경도, 고령인구비율, 1인가구비율, 수급자비율
# ------------------------------------------------------------
SAMPLE = [
    # 시도, 위도, 경도, 고령인구비율(%), 1인가구비율(%), 수급자비율(%)
    ("서울", 37.5665, 126.9780, 18.0, 36.0, 4.5),
    ("부산", 35.1796, 129.0756, 22.0, 36.5, 5.8),
    ("대구", 35.8714, 128.6014, 19.5, 33.0, 5.2),
    ("인천", 37.4563, 126.7052, 16.5, 31.0, 4.4),
    ("광주", 35.1595, 126.8526, 16.0, 34.0, 5.5),
    ("대전", 36.3504, 127.3845, 15.5, 36.0, 4.6),
    ("울산", 35.5384, 129.3114, 15.0, 29.0, 3.9),
    ("세종", 36.4800, 127.2890, 11.0, 28.0, 2.5),
    ("경기", 37.4138, 127.5183, 15.0, 30.0, 3.3),
    ("강원", 37.8228, 128.1555, 24.0, 36.0, 5.3),
    ("충북", 36.6357, 127.4917, 20.5, 35.0, 4.2),
    ("충남", 36.5184, 126.8000, 21.5, 33.5, 4.4),
    ("전북", 35.7175, 127.1530, 24.5, 35.0, 6.8),
    ("전남", 34.8161, 126.4629, 28.0, 34.0, 6.5),
    ("경북", 36.4919, 128.8889, 26.0, 36.0, 5.5),
    ("경남", 35.4606, 128.2132, 20.0, 32.0, 4.7),
    ("제주", 33.4996, 126.5312, 17.5, 33.0, 4.0),
]
COLUMNS = ["시도", "위도", "경도", "고령인구비율", "1인가구비율", "수급자비율"]


@st.cache_data
def load_data():
    if os.path.exists("welfare.csv"):
        return pd.read_csv("welfare.csv"), False
    return pd.DataFrame(SAMPLE, columns=COLUMNS), True


df, is_sample = load_data()

# ------------------------------------------------------------
# 2. 사각지대 위험도 계산 (0~100점)
#    세 지표를 0~1로 정규화(min-max)한 뒤 가중 평균
# ------------------------------------------------------------
INDICATORS = ["고령인구비율", "1인가구비율", "수급자비율"]

st.sidebar.header("⚙️ 설정")
st.sidebar.caption("지표별 가중치 (합이 1이 아니어도 자동 보정)")
weights = {
    col: st.sidebar.slider(col, 0.0, 1.0, 1.0 / 3, 0.05) for col in INDICATORS
}
total_w = sum(weights.values()) or 1.0


def minmax(s):
    return (s - s.min()) / (s.max() - s.min())


df = df.copy()
df["위험도"] = sum(minmax(df[c]) * w for c, w in weights.items()) / total_w * 100
df["위험도"] = df["위험도"].round(1)

# 지도 색상: 위험도가 높을수록 빨간색, 크기도 크게
df["색상"] = df["위험도"].apply(
    lambda v: "#%02x%02x%02x" % (int(60 + 195 * v / 100), int(180 - 140 * v / 100), 80)
)
df["크기"] = 8000 + df["위험도"] * 1500

# ------------------------------------------------------------
# 3. 화면
# ------------------------------------------------------------
st.title("🌿 GreenNet")
st.subheader("데이터로 찾는 우리 동네 복지 사각지대")

if is_sample:
    st.warning(
        "현재 **예시 데이터**로 표시 중입니다. 실제 값은 공공데이터포털·복지로 통계로 교체해야 합니다."
    )

# 상단 요약
top = df.sort_values("위험도", ascending=False).iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("분석 지역 수", f"{len(df)}개 시도")
c2.metric("위험도 1위 지역", top["시도"], f"{top['위험도']}점")
c3.metric("평균 위험도", f"{df['위험도'].mean():.1f}점")

tab1, tab2, tab3 = st.tabs(["🗺️ 위험도 지도", "📊 지표 비교", "📋 데이터"])

with tab1:
    st.caption("빨갛고 클수록 사각지대 위험도가 높은 지역입니다.")
    st.map(df, latitude="위도", longitude="경도", size="크기", color="색상")

with tab2:
    indicator = st.selectbox("비교할 지표", INDICATORS + ["위험도"])
    st.bar_chart(df.set_index("시도")[indicator].sort_values(ascending=False))

    region = st.selectbox("지역 선택", df["시도"])
    row = df[df["시도"] == region].iloc[0]
    st.write(f"**{region}** 상세")
    st.dataframe(
        row[INDICATORS + ["위험도"]].to_frame("값").T, use_container_width=True
    )

with tab3:
    st.dataframe(
        df[["시도"] + INDICATORS + ["위험도"]].sort_values("위험도", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

st.caption("출처: 공공데이터포털(data.go.kr), 복지로 복지통계(bokjiro.go.kr)")
