import streamlit as st
import requests as _requests
from groq import Groq
import os
import io
import base64
import hashlib
import time
from datetime import datetime, date
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
    """
    Return (label, rubric_text) for the given years of study.
    Supports three key formats in RUBRICS:
      1. String range  e.g. "2-3", "3-4"  (PPTX-loaded rubrics)
      2. Integer       e.g. 2, 3, 4        (simple rubric dict)
      3. String int    e.g. "2", "3"        (JSON-loaded rubrics)
    """
    # Pass 1: string range keys e.g. "2-3"
    for key, rubric_text in RUBRICS.items():
        if isinstance(key, str) and "-" in key:
            try:
                start, end = key.split("-")
                if int(start.strip()) <= year <= int(end.strip()):
                    return key, rubric_text
            except ValueError:
                continue

    # Pass 2: exact integer key e.g. 5
    if year in RUBRICS:
        return str(year), RUBRICS[year]

    # Pass 3: exact string-integer key e.g. "5"
    if str(year) in RUBRICS:
        return str(year), RUBRICS[str(year)]

    # Pass 4: closest integer key (fallback)
    int_keys = [k for k in RUBRICS if isinstance(k, int)]
    if int_keys:
        closest = min(int_keys, key=lambda k: abs(k - year))
        return str(closest), RUBRICS[closest]

    return "", ""


def extract_text_from_image(uploaded_file) -> str:
    """Extract Arabic/English text from an uploaded image using OCR."""
    try:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img, lang="eng+ara")
        return text.strip()
    except Exception:
        return ""


def get_level_note(year: int) -> str:
    """Return level-appropriate guidance for the prompt."""
    if year <= 3:
        return "This is a beginner student. Focus on basic sentence structure, simple vocabulary, and present tense. Keep expectations simple and very encouraging."
    elif year <= 5:
        return "This is an elementary student. Expect simple paragraphs, 2-3 tenses, and basic connectives. Encourage growth in vocabulary and sentence variety."
    elif year <= 7:
        return "This is an intermediate student. Expect coherent paragraphs, variety of tenses, connectives, and some complex structures."
    else:
        return "This is an advanced student. Expect multi-paragraph writing, rich vocabulary, all tenses, complex structures, and strong coherence."


def build_prompt(name: str, year: int, lo: str, sc: str, writing: str, rubric_key: str, rubric: str, word_bank: str = '') -> str:
    first_name = name.strip().split()[0] if name.strip() else name
    tip_count = 3 if year <= 4 else 5
    level_note = get_level_note(year)
    word_bank_section = f"""The teacher has provided a word bank of vocabulary to encourage. 
Use these words as reference when giving vocabulary advice and suggestions:
{word_bank}

When giving feedback:
- Check if the student used any of these words — praise them if they did
- Suggest 2-3 relevant unused words from this list that would improve their writing
- Add a section: ### 📚 Word Bank Suggestions — showing which words to try next time""" if word_bank.strip() else "No word bank provided — skip the Word Bank Suggestions section."

    return f"""
You are a warm, supportive Arabic teacher giving personalised feedback to a non-native student.

STUDENT PROFILE:
- Name: {name}
- First name: {first_name}
- Years of Learning Arabic: {year} (Rubric level: {rubric_key} years)

LEVEL GUIDANCE:
{level_note}

LEARNING OBJECTIVE (LO):
{lo if lo.strip() else "Not provided."}

SUCCESS CRITERIA:
{sc if sc.strip() else "Not provided."}

RUBRIC ({rubric_key} years of study):
{rubric}

WORD BANK / VOCABULARY LIST (OPTIONAL — only if provided):
{word_bank_section}

STUDENT WRITING:
{writing}

───────────────────────────────────────────
OUTPUT FORMAT (follow exactly — use these headings and emojis):

### 👋 Hello, {first_name}!
Start with one warm, personalised sentence using the student's name that references something specific and positive from their actual writing.
Example style: "Well done, {first_name}, you did a great job using..."

---

### ⭐ WWW — What Went Well:
Give exactly TWO clear strengths. Be specific — refer directly to the student's writing.
Use {first_name}'s name naturally at least once here.

- **Strength 1:** ...
- **Strength 2:** ...

---

### 🔴 EBI — Even Better If:
Give exactly ONE main improvement point. Keep it achievable and kind.
Do NOT list everything — pick the single most important issue.

> **Quote:** "exact text from student writing"
> **Category:** Grammar / Spelling / Vocabulary / Sentence Structure
> **What's wrong:** (1 sentence, plain language)
> **Hint:** Guide {first_name} toward the fix — do NOT rewrite or give the full answer

---

### ✏️ Spelling Corrections:
List spelling mistakes found in the writing using this format only:
- ❌ wrong word → ✅ correct word

(If no spelling errors, write: "Great job — no spelling errors found! 🎉")

---

### 🏗️ Structure Advice:
Give 1-2 sentences of structure advice adapted to {first_name}'s level ({year} years of study).
Base this on the rubric expectations for this level.

---

### 🟡 Success Criteria Check:
(Only include if Success Criteria were provided — otherwise skip this section entirely)
- ✔ [Criterion] — briefly explain why it's met
- ✖ [Criterion] — briefly explain why it's not yet met

---

### 🟢 Top {tip_count} Tips to Improve:
Actionable tips specific to {first_name}'s actual writing — no generic advice.
1.
2.
3.
{"4.\n5." if tip_count == 5 else ""}

---

### 🔵 Rubric Level:
- **Level:** Beginning / Developing / Accomplished / Advanced / Exemplary
- **Score estimate:** X / 15
- **Why:** 2-3 sentences tied directly to the rubric for {rubric_key} years of study.

---

### 💪 Next Step:
End with one clear, simple target sentence starting with:
"Next time, try to..."
Then close with one warm motivational line addressed to {first_name}.

───────────────────────────────────────────
STRICT RULES — NEVER BREAK THESE:
- NEVER rewrite the student's full text
- NEVER provide fully corrected sentences
- Use {first_name}'s name naturally — not in every sentence, but enough to feel personal
- Keep tone encouraging, honest, and simple
- Adapt all expectations to the student's level ({year} years of study)
- DO NOT give generic advice — tie everything to the student's actual writing
"""


# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY   = "gsk_DummyReplaceWithYourRealKey"   # ← Groq key (assessment)
GOOGLE_API_KEY = "AIzaDummyReplaceWithYourRealKey"   # ← Google key (OCR only)
# ──────────────────────────────────────────────────────────────────────────────

def get_google_api_key() -> str:
    """Return Google API key for OCR — secrets → env → hardcoded."""
    return (
        _secret("GOOGLE_API_KEY")
        or os.environ.get("GOOGLE_API_KEY", "")
        or GOOGLE_API_KEY
    )

def get_groq_api_key() -> str:
    """Return Groq API key (hardcoded, then env/secrets as fallback)."""
    return (
        GROQ_API_KEY
        or os.environ.get("GROQ_API_KEY", "")
        or _secret("GROQ_API_KEY")
    )

def _secret(key: str) -> str:
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
# CACHE & RATE LIMITER
# ══════════════════════════════════════════════════════════════

# Daily usage limits (well below free tier maximums)
MAX_OCR_PER_DAY    = 1500  # Google Gemini 2.0 Flash free tier max/day
MAX_ASSESS_PER_DAY = 1500  # Google Gemini 2.0 Flash free tier max/day
RATE_LIMIT_WINDOW  = 60    # seconds
MAX_CALLS_PER_MIN  = 14    # Google allows 15/min — 1 below for safety


def _get_usage() -> dict:
    """Get today's usage counters from session state."""
    today = str(date.today())
    if "usage" not in st.session_state or st.session_state["usage"].get("date") != today:
        st.session_state["usage"] = {"date": today, "ocr": 0, "assess": 0}
    return st.session_state["usage"]


def _increment_usage(kind: str):
    """Increment usage counter (kind = 'ocr' or 'assess')."""
    usage = _get_usage()
    usage[kind] = usage.get(kind, 0) + 1


def _check_limit(kind: str):
    """Raise error if daily limit exceeded."""
    usage = _get_usage()
    limit = MAX_OCR_PER_DAY if kind == "ocr" else MAX_ASSESS_PER_DAY
    count = usage.get(kind, 0)
    if count >= limit:
        raise RuntimeError(
            f"⛔ Daily limit reached ({count}/{limit}). Resets tomorrow at midnight."
        )


def _rate_limit():
    """Enforce rate limiting across all API calls."""
    if "rate_calls" not in st.session_state:
        st.session_state["rate_calls"] = []
    now = time.time()
    # Keep only calls within the last window
    st.session_state["rate_calls"] = [
        t for t in st.session_state["rate_calls"]
        if now - t < RATE_LIMIT_WINDOW
    ]
    if len(st.session_state["rate_calls"]) >= MAX_CALLS_PER_MIN:
        wait = RATE_LIMIT_WINDOW - (now - st.session_state["rate_calls"][0])
        raise RuntimeError(
            f"⏳ Too many requests. Please wait {int(wait)+1} seconds and try again."
        )
    st.session_state["rate_calls"].append(now)


def _image_hash(uploaded_file) -> str:
    """Generate a stable hash for an uploaded file (for caching)."""
    uploaded_file.seek(0)
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return hashlib.md5(data).hexdigest()


def _get_ocr_cache() -> dict:
    """Return the OCR cache dict from session state."""
    if "ocr_cache" not in st.session_state:
        st.session_state["ocr_cache"] = {}
    return st.session_state["ocr_cache"]


def _get_assess_cache() -> dict:
    """Return the assessment cache dict from session state."""
    if "assess_cache" not in st.session_state:
        st.session_state["assess_cache"] = {}
    return st.session_state["assess_cache"]


