import sqlite3

conn = sqlite3.connect('pic_gallery.db')

conn.execute('''CREATE TABLE USERS
         (USER_ID INT PRIMARY KEY     NOT NULL,
         NAME           TEXT    NOT NULL,
         PASSWORD TEXT NOT NULL);''')

conn.execute('''CREATE TABLE POSTS
         (POST_ID INT PRIMARY KEY     NOT NULL,
         NAME           TEXT    NOT NULL,
         USER_NAME TEXT NOT NULL,
         POST_TAG TEXT,
         S3_KEY TEXT NOT NULL,
         POST_DATE TEXT,
         LOCATION TEXT);''')

conn.close()