import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

print("Attempting to import app.order.router...")
try:
    from app.order.router import router
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()

print("Attempting to import app.main...")
try:
    from app.main import app
    print("Main app import successful!")
except Exception as e:
    print(f"Main app import failed: {e}")
    import traceback
    traceback.print_exc()
