"""Entry point: python main.py"""
import threading
import webbrowser
import uvicorn

def _open_browser():
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    threading.Timer(1.5, _open_browser).start()
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
