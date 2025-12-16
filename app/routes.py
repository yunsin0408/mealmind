from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort
from . import db
from utils import query
from datetime import date
from flask import flash
from flask_login import login_user, logout_user, login_required, current_user
import json

routes_bp = Blueprint('routes', __name__)

MEAL_CATEGORIES = ['Balanced', 'Low Calorie', 'High Protein', 'Low Carb']
CUISINE_STYLES = ['Taiwanese', 'Korean', 'Japanese', 'Western', 'Mediterranean']
DIETARY_PREFERENCES = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free']

def generate_recipes_hf(ingredients, categories, style, preferences, instructions, model_override=None, allergies=None):
    import json
    from flask import current_app
    # allergies can be passed inside `instructions` or we will append below if provided
    if "(exp:" in ingredients:
        prompt = f"""Generate 3 random meal ideas for {categories} meals in {style} style. Select random ingredients from this pantry list: {ingredients}, prioritizing those with earlier expiration dates. Dietary Preferences: {preferences}. {instructions}

Return **strict JSON array** of recipes. Each recipe must have:
- meal_name
- description
- pantry_ingredients (list of ingredients selected from the pantry list)
- missing_ingredients (list of any additional ingredients needed)
- instructions (list)
"""
    else:
        prompt = f"""
    Generate 3 meal ideas using:

    Ingredients: {ingredients}
    Categories: {categories}
    Style: {style}
    Dietary Preferences: {preferences}
    Additional Instructions: {instructions}

    Return **strict JSON array** of recipes. Each recipe must have:
    - meal_name
    - description
    - pantry_ingredients (list of ingredients used from the provided list)
    - missing_ingredients (list of any additional ingredients needed)
    - instructions (list)

    Prioritize recipes that use all the provided ingredients. If insufficient ingredients are given, suggest complementary ingredients commonly used in the specified cuisine style.
    """

    # If allergies provided, append explicit instruction to avoid them
    allergy_instr = ""
    if allergies:
        if isinstance(allergies, (list, tuple)):
            allergy_list = ", ".join([str(a).strip() for a in allergies if a])
        else:
            allergy_list = str(allergies).strip()
        if allergy_list:
            allergy_instr = f"\n\nIMPORTANT: The user has the following allergies: {allergy_list}. DO NOT include any of these ingredients in the recipes, pantry_ingredients, missing_ingredients, or instructions. If a common ingredient conflicts with these allergies, suggest safe substitutes and explicitly state the substitution."
    
    # Allow model selection from a passed override, then app config, then sensible default
    model_id = model_override or current_app.config.get('HF_MODEL')
    try:
        if isinstance(model_id, str) and ':' in model_id:
            model_id = model_id.split(':')[0]
    except Exception:
        # if sanitization fails, fall back to original value
        pass
    # attach allergy instruction into prompt
    if allergy_instr:
        prompt = prompt + allergy_instr

    payload = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": model_id,
        "temperature": 0.2,
        "max_tokens": 800
    }

    try:
        response = query(payload)
    except Exception as e:
        return {"error": f"LLM Connection Error: {str(e)}"}

    # Normalize responses from different LLM providers / HF endpoints
    try:
        if isinstance(response, dict) and response.get('error'):
            return {"error": f"LLM Connection Error: {response.get('error')}"}

        text = None
        # HF chat-router style
        if isinstance(response, dict) and 'choices' in response and response['choices']:
            first = response['choices'][0]
            if isinstance(first, dict) and first.get('message') and isinstance(first['message'], dict) and 'content' in first['message']:
                text = first['message']['content']
            elif isinstance(first, dict) and 'text' in first:
                text = first['text']

        # HF text-generation inference: {generated_text: '...'}
        if text is None and isinstance(response, dict) and 'generated_text' in response:
            text = response['generated_text']

        if text is None and isinstance(response, dict) and 'output' in response:
            out = response['output']
            if isinstance(out, list) and out:
                # try common keys
                if isinstance(out[0], dict):
                    for k in ('generated_text', 'text', 'content'):
                        if k in out[0]:
                            text = out[0][k]
                            break
                elif isinstance(out[0], str):
                    text = out[0]

        if text is None and isinstance(response, str):
            text = response

        if text is None:
            return {"error": "LLM Connection Error: unexpected response format", "response": response}
    except Exception as e:
        return {"error": f"LLM Parsing Error: {str(e)}", "response": response}

    try:
        from json import JSONDecoder, JSONDecodeError
        decoder = JSONDecoder()
        try:
            obj, idx = decoder.raw_decode(text)
            return obj
        except JSONDecodeError:
            pass

        for pos in range(len(text)):
            if text[pos] == '[':
                try:
                    obj, idx = decoder.raw_decode(text[pos:])
                    return obj
                except JSONDecodeError:
                    continue

        # As a last resort, try to extract bracketed substrings with regex
        import re
        candidates = re.findall(r"(\[.*?\])", text, flags=re.S)
        for cand in candidates:
            try:
                return json.loads(cand)
            except Exception:
                continue

        return {"error": "JSON Parsing Error: could not find a valid JSON array in model output"}
    except Exception as e:
        return {"error": f"JSON Parsing Error: {str(e)}"}
    

