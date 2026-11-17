import time
import json
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

st.set_page_config(page_title="SmartEdu AI & Blockchain", layout="wide")

# ==========================================
# 1. AI MODULE: STUDENT SUPPORT PREDICTION
# ==========================================
@st.cache_resource
def train_models():
    np.random.seed(42)
    N = 200
    attendance = np.random.randint(45, 100, N)
    assignments = np.random.randint(35, 100, N)
    quizzes = np.random.randint(30, 100, N)
    study_hours = np.random.randint(1, 20, N)

    X = np.column_stack([attendance, assignments, quizzes, study_hours])
    y = ((attendance < 70) | ((assignments + quizzes) / 2 < 55) | (study_hours < 5)).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    rf = RandomForestClassifier(n_estimators=50, random_state=42).fit(X_train, y_train)
    lr = LogisticRegression(random_state=42).fit(X_train, y_train)

    metrics = []
    for name, model in [("Random Forest", rf), ("Logistic Regression", lr)]:
        preds = model.predict(X_test)
        metrics.append({
            "Model": name,
            "Accuracy": f"{accuracy_score(y_test, preds)*100:.2f}%",
            "Precision": f"{precision_score(y_test, preds)*100:.2f}%",
            "Recall": f"{recall_score(y_test, preds)*100:.2f}%",
            "F1-Score": f"{f1_score(y_test, preds)*100:.2f}%"
        })
    return rf, pd.DataFrame(metrics)

rf_model, ml_comparison_df = train_models()

def recommend_resources(att, assign, quiz, hrs, needs_support):
    if needs_support == 0:
        return "On Track: Recommend Advanced Practice Modules & Peer Mentoring."
    tips = []
    if att < 70:
        tips.append("Recorded Lecture Summaries")
    if assign < 55:
        tips.append("Step-by-Step Guided Worksheets")
    if quiz < 55:
        tips.append("Interactive Concept Quizzes")
    if hrs < 5:
        tips.append("Structured Weekly Study Planner")
    return "Support Needed: Recommend " + ", ".join(tips or ["1-on-1 Faculty Remedial Session"]) + "."

# ==========================================
# 2. BLOCKCHAIN MODULE: HASH-LINKED LEDGER
# ==========================================
def compute_hash(block):
    encoded = json.dumps(block, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()

if "chain" not in st.session_state:
    genesis = {
        "index": 0,
        "timestamp": round(time.time(), 3),
        "student_id": "GENESIS",
        "record": {"ai_prediction": "SmartEdu Ledger Initialized"},
        "prev_hash": "0" * 64
    }
    genesis["hash"] = compute_hash(genesis)
    st.session_state.chain = [genesis]

def add_block(student_id, record_data):
    start = time.perf_counter()
    prev_hash = st.session_state.chain[-1]["hash"]
    block = {
        "index": len(st.session_state.chain),
        "timestamp": round(time.time(), 3),
        "student_id": student_id,
        "record": record_data,
        "prev_hash": prev_hash
    }
    block["hash"] = compute_hash(block)
    st.session_state.chain.append(block)
    return block, round((time.perf_counter() - start) * 1000, 4)

def verify_chain():
    start = time.perf_counter()
    chain = st.session_state.chain
    for i in range(1, len(chain)):
        curr, prev = chain[i], chain[i - 1]
        check_data = {k: v for k, v in curr.items() if k != "hash"}
        if curr["hash"] != compute_hash(check_data):
            return False, f"TAMPER DETECTED at Block #{i}: Record hash mismatch!"
        if curr["prev_hash"] != prev["hash"]:
            return False, f"CHAIN BROKEN between Block #{i-1} and Block #{i}!"
    elapsed_ms = (time.perf_counter() - start) * 1000
    return True, f"VERIFIED SECURE: All {len(chain)} blocks intact ({elapsed_ms:.4f} ms)."

# ==========================================
# 3. STREAMLIT WEB DASHBOARD
# ==========================================
st.title("SmartEdu: AI-Based Personalized Learning & Blockchain-Secured Records")
st.caption("ICAIB 2026 Prototype | UG Dept. of Computer Science & Applications, Sahrdaya College of Advanced Studies")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Student Activity Input")
    sid = st.text_input("Student ID", value="SCAS-2026-01")
    att = st.slider("Attendance (%)", 0, 100, 62)
    assign = st.slider("Assignment Score (%)", 0, 100, 50)
    quiz = st.slider("Quiz Score (%)", 0, 100, 48)
    hrs = st.slider("Weekly Study Hours", 0, 30, 4)

    if st.button("Analyze & Record on Blockchain", type="primary", use_container_width=True):
        clean_id = sid.strip() or f"STU-{len(st.session_state.chain):03d}"
        pred = int(rf_model.predict([[att, assign, quiz, hrs]])[0])
        prob = float(rf_model.predict_proba([[att, assign, quiz, hrs]])[0][1]) * 100

        status = f"Needs Academic Support ({prob:.1f}% risk)" if pred == 1 else f"On Track ({100-prob:.1f}% confidence)"
        rec = recommend_resources(att, assign, quiz, hrs, pred)
        block, proc_ms = add_block(clean_id, {
            "metrics": {"attendance": att, "assignment": assign, "quiz": quiz, "study_hours": hrs},
            "ai_prediction": status,
            "recommendation": rec
        })
        st.session_state.last_receipt = (status, rec, block["index"], proc_ms, block["hash"])

with col2:
    st.subheader("AI Recommendation & Blockchain Audit")
    if "last_receipt" in st.session_state:
        status, rec, b_idx, proc_ms, b_hash = st.session_state.last_receipt
        st.info(f"**AI Prediction:** {status}\n\n**Recommendation:** {rec}")
        st.success(f"**Stored in Block #{b_idx}** ({proc_ms} ms) | **SHA-256:** `{b_hash[:24]}...`")
    else:
        st.write("Adjust the student metrics on the left and click **Analyze & Record on Blockchain**.")

    st.markdown("---")
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("Verify Blockchain Integrity", use_container_width=True):
            ok, msg = verify_chain()
            st.success(msg) if ok else st.error(msg)
    with b_col2:
        if st.button("Simulate Record Tampering", use_container_width=True):
            if len(st.session_state.chain) > 1:
                st.session_state.chain[-1]["record"]["ai_prediction"] = "Altered Grade: A+ (Tampered)"
                st.warning(f"Simulated unauthorized edit on Block #{len(st.session_state.chain)-1}! Click Verify to detect.")
            else:
                st.warning("Add a student record first.")

st.subheader("Hash-Linked Academic Record Ledger")
ledger_rows = [
    {
        "Block #": b["index"],
        "Student ID": b["student_id"],
        "AI Outcome": b["record"].get("ai_prediction", ""),
        "Prev Hash": b["prev_hash"][:14] + "...",
        "Current SHA-256": b["hash"][:14] + "..."
    }
    for b in st.session_state.chain
]
st.dataframe(pd.DataFrame(ledger_rows), use_container_width=True, hide_index=True)

st.subheader("Machine Learning Model Comparison (Test Split)")
st.dataframe(ml_comparison_df, use_container_width=True, hide_index=True)
