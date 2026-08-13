import app

print("APP FILE =", app.__file__)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)