from app import create_app

app= create_app()

if __name__ == '__main__':
    print("Starting service k8s-scr-mgr (1.5.1)...") # keep version in sync with file /app/__init__.py
    app.run()

