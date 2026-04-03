import streamlit as st
import pandas as pd
import random
import uuid

st.set_page_config(page_title="레이드 매칭 시스템 v5", layout="wide")

# --- 직업 데이터 정의 ---
JOB_DETAILS = {
    "살성": "딜러", "궁성": "딜러", "마도성": "딜러", "정령성": "딜러",
    "검성": "탱커", "수호성": "탱커",
    "치유성": "치유성",
    "호법성": "호법성"
}

# --- 세션 상태 초기화 ---
if 'users' not in st.session_state: st.session_state.users = []
if 'raids' not in st.session_state: st.session_state.raids = {}
if 'comp_count' not in st.session_state: st.session_state.comp_count = 0
if 'schedules' not in st.session_state: st.session_state.schedules = []

ADMIN_PASSWORD = "admin" 

st.title("🎮 레이드 전략 매칭 시스템 (공팟 자동 채움)")

menu = st.sidebar.selectbox("메뉴", ["사용자 신청", "신청 취소", "관리자 설정", "매칭 결과"])

# --- 1. 사용자 신청 페이지 ---
if menu == "사용자 신청":
    st.header("📝 레이드 참가 신청")
    
    if not st.session_state.schedules:
        st.error("🚫 금주 고정 시간대가 없습니다. 관리자가 시간대를 등록할 때까지 신청이 불가능합니다.")
    else:
        st.info("💡 일행이 있다면 ➕ 버튼을 눌러 인원을 추가하세요. 일행은 모두 같은 레이드와 시간대로 신청됩니다.")
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("➕ 동반자 추가"): st.session_state.comp_count += 1
        with col2:
            if st.button("➖ 동반자 제거") and st.session_state.comp_count > 0: st.session_state.comp_count -= 1

        with st.form("apply_form"):
            st.subheader("🎯 레이드 및 시간대 선택")
            r1, r2 = st.columns(2)
            with r1: req_type = st.selectbox("레이드 종류", ["루드라", "침식"])
            with r2: req_schedule = st.selectbox("희망 요일/시간대", st.session_state.schedules)

            st.markdown("---")
            st.subheader("👤 본인 정보")
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("닉네임")
                u_pw = st.text_input("취소용 비밀번호", type="password")
            with c2: job = st.selectbox("직업", list(JOB_DETAILS.keys()))
            with c3: power = st.number_input("전투력", min_value=0, step=100)
            
            comp_data = []
            for i in range(st.session_state.comp_count):
                st.markdown(f"---")
                st.markdown(f"**👥 동반자 {i+1}**")
                cc1, cc2, cc3, cc4 = st.columns(4)
                with cc1: c_name = st.text_input("닉네임", key=f"cn_{i}")
                with cc2: c_job = st.selectbox("직업", list(JOB_DETAILS.keys()), key=f"cj_{i}")
                with cc3: c_power = st.number_input("전투력", min_value=0, step=100, key=f"cp_{i}")
                with cc4: c_type = st.radio("조건", ["같은 파티 희망", "같은 공격대 희망"], key=f"ct_{i}")
                comp_data.append({"name": c_name, "job": c_job, "power": c_power, "type": c_type})

            if st.form_submit_button("신청하기"):
                if any(u['닉네임'] == name for u in st.session_state.users):
                    st.error("이미 신청된 닉네임입니다.")
                elif not name or not u_pw:
                    st.error("닉네임과 비밀번호는 필수입니다.")
                else:
                    gid = str(uuid.uuid4())[:8]
                    st.session_state.users.append({
                        "닉네임": name, "세부직업": job, "분류": JOB_DETAILS[job], 
                        "전투력": power, "레이드종류": req_type, "시간대": req_schedule,
                        "비밀번호": u_pw, "그룹ID": gid, "고정": False, "배정공대": None
                    })
                    for c in comp_data:
                        if c['name']:
                            st.session_state.users.append({
                                "닉네임": c['name'], "세부직업": c['job'], "분류": JOB_DETAILS[c['job']], 
                                "전투력": c['power'], "레이드종류": req_type, "시간대": req_schedule,
                                "비밀번호": u_pw, "그룹ID": gid, "고정": False, "배정공대": None
                            })
                    st.success(f"[{req_type} / {req_schedule}] 신청 완료!")

