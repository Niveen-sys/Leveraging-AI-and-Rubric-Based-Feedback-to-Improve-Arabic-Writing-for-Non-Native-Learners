import streamlit as st
from groq import Groq
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
    """Extract Arabic/English text from an uploaded image or PDF using OCR."""
    try:
        filename = uploaded_file.name.lower()
        if filename.endswith(".pdf") and PDF_SUPPORTED:
            data = uploaded_file.read()
            doc = fitz.open(stream=data, filetype="pdf")
            all_text = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img, lang="eng+ara")
                if text.strip():
                    all_text.append(text.strip())
            return "\n".join(all_text)
        else:
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
    tip_count = 3 if year <= 4 else 4
    level_note = get_level_note(year)
    word_bank_section = f"""Word bank provided: {word_bank}
- Praise words the student used from this list
- Suggest 2-3 unused words that fit their writing
- Include: ### 📚 Word Bank — ✅ Used: [...] | 💡 Try next: [...]""" if word_bank.strip() else "No word bank — skip Word Bank section."

    common_mistakes_guide = """
COMMON MISTAKES FOR NON-NATIVE ARABIC LEARNERS (predict and address these):

ADJECTIVE PLACEMENT:
- Wrong: "كتاب أحمر" should be checked if correct — actually this IS correct
- Watch for: adjectives BEFORE nouns when they should be after
- Example error: "أحمر كتاب" (red book) instead of "كتاب أحمر"
- Hint in feedback: remind student adjectives come AFTER nouns in Arabic

MASCULINE/FEMININE AGREEMENT:
- Adjectives must agree with nouns: "كتاب أحمر" (masc) vs "سيارة حمراء" (fem)
- Verb subjects must agree: "هو يكتب" (he writes) vs "هي تكتب" (she writes)
- Common error: using masculine form with feminine subject or vice versa
- Watch for: mismatched adjective/noun endings or verb/subject agreement

VERB CONJUGATION & SUBJECT AGREEMENT:
- Present tense: يكتب (he), تكتب (she/you), أكتب (I), نكتب (we)
- Past tense: كتب (he), كتبت (she), كتبت (I), كتبنا (we)
- Common errors: wrong pronoun suffixes, wrong tense markers, non-agreement with subject
- Watch for: sentences where verb doesn't match the subject's person/number/gender

PRONOUN SUFFIXES:
- Object pronouns attach to verbs/prepositions: "رأيته" (I saw him), "في المنزل" (in the house)
- Common error: forgetting or misplacing the suffix

PREPOSITIONS & CASE ENDINGS:
- "في" (in), "من" (from), "إلى" (to) affect noun endings
- Genitive case after prepositions: "في البيت" not "في البيتْ"
- Watch for: wrong case endings after prepositions

If you spot ANY of these patterns, mention them specifically in the "Improve This" section.
"""

    return f"""You are a concise Arabic writing teacher. Give focused, specific feedback. No padding. No repetition.

Student: {first_name} | Years of Arabic: {year} ({rubric_key} rubric) | Level: {level_note}
LO: {lo if lo.strip() else "Not provided"}
Success Criteria: {sc if sc.strip() else "Not provided"}
Rubric: {rubric}

{common_mistakes_guide}

{f"Word Bank: {word_bank_section}" if word_bank.strip() else ""}
Student Writing: {writing}

SPELLING RULE: Only flag words you are 100% certain are misspelled. Never flag correct Arabic words. When in doubt, skip it.

OUTPUT — be brief and direct:

### 👋 {first_name}
One specific warm sentence about their writing.

### ⭐ What Went Well
- **Strength 1:** (tied to their writing)
- **Strength 2:** (tied to their writing)

### 🔴 Improve This
> Quote: "exact student quote"
> Issue: Grammar / Spelling / Vocabulary / Structure / Adjective Placement / Masculine-Feminine Agreement / Verb Conjugation
> Fix hint: one sentence guiding them — no full answer
> Predict: If you see patterns of a common mistake type (adjective order, gender agreement, verb conjugation), mention it here.

### ✏️ Spelling
Only real errors:
- ❌ wrong → ✅ correct — [why]
Or: ✅ No spelling errors found.

### 📐 Grammar & Common Mistakes
1-2 issues only if clearly present:
- [Issue]: [specific to this student's writing]
(Examples: adjective placement, masculine/feminine mismatch, verb not matching subject, preposition + case ending)

{"### 📚 Word Bank" if word_bank.strip() else ""}
{"- ✅ Used: [...] | 💡 Try next: [2-3 words]" if word_bank.strip() else ""}

### 🟢 Top {tip_count} Tips
Short, actionable, specific to this student:
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
| Sentence Structure | | |
| Grammar/Spelling | | |
| **TOTAL** | | **/15** |

### 💪 Next Step
"Next time, try to..." — one sentence only.
"""

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
CRITICAL SPELLING RULES — READ CAREFULLY:
- You must ONLY flag words that are genuinely misspelled in Arabic
- Do NOT flag correct Arabic words as errors
- Do NOT flag proper nouns, names, or numbers as errors
- Do NOT flag words just because they are informal or colloquial
- If you are not 100% certain a word is wrong, do NOT include it
- Double-check every word before listing it as an error
- It is better to miss a real error than to falsely flag a correct word
───────────────────────────────────────────

