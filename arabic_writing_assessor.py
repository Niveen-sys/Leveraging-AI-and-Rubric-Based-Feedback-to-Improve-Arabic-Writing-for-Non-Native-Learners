import streamlit as st
import streamlit.components.v1 as components
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

# DOCX support
try:
    import docx as python_docx
    DOCX_SUPPORTED = True
except ImportError:
    DOCX_SUPPORTED = False

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
    for key, rubric_text in RUBRICS.items():
        if isinstance(key, str) and "-" in key:
            try:
                start, end = key.split("-")
                if int(start.strip()) <= year <= int(end.strip()):
                    return key, rubric_text
            except ValueError:
                continue
    if year in RUBRICS:
        return str(year), RUBRICS[year]
    if str(year) in RUBRICS:
        return str(year), RUBRICS[str(year)]
    int_keys = [k for k in RUBRICS if isinstance(k, int)]
    if int_keys:
        closest = min(int_keys, key=lambda k: abs(k - year))
        return str(closest), RUBRICS[closest]
    return "", ""

def get_level_note(year: int) -> str:
    if year <= 3:
        return "This is a beginner student. Focus on basic sentence structure, simple vocabulary, and present tense. Keep expectations simple and very encouraging."
    elif year <= 5:
        return "This is an elementary student. Expect simple paragraphs, 2-3 tenses, and basic connectives. Encourage growth in vocabulary and sentence variety."
    elif year <= 7:
        return "This is an intermediate student. Expect coherent paragraphs, variety of tenses, connectives, and some complex structures."
    else:
        return "This is an advanced student. Expect multi-paragraph writing, rich vocabulary, all tenses, complex structures, and strong coherence."

def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def build_prompt(name: str, year: int, lo: str, sc: str, writing: str,
                 rubric_key: str, rubric: str, word_bank: str = '') -> str:
    first_name = name.strip().split()[0] if name.strip() else name
    level_note = get_level_note(year)

    # ── Word bank section ─────────────────────────────────────────────────
    if word_bank.strip():
        word_bank_section = f"""Word Bank provided by teacher:
{word_bank}

WORD BANK SPELLING RULES — TOP PRIORITY:
- The word bank IS the ground truth for correct Arabic spelling
- FIRST scan the word bank for every word that appears (correctly or incorrectly) in the student writing
- If a student wrote a word that SHOULD be a word-bank word but spelled it wrong → flag it
- If a student wrote something close (edit distance ≤ 2) to a word-bank word → that is a spelling error, use the word-bank version as the correct form
- ONLY flag spelling errors that relate to word-bank vocabulary OR very clear standard Arabic errors
- Do NOT flag words that have no word-bank equivalent — if unsure, skip it
- CRITICAL: Check which word-bank words the student DID use — praise them specifically
- CRITICAL: Identify 2-3 HIGH-IMPACT unused word-bank words that would strengthen the writing → use them as next-step suggestions"""
    else:
        word_bank_section = """No word bank provided.
SPELLING RULES: Only flag clear, obvious Arabic spelling errors where wrong consonants, missing letters, or extra letters change the word meaning. Maximum 3 corrections. Be very conservative."""

    return f"""
You are an experienced Arabic teacher marking a student's handwritten work.
You must produce feedback in EXACTLY the same style as this teacher example:

TEACHER STYLE EXAMPLE:
★ Amazing informations expressed clearly using past tense
★ Nice opening & closure
★ Excellent use of time adverbs & connectives
↗ Even better if you use different subjects (family members)
↗ Even better if you add more descriptive adjectives like كبير، جميل

YOUR FEEDBACK MUST:
1. Be written in English
2. Use ★ bullet points for WWW (green stars — what went well) — keep SHORT and SPECIFIC to what student ACTUALLY wrote
3. Use ↗ for EBI (red arrow) — EBI MUST be SPECIFIC and ACTIONABLE
   - If Success Criteria not met → suggest exactly what's missing from SC
   - If word bank provided → suggest 2-3 SPECIFIC unused words from word bank
   - If rubric gap → suggest next rubric level improvement
   - Start each with "Even better if you use..." or "Even better if you..."
4. Be SHORT and punchy — no long paragraphs, just clear bullet points
5. Identify ONLY TRUE Arabic spelling mistakes — follow the rules below STRICTLY
6. Generate "NEXT STEPS" — 2-3 specific, achievable targets
7. Be appropriate for Year {year} student ({year} years of Arabic)

════════════════════════════════════════════
SCORING CALIBRATION — READ CAREFULLY
════════════════════════════════════════════
Score must reflect ACTUAL quality relative to {year} years of study.

IMPORTANT SCORING PHILOSOPHY:
- A student who writes coherent, on-topic sentences appropriate for their level MUST score AT LEAST Accomplished (2pts per category, total ≥ 8/15)
- Do NOT default to Beginning or Developing unless the writing is genuinely very poor for this level
- Score GENEROUSLY for genuine effort and appropriate-level content
- NEVER under-score because handwriting looks messy — only score the content
- A student who attempts ALL required elements (even imperfectly) scores Accomplished or above
- The score should feel ENCOURAGING and FAIR, not punishing

Score breakdown: 5 categories × 3 points each = 15 total
* Beginning   = 1pt per category   (genuinely very weak)
* Developing  = 1.5pt per category (partial attempt, clear gaps)
* Accomplished= 2pt per category   (meets main expectations for year level)
* Advanced    = 2.5pt per category (above expectations)
* Exemplary   = 3pt per category   (outstanding for year level)

Add the per-category scores to get the total. Round to nearest 0.5.
Default assumption: if writing is on-topic and has appropriate length → Accomplished minimum.

════════════════════════════════════════════
NEXT STEPS — ANTI-REPETITION RULES (CRITICAL)
════════════════════════════════════════════
BEFORE writing next steps, you MUST:
1. READ the student writing very carefully
2. Make a MENTAL LIST of what the student ALREADY did:
   - Which tenses did they use?
   - Which connectives did they use?
   - How many lines did they write?
   - Which word-bank words did they use?
   - Did they write opinions, negation, adjectives?
3. ONLY suggest things that are GENUINELY MISSING from their writing
4. NEVER suggest something the student already did — this is the most important rule
5. Each next step must be UNIQUE — no two next steps should say the same thing in different words
6. Be SPECIFIC: name the exact Arabic word, tense, or structure they should add
7. Maximum 3 next steps — quality over quantity

BAD next steps (never write these if student already did them):
✗ "Use connectives" — if they already used connectives
✗ "Write more lines" — if they already meet the line count
✗ "Use past tense" — if they already used past tense
✗ "Add adjectives" — if they already used adjectives

GOOD next steps (specific and genuinely missing):
✓ "Add the connective بالإضافة إلى to link your second idea to your third"
✓ "Try using future tense (سوف + verb) to say what you will do next time"
✓ "Include the word bank word [specific word] to describe [specific thing]"

════════════════════════════════════════════
SPELLING CORRECTION RULES — STRICT
════════════════════════════════════════════
{"WORD BANK IS PRIMARY SOURCE: Compare student words against word-bank first." if word_bank.strip() else "No word bank — be very conservative, flag only obvious errors."}

WHAT TO FLAG:
- Student wrote an Arabic word in Arabic script with wrong letters (wrong consonant, missing letter, extra letter, wrong dot placement)
- If word bank provided: student wrote a near-match to a word-bank word with spelling error

WHAT TO IGNORE (NEVER FLAG):
- English words, romanised words, transliterations (e.g. "akhtar", "malak") — OCR artifacts
- Hamza differences: أ vs ا vs إ vs آ — do NOT correct these
- ة vs ه at word endings — do NOT correct these
- ى vs ي at word endings — do NOT correct these
- Any word not in the word bank AND not a clear standard Arabic error
- Maximum 5 corrections — if unsure, skip

Output fields:
- "wrong": the Arabic word as the student wrote it (Arabic script only)
- "correct": the correct spelling (Arabic script only, from word bank if available)

════════════════════════════════════════════
EBI (EVEN BETTER IF) — RULES
════════════════════════════════════════════
- MAXIMUM 2 EBI points
- Must come from: unmet SC, unused word bank words, or clear rubric gaps
- Be specific and kind — start with "Even better if you..."
- Do NOT repeat anything already in the next steps
- Do NOT suggest something the student already did

STUDENT: {first_name} (Year {year} — {year} years of Arabic study)
LEVEL GUIDANCE: {level_note}

LEARNING OBJECTIVE:
{lo if lo.strip() else "Not provided."}

SUCCESS CRITERIA:
{sc if sc.strip() else "Not provided."}

RUBRIC:
{rubric}

{word_bank_section}

STUDENT WRITING:
{writing}

OUTPUT — return ONLY this JSON and nothing else (no markdown, no explanation):
{{
  "www": ["strength 1", "strength 2", "strength 3"],
  "ebi": ["improvement 1", "improvement 2"],
  "next_steps": ["specific achievable target 1", "specific achievable target 2", "specific achievable target 3"],
  "spelling": [{{"wrong": "arabic word with mistake", "correct": "correct arabic word"}}],
  "grammar": [{{"original": "sentence from writing", "issue": "what is wrong", "hint": "guide to fix without giving answer"}}],
  "sc_check": [{{"criterion": "...", "met": true/false, "comment": "..."}}],
  "score": {{"level": "Beginning/Developing/Accomplished/Advanced/Exemplary", "score": 0, "out_of": 15, "reason": "..."}}
}}

WWW RULES:
- 2-3 specific strengths referencing ACTUAL words or sentences from the writing
- MUST mention any word-bank words they successfully used
- Be encouraging but grounded in what they actually wrote

Keep everything age-appropriate for Year {year}.
"""

