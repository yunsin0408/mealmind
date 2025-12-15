# MealMind — Internal Flask Recipe Generator (owner view)

This file documents the repository structure and purpose for internal/owner reference. The app is maintained privately and not distributed for general public use.

## Repository structure 

Top-level files
- `run.py` — app runner and lightweight DB seeding script. Instantiates the Flask app, creates DB tables if missing, seeds initial `PantryCategory` entries, and runs the dev server.
- `create_admin.py` — interactive helper script to create or promote a user to admin. Intended to be run locally or in a secure environment; remove after use.
- `config.py` — configuration object used by the Flask app. Reads environment variables such as `SECRET_KEY`, `HF_TOKEN`, `HF_URL`, `HF_MODEL`, and mail settings.
- `email_utils.py` — helpers for generating and confirming email tokens (itsdangerous) and sending confirmation/password reset emails via `flask-mail`. Falls back to logging when SMTP fails.
- `utils.py` — small HTTP adapter that posts payloads to the Hugging Face router (`HF_URL`) using `HF_TOKEN` from `config.py`.
- `auth.py` — blueprint providing register/login/logout routes (legacy or auxiliary auth handlers). Uses `email_utils` for confirmation flows.

Package: `app/`
- `app/__init__.py` — app factory (`create_app`) that initializes extensions (`SQLAlchemy`, `LoginManager`, `Mail`), registers blueprints, and exposes `mail` for `email_utils`.
- `app/models.py` — SQLAlchemy models: `User`, `Admin`, `PantryCategory`, `PantryItem`, `MealCategory`, and `SavedRecipe`. `User` includes password hashing, `allergies` (JSON), and basic helper methods.
- `app/routes.py` — main application routes (blueprint). Handles pantry CRUD, generator form and LLM integration (`generate_recipes_hf`), favorites (save/unsave), profile/edit, admin dashboard, password reset, and other UI endpoints. Also contains prompt-building and JSON parsing logic for LLM responses.

Other
- `instance/mealmind.db` — local SQLite DB file (development only). Back up before making schema changes.
- `static/` and `app/static/` — CSS and image assets used by the templates.
- `requirements.txt` — pinned Python dependencies used to install the environment.

## File-level descriptions (Python files)
- `run.py`: Creates the app via `create_app()`, ensures DB tables exist, seeds categories if empty, and runs Flask's dev server (used for local testing).
- `create_admin.py`: Interactive CLI script that prompts for username/email/password and either creates a new admin user or promotes an existing user to admin. Keep this file out of public copies.
- `config.py`: Loads environment variables (via `dotenv`) and exposes a `DevelopmentConfig` class with `HF_*` and mail configuration values.
- `email_utils.py`: Token generation/confirmation (`itsdangerous`) and email senders (`flask-mail`). Sends confirmation and password reset emails; logs URLs when email sending fails.
- `utils.py`: Wrapper around `requests.post` to call the HF router with authorization headers. Returns parsed JSON or an error dict.
- `auth.py`: Blueprint with routes for `/register`, `/login`, `/logout`, and email confirmation handling. Uses `User` model and `email_utils`.
- `app/__init__.py`: Flask app factory; initializes `db`, `LoginManager`, `Mail`, and registers blueprints. Exposes `mail` to be used by other modules.
- `app/models.py`: SQLAlchemy models and helper methods. `User` stores hashed passwords and a JSON `allergies` column; `SavedRecipe` persist generated recipes, etc.
- `app/routes.py`: The central routing and business logic. Contains the `generate_recipes_hf` helper that selects `model_id` from `model_override` → `HF_MODEL` env → default, builds the prompt, calls `utils.query`, and robustly parses JSON output.
- `auth.py` (legacy/duplicate): If you have both `auth.py` and auth within `app/routes.py`, confirm which one is active. Remove duplicates to avoid confusion.

## Notes & recommendations
- Remove `venv/` from the repository and ensure it's in `.gitignore`.
- Consolidate auth code if there are duplicates (`auth.py` vs auth routes inside `app/routes.py`).
- Consider adding `Flask-Migrate` and creating migration files to track schema changes (recommended before modifying models in production).
- Move allowed LLM `allowed_models` into `config.py` so the whitelist can be changed via environment configuration rather than code edits.

If you want, I can now:
- Edit `README.md` further to add a generated tree view (text) and link sections to file locations.
- Add `Flask-Migrate` and create an initial migration scaffold.
- Remove `venv/` from the repo and add `.gitignore` entries.

Tell me which of those you'd like next and I'll proceed.

## Repository tree (indented)
```text
/ (repo root)
	.env
	.gitignore
	README.md
	create_admin.py
	run.py
	config.py
	email_utils.py
	utils.py
	auth.py
	requirements.txt
	instance/
		mealmind.db
	static/
		style.css
	app/
		__init__.py
		models.py
		routes.py
		static/
			fonts/
			images/
			style.css
		templates/
			base.html
			about.html
			index.html
			admin_dashboard.html
			generator/
				generator.html
				results.html
				favorites.html
			profile/
				login.html
				register.html
				profile.html
				edit_profile.html
				reset_request.html
				reset_password.html
			pantry/
				pantry.html
				add_item.html
				edit_item.html
```
- User registration, login, and email confirmation (token-based)

- Password reset via email token

