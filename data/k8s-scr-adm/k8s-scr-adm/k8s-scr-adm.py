from app import create_app

app= create_app()

if __name__ == '__main__':
    print("Starting service k8s-scr-adm (1.0)...")
    app.run()