def convert_to_pil_image(uploaded_file) -> list:
    """Convert any uploaded file (HEIC, PDF, JPG, PNG) to a list of PIL Images."""
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
            raise ValueError("PDF support not available. Please install PyMuPDF.")
    else:
        # Handles JPG, PNG, HEIC, WEBP, BMP etc.
        img = Image.open(uploaded_file)
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)

    return images


def pil_image_to_base64(img) -> str:
    """Convert a PIL Image to a base64-encoded JPEG string."""
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=90)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _gemini_ocr_rest(img_b64: str, api_key: str, model: str, prompt: str) -> str:
    """Call Gemini Vision via direct REST API — bypasses SDK version issues."""
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                {"text": prompt}
            ]
        }]
    }
    resp = _requests.post(url, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"{resp.status_code} {resp.text[:200]}")
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def extract_arabic_from_image_gemini(uploaded_file) -> str:
    """Use Google Gemini Vision for Arabic OCR — direct REST, cache & rate limiting."""
    # Check cache first
    file_hash = _image_hash(uploaded_file)
    cache = _get_ocr_cache()
    if file_hash in cache:
        return cache[file_hash]  # ✅ Cache hit — no API call needed

    # Check daily limit & rate limit
    _check_limit("ocr")
    _rate_limit()

    api_key = get_google_api_key()
    prompt = (
        "This image contains handwritten Arabic text written by a student. "
        "Transcribe ALL the Arabic text exactly as written, including any spelling mistakes. "
        "Do NOT correct errors. Do NOT add punctuation that is not there. "
        "Return ONLY the Arabic text, nothing else."
    )

    models_to_try = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"]
    images = convert_to_pil_image(uploaded_file)
    last_error = None
    all_text = []

    for img in images:
        img_b64 = pil_image_to_base64(img)
        page_text = None
        for model_name in models_to_try:
            try:
                page_text = _gemini_ocr_rest(img_b64, api_key, model_name, prompt)
                break
            except Exception as e:
                last_error = e
                continue
        if page_text:
            all_text.append(page_text)
        else:
            raise RuntimeError(f"All OCR models failed. Last error: {last_error}")

    result = "\n".join(all_text)
    cache[file_hash] = result   # 💾 Save to cache
    _increment_usage("ocr")     # 📊 Count usage
    return result


def assess_with_gemini(prompt: str) -> str:
    """Call Groq API — with cache & rate limiting."""
    # Check cache
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    cache = _get_assess_cache()
    if prompt_hash in cache:
        return cache[prompt_hash]  # ✅ Cache hit

    # Check limits
    _check_limit("assess")
    _rate_limit()

    api_key = get_groq_api_key()
    client = Groq(api_key=api_key)
    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7,
            )
            result = response.choices[0].message.content
            _cache_assess_result(prompt, result)  # 💾 Cache it
            return result
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All assessment models failed. Last error: {last_error}")


def _cache_assess_result(prompt: str, result: str):
    """Save assessment result to cache."""
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    _get_assess_cache()[prompt_hash] = result
    _increment_usage("assess")


# =============================================
# STREAMLIT UI
# =============================================

st.set_page_config(
    page_title="مُقيِّم الكتابة العربية",
    page_icon="🌙",
    layout="wide"
)

