import streamlit as st
from groq import Groq
import google.generativeai as genai
import os
import base64
import io
from PIL import Image
import pytesseract

# HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

# PDF support
try:
    import fitz
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False

# =============================================
# RUBRICS
# =============================================
RUBRICS = {
    "2-3": """PURPOSE/CONTENT: Beginning (1), Developing (1.5), Accomplished (2), Advanced (2.5), Exemplary (3)
ORGANIZATION: Simple words → simple short sentences (2-3 lines) → sentences with pronouns (3-4 lines)
VOCABULARY: 4-5 basic words → includes 1-2 adjectives/connectives → more adjectives/connectives
SENTENCE STRUCTURE: Few simple short sentences → simple sentences clearly written → medium sentences with variety
GRAMMAR/SPELLING: Present tense only with errors → present tense with pronouns + connectives + some errors → minimal errors""",

    "3-4": """PURPOSE/CONTENT: None → Few clear → Some clear → Many clear → Most clear
ORGANIZATION: Short sentences present tense → 2-3 sentences with little details → 3-4 lines with complexity
VOCABULARY: Few basic → 1 adjective/connective → 2 adjectives/connectives → variety
SENTENCE STRUCTURE: Simple about basic topics → variety of structures → likes/dislikes/opinions
GRAMMAR/SPELLING: One tense only → 1 tense with pronouns + some errors → 2 tenses with minimal errors""",

    "4-5": """PURPOSE/CONTENT: None → Few → Some → Many → Most expressed clearly
ORGANIZATION: Descriptive sentences 1-2 lines → 2-3 sentences little details → 3-4 lines some details → 4-5 lines mostly coherent → 5-6 lines coherent
VOCABULARY: 1-2 adjectives → includes time phrases → some complex vocabulary → few complex → wide range
SENTENCE STRUCTURE: Short sentences personal info → variety with some complex → 30-40 words paragraph → 40-50 words → 50-60 words
GRAMMAR/SPELLING: 1 tense many errors → 2 tenses some errors → 2 tenses minimal errors → 3 tenses some errors → 3 tenses minimal""",

    "5-6": """PURPOSE/CONTENT: None → Few → Some → Many → Most expressed clearly
ORGANIZATION: 1 paragraph 2-3 lines minimal → 3-5 lines little details → 5-7 lines somewhat coherent → 6-8 lines mostly coherent → 7-9 lines coherent
VOCABULARY: 1-2 adjectives/adverbs/connectives → 2 of each → 3 of each → 2-3 of each → 3-5 of each
SENTENCE STRUCTURE: Short descriptive → some variety few complex → few varieties some complex → some variety some complex → variety of complex structures
GRAMMAR/SPELLING: 2 tenses → all tenses some errors → all tenses limited errors → all tenses no errors → all tenses with complex forms""",

    "6-7": """PURPOSE/CONTENT: None → Few → Some → Many → Most expressed clearly
ORGANIZATION: 1 paragraph 2-3 lines minimal → 4-5 lines little details → 6-7 lines somewhat coherent → 8-9 lines mostly coherent → 10-12+ lines coherent
VOCABULARY: 1-2 adj/adv/conn → 1 of each → 2 of each → 3-4 of each → 5+ of each
SENTENCE STRUCTURE: Very few complex structures → few complex structures → few varieties some complex → some variety some complex → variety of complex structures
GRAMMAR/SPELLING: 2 tenses → 2 tenses some errors → all tenses some errors → all tenses + negation some errors → all tenses + negation no errors""",

    "7-8": """PURPOSE/CONTENT: None → Few → Some → Many → Most expressed clearly
ORGANIZATION: Short paragraph 4-5 lines minimal → 6-7 lines little details → 8-9 lines somewhat coherent → 10-11 lines mostly coherent → 12-15+ lines coherent
VOCABULARY: No complex few adj/adv → few complex → some complex → many complex → rich complex vocabulary
SENTENCE STRUCTURE: Some structures very few complex → few variety few complex → some varieties some complex → some variety some complex → variety of linguistic structures
GRAMMAR/SPELLING: 2 tenses → few tenses → most tenses → many tenses + negation → all tenses + negation minimal""",

    "8-9": """PURPOSE/CONTENT: Not communicated → Some parts → Most communicated → Almost fully → Fully communicated
ORGANIZATION: Some sentences no organization → 1 paragraph little details → 1 narrative paragraph → 2 paragraphs → 3+ paragraphs
VOCABULARY: Very limited → Limited → Good → Very good → Rich and precise
SENTENCE STRUCTURE: Lacks structures only 1-2 connectives → very limited variety → some variety little complex → good variety some complex → strong variety complex structures
GRAMMAR/SPELLING: One tense many errors → two tenses some errors → two tenses some errors → three tenses few errors → nearly all tenses no errors"""
}

