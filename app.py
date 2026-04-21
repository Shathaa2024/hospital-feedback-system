import streamlit as st
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="hospital management"
    )

# -----------------------------
# LOAD DATA
# -----------------------------
def load_data():
    conn = connect_db()
    df = pd.read_sql("""
        SELECT *,
        CASE 
            WHEN patient_hospital_recommendation >= 4 THEN 'Positive'
            WHEN patient_hospital_recommendation = 3 THEN 'Neutral'
            ELSE 'Negative'
        END AS sentiment
        FROM feedback
    """, conn)
    conn.close()
    return df
# -----------------------------
# DOCTOR RATINGS DATA
# -----------------------------
def load_doctor_performance():
    conn = connect_db()
    
    query = """
    SELECT 
    LOWER(TRIM(d.specialization)) AS specialization,
    COUNT(f.feedback_id) AS total_feedback,
    ROUND(AVG(f.patient_hospital_recommendation), 2) AS avg_rating
FROM doctors d
LEFT JOIN feedback f ON d.doctor_id = f.doctor_id
GROUP BY LOWER(TRIM(d.specialization))
ORDER BY avg_rating DESC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df
# -----------------------------
# SENTIMENT LOGIC (NO DB CHANGE)
# -----------------------------
def classify_sentiment(row):
    try:
        score = row["patient_hospital_recommendation"]

        if score >= 4:
            return "Positive"
        elif score == 3:
            return "Neutral"
        else:
            return "Negative"
    except:
        return "Unknown"

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Hospital Feedback System", layout="wide")

st.title("Hospital Feedback Management System")
col1, col2 = st.columns([6, 1])

with col2:
    if st.button("Refresh Data"):
        st.rerun()

# -----------------------------
# LOAD DATA
# -----------------------------
df = load_data()

if not df.empty:

    # -----------------------------
    # SIDEBAR FILTER
    # -----------------------------
    st.sidebar.header("Filter")

sentiment_filter = st.sidebar.multiselect(
        "Select Sentiment",
        options=df["sentiment"].unique(),
        default=df["sentiment"].unique()
    )

df = df[df["sentiment"].isin(sentiment_filter)]


    # -----------------------------
    # METRICS
    # -----------------------------
st.subheader("Overview")

total = len(df)
positive = len(df[df["sentiment"] == "Positive"])
neutral = len(df[df["sentiment"] == "Neutral"])
negative = len(df[df["sentiment"] == "Negative"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Feedback", total)
col2.metric("Positive", positive)
col3.metric("Neutral", neutral)
col4.metric("Negative", negative)

# SIDE BY SIDE LAYOUT
col_left, col_right = st.columns([2, 1])
# =============================
# LEFT: DOCTOR PERFORMANCE
# =============================
with col_left:
    st.subheader("Doctor Performance")

    doc_perf = load_doctor_performance()

    # Label
    doc_perf["label"] = doc_perf["specialization"].str.title()

    # Color logic
    colors = []
    for rating in doc_perf["avg_rating"]:
        if rating >= 4:
            colors.append("#00C853")
        elif rating >= 3:
            colors.append("#FFD600")
        else:
            colors.append("#D50000")

    # Smaller + cleaner chart
    fig2, ax2 = plt.subplots(figsize=(6,4))
    fig2.patch.set_facecolor('#0E1117')
    ax2.set_facecolor('#0E1117')

    ax2.barh(doc_perf["label"], doc_perf["avg_rating"], color=colors)

    ax2.set_xlabel("Avg Rating (1–5)", color='white')
    ax2.set_title("By Department", color='white')

    ax2.tick_params(colors='white')

    for spine in ax2.spines.values():
        spine.set_visible(False)

    ax2.invert_yaxis()

    st.pyplot(fig2, use_container_width=True)

# RIGHT: PIE CHART
# =============================
with col_right:
    st.subheader("Overall Experience")

    sentiment_counts = df["sentiment"].value_counts()

    colors_map = {
        "Positive": "#00C853",
        "Neutral": "#FFD600",
        "Negative": "#D50000"
    }

    colors = [colors_map[label] for label in sentiment_counts.index]

    # smaller pie
    fig3, ax3 = plt.subplots(figsize=(4,4))
    fig3.patch.set_facecolor('#0E1117')

    ax3.pie(
        sentiment_counts,
        labels=sentiment_counts.index,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90
    )

    ax3.axis('equal')

    st.pyplot(fig3, use_container_width=True)
    # -----------------------------
    # TABLE VIEW
    # -----------------------------
st.subheader("Feedback Records")

if not df.empty:
 for index, row in df.iterrows():

        with st.container():
            cols = st.columns([2, 2, 2, 2, 3])

            cols[0].write(f"**Feedback ID:** {row['feedback_id']}")
            cols[1].write(f"**Patient ID:** {row['patient_id']}")
            cols[2].write(f"**Rating:** {row['patient_hospital_recommendation']}")
            cols[3].write(f"**Sentiment:** {row['sentiment']}")

            # -----------------------------
            # ACTION LOGIC
            # -----------------------------
            if row["sentiment"] == "Positive":
                cols[4].success("✔ No Action Needed")

            elif row["sentiment"] == "Neutral":
                cols[4].warning("⚠ Monitor")

            else:  # Negative
                if row["patient_id"] is not None:
                    if cols[4].button(f"📞 Contact Patient {row['feedback_id']}"):
                        st.info(f"Calling patient {row['patient_id']}...")

                else:
                    cols[4].error("❌ No Patient Info")

            st.divider()

else:
    st.warning("No data available")

  