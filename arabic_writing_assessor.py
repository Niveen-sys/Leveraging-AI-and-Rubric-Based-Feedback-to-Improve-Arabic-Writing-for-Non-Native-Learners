import streamlit as st
import streamlit.components.v1 as components
import requests as _requests
from groq import Groq
import os
import io
import re
import base64
import hashlib
import time
from datetime import datetime, date
from PIL import Image
# pytesseract removed — not available on Streamlit Cloud; Gemini handles all OCR

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
# GROQ MODEL CONFIG  (update here when Groq deprecates models)
# Checked against https://console.groq.com/docs/deprecations
# =============================================
GROQ_ASSESSMENT_MODELS = [
    "openai/gpt-oss-120b",   # primary
    "qwen/qwen3.8-27b",      # fallback
    "openai/gpt-oss-20b",    # light/fast fallback
]
GROQ_VISION_MODELS = [
    "qwen/qwen3.8-27b",      # multimodal (gpt-oss models are text-only)
]

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


def _get_next_step_examples(year: int) -> str:
    """Return year-appropriate concrete next step examples for the assessment prompt."""
    if year <= 3:
        return """  ✓ "Add one sentence using past tense — e.g. start with ذهبتُ إلى... or أكلتُ..."
  ✓ "Use the adjective جميل or كبير after a noun you already mentioned, e.g. بيت كبير"
  ✓ "Add the connective و or لكن to join two of your sentences"
  ✓ "Write one sentence about a family member using هو or هي instead of أنا"
  ✓ "Add a time phrase like كل يوم or في الصباح to one of your sentences"
  ✓ "Include one of these unused word bank words: [word] — use it to describe [topic]" """
    elif year <= 5:
        return """  ✓ "Add a sentence in the past tense with a time phrase, e.g. أمس، ذهبتُ إلى... لأن..."
  ✓ "Use the connective بعد ذلك or أيضاً to link your third and fourth sentences"
  ✓ "Add your opinion using أعتقد أن... or في رأيي... followed by a reason with لأن"
  ✓ "Write one sentence using a different subject (هو or هي) to describe someone else"
  ✓ "Use two adjectives together, e.g. المدرسة كبيرة وجميلة، to give more detail"
  ✓ "Add the negation لا or لم to one sentence to show contrast, e.g. لا أحب... لأن" """
    elif year <= 7:
        return """  ✓ "Add a conditional sentence using إذا... or لو... to extend your argument"
  ✓ "Write one sentence using the future tense سوف + verb to describe a plan or hope"
  ✓ "Use بالإضافة إلى ذلك or من ناحية أخرى to introduce a contrasting point"
  ✓ "Add a relative clause using الذي or التي to give more detail about a noun you mentioned"
  ✓ "Justify your opinion more fully: add لأن followed by TWO reasons connected with و"
  ✓ "Include a rhetorical question or هل to engage the reader at the start or end" """
    else:
        return """  ✓ "Open with a strong hook — a question, statistic, or bold statement — before your main argument"
  ✓ "Add a counter-argument paragraph: acknowledge the opposing view with يرى البعض أن... then refute with ولكن في رأيي..."
  ✓ "Use a passive construction مثل: يُعتبر، يُقال، يُلاحظ to vary your sentence structure"
  ✓ "Vary your connectives — replace و with علاوة على ذلك or فضلاً عن ذلك in at least one place"
  ✓ "Add a concluding paragraph that restates your thesis using different vocabulary (paraphrase, don't repeat)"
  ✓ "Use one idiomatic Arabic expression or proverb to strengthen your argument" """


def analyze_writing(writing: str) -> str:
    """
    Heuristic fact-sheet about the student's writing (tenses, connectives, etc.).
    It is given to the AI so that next steps target what is REALLY missing.
    These are hints, not proof: the AI is told to verify them against the text.
    """
    import re

    def n(t):  # normalise alef/yaa so matching is forgiving
        return re.sub(r'[أإآٱ]', 'ا', t).replace('ى', 'ي')

    text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', writing)  # strip tashkeel + tatweel
    raw_tokens = [t.strip('.,،؛:!?؟"()[]«»-') for t in text.split()]
    raw_tokens = [t for t in raw_tokens if t]
    tokens = [n(t) for t in raw_tokens]
    joined = " " + " ".join(tokens) + " "

    lines = [l for l in text.split('\n') if l.strip()]
    has_punct = bool(re.search(r'[.!?؟]', text))
    sentences = [x for x in re.split(r'[.!?؟]+', text.replace('\n', ' ')) if len(x.split()) >= 2]

    def find_words(vocab):
        seen = []
        for raw, tok in zip(raw_tokens, tokens):
            # also match words with the attached conjunction و (e.g. وأمس)
            if (tok in vocab or (tok.startswith("و") and tok[1:] in vocab)) and raw not in seen:
                seen.append(raw)
        return seen

    def find_phrases(phrases):
        return [p for p in phrases if f" {n(p)} " in joined]

    def fmt(label, found):
        if found:
            return f"- {label}: FOUND ({', '.join(found[:5])})"
        return f"- {label}: NONE detected"

    # Possible past-tense verbs: ends in ت / وا, not a plural noun (ات), not ال-noun, not a common noun
    not_verbs = {"بيت", "وقت", "صوت", "بنت", "اخت", "سبت", "ست", "زيت", "موت", "حوت", "انت", "كتت", "ملعت"}
    past = []
    for raw, tok in zip(raw_tokens, tokens):
        if len(tok) >= 4 and not tok.startswith("ال") and not tok.endswith("ات") \
                and tok not in not_verbs and (tok.endswith("ت") or tok.endswith("وا")):
            if raw not in past:
                past.append(raw)
    past += [w for w in find_words({"كان", "كانت", "كنت"}) if w not in past]

    past_time = find_words({"امس", "الماضي", "الماضيه", "الماضية"})
    future = find_words({"سوف"}) + [w for w in raw_tokens if w.startswith("سأ") and len(w) > 3][:2]
    connectives = find_words({"لان", "ولكن", "لكن", "ايضا", "ثم", "لذلك", "عندما", "بينما", "كذلك", "او", "حيث", "اذا", "لو", "وايضا"}) \
        + find_phrases(["بعد ذلك", "في النهاية", "بالاضافة الي ذلك", "من ناحية اخري"])
    # "لأن" with attached pronoun (لأنها، لأنه، ولأن...)
    for raw, tok in zip(raw_tokens, tokens):
        if (tok.startswith("لان") or tok.startswith("ولان")) and len(tok) <= 7 and raw not in connectives:
            connectives.append(raw)
    bare_waw = sum(1 for t in tokens if t == "و")
    if bare_waw:
        connectives.append(f"و ×{bare_waw}")
    time_phrases = find_words({"اليوم", "غدا", "دائما", "احيانا", "صباحا", "مساء", "عادة", "الان"}) \
        + find_phrases(["كل يوم", "في الصباح", "في المساء", "في الظهر", "الاسبوع الماضي", "في العطلة", "بعد المدرسة", "كل صباح"])
    negation = find_words({"لا", "لم", "لن", "ليس", "ليست", "لست"})
    opinion = find_words({"اعتقد", "اظن", "افضل", "احب", "احبه", "احبها", "يعجبني", "تعجبني"}) \
        + find_phrases(["في رايي", "من وجهة نظري"])
    other_subjects = find_words({"هو", "هي", "نحن", "هم", "هن"})
    preps = find_words({"في", "علي", "من", "الي", "مع", "عند", "عن", "بين"})
    questions = find_words({"هل", "ماذا", "لماذا", "كيف", "اين", "متي"})
    if "؟" in text and not questions:
        questions = ["؟"]

    out = [
        f"- Words: {len(tokens)} | Handwritten lines: {len(lines)} (a line break is NOT a sentence end — sentences often continue on the next line)"
        + (f" | Sentences by punctuation: {len(sentences)}" if has_punct else " | Sentence count not reliable (little or no punctuation — judge sentences by meaning)"),
        fmt("Past tense verbs (possible)", past),
        fmt("Past-time words", past_time),
        fmt("Future tense (سوف / سأ...)", future),
        fmt("Connectives", connectives),
        fmt("Time phrases", time_phrases),
        fmt("Negation (لا / لم / ليس)", negation),
        fmt("Opinion / likes (أحب / أعتقد / في رأيي)", opinion),
        fmt("Subjects other than أنا (هو / هي / نحن / هم)", other_subjects),
        fmt("Prepositions", preps),
        fmt("Question forms", questions),
    ]
    return "\n".join(out)


