import streamlit as st
import time
import json
import os
import html
import math
from datetime import date, timedelta

# ==========================================
# 0. 기본 설정 및 데이터 저장
# ==========================================

st.set_page_config(
    page_title="뼈마디 생존일지 & 힐링 정원",
    page_icon="🌿",
    layout="wide"
)

DATA_FILE = "app_data.json"

DEFAULT_DATA = {
    "points": 50,
    "garden": ["🌱 새싹"],
    "diaries": [],
    "completion_dates": []
}


def load_data():
    """JSON 파일에서 데이터를 안전하게 불러옵니다."""
    if not os.path.exists(DATA_FILE):
        return {
            "points": 50,
            "garden": ["🌱 새싹"],
            "diaries": [],
            "completion_dates": set()
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("데이터 형식이 올바르지 않습니다.")

        points = data.get("points", 50)
        garden = data.get("garden", ["🌱 새싹"])
        diaries = data.get("diaries", [])
        completion_dates = data.get("completion_dates", [])

        # 데이터 형식 검증
        if not isinstance(points, (int, float)) or points < 0:
            points = 50

        if not isinstance(garden, list):
            garden = ["🌱 새싹"]

        if not isinstance(diaries, list):
            diaries = []

        if not isinstance(completion_dates, list):
            completion_dates = []

        return {
            "points": int(points),
            "garden": [str(item) for item in garden],
            "diaries": [str(item) if isinstance(item, str) else item for item in diaries],
            "completion_dates": {
                str(d) for d in completion_dates
            }
        }

    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return {
            "points": 50,
            "garden": ["🌱 새싹"],
            "diaries": [],
            "completion_dates": set()
        }


def save_data():
    """임시 파일에 저장한 뒤 교체하여 저장 중 파일 손상을 줄입니다."""
    data = {
        "points": st.session_state.points,
        "garden": st.session_state.garden,
        "diaries": st.session_state.diaries,
        "completion_dates": sorted(
            list(st.session_state.completion_dates)
        )
    }

    temp_file = DATA_FILE + ".tmp"

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        os.replace(temp_file, DATA_FILE)
        return True

    except OSError:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        return False


# ==========================================
# 1. 세션 상태 초기화
# ==========================================

if "data_initialized" not in st.session_state:
    init_data = load_data()

    st.session_state.points = init_data["points"]
    st.session_state.garden = init_data["garden"]
    st.session_state.diaries = init_data["diaries"]
    st.session_state.completion_dates = init_data["completion_dates"]

    st.session_state.data_initialized = True

# 타이머 상태
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "timer_mode" not in st.session_state:
    st.session_state.timer_mode = "집중/업무 모드"

if "remaining_seconds" not in st.session_state:
    st.session_state.remaining_seconds = 25 * 60

if "timer_end_time" not in st.session_state:
    st.session_state.timer_end_time = None


# ==========================================
# 2. 공통 함수
# ==========================================

def get_streak():
    """오늘 또는 어제 기록을 기준으로 연속 달성 일수를 계산합니다."""
    dates = st.session_state.completion_dates

    today = date.today()
    yesterday = today - timedelta(days=1)

    if str(today) in dates:
        check_date = today
    elif str(yesterday) in dates:
        check_date = yesterday
    else:
        return 0

    streak = 0

    while str(check_date) in dates:
        streak += 1
        check_date -= timedelta(days=1)

    return streak


def show_save_result():
    if not save_data():
        st.warning(
            "데이터 저장에 실패했습니다. "
            "저장 공간과 파일 접근 권한을 확인해주세요."
        )


# ==========================================
# 3. 앱 제목
# ==========================================

st.title("🌿 뼈마디 생존일지 & 힐링 정원 (Pro Ver.)")
st.write("학생, 직장인, 주부를 위한 스마트 웰니스 정원 앱")


# ==========================================
# 4. 사이드바 설정
# ==========================================

st.sidebar.header("⚙️ 설정 및 페르소나")

mode = st.sidebar.selectbox(
    "내 페르소나 선택",
    [
        "학생 (도서관/책상)",
        "직장인 (사무실/오피스)",
        "주부 (홈/살림)"
    ]
)

today = date.today()
today_str = str(today)

streak = get_streak()

st.sidebar.markdown(f"""
### 🔥 연속 달성 현황

**현재 연속 스트레칭: {streak}일째**
""")

st.sidebar.divider()

st.sidebar.header("⏰ 알림 및 타이머 설정")

work_time = st.sidebar.slider(
    "집중/업무 시간 (분)",
    min_value=5,
    max_value=60,
    value=25,
    step=5
)

break_time = st.sidebar.slider(
    "스트레칭 휴식 시간 (분)",
    min_value=1,
    max_value=10,
    value=3,
    step=1
)


# ==========================================
# 5. 아이템 상점
# ==========================================

st.sidebar.divider()

st.sidebar.header(
    f"🛒 아이템 상점 (내 골드: 🪙 {st.session_state.points}G)"
)

items_for_sale = {
    "🌷 튤립": 20,
    "🌻 해바라기": 30,
    "🪵 나무 벤치": 40,
    "🐇 토끼 조각상": 50,
    "💧 작은 연못": 60
}

for item, price in items_for_sale.items():

    if st.sidebar.button(
        f"{item} (가격: {price}G) 구입",
        key=f"buy_{item}"
    ):

        if st.session_state.points >= price:

            # 골드 차감
            st.session_state.points -= price

            # 구매한 아이템을 정원에 실제 추가
            st.session_state.garden.append(item)

            show_save_result()

            st.sidebar.success(
                f"{item} 구매 완료! 정원에 추가되었습니다."
            )

            st.rerun()

        else:
            st.sidebar.error("골드가 부족해요!")


# ==========================================
# 6. 메인 탭 구성
# ==========================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🏡 내 정원 꾸미기",
    "⏱️ 스마트 타이머",
    "💪 맞춤 스트레칭 가이드",
    "📖 오늘의 뼈마디 일기"
])


