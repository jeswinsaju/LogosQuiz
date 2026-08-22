import streamlit as st
import gspread
import time
from datetime import datetime

# --- 1. CONFIGURATION ---
CURRENT_ACTIVE_WEEK = 8
QUIZ_DURATION_MINUTES = 10  # ക്വിസ് സമയം (മിനിറ്റിൽ)
QUIZ_DURATION_SECONDS = QUIZ_DURATION_MINUTES * 60

# അടുത്ത ശനിയാഴ്ചത്തെ ക്വിസ് വിവരങ്ങൾ (ഇവിടെ ആവശ്യാനുസരണം മാറ്റങ്ങൾ വരുത്താം)
NEXT_QUIZ_DATE = "അടുത്ത ശനിയാഴ്ച"
NEXT_QUIZ_TOPICS = "1 സാമുവേൽ 4, 5, 6, 7 "

# --- 2. DATABASE UTILITIES ---
@st.cache_data(ttl=600)
def fetch_weekly_questions(target_week):
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        sheet_id = st.secrets["spreadsheet_id"]
        
        workbook = gc.open_by_key(sheet_id)
        questions_sheet = workbook.worksheet("Questions")
        all_records = questions_sheet.get_all_records()
        
        formatted_questions = []
        for row in all_records:
            if int(row["week"]) == target_week:
                formatted_questions.append({
                    "id": int(row["id"]),
                    "question": str(row["question"]),
                    "options": [str(row["option1"]), str(row["option2"]), str(row["option3"]), str(row["option4"])],
                    "correct": str(row["correct"])
                })
        return formatted_questions
    except Exception as e:
        st.error(f"ചോദ്യങ്ങൾ ലോഡ് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        return []

def save_to_google_sheets(user_name, mobile, place, age_group, score, total, active_week):
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        sheet_id = st.secrets["spreadsheet_id"]
        
        workbook = gc.open_by_key(sheet_id)
        results_sheet = workbook.sheet1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row = [timestamp, f"Week {active_week}", age_group, user_name, mobile, place, score, total]
        results_sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"ഫലം സൂക്ഷിക്കാൻ സാധിച്ചില്ല: {e}")
        return False

# --- 3. FRONTEND UI & SESSION ISOLATION ---
st.set_page_config(page_title="മലയാളം ഓൺലൈൻ ക്വിസ്", page_icon="📝", layout="centered")

# Initialize Session State Variables
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "final_score" not in st.session_state:
    st.session_state.final_score = 0
if "total_q" not in st.session_state:
    st.session_state.total_q = 0
if "user_responses" not in st.session_state:
    st.session_state.user_responses = {}
if "participant_info" not in st.session_state:
    st.session_state.participant_info = {}

QUIZ_QUESTIONS = fetch_weekly_questions(CURRENT_ACTIVE_WEEK)

if not QUIZ_QUESTIONS:
    st.error(f"⏳ വാരം {CURRENT_ACTIVE_WEEK}-ലെ ക്വിസ് സമയം അവസാനിച്ചു! അടുത്ത വാരത്തിലെ മത്സരത്തിൽ പങ്കെടുക്കുക.")
    st.stop()

