from flask import Flask, render_template, redirect, request, url_for, session
import json
from mail import send_email
import random

app = Flask(__name__)
app.secret_key = 'atm@26'


# ---------------- OTP GENERATION ----------------
def generate_otp():
    return str(random.randint(100000, 999999))


# ---------------- GET DATA ----------------
def get_data():
    with open('data.json', 'r') as file:
        data = json.load(file)
    return data


# ---------------- UPDATE DATA ----------------
def update_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)


# ---------------- BASE ROUTE ----------------
@app.route('/')
def base():
    return redirect(url_for('login'))


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    info = request.args.get('info')

    if request.method == 'POST':

        email = request.form.get('email')
        pin = request.form.get('pin')

        data = get_data()
        users = data["users"]

        for i in users:

            if email == i["email"] and pin == i["pin"]:

                session['name'] = i["name"]
                session['id'] = i["id"]

                return redirect(url_for('dashboard'))

        return redirect(
            url_for('login', info='Invalid Login')
        )

    return render_template('login.html', info=info)


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    info = request.args.get('info')

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        pin = request.form.get('pin')
        cpin = request.form.get('cpin')

        data = get_data()
        users = data["users"]

        # Check email already exists
        for i in users:

            if i["email"] == email:

                return redirect(
                    url_for(
                        'register',
                        info='Email is already registered'
                    )
                )

        # Check PIN
        if pin != cpin:

            return redirect(
                url_for(
                    'register',
                    info='Enter the PIN properly'
                )
            )

        # Create new user
        userinfo = {
            "id": len(users) + 1,
            "name": name,
            "email": email,
            "pin": pin,
            "balance": 0,
            "history": []
        }

        users.append(userinfo)

        update_data(data)

        return redirect(
            url_for(
                'login',
                info='Successfully Registered'
            )
        )

    return render_template('register.html', info=info)


# ---------------- FORGOT PIN ----------------
@app.route('/forgotpin', methods=['GET', 'POST'])
def forgotpin():

    info = request.args.get('info')

    if request.method == 'POST':

        email = request.form.get('email')

        data = get_data()
        users = data["users"]

        for i in users:

            if i["email"] == email:

                username = i["name"]

                session["email"] = i["email"]

                otp = generate_otp()

                session["otp"] = otp

                # Send OTP to email
                send_email(email, username, otp)

                return redirect(url_for('verify'))

        return redirect(
            url_for(
                'forgotpin',
                info='Email is not registered'
            )
        )

    return render_template(
        'forgotpin.html',
        info=info
    )


# ---------------- VERIFY OTP ----------------
@app.route('/verify', methods=['GET', 'POST'])
def verify():

    info = request.args.get('info')

    if request.method == 'POST':

        otp = request.form.get('otp')

        if otp == session.get('otp'):

            session.pop('otp', None)

            return redirect(
                url_for(
                    'resetpin',
                    info='OTP verification done'
                )
            )

        return redirect(
            url_for(
                'verify',
                info='Invalid OTP'
            )
        )

    return render_template(
        'verify.html',
        info=info
    )


# ---------------- RESET PIN ----------------
@app.route('/resetpin', methods=['GET', 'POST'])
def resetpin():

    info = request.args.get('info')

    if request.method == 'POST':

        npin = request.form.get('npin')
        cpin = request.form.get('cpin')

        if npin == cpin:

            data = get_data()
            users = data["users"]

            for i in users:

                if i["email"] == session.get("email"):

                    i["pin"] = npin

                    update_data(data)

                    session.pop("email", None)

                    return redirect(
                        url_for(
                            'login',
                            info='Reset PIN is successful, now you can login'
                        )
                    )

        return redirect(
            url_for(
                'resetpin',
                info='Incorrect PIN'
            )
        )

    return render_template(
        'resetpin.html',
        info=info
    )


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():

    return render_template('dashboard.html')


# ---------------- CHECK BALANCE ----------------
@app.route('/checkbalance')
def checkbalance():

    data = get_data()
    users = data["users"]

    balance = 0

    for i in users:

        if i["id"] == session.get("id"):

            balance = i["balance"]
            break

    return render_template(
        'checkbalance.html',
        balance=balance
    )


# ---------------- DEPOSIT ----------------
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():

    info = request.args.get('info')

    if request.method == 'POST':

        try:

            amount = int(request.form.get('amount'))

            if amount <= 0:
                raise ValueError

        except (ValueError, TypeError):

            return redirect(
                url_for(
                    'deposit',
                    info='Enter a proper positive amount'
                )
            )

        data = get_data()
        users = data["users"]

        for i in users:

            if i["id"] == session.get("id"):

                # Add amount to balance
                i["balance"] += amount

                # Add transaction to history
                i["history"].append(
                    f"{amount} is deposited"
                )

                update_data(data)

                return redirect(
                    url_for('checkbalance')
                )

    return render_template(
        'deposit.html',
        info=info
    )


# ---------------- WITHDRAW ----------------
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():

    info = request.args.get('info')

    if request.method == 'POST':

        try:

            amount = int(request.form.get('amount'))

            if amount <= 0:
                raise ValueError

        except (ValueError, TypeError):

            return redirect(
                url_for(
                    'withdraw',
                    info='Enter a proper positive amount'
                )
            )

        data = get_data()
        users = data["users"]

        for i in users:

            if i["id"] == session.get("id"):

                # Check sufficient balance
                if amount > i["balance"]:

                    return redirect(
                        url_for(
                            'withdraw',
                            info='Insufficient Balance'
                        )
                    )

                # Subtract amount
                i["balance"] -= amount

                # Add transaction history
                i["history"].append(
                    f"{amount} is withdrawn"
                )

                update_data(data)

                return redirect(
                    url_for('checkbalance')
                )

    return render_template(
        'withdraw.html',
        info=info
    )


# ---------------- VIEW TRANSACTIONS ----------------
@app.route('/viewtransactions')
def viewtransactions():

    data = get_data()
    users = data["users"]

    history = []

    for i in users:

        if i["id"] == session.get("id"):

            history = i["history"]
            break

    return render_template(
        'transactions.html',
        history=history
    )


# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():

    data = get_data()
    users = data["users"]

    user = None

    for i in users:

        if i["id"] == session.get("id"):

            user = i
            break

    return render_template(
        'profile.html',
        user=user
    )


# ---------------- RUN APPLICATION ----------------
if __name__ == "__main__":
    app.run(debug=True)

