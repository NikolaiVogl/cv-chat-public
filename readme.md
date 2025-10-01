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
Create a `.env` file in the root directory and add the following environment variables:

```
OPENAI_API_KEY="your_openai_api_key"
OWNER_EMAIL="your_email@example.com"
GOOGLE_CLIENT_ID="your_google_client_id"
GOOGLE_CLIENT_SECRET="your_google_client_secret"
GOOGLE_REFRESH_TOKEN="your_google_refresh_token"
```

### 4. Set up Google Calendar API credentials

To obtain the Google Calendar API credentials for the environment variables:

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the "Google Calendar API".
4.  Go to "Credentials", click "Create Credentials", and choose "OAuth client ID".
5.  Configure the consent screen (select "External" and provide app details).
6.  Choose "Desktop app" as the application type.
7.  Click "Create". A dialog will appear with the client ID and secret. Click "Download JSON" and save the file as `credentials.json` in the root of your project directory.
6.  Choose "Web application" as the application type.
7.  Add authorized redirect URIs (e.g., `https://oauth2.googleapis.com/token`).
8.  Click "Create" and note the client ID and client secret.
9.  Follow the [OAuth 2.0 flow](https://developers.google.com/identity/protocols/oauth2) to obtain a refresh token.
10. Add the `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` to your `.env` file.

### 5. First Run and Authentication
### 5. First Run

The first time you run the application and try to schedule an interview, it will open a browser window for you to authorize access to your Google Calendar. After you approve, a `token.json` file will be created. This will be used for subsequent requests.
Once all environment variables are configured, you can start the application.

## Running the Application

```bash
uvicorn app.main:app --reload
```

Open your browser and go to `http://127.0.0.1:8000`.