@routes_bp.route("/pantry", methods=["GET"])
def pantry():
    from .models import PantryItem, PantryCategory
    # If user isn't logged in, show an empty pantry (no items or categories)
    if not current_user.is_authenticated:
        return render_template('pantry/pantry.html', items=[], categories=[],
                               selected_category='', q='', exp_before='', exp_after='')
    # read query params
    category_id = request.args.get("category", "").strip()
    q = request.args.get("q", "").strip()
    exp_before = request.args.get("exp_before", "").strip()
    query = PantryItem.query
    if category_id:
        try:
            cid = int(category_id)
            query = query.filter(PantryItem.category_id == cid)
        except ValueError:
            flash('Invalid category selected', 'warning')
    # simple name search
    if q:
        query = query.filter(PantryItem.name.ilike(f"%{q}%"))
    # expiration filters (expects YYYY-MM-DD from <input type="date">)
    if exp_before:
        try:
            d = date.fromisoformat(exp_before)
            query = query.filter(PantryItem.expiration_date <= d)
        except Exception:
            flash('Invalid "expires before" date', 'warning')
    # ordering: items expiring sooner first
    items = query.order_by(PantryItem.expiration_date.asc()).all()
    # categories for select control
    categories = PantryCategory.query.order_by(PantryCategory.name).all()
    return render_template('pantry/pantry.html', items=items, categories=categories,
                           selected_category=category_id, q=q,
                           exp_before=exp_before)

@routes_bp.route("/pantry/add", methods=["GET", "POST"])
@login_required
def add_item():
    from .models import PantryItem, PantryCategory
    categories = PantryCategory.query.order_by(PantryCategory.name).all()
    if request.method == 'GET':
        return render_template('pantry/add_item.html', categories=categories)

    # POST form submission (server-rendered)
    name = request.form.get('name')
    category_id = request.form.get('category_id')
    quantity = request.form.get('quantity') or None
    unit = request.form.get('unit') or None
    expiration_date = request.form.get('expiration_date') or None

    if expiration_date:
        expiration_date = date.fromisoformat(expiration_date)
    else:
        expiration_date = None

    new_item = PantryItem(name=name, category_id=int(category_id) if category_id else None,
                          quantity=float(quantity) if quantity else None,
                          unit=unit, expiration_date=expiration_date)
    db.session.add(new_item)
    db.session.commit()
    return redirect(url_for('routes.pantry'))

@routes_bp.route("/pantry/delete/<int:item_id>")
@login_required
def delete_item(item_id):
    from .models import PantryItem
    item = PantryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('routes.pantry'))