def build_prompt(name: str, year: int, lo: str, sc: str, writing: str, rubric_key: str, rubric: str, word_bank: str = '') -> str:
    first_name = name.strip().split()[0] if name.strip() else name
    level_note = get_level_note(year)
    word_bank_section = f"""Word Bank provided by teacher: {word_bank}
- CRITICAL: Check which words from the word bank the student DID use — praise them specifically in WWW
- CRITICAL: Identify 2-3 HIGH-IMPACT words from word bank they DIDN'T use that would strengthen their writing
- Use these unused words as specific next steps — name the EXACT Arabic word""" if word_bank.strip() else "No word bank provided."

    # Build year-specific next step instruction bank
    next_step_examples = _get_next_step_examples(year)
    analysis = analyze_writing(writing)

    return f"""
You are an experienced Arabic teacher marking a student's handwritten work.

═══════════════════════════════════════════════════
PART A — READ THE WRITING CAREFULLY FIRST
═══════════════════════════════════════════════════
Before writing any feedback, analyse what the student ACTUALLY wrote:

CHECKLIST — tick off what the student HAS already done:
□ Used past tense verbs (e.g. ذهبت، أكلت، لعبت)
□ Used present tense verbs (e.g. أذهب، أحب، يمكنني)
□ Used connectives (e.g. و، لأن، ولكن، أيضاً، ثم، بعد ذلك)
□ Used time phrases (e.g. كل يوم، في الصباح، أمس، الأسبوع الماضي)
□ Used adjectives (e.g. جميل، كبير، ممتع، مفيد)
□ Used personal pronouns (أنا، هو، هي، نحن)
□ Gave an opinion (أعتقد، أفضّل، في رأيي، أحب لأن)
□ Used word bank vocabulary (check each word from the bank)
□ Wrote more than 4 lines
□ Has an opening sentence
□ Has a closing/conclusion sentence
□ Used negation (لا، لم، ليس)
□ Used different subjects (not just أنا)
□ Used prepositions (في، على، من، إلى، مع، عند)
□ Used question forms

ONLY suggest things the student has NOT ticked off above.

AUTO-ANALYSIS OF THE WRITING (computer-detected hints — VERIFY each one against the actual text):
{analysis}

HOW TO USE THE AUTO-ANALYSIS:
  • "NONE detected" = probably missing. Re-read the text to confirm. If it is truly missing and appropriate for Year {year}, it is a TOP-PRIORITY next step (e.g. no past tense → "Add at least one sentence in the past tense, e.g. ذهبتُ إلى...").
  • "FOUND" = the student already did it. NEVER ask for it in EBI or next steps — praise it in WWW instead.
  • Detection is imperfect (OCR, handwriting, diacritics). If the text clearly shows the feature, trust the text over the analysis.
  • Do NOT judge by word count alone. Judge by what the student achieved.
  • LINE BREAKS: in Arabic handwriting a sentence often continues on the next line. Read the text as CONTINUOUS writing.
    A line break is NOT a sentence end, NOT a new paragraph, and must NOT be penalised or counted as a separate sentence.
    Never use the number of lines as evidence of length or quality; judge sentences by meaning and connectives.

═══════════════════════════════════════════════════
PART B — GENERATE FEEDBACK
═══════════════════════════════════════════════════
TEACHER STYLE EXAMPLE:
★ Amazing information expressed clearly using past tense
★ Nice opening & closure  
★ Excellent use of time adverbs & connectives
↗ Even better if you add a sentence using a different subject like هو or هي
↗ Even better if you use descriptive adjectives like كبير، جميل to describe nouns

YOUR FEEDBACK MUST:
1. Be written in English
2. Use ★ for WWW (2-3 points) — SHORT, specific to what the student ACTUALLY wrote
   - Reference actual words/sentences they used
   - Mention any word bank words they used successfully
3. Use ↗ for EBI (MAXIMUM 2 points) — MUST be specific and actionable
   - Start each with "Even better if you..."
   - Must target things GENUINELY MISSING from their writing (see checklist above)
4. Be appropriate for Year {year} student ({year} years of Arabic)

═══════════════════════════════════════════════════
PART C — NEXT STEPS (MOST IMPORTANT PART)
═══════════════════════════════════════════════════
Generate EXACTLY 2-3 next steps. Each must be:
  ✓ A CONCRETE, ACTIONABLE TASK — not a vague suggestion
  ✓ Based ONLY on things GENUINELY MISSING from the writing
  ✓ Specific to the student's level and the success criteria
  ✓ Something the student can DO in their next piece of writing

NEXT STEP FORMAT — each step must follow this pattern:
  "[Action verb] + [exact structure/word/grammar point] + [brief example in Arabic]"

GOOD EXAMPLES of well-formed next steps:
{next_step_examples}

BAD examples (too vague — NEVER write these):
  ✗ "Use more connectives"
  ✗ "Improve your vocabulary"
  ✗ "Write more sentences"
  ✗ "Use different tenses"
  ✗ "Add more detail"

ACCURACY RULE FOR NEXT STEPS:
  • Look at the AUTO-ANALYSIS above. Any feature marked NONE (and confirmed missing in the text)
    that the rubric/success criteria expect at Year {year} should become a next step FIRST.
  • Each next step = ONE small, doable task, e.g. "Add at least one sentence in the past tense,
    e.g. ذهبتُ إلى...".
  • Never ask for something the student already did.

NEXT STEP SOURCES — use in this priority order:
  1. UNMET SUCCESS CRITERIA → turn each unmet SC into a specific task
     e.g. SC says "use past tense" → "Write one sentence using past tense, e.g. ذهبتُ إلى..."
  2. UNUSED WORD BANK WORDS → name the exact word and where to use it
     e.g. "Add the word [Arabic word] to describe [noun from their writing]"
  3. NEXT RUBRIC LEVEL → identify the specific thing needed to reach the next level
     e.g. rubric says next level needs connectives → give exact connective + example
  4. PATTERN FROM THEIR WRITING → something they did once but could extend
     e.g. they used ذهبت once → "Add another past tense verb like لعبتُ or أكلتُ"

═══════════════════════════════════════════════════
PART D — SPELLING (STRICT RULES)
═══════════════════════════════════════════════════
Flag ONLY true spelling mistakes — wrong Arabic letters in Arabic script.
  • "wrong": the word exactly as the student wrote it (Arabic script only)
  • "correct": the correct Arabic spelling
  • SKIP: romanised text, English words, OCR artifacts
  • SKIP: ة/ه confusion, ى/ي confusion, hamza variations (أ/ا/إ) — these are not flagged
  • ONLY flag: wrong consonant used, missing essential letter, extra letter that changes meaning
  • USE CONTEXT: predict the intended word from word bank, topic, and surrounding text
  • MAXIMUM 5 corrections

═══════════════════════════════════════════════════
STUDENT INFO
═══════════════════════════════════════════════════
Student: {first_name} (Year {year} — {year} years of Arabic study)
Level: {level_note}
Learning Objective: {lo if lo.strip() else "Not provided."}
Success Criteria: {sc if sc.strip() else "Not provided."}
Rubric: {rubric}
{word_bank_section}

STUDENT WRITING:
{writing}

═══════════════════════════════════════════════════
SCORING
═══════════════════════════════════════════════════
Score each of the 5 rubric categories separately (Purpose/Content, Organization/Coherency,
Vocabulary, Sentence Structure, Grammar/Spelling) using:
  Beginning=1 | Developing=1.5 | Accomplished=2 | Advanced=2.5 | Exemplary=3

BE FAIR AND ENCOURAGING — follow these rules:
  1. BEST FIT, not "all or nothing": choose the descriptor that BEST matches the writing overall.
     The student does NOT need to meet every point in a descriptor. If the writing sits between
     two levels, choose the HIGHER one.
  2. Judge QUALITY and ACHIEVEMENT, not just quantity. Do not downgrade because of line counts
     or word counts: handwriting size varies. A clear, well-built short text can score highly.
  3. Give credit for effort and what the student did well in each category. One missing feature
     (e.g. no past tense) lowers ONLY the category it belongs to, not the whole score.
  4. Do NOT penalise OCR mistakes, handwriting, or the spelling variations listed as "SKIP" in Part D.
     Only clear spelling errors that change the meaning count in Grammar/Spelling.
  5. Calibration for a Year {year} student:
       • Coherent, on-topic writing that answers the task = at least Accomplished in every
         category (minimum 10/15).
       • Good writing with several of the rubric features present = 11–13 / 15.
       • Strong writing that nearly meets the top descriptors = 13.5–15 / 15.
       • Below 8/15 ONLY for very short, off-topic, or mostly unreadable writing.
  6. The "reason" must name the strongest category and the one category that most needs work.

OUTPUT — return ONLY this JSON (no markdown, no explanation):
{{
  "www": ["strength 1", "strength 2", "strength 3"],
  "ebi": ["Even better if you...", "Even better if you..."],
  "next_steps": ["concrete specific task 1", "concrete specific task 2", "concrete specific task 3"],
  "spelling": [{{"wrong": "arabic word as written", "correct": "correct arabic word"}}],
  "grammar": [{{"original": "sentence from writing", "issue": "what is wrong", "hint": "how to fix without giving the answer"}}],
  "sc_check": [{{"criterion": "...", "met": true, "comment": "..."}}],
  "category_scores": {{"purpose_content": 2, "organization": 2, "vocabulary": 2, "sentence_structure": 2, "grammar_spelling": 2}},
  "score": {{"level": "Beginning/Developing/Accomplished/Advanced/Exemplary", "score": 0, "out_of": 15, "reason": "brief reason"}}
}}
"""


