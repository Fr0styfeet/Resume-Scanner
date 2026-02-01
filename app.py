import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json
import re
import string

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# PDF text extractor
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += str(page.extract_text())
    return text

from textblob import TextBlob
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def extract_relevant_keywords(text):
    blob = TextBlob(text.lower())
    
    # POS tagging + stopword removal
    keywords = [
        word.lemmatize()
        for word, tag in blob.tags
        if tag.startswith(('NN', 'VB', 'JJ'))  # Keep nouns, verbs, adjectives
        and word.isalpha()
        and word not in ENGLISH_STOP_WORDS
    ]

    return list(set(keywords))

# Response parser
def parse_response(response_text):
    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            return {"error": "❗ Gemini did not return valid JSON format."}
    except Exception as e:
        return {"error": f"❗ Failed to parse response: {e}"}

# Gemini API
def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return parse_response(response.text)

# Prompt Template
input_prompt = """
You are an advanced ATS system. ONLY respond in valid JSON format like this:
{{"JD Match":"<match>%", "MissingKeywords":["<keyword1>", "<keyword2>"], "Profile Summary":"<summary>"}}

Evaluate the following resume against the job description.
The missing keywords should be those that are related to the job and field.
Resume:
{text}

Job Description:
{jd}

The resume and JD keywords have been extracted using simple keyword analysis.
"""

# Streamlit App
st.title("📄 Smart ATS Resume Checker")
st.text("Get resume match insights based on job descriptions!")

jd = st.text_area("📌 Paste the Job Description")
uploaded_file = st.file_uploader("📁 Upload Your Resume (PDF only)", type="pdf")

submit = st.button("🚀 Submit")

if submit:
    if uploaded_file and jd.strip():
        with st.spinner("Analyzing..."):
            resume_text = input_pdf_text(uploaded_file)

            # Extract keywords (for your reference/debugging, not sent)
            jd_keywords = extract_relevant_keywords(jd)
            resume_keywords = extract_relevant_keywords(resume_text)

            # Format prompt
            prompt = input_prompt.format(text=resume_text, jd=jd)
            result = get_gemini_response(prompt)

        if "error" in result:
            st.error(result["error"])
        else:
            st.subheader("✅ JD Match:")
            st.write(result["JD Match"])

            st.subheader("📌 Missing Keywords:")
            st.write(result["MissingKeywords"])

            st.subheader("📝 Profile Summary Suggestion:")
            st.write(result["Profile Summary"])
    else:
        st.warning("Please upload a resume and provide a job description.")