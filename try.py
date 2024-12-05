import streamlit as st
import PyPDF2
import pytesseract
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Set Tesseract path (make sure this is the correct path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\DELL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF with improved error handling"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + " "
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def extract_text_from_image(image_file):
    """Extract text from image using Tesseract OCR"""
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        st.error(f"Error reading image: {str(e)}")
        return None

def analyze_medical_report_with_explanations(text):
    """Generate a simple and patient-friendly health status explanation"""
    if not api_key:
        return {"error": "API key not configured"}
    
    prompt = f"""
    Perform a comprehensive analysis of the provided medical report, making it clear and easy to understand for the patient. Use simple language and avoid complex medical terms.
    
    1. For each key health metric, explain:
       - What it measures.
       - What is the result of the measurement.
       - What is the normal range for this measurement (if applicable).
       - What the result means for the patient's health (interpretation).
    
    2. Provide personalized recommendations for improving health in an easy-to-understand format:
       - Lifestyle and dietary changes.
       - Follow-up tests or consultations.
       - Preventative measures.

    Format the response into two sections: "Health Status Insights" and "Personalized Recommendations."

    Medical Report Text:
    {text}
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return {"detailed_explanation": response.text.strip()}
    except Exception as e:
        return {"error": f"Error analyzing report: {str(e)}"}

def chatbot_response(user_input, analysis_result):
    """Generate chatbot response based on the analyzed report"""
    prompt = f"""
    You are a compassionate medical assistant. Use the following analysis to respond:
    
    Medical Report Analysis:
    {analysis_result}
    
    User Question:
    {user_input}
    
    Guidelines:
    - Use simple and empathetic language.
    - Avoid medical jargon where possible.
    - Provide actionable advice and support.
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating response: {str(e)}"

def main():
    st.set_page_config(
        page_title="MediInsight: Medical Report Analyzer", 
        page_icon="🩺", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for styling
    st.markdown("""
    <style>
    .main-title {
        color: white; /* Set title color to white */
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    body {
        background-color: #1e1e1e; /* Optional: Set background color to dark for contrast */
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main Title
    st.markdown("<h1 class='main-title'>🩺 MediInsight: Medical Report Analyzer</h1>", unsafe_allow_html=True)

    st.sidebar.header("📋 About MediInsight")
    st.sidebar.info("""
    🔍 Analyze your medical report:
    - Get a summary of your health status.
    - Receive personalized recommendations.
    - Ask questions through an interactive chatbot.
    """)

    # File Upload - Allow both PDF and Image file uploads
    uploaded_file = st.file_uploader("Upload your medical report (PDF or Image)", type=['pdf', 'png', 'jpg', 'jpeg'])

    # Select interface: either analysis or chatbot
    interface_choice = st.selectbox("Choose Interface", ["Medical Report Analysis", "Chatbot Interaction"])

    if interface_choice == "Medical Report Analysis":
        if uploaded_file:
            with st.spinner("🔍 Analyzing your medical report..."):
                if uploaded_file.type == "application/pdf":
                    text = extract_text_from_pdf(uploaded_file)
                else:
                    text = extract_text_from_image(uploaded_file)

                if text:
                    analysis_result = analyze_medical_report_with_explanations(text)
                    
                    if "error" not in analysis_result:
                        # Display Insights and Recommendations
                        st.markdown("## 🩺 Health Status Insights")
                        health_status = analysis_result["detailed_explanation"].split("Personalized Recommendations")[0].strip()
                        st.markdown(health_status)

                        # Check if "Personalized Recommendations" section exists
                        if "Personalized Recommendations" in analysis_result["detailed_explanation"]:
                            recommendations = analysis_result["detailed_explanation"].split("Personalized Recommendations")[1].strip()
                            st.markdown("## Personalized Recommendations")
                            st.markdown(recommendations)
                        else:
                            st.markdown("## Personalized Recommendations")
                            st.markdown("No specific recommendations were provided. Please consult with your healthcare provider for further guidance.")
                    else:
                        st.error(f"Error analyzing report: {analysis_result['error']}")
                else:
                    st.error("Could not process the uploaded file. Please upload a valid medical report.")
    
    elif interface_choice == "Chatbot Interaction":
        st.markdown("## 🤖 Ask Questions About Your Report")
        user_input = st.text_input("Ask a question:")

        if uploaded_file and user_input:
            with st.spinner("🔍 Analyzing your medical report..."):
                if uploaded_file.type == "application/pdf":
                    text = extract_text_from_pdf(uploaded_file)
                else:
                    text = extract_text_from_image(uploaded_file)

                if text:
                    analysis_result = analyze_medical_report_with_explanations(text)
                    if "error" not in analysis_result:
                        response = chatbot_response(user_input, analysis_result["detailed_explanation"])
                        st.markdown(f"**Medical Assistant:** {response}")
                    else:
                        st.error(f"Error analyzing report: {analysis_result['error']}")
                else:
                    st.error("Could not process the uploaded file. Please upload a valid medical report.")

if __name__ == "__main__":
    main()
