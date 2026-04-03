import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="레이드 매칭 시스템", layout="wide")

# 세션 상태 초기화 (데이터 저장용)
if 'users' not in st.session_state:
    st.session_state.users = []
if 'raids' not in st.session_state:
    st.session_state.raids = {}

# 기본 관리자 비밀번호 설정 (원하는 대로 변경하세요)
ADMIN_PASSWORD = "admin" 

st.title("🎮 레이드 랜덤 매칭 및 관리 시스템")

menu = st.sidebar.selectbox("메뉴", ["사용자 신청", "신청 취소", "관리자 설정", "매칭 결과"])

# --- 1. 사용자 신청 페이지 ---
if menu == "사용자 신청":
    st.header("📝 레이드 참가 신청")
    with st.form("apply_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("닉네임")
            job = st.selectbox("직업", ["딜러", "치유성", "탱커"])
            user_pw = st.text_input("취소용 비밀번호 (숫자 4자리 권장)", type="password") # 취소용 비밀번호 추가
        with col2:
            power = st.number_input("전투력", min_value=0, step=100)
            companion = st.text_input("동반자 닉네임 (없으면 비움)")
        
        comp_type = st.radio("동반자 조건", ["없음", "같은 파티 희망", "같은 공격대 희망"])
        
        if st.form_submit_button("신청하기"):
            # 닉네임 중복 방지 로직 (선택 사항)
            if any(u['닉네임'] == name for u in st.session_state.users):
                st.error("이미 신청된 닉네임입니다. 다른 닉네임을 사용하거나 기존 신청을 취소해 주세요.")
            elif not name or not user_pw:
                st.error("닉네임과 취소용 비밀번호는 필수 입력 사항입니다.")
            else:
                st.session_state.users.append({
                    "닉네임": name, "직업": job, "전투력": power, 
                    "비밀번호": user_pw, # 비밀번호 저장
                    "동반자": companion, "조건": comp_type, "고정": False
                })
                st.success(f"{name}님 신청 완료!")

# --- 2. 신청 취소 페이지 (새로 추가됨) ---
elif menu == "신청 취소":
    st.header("🗑️ 참가 신청 취소")
    st.info("신청 시 입력했던 닉네임과 취소용 비밀번호를 입력해 주세요.")
    
    cancel_name = st.text_input("취소할 닉네임")
    cancel_pw = st.text_input("취소용 비밀번호", type="password")
    
    if st.button("신청 내역 삭제"):
        found = False
        for i, u in enumerate(st.session_state.users):
            if u['닉네임'] == cancel_name and u['비밀번호'] == cancel_pw:
                del st.session_state.users[i]
                found = True
                
                # 고정 인원 목록에서도 삭제
                for raid in st.session_state.raids.values():
                    raid['fixed'] = [f for f in raid['fixed'] if f['닉네임'] != cancel_name]
                    
                st.success(f"{cancel_name}님의 신청 내역이 성공적으로 취소되었습니다.")
                break
                
        if not found:
            st.error("닉네임 또는 비밀번호가 일치하지 않거나, 신청 내역이 없습니다.")

# --- 3. 관리자 설정 페이지 (보안 추가됨) ---
elif menu == "관리자 설정":
    st.header("👑 관리자 설정")
    
    # 관리자 비밀번호 검증
    input_pw = st.text_input("관리자 비밀번호를 입력하세요", type="password")
    
    if input_pw == ADMIN_PASSWORD:
        st.success("관리자 인증 성공!")
        st.markdown("---")
        
        # 공격대 생성
        st.subheader("🛠️ 공격대 설정 및 고정 인원 관리")
        col1, col2 = st.columns(2)
        with col1:
            raid_name = st.text_input("공격대 이름 (예: 1공대, A팀)")
            raid_cap = st.number_input("총 인원수 (4의 배수 권장)", min_value=4, step=4, value=8)
            if st.button("공격대 추가/수정"):
                # 기존 고정 인원 유지하면서 설정 업데이트
                current_fixed = st.session_state.raids.get(raid_name, {}).get('fixed', [])
                st.session_state.raids[raid_name] = {"capacity": raid_cap, "fixed": current_fixed}
                st.info(f"{raid_name} 설정 완료 (정원: {raid_cap}명)")

        # 고정 인원 지정
        if st.session_state.users and st.session_state.raids:
            st.markdown("---")
            st.subheader("📌 고정 인원 지정")
            user_names = [u['닉네임'] for u in st.session_state.users]
            selected_user = st.selectbox("고정할 사용자 선택", user_names)
            selected_raid = st.selectbox("배정할 공격대 선택", list(st.session_state.raids.keys()))
            
            if st.button("고정 인원으로 확정"):
                for u in st.session_state.users:
                    if u['닉네임'] == selected_user:
                        u['고정'] = True
                        st.session_state.raids[selected_raid]['fixed'].append(u)
                        st.success(f"{selected_user}님이 {selected_raid}에 고정되었습니다.")
    elif input_pw:
        st.error("비밀번호가 일치하지 않습니다.")

# --- 4. 매칭 결과 페이지 ---
elif menu == "매칭 결과":
    st.header("🎲 매칭 결과 확인")
    
    if not st.session_state.raids:
        st.warning("관리자 설정에서 공격대를 먼저 생성해 주세요.")
    else:
        if st.button("랜덤 매칭 시작"):
            # 매칭 로직
            all_participants = st.session_state.users.copy()
            result_display = {}

            for r_name, config in st.session_state.raids.items():
                cap = config['capacity']
                current_raid_members = config['fixed'].copy()
                
                # 남은 인원 중 고정되지 않은 사람 필터링
                available = [u for u in all_participants if not u['고정']]
                needed = cap - len(current_raid_members)
                
                # 랜덤 배분
                sampled = random.sample(available, min(len(available), needed))
                current_raid_members.extend(sampled)
                
                # 배분된 인원은 전체 리스트에서 '고정' 처리하여 중복 방지
                for s in sampled:
                    for u in all_participants:
                        if u['닉네임'] == s['닉네임']:
                            u['고정'] = True 
                
                # 부족하면 공석 채우기
                while len(current_raid_members) < cap:
                    current_raid_members.append({"닉네임": "공석(공팟)", "직업": "미정", "전투력": 0})
                
                result_display[r_name] = current_raid_members
                
            # 결과 화면 출력
            for r_name, members in result_display.items():
                st.subheader(f"📍 {r_name}")
                # 비밀번호 등 불필요한 정보는 표에서 숨기기
                display_df = pd.DataFrame(members)
                if '비밀번호' in display_df.columns:
                    display_df = display_df.drop(columns=['비밀번호', '고정'])
                
                st.table(display_df)
                avg_p = display_df['전투력'].mean()
                st.write(f"**평균 전투력: {avg_p:,.0f}**")