# ── API Keys from Secrets File ────────────────────────────────────────────────
def _secret(key: str) -> str:
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""

def get_google_api_key() -> str:
    key = _secret("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise ValueError("❌ GOOGLE_API_KEY not found! Please add it to .streamlit/secrets.toml")
    return key

def get_groq_api_key() -> str:
    key = _secret("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError("❌ GROQ_API_KEY not found! Please add it to .streamlit/secrets.toml")
    return key

# ══════════════════════════════════════════════════════════════
# CACHE & RATE LIMITER
# ══════════════════════════════════════════════════════════════
MAX_OCR_PER_DAY    = 1500
MAX_ASSESS_PER_DAY = 1500
RATE_LIMIT_WINDOW  = 60
MAX_CALLS_PER_MIN  = 14

def _get_usage() -> dict:
    today = str(date.today())
    if "usage" not in st.session_state or st.session_state["usage"].get("date") != today:
        st.session_state["usage"] = {"date": today, "ocr": 0, "assess": 0}
    return st.session_state["usage"]

def _increment_usage(kind: str):
    usage = _get_usage()
    usage[kind] = usage.get(kind, 0) + 1

def _check_limit(kind: str):
    usage = _get_usage()
    limit = MAX_OCR_PER_DAY if kind == "ocr" else MAX_ASSESS_PER_DAY
    count = usage.get(kind, 0)
    if count >= limit:
        raise RuntimeError(f"⛔ Daily limit reached ({count}/{limit}). Resets tomorrow at midnight.")

def _rate_limit():
    if "rate_calls" not in st.session_state:
        st.session_state["rate_calls"] = []
    now = time.time()
    st.session_state["rate_calls"] = [t for t in st.session_state["rate_calls"] if now - t < RATE_LIMIT_WINDOW]
    if len(st.session_state["rate_calls"]) >= MAX_CALLS_PER_MIN:
        wait = RATE_LIMIT_WINDOW - (now - st.session_state["rate_calls"][0])
        raise RuntimeError(f"⏳ Too many requests. Please wait {int(wait)+1} seconds and try again.")
    st.session_state["rate_calls"].append(now)

def _image_hash(uploaded_file) -> str:
    uploaded_file.seek(0)
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return hashlib.md5(data).hexdigest()

def _get_ocr_cache() -> dict:
    if "ocr_cache" not in st.session_state:
        st.session_state["ocr_cache"] = {}
    return st.session_state["ocr_cache"]

def _get_assess_cache() -> dict:
    if "assess_cache" not in st.session_state:
        st.session_state["assess_cache"] = {}
    return st.session_state["assess_cache"]

# =============================================
# FILE → PIL IMAGE CONVERSION
# Accepts: JPG, PNG, HEIC, WEBP, BMP, PDF,
#          DOCX, DOC, TXT, CSV
# =============================================
def convert_to_pil_image(uploaded_file) -> list:
    """
    Convert ANY uploaded file to a list of PIL Images for OCR.
    Plain-text formats (DOCX/TXT/CSV) are handled separately upstream;
    this function handles image and PDF paths only.
    """
    filename = uploaded_file.name.lower()
    images = []

    # ── PDF ────────────────────────────────────────────────────────────────
    if filename.endswith(".pdf"):
        if not PDF_SUPPORTED:
            raise ValueError("PDF support not available. Please install PyMuPDF: pip install pymupdf")
        uploaded_file.seek(0)
        data = uploaded_file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images

    # ── DOCX / DOC ─────────────────────────────────────────────────────────
    if filename.endswith(".docx") or filename.endswith(".doc"):
        if not DOCX_SUPPORTED:
            raise ValueError("DOCX support not available. Please install python-docx.")
        uploaded_file.seek(0)
        data = uploaded_file.read()
        doc = python_docx.Document(io.BytesIO(data))
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        from PIL import ImageDraw
        img = Image.new("RGB", (900, max(500, len(text.split('\n')) * 32 + 80)), color="white")
        draw = ImageDraw.Draw(img)
        y = 20
        for line in text.split('\n'):
            draw.text((20, y), line, fill="black")
            y += 30
        images.append(img)
        return images

    # ── TXT / CSV ──────────────────────────────────────────────────────────
    if filename.endswith(".txt") or filename.endswith(".csv"):
        uploaded_file.seek(0)
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        from PIL import ImageDraw
        lines = text.split('\n')
        img = Image.new("RGB", (900, max(500, len(lines) * 32 + 80)), color="white")
        draw = ImageDraw.Draw(img)
        y = 20
        for line in lines:
            draw.text((20, y), line, fill="black")
            y += 30
        images.append(img)
        return images

    # ── All image formats (JPG, PNG, HEIC, WEBP, BMP, etc.) ───────────────
    uploaded_file.seek(0)
    img = Image.open(uploaded_file)
    if img.mode != "RGB":
        img = img.convert("RGB")
    images.append(img)
    return images

def extract_text_from_docx(uploaded_file) -> str:
    """Extract text directly from a DOCX file without OCR."""
    if DOCX_SUPPORTED:
        uploaded_file.seek(0)
        data = uploaded_file.read()
        doc = python_docx.Document(io.BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    raise ValueError("python-docx not installed.")

def pil_image_to_base64(img) -> str:
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=90)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def _list_gemini_models(api_key: str) -> list:
    url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    try:
        resp = _requests.get(url, timeout=10)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return [
                m["name"].replace("models/", "")
                for m in models
                if "generateContent" in m.get("supportedGenerationMethods", [])
                and "gemini" in m.get("name", "").lower()
            ]
    except Exception:
        pass
    return []

def _preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    from PIL import ImageEnhance, ImageFilter
    w, h = img.size
    if max(w, h) < 1200:
        scale = 1200 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    grey = img.convert("L")
    grey = ImageEnhance.Contrast(grey).enhance(2.2)
    grey = ImageEnhance.Sharpness(grey).enhance(3.0)
    grey = grey.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return grey.convert("RGB")

def _gemini_ocr_rest(img_b64: str, api_key: str, model: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
            {"text": prompt}
        ]}],
        "generationConfig": {"temperature": 0.1, "topP": 0.95, "topK": 40, "maxOutputTokens": 2048}
    }
    resp = _requests.post(url, json=payload, timeout=45)
    if resp.status_code != 200:
        raise RuntimeError(f"{resp.status_code} {resp.text[:200]}")
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

