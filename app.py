import streamlit as st
import pandas as pd
import random
import uuid # 그룹 생성을 위한 고유 ID 라이브러리

st.set_page_config(page_title="레이드 매칭 시스템", layout="wide")

# 세션 상태 초기화 (데이터 저장 및 동적 UI용)
if 'users' not in st.session_state:
    st.session_state.users = []
if 'raids' not in st.session_state:
    st.session_state.raids = {}
if 'comp_count' not in st.session_state:
    st.session_state.comp_count = 0

# 기본 관리자 비밀번호 설정
ADMIN_PASSWORD = "1234" 

st.title("🎮 레이드 랜덤 매칭 및 관리 시스템")

menu = st.sidebar.selectbox("메뉴", ["사용자 신청", "신청 취소", "관리자 설정", "매칭 결과"])

# --- 1. 사용자 신청 페이지 ---
if menu == "사용자 신청":
    st.header("📝 레이드 참가 신청")
    st.info("💡 동반자가 있다면 아래 버튼을 먼저 눌러 인원을 추가한 뒤 폼을 작성해 주세요.")
    
    # 동반자 수 조절 버튼 (폼 외부에 배치하여 즉각 반응하도록 함)
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("➕ 동반자 인원 추가"):
            st.session_state.comp_count += 1
    with col2:
        if st.button("➖ 동반자 인원 빼기") and st.session_state.comp_count > 0:
            st.session_state.comp_count -= 1

    with st.form("apply_form"):
        st.subheader("👤 본인 정보")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("닉네임")
            job = st.selectbox("직업", ["딜러", "치유성", "탱커"])
            user_pw = st.text_input("취소용 비밀번호 (숫자 4자리 권장)", type="password")
        with c2:
            power = st.number_input("전투력", min_value=0, step=100)
        
        # 동반자 정보 입력란 동적 생성
        comp_data = []
        if st.session_state.comp_count > 0:
            st.markdown("---")
            st.subheader(f"👥 동반자 정보 (총 {st.session_state.comp_count}명)")
            
            for i in range(st.session_state.comp_count):
                st.markdown(f"**동반자 {i+1}**")
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    c_name = st.text_input("닉네임", key=f"c_name_{i}")
                    c_job = st.selectbox("직업", ["딜러", "치유성", "탱커"], key=f"c_job_{i}")
                with cc2:
                    c_power = st.number_input("전투력", min_value=0, step=100, key=f"c_pow_{i}")
                with cc3:
                    c_type = st.radio("본인과의 조건", ["같은 파티 희망", "같은 공격대 희망"], key=f"c_type_{i}")
                
                comp_data.append({"name": c_name, "job": c_job, "power": c_power, "type": c_type})

        if st.form_submit_button("신청하기"):
            if any(u['닉네임'] == name for u in st.session_state.users):
                st.error("이미 신청된 닉네임입니다.")
            elif not name or not user_pw:
                st.error("본인의 닉네임과 취소용 비밀번호는 필수 입력 사항입니다.")
            else:
                # 일행을 하나로 묶어줄 고유 그룹 ID 생성
                group_id = str(uuid.uuid4())[:8]
                
                # 본인 데이터 저장
                st.session_state.users.append({
                    "닉네임": name, "직업": job, "전투력": power, 
                    "비밀번호": user_pw, "고정": False,
                    "그룹ID": group_id, "관계": "본인(대표)", "조건": "없음"
                })
                
                # 동반자 데이터 저장
                added_companions = 0
                for c in comp_data:
                    if c['name']: # 이름이 입력된 동반자만 저장
                        st.session_state.users.append({
                            "닉네임": c['name'], "직업": c['job'], "전투력": c['power'], 
                            "비밀번호": user_pw, "고정": False, # 비밀번호는 대표자 것 공유
                            "그룹ID": group_id, "관계": f"{name}의 동반자", "조건": c['type']
                        })
                        added_companions += 1
                        
                st.success(f"{name}님 그룹 (총 {1 + added_companions}명) 신청 완료!")

# --- 2. 신청 취소 페이지 (그룹 취소 로직으로 변경) ---
elif menu == "신청 취소":
    st.header("🗑️ 참가 신청 취소")
    st.info("신청 시 입력했던 본인(대표자)의 닉네임과 취소용 비밀번호를 입력해 주세요. (일행 전체가 함께 취소됩니다)")
    
    cancel_name = st.text_input("취소할 닉네임")
    cancel_pw = st.text_input("취소용 비밀번호", type="password")
    
    if st.button("신청 내역 삭제"):
        target_group_id = None
        # 입력한 정보로 그룹 ID 찾기
        for u in st.session_state.users:
            if u['닉네임'] == cancel_name and u['비밀번호'] == cancel_pw:
                target_group_id = u['그룹ID']
                break
                
        if target_group_id:
            # 해당 그룹 ID를 가진 모든 유저(본인+동반자) 삭제
            st.session_state.users = [u for u in st.session_state.users if u['그룹ID'] != target_group_id]
            
            # 고정 인원 목록에서도 해당 그룹원들 삭제
            for raid in st.session_state.raids.values():
                raid['fixed'] = [f for f in raid['fixed'] if f.get('그룹ID') != target_group_id]
                
            st.success(f"{cancel_name}님 그룹의 신청 내역이 성공적으로 취소되었습니다.")
        else:
            st.error("닉네임 또는 비밀번호가 일치하지 않거나, 신청 내역이 없습니다.")

# --- 3. 관리자 설정 페이지 ---
elif menu == "관리자 설정":
    st.header("👑 관리자 설정")
    
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
            all_participants = st.session_state.users.copy()
            result_display = {}

            for r_name, config in st.session_state.raids.items():
                cap = config['capacity']
                current_raid_members = config['fixed'].copy()
                
                available = [u for u in all_participants if not u['고정']]
                needed = cap - len(current_raid_members)
                
                sampled = random.sample(available, min(len(available), needed))
                current_raid_members.extend(sampled)
                
                for s in sampled:
                    for u in all_participants:
                        if u['닉네임'] == s['닉네임']:
                            u['고정'] = True 
                
                while len(current_raid_members) < cap:
                    current_raid_members.append({"닉네임": "공석(공팟)", "직업": "-", "전투력": 0})
                
                result_display[r_name] = current_raid_members
                
            for r_name, members in result_display.items():
                st.subheader(f"📍 {r_name}")
                display_df = pd.DataFrame(members)
                
                # 표에서 불필요하거나 민감한 데이터 숨기기
                cols_to_drop = ['비밀번호', '고정', '그룹ID']
                for col in cols_to_drop:
                    if col in display_df.columns:
                        display_df = display_df.drop(columns=[col])
                
                st.table(display_df)
                if not display_df.empty and '전투력' in display_df.columns:
                    avg_p = display_df['전투력'].mean()
                    st.write(f"**평균 전투력: {avg_p:,.0f}**")