# ── Sidebar Usage Dashboard ──
with st.sidebar:
    st.markdown("### 📊 Daily Usage")
    usage = _get_usage()

    ocr_count   = usage.get("ocr", 0)
    assess_count = usage.get("assess", 0)
    ocr_pct     = int(ocr_count / MAX_OCR_PER_DAY * 100)
    assess_pct  = int(assess_count / MAX_ASSESS_PER_DAY * 100)

    ocr_color     = "#d4af37" if ocr_pct < 70 else ("#ff9900" if ocr_pct < 90 else "#ff4444")
    assess_color  = "#d4af37" if assess_pct < 70 else ("#ff9900" if assess_pct < 90 else "#ff4444")

    st.markdown(f"""
    <div style="font-family:'Tajawal',sans-serif;font-size:13px;color:rgba(220,205,185,0.85)">
        <div style="margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span>📷 Image OCR</span>
                <span style="color:{ocr_color};font-weight:700">{ocr_count} / {MAX_OCR_PER_DAY}</span>
            </div>
            <div style="background:rgba(255,255,255,0.07);border-radius:6px;height:6px;overflow:hidden">
                <div style="width:{ocr_pct}%;height:100%;background:{ocr_color};border-radius:6px;transition:width .3s"></div>
            </div>
        </div>
        <div style="margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span>✍️ Assessments</span>
                <span style="color:{assess_color};font-weight:700">{assess_count} / {MAX_ASSESS_PER_DAY}</span>
            </div>
            <div style="background:rgba(255,255,255,0.07);border-radius:6px;height:6px;overflow:hidden">
                <div style="width:{assess_pct}%;height:100%;background:{assess_color};border-radius:6px;transition:width .3s"></div>
            </div>
        </div>
        <div style="font-size:11px;color:rgba(212,175,55,0.4);margin-top:6px">🔄 Resets daily at midnight</div>
        <div style="font-size:11px;color:rgba(100,220,100,0.5);margin-top:3px">💾 Cached results don't count</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

# --- Rich Arabic-Inspired CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Cinzel+Decorative:wght@700&family=Tajawal:wght@300;400;700;900&display=swap');

    /* ══════════════════════════════════════════
       BASE & 3D PERSPECTIVE SCENE
    ══════════════════════════════════════════ */
    .stApp {
        background: #06050f;
        min-height: 100vh;
        perspective: 1200px;
    }

    /* Deep layered cosmic background */
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background:
            radial-gradient(ellipse 80% 50% at 20% 20%, rgba(120,60,200,0.18) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 80% 80%, rgba(212,175,55,0.12) 0%, transparent 50%),
            radial-gradient(ellipse 100% 80% at 50% 50%, rgba(10,5,30,0.95) 0%, #06050f 100%);
        pointer-events: none;
        z-index: 0;
    }

    /* Islamic geometric SVG pattern overlay */
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Cg fill='none' stroke='rgba(212,175,55,0.07)' stroke-width='0.5'%3E%3Cpolygon points='40,4 52,28 76,28 56,44 64,68 40,54 16,68 24,44 4,28 28,28'/%3E%3Crect x='20' y='20' width='40' height='40' transform='rotate(45 40 40)'/%3E%3Ccircle cx='40' cy='40' r='18'/%3E%3C/g%3E%3C/svg%3E");
        opacity: 1;
        pointer-events: none;
        z-index: 0;
    }

    /* Ensure content above overlays */
    .main .block-container { position: relative; z-index: 1; }

    /* ══════════════════════════════════════════
       HERO BANNER — 3D GOLD ARCH
    ══════════════════════════════════════════ */
    .hero-banner {
        background: linear-gradient(160deg,
            rgba(30,12,60,0.97) 0%,
            rgba(50,20,90,0.95) 40%,
            rgba(25,10,50,0.97) 100%);
        border: 1px solid rgba(212,175,55,0.5);
        border-radius: 24px;
        padding: 3rem 2rem 2.5rem;
        margin-bottom: 2.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow:
            0 0 0 1px rgba(212,175,55,0.15),
            0 30px 80px rgba(0,0,0,0.7),
            0 0 60px rgba(120,60,200,0.15),
            inset 0 1px 0 rgba(212,175,55,0.4),
            inset 0 -1px 0 rgba(212,175,55,0.1);
        transform: perspective(800px) rotateX(1deg);
    }

    /* Top gold arch */
    .hero-banner::before {
        content: '';
        position: absolute;
        top: 0; left: 10%; right: 10%;
        height: 3px;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(212,175,55,0.3) 20%,
            #d4af37 50%,
            rgba(212,175,55,0.3) 80%,
            transparent 100%);
        border-radius: 0 0 50% 50%;
    }

    /* Ambient glow orbs */
    .hero-banner::after {
        content: '';
        position: absolute;
        top: -60px; left: 50%;
        transform: translateX(-50%);
        width: 300px; height: 200px;
        background: radial-gradient(ellipse, rgba(212,175,55,0.12) 0%, transparent 70%);
        pointer-events: none;
    }

    .hero-arabic {
        font-family: 'Amiri', serif;
        font-size: 3.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f0d060 0%, #d4af37 40%, #c49a20 70%, #e8c84a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 2px 12px rgba(212,175,55,0.5));
        margin: 0;
        line-height: 1.4;
        letter-spacing: 2px;
        animation: shimmer 4s ease-in-out infinite;
    }

    @keyframes shimmer {
        0%, 100% { filter: drop-shadow(0 2px 12px rgba(212,175,55,0.4)); }
        50% { filter: drop-shadow(0 2px 24px rgba(212,175,55,0.8)); }
    }

    .hero-english {
        font-family: 'Cinzel Decorative', serif;
        font-size: 0.95rem;
        color: rgba(212,175,55,0.75);
        margin-top: 0.6rem;
        letter-spacing: 5px;
        text-transform: uppercase;
    }

    .hero-sub {
        font-family: 'Tajawal', sans-serif;
        font-size: 0.9rem;
        color: rgba(180,160,220,0.7);
        margin-top: 0.8rem;
    }

    /* Decorative corner ornaments */
    .hero-ornament {
        position: absolute;
        font-size: 1.4rem;
        color: rgba(212,175,55,0.35);
        line-height: 1;
    }

    /* ══════════════════════════════════════════
       SECTION CARDS — 3D FLOATING PANELS
    ══════════════════════════════════════════ */
    .section-card {
        background: linear-gradient(145deg,
            rgba(255,255,255,0.06) 0%,
            rgba(255,255,255,0.02) 50%,
            rgba(0,0,0,0.1) 100%);
        border: 1px solid rgba(212,175,55,0.22);
        border-radius: 18px;
        padding: 1.6rem;
        margin-bottom: 1.4rem;
        position: relative;
        overflow: hidden;
        box-shadow:
            0 4px 0 rgba(212,175,55,0.08),
            0 12px 40px rgba(0,0,0,0.4),
            0 0 0 1px rgba(255,255,255,0.03),
            inset 0 1px 0 rgba(255,255,255,0.07);
        transform: perspective(600px) rotateX(0.5deg);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .section-card:hover {
        transform: perspective(600px) rotateX(0deg) translateY(-2px);
        box-shadow:
            0 6px 0 rgba(212,175,55,0.1),
            0 20px 50px rgba(0,0,0,0.5),
            0 0 30px rgba(212,175,55,0.05),
            inset 0 1px 0 rgba(255,255,255,0.09);
    }

    /* Shimmer top line */
    .section-card::before {
        content: '';
        position: absolute;
        top: 0; left: 15%; right: 15%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(212,175,55,0.6), transparent);
    }

    /* Bottom gold shadow bar */
    .section-card::after {
        content: '';
        position: absolute;
        bottom: -1px; left: 30%; right: 30%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(212,175,55,0.2), transparent);
    }

    .section-title {
        font-family: 'Tajawal', sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        color: #d4af37;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: 1px;
        text-shadow: 0 0 20px rgba(212,175,55,0.3);
    }

    /* ══════════════════════════════════════════
       RUBRIC BADGE
    ══════════════════════════════════════════ */
    .rubric-badge {
        background: linear-gradient(135deg, rgba(212,175,55,0.12), rgba(212,175,55,0.04));
        border: 1px solid rgba(212,175,55,0.4);
        border-left: 3px solid #d4af37;
        padding: 0.7rem 1rem;
        border-radius: 10px;
        font-family: 'Tajawal', sans-serif;
        font-size: 0.9rem;
        color: #d4af37;
        margin-top: 0.5rem;
        box-shadow: 0 4px 20px rgba(212,175,55,0.08), inset 0 1px 0 rgba(212,175,55,0.1);
    }

    /* ══════════════════════════════════════════
       INPUT FIELDS — GOLD GLASS
    ══════════════════════════════════════════ */
    .stTextInput input, .stTextArea textarea {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(212,175,55,0.25) !important;
        border-radius: 12px !important;
        color: #ede0c8 !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.3), 0 1px 0 rgba(255,255,255,0.04) !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: rgba(212,175,55,0.7) !important;
        box-shadow:
            inset 0 2px 8px rgba(0,0,0,0.2),
            0 0 0 2px rgba(212,175,55,0.15),
            0 0 20px rgba(212,175,55,0.1) !important;
        background: rgba(255,255,255,0.06) !important;
    }

    /* ══════════════════════════════════════════
       3D ASSESS BUTTON — GOLD PILLAR
    ══════════════════════════════════════════ */
    .stButton > button {
        background: linear-gradient(160deg,
            #f0d060 0%,
            #d4af37 35%,
            #b8941f 70%,
            #9a7a10 100%) !important;
        color: #0d0a02 !important;
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 900 !important;
        font-size: 1.05rem !important;
        letter-spacing: 3px !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.85rem 2.5rem !important;
        box-shadow:
            0 8px 0 #5a4000,
            0 10px 30px rgba(0,0,0,0.6),
            0 0 0 1px rgba(212,175,55,0.3),
            inset 0 2px 0 rgba(255,255,255,0.35),
            inset 0 -2px 0 rgba(0,0,0,0.2) !important;
        transform: perspective(200px) rotateX(3deg) translateY(0) !important;
        transition: all 0.12s ease !important;
        text-transform: uppercase !important;
        position: relative !important;
    }

    .stButton > button:hover {
        background: linear-gradient(160deg,
            #f8e070 0%,
            #e8c84a 35%,
            #d4af37 70%,
            #b8941f 100%) !important;
        box-shadow:
            0 5px 0 #5a4000,
            0 7px 20px rgba(0,0,0,0.5),
            0 0 0 1px rgba(212,175,55,0.4),
            inset 0 2px 0 rgba(255,255,255,0.4),
            0 0 30px rgba(212,175,55,0.2) !important;
        transform: perspective(200px) rotateX(3deg) translateY(3px) !important;
    }

    .stButton > button:active {
        box-shadow:
            0 2px 0 #5a4000,
            0 3px 10px rgba(0,0,0,0.5),
            inset 0 2px 4px rgba(0,0,0,0.3) !important;
        transform: perspective(200px) rotateX(3deg) translateY(6px) !important;
    }

    /* ══════════════════════════════════════════
       TABS — GOLD SELECTOR
    ══════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(10,5,25,0.6) !important;
        border-radius: 14px !important;
        padding: 4px !important;
        border: 1px solid rgba(212,175,55,0.2) !important;
        gap: 4px !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.4) !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 700 !important;
        color: rgba(212,175,55,0.5) !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.25s ease !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(212,175,55,0.22), rgba(212,175,55,0.08)) !important;
        color: #d4af37 !important;
        box-shadow:
            0 2px 8px rgba(212,175,55,0.15),
            inset 0 1px 0 rgba(212,175,55,0.3) !important;
    }

    /* ══════════════════════════════════════════
       SLIDER
    ══════════════════════════════════════════ */
    .stSlider [data-baseweb="slider"] { padding: 0.5rem 0 !important; }
    .stSlider [data-baseweb="thumb"] {
        background: linear-gradient(145deg, #f0d060, #d4af37) !important;
        border: 2px solid #b8941f !important;
        box-shadow: 0 2px 8px rgba(212,175,55,0.4) !important;
    }
    .stSlider [data-baseweb="track-fill"] {
        background: linear-gradient(90deg, #d4af37, #f0d060) !important;
    }

    /* ══════════════════════════════════════════
       LABELS & TEXT
    ══════════════════════════════════════════ */
    .stTextInput label, .stTextArea label,
    .stSlider label, .stFileUploader label,
    .stToggle label {
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 700 !important;
        color: rgba(212,175,55,0.9) !important;
        font-size: 0.92rem !important;
        letter-spacing: 0.5px !important;
    }

    p, .stMarkdown p, .stCaption { color: rgba(220,205,185,0.85) !important; font-family: 'Tajawal', sans-serif !important; }
    h1, h2, h3 { font-family: 'Tajawal', sans-serif !important; color: #d4af37 !important; }

    /* ══════════════════════════════════════════
       FEEDBACK BOX — ORNATE SCROLL
    ══════════════════════════════════════════ */
    .feedback-box {
        background: linear-gradient(160deg,
            rgba(22,8,45,0.97),
            rgba(15,8,30,0.97));
        border: 1px solid rgba(212,175,55,0.4);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-top: 1.5rem;
        position: relative;
        box-shadow:
            0 0 0 1px rgba(212,175,55,0.08),
            0 30px 80px rgba(0,0,0,0.6),
            0 0 40px rgba(120,60,200,0.1),
            inset 0 1px 0 rgba(212,175,55,0.2),
            inset 0 -1px 0 rgba(212,175,55,0.08);
    }

    /* Floating label badge */
    .feedback-box::before {
        content: "❧  تقييم الطالب  ❧";
        position: absolute;
        top: -14px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
        color: #0d0a02;
        font-family: 'Tajawal', sans-serif;
        font-weight: 900;
        font-size: 0.78rem;
        padding: 3px 20px;
        border-radius: 20px;
        letter-spacing: 3px;
        white-space: nowrap;
        box-shadow: 0 4px 15px rgba(212,175,55,0.3);
    }

    /* Top shimmer */
    .feedback-box::after {
        content: '';
        position: absolute;
        top: 0; left: 15%; right: 15%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(212,175,55,0.5), transparent);
    }

    /* ══════════════════════════════════════════
       ALERTS
    ══════════════════════════════════════════ */
    .stAlert {
        border-radius: 14px !important;
        border: 1px solid rgba(212,175,55,0.18) !important;
        background: rgba(20,10,40,0.6) !important;
        backdrop-filter: blur(8px) !important;
    }

    /* ══════════════════════════════════════════
       DIVIDER
    ══════════════════════════════════════════ */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(212,175,55,0.3), transparent) !important;
        margin: 1.5rem 0 !important;
    }

    /* ══════════════════════════════════════════
       DOWNLOAD BUTTON
    ══════════════════════════════════════════ */
    .stDownloadButton > button {
        background: linear-gradient(145deg, rgba(212,175,55,0.12), rgba(212,175,55,0.04)) !important;
        border: 1px solid rgba(212,175,55,0.4) !important;
        color: #d4af37 !important;
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 0 rgba(212,175,55,0.15), 0 6px 20px rgba(0,0,0,0.3) !important;
        transition: all 0.15s ease !important;
    }

    .stDownloadButton > button:hover {
        background: linear-gradient(145deg, rgba(212,175,55,0.2), rgba(212,175,55,0.08)) !important;
        transform: translateY(2px) !important;
        box-shadow: 0 2px 0 rgba(212,175,55,0.15), 0 4px 12px rgba(0,0,0,0.3) !important;
    }

    /* ══════════════════════════════════════════
       FILE UPLOADER
    ══════════════════════════════════════════ */
    [data-testid="stFileUploader"] {
        border: 1px dashed rgba(212,175,55,0.3) !important;
        border-radius: 14px !important;
        padding: 0.6rem !important;
        background: rgba(212,175,55,0.02) !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: rgba(212,175,55,0.55) !important;
        background: rgba(212,175,55,0.04) !important;
    }

    /* ══════════════════════════════════════════
       SCROLLBAR
    ══════════════════════════════════════════ */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.01); }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, rgba(212,175,55,0.4), rgba(212,175,55,0.2));
        border-radius: 3px;
    }

    /* ══════════════════════════════════════════
       SPINNER / PROGRESS
    ══════════════════════════════════════════ */
    .stSpinner > div { border-top-color: #d4af37 !important; }

    /* ══════════════════════════════════════════
       SIDEBAR (API key area)
    ══════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0820 0%, #080514 100%) !important;
        border-right: 1px solid rgba(212,175,55,0.2) !important;
    }

    /* ══════════════════════════════════════════
       HIDE STREAMLIT CHROME
    ══════════════════════════════════════════ */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Hero Banner ──
st.markdown("""
<div class="hero-banner">
    <span class="hero-ornament" style="top:14px;left:18px;">✦</span>
    <span class="hero-ornament" style="top:14px;right:18px;">✦</span>
    <span class="hero-ornament" style="bottom:14px;left:18px;">✧</span>
    <span class="hero-ornament" style="bottom:14px;right:18px;">✧</span>
    <div style="font-family:'Amiri',serif;font-size:0.85rem;color:rgba(212,175,55,0.45);letter-spacing:12px;margin-bottom:0.6rem;">بِسْمِ اللَّهِ</div>
    <div class="hero-arabic">مُقيِّم الكتابة العربية</div>
    <div class="hero-english">Arabic Writing Assessor</div>
    <div style="width:120px;height:1px;background:linear-gradient(90deg,transparent,rgba(212,175,55,0.5),transparent);margin:0.9rem auto;"></div>
    <div class="hero-sub">✦ &nbsp; تقييم ذكي لكتابات الطلاب بالذكاء الاصطناعي &nbsp; ✦</div>
</div>
""", unsafe_allow_html=True)

# =============================================
# LAYOUT
# =============================================
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-title">🌙 Student Profile</div>', unsafe_allow_html=True)

    name = st.text_input("Student Name", placeholder="e.g. Sara Ahmed")

    year = st.slider(
        "Years of Learning Arabic",
        min_value=2, max_value=9, value=5,
        help="Drag to select how many years the student has been learning Arabic"
    )

    rubric_key, rubric_text = get_rubric_by_year(year)
    if rubric_key:
        st.markdown(f'<div class="rubric-badge">📊 Rubric applied: <strong>{rubric_key} Years of Study</strong></div>', unsafe_allow_html=True)
    else:
        st.warning("No rubric found for this year range.")

    st.divider()

    st.markdown('<div class="section-title">🎯 Learning Objective (LO)</div>', unsafe_allow_html=True)
    lo_text = st.text_area("Type the LO here", height=100, placeholder="e.g. Student can write a descriptive paragraph about their daily routine using past tense.")
    lo_img = st.file_uploader("Or upload LO as image", type=["png", "jpg", "jpeg", "heic", "heif", "webp", "pdf"], key="lo_img")
    if lo_img:
        lo_extracted = extract_text_from_image(lo_img)
        if lo_extracted:
            st.success("✅ LO extracted from image")
            lo_text = lo_extracted

    st.markdown('<div class="section-title">✅ Success Criteria</div>', unsafe_allow_html=True)
    sc_text = st.text_area("Type Success Criteria here", height=100, placeholder="e.g. Uses at least 3 connectives, writes 6-8 lines, uses past and present tense.")
    sc_img = st.file_uploader("Or upload Success Criteria as image", type=["png", "jpg", "jpeg", "heic", "heif", "webp", "pdf"], key="sc_img")
    if sc_img:
        sc_extracted = extract_text_from_image(sc_img)
        if sc_extracted:
            st.success("✅ Success Criteria extracted from image")
            sc_text = sc_extracted

    st.markdown('<div class="section-title">📚 Word Bank <span style="font-size:0.75rem;opacity:0.6;font-weight:400">(Optional)</span></div>', unsafe_allow_html=True)
    use_word_bank = st.toggle("Enable Word Bank / Vocabulary List", value=False, help="Add specific words you want the student to use in their writing")
    word_bank_text = ""
    if use_word_bank:
        st.caption("Add vocabulary words you want the student to use. The AI will check if they used them and suggest relevant ones.")
        wb_tab1, wb_tab2, wb_tab3 = st.tabs(["✏️ Type Words", "📄 Upload CSV / TXT", "📷 Upload Photo / PDF"])

        with wb_tab1:
            word_bank_text = st.text_area(
                "Type words (one per line or comma-separated)",
                height=120,
                placeholder="e.g. بالإضافة إلى ذلك، على الرغم من، في المقابل، لذلك، ومن ثم",
                help="Type Arabic vocabulary words, phrases, connectives, or adjectives you want the student to use."
            )

        with wb_tab2:
            wb_csv = st.file_uploader(
                "Upload CSV or TXT word list",
                type=["csv", "txt"],
                key="wb_csv"
            )
            if wb_csv:
                try:
                    import pandas as pd
                    from io import StringIO
                    wb_content = wb_csv.read().decode("utf-8")
                    try:
                        wb_df = pd.read_csv(StringIO(wb_content))
                        word_bank_text = "\n".join(wb_df.iloc[:, 0].dropna().astype(str).tolist())
                    except Exception:
                        word_bank_text = wb_content
                    st.success(f"✅ Loaded {len(word_bank_text.splitlines())} words from file")
                    st.text_area("Preview:", value=word_bank_text, height=100, disabled=True)
                except Exception as e:
                    st.error(f"❌ Could not read file: {str(e)}")

        with wb_tab3:
            st.caption("📸 Upload a photo, screenshot, or PDF of your word bank — AI will read the words automatically.")
            wb_imgs = st.file_uploader(
                "Upload word bank image(s) or PDF",
                type=["png", "jpg", "jpeg", "heic", "heif", "webp", "bmp", "pdf"],
                key="wb_img",
                accept_multiple_files=True
            )
            if wb_imgs:
                all_wb_words = []
                with st.spinner(f"🔍 Reading {len(wb_imgs)} file(s) for words..."):
                    for i, wb_img in enumerate(wb_imgs):
                        try:
                            extracted_words = extract_arabic_from_image_gemini(wb_img)
                            if extracted_words and extracted_words.strip():
                                all_wb_words.append(extracted_words.strip())
                                st.success(f"✅ File {i+1} read successfully")
                            else:
                                st.warning(f"⚠️ Could not extract words from file {i+1}. Try a clearer photo.")
                        except Exception as e:
                            st.error(f"❌ Could not read file {i+1}: {str(e)}")
                if all_wb_words:
                    word_bank_text = "\n".join(all_wb_words)
                    st.markdown("**📝 Extracted words:**")
                    st.text_area("Preview:", value=word_bank_text, height=100, disabled=True)

with col_right:
    st.markdown('<div class="section-title">✍️ Student Writing</div>', unsafe_allow_html=True)

    writing_tab1, writing_tab2 = st.tabs(["⌨️ Type / Paste Text", "📷 Upload Handwritten Photo"])

    writing = ""

    with writing_tab1:
        writing_typed = st.text_area(
            "Paste or type the student's Arabic writing here",
            height=260,
            placeholder="اكتب هنا...",
            help="You can paste Arabic text directly into this box."
        )
        if writing_typed.strip():
            writing = writing_typed

    with writing_tab2:
        st.info("📸 Upload a photo of the student's handwritten Arabic. AI will read it automatically.")
        st.caption("📱 Supports: JPG, PNG, HEIC (iPhone), PDF, WEBP, BMP — single or multiple photos")
        writing_imgs = st.file_uploader(
            "Upload handwriting photo(s) or PDF",
            type=["png", "jpg", "jpeg", "heic", "heif", "webp", "bmp", "pdf"],
            key="writing_img",
            accept_multiple_files=True
        )
        if writing_imgs:
            all_extracted = []
            for i, writing_img in enumerate(writing_imgs):
                st.image(writing_img, caption=f"📄 Page {i+1}: {writing_img.name}", use_column_width=True)
            with st.spinner(f"🔍 Reading {len(writing_imgs)} file(s)..."):
                for i, writing_img in enumerate(writing_imgs):
                    try:
                        extracted = extract_arabic_from_image_gemini(writing_img)
                        if extracted:
                            all_extracted.append(extracted)
                            st.success(f"✅ File {i+1} extracted successfully!")
                        else:
                            st.warning(f"⚠️ Could not extract text from file {i+1}. Try a clearer photo.")
                    except Exception as e:
                        st.error(f"❌ Could not read file {i+1}: {str(e)}")
            if all_extracted:
                extracted_writing = "\n".join(all_extracted)
                st.markdown("**📝 Extracted text:**")
                st.markdown(f"> {extracted_writing}")
                writing = extracted_writing

    if writing.strip():
        word_count = len(writing.split())
        st.caption(f"Word count: ~{word_count} words")

    st.divider()

    assess_btn = st.button(
        "🔍 Assess Writing",
        type="primary",
        use_container_width=True,
        disabled=not (name.strip() and writing.strip() and rubric_key)
    )

    if not name.strip():
        st.caption("⚠️ Please enter the student's name.")
    if not writing.strip():
        st.caption("⚠️ Please type the writing or upload a photo.")
    if not rubric_key:
        st.caption("⚠️ No rubric available for the selected year.")

# =============================================
# ASSESSMENT OUTPUT
# =============================================
if assess_btn:
    st.divider()
    with st.spinner(f"✨ Assessing {name.strip().split()[0]}'s writing with AI..."):
        try:
            prompt = build_prompt(
                name=name.strip(),
                year=year,
                lo=lo_text.strip(),
                sc=sc_text.strip(),
                writing=writing.strip(),
                rubric_key=rubric_key,
                rubric=rubric_text,
                word_bank=word_bank_text.strip() if use_word_bank else ""
            )
            result = assess_with_gemini(prompt)

            st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
            st.markdown(result)
            st.markdown('</div>', unsafe_allow_html=True)

            st.divider()
            st.download_button(
                label="⬇️ Download Feedback as .txt",
                data=result,
                file_name=f"feedback_{name.strip().replace(' ', '_')}.txt",
                mime="text/plain"
            )

        except ValueError as e:
            st.error(f"❌ API Key error: {str(e)}")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
