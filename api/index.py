import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from config import ProductionConfig

# Always use ProductionConfig on Vercel 
app = create_app(config_class=ProductionConfig)
