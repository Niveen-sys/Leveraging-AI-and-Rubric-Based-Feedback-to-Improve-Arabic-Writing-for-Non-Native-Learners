import streamlit as st
import openai
import os
import base64
import io
from PIL import Image

# HEIC support for iPhones
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

# PDF support
try:
    import fitz  # PyMuPDF
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False

# =============================================
# RUBRICS — Pre-loaded
# =============================================
RUBRICS = {
    "2-3": "Writing Skill: 2 to 3 Years of Study. Expect basic vocabulary, present tense, and short sentences.",
    "3-4": "Writing Skill: 3 to 4 Years of Study. Expect simple sentences, personal pronouns, minimal errors.",
    "4-5": "Writing Skill: 4 to 5 Years of Study. Expect short paragraphs, past/present/future tenses, 5-6 lines.",
    "5-6": "Writing Skill: 5 to 6 Years of Study. Expect organized paragraphs, 7-9 lines, all tenses, complex vocab.",
    "6-7": "Writing Skill: 6 to 7 Years of Study. Expect 10-12 lines, many complex structures, negation.",
    "7-8": "Writing Skill: 7 to 8 Years of Study. Expect long narratives, 12-15 lines, proverbs, rich vocabulary.",
    "8-9": "Writing Skill: 8 to 9 Years of Study. Expect 3+ paragraphs, clear justifications, imperative tense, flawless spelling."
}

# =============================================
# HELPER FUNCTIONS
# =============================================
def get_rubric_by_year(year: int) -> tuple[str, str]:
    for key, rubric_text in RUBRICS.items():
        if isinstance(key, str) and "-" in key:
            try:
                start, end = key.split("-")
                if int(start.strip()) <= year <= int(end.strip()):
                    return key, rubric_text
            except ValueError:
                continue
    if year in RUBRICS: return str(year), RUBRICS[year]
    if str(year) in RUBRICS: return str(year), RUBRICS[str(year)]
    return "", ""

def get_level_note(year: int) -> str:
    if year <= 3: return "Beginner student. Focus on basic sentence structure and present tense."
    elif year <= 5: return "Elementary student. Expect simple paragraphs and basic connectives."
    elif year <= 7: return "Intermediate student. Expect coherent paragraphs and complex structures."
    else: return "Advanced student. Expect multi-paragraph writing and rich vocabulary."

def build_prompt(name: str, year: int, lo: str, sc: str, writing: str, rubric_key: str, rubric: str, word_bank: str = '') -> str:
    first_name = name.strip().split()[0] if name.strip() else name
    tip_count = 3 if year <= 4 else 5
    level_note = get_level_note(year)
    word_bank_section = f"Word Bank:\n{word_bank}\nCheck if used, suggest relevant unused words." if word_bank.strip() else "No word bank provided."

    return f"""
You are a warm, supportive Arabic teacher giving personalised feedback to a non-native student.
STUDENT PROFILE: Name: {name}, Years of Learning: {year}.
LEVEL GUIDANCE: {level_note}
LEARNING OBJECTIVE: {lo if lo.strip() else "Not provided."}
SUCCESS CRITERIA: {sc if sc.strip() else "Not provided."}
RUBRIC: {rubric}
{word_bank_section}

STUDENT WRITING:
{writing}

OUTPUT FORMAT (in Arabic/English as appropriate):
### 👋 Hello, {first_name}!
### ⭐ WWW — What Went Well: (2 specific strengths)
### 🔴 EBI — Even Better If: (1 main improvement point. Quote the error, explain what's wrong, give a hint, do NOT fix it fully)
### ✏️ Spelling Corrections: (List like: ❌ wrong → ✅ correct)
### 🏗️ Structure Advice: (1-2 sentences based on their {year} years of study)
### 🟡 Success Criteria Check: (✔ or ✖ for each criteria)
### 🟢 Top {tip_count} Tips to Improve:
### 🔵 Rubric Level: (Level, Score / 15, Why)
### 💪 Next Step: (One clear target starting with "Next time, try to...")
"""

