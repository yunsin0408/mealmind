import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from config import ProductionConfig

# Always use ProductionConfig on Vercel
app = create_app(config_class=ProductionConfig)

with app.app_context():
    from app.models import db, PantryCategory
    db.create_all()
    if not PantryCategory.query.first():
        default_categories = [
            "Carbohydrates", "Vegetables", "Fruits",
            "Dairy", "Protein", "Seasoning", "Other",
        ]
        db.session.add_all(PantryCategory(name=n) for n in default_categories)
        db.session.commit()
