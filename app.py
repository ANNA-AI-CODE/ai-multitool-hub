import os
import re
import streamlit as st
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import PyPDF2

# Initialize Streamlit Page Layout
st.set_page_config(page_title="AI Multi-Tool Hub & Suite", page_icon="⚡", layout="wide")

def get_gemini_client():
    return genai.Client()

def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL format.")

def get_transcript(video_id: str) -> str:
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript_list])
    except Exception as e:
        raise RuntimeError(f"Could not fetch captions/transcript: {e}")

def extract_text_from_pdf(pdf_file) -> str:
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        if not text.strip():
            raise ValueError("The uploaded PDF appears to be empty or scanned images.")
        return text
    except Exception as e:
        raise RuntimeError(f"Error reading PDF file: {e}")

def run_ai_task(content_input: str, category: str, tool_name: str, summary_style: str, language: str):
    client = get_gemini_client()
    
    prompts = {
        "Summary": f"Provide a summary of the text in {language}. Style constraint: structured strictly as a **{summary_style}** format.\n\nText:\n{content_input}",
        "ChatPDF": f"Act as an interactive document assistant. Answer questions or explain insights about this text in {language}:\n\n{content_input}",
        "AI PDF Translator": f"Translate the entire text accurately into {language}:\n\n{content_input}",
        "PDF to Video": f"Create a script and scene-by-scene storyboard layout for a video based on this text, written in {language}:\n\n{content_input}",
        "AI PDF Converter": f"Clean up, reformat, and restructure this raw document text into professional markdown structure in {language}:\n\n{content_input}",

        "AI Homework Helper": f"Provide step-by-step solutions, explanations, and guidance for the homework assignment or text provided, written in {language}:\n\n{content_input}",
        "AI Math Solver": f"Solve any mathematical problems, equations, or logic puzzles found in this text with step-by-step reasoning, written in {language}:\n\n{content_input}",
        "AI Quiz Generator": f"Create 5 interactive multiple-choice quiz questions with answers and explanations based on this text, written in {language}:\n\n{content_input}",
        "AI Flashcard Maker": f"Create 5 digital flashcards (Front: Concept/Term, Back: Definition/Explanation) based on this text, written in {language}:\n\n{content_input}",

        "AI Detector": f"Analyze this text to evaluate writing style patterns, estimating if it reads like AI or human text, providing feedback in {language}:\n\n{content_input}",
        "AI Humanizer": f"Rewrite this text to sound completely natural, engaging, and conversational like a real human writer, in {language}:\n\n{content_input}",
        "AI Essay Writer": f"Write a comprehensive, well-structured professional essay based on this prompt or topic, written in {language}:\n\n{content_input}",
        "AI Essay Grader": f"Grade this essay, provide constructive feedback, point out flaws, and assign an estimated score, written in {language}:\n\n{content_input}",
        "APA Citation Generator": f"Generate formal APA style references and citations based on the provided text or source details, written in {language}:\n\n{content_input}",
        "AI Mind Map Generator": f"Create a structured hierarchical markdown outline representing a mind map layout based on this text, written in {language}:\n\n{content_input}",

        "AI Diagram Generator": f"Create a text-based ASCII structure or Mermaid.js chart code blueprint mapping out a clear diagram for this text, written in {language}:\n\n{content_input}",
        "AI Flowchart Generator": f"Create a step-by-step flowchart sequence blueprint using clear textual node steps for this text, written in {language}:\n\n{content_input}",
        "AI Infographic Generator": f"Design a visual concept layout, sections, icons, and descriptive blueprint for an infographic explaining this text, written in {language}:\n\n{content_input}",
    }

    prompt_text = prompts.get(tool_name, f"Process this text in {language}:\n\n{content_input}")
    system_instruction = f"You are an elite, multi-functional AI assistant, academic advisor, and content creator. Always respond precisely in {language}."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_text,
        config={
            "system_instruction": system_instruction,
            "temperature": 0.3
        }
    )
    return response.text

