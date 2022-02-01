import sqlite3
from flask import g

def connect_to_database():
    sql = sqlite3.connect('C:/Users/ashikagumbe/Desktop/engineer/review_analysis/hotel.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_database():
    if not hasattr(g, 'hotel_db'):
        g.hotel_db = connect_to_database()
    return g.hotel_db