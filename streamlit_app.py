import streamlit as st
from PIL import Image
import pytesseract
from streamlit_mic_recorder import speech_to_text
from src.digital_comp.crew import SchemeAndDocumentCrew
import re

# Set up Tesseract (adjust path for your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def show_scheme_reminders(agent_output: str):
    # 📅 Deadline detection
    deadline_match = re.search(
        r'(Deadline|Last date|Apply before):?\s*(\d{1,2}(st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})',
        agent_output, re.IGNORECASE
    )

    # 🧓 Age eligibility (improved)
    age_match = re.search(
        r'(above|over|under|below)?\s*(the\s+age\s+of\s+)?(\d{1,2})\s*(years)?(\s*(and|to|–|-)\s*(\d{1,2}))?',
        agent_output, re.IGNORECASE
    )

    # 🧒 Minor eligibility
    minor_match = re.search(
        r'(minor|children)\s*\(?(aged|age)?\s*(\d{1,2})\s*(to|–|-)\s*(\d{1,2})\)?',
        agent_output, re.IGNORECASE
    )

    # 💰 Income eligibility (improved)
    income_match = re.search(
        r'(BPL|Below Poverty Line|income\s*(below|under|less than)?\s*₹?\s*\d{1,3}(,\d{3})*|no income (restrictions|limit))',
        agent_output, re.IGNORECASE
    )

    # Show deadline
    if deadline_match:
        st.warning(f"⏰ Deadline: {deadline_match.group(0)}")

    # Show age requirement
    if age_match:
        st.info(f"🎯 Age Requirement: {age_match.group(0)}")
    
    if minor_match:
        st.info(f"🧒 Minor Eligibility: {minor_match.group(0)}")

    # Show income condition
    if income_match:
        st.info(f"💸 Income Condition: {income_match.group(0)}")

st.set_page_config(page_title="🎤📄 Scheme Info Assistant", layout="wide")

st.title("🧑‍🌾 Ask About Any Government Scheme(किसी भी सरकारी योजना के बारे में पूछें)")
st.markdown("You can *record your voice* and *upload related documents* to verify if they match scheme requirements.\n(आप अपनी आवाज़ रिकॉर्ड कर सकते हैं और संबंधित दस्तावेज़ अपलोड कर सकते हैं ताकि यह जांचा जा सके कि वे योजना की आवश्यकताओं से मेल खाते हैं या नहीं।)")

# --- 📤 Sidebar for Document Upload ---

result = ""

# --- 🎙 Audio Recording ---
text_from_mic = speech_to_text(
    start_prompt="🎙 Start Recording",
    stop_prompt="🔴 Stop Recording",
    language="en",
    use_container_width=True,
    just_once=True,
    key="mic"
)






#--- 🧠 Processing ---
if text_from_mic and text_from_mic.strip() != "":
    st.subheader("📝 Transcribed Query:")
    st.write(text_from_mic)

    st.subheader("🤖 AI Response:")
    with st.spinner("Working on your request..."):
        crew = SchemeAndDocumentCrew()

        # Pass both the scheme query and extracted document text (if any)
        result = crew.run_scheme_or_fraud_flow(
            text_from_mic
        )

        st.markdown(result)
        show_scheme_reminders(str(result)) 

with st.sidebar:
    st.sidebar.header("📄 Optional: Upload Scheme Documents(वैकल्पिक: योजना दस्तावेज़ अपलोड करें)")
uploaded_files = st.sidebar.file_uploader("Upload Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

documents_info = []

if uploaded_files:
    st.sidebar.markdown("✅ Documents received.")
    for file in uploaded_files:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)

        documents_info.append({
            "filename": file.name,
            "text": text
        })
    if result:
        show_scheme_reminders(str(result))    
        

    # Optional: Preview
    with st.expander("📜 Preview Extracted Texts"):
        for doc in documents_info:
            st.markdown(f"🗂 {doc['filename']}")
            st.text_area(label="", value=doc["text"], height=150)

        if documents_info:
            st.subheader("📁 Document Validation:")
            with st.spinner("Checking your documents for the scheme..."):
                validation_result = crew.run_document_validation_flow(
                    scheme_info=text_from_mic,  # or extract scheme name separately
                    documents_info=documents_info
                )
                st.markdown(validation_result)