OUTPUT FORMAT (follow exactly):

### 👋 Hello, {first_name}!
One warm sentence referencing something specific and positive from their actual writing.

---

### ⭐ WWW — What Went Well
- **Strength 1:** (specific to their writing)
- **Strength 2:** (specific to their writing)

---

### 🔴 EBI — Even Better If
> **Quote:** "exact quote from student writing"
> **Issue:** Grammar / Spelling / Vocabulary / Structure
> **Explanation:** One clear sentence explaining the problem
> **Hint:** Guide toward the fix without giving the full answer

---

### ✏️ Spelling Corrections
IMPORTANT: Only list words you are 100% certain are misspelled.
Format:
- ❌ [misspelled] → ✅ [correct] — [brief reason in English]

If no real errors found: "✅ No spelling errors found — great job!"

---

### 📐 Grammar Notes
List 1-2 grammar issues only if clearly present:
- [Issue]: [Brief explanation and example from their writing]

If no grammar issues: skip this section.

---

### 📚 Word Bank Suggestions
(Only if word bank was provided)
- ✅ Used from word bank: [words they used]
- 💡 Try next time: [2-3 specific words from the bank that fit their topic]

---

### 🏗️ Structure Advice
1-2 sentences of structure advice based on rubric for {year} years of study.

---

### 🟡 Success Criteria Check
(Only if Success Criteria provided — otherwise skip)
- ✔ [Criterion met]
- ✖ [Criterion not yet met]

---

### 🟢 Top {tip_count} Tips to Improve
Specific and actionable — tied to THIS student's writing:
1.
2.
3.
{"4.\n5." if tip_count == 5 else ""}

---

### 🔵 Rubric Assessment
| Category | Level | Score |
|---|---|---|
| Purpose/Content | [level] | [x]/3 |
| Organization | [level] | [x]/3 |
| Vocabulary | [level] | [x]/3 |
| Sentence Structure | [level] | [x]/3 |
| Grammar/Spelling | [level] | [x]/3 |
| **TOTAL** | **[Overall Level]** | **[x]/15** |

**Summary:** 2 sentences explaining the score based on the rubric.

---

### 💪 Next Step
"Next time, try to..." + one warm motivational closing line to {first_name}.

