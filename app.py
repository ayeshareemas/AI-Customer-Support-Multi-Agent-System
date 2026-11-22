import streamlit as st
import sqlite3
import joblib
import pandas as pd

from workflows.orchestrator import run_workflow
from agents.chatbot_agent import chatbot_reply


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Customer Support Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# PREMIUM DARK PURPLE AI THEME
# ==========================================

st.markdown("""
<style>

/* Main Background */
.stApp {
    background: linear-gradient(135deg, #0B1120 0%, #111827 55%, #1E1B4B 100%) !important;
    color: #F8FAFC !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background: transparent !important;
}

/* Header */
[data-testid="stHeader"] {
    background: #0B1120 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #1E1B4B) !important;
    border-right: 1px solid #4338CA !important;
}

[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}

/* Headings */
h1, h2, h3, h4 {
    color: #F8FAFC !important;
    font-weight: 700 !important;
}

/* Text */
p, label, .stMarkdown {
    color: #CBD5E1;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #6366F1, #9333EA) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 10px 18px !important;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #4F46E5, #7E22CE) !important;
    box-shadow: 0 0 15px #6366F155 !important;
}

/* Input Fields */
.stTextInput input,
.stTextArea textarea,
.stChatInput textarea,
.stNumberInput input {
    background: #1E293B !important;
    color: white !important;
    border: 1px solid #6366F1 !important;
    border-radius: 10px !important;
}

/* Metric Cards */
/* Dashboard Metric Numbers - White */
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 36px !important;
    font-weight: 800 !important;
}

/* Metric Labels */
[data-testid="stMetricLabel"] {
    color: #CBD5E1 !important;
    font-weight: 600 !important;
}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1E293B, #312E81) !important;
    padding: 18px !important;
    border-radius: 14px !important;
    border: 1px solid #6366F1 !important;
}

/* Chat Messages */
[data-testid="stChatMessage"] {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 12px !important;
}

/* Selectbox */
[data-baseweb="select"] > div {
    background: #1E293B !important;
    color: white !important;
    border-color: #6366F1 !important;
}

/* Divider */
hr {
    border-color: #4338CA !important;
}

/* Footer */
footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE CONNECTION
# ==========================================

def connect_db():
    return sqlite3.connect("customer_support.db")


# ==========================================
# 4. CREATE DATABASE TABLES
# ==========================================

def create_tables():

    conn = connect_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            order_id TEXT,
            complaint TEXT,
            status TEXT DEFAULT 'Pending',
            category TEXT,
            sentiment TEXT,
            priority TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER,
            customer_name TEXT,
            rating INTEGER,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add new columns to existing databases safely
    existing_columns = [
        row[1] for row in conn.execute(
            "PRAGMA table_info(complaints)"
        ).fetchall()
    ]

    if "category" not in existing_columns:
        conn.execute("ALTER TABLE complaints ADD COLUMN category TEXT")

    if "sentiment" not in existing_columns:
        conn.execute("ALTER TABLE complaints ADD COLUMN sentiment TEXT")

    if "priority" not in existing_columns:
        conn.execute("ALTER TABLE complaints ADD COLUMN priority TEXT")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT,
            product_name TEXT,
            order_status TEXT
        )
    """)

    sample_orders = [
        ("ORD1023", "Ayesha", "Headphones", "Delivered"),
        ("ORD1024", "Divya", "Laptop Bag", "Shipped"),
        ("ORD1025", "Nithya", "Smart Watch", "Processing")
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO orders
        (order_id, customer_name, product_name, order_status)
        VALUES (?, ?, ?, ?)
    """, sample_orders)
    # DAMAGE REPORT TABLE

    conn.execute("""
        CREATE TABLE IF NOT EXISTS damage_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            order_id TEXT,
            product_name TEXT,
            damage_type TEXT,
            description TEXT,
            image_path TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # REFUND REQUEST TABLE

    conn.execute("""
        CREATE TABLE IF NOT EXISTS refund_requests (
            refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            order_id TEXT,
            request_type TEXT,
            refund_amount REAL DEFAULT 0,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # REPLACEMENT REQUEST TABLE

    conn.execute("""
        CREATE TABLE IF NOT EXISTS replacement_requests (
            replacement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            order_id TEXT,
            product_name TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# ==========================================
# 5. VERIFY ORDER
# ==========================================

def verify_order(order_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT order_id, customer_name,
               product_name, order_status
        FROM orders
        WHERE order_id = ? COLLATE NOCASE
    """, (order_id.strip(),))

    result = cursor.fetchone()

    conn.close()

    return result


# ==========================================
# 6. SAVE COMPLAINT
# ==========================================

def save_complaint(
    name,
    order_id,
    complaint,
    category=None,
    sentiment=None,
    priority=None
):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints
        (customer_name, order_id, complaint,
         category, sentiment, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        order_id,
        complaint,
        category,
        sentiment,
        priority
    ))

    complaint_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return complaint_id

# ==========================================
# UPDATE COMPLAINT STATUS
# ==========================================

def update_complaint_status(complaint_id, new_status):

    conn = connect_db()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE complaint_id = ?
    """, (new_status, complaint_id))

    conn.commit()
    conn.close()

# ==========================================
# 7. GET COMPLAINT HISTORY
# ==========================================

def get_complaints():

    conn = connect_db()

    df = pd.read_sql_query(
        "SELECT * FROM complaints ORDER BY complaint_id DESC",
        conn
    )

    conn.close()

    return df


# ==========================================
# 8. LOAD MACHINE LEARNING MODELS
# ==========================================

model = joblib.load("complaint_model.pkl")
sentiment_model = joblib.load("sentiment_model.pkl")
priority_model = joblib.load("priority_model.pkl")
# ==========================================
# ADMIN LOGIN CONFIGURATION
# ==========================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ==========================================
# 9. INITIALIZE DATABASE
# ==========================================

create_tables()


# ==========================================
# 10. LOAD DASHBOARD DATA
# ==========================================

complaints_df = get_complaints()

total_complaints = len(complaints_df)

pending_complaints = (
    len(complaints_df[complaints_df["status"] == "Pending"])
    if not complaints_df.empty else 0
)

resolved_complaints = (
    len(complaints_df[complaints_df["status"] == "Resolved"])
    if not complaints_df.empty else 0
)


# ==========================================
# 11. SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown("# 🤖 AI SUPPORT")
    st.caption("Multi-Agent Automation System")

    st.divider()

    st.markdown("### NAVIGATION")

    selected_page = st.radio(
    "Select Module",
    [
        "Dashboard",
        "Order Verification",
        "AI Complaint Analysis",
        "AI Chatbot",
        "Submit Complaint",
        "Damage Report",
        "Refund Management",
        "Replacement Request",
        "Complaint History",
        "Complaint Tracking",
        "Customer Feedback",
        "Admin Management"
    ],
    label_visibility="collapsed"
)
    st.divider()

    st.markdown("### SYSTEM STATUS")

    st.success("Application Active")

    st.info("ML Models Loaded")

    st.caption("Version 1.0 | Academic Prototype")


# ==========================================
# 12. MAIN HEADER
# ==========================================

st.markdown(
    "<h1>🤖 AI-Powered Customer Support</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='color:#91B5E3;font-size:16px;'>"
    "Intelligent Multi-Agent Customer Support Automation Dashboard"
    "</p>",
    unsafe_allow_html=True
)

st.divider()


# ==========================================
# 13. DASHBOARD WITH ANALYTICS
# ==========================================

if selected_page == "Dashboard":

    st.subheader("📊 Dashboard Overview")

    st.caption(
        "Monitor customer complaints and support analytics."
    )

    # Refresh complaint data
    complaints_df = get_complaints()

    total_complaints = len(complaints_df)

    pending_complaints = (
        len(complaints_df[complaints_df["status"] == "Pending"])
        if not complaints_df.empty else 0
    )

    resolved_complaints = (
        len(complaints_df[complaints_df["status"] == "Resolved"])
        if not complaints_df.empty else 0
    )

    # KPI Cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Complaints", total_complaints)

    with col2:
        st.metric("Pending Complaints", pending_complaints)

    with col3:
        st.metric("Resolved Complaints", resolved_complaints)

    st.divider()

    # Complaint Analytics
    st.subheader("📈 Complaint Analytics")

    if not complaints_df.empty:

        chart1, chart2 = st.columns(2)

        # Complaint Status Chart
        with chart1:

            st.markdown("#### 📊 Complaint Status")

            status_counts = (
                complaints_df["status"]
                .value_counts()
                .rename_axis("Status")
                .to_frame("Complaints")
            )

            st.bar_chart(
                status_counts,
                color="#A78BFA"
            )

        # Daily Complaint Trend
        with chart2:

            st.markdown("#### 📈 Daily Complaint Trend")

            complaints_df["created_at"] = pd.to_datetime(
                complaints_df["created_at"],
                errors="coerce"
            )

            daily_counts = (
                complaints_df
                .dropna(subset=["created_at"])
                .assign(
                    Date=lambda df: df["created_at"].dt.date
                )
                .groupby("Date")
                .size()
                .to_frame("Complaints")
            )

            if not daily_counts.empty:

                st.line_chart(
                    daily_counts,
                    color="#22D3EE"
                )

            else:

                st.info("No valid date records available.")

    else:

        st.info(
            "Submit some complaints to view analytics charts."
        )

    st.divider()

    # AI Agent Modules
    st.subheader("⚡ AI Agent Modules")

    agent1, agent2 = st.columns(2)

    with agent1:

        with st.container(border=True):

            st.markdown("### 🔍 Complaint Agent")
            st.write(
                "Predicts complaint category using Machine Learning."
            )
            st.success("Ready")

        with st.container(border=True):

            st.markdown("### 📦 Order Agent")
            st.write(
                "Verifies customer orders using SQLite database."
            )
            st.success("Ready")

    with agent2:

        with st.container(border=True):

            st.markdown("### 📋 Policy Agent")
            st.write(
                "Provides policy-based resolution recommendations."
            )
            st.success("Ready")

        with st.container(border=True):

            st.markdown("### 💬 Response Agent")
            st.write(
                "Generates personalised customer support responses."
            )
            st.success("Ready")

    st.divider()

    # Recent Complaints
    st.subheader("🕒 Recent Complaints")

    if not complaints_df.empty:

        st.dataframe(
            complaints_df.head(5),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No complaints have been submitted yet.")


# ==========================================
# 14. ORDER VERIFICATION
# ==========================================

elif selected_page == "Order Verification":

    st.subheader("📦 Order Verification")

    st.caption("Check customer order details using the order ID.")

    with st.container(border=True):

        search_order_id = st.text_input(
            "Enter Order ID",
            placeholder="Example: ORD1023",
            key="search_order"
        )

        if st.button("🔎 Verify Order", use_container_width=True):

            if search_order_id.strip():

                verified_order = verify_order(search_order_id)

                if verified_order:

                    st.success("Order Found Successfully!")

                    c1, c2 = st.columns(2)

                    with c1:
                        st.metric("Order ID", verified_order[0])
                        st.write("**Customer:**", verified_order[1])

                    with c2:
                        st.write("**Product:**", verified_order[2])
                        st.write("**Order Status:**", verified_order[3])

                else:

                    st.error("Order Not Found. Please check the Order ID.")

            else:

                st.warning("Please enter an Order ID.")


# ==========================================
# 15. AI COMPLAINT ANALYSIS
# ==========================================

elif selected_page == "AI Complaint Analysis":

    st.subheader("🔍 AI Complaint Analysis")

    st.caption("Analyse customer complaints using three ML models and the agent workflow.")

    with st.container(border=True):

        customer_message = st.text_area(
            "Enter Customer Complaint",
            placeholder="Describe your problem here...",
            height=130,
            key="classification_text"
        )

        analysis_order_id = st.text_input(
            "Enter Order ID",
            placeholder="Example: ORD1023",
            key="analysis_order_id"
        )

        if st.button("🚀 Analyse Complaint", use_container_width=True):

            if customer_message.strip():

                result = run_workflow(
                    complaint_text=customer_message,
                    customer_name="Customer",
                    order_id=analysis_order_id.strip(),
                    category_model=model,
                    sentiment_model=sentiment_model,
                    priority_model=priority_model
                )

                analysis = result["analysis"]
                policy = result["policy"]
                order = result["order"]
                response = result["response"]

                st.success("Multi-Agent Workflow Completed!")

                st.divider()

                st.markdown("### 📦 Order Agent Result")

                if order:

                    c1, c2 = st.columns(2)

                    with c1:
                        st.write("**Order ID:**", order["order_id"])
                        st.write("**Customer:**", order["customer_name"])

                    with c2:
                        st.write("**Product:**", order["product_name"])
                        st.write("**Status:**", order["order_status"])

                    st.success("Order Verified")

                else:

                    st.warning("Order not found. Please check the Order ID.")

                st.divider()

                st.markdown("### 🧠 Machine Learning Predictions")

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "Complaint Category",
                        analysis["category"]
                    )

                with c2:
                    st.metric(
                        "Customer Sentiment",
                        analysis["sentiment"]
                    )

                with c3:
                    st.metric(
                        "Priority",
                        analysis["priority"]
                    )

                st.divider()

                st.markdown("### 📋 Policy Agent Recommendation")

                with st.container(border=True):

                    st.write("**Recommended Resolution**")
                    st.write(policy["resolution"])

                    st.write("**Next Action**")
                    st.write(policy["action"])

                    if policy["human_approval_required"]:

                        st.warning(
                            "Human approval required for refund review."
                        )

                st.divider()

                st.markdown("### 💬 Response Agent")

                st.text_area(
                    "Generated Customer Response",
                    value=response,
                    height=220,
                    key="generated_response"
                )

            else:

                st.warning("Please enter a customer complaint.")


 # ==========================================
# 16. SUBMIT COMPLAINT
# ==========================================

elif selected_page == "Submit Complaint":

    st.subheader("📝 Submit Customer Complaint")

    st.caption(
        "Submit your complaint and let our AI support system analyze it."
    )

    with st.form("submit_complaint_form"):

        name = st.text_input("Customer Name")

        submission_order_id = st.text_input("Order ID")

        complaint = st.text_area(
            "Describe Your Complaint",
            height=150
        )

        submit_button = st.form_submit_button(
            "Submit Complaint",
            use_container_width=True
        )

    if submit_button:

        if (
            name.strip()
            and submission_order_id.strip()
            and complaint.strip()
        ):

            # Run AI Multi-Agent Workflow
            result = run_workflow(
                complaint_text=complaint.strip(),
                customer_name=name.strip(),
                order_id=submission_order_id.strip(),
                category_model=model,
                sentiment_model=sentiment_model,
                priority_model=priority_model
            )

            # Extract AI Predictions
            analysis = result["analysis"]

            category = analysis["category"]
            sentiment = analysis["sentiment"]
            priority = analysis["priority"]

            # Save Complaint
            complaint_id = save_complaint(
                name.strip(),
                submission_order_id.strip(),
                complaint.strip(),
                category,
                sentiment,
                priority
            )

            st.success("Complaint Saved Successfully!")

            st.metric(
                "Your Complaint ID",
                complaint_id
            )

            st.divider()

            st.subheader("🤖 AI Analysis Results")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Category", category)

            with col2:
                st.metric("Sentiment", sentiment)

            with col3:
                st.metric("Priority", priority)

            st.success(
                "Your complaint has been analyzed and saved successfully!"
            )

        else:

            st.warning("Please fill in all fields.")
            # ==========================================
# DAMAGE REPORT MODULE
# ==========================================

elif selected_page == "Damage Report":

    st.subheader("📸 Damaged Product Report")

    st.write(
        "Upload your damaged product image "
        "and submit a damage complaint."
    )

    with st.form("damage_report_form"):

        customer_name = st.text_input(
            "Customer Name"
        )

        order_id = st.text_input(
            "Order ID"
        )

        damage_type = st.selectbox(
            "Damage Type",
            [
                "Broken Product",
                "Scratches",
                "Missing Parts",
                "Packaging Damage",
                "Defective Product",
                "Wrong Product"
            ]
        )

        description = st.text_area(
            "Describe the Damage"
        )

        uploaded_image = st.file_uploader(
            "Upload Damaged Product Photo",
            type=["jpg", "jpeg", "png"]
        )

        submit_damage = st.form_submit_button(
            "Submit Damage Report"
        )

    if submit_damage:

        if not all([
            customer_name.strip(),
            order_id.strip(),
            description.strip(),
            uploaded_image
        ]):

            st.warning(
                "Please complete all fields and upload a photo."
            )

        else:

            verified_order = verify_order(order_id)

            if verified_order:

                import os

                os.makedirs(
                    "uploaded_damage_images",
                    exist_ok=True
                )

                image_path = os.path.join(
                    "uploaded_damage_images",
                    f"damage_{uploaded_image.name}"
                )

                with open(image_path, "wb") as f:
                    f.write(uploaded_image.getbuffer())

                conn = connect_db()

                conn.execute("""
                    INSERT INTO damage_reports
                    (
                        customer_name,
                        order_id,
                        product_name,
                        damage_type,
                        description,
                        image_path
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    customer_name,
                    order_id,
                    verified_order[2],
                    damage_type,
                    description,
                    image_path
                ))

                conn.commit()
                conn.close()

                st.success(
                    "Damage report submitted successfully!"
                )

                st.image(
                    uploaded_image,
                    caption="Uploaded Damaged Product",
                    width=300
                )

                st.info(
                    "Your report is waiting for admin verification."
                )

            else:

                st.error("Invalid Order ID.")
                # ==========================================
# REFUND MANAGEMENT
# ==========================================

elif selected_page == "Refund Management":

    st.subheader("💰 Refund Management")

    st.caption(
        "Request a refund or return for your order."
    )

    with st.form("refund_form"):

        customer = st.text_input(
            "Customer Name",
            key="refund_customer"
        )

        order = st.text_input(
            "Order ID",
            key="refund_order"
        )

        request_type = st.selectbox(
            "Select Request Type",
            [
                "Full Refund",
                "Partial Refund",
                "Return & Refund"
            ]
        )

        amount = st.number_input(
            "Requested Refund Amount",
            min_value=0.0,
            step=100.0
        )

        reason = st.text_area(
            "Refund Reason"
        )

        submit_refund = st.form_submit_button(
            "Submit Refund Request"
        )

    if submit_refund:

        if not all([
            customer.strip(),
            order.strip(),
            reason.strip()
        ]):

            st.warning("Please complete all required fields.")

        elif not verify_order(order):

            st.error("Invalid Order ID.")

        elif amount <= 0:

            st.warning("Enter a valid refund amount.")

        else:

            conn = connect_db()

            conn.execute("""
                INSERT INTO refund_requests
                (
                    customer_name,
                    order_id,
                    request_type,
                    refund_amount,
                    reason
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                customer,
                order,
                request_type,
                amount,
                reason
            ))

            conn.commit()
            conn.close()

            st.success(
                "Refund request submitted successfully!"
            )

            st.info(
                "Your refund request is waiting for admin approval."
            )
            # ==========================================
# CUSTOMER REPLACEMENT REQUEST
# ==========================================

elif selected_page == "Replacement Request":

    st.subheader("🔄 Product Replacement Request")

    st.caption(
        "Request a replacement for your damaged or defective product."
    )

    with st.form("replacement_form"):

        customer = st.text_input(
            "Customer Name",
            key="replacement_customer"
        )

        order = st.text_input(
            "Order ID",
            key="replacement_order"
        )

        reason = st.selectbox(
            "Replacement Reason",
            [
                "Damaged Product",
                "Defective Product",
                "Wrong Product",
                "Missing Parts",
                "Other"
            ]
        )

        description = st.text_area(
            "Describe Your Problem"
        )

        submit_replacement = st.form_submit_button(
            "Submit Replacement Request"
        )

    if submit_replacement:

        if not all([
            customer.strip(),
            order.strip(),
            description.strip()
        ]):

            st.warning("Please fill in all fields.")

        else:

            verified_order = verify_order(order)

            if verified_order:

                conn = connect_db()

                conn.execute("""
                    INSERT INTO replacement_requests
                    (
                        customer_name,
                        order_id,
                        product_name,
                        reason
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    customer.strip(),
                    order.strip(),
                    verified_order[2],
                    reason + ": " + description.strip()
                ))

                conn.commit()
                conn.close()

                st.success(
                    "Replacement request submitted successfully!"
                )

                st.info(
                    "Your request is waiting for admin approval."
                )

            else:

                st.error("Invalid Order ID.")
# ==========================================
# 17. COMPLAINT HISTORY
# ==========================================

elif selected_page == "Complaint History":

    st.subheader("📋 Customer Complaint History")

    st.caption("View all complaints registered in the database.")

    complaints_df = get_complaints()

    if not complaints_df.empty:

        st.metric(
            "Total Records",
            len(complaints_df)
        )

        st.dataframe(
            complaints_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No complaints submitted yet.")
        # ==========================================
# COMPLAINT TRACKING
# ==========================================
def get_complaint_by_id(complaint_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id,))

    result = cursor.fetchone()
    conn.close()

    return result
if selected_page == "Complaint Tracking":

    st.title("🔍 Complaint Tracking")
    st.caption("Track your complaint using Complaint ID")

    complaint_id = st.number_input(
        "Enter Complaint ID",
        min_value=1,
        step=1
    )

    if st.button("Track Complaint"):

        complaint = get_complaint_by_id(complaint_id)

        if complaint:

            st.success("Complaint Found!")

            st.write("### Complaint Details")

            st.write("**Complaint ID:**", complaint[0])
            st.write("**Customer Name:**", complaint[1])
            st.write("**Order ID:**", complaint[2])
            st.write("**Complaint:**", complaint[3])
            st.write("**Status:**", complaint[4])
            st.write("**Category:**", complaint[5])
            st.write("**Sentiment:**", complaint[6])
            st.write("**Priority:**", complaint[7])
            st.write("**Created Date:**", complaint[8])

        else:
            st.error("Complaint ID not found.")
            # ==========================================
# CUSTOMER FEEDBACK
# ==========================================

if selected_page == "Customer Feedback":

    st.title("⭐ Customer Feedback")
    st.caption("Share your experience with our support team")

    with st.form("feedback_form"):

        complaint_id = st.number_input(
            "Complaint ID",
            min_value=1,
            step=1
        )

        customer_name = st.text_input("Customer Name")

        rating = st.select_slider(
            "Rate Your Experience",
            options=[1, 2, 3, 4, 5],
            value=5
        )

        st.write("⭐" * rating)

        comments = st.text_area("Your Feedback")

        submitted = st.form_submit_button("Submit Feedback")

        if submitted:

            if not customer_name.strip() or not comments.strip():
                st.warning("Please enter your name and feedback.")

            else:
                conn = connect_db()

                conn.execute("""
                    INSERT INTO feedback
                    (complaint_id, customer_name, rating, comments)
                    VALUES (?, ?, ?, ?)
                """, (
                    complaint_id,
                    customer_name,
                    rating,
                    comments
                ))

                conn.commit()
                conn.close()

                st.success("Thank you! Your feedback submitted successfully.")
# ==========================================
# ADMIN COMPLAINT MANAGEMENT FUNCTIONS
# ==========================================

def update_complaint_status(complaint_id, new_status):

    conn = connect_db()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE complaint_id = ?
    """, (new_status, complaint_id))

    conn.commit()
    conn.close()


def get_complaint_by_id(complaint_id):

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id,))

    result = cursor.fetchone()

    conn.close()

    return result

if selected_page == "AI Chatbot":

    st.title("🤖 AI Customer Support Chatbot")
    st.caption("Ask me anything about orders, refunds and replacements.")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Clear Chat Button
    col1, col2 = st.columns([4, 1])

    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Display previous messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_message = st.chat_input("Type your question here...")

    if user_message:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_message
        })

        with st.chat_message("user"):
            st.markdown(user_message)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                reply = chatbot_reply(user_message)
                st.markdown(reply)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": reply
        })
