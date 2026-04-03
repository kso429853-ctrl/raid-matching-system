import streamlit as st
import pandas as pd
import random
import uuid
import json
import os

st.set_page_config(page_title="CONTROL 레이드 신청", layout="wide")

# --- 데이터베이스(JSON) 연동 ---
DATA_FILE = "raid_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": [], "raids": {}, "schedules": [], "confirmed_matches": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# --- 직업 데이터 정의 ---
JOB_DETAILS = {
    "살성": "딜러", "궁성": "딜러", "마도성": "딜러", "정령성": "딜러",
    "검성": "탱커", "수호성": "탱커",
    "치유성": "치유성",
    "호법성": "호법성"
}

# --- 개인 세션 상태 ---
if 'comp_count' not in st.session_state: st.session_state.comp_count = 0
if 'apply_success' not in st.session_state: st.session_state.apply_success = False
if 'preview_result' not in st.session_state: st.session_state.preview_result = None

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
        req_type = st.selectbox("참여할 레이드 선택", ["루드라", "침식"])
        filtered_schedules = [s['time'] for s in db['schedules'] if s['type'] == req_type]
        
        if not filtered_schedules:
            st.error(f"🚫 현재 {req_type} 레이드의 시간대가 없습니다.")
        else:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("➕ 동반자 추가"): st.session_state.comp_count += 1
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
                    comp_data.append({"name": c_name, "job": c_job, "power": c_power, "type": c_type, "relation": f"{name}의 동반자"})

                if st.form_submit_button("신청하기"):
                    if any(u['닉네임'] == name for u in db['users']):
                        st.error("이미 신청된 닉네임입니다.")
                    elif not name or not u_pw:
                        st.error("필수 정보를 입력해주세요.")
                    else:
                        gid = str(uuid.uuid4())[:8]
                        db['users'].append({
                            "닉네임": name, "세부직업": job, "분류": JOB_DETAILS[job], 
                            "전투력": power, "레이드종류": req_type, "시간대": req_schedule,
                            "비밀번호": u_pw, "그룹ID": gid, "관계": "본인(대표)", "조건": "없음", "고정": False, "배정공대": None
                        })
                        for c in comp_data:
                            if c['name']:
                                db['users'].append({
                                    "닉네임": c['name'], "세부직업": c['job'], "분류": JOB_DETAILS[c['job']], 
                                    "전투력": c['power'], "레이드종류": req_type, "시간대": req_schedule,
                                    "비밀번호": u_pw, "그룹ID": gid, "관계": c['relation'], "조건": c['type'], "고정": False, "배정공대": None
                                })
                        save_data(db)
                        st.session_state.apply_success = True
                        st.rerun()

# --- 2. 현재 신청 현황 페이지 ---
elif menu == "현재 신청 현황":
    st.header("📊 현재 신청 현황")
    if not db['schedules']:
        st.info("등록된 시간대가 없습니다.")
    else:
        c1, c2 = st.columns(2)
        with c1: v_type = st.selectbox("조회할 레이드", ["루드라", "침식"])
        v_schs = [s['time'] for s in db['schedules'] if s['type'] == v_type]
        with c2: v_sch = st.selectbox("조회할 시간대", v_schs) if v_schs else None
        
        if v_sch:
            filtered = [u for u in db['users'] if u['레이드종류'] == v_type and u['시간대'] == v_sch]
            if not filtered: st.info("신청자가 없습니다.")
            else:
                st.table(pd.DataFrame(filtered)[['닉네임', '세부직업', '전투력']])

# --- 3. 신청 취소 페이지 ---
elif menu == "신청 취소":
    st.header("🗑️ 신청 취소")
    c_name = st.text_input("닉네임")
    c_pw = st.text_input("비밀번호", type="password")
    if st.button("취소하기"):
        target_gid = next((u['그룹ID'] for u in db['users'] if u['닉네임'] == c_name and u['비밀번호'] == c_pw), None)
        if target_gid:
            db['users'] = [u for u in db['users'] if u['그룹ID'] != target_gid]
            save_data(db)
            st.success("취소 완료.")
            st.rerun()
        else: st.error("정보 불일치.")