# ── OCR prompt ────────────────────────────────────────────────────────────────
_OCR_PROMPT = """
You are an EXPERT Arabic handwriting recognition system. Your ONLY job is to read what a
non-native Arabic student wrote by hand and transcribe it faithfully.

══════════════════════════════════════════════════════
STEP 1 — SCAN THE WHOLE PAGE FIRST
══════════════════════════════════════════════════════
Before reading individual words:
• Count the lines. Note where each line starts and ends (right to left).
• Identify any title or heading written larger/above the main text.
• Note the approximate topic from any clearly readable words — this context helps decode unclear words.

══════════════════════════════════════════════════════
STEP 2 — READ LINE BY LINE, RIGHT TO LEFT
══════════════════════════════════════════════════════
For each line, read every word in RIGHT-TO-LEFT order (Arabic direction).

LETTER READING RULES:
1. POSITION: determine if the letter is word-initial/medial/final — each Arabic letter has a different shape.
2. BASELINE SHAPE: identify the core skeleton of the letter ignoring dots.
3. DOTS: count dots and their position (above/below).
4. STUDENT DOT ERRORS: non-native students often misplace dots — accept it even if dots are wrong.
5. CONTEXT RECOVERY: if a word is ambiguous, pick the reading that makes grammatical/topical sense.

COMMON STUDENT ERRORS TO PRESERVE (do NOT correct):
• ة written as ه at word-end (or vice-versa)
• ى/ي confusion at word-end
• Hamza missing or wrong (أ إ آ ء ؤ ئ all accepted as written)
• Missing dots on ن ي ت ث etc.
• Connected letters that should be separate

EXTREMELY UNCLEAR LETTERS: make your best guess from context. Only use [?] if truly impossible.

══════════════════════════════════════════════════════
OUTPUT FORMAT — STRICT
══════════════════════════════════════════════════════
• Output ONLY the Arabic text. One transcribed line per written line.
• NO English words. NO explanations. NO tashkeel unless clearly visible.
• NO corrections — preserve every student error exactly as written.
• NO comments, notes, or confidence scores.
• If a page has a title/heading, put it on its own line first.
• Blank lines in the writing → blank lines in output.

NOW READ THE HANDWRITING IN THE IMAGE:
"""

# =============================================
# MAIN OCR FUNCTION
# Accepts ALL file types
# =============================================
def extract_arabic_from_image_gemini(uploaded_file) -> str:
    """
    Universal OCR / text-extraction for ANY file type:
    - DOCX / DOC → direct text extraction (no OCR)
    - TXT / CSV   → direct UTF-8 read
    - PDF         → render each page → Gemini OCR
    - Images (JPG, PNG, HEIC, WEBP, BMP, etc.) → Gemini OCR
    """
    filename = uploaded_file.name.lower()

    # ── Plain-text formats: no OCR needed ────────────────────────────────
    if filename.endswith(".docx") or filename.endswith(".doc"):
        try:
            text = extract_text_from_docx(uploaded_file)
            if text.strip():
                return text
        except Exception:
            pass  # Fall through to image-based OCR as last resort

    if filename.endswith(".txt") or filename.endswith(".csv"):
        try:
            uploaded_file.seek(0)
            return uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

    # ── Image / PDF path ─────────────────────────────────────────────────
    file_hash = _image_hash(uploaded_file)
    cache = _get_ocr_cache()
    if file_hash in cache:
        return cache[file_hash]

    _check_limit("ocr")
    _rate_limit()

    api_key = get_google_api_key()
    discovered = _list_gemini_models(api_key)

    preferred = [
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-2.5-flash-preview-04-17",
        "gemini-1.5-flash-002",
        "gemini-1.5-flash",
    ]
    ordered = (
        [m for m in preferred if m in discovered]
        + [m for m in discovered if m not in preferred]
        + [m for m in preferred if m not in discovered]
    )
    models_to_try = ordered[:6]

    raw_images = convert_to_pil_image(uploaded_file)
    last_error = None
    all_text = []

    for img in raw_images:
        enhanced_img = _preprocess_image_for_ocr(img)
        img_b64 = pil_image_to_base64(enhanced_img)
        page_text = None

        for model_name in models_to_try:
            try:
                page_text = _gemini_ocr_rest(img_b64, api_key, model_name, _OCR_PROMPT)
                break
            except Exception as e:
                last_error = e
                continue

        # Retry with original (unprocessed) image if enhanced failed
        if not page_text:
            orig_b64 = pil_image_to_base64(img)
            for model_name in models_to_try:
                try:
                    page_text = _gemini_ocr_rest(orig_b64, api_key, model_name, _OCR_PROMPT)
                    break
                except Exception as e:
                    last_error = e
                    continue

        if page_text:
            all_text.append(page_text)
        else:
            raise RuntimeError(f"All OCR models failed. Last error: {last_error}")

    result = "\n".join(all_text)
    cache[file_hash] = result
    _increment_usage("ocr")
    return result

