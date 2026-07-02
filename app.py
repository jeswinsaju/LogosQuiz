import streamlit as st
import gspread

# --- 1. CONFIGURATION ---
# Simply change this number to switch weeks or set to a week that doesn't exist to close the quiz
CURRENT_ACTIVE_WEEK = 1 

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

def save_to_google_sheets(user_name, age_group, score, total, active_week):
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        sheet_id = st.secrets["spreadsheet_id"]
        
        workbook = gc.open_by_key(sheet_id)
        results_sheet = workbook.sheet1
        
        # Get current time on user submission
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row = [timestamp, f"Week {active_week}", age_group, user_name, score, total]
        results_sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"ഫലം സൂക്ഷിക്കാൻ സാധിച്ചില്ല: {e}")
        return False

# --- 3. FRONTEND UI ---
st.set_page_config(page_title="മലയാളം ഓൺലൈൻ ക്വിസ്", page_icon="📝", layout="centered")

st.title(f"🎯 ഓൺലൈൻ ക്വിസ് മത്സരം (വാരം - {CURRENT_ACTIVE_WEEK})")
st.write("ചോദ്യങ്ങൾക്ക് ശരിയായ ഉത്തരം നൽകുക. ഫലങ്ങൾ തത്സമയം റെക്കോർഡ് ചെയ്യപ്പെടും.")
st.markdown("---")

# Initialize session state tracking to show score screen cleanly
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "final_score" not in st.session_state:
    st.session_state.final_score = 0
if "total_q" not in st.session_state:
    st.session_state.total_q = 0

# Fetch active questions
QUIZ_QUESTIONS = fetch_weekly_questions(CURRENT_ACTIVE_WEEK)

# 3. IF WEEK IS CLOSED / TIME EXPIRED
if not QUIZ_QUESTIONS:
    st.error(f"⏳ വാരം {CURRENT_ACTIVE_WEEK}-ലെ ക്വിസ് സമയം അവസാനിച്ചു! അടുത്ത വാരത്തിലെ മത്സരത്തിൽ പങ്കെടുക്കുക.")
    st.stop()

# Score View Layout replacement after submission
if st.session_state.quiz_submitted:
    st.success("🎉 നിങ്ങളുടെ ഉത്തരങ്ങൾ വിജയകരമായി സമർപ്പിച്ചു കഴിഞ്ഞു!")
    st.metric(label="നിങ്ങൾക്ക് ലഭിച്ച ആകെ മാർക്ക്", value=f"{st.session_state.final_score} / {st.session_state.total_q}")
    st.info("📊 പ്രായവിഭാഗം തിരിച്ചുള്ള വിജയികളുടെ വിവരങ്ങൾ പിന്നീട് ഔദ്യോഗികമായി അറിയിക്കുന്നതാണ്.")
    st.stop()

# Registration inputs
user_name = st.text_input("നിങ്ങളുടെ പൂർണ്ണമായ പേര് ഇവിടെ ടൈപ്പ് ചെയ്യുക:", placeholder="John Doe")

age_group_options = [
    "-- തിരഞ്ഞെടുക്കുക --",
    "A বিভাগം (1-1-2015 നും അതിനുശേഷവും ജനിച്ചവർ)",
    "B বিভাগം (1-1-2010 നും 31-12-2014 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
    "C বিভাগം (1-1-1995 നും 31-12-2009 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
    "D বিভাগം (1-1-1975 നും 31-12-1994 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
    "E বিভাগം (1-1-1962 നും 31-12-1974 നും ഇടയ്ക്ക് ജനിച്ചവർ)",
    "F বিভাগം (31-12-1961 നും അതിനുമുമ്പും ജനിച്ചവർ)"
]
selected_group = st.selectbox("നിങ്ങളുടെ പ്രായവിഭാഗം തിരഞ്ഞെടുക്കുക:", options=age_group_options)

# Main Quiz Engine
if user_name and selected_group != "-- തിരഞ്ഞെടുക്കുക --":
    with st.form("quiz_form"):
        user_answers = {}
        
        for q in QUIZ_QUESTIONS:
            st.markdown(f"#### Q{q['id']}. {q['question']}")
            # Set index=None to ensure no choice is pre-selected
            user_answers[q['id']] = st.radio(
                "ശരിയായ ഉത്തരം തിരഞ്ഞെടുക്കുക:", 
                options=q['options'], 
                index=None,
                key=f"w{CURRENT_ACTIVE_WEEK}_q_{q['id']}"
            )
            st.markdown("---")
        
        submitted = st.form_submit_button("Submit (സമർപ്പിക്കുക)")
        
        if submitted:
            # 1. ENFORCE ATTENDING ALL 10 QUESTIONS
            incomplete = False
            for q in QUIZ_QUESTIONS:
                if user_answers[q['id']] is None:
                    incomplete = True
            
            if incomplete:
                st.error("⚠️ ദയവായി എല്ലാ ചോദ്യങ്ങൾക്കും ഉത്തരം രേഖപ്പെടുത്തിയ ശേഷം മാത്രം സമർപ്പിക്കുക!")
            else:
                # Calculate absolute mark marks only
                score = 0
                total_questions = len(QUIZ_QUESTIONS)
                
                for q in QUIZ_QUESTIONS:
                    if user_answers[q['id']] == q['correct']:
                        score += 1
                
                with st.spinner("നിങ്ങളുടെ ഉത്തരങ്ങൾ സമർപ്പിക്കുന്നു..."):
                    clean_group_name = selected_group.split(" (")[0]
                    success = save_to_google_sheets(user_name, clean_group_name, score, total_questions, CURRENT_ACTIVE_WEEK)
                    if success:
                        # Save score configuration state and trigger application refresh
                        st.session_state.final_score = score
                        st.session_state.total_q = total_questions
                        st.session_state.quiz_submitted = True
                        st.rerun()