@routes_bp.route("/pantry/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    from .models import PantryItem, PantryCategory
    item = PantryItem.query.get_or_404(item_id)
    categories = PantryCategory.query.order_by(PantryCategory.name).all()
    if request.method == 'GET':
        return render_template('pantry/edit_item.html', item=item, categories=categories)

    # POST update
    item.name = request.form.get('name', item.name)
    item.category_id = int(request.form.get('category_id', item.category_id)) if request.form.get('category_id') else item.category_id
    quantity = request.form.get('quantity')
    item.quantity = float(quantity) if quantity else None
    item.unit = request.form.get('unit', item.unit)
    expiry_date = request.form.get('expiration_date')
    if expiry_date:
        item.expiration_date = date.fromisoformat(expiry_date)
    else:
        item.expiration_date = None
    db.session.commit()
    return redirect(url_for('routes.pantry'))
    
@routes_bp.route("/about")
def about():
    return render_template("home/index.html")


# --- Admin routes
@routes_bp.route('/admin')
@login_required
def admin_dashboard():
    # only admins may access
    if not getattr(current_user, 'is_admin', False):
        abort(403)
    from .models import User
    q = request.args.get('q', '').strip()
    users_query = User.query.order_by(User.created_on.desc())
    if q:
        users_query = users_query.filter((User.username.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%")))
    users = users_query.all()
    return render_template('admin_dashboard.html', users=users, q=q)


@routes_bp.route('/admin/user/<int:user_id>/action', methods=['POST'])
@login_required
def admin_user_action(user_id):
    if not getattr(current_user, 'is_admin', False):
        abort(403)
    from .models import User
    from datetime import datetime
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    if action == 'toggle_confirm':
        user.is_confirmed = not user.is_confirmed
        if user.is_confirmed and not user.confirmed_on:
            user.confirmed_on = datetime.now()
        db.session.commit()
        flash('使用者確認狀態已更新。', 'success')
    elif action == 'toggle_admin':
        user.is_admin = not user.is_admin
        db.session.commit()
        flash('使用者管理員身分已更新。', 'success')
    elif action == 'delete':
        if user.id == current_user.id:
            flash('無法刪除您自己的管理員帳號。', 'danger')
        else:
            db.session.delete(user)
            db.session.commit()
            flash('使用者已刪除。', 'info')
    else:
        flash('未知的操作。', 'warning')
    return redirect(url_for('routes.admin_dashboard'))


@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    from .models import User
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Basic validation
        if not username or not email or not password:
            flash('Please fill out all fields', 'danger')
            return redirect(url_for('routes.register'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('routes.register'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        # Send confirmation email (if mail configured this will send, otherwise URL will be logged)
        try:
            from email_utils import send_confirmation_email
            send_confirmation_email(new_user.email)
            flash('Registration successful. A confirmation email has been sent. Please check your inbox.', 'info')
        except Exception:
            flash('Registration successful. (Could not send confirmation email.)', 'warning')
        return redirect(url_for('routes.login'))

    return render_template('profile/register.html')


# --- Password reset: request and perform reset -------------------------------
@routes_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    from .models import User
    from email_utils import send_password_reset_email
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address', 'warning')
            return redirect(url_for('routes.reset_request'))
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                send_password_reset_email(user.email)
                flash('We have sent an email with instructions to reset your password. Please check your inbox.', 'info')
            except Exception:
                flash('Unable to send reset email. Please contact the site administrator or try again later.', 'warning')
        else:
            flash('We have sent an email with instructions to reset your password. Please check your inbox.', 'info')
        return redirect(url_for('routes.login'))
    return render_template('profile/reset_request.html')


@routes_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    from .models import User
    from email_utils import confirm_password_reset_token
    email = confirm_password_reset_token(token)
    if not email:
        flash('重設連結無效或已過期。請重新嘗試密碼重設流程。', 'danger')
        return redirect(url_for('routes.reset_request'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('找不到該帳號。', 'danger')
        return redirect(url_for('routes.register'))

    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('confirm_password')
        if not password or password != password2:
            flash('密碼不相符或為空，請重試。', 'warning')
            return redirect(url_for('routes.reset_with_token', token=token))
        # set new password
        user.set_password(password)
        db.session.commit()
        flash('密碼已更新。請用新密碼登入。', 'success')
        return redirect(url_for('routes.login'))

    return render_template('profile/reset_password.html', token=token, email=email)


@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    from .models import User
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not getattr(user, 'is_confirmed', False):
                flash('Please confirm your email address before logging in. Check your inbox or resend confirmation.', 'warning')
                return redirect(url_for('routes.login'))

            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('routes.index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('routes.login'))

    return render_template('profile/login.html')


@routes_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.index'))

# Email confirmation route
@routes_bp.route('/confirm/<token>')
def confirm_email(token):
    from email_utils import confirm_token
    from .models import User
    email = confirm_token(token)
    if not email:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('routes.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found for this confirmation link.', 'danger')
        return redirect(url_for('routes.register'))

    if user.is_confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.is_confirmed = True
        db.session.commit()
        flash('You have confirmed your account! Thanks!', 'success')

    return redirect(url_for('routes.login'))


@routes_bp.route('/profile')
@login_required
def profile():
    return render_template('profile/profile.html')


@routes_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # allow user to edit allergies (stored as JSON list)
    if request.method == 'POST':
        allergies_raw = request.form.get('allergies', '')
        # parse comma-separated list into clean list
        items = [a.strip() for a in allergies_raw.split(',') if a.strip()]
        try:
            current_user.allergies = items
            db.session.commit()
            flash('Profile updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Could not update profile: ' + str(e), 'danger')
        return redirect(url_for('routes.profile'))
    return render_template('profile/edit_profile.html')

# Save a generated recipe as favorite
@routes_bp.route('/recipes/save', methods=['POST'])
@login_required
def save_recipe():
    from .models import SavedRecipe

    meal_name = request.form.get('meal_name')
    description = request.form.get('description')
    pantry_ingredients = request.form.get('pantry_ingredients')
    missing_ingredients = request.form.get('missing_ingredients')
    instructions = request.form.get('instructions')

    # Parse JSON fields (they are sent as JSON strings via hidden inputs)
    try:
        pantry = json.loads(pantry_ingredients) if pantry_ingredients else []
    except Exception:
        pantry = []
    try:
        missing = json.loads(missing_ingredients) if missing_ingredients else []
    except Exception:
        missing = []
    try:
        instr = json.loads(instructions) if instructions else []
    except Exception:
        instr = []

    new = SavedRecipe(
        user_id=current_user.id,
        meal_name=meal_name or "",
        description=description or "",
        pantry_ingredients=pantry,
        missing_ingredients=missing,
        instructions=instr,
    )
    db.session.add(new)
    db.session.commit()
    flash('Recipe saved to favorites.', 'success')
    return redirect(request.referrer or url_for('routes.favorites'))


@routes_bp.route('/favorites')
@login_required
def favorites():
    from .models import SavedRecipe
    recipes = SavedRecipe.query.filter_by(user_id=current_user.id).order_by(SavedRecipe.created_on.desc()).all()
    return render_template('generator/favorites.html', recipes=recipes)


@routes_bp.route('/favorites/delete/<int:recipe_id>', methods=['POST'])
@login_required
def delete_favorite(recipe_id):
    from .models import SavedRecipe
    recipe = SavedRecipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('routes.favorites'))
    db.session.delete(recipe)
    db.session.commit()
    flash('Favorite removed.', 'info')
    return redirect(url_for('routes.favorites'))


@routes_bp.route('/recipes/unsave', methods=['POST'])
@login_required
def unsave_recipe():
    from .models import SavedRecipe
    meal_name = request.form.get('meal_name')
    if not meal_name:
        flash('No recipe specified to remove.', 'danger')
        return redirect(request.referrer or url_for('routes.index'))

    recipe = SavedRecipe.query.filter_by(user_id=current_user.id, meal_name=meal_name).first()
    if not recipe:
        flash('Recipe not found in your favorites.', 'warning')
        return redirect(request.referrer or url_for('routes.index'))

    db.session.delete(recipe)
    db.session.commit()
    flash('Recipe removed from favorites.', 'info')
    return redirect(request.referrer or url_for('routes.index'))


@routes_bp.route('/api/recipes/save', methods=['POST'])
@login_required
def api_save_recipe():
    """AJAX endpoint: save a recipe and return JSON with saved id."""
    from .models import SavedRecipe
    data = request.get_json() or request.form
    meal_name = data.get('meal_name')
    description = data.get('description')
    pantry = data.get('pantry_ingredients')
    missing = data.get('missing_ingredients')
    instructions = data.get('instructions')

    # If strings are JSON-encoded, try to parse them
    import json as _json
    def _parse(x):
        if not x:
            return []
        if isinstance(x, (list, dict)):
            return x
        try:
            return _json.loads(x)
        except Exception:
            return []

    pantry_list = _parse(pantry)
    missing_list = _parse(missing)
    instr_list = _parse(instructions)

    new = SavedRecipe(
        user_id=current_user.id,
        meal_name=meal_name or "",
        description=description or "",
        pantry_ingredients=pantry_list,
        missing_ingredients=missing_list,
        instructions=instr_list,
    )
    db.session.add(new)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': new.id, 'meal_name': new.meal_name})


@routes_bp.route('/api/recipes/unsave', methods=['POST'])
@login_required
def api_unsave_recipe():
    """AJAX endpoint: unsave by id or meal_name."""
    from .models import SavedRecipe
    data = request.get_json() or request.form
    rid = data.get('id')
    meal_name = data.get('meal_name')

    if rid:
        recipe = SavedRecipe.query.filter_by(id=int(rid), user_id=current_user.id).first()
    elif meal_name:
        recipe = SavedRecipe.query.filter_by(user_id=current_user.id, meal_name=meal_name).first()
    else:
        return jsonify({'status': 'error', 'message': 'no id or meal_name provided'}), 400

    if not recipe:
        return jsonify({'status': 'error', 'message': 'not found'}), 404

    db.session.delete(recipe)
    db.session.commit()
    return jsonify({'status': 'ok'})

@routes_bp.route("/", methods=["GET", "POST"])
def index():
    from .models import PantryItem
    if request.method == "POST":
        mode = request.form.get("mode")
        prioritize_flag = bool(request.form.get('prioritize_expiring'))

        if mode == "pantry":
            pantry_item_ids = request.form.getlist("pantry_items")
            items = [PantryItem.query.get(int(id)) for id in pantry_item_ids if PantryItem.query.get(int(id))]
            # If prioritize flag is set, sort by expiration date (soonest first), None at end
            if prioritize_flag:
                items = sorted(items, key=lambda it: it.expiration_date or date.max)
                # include expiration info inline to help model prioritize
                ingredients = ", ".join([f"{item.name} (exp: {item.expiration_date})" if item.expiration_date else item.name for item in items])
            else:
                ingredients = ", ".join([item.name for item in items])
        elif mode == "random":
            pantry_items_sorted = PantryItem.query.order_by(PantryItem.expiration_date).all()
            ingredients = ", ".join([f"{item.name} (exp: {item.expiration_date})" for item in pantry_items_sorted if item.expiration_date])
        else:
            ingredients = ""

        categories = ", ".join(request.form.getlist("categories")) + (", " + request.form.get("custom_categories") if request.form.get("custom_categories") else "")
        style = ", ".join(request.form.getlist("styles")) + (", " + request.form.get("custom_styles") if request.form.get("custom_styles") else "")
        preferences = ", ".join(request.form.getlist("preferences")) + (", " + request.form.get("custom_preferences") if request.form.get("custom_preferences") else "")
        instructions = request.form.get("instructions")
        # if prioritize flag, append instruction to prioritize expiring ingredients
        if prioritize_flag:
            if not instructions:
                instructions = "Prioritize ingredients that are close to expiration and use them first."
            else:
                instructions = instructions + "\nPrioritize ingredients that are close to expiration and use them first."

        # allow user to choose model via form 
        model_choice = request.form.get('model')
        allowed_models = [
            'mistralai/mixtral-instruct-8x:latest',
            'meta-llama/Llama-3.1-8B-Instruct:novita'
        ]
        if model_choice not in allowed_models:
            model_choice = None
        # collect user's allergies and pass to generator
        allergies = None
        if current_user.is_authenticated:
            try:
                allergies = current_user.allergies or None
            except Exception:
                allergies = None

        recipes = generate_recipes_hf(ingredients, categories, style, preferences, instructions, model_override=model_choice, allergies=allergies)
        form_data = {
            'mode': request.form.get('mode'),
            'pantry_items': request.form.getlist('pantry_items'),
            'prioritize_expiring': prioritize_flag,
            'categories': request.form.getlist('categories'),
            'styles': request.form.getlist('styles'),
            'preferences': request.form.getlist('preferences'),
            'custom_categories': request.form.get('custom_categories'),
            'custom_styles': request.form.get('custom_styles'),
            'custom_preferences': request.form.get('custom_preferences'),
            'instructions': instructions
        }

        saved_names = []
        if current_user.is_authenticated:
            from .models import SavedRecipe
            saved = SavedRecipe.query.filter_by(user_id=current_user.id).all()
            saved_names = [s.meal_name for s in saved]

        return render_template('generator/results.html', recipes=recipes, form_data=form_data, saved_names=saved_names)

    pantry_items = PantryItem.query.all()
  
    from flask import current_app
    hf_model = current_app.config.get('HF_MODEL')
    return render_template('home/index.html', pantry_items=pantry_items, meal_categories=MEAL_CATEGORIES, cuisine_styles=CUISINE_STYLES, dietary_preferences=DIETARY_PREFERENCES, hf_model=hf_model)

