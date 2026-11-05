"""Entry point. Development: python wsgi.py   Production: gunicorn -w 3 -b 127.0.0.1:5000 wsgi:app"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
