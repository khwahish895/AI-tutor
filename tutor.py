import streamlit as st
from openai import OpenAI
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Tutor", page_icon="🤖")

# ---------------- STATE INIT ----------------
if "users" not in st.session_state:
    st.session_state.users = {"user1": "pass123", "alice": "wonderland", "bob": "builder"}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "login"
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("current_question", "")
st.session_state.setdefault("current_answer", "")

# ---------------- LOGIN PAGE ----------------
def login_page():
    st.title("🔐 Login to AI Tutor")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username in st.session_state.users and st.session_state.users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.markdown("Don't have an account?")
    if st.button("Go to Sign Up"):
        st.session_state.page = "signup"
        st.rerun()

# ---------------- SIGNUP PAGE ----------------
def signup_page():
    st.title("📝 Sign Up for AI Tutor")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    signup_btn = st.button("Sign Up")

    if signup_btn:
        if new_username in st.session_state.users:
            st.warning("Username already exists. Choose another.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        elif not new_username or not new_password:
            st.error("Username and password cannot be empty.")
        else:
            st.session_state.users[new_username] = new_password
            st.success("Account created successfully! Please log in.")
            st.session_state.page = "login"
            st.rerun()

    st.markdown("Already have an account?")
    if st.button("Go to Login"):
        st.session_state.page = "login"
        st.rerun()

# ---------------- AI TUTOR FUNCTION ----------------
def tutor(problem):
    if not problem or len(problem.strip()) < 3:
        return "Please enter a detailed question to get help!"
    try:
        api_key = "YOUR_GEMINI_COMPATIBLE_API_KEY"  # Replace with your key
        BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
        gemini_model = OpenAI(api_key=api_key, base_url=BASE_URL)

        system_message = """I want you to act as a friendly AI tutor.
Give clear and simple answers.
Break down complex ideas into small steps.
Use examples or analogies when possible.
Correct my factual mistakes politely.
Provide well-commented code for programming questions."""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": problem}
        ]

        with st.spinner("Thinking... Please wait"):
            response = gemini_model.chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=messages,
                max_tokens=1200,
                temperature=0.7
            )
        return response.choices[0].message.content

    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg.upper():
            return "**API Key Error**: Please check your API key."
        elif "QUOTA" in error_msg.upper():
            return "⚠️ **Quota Exceeded**."
        elif "RATE" in error_msg.upper():
            return "**Rate Limited**. Please wait."
        else:
            return f"**Error**: {error_msg}"

# ---------------- PDF GENERATOR ----------------
def create_improved_pdf(text, question):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("AI Tutor Session Summary", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Question Asked:", styles['Heading2']))
    story.append(Paragraph(question, styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("AI Tutor Response:", styles['Heading2']))

    for para in text.split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), styles['Normal']))
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------- MAIN INTERFACE ----------------
def tutor_interface():
    st.title("🤖 AI Tutor")
    st.markdown(f"👋 Welcome, **{st.session_state.username}**!")

    # View all signed-up users
    with st.expander("🧑‍💻 View All Signed-Up Users"):
        st.markdown("These users have signed up:")
        for user in st.session_state.users:
            st.markdown(f"✅ {user}")

    # Logout
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Chat input
    user_question = st.chat_input("Ask me anything...")

    if user_question:
        st.session_state.current_question = user_question
        ai_response = tutor(user_question)
        st.session_state.current_answer = ai_response
        st.session_state.chat_history.append({
            "question": user_question,
            "answer": ai_response
        })

    if st.session_state.current_question and st.session_state.current_answer:
        st.markdown("### Current Session:")
        st.info(f"**Your Question:** {st.session_state.current_question}")
        st.success(f"**AI Tutor Response:**\n\n{st.session_state.current_answer}")

        if st.button("Download PDF Summary", use_container_width=True):
            try:
                pdf_file = create_improved_pdf(
                    st.session_state.current_answer,
                    st.session_state.current_question
                )
                st.download_button(
                    label="Download PDF",
                    data=pdf_file,
                    file_name=f"ai_tutor_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("PDF ready!")
            except Exception as e:
                st.error(f"Error creating PDF: {str(e)}")

    # Chat History
    if st.session_state.chat_history:
        st.markdown("### Previous Questions:")
        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
            with st.expander(f"Question {len(st.session_state.chat_history) - i}: {chat['question'][:50]}..."):
                st.markdown(f"**Question:** {chat['question']}")
                st.markdown(f"**Answer:** {chat['answer']}")

        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.current_question = ""
            st.session_state.current_answer = ""
            st.rerun()

# ---------------- ROUTER ----------------
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        login_page()
    else:
        signup_page()
else:
    tutor_interface()
