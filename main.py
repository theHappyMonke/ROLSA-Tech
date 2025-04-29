#Import the python modules
from flask import Flask, render_template, flash, request, redirect, url_for # flask is for rendering templates.
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user # flask_login is used for logging the user in.
from werkzeug.security import generate_password_hash, check_password_hash # This is used to hash the users password when they create an account for security.
import requests # requests is used for handeling HTTP requests.
import sqlite3 # sqlite3 is used for interacting with the database.

#Creates the database if it does not already exist, useful in prototypes and testing
connection = sqlite3.connect('database.db', check_same_thread=False)


#Establishes an API key for the carbon calculation
API_KEY = "xAiAmc3qjld6UHIUmxtw"
base_URL = "https://www.carboninterface.com/api/v1/" #base_URL is defined here so that it may be used for other carbon calculations without repeating the URL, this reduces repetition.


#Creates all the tables in the database if they do not already exist
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY NOT NULL, firstName TEXT NOT NULL, lastName TEXT NOT NULL, email TEXT NOT NULL UNIQUE, phone INTEGER NOT NULL, password TEXT NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS carbonFootprintCalculation (id INTEGER PRIMARY KEY NOT NULL, userID INTEGER NOT NULL, make TEXT NOT NULL, model TEXT NOT NULL, year INTEGER NOT NULL, unit TEXT NOT NULL, value INTEGER NOT NULL, grams INTEGER NOT NULL, pounds INTEGER NOT NULL, kilograms INTEGER NOT NULL, metricTon INTEGER NOT NULL, date TEXT NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS energyCalculation (id INTEGER PRIMARY KEY NOT NULL, userID INTEGER NOT NULL, country TEXT NOT NULL, state TEXT, unit TEXT NOT NULL, value INTEGER NOT NULL, grams INTEGER NOT NULL, pounds INTEGER NOT NULL, kilograms INTEGER NOT NULL, metricTon INTEGER NOT NULL, date TEXT NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS productTypes (id INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, origin TEXT NOT NULL, image TEXT NOT NULL, typeID INTEGER NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS consultations (id INTEGER PRIMARY KEY NOT NULL, userID INTEGER NOT NULL, typeID INTEGER NOT NULL, time TEXT NOT NULL)")
cursor.execute("CREATE TABLE IF NOT EXISTS installations (id INTEGER PRIMARY KEY NOT NULL, userID INTEGER NOT NULL, productID INTEGER NOT NULL, time TEXT NOT NULL)")
cursor.close()


#Creates an instance of the Flask class
app = Flask(__name__)
app.config['SECRET_KEY'] = 'this_is_a_very_secret_key' # This is used for flash to work


#Creates a class for the user
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


#Loads the user
class User(UserMixin):
    def __init__(self, id, firstName, lastName, email, phone, password):
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.phone = phone
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(id=user[0], firstName=user[1], lastName=user[2], email=user[3], phone=user[4], password=user[5])
    return None


#Functions in the system
def scheduleConsultation(typeID, timeslot):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO consultations (userID, typeID, time) VALUES (?, ?, ?)"
        insert_data = (current_user.id, typeID, timeslot,)
        cursor.execute(query, insert_data)
        connection.commit()
    except sqlite3.Error as error:
        print("Database error:", error)
    finally:
        cursor.close()
        return
    
def scheduleInstallation(productID, timeslot):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO installations (userID, productID, time) VALUES (?, ?, ?)"
        insert_data = (current_user.id, productID, timeslot,)
        cursor.execute(query, insert_data)
        connection.commit()
    except sqlite3.Error as error:
        print("Database error:", error)
    finally:
        cursor.close()
        return

def getConsultations():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT productTypes.name, consultations.time, consultations.id FROM consultations JOIN productTypes ON consultations.typeID = productTypes.id WHERE userID=?", (current_user.id,))
        consultations = cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
    finally:
        cursor.close()
    
    if consultations:
        return consultations
    else:
        return

def getInstallations():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT products.name, installations.time, installations.id FROM installations JOIN products ON installations.productID = products.id WHERE userID=?", (current_user.id,))
        installations = cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
    finally:
        cursor.close()
    
    if installations:
        return installations
    else:
        return

def getVehicleEstimations():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT make, model, year, unit, value, grams, pounds, kilograms, metricTon, date, id FROM carbonFootprintCalculation WHERE userID=?", (current_user.id,))
        vehicleEstimations = cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
    finally:
        cursor.close()
    
    if vehicleEstimations:
        return vehicleEstimations
    else:
        return
    
def getEnergyEstimations():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT country, state, unit, value, grams, pounds, kilograms, metricTon, date, id FROM energyCalculation WHERE userID=?", (current_user.id,))
        energyEstimations = cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
    finally:
        cursor.close()
    
    if energyEstimations:
        return energyEstimations
    else:
        return

def getProducts():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT products.name, products.description, products.image, productTypes.id FROM products JOIN productTypes ON products.typeID = productTypes.id")
        products = cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
    cursor.close()
    if products:
        return products
    else:
        return

def getProductTypes():
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM productTypes")
        productTypes = cursor.fetchall()
    except sqlite3.Error as error:
        print("Database error:", error)
    cursor.close()
    if productTypes:
        return productTypes
    else:
        return

def vehicleCarbonEstimate (unit, value, model):
    data = {
        "type": "vehicle",
        "distance_unit": unit,
        "distance_value": value,
        "vehicle_model_id": model,
        }
    
    headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

    try:
        response = requests.post(f"{base_URL}estimates", headers=headers, json=data)
        if response.status_code == 201:
            response = response.json()
            if current_user.is_authenticated:
                cursor = connection.cursor()
                query = "INSERT INTO carbonFootprintCalculation (userID, make, model, year, unit, value, grams, pounds, kilograms, metricTon, date) VALUES (?, ?, ?, ?, ?, ? ,? ,? ,? ,? ,?)"
                insert = (current_user.id, response['data']['attributes']['vehicle_make'], response['data']['attributes']['vehicle_model'], response['data']['attributes']['vehicle_year'], response['data']['attributes']['distance_unit'], response['data']['attributes']['distance_value'], response['data']['attributes']['carbon_g'], response['data']['attributes']['carbon_lb'], response['data']['attributes']['carbon_kg'], response['data']['attributes']['carbon_mt'], response['data']['attributes']['estimated_at'],)
                cursor.execute(query, insert)
                connection.commit()
                cursor.close()
        else:
            response = "Failed to calculate"
    except sqlite3.Error as error:
        print("Database error:", error)
        response = "Database error"
    except:
        response = "Failed to calculate"
    return response



def electricityCarbonEstimate (unit, value, country, state):
    if state:
        data = {
            "type": "electricity",
            "electricity_unit": unit,
            "electricity_value": value,
            "country": country,
            "state": state,
            }
    else:
        data = {
            "type": "electricity",
            "electricity_unit": unit,
            "electricity_value": value,
            "country": country,
            }
    
    headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

    try:
        response = requests.post(f"{base_URL}estimates", headers=headers, json=data)
        if response.status_code == 201:
            response = response.json()
            if current_user.is_authenticated:
                cursor = connection.cursor()
                query = "INSERT INTO energyCalculation (userID, country, state, unit, value, grams, pounds, kilograms, metricTon, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                insert = (current_user.id, response['data']['attributes']['country'], response['data']['attributes']['state'], response['data']['attributes']['electricity_unit'], response['data']['attributes']['electricity_value'], response['data']['attributes']['carbon_g'], response['data']['attributes']['carbon_lb'], response['data']['attributes']['carbon_kg'], response['data']['attributes']['carbon_mt'], response['data']['attributes']['estimated_at'],)
                cursor.execute(query, insert)
                connection.commit()
                cursor.close()
        else:
            response = "Failed to calculate"
    except sqlite3.Error as error:
        print("Database error:", error)
        response = "Database error"
    except:
        response = "Failed to calculate"
    return response


#Creates the URL for the pages
@app.route('/products')
def products():
    products = getProducts()
    return render_template('products.html', products=products)

@app.route('/schedule', methods = ['GET', 'POST'])
def schedule():
    productTypes = getProductTypes()
    if request.method == 'POST':
        user_data = []
        user_data.append(request.form['firstName'])
        user_data.append(request.form['lastName'])
        user_data.append(request.form['email'])
        user_data.append(request.form['phone'])
        user_data.append(request.form['password'])
        user_data.append(request.form['confirmPassword'])

        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email=?", (user_data[2],))
            user = cursor.fetchone()
        except sqlite3.Error as error:
            print("Database error:", error)
        finally:
            cursor.close()
        
        if user:
            flash("There is already a user with this email, please try again")
            return render_template('schedule.html', productTypes=productTypes, user_data=user_data)
        
        try:
            if user_data[4] != user_data[5]:
                flash("The passwords do not match, please try again")
                return render_template('schedule.html', productTypes=productTypes, user_data=user_data)
            elif len(user_data[4]) < 8:
                flash("The password must be at least 8 characters long, please try again")
                return render_template('schedule.html', productTypes=productTypes, user_data=user_data)
            elif user_data[4] == user_data[5]:
                cursor = connection.cursor()
                query = "INSERT INTO users (firstName, lastName, email, phone, password) VALUES (?, ?, ?, ?, ?)"
                insert_data =  (user_data[0], user_data[1], user_data[2], user_data[3], generate_password_hash(user_data[4]),)
                cursor.execute(query, insert_data)# The insert is completed like this to stop SQL injection
                connection.commit()# Makes the information stay in the database.
            else:
                flash("Unknown error")
                return render_template('schedule.html', productTypes=productTypes, user_data=user_data)
        except sqlite3.Error as error:
            print("Database error:", error)
            flash("Database error")
            return render_template('schedule.html', productTypes=productTypes, user_data=user_data)
        finally:
            cursor.close()

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (user_data[2],))
        user = cursor.fetchone()
        cursor.close()
        login_user(User(id=user[0], firstName=user[1], lastName=user[2], email=user[3], phone=user[4], password=user[5]))
        flash("Account successfully created")
        try:
            scheduleConsultation(request.form['typeID'], request.form['timeslot'])
            flash(f"Consultation scheduled for {request.form['timeslot']}, about {request.form['typeID']}")
            return redirect(url_for('user'))
        except:
            flash("Failure to schedule consultation")
        
        
    else:
        return render_template('schedule.html', productTypes=productTypes)

@app.route('/')
@app.route('/about-us')
def about():
    return render_template('about.html')

@app.route('/your-carbon-footprint', methods = ['GET', 'POST'])
def carbonFootprint():
    if request.method == 'POST':
        if request.form['form_id'] == 'carbon-estimate':    
            response = vehicleCarbonEstimate(request.form['vehicle-unit'], int(request.form['vehicle-value']), request.form['ID'])
        elif request.form['form_id'] == 'electricity-estimate':
            if request.form['state']:
                response = electricityCarbonEstimate(request.form['energy-unit'], int(request.form['energy-value']), request.form['country'], request.form['state'])
            else:
                response = electricityCarbonEstimate(request.form['energy-unit'], int(request.form['energy-value']), request.form['country'], False)
        if response == "Database error" or response == "Failed to calculate":
            flash(response)
            return render_template('carbon-footprint.html')
        else:
            return render_template('carbon-footprint.html', response=response)
    else:
        return render_template('carbon-footprint.html')

@app.route('/log-in', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = []
        user_data.append(request.form['email'])
        user_data.append(request.form['password'])

        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (user_data[0],))
            user = cursor.fetchone()
        except sqlite3.Error as error:
            print("Database error:", error)
        finally:
            cursor.close()
        
        if user:
            if check_password_hash(user[5], user_data[1]): #[5] is the password field
                login_user(User(id=user[0], firstName=user[1], lastName=user[2], email=user[3], phone=user[4], password=user[5]))
                flash("Logged in successfully")
                return redirect(url_for('user'))
            else:
                flash("Log in details are incorrect, please try again")
                return render_template('login.html', user_data=user_data)
        else:
            flash("Email does not match someone on the system, please try again")
            return render_template('login.html', user_data=user_data)
    else:
        return render_template('login.html')

@app.route('/log-out')
@login_required
def logout():
    logout_user()
    return redirect(url_for('about'))

@app.route('/user-panel', methods=['GET', 'POST'])
@login_required
def user():
    if request.method=='POST':
        if request.form['form_id'] == 'schedule-consultation':
            try:
                scheduleConsultation(request.form['typeID'], request.form['timeslot-consultation'])
            except:
                flash("Error, missing a field")
        elif request.form['form_id'] == 'schedule-installation':
            try:
                scheduleInstallation(request.form['productID'], request.form['timeslot-installation'])
            except:
                flash("Error, missing a field")
        elif request.form['form_id'] == 'delete-consultation':
            try:
                cursor = connection.cursor()
                query = "DELETE FROM consultations WHERE id=?"
                insert = (request.form['id'])
                cursor.execute(query, insert)
                connection.commit
                flash("Successfully deleted consultation")
            except sqlite3.Error as error:
                print("Database error:", error)
                flash("Error deleting consultation")
            finally:
                cursor.close()
        elif request.form['form_id'] == 'delete-installation':
            try:
                cursor = connection.cursor()
                query = "DELETE FROM installations WHERE id=?"
                insert = (request.form['id'])
                cursor.execute(query, insert)
                connection.commit
                flash("Successfully deleted installation")
            except sqlite3.Error as error:
                print("Database error:", error)
                flash("Error deleting installation")
            finally:
                cursor.close()
        elif request.form['form_id'] == 'delete-vehicle-estimate':
            try:
                cursor = connection.cursor()
                query = "DELETE FROM carbonFootprintCalculation WHERE id=?"
                insert = (request.form['id'])
                cursor.execute(query, insert)
                connection.commit
                flash("Successfully deleted calculation")
            except sqlite3.Error as error:
                print("Database error:", error)
                flash("Error deleting calculation")
            finally:
                cursor.close()
        elif request.form['form_id'] == 'delete-energy-estimate':
            try:
                cursor = connection.cursor()
                query = "DELETE FROM energyCalculation WHERE id=?"
                insert = (request.form['id'])
                cursor.execute(query, insert)
                connection.commit
                flash("Successfully deleted calculation")
            except sqlite3.Error as error:
                print("Database error:", error)
                flash("Error deleting calculation")
            finally:
                cursor.close()
        else:
            flash("Unknown error")
    products = getProducts()
    productTypes = getProductTypes()
    consultations = getConsultations()
    installations = getInstallations()
    vehicleEstimations = getVehicleEstimations()
    energyEstimations = getEnergyEstimations()
    return render_template('user.html', products=products, productTypes=productTypes, consultations=consultations, installations=installations, vehicleEstimations=vehicleEstimations, energyEstimations=energyEstimations)

@app.route('/privacy-policy')
def policy():
    return render_template('privacy.html')

@app.route('/vehicle-ID', methods=['GET', 'POST'])
def vehicleID():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        }
    if request.method == 'POST':
        try:
            vehicleMakeID = request.form['vehicle_make_id']
            response = requests.get(f"{base_URL}vehicle_makes/{vehicleMakeID}/vehicle_models", headers=headers)
            if response.status_code == 200:
                response = response.json()
                return render_template('vehicle-id.html', vehicles=response)
            else:
                response = "Failed to calculate"
                flash(response)
                return render_template('vehicle-id.html')
        except:
            response = "Failed to calculate"
            flash(response)
            return render_template('vehicle-id.html')
    else:
        try:
            response = requests.get("https://www.carboninterface.com/api/v1/vehicle_makes", headers=headers)
            if response.status_code == 200:
                response = response.json()
                return render_template('vehicle-id.html', vehicles=response)
            else:
                response = "Failed to calculate"
                flash(response)
                return render_template('vehicle-id.html')
        except:
            response = "Failed to calculate"
            flash(response)
            return render_template('vehicle-id.html')
        

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')


#Allows the system to run these pages. Debug mode is on so when changes are made the website is refreshed.
if __name__ == '__main__':
    app.run(debug=True)