# ==========================================
# 18. ADMIN COMPLAINT MANAGEMENT
# ==========================================

if selected_page == "Admin Management":

    st.subheader("🔵 Admin Complaint Management")

    st.caption(
        "Manage customer complaints and update their status."
    )

    # Get all complaints
    admin_df = get_complaints()

    # Check whether complaints exist
    if not admin_df.empty:

        # ----------------------------------
        # FILTER COMPLAINTS
        # ----------------------------------

        st.markdown("### 🔎 Filter Complaints")

        col1, col2 = st.columns(2)

        with col1:

            status_filter = st.selectbox(
                "Filter by Status",
                [
                    "All",
                    "Pending",
                    "In Progress",
                    "Resolved"
                ]
            )

        with col2:

            priority_filter = st.selectbox(
                "Filter by Priority",
                [
                    "All",
                    "High",
                    "Medium",
                    "Low"
                ]
            )

        # Apply filters
        filtered_df = admin_df.copy()

        if status_filter != "All":

            filtered_df = filtered_df[
                filtered_df["status"] == status_filter
            ]

        if priority_filter != "All":

            filtered_df = filtered_df[
                filtered_df["priority"] == priority_filter
            ]

        # ----------------------------------
        # COMPLAINT RECORDS
        # ----------------------------------

        st.divider()

        st.markdown("### 📋 Complaint Records")

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------
        # UPDATE COMPLAINT STATUS
        # ----------------------------------

        st.divider()

        st.markdown("### ✏️ Update Complaint Status")

        complaint_ids = admin_df["complaint_id"].tolist()

        selected_id = st.selectbox(
            "Select Complaint ID",
            complaint_ids
        )

        selected_complaint = admin_df[
            admin_df["complaint_id"] == selected_id
        ].iloc[0]

        st.write(
            "**Customer:**",
            selected_complaint["customer_name"]
        )

        st.write(
            "**Order ID:**",
            selected_complaint["order_id"]
        )

        st.write(
            "**Complaint:**",
            selected_complaint["complaint"]
        )

        st.write(
            "**Current Status:**",
            selected_complaint["status"]
        )

        new_status = st.selectbox(
            "Choose New Status",
            [
                "Pending",
                "In Progress",
                "Resolved"
            ],
            key="admin_new_status"
        )

        if st.button(
            "💾 Update Status",
            use_container_width=True
        ):

            update_complaint_status(
                selected_id,
                new_status
            )

            st.success(
                f"Complaint #{selected_id} updated successfully!"
            )

            st.rerun()

    else:

        st.info(
            "No complaints available for administration."
        )
        # ==========================================