# --- 2. 신청 취소 페이지 ---
elif menu == "신청 취소":
    st.header("🗑️ 신청 취소")
    c_name = st.text_input("대표자 닉네임")
    c_pw = st.text_input("비밀번호", type="password")
    if st.button("취소하기"):
        target_gid = next((u['그룹ID'] for u in st.session_state.users if u['닉네임'] == c_name and u['비밀번호'] == c_pw), None)
        if target_gid:
            st.session_state.users = [u for u in st.session_state.users if u['그룹ID'] != target_gid]
            for r_name in st.session_state.raids:
                st.session_state.raids[r_name]['fixed'] = [f for f in st.session_state.raids[r_name]['fixed'] if f.get('그룹ID') != target_gid]
            st.success("삭제되었습니다.")
        else:
            st.error("정보가 일치하지 않습니다.")

# --- 3. 관리자 설정 페이지 ---
elif menu == "관리자 설정":
    st.header("👑 관리자 페이지")
    if st.text_input("관리자 암호", type="password") == ADMIN_PASSWORD:
        
        st.subheader("📋 전체 신청자 목록")
        if st.session_state.users:
            df_users = pd.DataFrame(st.session_state.users)
            display_df = df_users[['닉네임', '세부직업', '분류', '전투력', '레이드종류', '시간대', '고정', '배정공대']]
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("아직 신청자가 없습니다.")
            
        st.markdown("---")
        
        st.subheader("⏰ 요일 및 시간대 관리")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            new_sch = st.text_input("새로운 시간대 추가", placeholder="예: 토요일 20:00")
            if st.button("시간대 추가") and new_sch:
                if new_sch not in st.session_state.schedules:
                    st.session_state.schedules.append(new_sch)
                    st.success(f"'{new_sch}' 추가 완료")
        with col_s2:
            if st.session_state.schedules:
                del_sch = st.selectbox("삭제할 시간대 선택", st.session_state.schedules)
                if st.button("시간대 삭제"):
                    st.session_state.schedules.remove(del_sch)
                    st.warning(f"'{del_sch}' 삭제 완료")
        
        st.markdown("---")
        
        st.subheader("⚔️ 공격대 구성 설정 (총 8명 고정)")
        if not st.session_state.schedules:
            st.error("먼저 위에서 시간대를 추가해주세요.")
        else:
            with st.expander("새 공격대 추가/수정"):
                r_type = st.selectbox("대상 레이드", ["루드라", "침식"])
                r_sch = st.selectbox("대상 시간대", st.session_state.schedules)
                r_name = st.text_input("공격대 이름", placeholder="예: 1공대")
                
                st.info("💡 아래 '배치할 신청자 수'를 6명으로 설정하면, 8자리 중 6자리는 신청자로 채우고 남은 2자리는 '공석(공팟)'으로 표기됩니다.")
                alloc_cap = st.number_input("배치할 신청자 수 (최대 8명)", 1, 8, 8)
                
                col1, col2, col3, col4 = st.columns(4)
                t_cnt = col1.number_input("최소 탱커 수", 0, 8, 2)
                h_cnt = col2.number_input("최소 호법 수", 0, 8, 1)
                c_cnt = col3.number_input("최소 치유 수", 0, 8, 1)
                d_cnt = col4.number_input("최소 딜러 수", 0, 8, 4)
                
                if st.button("공격대 설정 저장"):
                    if r_name:
                        st.session_state.raids[r_name] = {
                            "type": r_type, "schedule": r_sch, "allocate_count": alloc_cap,
                            "tank": t_cnt, "hodeop": h_cnt, "chiyu": c_cnt, "dealer": d_cnt, "fixed": []
                        }
                        st.success(f"[{r_type}/{r_sch}] {r_name} 설정 완료!")
                    else:
                        st.error("이름을 입력해주세요.")

            if st.session_state.users and st.session_state.raids:
                st.markdown("---")
                st.subheader("📌 특정 인원 공대 고정하기")
                
                user_options = [f"{u['닉네임']} ({u['레이드종류']} | {u['시간대']})" for u in st.session_state.users if not u['고정']]
                raid_options = [f"{r} ({config['type']} | {config['schedule']})" for r, config in st.session_state.raids.items()]
                
                if user_options and raid_options:
                    c_user, c_raid = st.columns(2)
                    with c_user: target_u_str = st.selectbox("사용자 선택", user_options)
                    with c_raid: target_r_str = st.selectbox("배정할 공격대 선택", raid_options)
                    
                    if st.button("해당 인원 고정 확정"):
                        target_u_name = target_u_str.split(" (")[0]
                        target_r_name = target_r_str.split(" (")[0]
                        
                        raid_type = st.session_state.raids[target_r_name]['type']
                        raid_sch = st.session_state.raids[target_r_name]['schedule']
                        
                        for u in st.session_state.users:
                            if u['닉네임'] == target_u_name:
                                if u['레이드종류'] != raid_type or u['시간대'] != raid_sch:
                                    st.error("신청 종류/시간대가 공격대 설정과 다릅니다!")
                                else:
                                    u['고정'] = True
                                    u['배정공대'] = target_r_name
                                    st.session_state.raids[target_r_name]['fixed'].append(u)
                                    st.success(f"{target_u_name}님 -> {target_r_name} 고정 완료.")
                                break

