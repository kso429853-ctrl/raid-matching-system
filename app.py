import streamlit as st
import pandas as pd
import random
import uuid

st.set_page_config(page_title="레이드 매칭 시스템 v3", layout="wide")

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
if 'schedules' not in st.session_state: st.session_state.schedules = [] # 요일/시간대 저장용

ADMIN_PASSWORD = "admin" 

st.title("🎮 레이드 전략 매칭 시스템 (루드라/침식)")

menu = st.sidebar.selectbox("메뉴", ["사용자 신청", "신청 취소", "관리자 설정", "매칭 결과"])

# --- 1. 사용자 신청 페이지 ---
if menu == "사용자 신청":
    st.header("📝 레이드 참가 신청")
    
    # 시간대가 하나도 설정되지 않은 경우 신청 차단
    if not st.session_state.schedules:
        st.error("🚫 금주 고정 시간대가 없습니다. 관리자가 시간대를 등록할 때까지 신청이 불가능합니다.")
    else:
        st.info("💡 일행(동반자)이 있다면 아래 버튼을 먼저 눌러 인원을 추가한 뒤 폼을 작성해 주세요. 일행은 모두 같은 레이드와 시간대로 자동 신청됩니다.")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("➕ 동반자 추가"): st.session_state.comp_count += 1
        with col2:
            if st.button("➖ 동반자 제거") and st.session_state.comp_count > 0: st.session_state.comp_count -= 1

        with st.form("apply_form"):
            st.subheader("🎯 레이드 및 시간대 선택")
            r1, r2 = st.columns(2)
            with r1:
                req_type = st.selectbox("레이드 종류", ["루드라", "침식"])
            with r2:
                req_schedule = st.selectbox("희망 요일/시간대", st.session_state.schedules)

            st.markdown("---")
            st.subheader("👤 본인 정보")
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("닉네임")
                u_pw = st.text_input("취소용 비밀번호", type="password")
            with c2:
                job = st.selectbox("직업", list(JOB_DETAILS.keys()))
            with c3:
                power = st.number_input("전투력", min_value=0, step=100)
            
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
                    # 본인 추가 (레이드종류, 시간대 포함)
                    st.session_state.users.append({
                        "닉네임": name, "세부직업": job, "분류": JOB_DETAILS[job], 
                        "전투력": power, "레이드종류": req_type, "시간대": req_schedule,
                        "비밀번호": u_pw, "그룹ID": gid, "고정": False, "배정공대": None
                    })
                    # 동반자 추가
                    for c in comp_data:
                        if c['name']:
                            st.session_state.users.append({
                                "닉네임": c['name'], "세부직업": c['job'], "분류": JOB_DETAILS[c['job']], 
                                "전투력": c['power'], "레이드종류": req_type, "시간대": req_schedule,
                                "비밀번호": u_pw, "그룹ID": gid, "고정": False, "배정공대": None
                            })
                    st.success(f"[{req_type} / {req_schedule}] 신청이 완료되었습니다!")

# --- 2. 신청 취소 페이지 ---
elif menu == "신청 취소":
    st.header("🗑️ 신청 취소")
    c_name = st.text_input("대표자 닉네임")
    c_pw = st.text_input("비밀번호", type="password")
    if st.button("취소하기"):
        target_gid = next((u['그룹ID'] for u in st.session_state.users if u['닉네임'] == c_name and u['비밀번호'] == c_pw), None)
        if target_gid:
            st.session_state.users = [u for u in st.session_state.users if u['그룹ID'] != target_gid]
            # 고정 인원 목록에서도 삭제
            for r_name in st.session_state.raids:
                st.session_state.raids[r_name]['fixed'] = [f for f in st.session_state.raids[r_name]['fixed'] if f.get('그룹ID') != target_gid]
            st.success("삭제되었습니다.")
        else:
            st.error("정보가 일치하지 않습니다.")

