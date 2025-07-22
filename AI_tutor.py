import streamlit as st
from openai import OpenAI
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# Page Config
st.set_page_config(page_title="AI Tutor", page_icon="🤖")

st.title("🤖 AI Tutor")

api_key = "AIzaSyDrx7j5XPIztMz274t-ItjxSE55sr6Q39g" # Put your OpenAI-compatible Gemini API Key here
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

try:
    gemini_model = OpenAI(api_key=api_key, base_url=BASE_URL)
except Exception as e:
    st.error(f"Error initializing AI model: {str(e)}")
    st.stop()

def tutor(problem):
    if not problem or len(problem.strip()) < 3:
        return "Please enter a detailed question to get help!"

    try:
        system_message = """I want you to act as a friendly AI tutor.
When I ask a question, you should:

Give clear and simple answers
Break down complex ideas into small steps
Use examples or analogies when possible
Correct my factual mistakes politely
Provide complete, well-commented code if the question is about programming
No word limit is required."""

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
            return "**API Key Error**: Please check your API key and try again."
        elif "QUOTA" in error_msg.upper():
            return "⚠️ **Quota Exceeded**: You've reached your API usage limit. Please try again later."
        elif "RATE" in error_msg.upper():
            return "**Rate Limited**: Too many requests. Please wait a moment and try again."
        else:
            return f"**Error**: {error_msg}\n\n💡 Please try rephrasing your question or check your internet connection."

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

# --- Session State Init ---
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("current_question", "")
st.session_state.setdefault("current_answer", "")

st.markdown("Ask your question:")
user_question = st.chat_input("Enter your doubts, questions, or problems here...")

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

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Download PDF Summary", use_container_width=True):
            try:
                pdf_file = create_improved_pdf(
                    st.session_state.current_answer,
                    st.session_state.current_question
                )
                st.download_button(
                    label="Download PDF",
                    data=pdf_file,
                    file_name=f"ai_tutor_session_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("PDF ready for download!")
            except Exception as e:
                st.error(f"Error creating PDF: {str(e)}")

# --- Chat History ---
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