───────────────────────────────────────────
STRICT RULES:
- NEVER rewrite the student's full text
- NEVER flag correct Arabic words as spelling errors
- Keep tone warm, honest, and encouraging
- Tie ALL feedback to the student's actual writing
- Adapt ALL expectations to {year} years of study level
"""


def get_api_key() -> str:
    """Retrieve Groq API key from secrets or environment."""
    api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in secrets or environment.")
    return api_key


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


def extract_arabic_from_image_gemini(uploaded_file) -> str:
    """Use Groq Vision to extract Arabic handwriting from any uploaded file."""
    api_key = get_api_key()
    client = Groq(api_key=api_key)

    images = convert_to_pil_image(uploaded_file)

    all_text = []
    for img in images:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        b64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                        },
                        {
                            "type": "text",
                            "text": """This image contains handwritten Arabic text written by a student.
Please transcribe ALL the Arabic text exactly as written — including any spelling mistakes.
Do NOT correct errors. Do NOT add punctuation that is not there.
Return ONLY the Arabic text, nothing else."""
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        all_text.append(response.choices[0].message.content.strip())

    return "\n".join(all_text)


def share_to_teams(student_name: str, report: str, teams_webhook: str) -> bool:
    """Send report to Microsoft Teams via webhook."""
    try:
        import requests
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"Arabic Writing Assessment - {student_name}",
            "themeColor": "d4af37",
            "title": f"📝 Writing Assessment for {student_name}",
            "sections": [
                {
                    "activityTitle": f"مُقيِّم الكتابة العربية",
                    "activitySubtitle": f"Student: {student_name}",
                    "text": report[:3000]  # Teams has char limit
                }
            ]
        }
        response = requests.post(teams_webhook, json=message, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ Teams error: {str(e)}")
        return False


def share_to_email(student_name: str, teacher_email: str, student_email: str, report: str) -> bool:
    """Send report via email using SMTP."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import pandas as pd
        
        # Get SMTP config from secrets
        smtp_server = st.secrets.get("SMTP_SERVER", "")
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        sender_email = st.secrets.get("SENDER_EMAIL", "")
        sender_password = st.secrets.get("SENDER_PASSWORD", "")
        
        if not all([smtp_server, sender_email, sender_password]):
            st.error("❌ Email configuration not set in secrets.")
            return False
        
        # Create email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌙 Arabic Writing Assessment - {student_name}"
        msg["From"] = sender_email
        msg["To"] = teacher_email
        if student_email:
            msg["Cc"] = student_email
        
        html = f"""
        <html>
          <body style="font-family: Tajawal, Arial; direction: rtl; color: #333;">
            <h2 style="color: #d4af37;">مُقيِّم الكتابة العربية</h2>
            <h3>Writing Assessment Report for {student_name}</h3>
            <pre style="white-space: pre-wrap; word-wrap: break-word; background: #f5f5f5; padding: 1rem; border-radius: 8px;">
{report}
            </pre>
            <p style="margin-top: 2rem; border-top: 1px solid #ddd; padding-top: 1rem; font-size: 0.9rem; color: #666;">
              Sent from Arabic Writing Assessor
            </p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            recipients = [teacher_email]
            if student_email:
                recipients.append(student_email)
            server.sendmail(sender_email, recipients, msg.as_string())
        
        return True
    except Exception as e:
        st.error(f"❌ Email error: {str(e)}")
        return False


def assess_with_gemini(prompt: str) -> str:
    """Call Groq API and return the assessment text."""
    api_key = get_api_key()
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    return response.choices[0].message.content


# =============================================
# STREAMLIT UI
# =============================================

st.set_page_config(
    page_title="مُقيِّم الكتابة العربية",
    page_icon="🌙",
    layout="wide"
)

# --- Rich Arabic-Inspired CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Scheherazade+New:wght@400;700&family=Tajawal:wght@300;400;700;900&family=Cinzel+Decorative:wght@700&display=swap');

    /* ── Base & Background ── */
    .stApp {
        background: linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 40%, #0d1a2e 100%);
        min-height: 100vh;
    }

    /* Geometric Arabic pattern overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image:
            repeating-linear-gradient(45deg, rgba(212,175,55,0.04) 0px, rgba(212,175,55,0.04) 1px, transparent 1px, transparent 40px),
            repeating-linear-gradient(-45deg, rgba(212,175,55,0.04) 0px, rgba(212,175,55,0.04) 1px, transparent 1px, transparent 40px),
            repeating-linear-gradient(0deg, rgba(212,175,55,0.02) 0px, rgba(212,175,55,0.02) 1px, transparent 1px, transparent 80px),
            repeating-linear-gradient(90deg, rgba(212,175,55,0.02) 0px, rgba(212,175,55,0.02) 1px, transparent 1px, transparent 80px);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Hero Header ── */
    .hero-banner {
        background: linear-gradient(135deg, #1a0a2e 0%, #2d1554 50%, #1a0a2e 100%);
        border: 2px solid rgba(212,175,55,0.5);
        border-radius: 24px;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(212,175,55,0.4), 0 0 80px rgba(212,175,55,0.05);
    }

    .hero-banner::before {
        content: "بِسْمِ اللهِ الرَّحْمٰنِ الرَّحِيْمِ";
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(212,175,55,0.4);
        font-family: 'Scheherazade New', serif;
        font-size: 0.85rem;
        letter-spacing: 3px;
        white-space: nowrap;
    }

    .hero-banner::after {
        content: "❧ ✦ ❧";
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        color: rgba(212,175,55,0.5);
        font-size: 1rem;
        letter-spacing: 8px;
    }

    /* Arabic corner decorations */
    .hero-corner-tl, .hero-corner-tr, .hero-corner-bl, .hero-corner-br {
        position: absolute;
        width: 40px;
        height: 40px;
        border-color: rgba(212,175,55,0.4);
        border-style: solid;
    }

    .hero-arabic {
        font-family: 'Scheherazade New', serif;
        font-size: 3.2rem;
        font-weight: 700;
        color: #d4af37;
        text-shadow: 0 0 40px rgba(212,175,55,0.5), 0 2px 4px rgba(0,0,0,0.8), 0 0 80px rgba(212,175,55,0.2);
        margin: 0.5rem 0 0 0;
        line-height: 1.3;
    }

    .hero-english {
        font-family: 'Cinzel Decorative', serif;
        font-size: 1.1rem;
        color: rgba(212,175,55,0.85);
        margin-top: 0.5rem;
        letter-spacing: 4px;
        text-transform: uppercase;
    }

    .hero-sub {
        font-family: 'Tajawal', sans-serif;
        font-size: 0.9rem;
        color: rgba(200,200,255,0.6);
        margin-top: 0.8rem;
    }

    .hero-divider {
        width: 200px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(212,175,55,0.6), transparent);
        margin: 1rem auto;
    }

    /* ── Section Cards ── */
    .section-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(212,175,55,0.25);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
        position: relative;
    }

    .section-card::before {
        content: '';
        position: absolute;
        top: 0; left: 20px; right: 20px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(212,175,55,0.5), transparent);
    }

    .section-title {
        font-family: 'Tajawal', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #d4af37;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: 1px;
    }

    /* ── Rubric Badge ── */
    .rubric-badge {
        background: linear-gradient(135deg, rgba(212,175,55,0.15), rgba(212,175,55,0.05));
        border: 1px solid rgba(212,175,55,0.4);
        border-left: 4px solid #d4af37;
        padding: 0.7rem 1rem;
        border-radius: 10px;
        font-family: 'Tajawal', sans-serif;
        font-size: 0.9rem;
        color: #d4af37;
        margin-top: 0.5rem;
        box-shadow: 0 4px 15px rgba(212,175,55,0.1);
    }

    /* ── Input Fields (general) ── */
    .stTextArea textarea, .stSelectbox select {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(212,175,55,0.3) !important;
        border-radius: 10px !important;
        color: #f0e6d3 !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }

    .stTextArea textarea:focus {
        border-color: #d4af37 !important;
        box-shadow: 0 0 0 2px rgba(212,175,55,0.2), 0 4px 20px rgba(212,175,55,0.1) !important;
        background: rgba(255,255,255,0.08) !important;
    }

    /* ── Student Name Input — BLACK background ── */
    div[data-testid="stTextInput"] input {
        background: #000000 !important;
        border: 2px solid #d4af37 !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        padding: 0.6rem 1rem !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #f0d060 !important;
        box-shadow: 0 0 0 3px rgba(212,175,55,0.3), 0 4px 20px rgba(212,175,55,0.2) !important;
        background: #111111 !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: rgba(212,175,55,0.5) !important;
    }

    /* ── 3D Assess Button ── */
    .stButton > button {
        background: linear-gradient(145deg, #d4af37, #b8941f) !important;
        color: #0d0d1a !important;
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 900 !important;
        font-size: 1.1rem !important;
        letter-spacing: 2px !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.8rem 2rem !important;
        box-shadow:
            0 6px 0 #8a6a10,
            0 8px 20px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.3) !important;
        transform: translateY(0) !important;
        transition: all 0.15s ease !important;
        text-transform: uppercase !important;
        cursor: pointer !important;
    }

    .stButton > button:hover {
        background: linear-gradient(145deg, #e8c84a, #d4af37) !important;
        box-shadow:
            0 4px 0 #8a6a10,
            0 6px 15px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.4) !important;
        transform: translateY(2px) !important;
    }

    .stButton > button:active {
        box-shadow:
            0 1px 0 #8a6a10,
            0 2px 8px rgba(0,0,0,0.4) !important;
        transform: translateY(5px) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        border: 1px solid rgba(212,175,55,0.2) !important;
        gap: 4px !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 700 !important;
        color: rgba(212,175,55,0.6) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(212,175,55,0.25), rgba(212,175,55,0.1)) !important;
        color: #d4af37 !important;
        box-shadow: 0 2px 8px rgba(212,175,55,0.2) !important;
    }

    /* ── Labels & Text ── */
    .stTextInput label, .stTextArea label, .stSlider label, .stFileUploader label {
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 700 !important;
        color: rgba(212,175,55,0.9) !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px !important;
    }

    p, .stMarkdown, .stCaption {
        color: rgba(220,210,200,0.85) !important;
        font-family: 'Tajawal', sans-serif !important;
    }

    h1, h2, h3 {
        font-family: 'Tajawal', sans-serif !important;
        color: #d4af37 !important;
    }

    /* ── Feedback Output Box ── */
    .feedback-box {
        background: linear-gradient(145deg, rgba(26,10,46,0.95), rgba(13,13,26,0.95));
        border: 2px solid rgba(212,175,55,0.4);
        border-radius: 20px;
        padding: 2.5rem;
        margin-top: 1.5rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(212,175,55,0.2), 0 0 40px rgba(212,175,55,0.05);
        position: relative;
    }

    .feedback-box::before {
        content: "❧ تقييم الطالب ❧";
        position: absolute;
        top: -14px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #d4af37, #b8941f);
        color: #0d0d1a;
        font-family: 'Tajawal', sans-serif;
        font-weight: 900;
        font-size: 0.85rem;
        padding: 3px 20px;
        border-radius: 20px;
        letter-spacing: 2px;
        white-space: nowrap;
        box-shadow: 0 4px 15px rgba(212,175,55,0.3);
    }

    /* Arabic ornament divider inside feedback */
    .feedback-box hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(212,175,55,0.4), transparent) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Info / Success / Warning boxes ── */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid rgba(212,175,55,0.2) !important;
        background: rgba(255,255,255,0.04) !important;
    }

    /* ── Divider ── */
    hr {
        border-color: rgba(212,175,55,0.2) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
    ::-webkit-scrollbar-thumb { background: rgba(212,175,55,0.3); border-radius: 3px; }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: linear-gradient(145deg, rgba(212,175,55,0.15), rgba(212,175,55,0.05)) !important;
        border: 1px solid rgba(212,175,55,0.4) !important;
        color: #d4af37 !important;
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 0 rgba(212,175,55,0.2), 0 6px 15px rgba(0,0,0,0.3) !important;
    }

    .stDownloadButton > button:hover {
        background: linear-gradient(145deg, rgba(212,175,55,0.25), rgba(212,175,55,0.1)) !important;
        transform: translateY(2px) !important;
        box-shadow: 0 2px 0 rgba(212,175,55,0.2), 0 4px 10px rgba(0,0,0,0.3) !important;
    }

    /* ── File uploader ── */
    .stFileUploader {
        border: 1px dashed rgba(212,175,55,0.3) !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
        background: rgba(255,255,255,0.02) !important;
    }

    /* ── Arabic ornament decorations ── */
    .ornament-divider {
        text-align: center;
        color: rgba(212,175,55,0.5);
        font-size: 1.2rem;
        letter-spacing: 8px;
        margin: 0.5rem 0;
        font-family: 'Scheherazade New', serif;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Hero Banner ──
st.markdown("""
<div class="hero-banner">
    <div class="hero-arabic">مُقيِّم الكتابة العربية</div>
    <div class="hero-divider"></div>
    <div class="hero-english">Arabic Writing Assessor</div>
    <div class="hero-sub">✦ تقييم ذكي للكتابة العربية لمتعلمي اللغة ✦</div>