# =============================================
# API KEYS
# =============================================
def get_groq_api_key() -> str:
    """Get Groq API key."""
    api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found")
    return api_key

def get_google_api_key() -> str:
    """Get Google API key for Vision."""
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found")
    return api_key

# =============================================
# OCR & TEXT EXTRACTION
# =============================================
def extract_text_from_image(uploaded_file) -> str:
    """Extract text using Google Gemini Vision (best for Arabic)."""
    try:
        api_key = get_google_api_key()
        genai.configure(api_key=api_key)
        
        # Read file
        if uploaded_file.name.lower().endswith(".pdf") and PDF_SUPPORTED:
            data = uploaded_file.read()
            doc = fitz.open(stream=data, filetype="pdf")
            all_text = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Send to Gemini Vision
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content([
                    "Extract ALL Arabic and English text from this image. Do NOT correct or modify anything. Return ONLY the text.",
                    img
                ])
                if response.text:
                    all_text.append(response.text.strip())
            return "\n".join(all_text)
        else:
            img = Image.open(uploaded_file)
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Send to Gemini Vision
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([
                "Extract ALL Arabic and English text from this image. Do NOT correct or modify anything. Return ONLY the text.",
                img
            ])
            return response.text.strip() if response.text else ""
    except Exception as e:
        st.warning(f"⚠️ OCR failed: {str(e)[:100]}... Trying fallback...")
        try:
            img = Image.open(uploaded_file)
            text = pytesseract.image_to_string(img, lang="eng+ara")
            return text.strip()
        except Exception:
            return ""

# =============================================
# PROMPT BUILDER
# =============================================
def get_level_note(year: int) -> str:
    """Level-appropriate guidance."""
    if year <= 3:
        return "Beginner: Focus on basic structure, simple vocabulary, present tense. Very encouraging."
    elif year <= 5:
        return "Elementary: Expect simple paragraphs, 2-3 tenses, basic connectives. Encourage growth."
    elif year <= 7:
        return "Intermediate: Expect coherent paragraphs, variety of tenses, connectives, some complexity."
    else:
        return "Advanced: Expect multi-paragraph, rich vocabulary, all tenses, complex structures, strong coherence."

