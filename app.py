import streamlit as st
import gspread
from datetime import datetime

# --- 1. CONFIGURATION: START OF THE QUIZ PROGRAM ---
PROGRAM_START_DATE = datetime(2026, 7, 1) 

def get_current_quiz_week():
    days_passed = (datetime.now() - PROGRAM_START_DATE).days
    current_week = (days_passed // 7) + 1
    return max(1, current_week)

# --- 2. FETCH AND FILTER QUESTIONS ---
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

# --- 3. SAVE RESULTS WITH AGE GROUP & WEEK TRACKING ---
def save_to_google_sheets(user_name, age_group, score, total, active_week):
    try:
        credentials = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(credentials)
        sheet_id = st.secrets["spreadsheet_id"]
        
        workbook = gc.open_by_key(sheet_id)
        results_sheet = workbook.sheet1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Appending data matching the new headers layout
        row = [timestamp, f"Week {active_week}", age_group, user_name, score, total]
        results_sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"ഫലം സൂക്ഷിക്കാൻ സാധിച്ചില്ല: {e}")
        return False

# --- 4. FRONTEND UI ---
st.set_page_config(page_title="മലയാളം ഓൺലൈൻ ക്വിസ്", page_icon="📝", layout="centered")

current_week = get_current_quiz_week()

st.title(f"🎯 ഓൺലൈൻ ക്വിസ് മത്സരം (വാരം - {current_week})")
st.write("ചോദ്യങ്ങൾക്ക് ശരിയായ ഉത്തരം നൽകുക. ഫലങ്ങൾ തത്സമയം റെക്കോർഡ് ചെയ്യപ്പെടും.")
st.markdown("---")

QUIZ_QUESTIONS = fetch_weekly_questions(current_week)

if not QUIZ_QUESTIONS:
    st.warning(f"വാരം {current_week}-ലെ ചോദ്യങ്ങൾ നിലവിൽ ലഭ്യമല്ല. ദയവായി പിന്നീട് ശ്രമിക്കുക.")
    st.stop()

# Participant Info Inputs
user_name = st.text_input("നിങ്ങളുടെ പൂർണ്ണമായ പേര് ഇവിടെ ടൈപ്പ് ചെയ്യുക:", placeholder="John Doe")

# Age Groups from your Image
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

# Show quiz only when Name is typed and a valid Age Group is chosen
if user_name and selected_group != "-- തിരഞ്ഞെടുക്കുക --":
    with st.form("quiz_form"):
        user_answers = {}
        
        for q in QUIZ_QUESTIONS:
            st.markdown(f"#### Q{q['id']}. {q['question']}")
            user_answers[q['id']] = st.radio(
                "ശരിയായ ഉത്തരം തിരഞ്ഞെടുക്കുക:", 
                options=q['options'], 
                key=f"w{current_week}_q_{q['id']}"
            )
            st.markdown("---")
        
        submitted = st.form_submit_button("Submit (സമർപ്പിക്കുക)")
        
        if submitted:
            score = 0
            total_questions = len(QUIZ_QUESTIONS)
            
            for q in QUIZ_QUESTIONS:
                if user_answers[q['id']] == q['correct']:
                    score += 1
            
            with st.spinner("നിങ്ങളുടെ ഉത്തരങ്ങൾ സമർപ്പിക്കുന്നു..."):
                # Clean up the string to just save the Category letter (e.g., "A വിഭാഗം")
                clean_group_name = selected_group.split(" (")[0]
                
                success = save_to_google_sheets(user_name, clean_group_name, score, total_questions, current_week)
                if success:
                    st.success(f"🎉 നന്ദി {user_name}! നിങ്ങളുടെ ഉത്തരങ്ങൾ വിജയകരമായി സമർപ്പിച്ചു.")
                    st.metric(label="ലഭിച്ച സ്കോർ", value=f"{score} / {total_questions}")