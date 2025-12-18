📄 Legal Policy Explainer Agent

An AI-powered web application that helps users understand legal and policy documents by automatically summarizing, translating, and reading them aloud using Generative AI.

This project is designed as an Enterprise / Concierge AI Agent that improves accessibility and comprehension of complex legal text.

🚀 Features

📂 Upload legal documents (.docx)

✍️ AI-generated plain-language summaries

🌍 Multi-language translation

🔊 Text-to-Speech (Read Aloud) support

🕘 History tracking of processed documents

🧠 Powered by Google Gemini API

🌐 Clean and responsive web interface

🧠 Why Agents?

Legal documents are long, complex, and time-consuming to understand.
This agent automates:

Understanding legal text

Extracting key points

Translating summaries

Reading content aloud

Agents reduce manual effort, improve accessibility, and enhance productivity.

🏗️ Project Architecture
legal_policy_explainer/
│
├── backend/
│   ├── app.py                 # Flask backend
│   ├── config.py              # API & app configuration
│   ├── requirements.txt       # Python dependencies
│   ├── static/                # CSS, JS, audio files
│   ├── templates/             # HTML templates
│   └── utils/                 # Helper utilities
│
├── .gitignore
└── README.md

🛠️ Technologies Used

Python

Flask

Google Gemini API

Google Text-to-Speech

HTML, CSS, JavaScript

Git & GitHub

⚙️ Installation & Setup (Local)
1️⃣ Clone the repository
git clone https://github.com/ruchitha7799/legal-policy-explainer-agent.git
cd legal-policy-explainer-agent

2️⃣ Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

3️⃣ Install dependencies
pip install -r backend/requirements.txt

4️⃣ Set API Key

Create a .env file or update config.py:

GEMINI_API_KEY=your_api_key_here

▶️ Run the Application
cd backend
python app.py


Open browser:

http://127.0.0.1:5000

📈 Future Improvements

Multi-agent orchestration

Long-term memory for document context

Cloud deployment with scalability

User authentication

Better quota handling & caching