def build_prompt(name: str, year: int, lo: str, sc: str, writing: str, rubric_key: str, rubric: str, word_bank: str = '') -> str:
    first_name = name.strip().split()[0] if name.strip() else name
    tip_count = 3 if year <= 4 else 4
    
    common_mistakes = f"""
WATCH FOR COMMON ARABIC L2 MISTAKES (mention in 'Improve This' if present):
- Adjective BEFORE noun (wrong order): "أحمر كتاب" instead of "كتاب أحمر"
- Gender mismatch: adjective/verb not matching noun gender (كتاب أحمراء, هي يكتب)
- Verb conjugation wrong: verb not matching subject (أنا تكتب, هو يكتبون)
- Missing pronoun suffixes: "رأي" instead of "رأيته" (saw him)
- Wrong case after prepositions: "في البيتْ" instead of "في البيت"
If you see these patterns, mention specifically: "E.g., you wrote 'X' but should be 'Y'"
"""

    word_bank_section = ""
    if word_bank.strip():
        word_bank_section = f"\nWORD BANK: {word_bank}\n- Praise words they used | Suggest 2-3 unused words that fit | Add to report: ### 📚 Word Bank — ✅ Used: [...] | 💡 Try: [...]"

    return f"""You are a warm, supportive Arabic teacher. Give concise, specific feedback.

STUDENT: {first_name} ({year} years) | Level: {get_level_note(year)}
LO: {lo if lo.strip() else "Not provided"}
SC: {sc if sc.strip() else "Not provided"}
RUBRIC: {rubric}
{common_mistakes}
{word_bank_section}

WRITING: {writing}

SPELLING RULE: Only flag words you are 100% certain are misspelled. Never flag correct Arabic words.

OUTPUT (concise, specific, no padding):

### 👋 {first_name}
One warm sentence about their writing.

### ⭐ What Went Well
- **Strength 1:** (specific)
- **Strength 2:** (specific)

### 🔴 Improve This
> Quote: "exact quote"
> Issue: [category]
> Hint: guide without full answer

### ✏️ Spelling
Only real errors: ❌ wrong → ✅ correct
Or: ✅ No spelling errors.

### 📐 Grammar & Common Mistakes
1-2 points only if present. (Adjective order, gender agreement, verb conjugation, etc.)

{"### 📚 Word Bank" if word_bank.strip() else ""}
{"✅ Used: [...] | 💡 Try: [...]" if word_bank.strip() else ""}

### 🟢 Top {tip_count} Tips
1.
2.
3.
{"4." if tip_count == 4 else ""}

### 🔵 Rubric Score
| Category | Level | /3 |
|---|---|---|
| Purpose/Content | | |
| Organization | | |
| Vocabulary | | |
| Structure | | |
| Grammar/Spelling | | |
| **TOTAL** | | **/15** |

### 💪 Next Step
"Next time, try to..." — one sentence only.
"""

def assess_with_groq(prompt: str) -> str:
    """Call Groq for assessment."""
    api_key = get_groq_api_key()
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    return response.choices[0].message.content