</div>
""", unsafe_allow_html=True)

# =============================================
# LAYOUT
# =============================================
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-title">🌙 Student Profile</div>', unsafe_allow_html=True)
    name = st.text_input("Student Name", placeholder="e.g. Sara Ahmed")
    year = st.slider("Years of Learning Arabic", min_value=2, max_value=9, value=5)
    rubric_key, rubric_text = get_rubric_by_year(year)
    if rubric_key:
        st.markdown(f'<div class="rubric-badge">📊 Rubric: <strong>{rubric_key} Years of Study</strong></div>', unsafe_allow_html=True)
    else:
        st.warning("No rubric found for this year range.")

    st.divider()

    # ── LO ──
    st.markdown('<div class="section-title">🎯 Learning Objective (LO)</div>', unsafe_allow_html=True)
    lo_text = st.text_area("Type or paste LO", height=80, placeholder="e.g. Write a paragraph about daily routine using past tense.")
    lo_file = st.file_uploader("Or upload image / PDF", type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf"], key="lo_file")
    if lo_file:
        with st.spinner("Reading LO..."):
            extracted = extract_text_from_image(lo_file)
            if extracted:
                lo_text = extracted
                st.success("✅ LO extracted")
                st.caption(extracted[:200])
            else:
                st.warning("⚠️ Could not extract text — try a clearer image.")

    st.divider()

    # ── SC ──
    st.markdown('<div class="section-title">✅ Success Criteria</div>', unsafe_allow_html=True)
    sc_text = st.text_area("Type or paste Success Criteria", height=80, placeholder="e.g. Uses 3 connectives, 6-8 lines, past and present tense.")
    sc_file = st.file_uploader("Or upload image / PDF", type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf"], key="sc_file")
    if sc_file:
        with st.spinner("Reading Success Criteria..."):
            extracted = extract_text_from_image(sc_file)
            if extracted:
                sc_text = extracted
                st.success("✅ Success Criteria extracted")
                st.caption(extracted[:200])
            else:
                st.warning("⚠️ Could not extract text — try a clearer image.")

    st.divider()

    # ── Word Bank ──
    st.markdown('<div class="section-title">📚 Word Bank <span style="font-size:0.75rem;opacity:0.6;font-weight:400">(Optional)</span></div>', unsafe_allow_html=True)
    use_word_bank = st.toggle("Enable Word Bank", value=False)
    word_bank_text = ""
    if use_word_bank:
        word_bank_text = st.text_area(
            "Type or paste words (one per line or comma-separated)",
            height=100,
            placeholder="e.g. بالإضافة إلى ذلك، على الرغم من، لذلك، ومن ثم"
        )
        wb_file = st.file_uploader(
            "Or upload image / PDF / CSV / TXT",
            type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf","csv","txt"],
            key="wb_file"
        )
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
                    except Exception:
                        word_bank_text = content
                    st.success(f"✅ Loaded word bank from file")
                except Exception as e:
                    st.error(f"❌ {str(e)}")
            else:
                with st.spinner("Reading word bank..."):
                    extracted = extract_text_from_image(wb_file)
                    if extracted:
                        word_bank_text = extracted
                        st.success("✅ Word bank extracted from image/PDF")
                        st.caption(extracted[:200])
                    else:
                        st.warning("⚠️ Could not extract — try a clearer image.")

with col_right:
    st.markdown('<div class="section-title">✍️ Student Writing</div>', unsafe_allow_html=True)

    writing_tab1, writing_tab2 = st.tabs(["⌨️ Type / Paste", "📷 Upload Photo / PDF"])
    writing = ""

    with writing_tab1:
        writing_typed = st.text_area(
            "Paste or type student's Arabic writing",
            height=280,
            placeholder="اكتب هنا...",
        )
        if writing_typed.strip():
            writing = writing_typed

    with writing_tab2:
        st.caption("📱 Supports: JPG, PNG, HEIC, WEBP, BMP, PDF — single or multiple files")
        writing_imgs = st.file_uploader(
            "Upload handwriting photo(s) or PDF",
            type=["png","jpg","jpeg","heic","heif","webp","bmp","pdf"],
            key="writing_img",
            accept_multiple_files=True
        )
        if writing_imgs:
            all_extracted = []
            for i, f in enumerate(writing_imgs):
                st.image(f, caption=f"Page {i+1}: {f.name}", use_column_width=True)
            with st.spinner(f"🔍 Reading {len(writing_imgs)} file(s)..."):
                for i, f in enumerate(writing_imgs):
                    try:
                        extracted = extract_arabic_from_image_gemini(f)
                        if extracted:
                            all_extracted.append(extracted)
                            st.success(f"✅ File {i+1} read successfully")
                        else:
                            st.warning(f"⚠️ File {i+1}: no text found — try a clearer photo.")
                    except Exception as e:
                        st.error(f"❌ File {i+1}: {str(e)}")
            if all_extracted:
                writing = "\n".join(all_extracted)
                st.markdown("**📝 Extracted:**")
                st.caption(writing[:300])

    if writing.strip():
        st.caption(f"Word count: ~{len(writing.split())} words")

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
    with st.spinner(f"✨ Assessing {name.strip().split()[0]}'s writing with Groq..."):
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

            # ── Styled Report Display ──
            st.markdown("""