# --- STEP 1: PARTICIPANT REGISTRATION / START SCREEN ---
if not st.session_state.quiz_started and not st.session_state.quiz_submitted:
    st.title(f"🎯 ലോഗോസ് ക്വിസ് ഓൺലൈൻ മത്സരം (വാരം - {CURRENT_ACTIVE_WEEK})")
    st.write(f"📋 **നിർദ്ദേശങ്ങൾ:** ക്വിസ് ആരംഭിച്ച ശേഷം നിങ്ങൾക്ക് ഉത്തരം നൽകാൻ **{QUIZ_DURATION_MINUTES} മിനിറ്റ്** സമയം ഉണ്ടായിരിക്കും.")
    st.markdown("---")
    
    user_name = st.text_input("നിങ്ങളുടെ പൂർണ്ണമായ പേര് ഇവിടെ ടൈപ്പ് ചെയ്യുക:", placeholder="John Doe")
    mobile = st.text_input("മൊബൈൽ നമ്പർ (Mobile Number):", placeholder="9876543210")
    place = st.text_input("സ്ഥലം (Place):", placeholder="Thrissur")

    age_group_options = [
        "-- തിരഞ്ഞെടുക്കുക --",
        "A വിഭാഗം (1-1-2015 നും അതിനുശേഷവും ജനിച്ചവർ)",
        "B വിഭാഗം (1-1-2010 നും 31-12-2014 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
        "C വിഭാഗം (1-1-1995 നും 31-12-2009 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
        "D വിഭാഗം (1-1-1975 നും 31-12-1994 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
        "E വിഭാഗം (1-1-1962 നും 31-12-1974 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
        "F വിഭാഗം (31-12-1961 നും അതിനുമുമ്പും ജനിച്ചവർ)"
    ]
    selected_group = st.selectbox("നിങ്ങളുടെ പ്രായവിഭാഗം തിരഞ്ഞെടുക്കുക:", options=age_group_options)

    if st.button("🚀 ക്വിസ് ആരംഭിക്കുക (Start Quiz)"):
        if not user_name or not mobile or not place or selected_group == "-- തിരഞ്ഞെടുക്കുക --":
            st.error("⚠️ ദയവായി നിങ്ങളുടെ എല്ലാ വിവരങ്ങളും കൃത്യമായി പൂരിപ്പിക്കുക!")
        else:
            st.session_state.participant_info = {
                "name": user_name,
                "mobile": mobile,
                "place": place,
                "group": selected_group.split(" (")[0]
            }
            st.session_state.quiz_started = True
            st.session_state.start_time = time.time()
            st.rerun()

    # മുകളിൽ ചേർത്ത NEXT QUIZ INFO CARD
    st.markdown("---")
    st.info(f"📌 **അടുത്ത ശനിയാഴ്ചത്തെ ക്വിസ് വിഷയം:**\n\n🗓️ **തീയതി:** {NEXT_QUIZ_DATE}\n\n📖 **പാഠഭാഗങ്ങൾ:** {NEXT_QUIZ_TOPICS}")
    st.stop()

# --- STEP 2: LIVE TIMER IN SIDEBAR ---
if st.session_state.quiz_started and not st.session_state.quiz_submitted:
    elapsed = time.time() - st.session_state.start_time
    remaining_time = max(0, int(QUIZ_DURATION_SECONDS - elapsed))
    mins, secs = divmod(remaining_time, 60)

    st.sidebar.title("⏱️ ക്വിസ് ടൈമർ")
    st.sidebar.info(f"**വാരം:** Week {CURRENT_ACTIVE_WEEK}")
    
    # Live Timer Display
    if remaining_time > 60:
        st.sidebar.metric(label="ബാക്കിയുള്ള സമയം", value=f"{mins:02d}:{secs:02d}")
    elif remaining_time > 0:
        st.sidebar.metric(label="⚠️ സമയം അവസാനിക്കാറായി!", value=f"{mins:02d}:{secs:02d}")
    else:
        st.sidebar.error("⏰ സമയം അവസാനിച്ചു!")