# =============================================
# SHARING FUNCTIONS
# =============================================
def share_to_teams(student_name: str, report: str, teams_webhook: str) -> bool:
    """Send to Teams."""
    try:
        import requests
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"Arabic Writing Assessment - {student_name}",
            "themeColor": "d4af37",
            "title": f"📝 {student_name}",
            "sections": [{"activityTitle": "مُقيِّم الكتابة العربية", "text": report[:3000]}]
        }
        response = requests.post(teams_webhook, json=message, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Teams error: {str(e)[:100]}")
        return False

def share_to_email(student_name: str, teacher_email: str, student_email: str, report: str) -> bool:
    """Send email."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_server = st.secrets.get("SMTP_SERVER", "")
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        sender_email = st.secrets.get("SENDER_EMAIL", "")
        sender_password = st.secrets.get("SENDER_PASSWORD", "")
        
        if not all([smtp_server, sender_email, sender_password]):
            st.error("Email not configured. Add SMTP settings to secrets.")
            return False
        
        msg = MIMEMultipart()
        msg["Subject"] = f"🌙 Arabic Assessment - {student_name}"
        msg["From"] = sender_email
        msg["To"] = teacher_email
        
        html = f"""<html><body style="font-family:Tajawal;color:#333;">
<h2 style="color:#d4af37;">مُقيِّم الكتابة العربية</h2>
<pre style="white-space:pre-wrap;background:#f5f5f5;padding:1rem;border-radius:8px;">{report}</pre>
</body></html>"""
        msg.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            recipients = [teacher_email]
            if student_email:
                recipients.append(student_email)
            server.sendmail(sender_email, recipients, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email error: {str(e)[:100]}")
        return False

# =============================================
# STREAMLIT UI
# =============================================
st.set_page_config(page_title="مُقيِّم الكتابة العربية", page_icon="🌙", layout="wide")

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 40%, #0d1a2e 100%);min-height:100vh;}
.hero-banner {background:linear-gradient(135deg,#1a0a2e,#2d1554);border:2px solid rgba(212,175,55,0.5);border-radius:24px;padding:2rem;margin-bottom:2rem;text-align:center;}
.hero-arabic {font-size:2.5rem;color:#d4af37;font-weight:700;margin:0.5rem 0;}
.hero-english {font-size:1rem;color:rgba(212,175,55,0.85);letter-spacing:2px;}
.section-title {font-size:1.1rem;font-weight:700;color:#d4af37;margin-bottom:1rem;letter-spacing:0.5px;}
.section-card {background:rgba(255,255,255,0.05);border:1px solid rgba(212,175,55,0.25);border-radius:16px;padding:1.5rem;margin-bottom:1rem;}
.report-container {background:linear-gradient(145deg,#0f0f1f,#1a0a2e);border:2px solid rgba(212,175,55,0.5);border-radius:24px;padding:2.5rem;margin:1.5rem 0;box-shadow:0 20px 60px rgba(0,0,0,0.6);}
.report-container h3 {color:#ffffff;background:linear-gradient(135deg,rgba(212,175,55,0.2),rgba(212,175,55,0.05));border-left:4px solid #d4af37;border-radius:8px;padding:0.6rem 1rem;margin-top:1.5rem;}
.report-container p,.report-container li {color:rgba(230,220,210,0.95);line-height:1.8;}
.report-container strong {color:#d4af37;font-weight:700;}
.report-container table {width:100%;border-collapse:collapse;margin:1rem 0;}
.report-container th {background:rgba(212,175,55,0.2);color:#d4af37;padding:0.6rem;border:1px solid rgba(212,175,55,0.3);}
.report-container td {padding:0.5rem;border:1px solid rgba(212,175,55,0.15);color:rgba(230,220,210,0.9);}
.stTabs [data-baseweb="tab-list"] {background:rgba(255,255,255,0.03);border:1px solid rgba(212,175,55,0.2);border-radius:12px;padding:4px;}
.stTabs [aria-selected="true"] {background:linear-gradient(135deg,rgba(212,175,55,0.25),rgba(212,175,55,0.1));color:#d4af37;}
.stButton > button {background:linear-gradient(145deg,#d4af37,#b8941f);color:#0d0d1a;font-weight:900;border-radius:12px;transition:all 0.15s;text-transform:uppercase;}
.stButton > button:hover {background:linear-gradient(145deg,#e8c84a,#d4af37);transform:translateY(2px);}
</style>
""", unsafe_allow_html=True)

# Hero
st.markdown("""
<div class="hero-banner">
    <div class="hero-arabic">مُقيِّم الكتابة العربية</div>
    <div class="hero-english">Arabic Writing Assessor</div>
    <div style="color:rgba(200,200,255,0.6);font-size:0.9rem;margin-top:0.5rem;">✦ Smart Feedback for Non-Native Learners ✦</div>
</div>
""", unsafe_allow_html=True)

# ── MAIN TABS ──
main_tab1, main_tab2, main_tab3 = st.tabs(["📋 Student Info & Context", "✍️ Student Writing", "📊 Assessment & Share"])