<style>
/* Report container */
.report-container {
    background: linear-gradient(145deg, #0f0f1f, #1a0a2e);
    border: 2px solid rgba(212,175,55,0.5);
    border-radius: 24px;
    padding: 2.5rem 3rem;
    margin-top: 1.5rem;
    position: relative;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(212,175,55,0.05);
}

.report-container::before {
    content: "❧ تقييم الطالب ❧";
    position: absolute;
    top: -16px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #d4af37, #b8941f);
    color: #0d0d1a;
    font-family: 'Tajawal', sans-serif;
    font-weight: 900;
    font-size: 0.9rem;
    padding: 4px 24px;
    border-radius: 20px;
    letter-spacing: 3px;
    white-space: nowrap;
    box-shadow: 0 4px 15px rgba(212,175,55,0.4);
}

/* Section headings h3 */
.report-container h3 {
    font-family: 'Tajawal', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(212,175,55,0.05));
    border-left: 4px solid #d4af37;
    border-radius: 8px;
    padding: 0.6rem 1rem !important;
    margin-top: 1.8rem !important;
    margin-bottom: 0.8rem !important;
    letter-spacing: 0.5px;
}

/* Paragraph text */
.report-container p {
    font-family: 'Tajawal', sans-serif !important;
    font-size: 1rem !important;
    color: rgba(230,220,210,0.95) !important;
    line-height: 1.8 !important;
    margin-bottom: 0.6rem !important;
}