# --- STEP 3: QUIZ QUESTIONNAIRE FORM ---
if st.session_state.quiz_started and not st.session_state.quiz_submitted:
    p_info = st.session_state.participant_info
    st.title(f"🎯 ലോഗോസ് ക്വിസ് വാരം - {CURRENT_ACTIVE_WEEK}")
    st.caption(f"മത്സരാർത്ഥി: **{p_info['name']}** ({p_info['group']})")
    st.markdown("---")

    with st.form("quiz_form"):
        user_answers = {}
        
        for q in QUIZ_QUESTIONS:
            st.markdown(f"#### Q{q['id']}. {q['question']}")
            
            saved_ans = st.session_state.user_responses.get(q['id'])
            idx = q['options'].index(saved_ans) if saved_ans in q['options'] else None
            
            user_answers[q['id']] = st.radio(
                "ശരിയായ ഉത്തരം തിരഞ്ഞെടുക്കുക:", 
                options=q['options'], 
                index=idx,
                key=f"w{CURRENT_ACTIVE_WEEK}_q_{q['id']}"
            )
            st.markdown("---")
        
        submitted = st.form_submit_button("Submit (സമർപ്പിക്കുക)")
        
        time_expired = (remaining_time == 0)

        if submitted or time_expired:
            incomplete = False
            for q in QUIZ_QUESTIONS:
                if user_answers[q['id']] is None:
                    incomplete = True

            if incomplete and not time_expired:
                st.error("⚠️ ദയവായി എല്ലാ ചോദ്യങ്ങൾക്കും ഉത്തരം രേഖപ്പെടുത്തിയ ശേഷം മാത്രം സമർപ്പിക്കുക!")
            else:
                score = 0
                total_questions = len(QUIZ_QUESTIONS)
                
                for q in QUIZ_QUESTIONS:
                    if user_answers[q['id']] == q['correct']:
                        score += 1

                with st.spinner("നിങ്ങളുടെ ഉത്തരങ്ങൾ സമർപ്പിക്കുന്നു..."):
                    success = save_to_google_sheets(
                        p_info['name'], 
                        p_info['mobile'], 
                        p_info['place'], 
                        p_info['group'], 
                        score, 
                        total_questions, 
                        CURRENT_ACTIVE_WEEK
                    )
                    
                    if success or time_expired:
                        st.session_state.final_score = score
                        st.session_state.total_q = total_questions
                        st.session_state.user_responses = user_answers
                        st.session_state.quiz_submitted = True
                        st.rerun()

# --- STEP 4: SHOW DETAILED RESULTS & NEXT QUIZ NOTICE AFTER SUBMISSION ---
if st.session_state.quiz_submitted:
    st.title("📊 ക്വിസ് ഫലങ്ങൾ")
    st.success("🎉 നിങ്ങളുടെ ഉത്തരങ്ങൾ വിജയകരമായി സമർപ്പിച്ചു കഴിഞ്ഞു!")
    st.metric(label="നിങ്ങൾക്ക് ലഭിച്ച ആകെ മാർക്ക്", value=f"{st.session_state.final_score} / {st.session_state.total_q}")
    
    # 🌟 NEXT SATURDAY QUIZ ANNOUNCEMENT BOX 🌟
    st.markdown("---")
    st.warning(f"""
    ### 📢 അടുത്ത വാരത്തിലെ ക്വിസ് അറിയിപ്പ് (Week {CURRENT_ACTIVE_WEEK + 1})
    
    🗓️ **തീയതി:** {NEXT_QUIZ_DATE}  
    📖 **അടുത്ത ആഴ്ചയിലെ പഠനഭാഗങ്ങൾ:**  
    *{NEXT_QUIZ_TOPICS}*  
    
    *ദയവായി ഈ പാഠഭാഗങ്ങൾ മുൻകൂട്ടി പഠിച്ച് തയ്യാറാകുക. ആശംസകൾ!*
    """)
    st.markdown("---")

    st.markdown("### 📊 നിങ്ങളുടെ ഉത്തരങ്ങളുടെ വിവരങ്ങൾ:")
    st.markdown("---")
    
    for q in QUIZ_QUESTIONS:
        user_ans = st.session_state.user_responses.get(q['id'])
        correct_ans = q['correct']
        
        st.markdown(f"**Q{q['id']}. {q['question']}**")
        
        if user_ans == correct_ans:
            st.markdown(f"🟢 **നിങ്ങളുടെ ഉത്തരം:** {user_ans} *(ശരിയാണ്)*")
        else:
            st.markdown(f"🔴 **നിങ്ങളുടെ ഉത്തരം:** {user_ans} *(തെറ്റാണ്)*")
            st.markdown(f"✅ **ശരിയായ ഉത്തരം:** {correct_ans}")
        st.markdown("---")
        
    st.info("📊 പ്രായവിഭാഗം തിരിച്ചുള്ള വിജയികളുടെ വിവരങ്ങൾ പിന്നീട് ഔദ്യോഗികമായി അറിയിക്കുന്നതാണ്.")
