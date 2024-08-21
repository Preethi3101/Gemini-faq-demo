import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

google_api_key = os.getenv('GOOGLE_API_KEY')

def preprocess_text(text):
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = text.lower()
    return text

def generate_responses(prompt, model):
    response = model.generate_content(prompt)
    return response.text

def main():
    st.set_page_config(
        page_title="FAQ Extraction Web App",
        page_icon=":books:",
        layout="wide",
    )
    
    st.markdown("""
        <style>
        body { font-family: 'Arial', sans-serif; }
        .stApp { background-color: #f5f5f5; }
        .header { color: #2e3b4e; font-weight: bold; font-size: 30px; text-align: center; padding: 20px 0; }
        .subheader { color: #4a6fa5; font-weight: bold; font-size: 24px; margin-top: 20px; }
        .main-container { background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
        .button { background-color: #4a6fa5; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .info-message { color: #007bff; font-size: 18px; font-weight: bold; margin-top: 20px; }
        .error-message { color: #ff0000; font-size: 18px; font-weight: bold; margin-top: 20px; }
        .response-text { color: #333333; font-size: 16px; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='header'>FAQ Extraction Web App</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)

            if 'Transcript' in df.columns:
                transcript = df['Transcript'].str.cat(sep='\n')

                cleaned_text = preprocess_text(transcript)

                # Initialize Google Gemini
                genai.configure(api_key=google_api_key)
                generation_config = {
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "top_k": 10,
                    "max_output_tokens": 1024,
                }
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                ]

                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash-latest",
                    safety_settings=safety_settings,
                    generation_config=generation_config,
                    system_instruction="You are a professional assistant that generates FAQs based on the provided content."
                )

                topics = st.multiselect(
                    "Select Topics",
                    ["ACM", "User Management", "Ackumen General", "Connected Planning", "Chemical Ordering", "Smart Inventory", "Process View", "Connected Lab", "MCA", "Ackumen Data Entry", "ABM", "3PC", "Report Builder", "Charts", "Pricing", "Equipment Ordering", "Alarms", "Ackumen Document Management", "Ackumen Quotes", "Ackumen CRM"]
                )

                if topics:
                    responses = {}
                    for topic in topics:
                        prompt = f"""
                        Below is a transcript of conversations that contains content related to {topic}.
                        Please consider only the sentences with the keyword {topic} 
                        Please extract the top 10 frequently asked questions (FAQs) about {topic} from the content. 
                        Ensure to pick each question that appears greater than 20 times in the transcript. 
                        Provide only the questions with the frequency of occurance greater than 35, not the answers, and make sure all questions are unique and related to the context of {topic}.
                        Please use varied question tags for a single response as in what why where can How etc.,
                        Your Response should contain question and its frequency.

                        Transcript:
                        {cleaned_text}
                        """
                        response = generate_responses(prompt, model)
                        responses[topic] = response

                    st.markdown("<div class='subheader'>Generated FAQs</div>", unsafe_allow_html=True)
                    for topic, response in responses.items():
                        st.markdown(f"### {topic}")
                        st.markdown(f"<div class='response-text'>{response}</div>", unsafe_allow_html=True)

                    if st.button("Create Excel File and Send Response to It"):
                        excel_writer = pd.ExcelWriter("output.xlsx", engine="xlsxwriter")

                        for topic, response in responses.items():
                            questions = response.split('\n')
                            df_responses = pd.DataFrame({"Question": questions, "Count": [None] * len(questions)})
                            df_responses.to_excel(excel_writer, sheet_name=topic, index=False)

                        excel_writer.close()

                        with open("output.xlsx", "rb") as file:
                            st.download_button(
                                label="Download Excel",
                                data=file.read(),
                                file_name="output.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.markdown("<div class='info-message'>Please select at least one topic to proceed.</div>", unsafe_allow_html=True)

            else:
                st.markdown("<div class='error-message'>The uploaded Excel file does not contain a 'Transcript' column.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-message'>Please upload an Excel file to proceed.</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
