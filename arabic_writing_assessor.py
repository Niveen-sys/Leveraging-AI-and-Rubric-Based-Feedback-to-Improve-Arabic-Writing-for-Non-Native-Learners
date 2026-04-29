import streamlit as st
import openai
import os
import io
import base64
from PIL import Image

# HEIC support
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
# RUBRICS — Pre-loaded from PPTX
# =============================================
RUBRICS = {
    "2-3": """
Writing Skill: 2 to 3 Years of Study

PURPOSE/CONTENT:
- Beginning (1): None of the information of the task are expressed clearly.
- Developing (1.5): Few of the information of the task are expressed clearly.
- Accomplished (2): Some of the information of the task are expressed clearly.
- Advanced (2.5): Many of the information of the task are expressed clearly.
- Exemplary (3): Most of the information of the task are expressed clearly.

ORGANIZATION/COHERENCY:
- Beginning (1): Writer can write simple words with correct conjugation of letters about personal information clearly.
- Developing (1.5): Can write simple short sentence with correct conjugation of letters about personal information and basic topics.
- Accomplished (2): Can write simple short sentences (2-3 lines) with personal pronoun (I) about personal and basic topics.
- Advanced (2.5): Can write simple short sentences (3-4 lines) with personal pronouns (I and He/She).
- Exemplary (3): Can write simple short sentences (more than 4 lines) with personal pronouns (I, He, She).

VOCABULARY:
- Beginning (1): Very few basic vocabulary words (4-5) from topic learned.
- Developing (1.5): Basic vocabulary words (5-6) including 1 adjective or connective.
- Accomplished (2): Some vocabulary words including at least 2 adjectives or 2 connectives.
- Advanced (2.5): Variety of vocabulary including 2-3 adjectives, connectives, or time phrases.
- Exemplary (3): Many vocabulary words including more than 3 adjectives, connectives, or adverbs.

SENTENCE STRUCTURE:
- Beginning (1): Few simple short sentences with some ambiguity.
- Developing (1.5): Simple short sentences, clearly written, minimal ambiguity, very few errors.
- Accomplished (2): Medium sentences, clearly written, very few errors, some complex words.
- Advanced (2.5): Short paragraph (3-4 lines) about familiar topics with variety of structures (likes/dislikes), some complex words.
- Exemplary (3): Short paragraph about basic topics with variety of structures (likes/dislikes, opinions, negation, connectives).

GRAMMAR/SPELLING:
- Beginning (1): Present tense only, with spelling errors.
- Developing (1.5): Present tense with personal pronouns (I/He/She), a connective and preposition. Some spelling errors.
- Accomplished (2): Present tense with personal pronouns (I/He/She/We), connectives (1-2), prepositions (1-2). Some spelling errors.
- Advanced (2.5): Present and past tenses with personal pronouns (I/He/She/We), connectives (2-3), prepositions (2-3). Some spelling errors.
- Exemplary (3): Present and past tenses with personal pronouns (I/He/She/We), connectives (2-3), prepositions (2-3). No spelling errors.
""",

    "3-4": """
Writing Skill: 3 to 4 Years of Study

PURPOSE/CONTENT:
- Beginning (1): None of the information expressed clearly.
- Developing (1.5): Few of the information expressed clearly.
- Accomplished (2): Some of the information expressed clearly.
- Advanced (2.5): Many of the information expressed clearly.
- Exemplary (3): Most of the information expressed clearly.

ORGANIZATION/COHERENCY:
- Beginning (1): Short sentences in present tense with pronoun (I). Short phrases about personal information and basic topics.
- Developing (1.5): Short sentences in present tense with pronoun (I), 2-3 sentences, little details and organization.
- Accomplished (2): Medium sentences with personal pronouns (I/He/She), 3-4 lines, some complexity.
- Advanced (2.5): Medium sentences with personal pronouns (I/He/She), 4-5 lines, some complex words.
- Exemplary (3): Medium sentences with personal pronouns (I/He/She), 4-5 lines, complex words, coherent and organized.

VOCABULARY:
- Beginning (1): Few basic vocabulary words from the topic.
- Developing (1.5): Basic vocabulary including 1 adjective or connective.
- Accomplished (2): Vocabulary including 2 adjectives or connectives.
- Advanced (2.5): Vocabulary including 2 adjectives, connectives, or time phrases.
- Exemplary (3): Vocabulary including more than 2 adjectives, connectives, or adverbs.

SENTENCE STRUCTURE:
- Beginning (1): Simple short sentences about basic topics. Few errors.
- Developing (1.5): Simple sentences about basic topics. Very few errors.
- Accomplished (2): Simple sentences with variety of structures (likes/dislikes). Some complex words.
- Advanced (2.5): Sentences with variety of structures (likes/dislikes, opinions, negation). Some complex words.
- Exemplary (3): Sentences/short paragraph with variety of structures (likes/dislikes, opinions, negation). Some complex words.

GRAMMAR/SPELLING:
- Beginning (1): One tense only, spelling errors.
- Developing (1.5): 1 tense with 2 personal pronouns. Some spelling errors.
- Accomplished (2): 1 tense with at least 2 personal pronouns. Minimal spelling errors.
- Advanced (2.5): 2 tenses, some spelling errors.
- Exemplary (3): 2 tenses with more personal pronouns. Minimal spelling errors.
""",

    "4-5": """
Writing Skill: 4 to 5 Years of Study

PURPOSE/CONTENT:
- Beginning (1): None of the information expressed clearly.
- Developing (1.5): Few of the information expressed clearly.
- Accomplished (2): Some of the information expressed clearly.
- Advanced (2.5): Many of the information expressed clearly.
- Exemplary (3): Most of the information expressed clearly.

ORGANIZATION/COHERENCY:
- Beginning (1): Descriptive sentences in present tense, 1-2 lines, minimal details.
- Developing (1.5): Present and future tense sentences, 2-3 sentences, little details and organization.
- Accomplished (2): Present/past/future tenses, 3-4 lines, some details and organization, somewhat coherent.
- Advanced (2.5): Narrative and descriptive paragraph, 4-5 lines, mostly coherent and organized.
- Exemplary (3): Narrative and descriptive paragraph, 5-6 lines, coherent and organized well.

VOCABULARY:
- Beginning (1): 1-2 adjectives or connectives.
- Developing (1.5): 1-2 adjectives, connectives, time phrases, or adverbs.
- Accomplished (2): Some complex vocabulary including adjectives, adverbs, time phrases, or connectives.
- Advanced (2.5): Few complex vocabulary including 2-3 adjectives, adverbs, time phrases, or connectives.
- Exemplary (3): Range of complex vocabulary including 3-4 of each: adjectives, adverbs, time phrases, and connectives.

SENTENCE STRUCTURE:
- Beginning (1): Short sentences with personal information. Very few errors.
- Developing (1.5): Sentences with personal information and some variety of structures. Some complex words.
- Accomplished (2): Short paragraph (30-40 words), some complex structures and connectives, medium-long sentences.
- Advanced (2.5): Descriptive paragraph (40-50 words), complex words, variety of connectives, medium length.
- Exemplary (3): Descriptive paragraph (50-60 words), variety of complex structures, full clarity, variety of connectives.

GRAMMAR/SPELLING:
- Beginning (1): 1 tense only, many spelling errors.
- Developing (1.5): 2 tenses, some spelling errors.
- Accomplished (2): 2 tenses, minimal spelling errors.
- Advanced (2.5): 3 tenses, some spelling errors.
- Exemplary (3): 3 tenses, minimal spelling errors.
""",

    "5-6": """
Writing Skill: 5 to 6 Years of Study

PURPOSE/CONTENT:
- Beginning (1): None of the information expressed clearly.
- Developing (1.5): Few expressed clearly.
- Accomplished (2): Some expressed clearly.
- Advanced (2.5): Many expressed clearly.
- Exemplary (3): Most expressed clearly.

ORGANIZATION/COHERENCY:
- Beginning (1): 1 paragraph, 2-3 lines, minimal details. Little coherence.
- Developing (1.5): 1 paragraph, 3-5 lines, little details. Some coherence.
- Accomplished (2): 1 paragraph, 5-7 lines, some details. Somewhat coherent.
- Advanced (2.5): 1 paragraph, 6-8 lines, details. Mostly coherent and organized.
- Exemplary (3): 1 paragraph, 7-9 lines, details and organization. Coherent and organized well.

VOCABULARY:
- Beginning (1): 1-2 adjectives, adverbs, and connectives.
- Developing (1.5): Few complex vocabulary including 2 adjectives/adverbs/time phrases/connectives.
- Accomplished (2): Some complex vocabulary including 3 adjectives/adverbs/time phrases/connectives.
- Advanced (2.5): Complex vocabulary including 2-3 of each: adjectives/adverbs/time phrases/connectives.
- Exemplary (3): Wide range of complex vocabulary including 3-5 of each.

SENTENCE STRUCTURE:
- Beginning (1): Short descriptive paragraphs. Very few complex structures. 1-2 connectives.
- Developing (1.5): Descriptive paragraphs with some variety of structures. Few complex structures. 2-3 connectives.
- Accomplished (2): Few varieties of linguistic structures. Few complex structures. More than 3 connectives. Medium length. Somewhat organized.
- Advanced (2.5): Some variety of complex structures, more than 4 connectives. Medium to long text. Well organized.
- Exemplary (3): Variety of complex structures. Full clarity. More than 5 connectives. Well organized.

GRAMMAR/SPELLING:
- Beginning (1): 2 tenses only, spelling errors.
- Developing (1.5): All tenses (past/present/future), some spelling errors.
- Accomplished (2): All tenses, limited spelling errors.
- Advanced (2.5): All tenses, no spelling errors.
- Exemplary (3): All tenses, no errors, some complex verb forms.
""",

    "6-7": """
Writing Skill: 6 to 7 Years of Study

PURPOSE/CONTENT:
- Beginning (1): None of the details communicated with clarity.
- Developing (1.5): Few details communicated with clarity.
- Accomplished (2): Some details communicated with clarity.
- Advanced (2.5): Many details communicated with clarity.
- Exemplary (3): Most details communicated with clarity.

ORGANIZATION/COHERENCY:
- Beginning (1): 1 paragraph, 2-3 lines, minimal details. Little coherence.
- Developing (1.5): 1 paragraph, 4-5 lines, little details. Some coherence.
- Accomplished (2): 1 paragraph, 6-7 lines, some details. Somehow coherent.
- Advanced (2.5): 1 paragraph, 8-9 lines, details. Mostly coherent and organized.
- Exemplary (3): 1 paragraph, 10-12 lines minimum. Coherent and organized well.

VOCABULARY:
- Beginning (1): 1-2 adjectives, adverbs, and connectives.
- Developing (1.5): 1 of each: adjectives/adverbs/time phrases/connectives.
- Accomplished (2): 2 of each: adjectives/adverbs/time phrases/connectives.
- Advanced (2.5): 3-4 of each: adjectives/adverbs/time phrases/connectives.
- Exemplary (3): At least 5 of each: adjectives/adverbs/time phrases/connectives.

SENTENCE STRUCTURE:
- Beginning (1): Short paragraphs with personal info. Very few/no complex structures. Very limited connectives.
- Developing (1.5): Paragraphs with personal info, some variety of structures. Few complex structures. Minimal connectives. Not lengthy.
- Accomplished (2): Paragraphs with few varieties of linguistic structures. Few complex structures. Somehow cohesive. Some connectives. Not lengthy.
- Advanced (2.5): Paragraphs with some variety of linguistic structures. Some complex structures. Cohesive. Use of connectives. Well organized.
- Exemplary (3): Paragraphs with variety of linguistic structures. Many complex structures. Cohesive. Variety of connectives. Well organized.

GRAMMAR/SPELLING:
- Beginning (1): 2 tenses only, spelling errors.
- Developing (1.5): 2 tenses, some spelling errors.
- Accomplished (2): All tenses (past/present/future), some spelling errors.
- Advanced (2.5): All tenses plus negation, some spelling errors.
- Exemplary (3): All tenses plus negation, no spelling errors.
""",

    "7-8": """
Writing Skill: 7 to 8 Years of Study

PURPOSE/CONTENT:
- Beginning (1): None of the details communicated with clarity.
- Developing (1.5): Few details communicated with clarity.
- Accomplished (2): Some details communicated with clarity.
- Advanced (2.5): Many details communicated with clarity.
- Exemplary (3): Most details communicated with clarity.

ORGANIZATION/COHERENCY:
- Beginning (1): Short paragraph, 4-5 lines, minimal details. Little coherence.
- Developing (1.5): Short narrative text, 6-7 lines, little details. Some coherence.
- Accomplished (2): Short narrative text, 8-9 lines, some details. Somehow coherent.
- Advanced (2.5): Medium narrative text, 10-11 lines, details. Mostly coherent.
- Exemplary (3): Long narrative text, 12-15 lines minimum. Coherent and well organized.

VOCABULARY:
- Beginning (1): No complex vocabulary. Few adjectives, adverbs, and connectives.
- Developing (1.5): Few complex vocabulary including adjectives/adverbs/time phrases/connectives.
- Accomplished (2): Some complex vocabulary including adjectives/adverbs/time phrases/connectives.
- Advanced (2.5): Many complex vocabulary including adjectives/adverbs/time phrases/connectives.
- Exemplary (3): Rich complex vocabulary including adjectives/adverbs/time phrases/connectives/proverbs.

SENTENCE STRUCTURE:
- Beginning (1): Short paragraph, some linguistic structures. Very few complex structures. Very limited connectives. Not cohesive.
- Developing (1.5): Paragraph with few variety of linguistic structures. Few complex structures. Not fully cohesive. Minimal connectives.
- Accomplished (2): Paragraphs with some varieties. Some complex structures. Somehow cohesive. Use of connectives.
- Advanced (2.5): Paragraphs with some variety. Some complex structures. Cohesive. Variety of connectives. Well organized.
- Exemplary (3): Paragraphs with variety of linguistic structures. Many complex structures. Cohesive. Variety of connectives. Well organized.

GRAMMAR/SPELLING:
- Beginning (1): 2 tenses only, spelling errors that hinder clarity.
- Developing (1.5): Few tenses, with spelling errors.
- Accomplished (2): Most tenses, some spelling errors.
- Advanced (2.5): Many tenses including negation, few spelling errors.
- Exemplary (3): All tenses including negation and opinions, minimal spelling errors.
""",

    "8-9": """
Writing Skill: 8 to 9 Years of Study

PURPOSE/CONTENT:
- Beginning (1): Task not communicated. Only 1-2 pieces of information. No clarity or elaboration.
- Developing (1.5): Some parts communicated. Some information mentioned. Some clarity and expression.
- Accomplished (2): Most of the task communicated. Many information points mentioned. Partial clarity and expression.
- Advanced (2.5): Almost fully communicated. All required info except 1-2. Almost clear expression with justification.
- Exemplary (3): Fully communicated. All information mentioned. Clear expression of ideas and opinions with justification.

ORGANIZATION/COHERENCY:
- Beginning (1): Some sentences, very little details, no organization.
- Developing (1.5): 1 paragraph, little details and organization. Coherency not delivered.
- Accomplished (2): 1 narrative paragraph, some details and organization. Coherency delivered with some gaps.
- Advanced (2.5): 2 narrative paragraphs, good details and organization. Coherency almost fully delivered and sequenced.
- Exemplary (3): At least 3 narrative paragraphs, very good details and organization. Coherency fully delivered and sequenced.

VOCABULARY:
- Beginning (1): Very limited vocabulary. At least 1 each of adjective and adverb.
- Developing (1.5): Limited vocabulary. At least 2 each of adjectives and adverbs.
- Accomplished (2): Good vocabulary. At least 3 each of adjectives and adverbs/time phrases.
- Advanced (2.5): Very good vocabulary. At least 4 each of adjectives and adverbs/time phrases.
- Exemplary (3): Rich and precise vocabulary. At least 5 each of adjectives and adverbs/time phrases.

SENTENCE STRUCTURE:
- Beginning (1): Lacks linguistic structures. Only 1-2 connectives. Lots of ambiguity.
- Developing (1.5): Very limited variety of linguistic structures. No complex high frequency words. 1-2 connectives. Many errors.
- Accomplished (2): Some ability to use variety of linguistic structures. Little complex high frequency words. 1-2 connectives. Some errors.
- Advanced (2.5): Good ability to use variety of linguistic structures. Some complex high frequency words. 3+ connectives. Some errors.
- Exemplary (3): Strong ability to use variety of linguistic structures. Complex high frequency words. Variety of connectives. Few errors.

GRAMMAR/SPELLING:
- Beginning (1): One tense (present) only. Many spelling errors.
- Developing (1.5): Two tenses (present and future). Some spelling errors.
- Accomplished (2): Two tenses (present and past). Some spelling errors.
- Advanced (2.5): Three tenses (present/past/future/negation). Few spelling errors.
- Exemplary (3): Nearly all tenses (past/present/future/negation/imperative). No spelling errors.
"""
}

