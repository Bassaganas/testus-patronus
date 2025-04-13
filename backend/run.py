import uvicorn
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    print("="*50)
    print("Starting Testus Patronus API from run.py")
    print("="*50)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 