# 📝 Arabic Writing Assessor
### AI-powered writing feedback for non-native Arabic learners

---

## 🌟 Overview

**Arabic Writing Assessor** is a Streamlit web app that uses **Claude AI (Anthropic)** to provide structured, personalized feedback on Arabic writing tasks for non-native students.

Designed for **Arabic language teachers**, it analyzes student writing against:
- A **Learning Objective (LO)**
- **Success Criteria**
- A **Year-specific Rubric** (2–9 years of study)

The app gives honest, supportive feedback — without rewriting the student's work.

---

## ✨ Features

- 🤖 **Claude-powered assessment** — using `claude-sonnet-4-5`
- 👤 **Personalized feedback** — addressed to each student by name
- 📊 **7 built-in rubrics** — covering 2 to 9 years of Arabic study
- 🖼️ **Image upload support** — upload LO or Success Criteria as images (OCR)
- ⬇️ **Download feedback** — export as `.txt` file
- 🔴🟡🟢🔵 **Structured output** — mistakes, criteria check, tips, rubric level

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/arabic-writing-assessor.git
cd arabic-writing-assessor
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Anthropic API key
```bash
# Mac/Linux
export ANTHROPIC_API_KEY="your-key-here"

# Windows
set ANTHROPIC_API_KEY=your-key-here
```

### 4. Run the app
```bash
streamlit run arabic_writing_assessor.py
```

Then open `http://localhost:8501` in your browser.

---

## ☁️ Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add your API key under **Settings → Secrets**:
```toml
ANTHROPIC_API_KEY = "your-key-here"
```
5. Click **Deploy** 🎉

---

## 📁 Project Structure

```
📁 arabic-writing-assessor/
├── arabic_writing_assessor.py   # Main app
├── requirements.txt             # Python dependencies
└── README.md                    # You are here
```

---

## 📊 Rubric Levels Covered

| Years of Study | Level |
|----------------|-------|
| 2 – 3 years | Beginner |
| 3 – 4 years | Elementary |
| 4 – 5 years | Pre-Intermediate |
| 5 – 6 years | Intermediate |
| 6 – 7 years | Upper-Intermediate |
| 7 – 8 years | Advanced |
| 8 – 9 years | Near-Fluent |

Each rubric evaluates **5 categories** across **5 levels** (Beginning → Exemplary):
- Purpose / Content
- Organization / Coherency
- Vocabulary
- Sentence Structure
- Grammar / Spelling

---

## 🔒 Privacy

- No student data is stored by the app
- Writing is sent to the Claude API for assessment only
- API calls are subject to [Anthropic's privacy policy](https://www.anthropic.com/privacy)

---

## 🛠️ Built With

- [Streamlit](https://streamlit.io) — Web interface
- [Anthropic Claude](https://www.anthropic.com) — AI assessment engine
- [Pytesseract](https://github.com/madmaze/pytesseract) — OCR for image uploads
- [Pillow](https://python-pillow.org) — Image processing

---

## 👩‍🏫 Designed For

Arabic language teachers working with non-native learners in international or bilingual school settings.

---

## 📄 License

MIT License — free to use, modify, and share.
