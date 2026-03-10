import os
import sys
import threading
import time
import webbrowser
import uvicorn
from multiprocessing import freeze_support

# Fix import resolution so it can find `app` when run un-frozen.
# When frozen, PyInstaller collects the imports automatically.
current_dir = os.path.dirname(os.path.realpath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if not hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, backend_dir)

from app.main import app

def open_browser():
    """Wait briefly for the server to start, then open the default web browser."""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\nOpening browser at {url}...\n")
    webbrowser.open(url)

if __name__ == "__main__":
    # Required for Windows multiprocessing support in PyInstaller
    freeze_support()
    
    # Start the browser-opening thread in the background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the FastAPI app programmatically
    print("Starting Email Extraction System server...")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        workers=1 # Must use 1 worker when packaged with PyInstaller to prevent fork bombs
    )
