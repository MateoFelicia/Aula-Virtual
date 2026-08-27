# run.py
from app import create_app #Accede a la carpeta por dinamismo

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)