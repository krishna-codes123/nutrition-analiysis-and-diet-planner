from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector

app = Flask(__name__)


# =========================================================
# MYSQL CONNECTION
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="nutrition_db",
        port=3306
    )


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# GENERATE NUTRITION REPORT
# =========================================================

@app.route("/generate_report", methods=["POST"])
def generate_report():

    try:
        data = request.get_json()

        name = data.get("name")
        age = data.get("age")
        gender = data.get("gender")
        height = data.get("height")
        weight = data.get("weight")
        diabetes = data.get("diabetes")
        bp = data.get("bp")
        surgery = data.get("surgery")

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not name or not age or not gender or not height or not weight:
            return jsonify({
                "success": False,
                "error": "Please fill all the Client details."
            })

        age = int(age)
        height = float(height)
        weight = float(weight)

        if height <= 0 or weight <= 0:
            return jsonify({
                "success": False,
                "error": "Height and Weight must be greater than 0."
            })

        # -------------------------------------------------
        # BMI CALCULATION
        # -------------------------------------------------

        height_meter = height / 100

        bmi = weight / (height_meter * height_meter)

        bmi = round(bmi, 2)

        # -------------------------------------------------
        # BMI STATUS
        # -------------------------------------------------

        if bmi < 18.5:
            bmi_status = "Underweight"
            recommendation = (
                "Your BMI indicates that you are underweight. "
                "Include nutritious calorie-dense foods, protein-rich foods "
                "and maintain regular meals."
            )

        elif bmi < 25:
            bmi_status = "Normal"
            recommendation = (
                "Your BMI is in the normal range. "
                "Continue with a balanced diet, regular physical activity "
                "and adequate water intake."
            )

        elif bmi < 30:
            bmi_status = "Overweight"
            recommendation = (
                "Your BMI indicates that you are overweight. "
                "Focus on balanced meals, vegetables, whole grains, "
                "adequate protein and regular physical activity."
            )

        else:
            bmi_status = "Obese"
            recommendation = (
                "Your BMI is in the obese range. "
                "Choose balanced meals, reduce highly processed foods "
                "and maintain regular physical activity. "
                "Professional dietary guidance may be helpful."
            )

        # -------------------------------------------------
        # INSERT CLIENT INTO DATABASE
        # -------------------------------------------------

        connection = get_db_connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO clients
            (
                name,
                age,
                gender,
                height,
                weight,
                bmi,
                bmi_status,
                diabetes,
                bp,
                surgery
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            age,
            gender,
            height,
            weight,
            bmi,
            bmi_status,
            diabetes,
            bp,
            surgery
        )

        cursor.execute(sql, values)

        connection.commit()

        client_id = cursor.lastrowid

        cursor.close()
        connection.close()

        # -------------------------------------------------
        # CLIENT RESPONSE
        # -------------------------------------------------

        client = {
            "id": client_id,
            "name": name,
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,
            "bmi": bmi,
            "bmi_status": bmi_status,
            "diabetes": diabetes,
            "bp": bp,
            "surgery": surgery
        }

        return jsonify({
            "success": True,
            "client": client,
            "recommendation": recommendation
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })


# =========================================================
# CLIENT HISTORY
# =========================================================

@app.route("/history")
def history():

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                age,
                gender,
                height,
                weight,
                bmi,
                bmi_status,
                diabetes,
                bp,
                surgery
            FROM clients
            ORDER BY id DESC
        """)

        clients = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "history.html",
            clients=clients
        )

    except Exception as e:

        return str(e)


# =========================================================
# DELETE CLIENT
# =========================================================

@app.route("/delete/<int:id>")
def delete_client(id):

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM clients WHERE id = %s",
            (id,)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("history"))

    except Exception as e:

        return str(e)


# =========================================================
# EDIT CLIENT - GET
# =========================================================

@app.route("/edit/<int:id>", methods=["GET"])
def edit_client(id):

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM clients WHERE id = %s",
            (id,)
        )

        client = cursor.fetchone()

        cursor.close()
        connection.close()

        if client is None:
            return "Client not found"

        return render_template(
            "edit.html",
            client=client
        )

    except Exception as e:

        return str(e)


# =========================================================
# EDIT CLIENT - POST
# =========================================================

@app.route("/edit/<int:id>", methods=["POST"])
def update_client(id):

    try:

        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        height = request.form.get("height")
        weight = request.form.get("weight")
        diabetes = request.form.get("diabetes")
        bp = request.form.get("bp")
        surgery = request.form.get("surgery")

        age = int(age)
        height = float(height)
        weight = float(weight)

        # -------------------------------------------------
        # RECALCULATE BMI
        # -------------------------------------------------

        height_meter = height / 100

        bmi = weight / (height_meter * height_meter)

        bmi = round(bmi, 2)

        if bmi < 18.5:
            bmi_status = "Underweight"

        elif bmi < 25:
            bmi_status = "Normal"

        elif bmi < 30:
            bmi_status = "Overweight"

        else:
            bmi_status = "Obese"

        # -------------------------------------------------
        # UPDATE CLIENT
        # -------------------------------------------------

        connection = get_db_connection()
        cursor = connection.cursor()

        sql = """
            UPDATE clients
            SET
                name = %s,
                age = %s,
                gender = %s,
                height = %s,
                weight = %s,
                bmi = %s,
                bmi_status = %s,
                diabetes = %s,
                bp = %s,
                surgery = %s
            WHERE id = %s
        """

        values = (
            name,
            age,
            gender,
            height,
            weight,
            bmi,
            bmi_status,
            diabetes,
            bp,
            surgery,
            id
        )

        cursor.execute(sql, values)

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("history"))

    except Exception as e:

        return str(e)


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=True
    )