# ── API Keys from Secrets File ──────────────────────────────────────────────

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

def get_google_api_keys() -> list:
    """Return all configured Google API keys (supports up to 3 for quota rotation)."""
    keys = []
    for var in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_2", "GOOGLE_API_KEY_3"]:
        k = _secret(var) or os.environ.get(var, "")
        if k:
            keys.append(k)
    if not keys:
        raise ValueError("❌ GOOGLE_API_KEY not found! Please add it to .streamlit/secrets.toml")
    return keys

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


def convert_to_pil_image(uploaded_file) -> list:
    """Convert any uploaded file (HEIC, PDF, JPG, PNG, DOCX, etc.) to a list of PIL Images."""
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
    elif filename.endswith(".docx") or filename.endswith(".doc"):
        # For DOCX: extract text directly
        if DOCX_SUPPORTED:
            data = uploaded_file.read()
            doc = python_docx.Document(io.BytesIO(data))
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            # Create a white image with the text rendered on it via PIL
            from PIL import ImageDraw, ImageFont
            img = Image.new("RGB", (800, max(400, len(text.split('\n')) * 30 + 60)), color="white")
            draw = ImageDraw.Draw(img)
            y = 20
            for line in text.split('\n'):
                draw.text((20, y), line, fill="black")
                y += 28
            images.append(img)
        else:
            raise ValueError("DOCX support not available. Please install python-docx.")
    else:
        img = Image.open(uploaded_file)
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)

    return images


def extract_text_from_docx(uploaded_file) -> str:
    """Extract text directly from a DOCX file without OCR."""
    if DOCX_SUPPORTED:
        data = uploaded_file.read()
        doc = python_docx.Document(io.BytesIO(data))
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    raise ValueError("python-docx not installed.")


def pil_image_to_base64(img) -> str:
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=90)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _list_gemini_models(api_key: str) -> list:
    """All Gemini models this key can call with generateContent."""
    for ver in ("v1beta", "v1"):
        try:
            resp = _requests.get(
                f"https://generativelanguage.googleapis.com/{ver}/models",
                headers={"x-goog-api-key": api_key},
                params={"pageSize": 200},
                timeout=10,
            )
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                names = [
                    m["name"].replace("models/", "")
                    for m in models
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                    and "gemini" in m.get("name", "").lower()
                ]
                if names:
                    return names
        except Exception:
            continue
    return []


def _rank_gemini_models(names: list) -> list:
    """
    Rank Gemini models for reading handwriting, best first.
    Newest 'flash' > 'pro' > 'lite'. Stable beats preview. Image/TTS/live/embedding models are skipped.
    This avoids hard-coding model names that Google later shuts down.
    """
    skip = ("image", "tts", "live", "audio", "embedding", "robotics", "computer-use",
            "omni", "native", "imagen", "veo", "lyria", "aqa", "learnlm", "gemma", "thinking")
    ranked = []
    for name in names:
        low = name.lower()
        if any(k in low for k in skip):
            continue
        m = re.match(r"^gemini-(\d+(?:\.\d+)?)-(pro|flash)(.*)$", low)
        if m:
            ver, family, rest = float(m.group(1)), m.group(2), m.group(3)
        else:
            m2 = re.match(r"^gemini-(pro|flash)(-lite)?-latest$", low)
            if not m2:
                continue
            ver, family, rest = 99.0, m2.group(1), (m2.group(2) or "")
        if "lite" in rest:
            tier = 0
        elif family == "flash":
            tier = 2
        else:
            tier = 1
        stable = 0 if ("preview" in rest or "exp" in rest) else 1
        ranked.append((tier, ver, stable, name))
    ranked.sort(reverse=True)
    return [r[3] for r in ranked]


def _gemini_models_for_ocr(api_key: str) -> list:
    """Pick up to 4 models: best 2 flash, best pro, best lite (so a quota hit on one still leaves options)."""
    ranked = _rank_gemini_models(_list_gemini_models(api_key))
    if not ranked:
        return ["gemini-flash-latest", "gemini-3.1-flash-lite"]
    flash = [n for n in ranked if "flash" in n and "lite" not in n]
    pro = [n for n in ranked if "pro" in n]
    lite = [n for n in ranked if "lite" in n]
    picked = flash[:2] + pro[:1] + lite[:1]
    return picked or ranked[:4]


def _limit_size(img: Image.Image, max_side: int = 3000) -> Image.Image:
    """Downscale very large phone photos (keeps upload fast, no loss of handwriting detail)."""
    w, h = img.size
    longest = max(w, h)
    if longest > max_side:
        scale = max_side / longest
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img


def _preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    """
    Gentle clean-up for handwriting photos:
    - fix phone rotation (EXIF)
    - upscale small images to ~1800px so thin strokes and dots are visible
    - remove shadows / uneven lighting (divide by blurred background)
    - auto-contrast + light unsharp mask
    NOTE: no harsh edge-enhance filter — it adds noise that looks like extra dots/strokes.
    """
    from PIL import ImageOps, ImageEnhance, ImageFilter

    img = ImageOps.exif_transpose(img)
    w, h = img.size
    longest = max(w, h)
    if longest < 1800:
        scale = 1800 / longest
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = _limit_size(img, 3000)

    grey = ImageOps.grayscale(img)

    # Remove shadows / uneven lighting
    try:
        import numpy as np
        arr = np.asarray(grey, dtype=np.float32)
        bg = np.asarray(grey.filter(ImageFilter.GaussianBlur(radius=max(grey.size) / 25)), dtype=np.float32)
        norm = np.clip(arr / np.maximum(bg, 1.0) * 235.0, 0, 255).astype(np.uint8)
        grey = Image.fromarray(norm)
    except Exception:
        pass

    grey = ImageOps.autocontrast(grey, cutoff=1)
    grey = ImageEnhance.Contrast(grey).enhance(1.3)
    grey = grey.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
    return grey.convert("RGB")