# --- 3. 관리자 설정 페이지 ---
elif menu == "관리자 설정":
    st.header("👑 관리자 페이지")
    if st.text_input("관리자 암호", type="password") == ADMIN_PASSWORD:
        st.success("관리자 인증 성공!")
        st.markdown("---")
        
        # 1. 시간대 관리
        st.subheader("⏰ 요일 및 시간대 관리")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            new_sch = st.text_input("새로운 시간대 추가", placeholder="예: 토요일 20:00")
            if st.button("시간대 추가") and new_sch:
                if new_sch not in st.session_state.schedules:
                    st.session_state.schedules.append(new_sch)
                    st.success(f"'{new_sch}' 시간대가 추가되었습니다.")
        with col_s2:
            if st.session_state.schedules:
                del_sch = st.selectbox("삭제할 시간대 선택", st.session_state.schedules)
                if st.button("시간대 삭제"):
                    st.session_state.schedules.remove(del_sch)
                    st.warning(f"'{del_sch}' 시간대가 삭제되었습니다.")
        
        st.markdown("---")
        
        # 2. 공격대 구성 설정
        st.subheader("⚔️ 공격대 구성 설정")
        if not st.session_state.schedules:
            st.error("먼저 위에서 시간대를 1개 이상 추가해야 공격대를 구성할 수 있습니다.")
        else:
            with st.expander("새 공격대 추가/수정 (여기를 클릭하세요)"):
                r_type = st.selectbox("대상 레이드", ["루드라", "침식"])
                r_sch = st.selectbox("대상 시간대", st.session_state.schedules)
                r_name = st.text_input("공격대 이름", placeholder="예: 1공대")
                
                col1, col2, col3, col4 = st.columns(4)
                t_cnt = col1.number_input("탱커 수", 0, 8, 2)
                h_cnt = col2.number_input("호법 수", 0, 8, 1)
                c_cnt = col3.number_input("치유 수", 0, 8, 1)
                d_cnt = col4.number_input("딜러 수", 0, 8, 4)
                
                if st.button("설정 저장"):
                    if r_name:
                        st.session_state.raids[r_name] = {
                            "type": r_type, "schedule": r_sch,
                            "tank": t_cnt, "hodeop": h_cnt, "chiyu": c_cnt, "dealer": d_cnt, "fixed": []
                        }
                        st.success(f"[{r_type}/{r_sch}] {r_name} 설정 저장 완료!")
                    else:
                        st.error("공격대 이름을 입력해주세요.")

            # 3. 고정 인원 지정
            if st.session_state.users and st.session_state.raids:
                st.markdown("---")
                st.subheader("📌 고정 인원 지정")
                
                # 가독성을 위해 신청자의 이름 뒤에 신청 정보를 붙여서 보여줍니다.
                user_options = [f"{u['닉네임']} ({u['레이드종류']} | {u['시간대']})" for u in st.session_state.users if not u['고정']]
                raid_options = [f"{r} ({config['type']} | {config['schedule']})" for r, config in st.session_state.raids.items()]
                
                if user_options and raid_options:
                    target_u_str = st.selectbox("사용자 선택", user_options)
                    target_r_str = st.selectbox("배정할 공격대 선택", raid_options)
                    
                    if st.button("해당 인원 고정"):
                        # '이름 (레이드 | 시간)' 형태에서 실제 닉네임과 공대 이름만 추출
                        target_u_name = target_u_str.split(" (")[0]
                        target_r_name = target_r_str.split(" (")[0]
                        
                        # 대상 공대의 레이드 종류 및 시간대 가져오기
                        raid_type = st.session_state.raids[target_r_name]['type']
                        raid_sch = st.session_state.raids[target_r_name]['schedule']
                        
                        for u in st.session_state.users:
                            if u['닉네임'] == target_u_name:
                                # 레이드 종류와 시간대가 일치하는지 검증
                                if u['레이드종류'] != raid_type or u['시간대'] != raid_sch:
                                    st.error(f"경고: {target_u_name}님이 신청한 정보와 {target_r_name}의 설정(종류/시간)이 다릅니다!")
                                else:
                                    u['고정'] = True
                                    u['배정공대'] = target_r_name
                                    st.session_state.raids[target_r_name]['fixed'].append(u)
                                    st.success(f"{target_u_name}님을 {target_r_name}에 고정했습니다.")
                                break

