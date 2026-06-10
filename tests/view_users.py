from flask import Blueprint, jsonify
import sqlite3

DATABASE = "users.db"

view_users_bp = Blueprint("view_users", __name__)

@view_users_bp.route("/view_users", methods=["GET"])
def view_users():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    conn.close()

    return jsonify([dict(user) for user in users])