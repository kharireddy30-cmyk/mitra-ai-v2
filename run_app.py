import os
import sys
import streamlit.web.cli as stcli

def resolve_path(path):
    if getattr(sys, "frozen", False):
        resolved_path = os.path.join(sys._MEIPASS, path)
    else:
        resolved_path = os.path.abspath(path)
    return resolved_path

if __name__ == "__main__":
    app_path = resolve_path("app.py")
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=false",
        "--browser.serverAddress=localhost",
        "--server.port=8501",
    ]
    sys.exit(stcli.main())
