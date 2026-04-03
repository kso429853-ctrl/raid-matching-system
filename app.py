import streamlit as st
import pandas as pd
import random
import uuid

st.set_page_config(page_title="CONTROL 레이드 신청", layout="wide")

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
if 'apply_success' not in st.session_state: st.session_state.apply_success = False
# 확정된 매칭 결과를 저장할 저장소 (Key: (레이드종류, 시간대), Value: 매칭데이터)
if 'confirmed_matches' not in st.session_state: st.session_state.confirmed_matches = {}
# 관리자용 임시 미리보기 결과
if 'preview_result' not in st.session_state: st.session_state.preview_result = None

ADMIN_PASSWORD = "admin" 

st.title("🎮 CONTROL 레이드 신청")

menu = st.sidebar.selectbox("메뉴", ["사용자 신청", "현재 신청 현황", "신청 취소", "관리자 설정", "매칭 결과"])

# --- 1. 사용자 신청 페이지 ---
if menu == "사용자 신청":
    if st.session_state.apply_success:
        st.success("🎉 성공적으로 신청이 완료되었습니다!")
        st.balloons() 
        if st.button("초기 화면으로 돌아가기"):
            st.session_state.apply_success = False
            st.session_state.comp_count = 0
            st.rerun()
    else:
        st.header("📝 레이드 참가 신청")
        req_type = st.selectbox("참여할 레이드 선택", ["루드라", "침식"])
        filtered_schedules = [s['time'] for s in st.session_state.schedules if s['type'] == req_type]
        
        if not filtered_schedules:
            st.error(f"🚫 현재 {req_type} 레이드의 시간대가 없습니다.")
        else:
            st.info("💡 일행이 있다면 ➕ 버튼을 눌러 인원을 추가하세요.")
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("➕ 동반자 추가"): st.session_state.comp_count += 1
            with col2:
                if st.button("➖ 동반자 제거") and st.session_state.comp_count > 0: st.session_state.comp_count -= 1

            with st.form("apply_form"):
                req_schedule = st.selectbox(f"[{req_type}] 희망 시간대 선택", filtered_schedules)
                st.markdown("---")
                st.subheader("👤 본인 정보")
                c1, c2, c3 = st.columns(3)
                with c1:
                    name = st.text_input("닉네임")
                    u_pw = st.text_input("비밀번호", type="password")
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
                        st.error("필수 정보를 입력해주세요.")
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
                        st.session_state.apply_success = True
                        st.rerun()

# --- 2. 현재 신청 현황 페이지 ---
elif menu == "현재 신청 현황":
    st.header("📊 현재 신청 현황")
    if not st.session_state.schedules:
        st.info("등록된 시간대가 없습니다.")
    else:
        c1, c2 = st.columns(2)
        with c1: v_type = st.selectbox("조회할 레이드", ["루드라", "침식"])
        v_schs = [s['time'] for s in st.session_state.schedules if s['type'] == v_type]
        with c2: v_sch = st.selectbox("조회할 시간대", v_schs) if v_schs else None
        
        if v_sch:
            filtered = [u for u in st.session_state.users if u['레이드종류'] == v_type and u['시간대'] == v_sch]
            if not filtered: st.info("신청자가 없습니다.")
            else:
                st.table(pd.DataFrame(filtered)[['닉네임', '세부직업', '전투력']])

# --- 3. 신청 취소 페이지 ---
elif menu == "신청 취소":
    st.header("🗑️ 신청 취소")
    c_name = st.text_input("닉네임")
    c_pw = st.text_input("비밀번호", type="password")
    if st.button("취소하기"):
        target_gid = next((u['그룹ID'] for u in st.session_state.users if u['닉네임'] == c_name and u['비밀번호'] == c_pw), None)
        if target_gid:
            st.session_state.users = [u for u in st.session_state.users if u['그룹ID'] != target_gid]
            st.success("취소 완료.")
        else: st.error("정보 불일치.")

