import streamlit as st
import gspread

# --- 1. CONFIGURATION ---
CURRENT_ACTIVE_WEEK = 3

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
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # New row matching the updated headers
        row = [timestamp, f"Week {active_week}", age_group, user_name, mobile, place, score, total]
        results_sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"ഫലം സൂക്ഷിക്കാൻ സാധിച്ചില്ല: {e}")
        return False

# --- 3. FRONTEND UI ---
st.set_page_config(page_title="മലയാളം ഓൺലൈൻ ക്വിസ്", page_icon="📝", layout="centered")

st.title(f"🎯 ലോഗോസ് ക്വിസ് ഓൺലൈൻ മത്സരം (വാരം - {CURRENT_ACTIVE_WEEK})")
st.write("ചോദ്യങ്ങൾക്ക് ശരിയായ ഉത്തരം നൽകുക. ഫലങ്ങൾ തത്സമയം റെക്കോർഡ് ചെയ്യപ്പെടും.")
st.markdown("---")

# Session State for controlling app flow after submission
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "final_score" not in st.session_state:
    st.session_state.final_score = 0
if "total_q" not in st.session_state:
    st.session_state.total_q = 0
if "user_responses" not in st.session_state:
    st.session_state.user_responses = {}

QUIZ_QUESTIONS = fetch_weekly_questions(CURRENT_ACTIVE_WEEK)

if not QUIZ_QUESTIONS:
    st.error(f"⏳ വാരം {CURRENT_ACTIVE_WEEK}-ലെ ക്വിസ് സമയം അവസാനിച്ചു! അടുത്ത വാരത്തിലെ മത്സരത്തിൽ പങ്കെടുക്കുക.")
    st.stop()

# --- SHOW DETAILED RESULTS IF SUBMITTED ---
if st.session_state.quiz_submitted:
    st.success("🎉 നിങ്ങളുടെ ഉത്തരങ്ങൾ വിജയകരമായി സമർപ്പിച്ചു കഴിഞ്ഞു!")
    st.metric(label="നിങ്ങൾക്ക് ലഭിച്ച ആകെ മാർക്ക്", value=f"{st.session_state.final_score} / {st.session_state.total_q}")
    
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
    st.stop()

# --- PARTICIPANT REGISTRATION FORM ---
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

# --- QUIZ QUESTIONS FORM ---
if user_name and mobile and place and selected_group != "-- തിരഞ്ഞെടുക്കുക --":
    with st.form("quiz_form"):
        user_answers = {}
        
        for q in QUIZ_QUESTIONS:
            st.markdown(f"#### Q{q['id']}. {q['question']}")
            user_answers[q['id']] = st.radio(
                "ശരിയായ ഉത്തരം തിരഞ്ഞെടുക്കുക:", 
                options=q['options'], 
                index=None,
                key=f"w{CURRENT_ACTIVE_WEEK}_q_{q['id']}"
            )
            st.markdown("---")
        
        submitted = st.form_submit_button("Submit (സമർപ്പിക്കുക)")
        
        if submitted:
            # Enforce that all questions must be answered
            incomplete = False
            for q in QUIZ_QUESTIONS:
                if user_answers[q['id']] is None:
                    incomplete = True
            
            if incomplete:
                st.error("⚠️ ദയവായി എല്ലാ ചോദ്യങ്ങൾക്കും ഉത്തരം രേഖപ്പെടുത്തിയ ശേഷം മാത്രം സമർപ്പിക്കുക!")
            else:
                score = 0
                total_questions = len(QUIZ_QUESTIONS)
                
                for q in QUIZ_QUESTIONS:
                    if user_answers[q['id']] == q['correct']:
                        score += 1
                
                with st.spinner("നിങ്ങളുടെ ഉത്തരങ്ങൾ സമർപ്പിക്കുന്നു..."):
                    clean_group_name = selected_group.split(" (")[0]
                    success = save_to_google_sheets(user_name, mobile, place, clean_group_name, score, total_questions, CURRENT_ACTIVE_WEEK)
                    if success:
                        # Store everything in session state before updating page view
                        st.session_state.final_score = score
                        st.session_state.total_q = total_questions
                        st.session_state.user_responses = user_answers
                        st.session_state.quiz_submitted = True
                        st.rerun()
