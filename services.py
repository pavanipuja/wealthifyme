# services.py

import re
from datetime import date

from db import mysql  

def check_user(email, password):
    check_mail=validate_user_email(email)
    if(not check_mail):
        return False
    else:
        con = mysql.connect
        cur = con.cursor()
        cur.execute("SELECT * FROM login WHERE email=%s AND password=%s", (email, password))
        res = cur.fetchone()
        cur.close()
        con.close()
        if res:
            return True
        return False

def registration(name,email,password,confirm_password,hint_question,hint_answer):
    check_mail=validate_user_email(email)
    if(not check_mail):
        return False
    else:
        if(password==confirm_password):
            con=mysql.connect
            cur=con.cursor()
            cur.execute("insert into registration(name,email,password,date,hint_question,hint_answer) values(%s,%s,%s,current_date(),%s,%s)",(name,email,password,hint_question,hint_answer))
            con.commit()
            cur.close()
            con.close() 
            return True
        else:
            return False
    
def validate_user_email(email):
    res=re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',email)
    if(res):
        return True
    else:
        return False