# --- 4. 관리자 설정 페이지 ---
elif menu == "관리자 설정":
    st.header("👑 관리자 페이지")
    if st.text_input("관리자 암호", type="password") == ADMIN_PASSWORD:
        
        # 1. 시간대 및 공격대 설정
        st.subheader("⚙️ 레이드 및 공격대 설정")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**시간대 등록**")
            add_type = st.selectbox("레이드 선택", ["루드라", "침식"], key="adm_t")
            new_time = st.text_input("시간 입력")
            if st.button("시간대 추가"):
                st.session_state.schedules.append({"type": add_type, "time": new_time})
                st.rerun()
        
        st.markdown("---")
        with st.expander("⚔️ 공격대 구성 정보 입력"):
            r_type = st.selectbox("대상 레이드", ["루드라", "침식"], key="r_t")
            r_sch_opts = [s['time'] for s in st.session_state.schedules if s['type'] == r_type]
            r_sch = st.selectbox("대상 시간대", r_sch_opts)
            r_name = st.text_input("공격대 이름 (예: 1공대)")
            alloc_cap = st.number_input("매칭할 인원 수", 1, 8, 8)
            c1, c2, c3, c4 = st.columns(4)
            t_cnt = c1.number_input("최소 탱커", 0, 8, 2)
            h_cnt = c2.number_input("최소 호법", 0, 8, 1)
            c_cnt = c3.number_input("최소 치유", 0, 8, 1)
            d_cnt = c4.number_input("최소 딜러", 0, 8, 4)
            if st.button("공대 설정 저장"):
                st.session_state.raids[r_name] = {"type": r_type, "schedule": r_sch, "allocate_count": alloc_cap, "tank": t_cnt, "hodeop": h_cnt, "chiyu": c_cnt, "dealer": d_cnt, "fixed": []}
                st.success("저장됨")

        st.markdown("---")
        # 2. 신청자 관리 및 고정
        st.subheader("👥 신청자 관리 및 고정")
        if st.session_state.users:
            admin_df = pd.DataFrame(st.session_state.users)[['레이드종류', '시간대', '닉네임', '세부직업', '고정', '배정공대']]
            st.dataframe(admin_df, use_container_width=True)
            
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                u_opts = [f"{u['닉네임']} ({u['레이드종류']}/{u['시간대']})" for u in st.session_state.users if not u['고정']]
                r_opts = [f"{r} ({v['type']}/{v['schedule']})" for r, v in st.session_state.raids.items()]
                if u_opts and r_opts:
                    sel_u = st.selectbox("사용자 선택", u_opts)
                    sel_r = st.selectbox("공대 선택", r_opts)
                    if st.button("인원 고정 확정"):
                        u_name = sel_u.split(" (")[0]
                        r_name = sel_r.split(" (")[0]
                        for u in st.session_state.users:
                            if u['닉네임'] == u_name:
                                u['고정'] = True
                                u['배정공대'] = r_name
                                st.session_state.raids[r_name]['fixed'].append(u)
                                st.rerun()
            with c_f2:
                all_u = [u['닉네임'] for u in st.session_state.users]
                del_target = st.selectbox("강제 취소할 닉네임", all_u)
                if st.button("해당 유저 삭제"):
                    t_gid = next(u['그룹ID'] for u in st.session_state.users if u['닉네임'] == del_target)
                    st.session_state.users = [u for u in st.session_state.users if u['그룹ID'] != t_gid]
                    st.rerun()

        st.markdown("---")
        # 3. 전략 매칭 및 확정 (요청하신 기능)
        st.subheader("🎲 랜덤 매칭 실행 및 확정")
        m_type = st.selectbox("매칭할 레이드 종류", ["루드라", "침식"], key="m_t")
        m_sch_opts = [s['time'] for s in st.session_state.schedules if s['type'] == m_type]
        m_sch = st.selectbox("매칭할 시간대", m_sch_opts, key="m_s") if m_sch_opts else None
        
        if st.button("선택한 시간대 랜덤 매칭 실행"):
            if not m_sch:
                st.error("시간대를 먼저 선택하세요.")
            else:
                available_users = [u.copy() for u in st.session_state.users if u['레이드종류'] == m_type and u['시간대'] == m_sch]
                raids_to_match = {k: v for k, v in st.session_state.raids.items() if v['type'] == m_type and v['schedule'] == m_sch}
                
                if not raids_to_match:
                    st.warning("해당 시간대에 설정된 공격대가 없습니다.")
                else:
                    preview = {}
                    for r_name, config in raids_to_match.items():
                        raid_list = []
                        # 고정 인원
                        fixed = [u for u in available_users if u['고정'] and u['배정공대'] == r_name]
                        raid_list.extend(fixed)
                        available_users = [u for u in available_users if u['닉네임'] not in [f['닉네임'] for f in fixed]]
                        
                        # 역할별 매칭
                        roles = {"탱커": config['tank'], "호법성": config['hodeop'], "치유성": config['chiyu'], "딜러": config['dealer']}
                        for role, count in roles.items():
                            n = count - sum(1 for x in raid_list if x['분류'] == role)
                            if n > 0:
                                cands = [u for u in available_users if u['분류'] == role]
                                selected = random.sample(cands, min(len(cands), n))
                                raid_list.extend(selected)
                                available_users = [u for u in available_users if u['닉네임'] not in [s['닉네임'] for s in selected]]
                        
                        # 나머지 자리
                        rem = config['allocate_count'] - len(raid_list)
                        if rem > 0:
                            selected = random.sample(available_users, min(len(available_users), rem))
                            raid_list.extend(selected)
                            available_users = [u for u in available_users if u['닉네임'] not in [s['닉네임'] for s in selected]]
                        
                        while len(raid_list) < 8:
                            raid_list.append({"닉네임": "공석(공팟)", "세부직업": "-", "분류": "공석", "전투력": 0})
                        preview[r_name] = raid_list
                    
                    st.session_state.preview_result = {"key": (m_type, m_sch), "data": preview}

        # 미리보기 및 확정 버튼
        if st.session_state.preview_result:
            st.info("⚠️ 아래는 미리보기입니다. [매칭 확정]을 눌러야 사용자들이 볼 수 있습니다.")
            for r_name, members in st.session_state.preview_result['data'].items():
                st.write(f"**{r_name}**")
                st.table(pd.DataFrame(members)[['닉네임', '세부직업', '전투력']])
            
            if st.button("위 결과로 매칭 확정하기"):
                key = st.session_state.preview_result['key']
                st.session_state.confirmed_matches[key] = st.session_state.preview_result['data']
                st.success(f"{key[0]} | {key[1]} 매칭이 확정되어 공개되었습니다!")
                st.session_state.preview_result = None

# --- 5. 매칭 결과 페이지 (사용자 확인용) ---
elif menu == "매칭 결과":
    st.header("🏆 최종 매칭 결과 확인")
    st.info("레이드와 시간대를 선택하면 확정된 공격대 명단이 나타납니다.")
    
    c1, c2 = st.columns(2)
    with c1: res_type = st.selectbox("레이드 종류", ["루드라", "침식"], key="res_t")
    with c2: 
        res_sch_opts = [s['time'] for s in st.session_state.schedules if s['type'] == res_type]
        res_sch = st.selectbox("시간대 선택", res_sch_opts, key="res_s") if res_sch_opts else None
        
    if res_sch:
        match_data = st.session_state.confirmed_matches.get((res_type, res_sch))
        if not match_data:
            st.warning("해당 시간대는 아직 매칭이 확정되지 않았습니다.")
        else:
            for r_name, members in match_data.items():
                st.markdown(f"### 📍 {r_name}")
                st.table(pd.DataFrame(members)[['닉네임', '세부직업', '전투력']])