def smart_spelling_matcher(writing: str, word_bank: str) -> list:
    if not word_bank.strip():
        return []
    known_words = set()
    for line in word_bank.strip().split('\n'):
        for word in line.replace(',', ' ').split():
            word = word.strip()
            if word and len(word) > 1:
                known_words.add(word)
    if not known_words:
        return []
    writing_words = []
    for line in writing.split('\n'):
        for word in line.split():
            clean = word.strip('.,،؛:!?""()[]')
            if clean and len(clean) > 1:
                writing_words.append(clean)
    corrections = []
    for written_word in writing_words:
        if written_word in known_words:
            continue
        best_match = None
        min_distance = 999
        for known_word in known_words:
            distance = levenshtein_distance(written_word, known_word)
            if distance < min_distance and distance <= 2 and abs(len(written_word) - len(known_word)) <= 2:
                min_distance = distance
                best_match = known_word
        if best_match and min_distance <= 2:
            confidence = "high" if min_distance == 1 else "medium"
            corrections.append({
                "wrong": written_word,
                "correct": best_match,
                "priority": confidence,
                "distance": min_distance
            })
    corrections.sort(key=lambda x: (x["priority"] == "medium", x["distance"]))
    return corrections[:7]

def assess_with_gemini(prompt: str) -> str:
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    cache = _get_assess_cache()
    if prompt_hash in cache:
        return cache[prompt_hash]

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
                max_tokens=2500,
                temperature=0.7,
            )
            result = response.choices[0].message.content
            cache[prompt_hash] = result
            _increment_usage("assess")
            return result
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All assessment models failed. Last error: {last_error}")

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
    ocr_count    = usage.get("ocr", 0)
    assess_count = usage.get("assess", 0)
    ocr_pct    = int(ocr_count    / MAX_OCR_PER_DAY    * 100)
    assess_pct = int(assess_count / MAX_ASSESS_PER_DAY * 100)
    ocr_color    = "#d4af37" if ocr_pct    < 70 else ("#ff9900" if ocr_pct    < 90 else "#ff4444")
    assess_color = "#d4af37" if assess_pct < 70 else ("#ff9900" if assess_pct < 90 else "#ff4444")
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Cinzel+Decorative:wght@700&family=Tajawal:wght@300;400;700;900&display=swap');

.stApp {
  background: #06050f;
  min-height: 100vh;
  perspective: 1200px;
}
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
.stApp::after {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Cg fill='none' stroke='rgba(212,175,55,0.07)' stroke-width='0.5'%3E%3Cpolygon points='40,4 52,28 76,28 56,44 64,68 40,54 16,68 24,44 4,28 28,28'/%3E%3Crect x='20' y='20' width='40' height='40' transform='rotate(45 40 40)'/%3E%3Ccircle cx='40' cy='40' r='18'/%3E%3C/g%3E%3C/svg%3E");
  opacity: 1;
  pointer-events: none;
  z-index: 0;
}
.main .block-container { position: relative; z-index: 1; }

.hero-banner {
  background: linear-gradient(160deg, rgba(30,12,60,0.97) 0%, rgba(50,20,90,0.95) 40%, rgba(25,10,50,0.97) 100%);
  border: 1px solid rgba(212,175,55,0.5);
  border-radius: 24px;
  padding: 3rem 2rem 2.5rem;
  margin-bottom: 2.5rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(212,175,55,0.15), 0 30px 80px rgba(0,0,0,0.7),
              0 0 60px rgba(120,60,200,0.15), inset 0 1px 0 rgba(212,175,55,0.4),
              inset 0 -1px 0 rgba(212,175,55,0.1);
  transform: perspective(800px) rotateX(1deg);
}
.hero-banner::before {
  content: '';
  position: absolute;
  top: 0; left: 10%; right: 10%;
  height: 3px;
  background: linear-gradient(90deg, transparent 0%, rgba(212,175,55,0.3) 20%, #d4af37 50%, rgba(212,175,55,0.3) 80%, transparent 100%);
  border-radius: 0 0 50% 50%;
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
  50%       { filter: drop-shadow(0 2px 24px rgba(212,175,55,0.8)); }
}
.hero-english {
  font-family: 'Cinzel Decorative', serif;
  font-size: 0.95rem;
  color: rgba(212,175,55,0.75);
  margin-top: 0.6rem;
  letter-spacing: 5px;
  text-transform: uppercase;
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
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.2), 0 0 0 2px rgba(212,175,55,0.15), 0 0 20px rgba(212,175,55,0.1) !important;
  background: rgba(255,255,255,0.06) !important;
}
.stButton > button {
  background: linear-gradient(160deg, #f0d060 0%, #d4af37 35%, #b8941f 70%, #9a7a10 100%) !important;
  color: #0d0a02 !important;
  font-family: 'Tajawal', sans-serif !important;
  font-weight: 900 !important;
  font-size: 1.05rem !important;
  letter-spacing: 3px !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 0.85rem 2.5rem !important;
  box-shadow: 0 8px 0 #5a4000, 0 10px 30px rgba(0,0,0,0.6), 0 0 0 1px rgba(212,175,55,0.3),
              inset 0 2px 0 rgba(255,255,255,0.35), inset 0 -2px 0 rgba(0,0,0,0.2) !important;
  transform: perspective(200px) rotateX(3deg) translateY(0) !important;
  transition: all 0.12s ease !important;
  text-transform: uppercase !important;
}
.stButton > button:hover {
  background: linear-gradient(160deg, #f8e070 0%, #e8c84a 35%, #d4af37 70%, #b8941f 100%) !important;
  box-shadow: 0 5px 0 #5a4000, 0 7px 20px rgba(0,0,0,0.5), 0 0 0 1px rgba(212,175,55,0.4),
              inset 0 2px 0 rgba(255,255,255,0.4), 0 0 30px rgba(212,175,55,0.2) !important;
  transform: perspective(200px) rotateX(3deg) translateY(3px) !important;
}
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
  box-shadow: 0 2px 8px rgba(212,175,55,0.15), inset 0 1px 0 rgba(212,175,55,0.3) !important;
}
.stTextInput label, .stTextArea label, .stSlider label,
.stFileUploader label, .stToggle label {
  font-family: 'Tajawal', sans-serif !important;
  font-weight: 700 !important;
  color: rgba(212,175,55,0.9) !important;
  font-size: 0.92rem !important;
  letter-spacing: 0.5px !important;
}
p, .stMarkdown p, .stCaption { color: rgba(220,205,185,0.85) !important; font-family: 'Tajawal', sans-serif !important; }
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
textarea {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext !important;
  font-family: 'Amiri', 'Tajawal', 'Arial Unicode MS', Arial, sans-serif !important;
  font-size: 1.05rem !important;
  line-height: 1.9 !important;
  letter-spacing: 0.5px !important;
}
input[type="text"] { direction: ltr !important; text-align: left !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.01); }
::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(212,175,55,0.4), rgba(212,175,55,0.2));
  border-radius: 3px;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0d0820 0%, #080514 100%) !important;
  border-right: 1px solid rgba(212,175,55,0.2) !important;
}
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

