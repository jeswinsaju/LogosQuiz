import streamlit as st
import json
import time

st.set_page_config(page_title="IPDE - ICD-10 Screening Tool", layout="wide")

# Set Quiz Duration (e.g., 10 minutes = 600 seconds)
QUIZ_DURATION_SECONDS = 10 * 60

# --- 1. SESSION ISOLATION INIT ---
# Storing user responses & timestamps strictly in session_state prevents user cross-talk
if "user_responses" not in st.session_state:
    st.session_state.user_responses = {}
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Database of Malayalam Questions
QUESTIONS = {
    1: "സാധാരണയായി എനിക്ക് ജീവിതത്തിൽ നിന്ന് സന്തോഷവും ആസ്വാദനവും ലഭിക്കുന്നു.",
    2: "ആരെങ്കിലും എന്നെ വ്രണപ്പെടുത്തുമ്പോൾ ഞാൻ ശരിയായ രീതിയിൽ/വേണ്ടവിധം പ്രതികരിക്കാറില്ല.",
    3: "ചെറിയ കാര്യങ്ങളെക്കുറിച്ച് ഓർത്ത് ഞാൻ വ്യാകുലപ്പെടാറില്ല / ബഹളം വെക്കാറില്ല.",
    4: "ഞാൻ ഏതു തരത്തിലുള്ള വ്യക്തിയായിത്തീരണമെന്ന് എനിക്ക് തീരുമാനിക്കാൻ കഴിയുന്നില്ല.",
    5: "എല്ലാവരും കാണുന്നതിനു വേണ്ടി ഞാൻ എന്റെ വികാരങ്ങൾ പ്രകടിപ്പിക്കും.",
    6: "എനിക്ക് വേണ്ടി തീരുമാനങ്ങൾ എടുക്കാൻ ഞാൻ മറ്റുള്ളവരെ അനുവദിക്കുന്നു.",
    7: "എനിക്ക് സാധാരണയായി പിരിമുറുക്കമോ അസ്വസ്ഥതയോ (പരിഭ്രാന്തിയോ) അനുഭവപ്പെടാറുണ്ട്.",
    8: "ഞാൻ മിക്കവാറും ഒന്നിനെക്കുറിച്ചും ദേഷ്യപ്പെടാറില്ല.",
    9: "ആളുകൾ എന്നെ വിട്ടുപോകാതിരിക്കാൻ ഞാൻ ഏതറ്റം വരെയും പോകും.",
    10: "ഞാൻ പൊതുവായി എല്ലാ കാര്യത്തിലും വളരെ അധികം ജാഗ്രത പുലർത്തുന്ന ഒരു വ്യക്തിയാണ്."
}

SCORING_GRID = {
    "F60.0 Paranoid": [(2, True)],
    "F60.1 Schizoid": [(1, False), (8, True)],
    "F60.7 Dependent": [(6, True)]
}

# --- 2. WELCOME / START SCREEN ---
if not st.session_state.quiz_started:
    st.title("IPDE - ICD-10 Screening Tool")
    st.write("📋 **Instructions:** You will have **10 minutes** to complete this assessment.")
    
    p_name = st.text_input("പേര് (Participant Name)", key="init_p_name")
    
    if st.button("🚀 Start Assessment"):
        if not p_name.strip():
            st.error("Please enter a valid participant name to start.")
        else:
            st.session_state.p_name = p_name
            st.session_state.quiz_started = True
            st.session_state.start_time = time.time()  # Unique start time per session
            st.rerun()
    st.stop()

# --- 3. TIMER CALCULATION (Per Session) ---
elapsed = time.time() - st.session_state.start_time
remaining_time = max(0, int(QUIZ_DURATION_SECONDS - elapsed))

mins, secs = divmod(remaining_time, 60)

st.sidebar.title("⏱️ Quiz Timer")
timer_widget = st.sidebar.empty()

if remaining_time > 60:
    timer_widget.metric(label="Time Remaining", value=f"{mins:02d}:{secs:02d}")
elif remaining_time > 0:
    timer_widget.metric(label="⚠️ Time Running Out!", value=f"{mins:02d}:{secs:02d}")
else:
    timer_widget.error("⏰ Time Expired!")

# Force auto-submit if time reaches 0
if remaining_time == 0:
    st.session_state.submitted = True

# --- 4. QUESTIONNAIRE FORM ---
st.title(f"Assessment: {st.session_state.get('p_name', 'Participant')}")

if not st.session_state.submitted:
    with st.form("quiz_form"):
        col1, col2 = st.columns(2)
        
        for item_no, question_text in QUESTIONS.items():
            target_col = col1 if item_no <= 5 else col2
            
            with target_col:
                st.markdown(f"**Q-{item_no}:** {question_text}")
                
                # Fetch existing response if script reruns
                current_val = st.session_state.user_responses.get(item_no, "Unanswered")
                idx = 0
                if current_val is True: idx = 1
                elif current_val is False: idx = 2
                
                resp = st.radio(
                    label=f"q_{item_no}",
                    options=["Unanswered", "ശരി (True)", "തെറ്റ് (False)"],
                    index=idx,
                    key=f"radio_{item_no}",
                    label_visibility="collapsed"
                )
                
                # Save into session state dynamically
                if resp == "ശരി (True)":
                    st.session_state.user_responses[item_no] = True
                elif resp == "തെറ്റ് (False)":
                    st.session_state.user_responses[item_no] = False
                else:
                    st.session_state.user_responses[item_no] = None
                    
        submit_btn = st.form_submit_button("Submit Assessment")
        if submit_btn:
            st.session_state.submitted = True
            st.rerun()

# --- 5. RESULTS DISPLAY ---
if st.session_state.submitted:
    st.success("✅ Assessment Completed and Submitted!")
    st.header(f"Results Summary for {st.session_state.get('p_name')}")
    
    # Calculate scores from isolated user_responses
    table_rows = []
    for diagnosis, scoring_criteria in SCORING_GRID.items():
        score = sum(1 for item, expected in scoring_criteria if st.session_state.user_responses.get(item) == expected)
        table_rows.append({"Category": diagnosis, "Score": f"{score} / {len(scoring_criteria)}"})
    
    st.table(table_rows)
    
    if st.button("🔄 Start New Screening"):
        st.session_state.clear()
        st.rerun()
