# CV Chat and Interview Scheduler

This application allows users to ask questions about a resume and schedule an interview using Google Calendar.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/NikolaiVogl/cv-chat.git
cd cv-chat
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the root directory and add your OpenAI API key and your email address:

```
OPENAI_API_KEY="your_openai_api_key"
OWNER_EMAIL="your_email@example.com"
```

### 4. Set up Google Calendar API credentials

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the "Google Calendar API".
4.  Go to "Credentials", click "Create Credentials", and choose "OAuth client ID".
5.  Configure the consent screen (select "External" and provide app details).
6.  Choose "Desktop app" as the application type.
7.  Click "Create". A dialog will appear with the client ID and secret. Click "Download JSON" and save the file as `credentials.json` in the root of your project directory.

### 5. First Run and Authentication

The first time you run the application and try to schedule an interview, it will open a browser window for you to authorize access to your Google Calendar. After you approve, a `token.json` file will be created. This will be used for subsequent requests.

## Running the Application

```bash
uvicorn app.main:app --reload
```

Open your browser and go to `http://127.0.0.1:8000`.