def _gemini_ocr_rest(img_b64: str, api_key: str, model: str, prompt: str) -> str:
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.0,      # faithful transcription, no creativity
            "topP": 0.9,
            "maxOutputTokens": 8192  # thinking models spend part of this on reasoning
        }
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    last = None
    for ver in ("v1beta", "v1"):
        url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent"
        resp = _requests.post(url, json=payload, headers=headers, timeout=90)
        if resp.status_code == 404:      # model not on this API version — try the other one
            last = f"404 {resp.text[:150]}"
            continue
        if resp.status_code != 200:
            raise RuntimeError(f"{resp.status_code} {resp.text[:200]}")
        data = resp.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError):
            reason = (data.get("candidates") or [{}])[0].get("finishReason", "unknown")
            raise RuntimeError(f"Empty response from {model} (finishReason={reason})")
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        return text.strip()
    raise RuntimeError(last or f"{model} not available")


# ── OCR prompt — multi-pass strategy ─────────────────────────────────────────
_OCR_PROMPT = """
You are an EXPERT Arabic handwriting recognition system specialising in NON-NATIVE student work.
Your ONLY job is to faithfully transcribe what the student wrote — preserving ALL their errors.

══════════════════════════════════════════════════════
STEP 1 — UNDERSTAND THE CONTEXT BEFORE READING
══════════════════════════════════════════════════════
Non-native Arabic students at school level typically write about these topics:
  • SELF / FAMILY: اسمي، عمري، أسرتي، أبي، أمي، أخي، أختي، بيتي
  • SCHOOL: مدرستي، الفصل، المعلم، الدروس، الواجب، الامتحان
  • HOBBIES: أحب، ألعب، أشاهد، الكرة، الموسيقى، القراءة، الرياضة
  • FOOD: أكل، أشرب، الطعام، الفاكهة، الخضروات، المطعم
  • DAILY ROUTINE: أستيقظ، أذهب، أعود، الصباح، المساء، كل يوم
  • DESCRIPTION: جميل، كبير، صغير، ممتع، مفيد، سعيد، ذكي
  • CONNECTIVES: و، لأن، ولكن، أيضاً، ثم، بعد ذلك، لذلك
  • TIME PHRASES: كل يوم، في الصباح، أمس، الأسبوع الماضي، في المستقبل

Common beginner vocabulary the student may have written (possibly with errors):
  ذهبت، لعبت، أكلت، شربت، رأيت، كتبت، قرأت، ساعدت
  يمكنني، أريد، أحتاج، أعتقد، أفضّل، أستمتع
  مع، في، على، من، إلى، عند، بين
  هذا، هذه، هناك، هنا، كثير، قليل، دائماً، أحياناً

══════════════════════════════════════════════════════
STEP 2 — SCAN THE WHOLE IMAGE FIRST
══════════════════════════════════════════════════════
• Count the lines. Identify title/heading (larger text at top).
• Note the topic from any clearly readable words — this is your context anchor.
• Note writing quality: are letters well-formed or hasty? Are dots often missing?
• Reading direction: ALWAYS right to left, line by line top to bottom.

══════════════════════════════════════════════════════
STEP 3 — READ WORD BY WORD USING THIS DECISION TREE
══════════════════════════════════════════════════════
For EVERY ambiguous word, work through this in order:

1. SKELETON FIRST — identify the letter shapes WITHOUT dots
   Core shapes: ا ب ح د ر س ص ط ع ف ق ك ل م ن ه و ي
   (dots are secondary — many students forget or misplace them)

2. POSITION SHAPES — each letter looks different at start / middle / end:
   ع: ع (start) → ـعـ (mid) → ـع (end)
   ه: هـ (start) → ـهـ (mid) → ـه (end)  
   ك: كـ → ـكـ → ـك
   ف: فـ → ـفـ → ـف (easy to confuse with ق)

3. DOT DECISION — after fixing the skeleton, add dots:
   1 dot below: ب
   2 dots above: ت  |  2 dots below: ي
   3 dots above: ث ش
   1 dot above: خ ذ ز ض ظ غ ف ن (check position carefully)
   2 dots above: ق
   NO dots: ا ح د ر س ص ط ع ك ل م و ه

   ⚠ STUDENT DOT ERRORS — very common, PRESERVE them:
   - ب written without dot (looks like ا with bump)
   - ن written without dot (looks like ي shape)
   - ي written with dots above (student wrote ت instead)
   - ة at end written as ه (VERY common — keep as written)
   - Dots above when they should be below, or vice versa

4. WORD RECOVERY — if a word is unclear, ask: 
   "Given the TOPIC and SURROUNDING WORDS, what common Arabic word would fit here?"
   Pick the best match from the vocabulary list in Step 1.
   Transcribe the word AS WRITTEN (including errors), not the corrected version.

5. NEVER CORRECT — preserve ALL of these exactly as written:
   • ة written as ه or ت at word-end
   • ى written as ي (or vice versa) at word-end  
   • Missing hamza: أ written as ا, إ written as ا, ؤ written as و, ئ written as ي
   • Wrong tense vowel patterns (كتبت vs كاتبت)
   • Wrong gender agreement (الولد الجميلة instead of الجميل)
   • Wrong case endings or tanwin
   • Repeated letters, missing letters, extra letters
   • Run-together words or incorrectly split words

══════════════════════════════════════════════════════
STEP 4 — HANDLE ESPECIALLY TRICKY PAIRS
══════════════════════════════════════════════════════
Pairs students confuse most — use CONTEXT to decide:
  ح / ج / خ  (same body, different dots)
  ر / ز       (ز has 1 dot above)
  د / ذ       (ذ has 1 dot above)
  س / ش      (ش has 3 dots above)
  ص / ض      (ض has 1 dot above-right)
  ط / ظ       (ظ has 1 dot above)
  ع / غ       (غ has 1 dot above)
  ف / ق       (ق has 2 dots above; ف has 1 dot above)
  ه / ة / ت   (at word-end, students mix these — keep as written)
  ك / ل       (in medial position, easily confused if handwriting is fast)

For NUMBERS mixed into text:
  Preserve Arabic-Indic numerals (١٢٣٤٥٦٧٨٩٠) exactly as written.

══════════════════════════════════════════════════════
STEP 5 — VERIFY BEFORE OUTPUTTING
══════════════════════════════════════════════════════
Read your transcription back:
  ✓ Does the right-to-left word order make sense for the topic?
  ✓ Are there any words you accidentally read left-to-right? (Fix them)
  ✓ Does each line have a plausible number of words for what you see?
  ✓ Did you preserve all errors (not silently fix them)?

══════════════════════════════════════════════════════
OUTPUT FORMAT — STRICT
══════════════════════════════════════════════════════
• Output ONLY the Arabic text — one transcribed line per written line.
• NO English words. NO explanations. NO tashkeel unless clearly visible.
• NO corrections. NO comments. NO confidence scores. NO [?] unless truly unreadable.
• Title/heading on its own line first if present.
• Preserve blank lines.

NOW TRANSCRIBE THE HANDWRITING:
"""


_OCR_EXTRA_RULES = """
══════════════════════════════════════════════════════
LINE BREAKS — IMPORTANT
══════════════════════════════════════════════════════
In Arabic school writing a sentence very often continues on the next line.
• Transcribe EACH physical line of handwriting on its OWN line, in order, top to bottom.
• Do NOT merge lines. Do NOT add full stops, commas or any punctuation the student did not write.
• The end of a line does NOT mean the end of a sentence.
• Read every line right-to-left, exactly as the student wrote it.
• If a word is truly unreadable write [؟] — never invent a word.
"""