# --- 4. 관리자 설정 페이지 ---
elif menu == "관리자 설정":
    st.header("👑 관리자 페이지")
    if st.text_input("관리자 암호", type="password") == ADMIN_PASSWORD:
        
        tab1, tab2, tab3 = st.tabs(["👥 신청자 관리", "⚔️ 시간대/공대 설정", "🎲 전략 매칭 실행"])

        with tab1:
            st.subheader("📋 전체 신청자 목록 (동반자 확인 가능)")
            if db['users']:
                df_admin = pd.DataFrame(db['users']).sort_values(by="그룹ID")
                
                # 💡 과거 데이터 충돌 방지: 데이터프레임에 존재하는 열만 선택하도록 안전망 추가
                desired_cols = ['그룹ID', '닉네임', '세부직업', '관계', '조건', '전투력', '레이드종류', '시간대', '고정', '배정공대']
                valid_cols = [col for col in desired_cols if col in df_admin.columns]
                
                st.dataframe(df_admin[valid_cols], use_container_width=True)
                
                st.markdown("---")
                col_del1, col_del2 = st.columns(2)
                with col_del1:
                    all_u = [f"{u['닉네임']} ({u['레이드종류']}/{u['시간대']})" for u in db['users']]
                    del_target = st.selectbox("강제 삭제할 사용자", all_u)
                    if st.button("해당 유저(일행포함) 삭제"):
                        t_name = del_target.split(" (")[0]
                        t_gid = next(u['그룹ID'] for u in db['users'] if u['닉네임'] == t_name)
                        db['users'] = [u for u in db['users'] if u['그룹ID'] != t_gid]
                        save_data(db)
                        st.rerun()
            else:
                st.info("신청자가 없습니다.")

        with tab2:
            st.subheader("⏰ 시간대 및 ⚔️ 공격대 이름 관리")
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.markdown("**시간대 등록/삭제**")
                at = st.selectbox("레이드", ["루드라", "침식"], key="at")
                nt = st.text_input("시간 (예: 토요일 20시)")
                if st.button("추가"):
                    db['schedules'].append({"type": at, "time": nt}); save_data(db); st.rerun()
                
                if db['schedules']:
                    slist = [f"{s['type']} | {s['time']}" for s in db['schedules']]
                    dt = st.selectbox("삭제할 시간대", slist)
                    if st.button("시간대 삭제"):
                        dt_type, dt_time = dt.split(" | ")
                        db['schedules'] = [s for s in db['schedules'] if not (s['type'] == dt_type and s['time'] == dt_time)]
                        db['users'] = [u for u in db['users'] if not (u['레이드종류'] == dt_type and u['시간대'] == dt_time)]
                        save_data(db); st.rerun()

            with c_s2:
                st.markdown("**공격대 등록/삭제**")
                rt = st.selectbox("레이드", ["루드라", "침식"], key="rt")
                rs_opts = [s['time'] for s in db['schedules'] if s['type'] == rt]
                rs = st.selectbox("시간대", rs_opts) if rs_opts else None
                rn = st.text_input("공대 이름 (예: 1공대)")
                if st.button("공대 생성"):
                    if rn and rs:
                        db['raids'][rn] = {"type": rt, "schedule": rs, "allocate_count": 8, "tank": 2, "hodeop": 1, "chiyu": 1, "dealer": 4, "fixed": []}
                        save_data(db); st.rerun()
                
                if db['raids']:
                    st.markdown("---")
                    r_to_del = st.selectbox("삭제할 공격대 선택", list(db['raids'].keys()))
                    if st.button("🔴 선택한 공대 삭제"):
                        del db['raids'][r_to_del]
                        save_data(db); st.rerun()

        with tab3:
            st.subheader("🎲 랜덤 매칭 실행 (설정 수정 후 실행)")
            mt = st.selectbox("매칭 레이드", ["루드라", "침식"], key="mt")
            ms_opts = [s['time'] for s in db['schedules'] if s['type'] == mt]
            ms = st.selectbox("매칭 시간대", ms_opts, key="ms") if ms_opts else None
            
            if ms:
                raids_in_slot = {k: v for k, v in db['raids'].items() if v['type'] == mt and v['schedule'] == ms}
                
                if raids_in_slot:
                    st.info(f"💡 [{mt} | {ms}]에 배정된 공격대들입니다. 매칭 전 인원 설정을 최종 확인하세요.")
                    for name, conf in raids_in_slot.items():
                        with st.expander(f"⚙️ {name} 세부 설정 수정"):
                            conf['allocate_count'] = st.number_input(f"{name} 배치 인원", 1, 8, conf['allocate_count'], key=f"ac_{name}")
                            c1, c2, c3, c4 = st.columns(4)
                            conf['tank'] = c1.number_input("최소 탱커", 0, 8, conf['tank'], key=f"t_{name}")
                            conf['hodeop'] = c2.number_input("최소 호법", 0, 8, conf['hodeop'], key=f"h_{name}")
                            conf['chiyu'] = c3.number_input("최소 치유", 0, 8, conf['chiyu'], key=f"c_{name}")
                            conf['dealer'] = c4.number_input("최소 딜러", 0, 8, conf['dealer'], key=f"d_{name}")
                    
                    if st.button("🚀 위 설정으로 랜덤 매칭 미리보기"):
                        available_users = [u.copy() for u in db['users'] if u['레이드종류'] == mt and u['시간대'] == ms]
                        preview = {}
                        
                        for r_name, config in raids_in_slot.items():
                            raid_list = []
                            fixed = [u for u in available_users if u['고정'] and u['배정공대'] == r_name]
                            raid_list.extend(fixed)
                            available_users = [u for u in available_users if u['닉네임'] not in [f['닉네임'] for f in fixed]]
                            
                            roles = {"탱커": config['tank'], "호법성": config['hodeop'], "치유성": config['chiyu'], "딜러": config['dealer']}
                            for role, count in roles.items():
                                n = count - sum(1 for x in raid_list if x['분류'] == role)
                                if n > 0:
                                    cands = [u for u in available_users if u['분류'] == role]
                                    sel = random.sample(cands, min(len(cands), n))
                                    raid_list.extend(sel)
                                    available_users = [u for u in available_users if u['닉네임'] not in [s['닉네임'] for s in sel]]
                            
                            rem = config['allocate_count'] - len(raid_list)
                            if rem > 0:
                                sel = random.sample(available_users, min(len(available_users), rem))
                                raid_list.extend(sel)
                                available_users = [u for u in available_users if u['닉네임'] not in [s['닉네임'] for s in sel]]
                            
                            while len(raid_list) < 8:
                                raid_list.append({"닉네임": "공석(공팟)", "세부직업": "-", "분류": "공석", "전투력": 0})
                            
                            for idx, member in enumerate(raid_list):
                                member['파티'] = "1파티" if idx < 4 else "2파티"
                            preview[r_name] = raid_list
                        
                        st.session_state.preview_result = {"key": f"{mt}_{ms}", "data": preview}

                if st.session_state.preview_result:
                    st.markdown("---")
                    st.subheader("👀 매칭 결과 미리보기")
                    for r_name, members in st.session_state.preview_result['data'].items():
                        st.write(f"**{r_name}**")
                        st.table(pd.DataFrame(members)[['파티', '닉네임', '세부직업', '전투력']])
                    
                    if st.button("✅ 최종 매칭 결과 확정 및 공개"):
                        key = st.session_state.preview_result['key']
                        db['confirmed_matches'][key] = st.session_state.preview_result['data']
                        save_data(db)
                        st.success("매칭 결과가 확정되었습니다!")
                        st.session_state.preview_result = None

# --- 5. 매칭 결과 페이지 ---
elif menu == "매칭 결과":
    st.header("🏆 최종 매칭 결과 확인")
    c1, c2 = st.columns(2)
    with c1: res_type = st.selectbox("레이드 선택", ["루드라", "침식"])
    with c2: 
        res_sch_opts = [s['time'] for s in db['schedules'] if s['type'] == res_type]
        res_sch = st.selectbox("시간대 선택", res_sch_opts) if res_sch_opts else None
        
    if res_sch:
        res_key = f"{res_type}_{res_sch}"
        match_data = db['confirmed_matches'].get(res_key)
        if match_data:
            for r_name, members in match_data.items():
                st.markdown(f"### 📍 {r_name}")
                st.table(pd.DataFrame(members)[['파티', '닉네임', '세부직업', '전투력']])
        else: st.warning("아직 확정된 매칭 결과가 없습니다.")