# =============================================
# HELPER FUNCTIONS
# =============================================

def get_rubric_by_year(year: int) -> tuple[str, str]:
    """Return (label, rubric_text) for the given years of study."""
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
    """Return level-appropriate guidance for the prompt."""
    if year <= 3: return "Beginner student. Focus on basic sentence structure and present tense."
    elif year <= 5: return "Elementary student. Expect simple paragraphs and basic connectives."
    elif year <= 7: return "Intermediate student. Expect coherent paragraphs and complex structures."
    else: return "Advanced student. Expect multi-paragraph writing and rich vocabulary."

def build_prompt(name: str, year: int, lo: str, sc: str, writing: str, rubric_key: str, rubric: str, word_bank: str = '') -> str:
    first_name = name.strip().split()[0] if name.strip() else name
    tip_count = 3 if year <= 4 else 5
    level_note = get_level_note(year)
    word_bank_section = f"""The teacher has provided a word bank: {word_bank}. 
Check if used, and suggest relevant unused words.""" if word_bank.strip() else "No word bank provided."

    return f"""
You are a warm, supportive Arabic teacher giving personalised feedback.
STUDENT PROFILE: Name: {name}, Years of Learning: {year}.
LEVEL GUIDANCE: {level_note}
LEARNING OBJECTIVE: {lo if lo.strip() else "Not provided."}
SUCCESS CRITERIA: {sc if sc.strip() else "Not provided."}
RUBRIC: {rubric}
WORD BANK: {word_bank_section}

STUDENT WRITING:
{writing}

OUTPUT FORMAT:
### 👋 Hello, {first_name}!
### ⭐ WWW — What Went Well: (2 specific strengths)
### 🔴 EBI — Even Better If: (1 main improvement point. Quote error, give hint. Do NOT rewrite)
### ✏️ Spelling Corrections: (❌ wrong → ✅ correct)
### 🏗️ Structure Advice: (1-2 sentences)
### 🟡 Success Criteria Check: (✔ or ✖)
### 🟢 Top {tip_count} Tips to Improve:
### 🔵 Rubric Level: (Level, Score / 15, Why)
### 💪 Next Step: (One clear target starting with "Next time, try to...")
"""