def _ocr_context_block(context: str) -> str:
    if not context or not context.strip():
        return ""
    return (
        "\n══════════════════════════════════════════════════════\n"
        "TASK CONTEXT — use ONLY to help recognise ambiguous words.\n"
        "NEVER write a word from this list unless it is really written in the image:\n"
        + context.strip()[:1500] + "\n"
    )


def _build_ocr_prompt(context: str = "") -> str:
    head, _sep, _tail = _OCR_PROMPT.rpartition("NOW TRANSCRIBE THE HANDWRITING:")
    return head + _OCR_EXTRA_RULES + _ocr_context_block(context) + "\nNOW TRANSCRIBE THE HANDWRITING:\n"


def _build_refine_prompt(draft: str, context: str = "") -> str:
    return f"""You are proofreading a transcription of a NON-NATIVE student's Arabic handwriting.
Below is a DRAFT transcription of the attached image. Compare it with the handwriting LINE BY LINE (right to left).

Fix ONLY real reading mistakes:
  • wrong letters or wrong dots
  • words wrongly merged or split
  • missing or duplicated words or lines
KEEP the student's own spelling and grammar mistakes — do NOT correct them.
Do NOT add punctuation. Keep each physical line on its own line.
Output ONLY the final Arabic transcription — no comments, no English.
{_ocr_context_block(context)}
DRAFT:
{draft}
"""


def _clean_ocr_output(text: str) -> str:
    """Remove code fences and stray English commentary lines from the model output."""
    text = re.sub(r"```[a-zA-Z]*", "", text or "").replace("```", "")
    lines = []
    for line in text.splitlines():
        t = line.rstrip()
        if re.search(r"[A-Za-z]", t) and not re.search(r"[\u0600-\u06FF]", t):
            continue
        lines.append(t)
    return "\n".join(lines).strip()


def extract_arabic_from_image_gemini(uploaded_file, context: str = "") -> str:
    """
    ENHANCED OCR for Arabic handwriting — accepts all file types.
    Two passes: (1) transcribe, (2) proofread the draft against the image.
    `context` (LO / success criteria / word bank) only helps recognise ambiguous words.
    """
    filename = uploaded_file.name.lower()

    # ── Plain-text formats: no OCR needed ────────────────────────────────────
    if filename.endswith(".docx") or filename.endswith(".doc"):
        try:
            text = extract_text_from_docx(uploaded_file)
            if text.strip():
                return text
        except Exception:
            pass

    if filename.endswith(".txt"):
        try:
            uploaded_file.seek(0)
            return uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

    if filename.endswith(".csv"):
        try:
            uploaded_file.seek(0)
            return uploaded_file.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

    # ── Image / PDF path ─────────────────────────────────────────────────────
    file_hash = _image_hash(uploaded_file) + "-" + hashlib.md5((context or "").encode("utf-8")).hexdigest()[:8]
    cache = _get_ocr_cache()
    if file_hash in cache:
        return cache[file_hash]

    _check_limit("ocr")
    _rate_limit()

    api_keys = get_google_api_keys()
    prompt = _build_ocr_prompt(context)

    raw_images = convert_to_pil_image(uploaded_file)
    last_error = None
    quota_errors = 0
    all_text = []

    for img in raw_images:
        enhanced_b64 = pil_image_to_base64(_preprocess_image_for_ocr(img))
        orig_b64 = pil_image_to_base64(_limit_size(img, 3000))

        page_text = None
        used = None   # (api_key, model, image_b64) that worked — reused for the proofreading pass

        # Try every key × best-available models (cleaned image first, then original)
        for api_key in api_keys:
            if page_text:
                break
            models_to_try = _gemini_models_for_ocr(api_key)
            for b64 in [enhanced_b64, orig_b64]:
                if page_text:
                    break
                for model_name in models_to_try:
                    try:
                        text = _clean_ocr_output(_gemini_ocr_rest(b64, api_key, model_name, prompt))
                        if text:
                            page_text = text
                            used = (api_key, model_name, b64)
                            break
                    except Exception as e:
                        err_str = str(e).lower()
                        if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                            quota_errors += 1
                        last_error = e
                        continue

        if page_text and used:
            # ── Pass 2: proofread the draft against the image ──
            try:
                refined = _clean_ocr_output(
                    _gemini_ocr_rest(used[2], used[0], used[1], _build_refine_prompt(page_text, context))
                )
                if refined and len(refined) >= 0.6 * len(page_text):
                    page_text = refined
            except Exception:
                pass   # keep the first-pass draft
            all_text.append(page_text)
        else:
            # ── Gemini exhausted → try Groq vision as last resort ──
            try:
                groq_text = _clean_ocr_output(_groq_ocr_fallback(orig_b64, prompt))
                if groq_text:
                    all_text.append(groq_text)
                    continue  # success — move to next page
            except Exception as groq_err:
                last_error = groq_err

            # All methods failed — give clear guidance
            if quota_errors > 0:
                key_count = len(api_keys)
                extra = (
                    " You only have 1 API key configured — add GOOGLE_API_KEY_2 (and optionally GOOGLE_API_KEY_3) "
                    "in .streamlit/secrets.toml to automatically rotate keys when quota is hit."
                    if key_count == 1 else
                    f" All {key_count} configured Google API keys have hit their quota, and the Groq vision fallback also failed."
                )
                raise RuntimeError(
                    f"⚠️ Google Gemini quota exceeded — the free OCR limit has been reached for today.{extra}\n\n"
                    "💡 **Quick fix:** Switch to the '⌨️ Type / Paste Text' tab and paste the Arabic text manually, "
                    "or try again after midnight when the quota resets."
                )
            raise RuntimeError(
                f"OCR failed for this image. Last error: {last_error}\n\n"
                "💡 Try the '⌨️ Type / Paste Text' tab to paste the Arabic text manually."
            )

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


def _groq_ocr_fallback(img_b64: str, prompt_text: str = "") -> str:
    """
    Fallback OCR using Groq's vision models.
    Called automatically when Gemini fails or is quota-exhausted.
    Model list lives in GROQ_VISION_MODELS at the top of the file.
    """
    api_key = get_groq_api_key()
    client = Groq(api_key=api_key)

    if not prompt_text:
        prompt_text = (
            "You are an expert Arabic handwriting recognition system. "
            "Read the handwritten Arabic text in this image EXACTLY as written by the student — "
            "do NOT correct spelling mistakes, do NOT add tashkeel unless clearly visible. "
            "Keep each written line on its own line; do not add punctuation. "
            "Output ONLY the Arabic text. No English, no explanations, no comments."
        )

    last_error = None
    for model_name in GROQ_VISION_MODELS:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                        },
                        {"type": "text", "text": prompt_text}
                    ]
                }],
                max_tokens=3000,
                temperature=0.0,
            )
            result = response.choices[0].message.content.strip()
            if result:
                return result
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Groq vision OCR also failed. Last error: {last_error}")


