from flask import Flask, request, redirect, render_template

app = Flask(__name__)



EMAILE_FILE = "emaile.txt"
WYGRANI_FILE = "wygrani.txt"

@app.route('/')
def index():
    return 'Witaj! To strona konkursowa.'



def count_lines(filename):
    with open(filename, 'r') as file:
        return len(file.readlines())


def wczytaj_emaile():
    """
    Funkcja wczytująca adresy e-mail pracowników z pliku emaile.txt
    i zwracająca słownik, gdzie kluczem jest identyfikator, a wartością adres e-mail.
    """
    pracownicy = {}
    with open(EMAILE_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split(' ', 1)
            if len(parts) == 2:
                identyfikator, email = parts
                pracownicy[int(identyfikator)] = email
    return pracownicy

PRACOWNICY = wczytaj_emaile()


@app.route('/konkurs')
def konkurs():
    employee_id = request.args.get('id')
    
    if employee_id and int(employee_id) in PRACOWNICY:
        email = PRACOWNICY[int(employee_id)]
        
        with open(WYGRANI_FILE, 'a') as f:
            f.write(email + '\n')
        
        return redirect('/wygrales')
    else:
        return 'Niepoprawny identyfikator pracownika.'

@app.route('/wygrales')
def wygrales():
    return render_template('wygrales.html')

@app.route('/omnie')
def omnie():
    return render_template('o_mnie.html')

@app.route('/statystyki')
def statystyki():
    participants_count = count_lines(EMAILE_FILE)
    winners_count = count_lines(WYGRANI_FILE)

    return render_template('statystyki.html', participants_count=participants_count, winners_count=winners_count)

@app.route('/informacje')
def informacje():
    return render_template('informacje.html')


if __name__ == '__main__':
    app.run(debug=True)
