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
# 시간대를 딕셔너리 형태로 저장하여 레이드별 분류 가능하게 수정
if 'schedules' not in st.session_state: st.session_state.schedules = [] 
if 'apply_success' not in st.session_state: st.session_state.apply_success = False

ADMIN_PASSWORD = "admin" 

st.title("🎮 CONTROL 레이드 신청")

menu = st.sidebar.selectbox("메뉴", ["사용자 신청", "현재 신청 현황", "신청 취소", "관리자 설정", "매칭 결과"])

# --- 1. 사용자 신청 페이지 ---
if menu == "사용자 신청":
    if st.session_state.apply_success:
        st.success("🎉 성공적으로 신청이 완료되었습니다!")
        st.balloons() 
        if st.button("확인"):
            st.session_state.apply_success = False
            st.session_state.comp_count = 0
            st.rerun()
    else:
        st.header("📝 레이드 참가 신청")
        
        # 레이드 종류 먼저 선택
        req_type = st.selectbox("먼저 참여할 레이드를 골라주세요", ["루드라", "침식"])
        
        # 선택한 레이드에 맞는 시간대만 필터링
        filtered_schedules = [s['time'] for s in st.session_state.schedules if s['type'] == req_type]
        
        if not filtered_schedules:
            st.error(f"🚫 현재 {req_type} 레이드의 고정 시간대가 없습니다. 관리자가 등록할 때까지 신청이 불가능합니다.")
        else:
            st.info("💡 일행이 있다면 ➕ 버튼을 눌러 인원을 추가하세요.")
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("➕ 동반자 추가"): st.session_state.comp_count += 1
            with col2:
                if st.button("➖ 동반자 제거") and st.session_state.comp_count > 0: st.session_state.comp_count -= 1

            with st.form("apply_form"):
                req_schedule = st.selectbox(f"[{req_type}] 희망 요일/시간대 선택", filtered_schedules)

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
                        st.session_state.apply_success = True
                        st.rerun()