def get_api_key() -> str:
    api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in secrets.")
    return api_key

def convert_to_pil_image(uploaded_file) -> list:
    filename = uploaded_file.name.lower()
    images = []
    if filename.endswith(".pdf"):
        if PDF_SUPPORTED:
            data = uploaded_file.read()
            doc = fitz.open(stream=data, filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
    else:
        img = Image.open(uploaded_file)
        if img.mode != "RGB": img = img.convert("RGB")
        images.append(img)
    return images

def extract_arabic_from_image_openai(uploaded_file) -> str:
    """Uses OpenAI Vision (gpt-4o) to extract Arabic text"""
    client = openai.OpenAI(api_key=get_api_key())
    images = convert_to_pil_image(uploaded_file)
    all_text = []
    
    for img in images:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "Transcribe ALL the handwritten Arabic text exactly as written, including mistakes. Return ONLY the Arabic text."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]}
            ],
            max_tokens=1500
        )
        all_text.append(response.choices[0].message.content.strip())
    return "\n".join(all_text)

def assess_with_openai(prompt: str) -> str:
    """Uses OpenAI to generate the final assessment feedback"""
    client = openai.OpenAI(api_key=get_api_key())
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    return response.choices[0].message.content

# =============================================
# STREAMLIT UI
# =============================================
st.set_page_config(page_title="مُقيِّم الكتابة العربية", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;700&display=swap');
    .stApp { background-color: #0d1a2e; color: #f0e6d3; font-family: 'Tajawal', sans-serif; }
    h1, h2, h3, h4 { color: #d4af37 !important; }
    .hero-banner { text-align: center; padding: 2rem; border-radius: 15px; background: #1a0a2e; margin-bottom: 2rem; border: 1px solid #d4af37;}
    .hero-arabic { font-size: 2.5rem; color: #d4af37; font-weight: bold;}
    .stButton > button { background: #d4af37; color: black; font-weight: bold; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-banner"><div class="hero-arabic">مُقيِّم الكتابة العربية</div><div>Arabic Writing Assessor (Powered by OpenAI GPT-4o)</div></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("🌙 Student Profile")
    name = st.text_input("Student Name")
    year = st.slider("Years of Learning Arabic", 2, 9, 5)
    rubric_key, rubric_text = get_rubric_by_year(year)
    if rubric_key:
        st.success(f"📊 Rubric applied: {rubric_key} Years of Study")
    
    st.subheader("🎯 Goals & Criteria")
    lo_text = st.text_area("Learning Objective (LO)", height=70)
    sc_text = st.text_area("Success Criteria", height=70)
    use_word_bank = st.toggle("Enable Word Bank")
    word_bank_text = st.text_area("Word Bank") if use_word_bank else ""

with col_right:
    st.subheader("✍️ Student Writing")
    writing_tab1, writing_tab2 = st.tabs(["⌨️ Type Text", "📷 Upload Photo"])
    writing = ""
    
    with writing_tab1:
        writing_typed = st.text_area("Type student's writing here", height=200)
        if writing_typed: writing = writing_typed
        
    with writing_tab2:
        writing_imgs = st.file_uploader("Upload handwriting photo", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)
        if writing_imgs:
            all_extracted = []
            with st.spinner("🔍 Reading handwritten files with GPT-4o..."):
                for img in writing_imgs:
                    st.image(img, use_column_width=True)
                    all_extracted.append(extract_arabic_from_image_openai(img))
            writing = "\n".join(all_extracted)
            st.markdown(f"**📝 Extracted text:**\n> {writing}")

    assess_btn = st.button("🔍 Assess Writing", use_container_width=True, disabled=not(name and writing and rubric_key))

if assess_btn:
    st.divider()
    with st.spinner(f"✨ Assessing {name}'s writing with OpenAI GPT-4o..."):
        try:
            prompt = build_prompt(name, year, lo_text, sc_text, writing, rubric_key, rubric_text, word_bank_text)
            result = assess_with_openai(prompt)
            st.markdown(result)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