@media print {
  @page { size: A5 portrait; margin: 0; }
  body > * { display: none !important; }
  iframe { display: block !important; border: none !important; }
  .print-report {
    display: block !important;
    position: fixed !important;
    top: 0; left: 0;
    width: 148mm !important;
    min-height: 210mm !important;
    margin: 0 !important;
    padding: 10mm !important;
    box-shadow: none !important;
    border: none !important;
    box-sizing: border-box !important;
  }
  .print-report button { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Hero Banner ──
st.markdown("""
<div class="hero-banner">
  <div style="font-family:'Amiri',serif;font-size:0.85rem;color:rgba(212,175,55,0.45);letter-spacing:12px;margin-bottom:0.6rem;">بِسْمِ اللَّهِ</div>
  <div class="hero-arabic">مُقيِّم الكتابة العربية</div>
  <div class="hero-english">Arabic Writing Assessor</div>
  <div style="width:120px;height:1px;background:linear-gradient(90deg,transparent,rgba(212,175,55,0.5),transparent);margin:0.9rem auto;"></div>
  <div style="font-family:'Tajawal',sans-serif;font-size:0.9rem;color:rgba(180,160,220,0.7);margin-top:0.8rem;">
    ✦ &nbsp; Enhanced OCR • Smart Spelling • A5 Print Reports &nbsp; ✦
  </div>
</div>
""", unsafe_allow_html=True)

# ── Global RTL enforcer ──
components.html("""
<script>
(function globalRTL() {
  function applyRTL() {
    var sel = window.parent.document.querySelectorAll('textarea');
    sel.forEach(function(ta) {
      ta.setAttribute('dir', 'rtl');
      ta.style.direction   = 'rtl';
      ta.style.textAlign   = 'right';
      ta.style.unicodeBidi = 'plaintext';
      ta.style.fontFamily  = "'Amiri','Tajawal',Arial,sans-serif";
      ta.style.fontSize    = '1.05rem';
      ta.style.lineHeight  = '1.85';
    });
  }
  applyRTL();
  var observer = new MutationObserver(applyRTL);
  observer.observe(window.parent.document.body, { childList: true, subtree: true });
})();
</script>
""", height=0)

# =============================================
# LAYOUT
# =============================================
col_left, col_right = st.columns([1, 1], gap="large")

# ── Accepted file types ──
ALL_FILE_TYPES = ["png", "jpg", "jpeg", "heic", "heif", "webp", "bmp",
                  "pdf", "doc", "docx", "txt", "csv"]

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
        st.markdown(
            f'<div class="rubric-badge">📊 Rubric applied: <strong>{rubric_key} Years of Study</strong></div>',
            unsafe_allow_html=True
        )
    else:
        st.warning("No rubric found for this year range.")

    st.divider()

    # ── LO ──
    st.markdown('<div class="section-title">🎯 Learning Objective (LO)</div>', unsafe_allow_html=True)
    lo_text = st.text_area("Type the LO here", height=100,
        placeholder="e.g. Student can write a descriptive paragraph about their daily routine using past tense.")
    lo_img = st.file_uploader(
        "📷 Or upload LO (image / PDF / Word / TXT)",
        type=ALL_FILE_TYPES, key="lo_img",
        help="Upload any file containing the Learning Objective"
    )
    if lo_img:
        with st.spinner("🔍 Reading Learning Objective..."):
            try:
                lo_extracted = extract_arabic_from_image_gemini(lo_img)
                if lo_extracted:
                    st.success("✅ LO extracted")
                    lo_text = lo_extracted
                    st.text_area("Extracted LO (edit if needed):", value=lo_extracted, height=80, key="lo_preview")
                else:
                    st.warning("⚠️ Could not extract text from file")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

    # ── SC ──
    st.markdown('<div class="section-title">✅ Success Criteria</div>', unsafe_allow_html=True)
    sc_text = st.text_area("Type Success Criteria here", height=100,
        placeholder="e.g. Uses at least 3 connectives, writes 6-8 lines, uses past and present tense.")
    sc_img = st.file_uploader(
        "📷 Or upload SC (image / PDF / Word / TXT)",
        type=ALL_FILE_TYPES, key="sc_img",
        help="Upload any file containing the Success Criteria"
    )
    if sc_img:
        with st.spinner("🔍 Reading Success Criteria..."):
            try:
                sc_extracted = extract_arabic_from_image_gemini(sc_img)
                if sc_extracted:
                    st.success("✅ Success Criteria extracted")
                    sc_text = sc_extracted
                    st.text_area("Extracted SC (edit if needed):", value=sc_extracted, height=80, key="sc_preview")
                else:
                    st.warning("⚠️ Could not extract text from file")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

    # ── Word Bank ──
    st.markdown(
        '<div class="section-title">📚 Word Bank <span style="font-size:0.75rem;opacity:0.6;font-weight:400">(Optional)</span></div>',
        unsafe_allow_html=True
    )
    use_word_bank = st.toggle("Enable Word Bank / Vocabulary List", value=False)
    word_bank_text = ""

    if use_word_bank:
        st.caption("💡 Spelling corrections will be based primarily on word-bank vocabulary. AI will also check which words the student used and suggest specific unused words as next steps.")
        wb_tab1, wb_tab2 = st.tabs(["✏️ Type Words", "📂 Upload Any File"])

        with wb_tab1:
            word_bank_text = st.text_area(
                "Type words (one per line or comma-separated)",
                height=120,
                placeholder="e.g. بالإضافة إلى ذلك، على الرغم من، في المقابل، لذلك، ومن ثم",
            )

        with wb_tab2:
            st.caption("📸 Upload a photo, PDF, Word doc, CSV, or TXT file of your word bank")
            wb_imgs = st.file_uploader(
                "Upload word bank file(s)",
                type=ALL_FILE_TYPES,
                key="wb_img",
                accept_multiple_files=True,
                help="Accepts: JPG, PNG, HEIC, PDF, Word (doc/docx), CSV, TXT, WEBP, BMP"
            )
            if wb_imgs:
                all_wb_words = []
                with st.spinner(f"🔍 Reading {len(wb_imgs)} file(s)..."):
                    for i, wb_img in enumerate(wb_imgs):
                        try:
                            extracted_words = extract_arabic_from_image_gemini(wb_img)
                            if extracted_words and extracted_words.strip():
                                all_wb_words.append(extracted_words.strip())
                                st.success(f"✅ File {i+1} read successfully")
                            else:
                                st.warning(f"⚠️ No words found in file {i+1}")
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
            "اكتب أو الصق النص العربي هنا — Paste or type the student's Arabic writing (reads right-to-left ←)",
            height=260,
            placeholder="اكتب هنا...",
        )
        if writing_typed.strip():
            writing = writing_typed

    with writing_tab2:
        st.info("📸 **ENHANCED OCR** — Now reads even poor/messy handwriting!")
        st.caption("📱 Supports: JPG, PNG, HEIC (iPhone), PDF, Word, WEBP, BMP, TXT, CSV")
        writing_imgs = st.file_uploader(
            "Upload handwriting photo(s) or document",
            type=ALL_FILE_TYPES,
            key="writing_img",
            accept_multiple_files=True
        )
        if writing_imgs:
            img_exts = ["png", "jpg", "jpeg", "heic", "heif", "webp", "bmp"]
            for i, writing_img in enumerate(writing_imgs):
                if any(writing_img.name.lower().endswith(ext) for ext in img_exts):
                    st.image(writing_img, caption=f"📄 Page {i+1}: {writing_img.name}", use_column_width=True)

            all_extracted = []
            with st.spinner(f"🔍 Reading {len(writing_imgs)} file(s) with ENHANCED OCR..."):
                for i, writing_img in enumerate(writing_imgs):
                    try:
                        extracted = extract_arabic_from_image_gemini(writing_img)
                        if extracted:
                            all_extracted.append(extracted)
                            st.success(f"✅ File {i+1} extracted!")
                        else:
                            st.warning(f"⚠️ Could not extract text from file {i+1}")
                    except Exception as e:
                        st.error(f"❌ Error reading file {i+1}: {str(e)}")

            if all_extracted:
                extracted_writing = "\n".join(all_extracted)
                auto_corrections = []
                if word_bank_text.strip():
                    auto_corrections = smart_spelling_matcher(extracted_writing, word_bank_text)

                st.markdown("""
<div style="background:linear-gradient(135deg,rgba(212,175,55,0.25),rgba(212,175,55,0.15));
            border:2px solid #d4af37;border-radius:16px;padding:18px 22px;margin:12px 0;
            box-shadow:0 4px 12px rgba(212,175,55,0.2)">
  <div style="font-size:16px;color:#ffd54f;letter-spacing:2px;font-weight:900;margin-bottom:10px">
    📝 OCR EXTRACTED TEXT — REVIEW CAREFULLY
  </div>
  <div style="font-size:14px;color:#ffffff;line-height:1.6">
    ⚠️ AI read the handwriting below. Please review and fix any mistakes before assessment.
  </div>
</div>""", unsafe_allow_html=True)

                if auto_corrections:
                    with st.expander(f"🔧 Smart Spelling: {len(auto_corrections)} potential corrections from word bank"):
                        for corr in auto_corrections[:7]:
                            priority_emoji = "🔴" if corr["priority"] == "high" else "🟡"
                            st.markdown(f"{priority_emoji} `{corr['wrong']}` → `{corr['correct']}`")

                # RTL enforcer for the textarea
                components.html("""
<script>
(function applyRTL() {
  function setRTL() {
    document.querySelectorAll('textarea').forEach(function(ta) {
      ta.setAttribute('dir', 'rtl');
      ta.style.direction   = 'rtl';
      ta.style.textAlign   = 'right';
      ta.style.unicodeBidi = 'plaintext';
      ta.style.fontFamily  = "'Amiri','Tajawal',Arial,sans-serif";
      ta.style.fontSize    = '1.05rem';
      ta.style.lineHeight  = '1.9';
    });
  }
  setRTL();
  var obs = new MutationObserver(setRTL);
  obs.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", height=0)

                corrected_writing = st.text_area(
                    "✏️ مراجعة النص المستخرج — Review & correct (Arabic reads right-to-left ←):",
                    value=extracted_writing,
                    height=260,
                    key="corrected_writing",
                    placeholder="سيظهر النص العربي هنا بعد المعالجة..."
                )
                writing = corrected_writing if corrected_writing.strip() else extracted_writing
                if corrected_writing.strip() != extracted_writing.strip():
                    st.success("✅ Using your manually corrected version")
                elif auto_corrections:
                    st.info(f"💡 {len(auto_corrections)} spelling suggestions found")

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

    if name.strip() and writing.strip() and rubric_key:
        word_count = len(writing.split())
        wb_count   = len([w for w in word_bank_text.split('\n') if w.strip()]) if word_bank_text.strip() else 0
        st.markdown(f"""
<div style="background:rgba(212,175,55,0.08);border:1px solid rgba(212,175,55,0.3);
            border-radius:10px;padding:12px;margin-top:10px;
            font-size:11px;color:rgba(220,205,185,0.9)">
  <div style="font-weight:700;color:#d4af37;margin-bottom:6px;font-size:12px">📋 READY TO ASSESS:</div>
  <div>✓ Student: <strong>{name.strip()}</strong> (Year {year})</div>
  <div>✓ Writing: <strong>~{word_count} words</strong></div>
  <div>✓ Rubric: <strong>{rubric_key} years</strong></div>
  {f'<div>✓ Word Bank: <strong>{wb_count} words</strong></div>' if wb_count > 0 else '<div style="opacity:0.6">○ No word bank</div>'}
  {f'<div>✓ Success Criteria: <strong>Provided</strong></div>' if sc_text.strip() else '<div style="opacity:0.6">○ No success criteria</div>'}
</div>
""", unsafe_allow_html=True)

# =============================================
# ASSESSMENT OUTPUT WITH A5 PRINT REPORT
# =============================================
if assess_btn:
    st.divider()
    with st.spinner(f"✨ Assessing {name.strip().split()[0]}'s writing..."):
        try:
            prompt = build_prompt(
                name=name.strip(), year=year,
                lo=lo_text.strip(), sc=sc_text.strip(),
                writing=writing.strip(),
                rubric_key=rubric_key, rubric=rubric_text,
                word_bank=word_bank_text.strip() if use_word_bank else ""
            )
            result = assess_with_gemini(prompt)

            import json, re
            try:
                clean = re.sub(r"```json|```", "", result).strip()
                data  = json.loads(clean)
            except Exception:
                data = None

            if data:
                www        = data.get("www", [])
                ebi        = data.get("ebi", [])
                next_steps = data.get("next_steps", [])
                sc_check   = data.get("sc_check", [])
                score      = data.get("score", {})

                # ── Filter spelling: keep only Arabic→Arabic entries ──────
                raw_spelling = data.get("spelling", [])

                def is_arabic(text: str) -> bool:
                    return any('\u0600' <= ch <= '\u06FF' for ch in text)

                def normalize_ar(t: str) -> str:
                    t = re.sub(r'[أإآٱ]', 'ا', t)
                    t = re.sub(r'[ةه]$',  'ه', t)
                    t = re.sub(r'[ىي]$',  'ي', t)
                    return t

                spelling = []
                for s in raw_spelling:
                    w = s.get("wrong",   "").strip()
                    c = s.get("correct", "").strip()
                    if not (is_arabic(w) and is_arabic(c)):
                        continue
                    if normalize_ar(w) == normalize_ar(c):
                        continue
                    spelling.append({"wrong": w, "correct": c})
                    if len(spelling) >= 5:
                        break

                # ── Deduplicate next_steps ────────────────────────────────
                seen_ns = set()
                deduped_next_steps = []
                for ns in next_steps:
                    ns_key = re.sub(r'\s+', ' ', ns.lower().strip())[:60]
                    if ns_key not in seen_ns:
                        seen_ns.add(ns_key)
                        deduped_next_steps.append(ns)
                next_steps = deduped_next_steps[:3]

                # ── Deduplicate EBI ───────────────────────────────────────
                seen_ebi = set()
                deduped_ebi = []
                for e in ebi:
                    e_key = re.sub(r'\s+', ' ', e.lower().strip())[:60]
                    if e_key not in seen_ebi:
                        seen_ebi.add(e_key)
                        deduped_ebi.append(e)
                ebi = deduped_ebi[:2]

                first_name = name.strip().split()[0] if name.strip() else name

                # ── Word Bank Usage Analysis ──────────────────────────────
                wb_analysis = ""
                if word_bank_text.strip():
                    wb_words = set()
                    for line in word_bank_text.strip().split('\n'):
                        for word in line.replace(',', ' ').split():
                            clean_w = word.strip()
                            if clean_w and len(clean_w) > 1:
                                wb_words.add(clean_w)
                    used_words   = [w for w in wb_words if w in writing]
                    unused_words = [w for w in wb_words if w not in writing]
                    if used_words or unused_words:
                        used_html   = " ".join([
                            f"<span style='background:#c8e6c9;padding:2px 6px;border-radius:4px;"
                            f"margin:2px;display:inline-block;font-family:\"Amiri\",serif;"
                            f"direction:rtl'>{w}</span>" for w in used_words[:10]
                        ])
                        unused_html = " ".join([
                            f"<span style='background:#ffcdd2;padding:2px 6px;border-radius:4px;"
                            f"margin:2px;display:inline-block;font-family:\"Amiri\",serif;"
                            f"direction:rtl'>{w}</span>" for w in unused_words[:10]
                        ])
                        wb_analysis = f"""
<div style="margin:16px 0;padding:12px;background:rgba(212,175,55,0.05);
            border:1px solid rgba(212,175,55,0.2);border-radius:10px">
  <div style="font-size:13px;font-weight:700;color:#d4af37;margin-bottom:8px">
    📚 WORD BANK USAGE ANALYSIS
  </div>
  {f'<div style="margin-bottom:6px"><span style="font-weight:700;color:#2e7d32">✓ Used ({len(used_words)}):</span><div style="margin-top:4px">{used_html}</div></div>' if used_words else ''}
  {f'<div><span style="font-weight:700;color:#c62828">○ Not used yet ({len(unused_words)}):</span><div style="margin-top:4px">{unused_html}</div></div>' if unused_words else ''}
</div>"""

                # ── Level colour map ──────────────────────────────────────
                level_colors = {
                    "Beginning":   "#8b0000",
                    "Developing":  "#b8600a",
                    "Accomplished":"#0a5c8b",
                    "Advanced":    "#155724",
                    "Exemplary":   "#4a0080"
                }
                lvl       = score.get("level", "Developing")
                lvl_color = level_colors.get(lvl, "#5a4000")

                # ══════════════════════════════════════════════════════════
                # BUILD HTML REPORT
                # ══════════════════════════════════════════════════════════
                www_rows = "".join([f"""
  <tr>
    <td style="padding:6px 10px;font-size:11px;line-height:1.5;
               border-bottom:1px solid rgba(76,175,80,0.12)">
      <span style="color:#2e7d32;font-weight:700;margin-left:4px">★</span> {w}
    </td>
  </tr>""" for w in www])

                ebi_rows = "".join([f"""
  <tr>
    <td style="padding:6px 10px;font-size:11px;line-height:1.5;
               border-bottom:1px solid rgba(229,115,115,0.12)">
      <span style="color:#c62828;font-weight:700;margin-left:4px">↗</span> {e}
    </td>
  </tr>""" for e in ebi])

                next_steps_rows = "".join([f"""
  <tr>
    <td style="padding:6px 10px;font-size:11px;line-height:1.5;
               border-bottom:1px solid rgba(156,39,176,0.12)">
      <span style="color:#6a1b9a;font-weight:700;margin-left:4px">►</span> {ns}
    </td>
  </tr>""" for ns in next_steps])

                if spelling:
                    spell_rows = "".join([f"""
  <tr style="border-bottom:1px solid rgba(139,0,0,0.08)">
    <td style="padding:5px 10px;font-size:14px;color:#2e7d32;font-weight:700;
               font-family:'Amiri',serif;direction:rtl;text-align:right">
      {s.get('correct','')}
    </td>
    <td style="padding:5px 6px;font-size:12px;color:#888;text-align:center">←</td>
    <td style="padding:5px 10px;font-size:14px;color:#c62828;
               font-family:'Amiri',serif;direction:rtl;text-align:right;text-decoration:line-through">
      {s.get('wrong','')}
    </td>
  </tr>""" for s in spelling])
                    spelling_section = f"""
<div style="margin-top:12px">
  <div style="font-size:10px;color:#8b0000;font-weight:700;letter-spacing:1px;
              margin-bottom:5px;border-bottom:2px solid rgba(139,0,0,0.2);padding-bottom:3px">
    KEY SPELLING CORRECTIONS
  </div>
  <div style="font-size:9px;color:#888;margin-bottom:4px;text-align:right;direction:rtl">التصحيح ← الخطأ</div>
  <table style="width:100%;border-collapse:collapse;direction:rtl">
    <tbody>{spell_rows}</tbody>
  </table>
</div>"""
                else:
                    spelling_section = """
<div style="margin-top:12px;padding:6px 10px;background:#e8f5e9;border-radius:6px;
            border:1px solid #4caf50;font-size:10px;color:#2e7d32;text-align:center">
  🎉 No major spelling errors detected
</div>"""

                html_report = f"""
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
<div class="print-report" style="
  width:555px;background:#ffffff;border:2px solid #d4af37;border-radius:10px;
  padding:18px 22px 20px;margin:10px auto;font-family:'Tajawal',sans-serif;
  font-size:11.5px;color:#2c1810;
  box-shadow:0 6px 20px rgba(0,0,0,0.18);box-sizing:border-box;">

  <!-- Header -->
  <div style="text-align:center;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid #d4af37">
    <div style="font-size:9px;color:#b8941f;letter-spacing:3px;font-weight:700;
                margin-bottom:3px;text-transform:uppercase">Arabic Writing Assessment</div>
    <div style="font-family:'Amiri',serif;font-size:26px;color:#2c1810;font-weight:700;margin:2px 0">
      {first_name}
    </div>
    <div style="font-size:9px;color:#5a4000;font-weight:600;letter-spacing:1px">
      YEAR {year} &nbsp;·&nbsp; {year} YEARS OF STUDY &nbsp;·&nbsp; {datetime.now().strftime('%d %b %Y')}
    </div>
  </div>

  <!-- Score Badge -->
  <div style="margin-bottom:14px;padding:10px 14px;background:rgba(212,175,55,0.07);
              border-radius:8px;border:1px solid rgba(212,175,55,0.35);
              display:flex;align-items:center;gap:14px">
    <div style="text-align:center;min-width:64px;border-right:2px solid rgba(212,175,55,0.25);
                padding-right:14px;flex-shrink:0">
      <div style="font-size:30px;font-weight:900;color:#b8941f;line-height:1">
        {score.get('score','?')}<span style="font-size:13px;color:rgba(184,148,31,0.6)">/{score.get('out_of',15)}</span>
      </div>
      <div style="font-size:8px;color:#b8941f;font-weight:700;letter-spacing:1px;margin-top:2px">SCORE</div>
    </div>
    <div style="flex:1">
      <div style="display:inline-block;background:{lvl_color};color:white;font-size:8px;
                  font-weight:700;letter-spacing:1px;padding:3px 12px;border-radius:12px;
                  margin-bottom:5px;text-transform:uppercase">{lvl}</div>
      <div style="font-size:10px;color:#3a2010;line-height:1.4">{score.get('reason','')}</div>
    </div>
  </div>

  <!-- WWW -->
  <div style="margin-bottom:11px">
    <div style="font-size:10px;color:#2e7d32;letter-spacing:1px;font-weight:700;
                margin-bottom:5px;border-bottom:2px solid rgba(76,175,80,0.3);padding-bottom:3px">
      ★ WHAT WENT WELL
    </div>
    <table style="width:100%;border-collapse:collapse;background:#f1f8e9;border-radius:6px;overflow:hidden">
      <tbody>{www_rows}</tbody>
    </table>
  </div>

  <!-- EBI -->
  <div style="margin-bottom:11px">
    <div style="font-size:10px;color:#c62828;letter-spacing:1px;font-weight:700;
                margin-bottom:5px;border-bottom:2px solid rgba(229,115,115,0.3);padding-bottom:3px">
      ↗ EVEN BETTER IF YOU...
    </div>
    <table style="width:100%;border-collapse:collapse;background:#ffebee;border-radius:6px;overflow:hidden">
      <tbody>{ebi_rows}</tbody>
    </table>
  </div>

  <!-- NEXT STEPS -->
  <div style="margin-bottom:11px">
    <div style="font-size:10px;color:#6a1b9a;letter-spacing:1px;font-weight:700;
                margin-bottom:5px;border-bottom:2px solid rgba(156,39,176,0.3);padding-bottom:3px">
      ► SPECIFIC TARGETS FOR NEXT TIME
    </div>
    <table style="width:100%;border-collapse:collapse;background:#f3e5f5;border-radius:6px;overflow:hidden">
      <tbody>{next_steps_rows}</tbody>
    </table>
  </div>

  <!-- SPELLING -->
  {spelling_section}

  <!-- Footer -->
  <div style="margin-top:14px;padding:8px 12px;background:rgba(212,175,55,0.05);
              border-radius:6px;border:1px solid rgba(212,175,55,0.2);text-align:center">
    <div style="font-size:9px;color:#5a4000;line-height:1.5">
      Keep up the great work! Focus on the targets above for your next writing task. 💫
    </div>
  </div>
</div>"""

                print_button_html = """
<div style="text-align:center;margin:16px 0">
  <button onclick="window.print()" style="
    background:linear-gradient(160deg,#f0d060 0%,#d4af37 35%,#b8941f 70%,#9a7a10 100%);
    color:#0d0a02;font-family:'Tajawal',sans-serif;font-weight:900;font-size:14px;
    letter-spacing:2px;border:none;border-radius:12px;padding:12px 32px;cursor:pointer;
    box-shadow:0 6px 0 #5a4000,0 8px 20px rgba(0,0,0,0.4);">
    🖨️ PRINT A5 REPORT
  </button>
  <div style="font-size:11px;color:#b8941f;margin-top:8px;font-family:'Tajawal',sans-serif">
    Click to print or save as PDF &nbsp;(Ctrl+P / Cmd+P)
  </div>
</div>"""

                if wb_analysis:
                    st.markdown(wb_analysis, unsafe_allow_html=True)
                components.html(html_report + print_button_html, height=1020, scrolling=True)

                # ── TXT download ──────────────────────────────────────────
                txt_lines = [
                    "ARABIC WRITING ASSESSMENT REPORT",
                    "=" * 60,
                    f"Student: {name.upper()}",
                    f"Year: {year} ({year} years of Arabic study)",
                    f"Date: {datetime.now().strftime('%d/%m/%Y')}",
                    "=" * 60 + "\n",
                    f"SCORE: {score.get('score','?')}/{score.get('out_of',15)} — {score.get('level','')}",
                    f"{score.get('reason','')}\n",
                    "=" * 60,
                    "★ WHAT WENT WELL:",
                ]
                for w in www:
                    txt_lines.append(f"  ★ {w}")
                txt_lines.append("\n↗ EVEN BETTER IF YOU...")
                for e in ebi:
                    txt_lines.append(f"  ↗ {e}")
                txt_lines.append("\n► SPECIFIC TARGETS FOR NEXT TIME:")
                for ns in next_steps:
                    txt_lines.append(f"  ► {ns}")
                if spelling:
                    txt_lines.append("\n✏️ KEY SPELLING CORRECTIONS:")
                    for s in spelling:
                        txt_lines.append(f"  {s.get('wrong','')} ← {s.get('correct','')}")
                txt_lines += ["\n" + "=" * 60, "Keep up the great work!", "=" * 60]

            else:
                st.error("❌ Could not parse assessment results. Please try again.")
                txt_lines = [result]

            st.divider()
            st.download_button(
                label="⬇️ Download Feedback Report (TXT)",
                data="\n".join(txt_lines),
                file_name=f"feedback_{name.strip().replace(' ', '_')}.txt",
                mime="text/plain"
            )

        except ValueError as e:
            st.error(f"❌ API Key error: {str(e)}")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
