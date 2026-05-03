# مُقيِّم الكتابة العربية — Arabic Writing Assessor

## ✨ New Features (Updated Version)

### 1. **Common Arabic Learner Mistakes Prediction**
The AI now identifies and highlights common mistakes made by non-native Arabic speakers:
- **Adjective Placement** — Adjectives after nouns (not before)
- **Masculine/Feminine Agreement** — Matching adjectives and verbs with noun gender
- **Verb Conjugation** — Verbs agreeing with subject (person, number, gender)
- **Pronoun Suffixes** — Correct object pronouns on verbs/prepositions
- **Prepositions & Case Endings** — Proper genitive case after prepositions

The assessment predicts these patterns based on the student's level and provides specific, actionable hints.

### 2. **Multiple Input Methods**
Every section now accepts:
- ✅ **Text input** — Type or paste directly
- ✅ **Image upload** — JPG, PNG, HEIC (iPhone), WEBP, BMP
- ✅ **PDF upload** — Handwritten notes or scanned documents

Supported sections:
- 🎯 Learning Objective (LO)
- ✅ Success Criteria
- 📚 Word Bank (optional)
- ✍️ Student Writing

### 3. **Report Sharing**

#### **Download as Text**
- ⬇️ Download the full report as `.txt` file

#### **Share to Microsoft Teams**
- 💬 Send report directly to Teams channel
- **Setup:** Add `TEAMS_WEBHOOK` to secrets
- See `secrets.toml` for configuration

#### **Share via Email**
- 📧 Send to teacher and/or student
- **Setup:** Configure SMTP credentials in `secrets.toml`
- Supports Gmail, Outlook, Office365, and other SMTP servers

---

## 🚀 Setup Instructions

### 1. **Install on Streamlit Cloud**

```bash
git clone https://github.com/[your-repo]/leveraging-ai-and-rubric-based-feedback-to-improve-arabic-writing-for-non-native-learners.git
cd [repo-folder]
```

### 2. **Add Required Secrets**

In **Streamlit Cloud Dashboard** → **Settings** → **Secrets**:

```toml
# Required
GROQ_API_KEY = "gsk_..."

# Optional: Teams
TEAMS_WEBHOOK = "https://outlook.webhook.office.com/webhookb2/..."

# Optional: Email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "app-password-only"
```

### 3. **Configure Teams Webhook** (if using Teams)

1. Open your Teams channel
2. Click **⋯ (More options)** → **Connectors**
3. Search for **Incoming Webhook**
4. Click **Configure**
5. Name: "Arabic Writing Assessor"
6. Copy the webhook URL
7. Add to secrets as `TEAMS_WEBHOOK`

### 4. **Configure Email** (if using Email)

#### **For Gmail:**
1. Enable 2-Factor Authentication
2. Go to: https://myaccount.google.com/apppasswords
3. Select **Mail** and **Windows Computer** (or your device)
4. Google generates an **App Password** (16 characters)
5. Use that password in secrets, NOT your regular Gmail password

#### **For Outlook/Office365:**
```toml
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@outlook.com"
SENDER_PASSWORD = "your-office365-password"
```

---

## 📊 Assessment Features

### Rubric-Based Feedback
- **Years of Study:** 2-3, 3-4, 4-5, 5-6, 6-7, 7-8, 8-9
- **Assessment Criteria:**
  - Purpose/Content
  - Organization & Coherency
  - Vocabulary
  - Sentence Structure
  - Grammar & Spelling

### Concise Report Format
- 👋 Greeting with specific praise
- ⭐ What Went Well (2 strengths)
- 🔴 Even Better If (1 improvement with hint)
- ✏️ Spelling Corrections (only real errors)
- 📐 Grammar & Common Mistakes
- 📚 Word Bank Suggestions (if provided)
- 🟢 Top 3-4 Tips
- 🔵 Rubric Score Table
- 💪 Next Step

---

## 🎯 How to Use

### Step 1: Fill Student Profile
- Enter student name
- Select years of learning Arabic (2-9)
- Rubric automatically loads

### Step 2: Add Context (Optional)
- 🎯 **LO:** Type or upload learning objective
- ✅ **SC:** Type or upload success criteria
- 📚 **Word Bank:** Enable and add vocabulary words

### Step 3: Upload Student Writing
- **Option A:** Paste typed Arabic text
- **Option B:** Upload handwritten photo(s)
- **Option C:** Upload PDF with multiple pages

### Step 4: Assess
- Click **🔍 Assess Writing**
- AI analyzes using Groq + Rubric

### Step 5: Share
- ⬇️ Download as `.txt`
- 💬 Share to Teams (if configured)
- 📧 Share via Email (if configured)

---

## 🛠️ Requirements

```
streamlit>=1.28.0
groq>=0.4.0
pytesseract>=0.3.10
pymupdf>=1.23.0
pillow-heif>=0.1.0
pandas>=2.0.0
pillow>=10.0.0
requests>=2.31.0
```

---

## 🐛 Troubleshooting

**Q: "GROQ_API_KEY not found"**
- Get free API key: https://console.groq.com
- Add to Streamlit secrets as `GROQ_API_KEY = "gsk_..."`

**Q: "Email configuration not set"**
- Add `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD` to secrets
- For Gmail, use app-specific password (not regular password)

**Q: "Teams webhook error"**
- Verify webhook URL is correct and active
- Check that Teams channel exists and you have permission

**Q: "OCR not extracting text correctly"**
- Make sure image is clear and legible
- Try a different angle or lighting
- For handwriting, ensure contrast between text and background

---

## 📝 Credits

**Arabic Writing Assessment Tool** for non-native learners
- Built with Streamlit + Groq AI
- Rubric-based feedback system
- Multi-modal input (text, image, PDF)
- Integration with Teams and Email

---

## 📄 License

MIT License — Feel free to use, modify, and share!