def get_api_key() -> str:
    """Retrieve OpenAI API key."""
    api_key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key: raise ValueError("OPENAI_API_KEY not found in secrets.")
    return api_key

def convert_to_pil_image(uploaded_file) -> list:
    """Convert any uploaded file to PIL Images."""
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
    """Use OpenAI Vision to extract Arabic text."""
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
                    {"type": "text", "text": "Transcribe ALL handwritten Arabic text exactly as written. Return ONLY the Arabic text."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]}
            ],
            max_tokens=1500
        )
        all_text.append(response.choices[0].message.content.strip())
    return "\n".join(all_text)

def assess_with_openai(prompt: str) -> str:
    """Generate final feedback using OpenAI."""
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
    .stApp { background: linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 40%, #0d1a2e 100%); color: #f0e6d3; font-family: 'Tajawal', sans-serif; }
    h1, h2, h3, h4 { color: #d4af37 !important; }
    .hero-banner { text-align: center; padding: 2.5rem; border-radius: 20px; background: #1a0a2e; margin-bottom: 2rem; border: 1px solid rgba(212,175,55,0.4); box-shadow: 0 10px 30px rgba(0,0,0,0.5);}
    .hero-arabic { font-size: 2.8rem; color: #d4af37; font-weight: bold; }
    .stButton > button { background: linear-gradient(145deg, #d4af37, #b8941f) !important; color: #0d0d1a !important; font-weight: bold !important; border-radius: 12px !important; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #d4af37; margin-bottom: 1rem; }
    .feedback-box { background: rgba(26,10,46,0.9); border: 1px solid rgba(212,175,55,0.35); border-radius: 16px; padding: 2rem; margin-top: 1.5rem; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-banner"><div class="hero-arabic">مُقيِّم الكتابة العربية</div><div>Arabic Writing Assessor (Powered by OpenAI)</div></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-title">🌙 Student Profile</div>', unsafe_allow_html=True)
    name = st.text_input("Student Name")
    year = st.slider("Years of Learning Arabic", 2, 9, 5)
    rubric_key, rubric_text = get_rubric_by_year(year)
    if rubric_key: st.success(f"📊 Rubric applied: {rubric_key} Years of Study")

    st.markdown('<div class="section-title">🎯 Goals & Criteria</div>', unsafe_allow_html=True)
    lo_text = st.text_area("Learning Objective (LO)", height=70)
    sc_text = st.text_area("Success Criteria", height=70)
    use_word_bank = st.toggle("Enable Word Bank")
    word_bank_text = st.text_area("Word Bank (comma-separated)") if use_word_bank else ""

with col_right:
    st.markdown('<div class="section-title">✍️ Student Writing</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
            st.markdown(result)
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("⬇️ Download Feedback", data=result, file_name=f"feedback_{name}.txt", mime="text/plain")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