# --- 4. 매칭 결과 페이지 ---
elif menu == "매칭 결과":
    st.header("🎲 매칭 결과")
    
    if not st.session_state.raids:
        st.warning("관리자가 공격대 설정을 완료하지 않았습니다.")
    else:
        filter_type = st.selectbox("조회할 레이드", ["전체", "루드라", "침식"])
        
        if st.button("전체 랜덤 매칭 시작"):
            available_users = [u.copy() for u in st.session_state.users]
            final_raids = {}

            def pick_smart_user(candidates, current_members):
                if not candidates: return None
                current_subjobs = [x['세부직업'] for x in current_members]
                preferred = [c for c in candidates if c['세부직업'] not in current_subjobs]
                
                if preferred:
                    return random.choice(preferred)
                return random.choice(candidates)

            for r_name, config in st.session_state.raids.items():
                raid_list = []
                
                # 1. 고정 인원 배치
                fixed_in_this_raid = [u for u in available_users if u['고정'] and u['배정공대'] == r_name]
                raid_list.extend(fixed_in_this_raid)
                for f in fixed_in_this_raid:
                    available_users = [u for u in available_users if u['닉네임'] != f['닉네임']]

                valid_candidates = [u for u in available_users 
                                    if not u['고정'] 
                                    and u['레이드종류'] == config['type'] 
                                    and u['시간대'] == config['schedule']]

                # 2. 필수 역할군 충족
                roles_needed = {
                    "탱커": config['tank'] - sum(1 for x in raid_list if x['분류'] == "탱커"),
                    "호법성": config['hodeop'] - sum(1 for x in raid_list if x['분류'] == "호법성"),
                    "치유성": config['chiyu'] - sum(1 for x in raid_list if x['분류'] == "치유성"),
                    "딜러": config['dealer'] - sum(1 for x in raid_list if x['분류'] == "딜러")
                }

                for role, needed_count in roles_needed.items():
                    while needed_count > 0:
                        role_candidates = [u for u in valid_candidates if u['분류'] == role]
                        chosen = pick_smart_user(role_candidates, raid_list)
                        if chosen:
                            raid_list.append(chosen)
                            valid_candidates = [u for u in valid_candidates if u['닉네임'] != chosen['닉네임']]
                            available_users = [u for u in available_users if u['닉네임'] != chosen['닉네임']]
                            needed_count -= 1
                        else:
                            break 

                # 3. 설정한 '배치할 신청자 수(allocate_count)'까지만 시스템 인원으로 남은 자리 채우기
                remaining_slots = config['allocate_count'] - len(raid_list)
                while remaining_slots > 0 and valid_candidates:
                    chosen = pick_smart_user(valid_candidates, raid_list)
                    raid_list.append(chosen)
                    valid_candidates = [u for u in valid_candidates if u['닉네임'] != chosen['닉네임']]
                    available_users = [u for u in available_users if u['닉네임'] != chosen['닉네임']]
                    remaining_slots -= 1

                # 4. 무조건 공대 전체 인원이 8명이 되도록 남은 자리를 '공석(공팟)'으로 고정 채우기
                while len(raid_list) < 8:
                    raid_list.append({"닉네임": "공석(공팟)", "세부직업": "-", "분류": "공석", "전투력": 0})

                final_raids[r_name] = {"config": config, "members": raid_list}
            
            st.session_state.last_match = final_raids

        if 'last_match' in st.session_state:
            for r_name, data in st.session_state.last_match.items():
                config = data['config']
                members = data['members']
                
                if filter_type == "전체" or filter_type == config['type']:
                    st.markdown("---")
                    st.subheader(f"📍 {r_name} [{config['type']} | {config['schedule']}] (배치인원: {config['allocate_count']}명 / 공팟: {8 - config['allocate_count']}자리)")
                    df = pd.DataFrame(members)[['닉네임', '세부직업', '분류', '전투력']]
                    st.table(df)
                    
                    real_members = df[df['전투력'] > 0]
                    if not real_members.empty:
                        st.write(f"📊 **실제 파티원 평균 전투력:** {real_members['전투력'].mean():,.0f}")