# ==========================================
# TAB 1. 정원 꾸미기
# ==========================================

with tab1:

    st.subheader(f"✨ {mode}님의 힐링 정원")

    garden_display = " ".join(
        html.escape(str(item))
        for item in st.session_state.garden
    )

    st.markdown(f"""
    <div style="
        padding: 25px;
        background-color: #f0f8ff;
        border-radius: 15px;
        font-size: 30px;
        text-align: center;
        min-height: 100px;
    ">
        {garden_display}
    </div>
    """, unsafe_allow_html=True)

    st.write(
        f"현재 보유 골드: 🪙 **{st.session_state.points}G**"
    )

    st.write(
        f"📅 총 스트레칭 달성일: "
        f"**{len(st.session_state.completion_dates)}일**"
    )

    st.caption("💾 활동 데이터는 JSON 파일에 영구 저장됩니다.")


# ==========================================
# TAB 2. 스마트 타이머
# ==========================================

with tab2:

    st.subheader("⏱️ 집중 & 휴식 자동 전환 타이머")

    st.write(
        "집중 시간이 끝나면 휴식 시간으로, "
        "휴식 시간이 끝나면 집중 시간으로 자동 전환됩니다."
    )

    current_timer_mode = st.radio(
        "시작할 모드를 선택하세요.",
        ["집중/업무 모드", "휴식 및 스트레칭 모드"],
        horizontal=True
    )

    work_seconds = work_time * 60
    break_seconds = break_time * 60

    @st.fragment(run_every="1s")
    def timer_panel(selected_mode, focus_seconds, rest_seconds):

        col1, col2, col3 = st.columns(3)

        # 시작 버튼
        with col1:
            if st.button("▶️ 타이머 시작", use_container_width=True):

                st.session_state.timer_running = True
                st.session_state.timer_mode = selected_mode

                if "집중" in selected_mode:
                    duration = focus_seconds
                else:
                    duration = rest_seconds

                st.session_state.remaining_seconds = duration
                st.session_state.timer_end_time = time.time() + duration

        # 일시정지 버튼
        with col2:
            if st.button("⏸️ 일시정지", use_container_width=True):

                if st.session_state.timer_running and st.session_state.timer_end_time:

                    remaining = (
                        st.session_state.timer_end_time - time.time()
                    )

                    st.session_state.remaining_seconds = max(
                        0, math.ceil(remaining)
                    )

                st.session_state.timer_running = False
                st.session_state.timer_end_time = None

        # 초기화 버튼
        with col3:
            if st.button("⏹️ 초기화", use_container_width=True):

                st.session_state.timer_running = False
                st.session_state.timer_mode = selected_mode
                st.session_state.timer_end_time = None

                if "집중" in selected_mode:
                    st.session_state.remaining_seconds = focus_seconds
                else:
                    st.session_state.remaining_seconds = rest_seconds

        # --------------------------------------
        # 타이머 진행 및 자동 전환
        # --------------------------------------

        completed_message = None

        if st.session_state.timer_running and st.session_state.timer_end_time:

            remaining = (
                st.session_state.timer_end_time - time.time()
            )

            if remaining <= 0:

                # 현재 모드 종료
                if "집중" in st.session_state.timer_mode:

                    completed_message = (
                        "🎉 집중 시간 종료! 휴식 시간이 시작됩니다."
                    )

                    st.session_state.timer_mode = (
                        "휴식 및 스트레칭 모드"
                    )

                    next_duration = rest_seconds

                else:

                    completed_message = (
                        "💪 휴식 시간 종료! 다시 집중할 시간입니다."
                    )

                    st.session_state.timer_mode = (
                        "집중/업무 모드"
                    )

                    next_duration = focus_seconds

                # 다음 모드를 자동으로 시작
                st.session_state.remaining_seconds = next_duration
                st.session_state.timer_end_time = (
                    time.time() + next_duration
                )

            else:

                st.session_state.remaining_seconds = max(
                    0, math.ceil(remaining)
                )

        # --------------------------------------
        # 타이머 화면 표시
        # --------------------------------------

        remaining_seconds = st.session_state.remaining_seconds

        mins, secs = divmod(remaining_seconds, 60)

        if st.session_state.timer_running:
            status = "🟢 진행 중"
        else:
            status = "⏸️ 일시정지"

        st.markdown(f"""
        <div style="
            padding: 30px;
            background-color: #fffacd;
            border-radius: 15px;
            text-align: center;
            color: #333;
        ">
            <div style="font-size: 18px;">
                {html.escape(st.session_state.timer_mode)}
            </div>

            <div style="
                font-size: 48px;
                font-weight: bold;
                margin: 10px 0;
            ">
                {mins:02d}:{secs:02d}
            </div>

            <div style="font-size: 15px;">
                {status}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if completed_message:
            st.success(completed_message)

    timer_panel(
        current_timer_mode,
        work_seconds,
        break_seconds
    )


# ==========================================
# TAB 3. 맞춤 스트레칭 가이드
# ==========================================

with tab3:

    st.subheader("💪 부위별 정확한 운동 방법 및 가이드")

    target_area = st.selectbox(
        "타겟 부위 선택",
        [
            "🐢 거북목 & 목·어깨 릴렉스",
            "💼 수근관증후군 예방 손목 스트레칭",
            "🪵 척추 신전 및 허리 요통 방지 운동"
        ]
    )

    if "거북목" in target_area:

        st.markdown("### 📌 1. 턱 당기기 (Chin Tuck)")

        st.write(
            "• **방법:** 시선을 정면으로 향한 채 "
            "턱을 뒤쪽 수평으로 밀어 넣습니다. "
            "목 뒤쪽이 길어지는 느낌을 유지합니다."
        )

        st.image(
            "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&q=80",
            width=400
        )

    elif "손목" in target_area:

        st.markdown("### 📌 2. 손목 굴근 및 신근 스트레칭")

        st.write(
            "• **방법:** 팔을 앞으로 뻗고 손바닥 또는 "
            "손등이 위를 향하도록 한 뒤, "
            "반대 손으로 손가락을 부드럽게 당깁니다."
        )

        st.image(
            "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=600&q=80",
            width=400
        )

    else:

        st.markdown("### 📌 3. 척추 신전 운동")

        st.write(
            "• **방법:** 통증이 없는 범위에서 "
            "엎드린 자세로 팔꿈치나 손바닥을 지지하여 "
            "상체를 부드럽게 들어 올립니다."
        )

        st.image(
            "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=600&q=80",
            width=400
        )

    st.caption(
        "※ 운동 중 통증이나 저림이 심해지면 중단하세요. "
        "개인의 증상에 따라 운동 적합성이 달라질 수 있습니다."
    )

    st.divider()

    already_done_today = (
        today_str in st.session_state.completion_dates
    )

    if already_done_today:

        st.warning(
            "🎉 오늘의 스트레칭 보상을 이미 받으셨습니다! "
            "내일 또 만나요."
        )

        st.button(
            "✅ 오늘의 스트레칭 완료 (보상 수령 완료)",
            disabled=True
        )

    else:

        if st.button("✅ 스트레칭 완료하고 골드 받기 (+30G)"):

            st.session_state.points += 30

            st.session_state.completion_dates.add(today_str)

            show_save_result()

            st.success(
                f"[{target_area}] 완료! "
                "🪙 30골드가 적립되었습니다."
            )

            st.balloons()
            st.rerun()


# ==========================================
# TAB 4. 오늘의 뼈마디 일기
# ==========================================

with tab4:

    st.subheader("📖 오늘의 뼈마디 일기")

    with st.form("diary_form", clear_on_submit=True):

        pain_level = st.selectbox(
            "오늘 가장 뻐근했던 부위",
            [
                "목 (거북목)",
                "어깨 (라운드숄더)",
                "손목 (건초염)",
                "허리 (요통)"
            ]
        )

        diary_text = st.text_input(
            "한줄 일기를 작성하세요.",
            placeholder="예: 오늘 하루도 고생했다 내 척추야..."
        )

        submit_diary = st.form_submit_button(
            "일기 저장하기"
        )

    if submit_diary:

        if diary_text.strip():

            new_entry = {
                "date": today_str,
                "area": pain_level,
                "content": diary_text.strip()
            }

            st.session_state.diaries.append(new_entry)

            show_save_result()

            st.success("일기가 성공적으로 저장되었습니다!")

            st.rerun()

        else:

            st.warning("일기 내용을 입력해주세요.")

    st.divider()

    st.subheader("📚 나의 일기 & 기록 히스토리")

    if not st.session_state.diaries:

        st.info("아직 작성된 일기가 없습니다.")

    else:

        for index, diary in enumerate(
            reversed(st.session_state.diaries)
        ):

            if isinstance(diary, dict):

                diary_date = diary.get("date", "")
                diary_area = diary.get("area", "")
                diary_content = diary.get("content", "")

                with st.container(border=True):

                    st.markdown(
                        f"**📅 {diary_date} | {diary_area}**"
                    )

                    st.write(diary_content)

            else:

                with st.container(border=True):
                    st.write(f"• {diary}")
