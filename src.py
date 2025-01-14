from datetime import datetime
import os

from sqlalchemy import null
from app import app
import urllib.request
import sqlite3
import secrets 
import time
import boto3
import json
import base64
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory, send_file, jsonify, g, abort
from werkzeug.utils import secure_filename
from PIL import Image

#download, thumbnail, delete, select, sqlite, google vision ai, list images, location(extracted from image file), timestamp, description(in s3), posts should have user id instead of name

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
conn = sqlite3.connect('pic_gallery.db')

DATABASE = 'pic_gallery.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

f = open('creds.json')
creds = json.load(f)

def upload_s3(filepath, username, filename):
    BUCKET = creds['s3_creds'][0]["BUCKET"]
    ACCESS_KEY = creds['s3_creds'][0]["ACCESS_KEY"]
    SECRET_KEY = creds['s3_creds'][0]["SECRET_KEY"]
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)

    s3.upload_file(filepath, BUCKET, username + '/' + filename)

def list_s3():
    BUCKET = creds['s3_creds'][0]["BUCKET"]
    ACCESS_KEY = creds['s3_creds'][0]["ACCESS_KEY"]
    SECRET_KEY = creds['s3_creds'][0]["SECRET_KEY"]
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
    contents = []
    ret_val = []
    for item in s3.list_objects(Bucket=BUCKET)['Contents']:
        contents.append(item)
    return contents
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
def encode_string(password):
    password_bytes = password.encode('ascii')
    encoded_bytes = base64.b64encode(password_bytes)
    return encoded_bytes.decode("ascii")
# Check user in database
def auth_check(auth_query, password):
    con = get_db()
    cur = get_db().cursor()

    cur.execute(auth_query)
    rows = cur.fetchall()
    if rows == []:
        con.commit()
        return 'Wrong username'
    else:
        if password != rows[0][2]:
            con.commit()
            return 'Wrong password'
    con.commit()
    return 1

def get_uid(name):
    con = get_db()
    cur = get_db().cursor()
    query = 'SELECT USER_ID FROM USERS WHERE(USER_NAME = "' + name + '")'
    cur.execute(query)
    rows = cur.fetchall()
    return rows[0][0]


# Create user and write to database
@app.route('/create_user', methods=['GET'])
def create_user():
    args = request.args
    name = args.get('name', type=str)
    password = args.get('password', type=str)
    encoded_password = encode_string(password)
    #conn.execute("INSERT INTO USERS (NAME, PASSWORD ) VALUES (" + name + ", " + password ")")
    query = 'INSERT INTO USERS(USER_NAME,PASSWORD) VALUES("'  + name + '", "' + encoded_password + '")'
    con = get_db()
    cur = get_db().cursor()
    cur.execute(query)
    con.commit()
    path = './userdirs/' + name
    thumbnail_path = './thumbnails/' + name
    if not os.path.exists(path):
        os.makedirs(path)
        os.makedirs(thumbnail_path)
    return 'Created user'

@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(name)


# Downloads all posts belonging to user, returns s3 elements of the user. Will add topic filtering in the future
@app.route('/download_posts', methods=['GET'])
def download_posts():
    name = request.args.get('name', type=str)
    password = request.args.get('password', type=str)
    encoded_password = encode_string(password)
    post_topic = request.args.get('topic', type=str)
    print(post_topic)
    posts = []
    contents = list_s3()
    for c in contents:
        key = c['Key']
        username = key.split('/')[0]
        if username == name:
            BUCKET = creds['s3_creds'][0]["BUCKET"]
            ACCESS_KEY = creds['s3_creds'][0]["ACCESS_KEY"]
            SECRET_KEY = creds['s3_creds'][0]["SECRET_KEY"]
            s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
            with open('downloads/' + key.split('/')[1], 'wb') as f:
                s3.download_fileobj(BUCKET, key, f)
                posts.append(c)
    return jsonify(posts)

@app.route('/download_key', methods=['GET'])
def download_key():
    name = request.args.get('name', type=str)
    password = request.args.get('password', type=str)
    encoded_password = encode_string(password)
    key = request.args.get('key', type=str)
    con = get_db()
    cur = get_db().cursor()
    auth_query = 'SELECT * FROM USERS WHERE USER_NAME="' + name + '";'

    res = auth_check(auth_query, encoded_password)
    if res != 1:
        abort(401)
    uid = get_uid(name)
    post_check_query = 'SELECT * FROM POSTS WHERE USER_ID=' + str(uid)  + ';'
    contents = cur.execute(post_check_query)
    con.commit()
    print(contents)
    if contents == []:
        abort(401)
    else:
        try:
            BUCKET = creds['s3_creds'][0]["BUCKET"]
            ACCESS_KEY = creds['s3_creds'][0]["ACCESS_KEY"]
            SECRET_KEY = creds['s3_creds'][0]["SECRET_KEY"]
            s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
            with open('downloads/' + key.split('/')[1], 'wb') as f:
                s3.download_fileobj(BUCKET, key, f)
        except:
            return 'No such object "' + key + '".'

    return 'Object ' + key + ' downloaded.'

@app.route('/list_posts', methods=['GET'])
def list_posts():
    name = request.args.get('name', type=str)
    password = request.args.get('password', type=str)
    encoded_password = encode_string(password)
    post_topic = request.args.get('topic', type=str)
    con = get_db()
    cur = get_db().cursor()
    auth_query = 'SELECT * FROM USERS WHERE USER_NAME="' + name + '";'

    res = auth_check(auth_query, encoded_password)
    if res != 1:
        abort(401)
    uid = get_uid(name) 
    post_query = 'SELECT * FROM POSTS WHERE USER_ID=' + str(uid) + ';'
    posts = []
    contents = cur.execute(post_query)
    con.commit()
    for c in contents:
        posts.append(c)
        print(c)
    return jsonify(posts)



# Upload image to s3 and insert post to posts table
@app.route('/upload_post', methods=['GET', 'POST'])
def upload_file():
    name = request.args.get('name', type=str)
    password = request.args.get('password', type=str)
    encoded_password = encode_string(password)
    post_topic = request.args.get('topic', type=str)
    if post_topic == null:
        post_topic = ''
#    if not os.path.exists('./userdirs/' + name):
#        return 'sen kimsin'

    auth_query = 'SELECT * FROM USERS WHERE USER_NAME="' + name + '";'

    res = auth_check(auth_query, encoded_password)
    if res != 1:
        abort(401)
    user_id = get_uid(name)
    con = get_db()
    cur = get_db().cursor()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('userdirs/' + name + '/', filename))
            image = Image.open('userdirs/' + name + '/' + filename)
            image.thumbnail((400,400))
            image.save('thumbnails/' + name + '/' + filename, optimize=True, quality=40)
            upload_s3('thumbnails/' + name + '/' + filename, 'thumbnails/' + name, filename)
            upload_s3('userdirs/' + name + '/' + filename, name, filename)
            post_query = 'INSERT INTO POSTS(FILE_NAME, USER_ID, POST_TAG, S3_KEY, POST_DATE) VALUES("'  + filename + '", ' + str(user_id) + ', "' + str(post_topic) + '", "' + name + '/' + filename + '", "' + str(time.time()) + '")'
            cur.execute(post_query)
            con.commit()
            return send_file('./userdirs/' + name + '/' + filename)
    return '''
    <!doctype html>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == "__main__":
    app.run()