def assess_with_gemini(prompt: str) -> str:
    """Runs the assessment on Groq (name kept for compatibility with the rest of the app)."""
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    cache = _get_assess_cache()
    if prompt_hash in cache:
        return cache[prompt_hash]

    _check_limit("assess")
    _rate_limit()

    api_key = get_groq_api_key()
    client = Groq(api_key=api_key)
    last_error = None
    for model_name in GROQ_ASSESSMENT_MODELS:
        try:
            kwargs = dict(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=6000,   # reasoning models spend part of this on thinking
                temperature=0.3,
            )
            if model_name.startswith("openai/gpt-oss"):
                kwargs["reasoning_effort"] = "low"
            response = client.chat.completions.create(**kwargs)
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

    ocr_count = usage.get("ocr", 0)
    assess_count = usage.get("assess", 0)
    ocr_pct = int(ocr_count / MAX_OCR_PER_DAY * 100)
    assess_pct = int(assess_count / MAX_ASSESS_PER_DAY * 100)

    ocr_color = "#d4af37" if ocr_pct < 70 else ("#ff9900" if ocr_pct < 90 else "#ff4444")
    assess_color = "#d4af37" if assess_pct < 70 else ("#ff9900" if assess_pct < 90 else "#ff4444")

    # Count configured API keys
    try:
        n_keys = len(get_google_api_keys())
    except Exception:
        n_keys = 0
    key_badge = f"🔑 {n_keys} API key{'s' if n_keys != 1 else ''} configured"
    key_color = "#4caf50" if n_keys >= 2 else ("#ff9900" if n_keys == 1 else "#ff4444")

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
        <div style="font-size:11px;color:{key_color};margin-top:6px;font-weight:700">{key_badge}</div>
        {'<div style="font-size:10px;color:rgba(255,153,0,0.7);margin-top:2px">Add GOOGLE_API_KEY_2 to secrets.toml to auto-rotate when quota hits</div>' if n_keys == 1 else ''}
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
        background: #ffffff !important;
        border: 1px solid rgba(212,175,55,0.4) !important;
        border-radius: 12px !important;
        color: #1a1a1a !important;
        font-family: 'Tajawal', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }

    /* Placeholder text — keep it subtle */
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #aaaaaa !important;
        font-weight: 400 !important;
    }

    /* Extracted preview fields (LO/SC/WB) — same white but with gold border highlight */
    .extracted-preview .stTextArea textarea {
        background: #fffdf5 !important;
        color: #111111 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: 2px solid rgba(212,175,55,0.8) !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 12px rgba(212,175,55,0.2) !important;
        direction: rtl !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #d4af37 !important;
        box-shadow:
            0 0 0 2px rgba(212,175,55,0.25),
            0 0 20px rgba(212,175,55,0.1) !important;
        background: #ffffff !important;
        outline: none !important;
    }

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

    .stTextInput label, .stTextArea label, .stSlider label, .stFileUploader label, .stToggle label {
        font-family: 'Tajawal', sans-serif !important;
        font-weight: 700 !important;
        color: rgba(212,175,55,0.9) !important;
        font-size: 0.92rem !important;
        letter-spacing: 0.5px !important;
    }

    p, .stMarkdown p, .stCaption {
        color: rgba(220,205,185,0.85) !important;
        font-family: 'Tajawal', sans-serif !important;
    }

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

    /* ── RTL for ALL textareas that contain Arabic content ── */
    textarea {
        direction: rtl !important;
        text-align: right !important;
        unicode-bidi: embed !important;
        font-family: 'Amiri', 'Tajawal', 'Arial Unicode MS', Arial, sans-serif !important;
        font-size: 1.05rem !important;
        line-height: 1.9 !important;
        letter-spacing: 0.5px !important;
    }

    [data-testid="stTextArea"] textarea,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="base-input"] textarea {
        direction: rtl !important;
        text-align: right !important;
        unicode-bidi: embed !important;
    }
    textarea::placeholder { text-align: right !important; direction: rtl !important; }

    /* Keep LTR for the student-name input (Latin text) */
    input[type="text"] {
        direction: ltr !important;
        text-align: left !important;
    }

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
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }

    /* ── Print styles: render ONLY .print-report at A5 ── */
    @media print {
        @page { size: A5 portrait; margin: 0; }

        /* Hide everything */
        body > * { display: none !important; }

        /* Show only the report iframe contents */
        iframe { display: block !important; border: none !important; }

        /* Inside the iframe the .print-report is already the only content */
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
    <div style="font-family:'Tajawal',sans-serif;font-size:0.9rem;color:rgba(180,160,220,0.7);margin-top:0.8rem;">✦ &nbsp; Enhanced OCR • Smart Spelling • A5 Print Reports &nbsp; ✦</div>
</div>
""", unsafe_allow_html=True)

# ── Global RTL enforcer for all Arabic textareas ──────────────────────────
components.html("""
<script>
(function globalRTL() {
    function applyRTL() {
        // Target all Streamlit textareas
        var sel = window.parent.document.querySelectorAll('textarea');
        sel.forEach(function(ta) {
            ta.setAttribute('dir', 'rtl');
            ta.style.direction      = 'rtl';
            ta.style.textAlign      = 'right';
            ta.style.unicodeBidi    = 'embed';
            ta.style.fontFamily     = "'Amiri','Tajawal',Arial,sans-serif";
            ta.style.fontSize       = '1.05rem';
            ta.style.lineHeight     = '1.85';
        });
    }
    // Run now and whenever the DOM changes (Streamlit re-renders on interaction)
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

# ── All accepted file types (unified) ──
ALL_FILE_TYPES = ["png", "jpg", "jpeg", "heic", "heif", "webp", "bmp",
                  "pdf", "doc", "docx", "txt", "csv"]

with col_left:
    st.markdown('<div class="section-title">🌙 Student Profile</div>', unsafe_allow_html=True)

    name = st.text_input("Student Name", placeholder="e.g. Sara Ahmed")

    year_group = st.text_input(
        "Year Group",
        placeholder="e.g. Year 7, Grade 5, Form 3B...",
        help="The student's school year group (e.g. Year 7). This appears on the report."
    )

    year = st.slider(
        "Years of Studying Arabic",
        min_value=2, max_value=9, value=5,
        help="Drag to select how many years the student has been studying Arabic"
    )

    rubric_key, rubric_text = get_rubric_by_year(year)
    if rubric_key:
        st.markdown(f'<div class="rubric-badge">📊 Rubric applied: <strong>{rubric_key} Years of Studying Arabic</strong></div>', unsafe_allow_html=True)
    else:
        st.warning("No rubric found for this year range.")

    st.divider()

    st.markdown('<div class="section-title">🎯 Learning Objective (LO)</div>', unsafe_allow_html=True)
    lo_text = st.text_area("Type the LO here", height=100, placeholder="e.g. Student can write a descriptive paragraph about their daily routine using past tense.")

    lo_img = st.file_uploader(
        "📷 Or upload LO (image / PDF / Word / TXT)",
        type=ALL_FILE_TYPES,
        key="lo_img",
        help="Upload any file containing the Learning Objective"
    )
    if lo_img:
        with st.spinner("🔍 Reading Learning Objective..."):
            try:
                lo_extracted = extract_arabic_from_image_gemini(lo_img)
                if lo_extracted:
                    st.success("✅ LO extracted")
                    lo_text = lo_extracted
                    st.markdown('<div class="extracted-preview">', unsafe_allow_html=True)
                    st.text_area("Extracted LO (edit if needed):", value=lo_extracted, height=80, key="lo_preview")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Could not extract text from file")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

    st.markdown('<div class="section-title">✅ Success Criteria</div>', unsafe_allow_html=True)
    sc_text = st.text_area("Type Success Criteria here", height=100, placeholder="e.g. Uses at least 3 connectives, writes 6-8 lines, uses past and present tense.")

    sc_img = st.file_uploader(
        "📷 Or upload SC (image / PDF / Word / TXT)",
        type=ALL_FILE_TYPES,
        key="sc_img",
        help="Upload any file containing the Success Criteria"
    )
    if sc_img:
        with st.spinner("🔍 Reading Success Criteria..."):
            try:
                sc_extracted = extract_arabic_from_image_gemini(sc_img)
                if sc_extracted:
                    st.success("✅ Success Criteria extracted")
                    sc_text = sc_extracted
                    st.markdown('<div class="extracted-preview">', unsafe_allow_html=True)
                    st.text_area("Extracted SC (edit if needed):", value=sc_extracted, height=80, key="sc_preview")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Could not extract text from file")
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

    st.markdown('<div class="section-title">📚 Word Bank <span style="font-size:0.75rem;opacity:0.6;font-weight:400">(Optional)</span></div>', unsafe_allow_html=True)
    use_word_bank = st.toggle("Enable Word Bank / Vocabulary List", value=False)
    word_bank_text = ""
    if use_word_bank:
        st.caption("💡 AI will check which words the student used and suggest specific unused words as next steps")
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
        st.caption("📱 Supports: JPG, PNG, HEIC (iPhone), PDF, Word, WEBP, BMP")
        writing_imgs = st.file_uploader(
            "Upload handwriting photo(s) or document",
            type=ALL_FILE_TYPES,
            key="writing_img",
            accept_multiple_files=True
        )
        if writing_imgs:
            all_extracted = []
            for i, writing_img in enumerate(writing_imgs):
                # Only show image preview for actual image files
                img_exts = ["png", "jpg", "jpeg", "heic", "heif", "webp", "bmp"]
                if any(writing_img.name.lower().endswith(ext) for ext in img_exts):
                    st.image(writing_img, caption=f"📄 Page {i+1}: {writing_img.name}", use_column_width=True)
            ocr_context = "\n".join(x.strip() for x in [lo_text, sc_text, word_bank_text] if x and x.strip())
            with st.spinner(f"🔍 Reading {len(writing_imgs)} file(s) with ENHANCED OCR..."):
                for i, writing_img in enumerate(writing_imgs):
                    try:
                        extracted = extract_arabic_from_image_gemini(writing_img, context=ocr_context)
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
<div style="background:linear-gradient(135deg,rgba(212,175,55,0.25),rgba(212,175,55,0.15));border:2px solid #d4af37;border-radius:16px;padding:18px 22px;margin:12px 0;box-shadow:0 4px 12px rgba(212,175,55,0.2)">
<div style="font-size:16px;color:#ffd54f;letter-spacing:2px;font-weight:900;margin-bottom:10px">📝 OCR EXTRACTED TEXT — REVIEW CAREFULLY</div>
<div style="font-size:14px;color:#ffffff;line-height:1.6">⚠️ AI read the handwriting below. Please review and fix any mistakes before assessment.</div>
</div>""", unsafe_allow_html=True)

                if auto_corrections:
                    with st.expander(f"🔧 Smart Spelling: {len(auto_corrections)} potential corrections from word bank"):
                        for corr in auto_corrections[:7]:
                            priority_emoji = "🔴" if corr["priority"] == "high" else "🟡"
                            st.markdown(f"{priority_emoji} `{corr['wrong']}` → `{corr['correct']}`")

                # ── RTL enforcer: inject JS once to set dir=rtl on all textareas ──
                components.html("""
<script>
(function applyRTL() {
    function setRTL() {
        document.querySelectorAll('textarea').forEach(function(ta) {
            ta.setAttribute('dir', 'rtl');
            ta.style.direction = 'rtl';
            ta.style.textAlign = 'right';
            ta.style.unicodeBidi = 'embed';
            ta.style.fontFamily = "'Amiri','Tajawal',Arial,sans-serif";
            ta.style.fontSize = '1.05rem';
            ta.style.lineHeight = '1.9';
        });
    }
    setRTL();
    // Observe DOM changes so new textareas also get RTL
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
        wb_count = len([w for w in word_bank_text.split('\n') if w.strip()]) if word_bank_text.strip() else 0
        st.markdown(f"""
        <div style="background:rgba(212,175,55,0.08);border:1px solid rgba(212,175,55,0.3);border-radius:10px;padding:12px;margin-top:10px;font-size:11px;color:rgba(220,205,185,0.9)">
            <div style="font-weight:700;color:#d4af37;margin-bottom:6px;font-size:12px">📋 READY TO ASSESS:</div>
            <div>✓ Student: <strong>{name.strip()}</strong>{(" — " + year_group.strip()) if year_group.strip() else ""} ({year} years studying Arabic)</div>
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

            import json, re
            try:
                clean = re.sub(r"```json|```", "", result).strip()
                data = json.loads(clean)
            except Exception:
                data = None

            if data:
                www       = data.get("www", [])
                ebi       = data.get("ebi", [])
                next_steps= data.get("next_steps", [])
                sc_check  = data.get("sc_check", [])
                score     = data.get("score", {}) or {}

                # ── Compute the total in Python from the 5 category scores (no AI arithmetic errors) ──
                cat = data.get("category_scores", {}) or {}
                cat_values = []
                for v in cat.values():
                    try:
                        cat_values.append(min(3.0, max(1.0, float(v))))
                    except (TypeError, ValueError):
                        continue
                if len(cat_values) == 5:
                    total = round(sum(cat_values) * 2) / 2   # nearest 0.5
                    avg = total / 5
                    if avg >= 2.75:
                        lvl_calc = "Exemplary"
                    elif avg >= 2.25:
                        lvl_calc = "Advanced"
                    elif avg >= 1.75:
                        lvl_calc = "Accomplished"
                    elif avg >= 1.25:
                        lvl_calc = "Developing"
                    else:
                        lvl_calc = "Beginning"
                    score["score"] = int(total) if total == int(total) else total
                    score["out_of"] = 15
                    score["level"] = lvl_calc

                # ── Filter spelling: keep only Arabic→Arabic entries ──
                raw_spelling = data.get("spelling", [])
                def is_arabic(text: str) -> bool:
                    """Return True if text contains any Arabic character."""
                    return any('\u0600' <= ch <= '\u06FF' for ch in text)

                spelling = []
                for s in raw_spelling:
                    w = s.get("wrong", "").strip()
                    c = s.get("correct", "").strip()
                    # Both sides must be Arabic, and they must differ (after ignoring hamza/taa marbuta/alef variants)
                    if not (is_arabic(w) and is_arabic(c)):
                        continue
                    # Skip if only hamza/alef variants differ: normalize and compare
                    def normalize_ar(t):
                        t = re.sub(r'[أإآٱ]', 'ا', t)
                        t = re.sub(r'[ةه]$', 'ه', t)
                        t = re.sub(r'[ىي]$', 'ي', t)
                        return t
                    if normalize_ar(w) == normalize_ar(c):
                        continue
                    spelling.append({"wrong": w, "correct": c})
                    if len(spelling) >= 5:
                        break

                first_name = name.strip().split()[0] if name.strip() else name

                # ── Word Bank Usage Analysis ──
                wb_analysis = ""
                if word_bank_text.strip():
                    wb_words = set()
                    for line in word_bank_text.strip().split('\n'):
                        for word in line.replace(',', ' ').split():
                            clean = word.strip()
                            if clean and len(clean) > 1:
                                wb_words.add(clean)
                    used_words   = [w for w in wb_words if w in writing]
                    unused_words = [w for w in wb_words if w not in writing]
                    if used_words or unused_words:
                        used_html   = " ".join([f"<span style='background:#c8e6c9;padding:2px 6px;border-radius:4px;margin:2px;display:inline-block;font-family:\"Amiri\",serif;direction:rtl'>{w}</span>" for w in used_words[:10]])
                        unused_html = " ".join([f"<span style='background:#ffcdd2;padding:2px 6px;border-radius:4px;margin:2px;display:inline-block;font-family:\"Amiri\",serif;direction:rtl'>{w}</span>" for w in unused_words[:10]])
                        wb_analysis = f"""
                        <div style="margin:16px 0;padding:12px;background:rgba(212,175,55,0.05);border:1px solid rgba(212,175,55,0.2);border-radius:10px">
                            <div style="font-size:13px;font-weight:700;color:#d4af37;margin-bottom:8px">📚 WORD BANK USAGE ANALYSIS</div>
                            {f'<div style="margin-bottom:6px"><span style="font-weight:700;color:#2e7d32">✓ Used ({len(used_words)}):</span><div style="margin-top:4px">{used_html}</div></div>' if used_words else ''}
                            {f'<div><span style="font-weight:700;color:#c62828">○ Not used yet ({len(unused_words)}):</span><div style="margin-top:4px">{unused_html}</div></div>' if unused_words else ''}
                        </div>"""

                # ── Level colour map ──
                level_colors = {
                    "Beginning":   "#8b0000",
                    "Developing":  "#b8600a",
                    "Accomplished":"#0a5c8b",
                    "Advanced":    "#155724",
                    "Exemplary":   "#4a0080"
                }
                lvl       = score.get("level", "Developing")
                lvl_color = level_colors.get(lvl, "#5a4000")

                # ══════════════════════════════════════════
                # BUILD HTML REPORT  (matches on-screen UI)
                # Spelling table: mistake on RIGHT (Arabic RTL), correction on LEFT
                # ══════════════════════════════════════════
                www_rows = "".join([f"""
                <tr>
                  <td style="padding:6px 10px;font-size:11px;line-height:1.5;border-bottom:1px solid rgba(76,175,80,0.12)">
                    <span style="color:#2e7d32;font-weight:700;margin-left:4px">★</span> {w}
                  </td>
                </tr>""" for w in www])

                ebi_rows = "".join([f"""
                <tr>
                  <td style="padding:6px 10px;font-size:11px;line-height:1.5;border-bottom:1px solid rgba(229,115,115,0.12)">
                    <span style="color:#c62828;font-weight:700;margin-left:4px">↗</span> {e}
                  </td>
                </tr>""" for e in ebi])

                next_steps_rows = "".join([f"""
                <tr>
                  <td style="padding:6px 10px;font-size:11px;line-height:1.5;border-bottom:1px solid rgba(156,39,176,0.12)">
                    <span style="color:#6a1b9a;font-weight:700;margin-left:4px">►</span> {ns}
                  </td>
                </tr>""" for ns in next_steps])

                # Spelling section — RTL table: wrong (red, right side) → correct (green, left side)
                if spelling:
                    spell_rows = "".join([f"""
                    <tr style="border-bottom:1px solid rgba(139,0,0,0.08)">
                      <td style="padding:5px 10px;font-size:14px;color:#2e7d32;font-weight:700;font-family:'Amiri',serif;direction:rtl;text-align:right">{s.get('correct','')}</td>
                      <td style="padding:5px 6px;font-size:12px;color:#888;text-align:center">←</td>
                      <td style="padding:5px 10px;font-size:14px;color:#c62828;font-family:'Amiri',serif;direction:rtl;text-align:right;text-decoration:line-through">{s.get('wrong','')}</td>
                    </tr>""" for s in spelling])
                    spelling_section = f"""
                    <div style="margin-top:12px">
                      <div style="font-size:10px;color:#8b0000;font-weight:700;letter-spacing:1px;margin-bottom:5px;border-bottom:2px solid rgba(139,0,0,0.2);padding-bottom:3px">KEY SPELLING CORRECTIONS</div>
                      <div style="font-size:9px;color:#888;margin-bottom:4px;text-align:right;direction:rtl">التصحيح ← الخطأ</div>
                      <table style="width:100%;border-collapse:collapse;direction:rtl">
                        <tbody>{spell_rows}</tbody>
                      </table>
                    </div>"""
                else:
                    spelling_section = """
                    <div style="margin-top:12px;padding:6px 10px;background:#e8f5e9;border-radius:6px;border:1px solid #4caf50;font-size:10px;color:#2e7d32;text-align:center">
                      🎉 No major spelling errors detected
                    </div>"""

                # ── Full A5 HTML report ──
                html_report = f"""
<link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
<div class="print-report" style="
  width:555px;
  background:#ffffff;
  border:2px solid #d4af37;
  border-radius:10px;
  padding:18px 22px 20px;
  margin:10px auto;
  font-family:'Tajawal',sans-serif;
  font-size:11.5px;
  color:#2c1810;
  box-shadow:0 6px 20px rgba(0,0,0,0.18);
  box-sizing:border-box;
">

  <!-- ── Header ── -->
  <div style="text-align:center;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid #d4af37">
    <div style="font-size:9px;color:#b8941f;letter-spacing:3px;font-weight:700;margin-bottom:3px;text-transform:uppercase">Arabic Writing Assessment</div>
    <div style="font-family:'Amiri',serif;font-size:26px;color:#2c1810;font-weight:700;margin:2px 0">{first_name}</div>
    <div style="font-size:9px;color:#5a4000;font-weight:600;letter-spacing:1px">{(year_group.strip().upper() + " &nbsp;·&nbsp; ") if year_group.strip() else ""}{year} YEARS OF STUDYING ARABIC &nbsp;·&nbsp; {datetime.now().strftime('%d %b %Y')}</div>
  </div>

  <!-- ── Score Badge ── -->
  <div style="margin-bottom:14px;padding:10px 14px;background:rgba(212,175,55,0.07);border-radius:8px;border:1px solid rgba(212,175,55,0.35);display:flex;align-items:center;gap:14px">
    <div style="text-align:center;min-width:64px;border-right:2px solid rgba(212,175,55,0.25);padding-right:14px;flex-shrink:0">
      <div style="font-size:30px;font-weight:900;color:#b8941f;line-height:1">{score.get('score','?')}<span style="font-size:13px;color:rgba(184,148,31,0.6)">/{score.get('out_of',15)}</span></div>
      <div style="font-size:8px;color:#b8941f;font-weight:700;letter-spacing:1px;margin-top:2px">SCORE</div>
    </div>
    <div style="flex:1">
      <div style="display:inline-block;background:{lvl_color};color:white;font-size:8px;font-weight:700;letter-spacing:1px;padding:3px 12px;border-radius:12px;margin-bottom:5px;text-transform:uppercase">{lvl}</div>
      <div style="font-size:10px;color:#3a2010;line-height:1.4">{score.get('reason','')}</div>
    </div>
  </div>

  <!-- ── WWW ── -->
  <div style="margin-bottom:11px">
    <div style="font-size:10px;color:#2e7d32;letter-spacing:1px;font-weight:700;margin-bottom:5px;border-bottom:2px solid rgba(76,175,80,0.3);padding-bottom:3px">★ WHAT WENT WELL</div>
    <table style="width:100%;border-collapse:collapse;background:#f1f8e9;border-radius:6px;overflow:hidden">
      <tbody>{www_rows}</tbody>
    </table>
  </div>

  <!-- ── EBI ── -->
  <div style="margin-bottom:11px">
    <div style="font-size:10px;color:#c62828;letter-spacing:1px;font-weight:700;margin-bottom:5px;border-bottom:2px solid rgba(229,115,115,0.3);padding-bottom:3px">↗ EVEN BETTER IF YOU...</div>
    <table style="width:100%;border-collapse:collapse;background:#ffebee;border-radius:6px;overflow:hidden">
      <tbody>{ebi_rows}</tbody>
    </table>
  </div>

  <!-- ── NEXT STEPS ── -->
  <div style="margin-bottom:11px">
    <div style="font-size:10px;color:#6a1b9a;letter-spacing:1px;font-weight:700;margin-bottom:5px;border-bottom:2px solid rgba(156,39,176,0.3);padding-bottom:3px">► SPECIFIC TARGETS FOR NEXT TIME</div>
    <table style="width:100%;border-collapse:collapse;background:#f3e5f5;border-radius:6px;overflow:hidden">
      <tbody>{next_steps_rows}</tbody>
    </table>
  </div>

  <!-- ── SPELLING ── -->
  {spelling_section}

  <!-- ── Footer ── -->
  <div style="margin-top:14px;padding:8px 12px;background:rgba(212,175,55,0.05);border-radius:6px;border:1px solid rgba(212,175,55,0.2);text-align:center">
    <div style="font-size:9px;color:#5a4000;line-height:1.5">Keep up the great work! Focus on the targets above for your next writing task. 💫</div>
  </div>

</div>"""

                # Print button HTML (lives outside .print-report so it is hidden on print)
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

                # Display word bank analysis
                if wb_analysis:
                    st.markdown(wb_analysis, unsafe_allow_html=True)

                components.html(html_report + print_button_html, height=1020, scrolling=True)

                # ── TXT download ──
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
