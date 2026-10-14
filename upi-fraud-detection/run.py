"""Starts UPI Shield on a free port and opens the NEW pay app in your browser."""
import socket, threading, webbrowser
import uvicorn


def is_free(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


port = next(p for p in range(8765, 8800) if is_free(p))
url = f"http://127.0.0.1:{port}/pay.html"
print("\n==============================================")
print(" UPI Shield v2 (All Services design) is running")
print(f" Pay app : {url}")
print(f" Dashboard: http://127.0.0.1:{port}/")
print(" Close this window to stop the app.")
print("==============================================\n")
threading.Timer(2.5, lambda: webbrowser.open(url)).start()
uvicorn.run("backend.main:app", host="127.0.0.1", port=port)