def create_pdf(content_text, title="AI_Report.pdf"):
    pdf_filename = "temp_output.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor='#1f2937', spaceAfter=12)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=11, textColor='#4b5563', spaceAfter=8, leading=14)
    
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))
    
    for line in content_text.split('\n'):
        if line.strip():
            story.append(Paragraph(line, body_style))
        else:
            story.append(Spacer(1, 6))
            
    doc.build(story)
    return pdf_filename

st.sidebar.title("⚡ More Tools Dashboard")
category_choice = st.sidebar.radio(
    "Categories", 
    ["📁 AI PDF Tools", "📚 AI Study Tools", "✍️ AI Writer Tools", "📊 AI Diagram Tools"]
)

tool_mapping = {
    "📁 AI PDF Tools": ["Summary", "ChatPDF", "AI PDF Translator", "PDF to Video", "AI PDF Converter"],
    "📚 AI Study Tools": ["AI Homework Helper", "AI Math Solver", "AI Quiz Generator", "AI Flashcard Maker"],
    "✍️ AI Writer Tools": ["AI Detector", "AI Humanizer", "AI Essay Writer", "AI Essay Grader", "APA Citation Generator", "AI Mind Map Generator"],
    "📊 AI Diagram Tools": ["AI Diagram Generator", "AI Flowchart Generator", "AI Infographic Generator"]
}

selected_tool = st.sidebar.selectbox("Choose Specific Tool", tool_mapping[category_choice])

st.title(f"⚡ Hub: {selected_tool}")
st.markdown(f"Running tool under category **{category_choice}** with full multilingual and formatting controls.")

col1, col2 = st.columns([1, 1])

with col1:
    input_source = st.selectbox("Select Input Source Type", ["PDF File Upload", "YouTube URL", "Raw Text / Notes"])
    
    raw_text_input = ""
    uploaded_pdf = None
    
    if input_source == "PDF File Upload":
        uploaded_pdf = st.file_uploader("Upload target PDF document:", type=["pdf"])
    elif input_source == "YouTube URL":
        raw_text_input = st.text_input("Paste YouTube Video URL:")
    else:
        raw_text_input = st.text_area("Paste text notes, homework question, or topic prompt here:")

with col2:
    target_language = st.selectbox(
        "🌍 Output Language", 
        ["English", "Spanish", "French", "German", "Hindi", "Mandarin", "Japanese", "Arabic", "Telugu", "Portuguese"]
    )
    
    summary_style = "Bullet Points"
    if selected_tool == "Summary":
        st.markdown("### 📌 Summary Format Option")
        summary_style = st.radio(
            "Select format style:", 
            ["Paragraph", "Detailed", "Bullet Points"], 
            horizontal=True
        )

if st.button(f"🚀 Run {selected_tool}", type="primary"):
    if input_source == "PDF File Upload" and not uploaded_pdf:
        st.error("Please upload a PDF file to proceed.")
    elif input_source != "PDF File Upload" and not raw_text_input.strip():
        st.error("Please provide valid text or a YouTube URL input.")
    else:
        try:
            with st.spinner(f"Executing {selected_tool} via Gemini AI..."):
                if input_source == "PDF File Upload":
                    source_content = extract_text_from_pdf(uploaded_pdf)
                elif input_source == "YouTube URL":
                    vid_id = extract_video_id(raw_text_input)
                    source_content = get_transcript(vid_id)
                else:
                    source_content = raw_text_input
                
                ai_output = run_ai_task(source_content, category_choice, selected_tool, summary_style, target_language)
            
            st.success("Execution Successful!")
            st.markdown("---")
            st.markdown(f"### 📄 Result: {selected_tool} ({target_language})")
            st.markdown(ai_output)
            
            pdf_path = create_pdf(ai_output, title=f"AI Report - {selected_tool} ({target_language})")
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📥 Download Result as PDF",
                    data=pdf_file,
                    file_name=f"ai_{selected_tool.lower().replace(' ', '_')}_report.pdf",
                    mime="application/pdf"
                )
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