/* List items */
.report-container li {
    font-family: 'Tajawal', sans-serif !important;
    font-size: 1rem !important;
    color: rgba(230,220,210,0.9) !important;
    line-height: 1.8 !important;
    margin-bottom: 0.4rem !important;
    padding-left: 0.3rem;
}

/* Bold text */
.report-container strong {
    color: #d4af37 !important;
    font-weight: 700 !important;
}

/* Blockquote (EBI quote) */
.report-container blockquote {
    background: rgba(212,175,55,0.08) !important;
    border-left: 4px solid #d4af37 !important;
    border-radius: 8px !important;
    padding: 1rem 1.2rem !important;
    margin: 0.8rem 0 !important;
    color: rgba(240,230,220,0.9) !important;
    font-style: normal !important;
}

/* Table (rubric assessment) */
.report-container table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 1rem 0 !important;
    font-family: 'Tajawal', sans-serif !important;
}

.report-container th {
    background: rgba(212,175,55,0.2) !important;
    color: #d4af37 !important;
    font-weight: 700 !important;
    padding: 0.6rem 1rem !important;
    border: 1px solid rgba(212,175,55,0.3) !important;
    font-size: 0.95rem !important;
}

.report-container td {
    padding: 0.5rem 1rem !important;
    border: 1px solid rgba(212,175,55,0.15) !important;
    color: rgba(230,220,210,0.9) !important;
    font-size: 0.95rem !important;
}

