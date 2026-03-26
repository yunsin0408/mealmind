# [Mealmind](https://mealmind-five.vercel.app)
Mealmind is a smart virtual pantry application designed to help users track ingredients, reduce food waste, and generate creative meal ideas based on what they already have at home. 

## Live App
Use the deployed app here: https://mealmind-five.vercel.app

## Watch the System Demo:
[![Watch the System Demo](https://img.youtube.com/vi/lWiCT5hijUI/0.jpg)](https://youtu.be/lWiCT5hijUI)

## 🚀 Features [IN PROGRESS]
 **Virtual Pantry Tracker**:
* Add, edit, and remove ingredients from your personal inventory.
* Track quantities, categories, and expiration dates.


 **Smart Meal Generator**:
* Generate recipe ideas based on the ingredients currently in your pantry. Users can select ingredients or have AI choose for them!
* Save your favorite generated meals for later.


 **User Authentication**:
* Secure Login and Registration system.
* Password reset functionality via email.
* Personalized profile management.


## 🚀 Tech Stack
* **Backend**: Python 3.10+, Flask
* **Database**: SQLite (via SQLAlchemy ORM)
* **Frontend**: HTML5, CSS3, Jinja2 Templates
* **Authentication**: Flask-Login
* **Utilities**: Python-dotenv, Email-validator

## Database Note
- Current local setup uses SQLite.
- PostgreSQL will be added in future deployment.

## Project Structure
```text
mealmind/
├── app/
│   ├── __init__.py         # App factory and configuration
│   ├── models.py           # Database models (User, PantryItem, etc.)
│   ├── routes.py           # Application routes and logic
│   ├── static/             # CSS and Images
│   └── templates/          # HTML Templates
│       ├── home/           # Landing page
│       ├── pantry/         # Pantry management screens
│       ├── generator/      # Meal generation & favorites
│       ├── profile/        # Auth and user settings
│       └── admin_dashboard.html
├── instance/
│   └── mealmind.db         # SQLite Database
├── api/
│   └── index.py            # Vercel entrypoint (public deployment)
├── run.py                  # Local development entrypoint
├── config.py               # Config settings
├── requirements.txt        # Project dependencies
└── .env                    # Environment variables (Hidden)

```

### Prerequisites
* Python 3.8 or higher
* Git

### Installation (Local Deployment)
1. **Clone the repository**
```bash
git clone https://github.com/yunsin0408/mealmind.git
cd mealmind

```


2. **Create a Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```


3. **Install Dependencies**
```bash
pip install -r requirements.txt

```


4. **Configure Environment Variables**
Create a `.env` file in the root directory and add the following:
```ini
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///database.db
HF_TOKEN=your_hugging_face_token
# If using email features:
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password

```

5. **Initialize Database**

The app is set to create the database automatically on the first run.

7. **Run the Application**
```bash
python run.py

```

Open your browser and navigate to `http://127.0.0.1:5001`.

## Usage
1. Register a new account. Confirm your account via email
2. Go to **My Pantry** to add items you currently have (e.g., "Chicken", "Rice", "Broccoli").
3. Navigate to **Meal Generator** and click "Generate" to see what you can cook.
4. Save recipes you like to your favorites list.

