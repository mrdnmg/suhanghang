import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        # 지역별 인구 데이터셋 출처 및 소개
        st.markdown("""
        ---
        **Population Trends 데이터셋**

        - 설명: 연도별로 지역별 인구, 출생아 수, 사망자 수 등을 기록한 통계 데이터입니다.  
        - 주요 목적: 대한민국 각 지역의 인구 구조 변화 및 추이를 분석하여  
          출생/사망 추세, 변화량, 예측 등을 시각화합니다.
        - 주요 변수:
          - `연도`: 인구 데이터가 측정된 연도  
          - `지역`: 해당 통계가 적용되는 행정구역  
          - `인구`: 해당 연도의 총 인구 수  
          - `출생아수(명)`: 출생 인원  
          - `사망자수(명)`: 사망 인원  
          - 기타 행정통계 항목들

        ---
        이 앱은 `population_trends.csv`를 업로드하여  
        기초 통계, 연도별 추이, 지역별 분석, 변화량 및 시각화 분석을 제공합니다.
        """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 지역별 인구 분석 EDA")

        import matplotlib.font_manager as fm
        plt.rcParams['axes.unicode_minus'] = False

        uploaded = st.file_uploader("population_trends.csv 파일을 업로드해주세요", type="csv")
        if not uploaded:
            st.info("CSV 파일을 업로드하면 분석 결과가 표시됩니다.")
            return

        df = pd.read_csv(uploaded)

        # 한글 지역명을 영어로 매핑
        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
            '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
            '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
            '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju', '전국': 'Nationwide'
        }
        df['지역'] = df['지역'].replace(region_map)

        df.replace('-', 0, inplace=True)
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        with tab1:
            st.header("📌 기초 통계 및 구조 확인 (결측치/중복 포함)")
            st.subheader("데이터프레임 구조")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.subheader("기초 통계량")
            st.dataframe(df.describe())
            st.subheader("결측치 개수")
            st.dataframe(df.isnull().sum())
            st.subheader("중복 행 개수")
            st.write(f"중복 행: {df.duplicated().sum()}개")

        with tab2:
            st.header("📈 연도별 전국 인구 추이 분석")
            nation = df[df['지역'] == 'Nationwide']
            plt.figure(figsize=(10, 4))
            sns.lineplot(x='연도', y='인구', data=nation)
            last3 = nation.sort_values('연도').tail(3)
            avg_delta = (last3['출생아수(명)'].mean() - last3['사망자수(명)'].mean())
            pred_2035 = nation['인구'].iloc[-1] + avg_delta * (2035 - nation['연도'].iloc[-1])
            plt.axhline(pred_2035, color='red', linestyle='--', label='Prediction 2035')
            plt.title("National Population Trend")
            plt.xlabel("Year")
            plt.ylabel("Population")
            plt.legend()
            st.pyplot(plt.gcf())
            st.write(f"2035 Predicted Population: {int(pred_2035):,}")

        with tab3:
            st.header("📊 Population Change by Region (last 5 years)")
            df_sorted = df.sort_values(['지역', '연도'])
            recent = df[df['연도'] >= df['연도'].max() - 5]
            pivot = recent.pivot(index='연도', columns='지역', values='인구')
            delta = pivot.iloc[-1] - pivot.iloc[0]
            delta = delta.drop('Nationwide', errors='ignore').sort_values(ascending=False)
            plt.figure(figsize=(10, 8))
            ax1 = sns.barplot(x=delta.values / 1000, y=delta.index, orient='h')
            ax1.set_title("Population Change by Region")
            ax1.set_xlabel("Change (thousands)")
            ax1.set_ylabel("Region")
            for i, val in enumerate(delta.values / 1000):
                ax1.text(val, i, f'{val:.1f}', va='center')
            plt.tight_layout()
            st.pyplot(plt.gcf())

            st.subheader("📈 Growth Rate (%)")
            base = pivot.iloc[0]
            rate = ((pivot.iloc[-1] - base) / base * 100).drop('Nationwide', errors='ignore').sort_values(ascending=False)
            plt.figure(figsize=(10, 8))
            ax2 = sns.barplot(x=rate.values, y=rate.index, orient='h')
            ax2.set_title("Population Growth Rate by Region")
            ax2.set_xlabel("Growth Rate (%)")
            ax2.set_ylabel("Region")
            for i, val in enumerate(rate.values):
                ax2.text(val, i, f'{val:.1f}%', va='center')
            plt.tight_layout()
            st.pyplot(plt.gcf())

        with tab4:
            st.header("📋 Top 100 Population Changes")
            df_diff = df[df['지역'] != 'Nationwide'].sort_values(['지역', '연도'])
            df_diff['증감'] = df_diff.groupby('지역')['인구'].diff()
            top_diff = df_diff.sort_values('증감', ascending=False).head(100)
            top_diff['증감'] = top_diff['증감'].astype(int)
            styled = top_diff.style.format({"증감": "{:,}"}).background_gradient(
                subset=['증감'], cmap='RdBu', axis=0)
            st.dataframe(styled)

        with tab5:
            st.header("🗺️ Stacked Area Population by Region")
            pivot = df.pivot(index='연도', columns='지역', values='인구')
            pivot = pivot.drop(columns='Nationwide', errors='ignore').fillna(0)
            pivot = pivot.div(1000)
            plt.figure(figsize=(12, 6))
            ax = pivot.plot.area(legend=True)
            ax.legend(title='Region', loc='center left', bbox_to_anchor=(1.0, 0.5))
            plt.title("Population Trend by Region")
            plt.xlabel("Year")
            plt.ylabel("Population (thousands)")
            plt.tight_layout()
            st.pyplot(plt.gcf())

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()