.report-container tr:last-child td {
    background: rgba(212,175,55,0.1) !important;
    color: #d4af37 !important;
    font-weight: 700 !important;
}

.report-container tr:nth-child(even) td {
    background: rgba(255,255,255,0.03) !important;
}

/* Horizontal rule */
.report-container hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(212,175,55,0.4), transparent) !important;
    margin: 1.2rem 0 !important;
}

/* Code inline */
.report-container code {
    background: rgba(212,175,55,0.1) !important;
    color: #d4af37 !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
}
</style>
""", unsafe_allow_html=True)

            st.markdown('<div class="report-container">', unsafe_allow_html=True)
            st.markdown(result)
            st.markdown('</div>', unsafe_allow_html=True)

            st.divider()

            # ── Sharing Section ──
            st.markdown('<div class="section-title">📤 Share Report</div>', unsafe_allow_html=True)
            
            share_col1, share_col2, share_col3 = st.columns([1, 1, 1])

            with share_col1:
                st.download_button(
                    label="⬇️ Download as .txt",
                    data=result,
                    file_name=f"feedback_{name.strip().replace(' ', '_')}.txt",
                    mime="text/plain"
                )

            with share_col2:
                if st.button("💬 Share to Teams", use_container_width=True):
                    teams_webhook = st.secrets.get("TEAMS_WEBHOOK", "")
                    if teams_webhook:
                        with st.spinner("Sending to Teams..."):
                            if share_to_teams(name.strip(), result, teams_webhook):
                                st.success("✅ Report sent to Teams!")
                            else:
                                st.error("❌ Failed to send to Teams.")
                    else:
                        st.info("⚠️ Teams webhook not configured. Add TEAMS_WEBHOOK to secrets.")

            with share_col3:
                if st.button("📧 Share via Email", use_container_width=True):
                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    teacher_email = st.text_input("Your email address", placeholder="teacher@example.com")
                    student_email = st.text_input("Student email (optional)", placeholder="student@example.com")
                    
                    if st.button("Send Email", use_container_width=True):
                        if teacher_email:
                            with st.spinner("Sending email..."):
                                if share_to_email(name.strip(), teacher_email, student_email, result):
                                    st.success("✅ Report sent via email!")
                                else:
                                    st.error("❌ Failed to send email. Check configuration.")
                        else:
                            st.warning("⚠️ Please enter your email address.")
                    st.markdown('</div>', unsafe_allow_html=True)

        except ValueError as e:
            st.error(f"❌ API Key error: {str(e)}")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