# --- 4. 매칭 결과 페이지 ---
elif menu == "매칭 결과":
    st.header("🎲 매칭 결과")
    
    if not st.session_state.raids:
        st.warning("관리자가 공격대 설정을 완료하지 않았습니다.")
    else:
        # 결과를 레이드 종류/시간대 별로 필터링해서 볼 수 있는 기능 추가
        filter_type = st.selectbox("조회할 레이드", ["전체", "루드라", "침식"])
        
        if st.button("전체 랜덤 매칭 시작"):
            available_users = [u.copy() for u in st.session_state.users]
            final_raids = {}

            for r_name, config in st.session_state.raids.items():
                raid_list = []
                # 1. 고정 인원 선배치
                fixed_in_this_raid = [u for u in available_users if u['고정'] and u['배정공대'] == r_name]
                raid_list.extend(fixed_in_this_raid)
                
                # 이미 배치된 인원은 가용 인원에서 제거
                for f in fixed_in_this_raid:
                    available_users = [u for u in available_users if u['닉네임'] != f['닉네임']]

                roles_needed = {
                    "탱커": config['tank'] - sum(1 for x in raid_list if x['분류'] == "탱커"),
                    "호법성": config['hodeop'] - sum(1 for x in raid_list if x['분류'] == "호법성"),
                    "치유성": config['chiyu'] - sum(1 for x in raid_list if x['분류'] == "치유성"),
                    "딜러": config['dealer'] - sum(1 for x in raid_list if x['분류'] == "딜러")
                }

                # 2. 해당 공대와 '레이드 종류' 및 '시간대'가 완벽히 일치하는 인원들만 후보로 필터링
                valid_candidates = [u for u in available_users 
                                    if not u['고정'] 
                                    and u['레이드종류'] == config['type'] 
                                    and u['시간대'] == config['schedule']]

                # 3. 역할별 랜덤 매칭
                for role, count in roles_needed.items():
                    if count > 0:
                        candidates = [u for u in valid_candidates if u['분류'] == role]
                        selected = random.sample(candidates, min(len(candidates), count))
                        raid_list.extend(selected)
                        
                        # 배정된 인원 제거
                        selected_names = [s['닉네임'] for s in selected]
                        valid_candidates = [u for u in valid_candidates if u['닉네임'] not in selected_names]
                        available_users = [u for u in available_users if u['닉네임'] not in selected_names]
                    
                    # 부족한 자리는 공석 처리
                    while (sum(1 for x in raid_list if x['분류'] == role)) < (config['tank'] if role=="탱커" else config['hodeop'] if role=="호법성" else config['chiyu'] if role=="치유성" else config['dealer']):
                        raid_list.append({"닉네임": "공석", "세부직업": "-", "분류": role, "전투력": 0})

                final_raids[r_name] = {"config": config, "members": raid_list}
            
            # 매칭 결과를 세션에 저장하여 탭 이동 시에도 날아가지 않게 보존
            st.session_state.last_match = final_raids

        # 결과 출력 화면
        if 'last_match' in st.session_state:
            for r_name, data in st.session_state.last_match.items():
                config = data['config']
                members = data['members']
                
                # 필터링 적용 (전체 보기이거나 선택한 레이드와 일치할 때만 표시)
                if filter_type == "전체" or filter_type == config['type']:
                    st.markdown("---")
                    st.subheader(f"📍 {r_name} [{config['type']} | {config['schedule']}]")
                    df = pd.DataFrame(members)[['닉네임', '세부직업', '분류', '전투력']]
                    st.table(df)
                    st.write(f"평균 전투력: {df['전투력'].mean():,.0f}")