# ADMIN REFUND APPROVAL
# ==========================================

if selected_page == "Admin Management":

    st.divider()

    st.subheader("💰 Admin Refund Management")

    conn = connect_db()

    refund_df = pd.read_sql_query(
        """
        SELECT * FROM refund_requests
        ORDER BY refund_id DESC
        """,
        conn
    )

    conn.close()

    if not refund_df.empty:

        st.markdown("### 📊 Refund Overview")

        pending = len(
            refund_df[refund_df["status"] == "Pending"]
        )

        approved = len(
            refund_df[refund_df["status"] == "Approved"]
        )

        rejected = len(
            refund_df[refund_df["status"] == "Rejected"]
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Pending Refunds", pending)
        c2.metric("Approved Refunds", approved)
        c3.metric("Rejected Refunds", rejected)

        st.divider()

        st.markdown("### 📋 Refund Requests")

        st.dataframe(
            refund_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### ✏️ Review Refund Request")

        refund_ids = refund_df["refund_id"].tolist()

        selected_refund = st.selectbox(
            "Select Refund ID",
            refund_ids,
            key="admin_refund_id"
        )

        refund = refund_df[
            refund_df["refund_id"] == selected_refund
        ].iloc[0]

        st.write("**Customer:**", refund["customer_name"])
        st.write("**Order ID:**", refund["order_id"])
        st.write("**Request Type:**", refund["request_type"])
        st.write("**Amount:**", refund["refund_amount"])
        st.write("**Reason:**", refund["reason"])
        st.write("**Current Status:**", refund["status"])

        if refund["status"] == "Pending":

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✅ Approve Refund",
                    use_container_width=True
                ):

                    conn = connect_db()

                    conn.execute(
                        """
                        UPDATE refund_requests
                        SET status = 'Approved'
                        WHERE refund_id = ?
                        """,
                        (selected_refund,)
                    )

                    conn.commit()
                    conn.close()

                    st.success("Refund request approved!")

                    st.rerun()

            with col2:

                if st.button(
                    "❌ Reject Refund",
                    use_container_width=True
                ):

                    conn = connect_db()

                    conn.execute(
                        """
                        UPDATE refund_requests
                        SET status = 'Rejected'
                        WHERE refund_id = ?
                        """,
                        (selected_refund,)
                    )

                    conn.commit()
                    conn.close()

                    st.warning("Refund request rejected!")

                    st.rerun()

        else:

            st.info(
                "This refund request has already been reviewed."
            )

    else:

        st.info("No refund requests available.")
        # ==========================================
# ADMIN REPLACEMENT MANAGEMENT
# ==========================================

if selected_page == "Admin Management":

    st.divider()

    st.subheader("🔄 Admin Replacement Management")

    conn = connect_db()

    replacement_df = pd.read_sql_query(
        """
        SELECT * FROM replacement_requests
        ORDER BY replacement_id DESC
        """,
        conn
    )

    conn.close()

    if not replacement_df.empty:

        pending = len(
            replacement_df[
                replacement_df["status"] == "Pending"
            ]
        )

        approved = len(
            replacement_df[
                replacement_df["status"] == "Approved"
            ]
        )

        rejected = len(
            replacement_df[
                replacement_df["status"] == "Rejected"
            ]
        )

        c1, c2, c3 = st.columns(3)

        c1.metric("Pending", pending)
        c2.metric("Approved", approved)
        c3.metric("Rejected", rejected)

        st.markdown("### 📋 Replacement Requests")

        st.dataframe(
            replacement_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### ✏️ Review Replacement")

        replacement_ids = replacement_df[
            "replacement_id"
        ].tolist()

        selected_replacement = st.selectbox(
            "Select Replacement ID",
            replacement_ids,
            key="admin_replacement_id"
        )

        replacement = replacement_df[
            replacement_df["replacement_id"]
            == selected_replacement
        ].iloc[0]

        st.write(
            "**Customer:**",
            replacement["customer_name"]
        )

        st.write(
            "**Order ID:**",
            replacement["order_id"]
        )

        st.write(
            "**Product:**",
            replacement["product_name"]
        )

        st.write(
            "**Reason:**",
            replacement["reason"]
        )

        st.write(
            "**Status:**",
            replacement["status"]
        )

        if replacement["status"] == "Pending":

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✅ Approve Replacement",
                    use_container_width=True
                ):

                    conn = connect_db()

                    conn.execute("""
                        UPDATE replacement_requests
                        SET status = 'Approved'
                        WHERE replacement_id = ?
                    """, (selected_replacement,))

                    conn.commit()
                    conn.close()

                    st.success(
                        "Replacement approved successfully!"
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "❌ Reject Replacement",
                    use_container_width=True
                ):

                    conn = connect_db()

                    conn.execute("""
                        UPDATE replacement_requests
                        SET status = 'Rejected'
                        WHERE replacement_id = ?
                    """, (selected_replacement,))

                    conn.commit()
                    conn.close()

                    st.warning(
                        "Replacement request rejected."
                    )

                    st.rerun()

    else:

        st.info("No replacement requests available.")
        # ==========================================
# ADMIN FEEDBACK MANAGEMENT
# ==========================================

if selected_page == "Admin Management":

    st.divider()
    
    st.subheader("⭐ Customer Feedback Management")

    conn = connect_db()

    feedback_df = pd.read_sql_query("""
        SELECT *
        FROM feedback
        ORDER BY created_at DESC
    """, conn)

    conn.close()

    if not feedback_df.empty:

        st.metric(
            "Average Customer Rating",
            f"{feedback_df['rating'].mean():.1f} / 5 ⭐"
        )

        st.dataframe(
            feedback_df,
            use_container_width=True
        )

    else:
        st.info("No customer feedback available yet.")
# 19. FOOTER

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; padding:15px; color:#9CA3AF;">
        <h4 style="color:#60A5FA;">
            AI-Powered Multi-Agent Customer Support Automation System
        </h4>
        <p>Intelligent Complaint Analysis | Order Verification</p>
        <p>Developed using Python and Streamlit</p>
        <p>© 2026 Customer Support System</p>
    </div>
    """,
    unsafe_allow_html=True
)