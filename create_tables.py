import sqlite3

conn = sqlite3.connect('pic_gallery.db')

conn.execute('''CREATE TABLE USERS
         (USER_ID INTEGER PRIMARY KEY     AUTOINCREMENT,
         USER_NAME           TEXT    NOT NULL,
         PASSWORD TEXT NOT NULL);''')

conn.execute('''CREATE TABLE POSTS
         (POST_ID INTEGER PRIMARY KEY    AUTOINCREMENT,
         FILE_NAME           TEXT    NOT NULL,
         USER_ID INTEGER NOT NULL,
         POST_TAG TEXT,
         S3_KEY TEXT NOT NULL,
         POST_DATE TEXT,
         LOCATION TEXT,
         FOREIGN KEY(USER_ID) REFERENCES USERS(USER_ID));''')

conn.close()