from app import create_app

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        from app.models import db, PantryCategory
        db.create_all()
        
        if not PantryCategory.query.first():  
            carbonhydrate = PantryCategory(name="Carbohydrates")
            vegetable = PantryCategory(name="Vegetables")
            fruit = PantryCategory(name="Fruits")
            dairy = PantryCategory(name="Dairy")
            protein = PantryCategory(name="Protein")
            seasoning = PantryCategory(name="Seasoning")
            other = PantryCategory(name="Other")
            
            db.session.add_all([carbonhydrate, vegetable, fruit, dairy, protein, seasoning, other])
            db.session.commit()
    
    app.run(debug=True, host="0.0.0.0", port=5001)