# ==================== TAB 1: STUDENT INFO & CONTEXT ====================
with main_tab1:
    st.markdown('<div class="section-title">🌙 Student Profile</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        name = st.text_input("Student Name", placeholder="e.g. Sara Ahmed")
    with col2:
        year = st.slider("Years of Learning Arabic", 2, 9, 5)
    
    rubric_key, rubric_text = next(((k, v) for k, v in RUBRICS.items() if "-" in k and int(k.split("-")[0]) <= year <= int(k.split("-")[1])), ("", ""))
    
    if rubric_key:
        st.markdown(f'<div class="section-card">📊 **Rubric:** {rubric_key} Years of Study</div>', unsafe_allow_html=True)
    else:
        st.error("No rubric found for this year.")
    
    st.divider()
    
    # Context Tabs
    context_tab1, context_tab2, context_tab3 = st.tabs(["🎯 Learning Objective", "✅ Success Criteria", "📚 Word Bank (Optional)"])
    
    with context_tab1:
        st.markdown('<div class="section-title">🎯 Learning Objective (LO)</div>', unsafe_allow_html=True)
        lo_text = st.text_area("Type or paste LO", height=80, placeholder="e.g. Write a paragraph about daily routine using past tense.", key="lo_text")
        lo_file = st.file_uploader("Or upload image/PDF", type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf"], key="lo_file")
        if lo_file:
            with st.spinner("Reading LO..."):
                extracted = extract_text_from_image(lo_file)
                if extracted:
                    lo_text = extracted
                    st.success("✅ LO extracted")
                    st.caption(extracted[:150])
                else:
                    st.warning("⚠️ Could not extract. Try a clearer image.")
    
    with context_tab2:
        st.markdown('<div class="section-title">✅ Success Criteria</div>', unsafe_allow_html=True)
        sc_text = st.text_area("Type or paste Success Criteria", height=80, placeholder="e.g. Uses 3 connectives, 6-8 lines, past and present tense.", key="sc_text")
        sc_file = st.file_uploader("Or upload image/PDF", type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf"], key="sc_file")
        if sc_file:
            with st.spinner("Reading Success Criteria..."):
                extracted = extract_text_from_image(sc_file)
                if extracted:
                    sc_text = extracted
                    st.success("✅ Success Criteria extracted")
                    st.caption(extracted[:150])
                else:
                    st.warning("⚠️ Could not extract. Try a clearer image.")
    
    with context_tab3:
        st.markdown('<div class="section-title">📚 Word Bank</div>', unsafe_allow_html=True)
        use_word_bank = st.toggle("Enable Word Bank", value=False)
        word_bank_text = ""
        if use_word_bank:
            word_bank_text = st.text_area("Type or paste words (one per line)", height=100, placeholder="e.g. بالإضافة إلى، على الرغم من، لذلك", key="wb_text")
            wb_file = st.file_uploader("Or upload image/PDF/CSV/TXT", type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf","csv","txt"], key="wb_file")
            if wb_file:
                fname = wb_file.name.lower()
                if fname.endswith((".csv", ".txt")):
                    try:
                        import pandas as pd
                        from io import StringIO
                        content = wb_file.read().decode("utf-8")
                        try:
                            wb_df = pd.read_csv(StringIO(content))
                            word_bank_text = "\n".join(wb_df.iloc[:, 0].dropna().astype(str).tolist())
                        except:
                            word_bank_text = content
                        st.success("✅ Word bank loaded")
                    except Exception as e:
                        st.error(f"Error: {str(e)[:100]}")
                else:
                    with st.spinner("Reading word bank..."):
                        extracted = extract_text_from_image(wb_file)
                        if extracted:
                            word_bank_text = extracted
                            st.success("✅ Word bank extracted")
                            st.caption(extracted[:150])
                        else:
                            st.warning("⚠️ Could not extract.")

# ==================== TAB 2: STUDENT WRITING ====================
with main_tab2:
    st.markdown('<div class="section-title">✍️ Student Writing</div>', unsafe_allow_html=True)
    
    writing_tab1, writing_tab2 = st.tabs(["⌨️ Type / Paste", "📷 Upload Photo/PDF"])
    
    writing = ""
    
    with writing_tab1:
        writing_typed = st.text_area("Paste or type student writing", height=300, placeholder="اكتب هنا...", key="writing_typed")
        if writing_typed.strip():
            writing = writing_typed
    
    with writing_tab2:
        st.caption("📱 JPG, PNG, HEIC, PDF — single or multiple files")
        writing_imgs = st.file_uploader("Upload photo(s) or PDF", type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf"], key="writing_img", accept_multiple_files=True)
        if writing_imgs:
            all_extracted = []
            for i, f in enumerate(writing_imgs):
                st.image(f, caption=f"Page {i+1}: {f.name}", use_column_width=True)
            
            with st.spinner(f"🔍 Reading {len(writing_imgs)} file(s)..."):
                for i, f in enumerate(writing_imgs):
                    try:
                        extracted = extract_text_from_image(f)
                        if extracted:
                            all_extracted.append(extracted)
                            st.success(f"✅ File {i+1} read")
                        else:
                            st.warning(f"⚠️ File {i+1}: no text found — try a clearer photo.")
                    except Exception as e:
                        st.error(f"❌ File {i+1}: {str(e)[:100]}")
            
            if all_extracted:
                writing = "\n".join(all_extracted)
                st.markdown("**📝 Extracted text:**")
                st.caption(writing[:300])
    
    if writing.strip():
        st.caption(f"📊 ~{len(writing.split())} words")

# ==================== TAB 3: ASSESSMENT & SHARE ====================
with main_tab3:
    st.markdown('<div class="section-title">🔍 Assess & Share</div>', unsafe_allow_html=True)
    
    assess_btn = st.button(
        "🔍 Assess Writing",
        type="primary",
        use_container_width=True,
        disabled=not (name.strip() and writing.strip() and rubric_key)
    )
    
    if not name.strip():
        st.info("⚠️ Enter student name")
    if not writing.strip():
        st.info("⚠️ Provide student writing")
    if not rubric_key:
        st.info("⚠️ Select valid year of study")
    
    if assess_btn:
        with st.spinner(f"✨ Assessing {name.strip().split()[0]}'s writing..."):
            try:
                prompt = build_prompt(
                    name=name.strip(),
                    year=year,
                    lo=lo_text.strip() if 'lo_text' in locals() else "",
                    sc=sc_text.strip() if 'sc_text' in locals() else "",
                    writing=writing.strip(),
                    rubric_key=rubric_key,
                    rubric=rubric_text,
                    word_bank=word_bank_text.strip() if use_word_bank and 'word_bank_text' in locals() else ""
                )
                result = assess_with_groq(prompt)
                
                # Display Report
                st.markdown('<div class="report-container">', unsafe_allow_html=True)
                st.markdown(result)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.divider()
                st.markdown('<div class="section-title">📤 Share Report</div>', unsafe_allow_html=True)
                
                share_col1, share_col2, share_col3 = st.columns(3)
                
                with share_col1:
                    st.download_button(
                        "⬇️ Download .txt",
                        data=result,
                        file_name=f"feedback_{name.strip().replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with share_col2:
                    if st.button("💬 Teams", use_container_width=True):
                        teams_webhook = st.secrets.get("TEAMS_WEBHOOK", "")
                        if teams_webhook:
                            with st.spinner("Sending to Teams..."):
                                if share_to_teams(name.strip(), result, teams_webhook):
                                    st.success("✅ Sent to Teams!")
                                else:
                                    st.error("❌ Failed")
                        else:
                            st.info("⚠️ Teams not configured")
                
                with share_col3:
                    if st.button("📧 Email", use_container_width=True):
                        st.markdown('<div class="section-card">', unsafe_allow_html=True)
                        teacher_email = st.text_input("Your email", placeholder="teacher@example.com", key="t_email")
                        student_email = st.text_input("Student email (optional)", placeholder="student@example.com", key="s_email")
                        
                        if st.button("Send", use_container_width=True, key="send_email"):
                            if teacher_email:
                                with st.spinner("Sending..."):
                                    if share_to_email(name.strip(), teacher_email, student_email, result):
                                        st.success("✅ Sent!")
                                    else:
                                        st.error("❌ Failed")
                            else:
                                st.warning("Enter your email")
                        st.markdown('</div>', unsafe_allow_html=True)
            
            except ValueError as e:
                if "GOOGLE_API_KEY" in str(e):
                    st.error("❌ Google API key missing. Add GOOGLE_API_KEY to secrets.")
                elif "GROQ_API_KEY" in str(e):
                    st.error("❌ Groq API key missing. Add GROQ_API_KEY to secrets.")
                else:
                    st.error(f"❌ Error: {str(e)[:150]}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)[:150]}")
