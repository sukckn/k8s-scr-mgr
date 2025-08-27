from app import create_app

app= create_app()

if __name__ == '__main__':
    print("Starting service pull-scr (1.0)...")
    app.run()