# --- 2. 현재 신청 현황 페이지 ---
elif menu == "현재 신청 현황":
    st.header("📊 현재 신청 현황")
    if not st.session_state.users:
        st.info("현재 접수된 신청이 없습니다.")
    else:
        df = pd.DataFrame(st.session_state.users)
        st.subheader("📌 레이드 및 시간대별 신청 요약")
        summary_df = df.groupby(['레이드종류', '시간대', '분류']).size().unstack(fill_value=0)
        st.dataframe(summary_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 세부 신청자 명단")
        display_df = df[['레이드종류', '시간대', '분류', '세부직업', '닉네임', '전투력', '고정']]
        st.dataframe(display_df, use_container_width=True)

# --- 3. 신청 취소 페이지 ---
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

# --- 4. 관리자 설정 페이지 ---
elif menu == "관리자 설정":
    st.header("👑 관리자 페이지")
    if st.text_input("관리자 암호", type="password") == ADMIN_PASSWORD:
        
        st.subheader("⏰ 레이드별 요일 및 시간대 관리")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**시간대 추가**")
            add_type = st.selectbox("레이드 종류 선택", ["루드라", "침식"], key="add_t")
            new_time = st.text_input("시간대 입력 (예: 토요일 20:00)", key="add_time")
            if st.button("시간대 등록"):
                if new_time and not any(s['type'] == add_type and s['time'] == new_time for s in st.session_state.schedules):
                    st.session_state.schedules.append({"type": add_type, "time": new_time})
                    st.success(f"{add_type} - {new_time} 등록 완료")
                    st.rerun()
        
        with col_s2:
            st.markdown("**시간대 삭제**")
            if st.session_state.schedules:
                sch_list = [f"{s['type']} | {s['time']}" for s in st.session_state.schedules]
                del_target = st.selectbox("삭제할 항목 선택", sch_list)
                if st.button("선택 항목 삭제"):
                    # 데이터 분리
                    d_type, d_time = del_target.split(" | ")
                    # 시간대 리스트에서 삭제
                    st.session_state.schedules = [s for s in st.session_state.schedules if not (s['type'] == d_type and s['time'] == d_time)]
                    # [핵심] 해당 레이드와 시간대가 모두 일치하는 신청자만 삭제
                    st.session_state.users = [u for u in st.session_state.users if not (u['레이드종류'] == d_type and u['시간대'] == d_time)]
                    # 고정 인원에서도 삭제
                    for r_name in st.session_state.raids:
                        st.session_state.raids[r_name]['fixed'] = [f for f in st.session_state.raids[r_name]['fixed'] if not (f.get('레이드종류') == d_type and f.get('시간대') == d_time)]
                    
                    st.warning(f"{del_target} 관련 모든 데이터가 정리되었습니다.")
                    st.rerun()
        
        st.markdown("---")
        
        # 관리자 직권 취소
        st.subheader("🗑️ 관리자 직권 유저 취소")
        if st.session_state.users:
            del_user = st.selectbox("취소할 신청자 선택", [f"{u['닉네임']} ({u['레이드종류']}/{u['시간대']})" for u in st.session_state.users])
            if st.button("해당 유저 강제 취소"):
                target_name = del_user.split(" (")[0]
                target_gid = next((u['그룹ID'] for u in st.session_state.users if u['닉네임'] == target_name), None)
                if target_gid:
                    st.session_state.users = [u for u in st.session_state.users if u['그룹ID'] != target_gid]
                    st.success(f"취소 완료")
                    st.rerun()
        
        st.markdown("---")
        st.subheader("⚔️ 공격대 구성 설정 (총 8명 고정)")
        if not st.session_state.schedules:
            st.error("시간대를 먼저 추가해주세요.")
        else:
            with st.expander("새 공격대 추가/수정"):
                r_type = st.selectbox("대상 레이드", ["루드라", "침식"], key="raid_sel")
                # 선택한 레이드에 맞는 시간대만 옵션으로 제공
                r_sch_opts = [s['time'] for s in st.session_state.schedules if s['type'] == r_type]
                r_sch = st.selectbox("대상 시간대", r_sch_opts)
                r_name = st.text_input("공격대 이름", placeholder="예: 1공대")
                alloc_cap = st.number_input("배치할 신청자 수 (최대 8명)", 1, 8, 8)
                
                col1, col2, col3, col4 = st.columns(4)
                t_cnt = col1.number_input("최소 탱커", 0, 8, 2)
                h_cnt = col2.number_input("최소 호법", 0, 8, 1)
                c_cnt = col3.number_input("최소 치유", 0, 8, 1)
                d_cnt = col4.number_input("최소 딜러", 0, 8, 4)
                
                if st.button("공격대 저장"):
                    if r_name:
                        st.session_state.raids[r_name] = {
                            "type": r_type, "schedule": r_sch, "allocate_count": alloc_cap,
                            "tank": t_cnt, "hodeop": h_cnt, "chiyu": c_cnt, "dealer": d_cnt, "fixed": []
                        }
                        st.success("저장 완료")

            # 고정 인원 지정
            if st.session_state.users and st.session_state.raids:
                st.markdown("---")
                st.subheader("📌 특정 인원 공대 고정")
                u_opts = [f"{u['닉네임']} ({u['레이드종류']} | {u['시간대']})" for u in st.session_state.users if not u['고정']]
                r_opts = [f"{r} ({v['type']} | {v['schedule']})" for r, v in st.session_state.raids.items()]
                if u_opts and r_opts:
                    c_u, c_r = st.columns(2)
                    with c_u: target_u = st.selectbox("사용자 선택", u_opts)
                    with c_r: target_r = st.selectbox("공대 선택", r_opts)
                    if st.button("고정 확정"):
                        u_n = target_u.split(" (")[0]
                        r_n = target_r.split(" (")[0]
                        raid_conf = st.session_state.raids[r_n]
                        for u in st.session_state.users:
                            if u['닉네임'] == u_n:
                                if u['레이드종류'] == raid_conf['type'] and u['시간대'] == raid_conf['schedule']:
                                    u['고정'] = True
                                    u['배정공대'] = r_n
                                    st.session_state.raids[r_n]['fixed'].append(u)
                                    st.success("고정 완료")
                                else:
                                    st.error("레이드 종류나 시간대가 일치하지 않습니다.")

# --- 5. 매칭 결과 페이지 ---
elif menu == "매칭 결과":
    st.header("🎲 매칭 결과")
    if not st.session_state.raids:
        st.warning("공격대 설정이 없습니다.")
    else:
        f_type = st.selectbox("필터", ["전체", "루드라", "침식"])
        if st.button("전체 랜덤 매칭 시작"):
            available_users = [u.copy() for u in st.session_state.users]
            final_raids = {}

            def pick_smart_user(candidates, current_members):
                if not candidates: return None
                current_subjobs = [x['세부직업'] for x in current_members]
                preferred = [c for c in candidates if c['세부직업'] not in current_subjobs]
                return random.choice(preferred if preferred else candidates)

            for r_name, config in st.session_state.raids.items():
                raid_list = []
                fixed_in = [u for u in available_users if u['고정'] and u['배정공대'] == r_name]
                raid_list.extend(fixed_in)
                for f in fixed_in: available_users = [u for u in available_users if u['닉네임'] != f['닉네임']]

                valid_candidates = [u for u in available_users if not u['고정'] and u['레이드종류'] == config['type'] and u['시간대'] == config['schedule']]

                roles = {"탱커": config['tank'], "호법성": config['hodeop'], "치유성": config['chiyu'], "딜러": config['dealer']}
                for role, needed in roles.items():
                    n = needed - sum(1 for x in raid_list if x['분류'] == role)
                    while n > 0:
                        cands = [u for u in valid_candidates if u['분류'] == role]
                        chosen = pick_smart_user(cands, raid_list)
                        if chosen:
                            raid_list.append(chosen)
                            valid_candidates = [u for u in valid_candidates if u['닉네임'] != chosen['닉네임']]
                            available_users = [u for u in available_users if u['닉네임'] != chosen['닉네임']]
                            n -= 1
                        else: break

                rem = config['allocate_count'] - len(raid_list)
                while rem > 0 and valid_candidates:
                    chosen = pick_smart_user(valid_candidates, raid_list)
                    raid_list.append(chosen)
                    valid_candidates = [u for u in valid_candidates if u['닉네임'] != chosen['닉네임']]
                    available_users = [u for u in available_users if u['닉네임'] != chosen['닉네임']]
                    rem -= 1

                while len(raid_list) < 8:
                    raid_list.append({"닉네임": "공석(공팟)", "세부직업": "-", "분류": "공석", "전투력": 0})
                final_raids[r_name] = {"config": config, "members": raid_list}
            st.session_state.last_match = final_raids

        if 'last_match' in st.session_state:
            for r_name, data in st.session_state.last_match.items():
                if f_type == "전체" or f_type == data['config']['type']:
                    st.markdown("---")
                    st.subheader(f"📍 {r_name} [{data['config']['type']} | {data['config']['schedule']}]")
                    st.table(pd.DataFrame(data['members'])[['닉네임', '세부직업', '분류', '전투력']])
