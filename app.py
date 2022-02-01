from flask import Flask, g, request , session, redirect
from flask.helpers import url_for
from flask.templating import render_template
from database import get_database
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
import math

UPLOAD_FOLDER = 'C:/Users/bbkbh/OneDrive/Desktop/project/review_analysis/hotel_review_app\\static'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)
tfvect = TfidfVectorizer(stop_words='english', max_df=0.7)
loaded_model = pickle.load(open('review_model.pkl', 'rb'))
dataframe = pd.read_csv('fake_reviews_dataset.csv')
x = dataframe['text']
y = dataframe['label']
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
tfid_x_train = tfvect.fit_transform(x_train.values.astype('U'))
tfid_x_test = tfvect.transform(x_test.values.astype('U'))

def fake_review_det(review):
    input_data = [review]
    vectorized_input_data = tfvect.transform(input_data)
    prediction = loaded_model.predict(vectorized_input_data)
    return prediction

@app.route('/addreview/<hotelid>', methods = ["POST", "GET"])
def addreview(hotelid):
    user = get_current_user()
    db = get_database()

    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()

    hotel_one = db.execute("select * from hotel where hotelid = ?",[hotelid])
    single_hotel = hotel_one.fetchone()

    review_cur = db.execute("select * from review where hotelid = ?",[hotelid])
    allreviews = review_cur.fetchall()
    if request.method == 'POST':
        review_rating = request.form['rating']
        review1 = request.form['message']
        pred = fake_review_det(review1)
        if pred == ['OR']:
            db.execute('insert into review(username,rating,review,fake,real,verified\
            ,liked,disliked,hotelid) values(?,?,?,?,?,?,?,?,?)',[user['username'], 
            review_rating,review1,0,1,0,0,0,hotelid])
            db.commit()
            return redirect(url_for('viewreview', hotelid  = hotelid))
        elif pred == ['CG']:
            db.execute('insert into review(username,rating,review,fake,real,verified,liked,\
            disliked,hotelid) values(?,?,?,?,?,?,?,?,?)',[user['username'],
             review_rating,review1,0,0,0,0,0,hotelid])
            db.commit()
            return redirect(url_for('viewreview', hotelid  = hotelid))

    return render_template('addreview.html',allhotels = allhotels,
        allreviews=allreviews,single_hotel = single_hotel,user = user)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.teardown_appcontext
def close_database(error):
    if hasattr(g, 'hotel_db'):
        g.hotel_db.close()

def get_current_user():
    # there is no current user at the beginning.
    user_result = None
    if 'user' in session:
        user = session['user']
        # fetch that user from the database , which is entered by the user 
        db = get_database()
        user_cur = db.execute('select * from users where username = ?', [user])
        user_result = user_cur.fetchone()
    
    # return that user in every route.
    return user_result

@app.route('/')
def homepage():
    user = get_current_user()
    # and we will pass the user , to the home.html page.
    return render_template('index.html' , user = user)

@app.route('/register', methods = ["POST", "GET"])
def register():
    user = get_current_user()
    if request.method == 'POST':
        db = get_database()
        hashed_password = generate_password_hash(request.form['password'], method = 'sha256')
        db.execute('insert into users (username,password,admin,reviewed) values (?,?,?,?)', 
            [request.form['username'],hashed_password,'0','0'])
        db.commit()
        session['user'] = request.form['username']
        return redirect(url_for('homepage'))
    return render_template('register.html' , user = user)

@app.route('/login', methods = ["POST", "GET"])
def login():
    user = get_current_user()
    if request.method == 'POST':
        db = get_database()

        # get the values entered by the user from the login form .
        name = request.form['username']
        password_user_entered = request.form['password']

        user_fetched_from_db = db.execute('select username,password,admin,reviewed from users where username = ?', [name])
        user_fetched_result = user_fetched_from_db.fetchone()

        # check the hashcode for password in database and password entered by the user, then create the session 
        #object . and pass it to other pages. 
        if check_password_hash(user_fetched_result['password'],  password_user_entered):
            session['user'] = user_fetched_result['username']
            return redirect(url_for('homepage'))
        else:
            return '<h1> Password is incorrect </h1>'
    return render_template('login.html', user = user)

@app.route('/inserthotel', methods = ["POST", "GET"])
def inserthotel():
    user = get_current_user()
    db = get_database()
    if request.method == 'POST':
        hotelname = request.form['hotelname']
        hotel_image = str(hotelname)+'.jpg'
        address = request.form['address']
        overall_rating = request.form['overall_rating']
        weblink = request.form['weblink']
        phone = request.form['phone']
        totalmenu = request.form['totalmenu']
        totalworkers = request.form['totalworkers']
        db.execute('insert into hotel(hotelname, address,overall_rating, weblink,\
        phone,image_name, totalmenu,totalworkers) values (?,?,?,?,?,?,?,?)'
        ,[hotelname, address,overall_rating, weblink, phone, hotel_image, totalmenu,totalworkers])
        db.commit()
        return render_template('upload_file.html',user = user)
    return render_template('inserthotel.html',user = user)

@app.route('/viewallhotels', methods = ["POST", "GET"])
def viewallhotels():
    user = get_current_user()
    db = get_database()
    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()
    return render_template('viewallhotels.html', allhotels = allhotels,user = user)

@app.route('/viewonehotel/<name>')
def viewonehotel(name):
    user = get_current_user()
    db = get_database()
    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()
    
    hotel_one = db.execute("select * from hotel where image_name = ?",[name])
    single_hotel = hotel_one.fetchone()

    all_count_cur = db.execute("select count(review) as all_count,sum(real)\
    as real_count,sum(verified) as verify_count from review,hotel on\
    hotel.hotelid = review.hotelid where hotel.image_name = ?",[name])
    all_count = all_count_cur.fetchone()
    if all_count['all_count'] == 0:
        return render_template('viewonehotel.html' , name = name,
            allhotels = allhotels,single_hotel = single_hotel,
            all_count = all_count,user = user)
    else:
        return render_template('viewonehotel.html' , name = name,
            allhotels = allhotels,single_hotel = single_hotel,
            all_count = all_count,user = user, auth = int((all_count['real_count'] / all_count['all_count'] )*100))

@app.route('/updatereview/<userid>')
def updatereview(userid):
    user = get_current_user()
    db = get_database()
    hotelid_cur = db.execute("select * from review where userid = ?",[userid])
    hoteldetails = hotelid_cur.fetchone()

    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()

    hotel_one = db.execute("select * from hotel where hotelid = ?",
        [hoteldetails['hotelid']])
    single_hotel = hotel_one.fetchone()

    review_cur = db.execute("select * from review where verified = '0'\
     and hotelid = ? and real = 1",[hoteldetails['hotelid']])
    allreviews = review_cur.fetchall()

    all_count_cur = db.execute("select count(review) as all_count,sum(real)\
        as real_count,sum(verified) as verify_count from review,hotel on\
        hotel.hotelid = review.hotelid where hotel.hotelid = ?",[hoteldetails['hotelid']])
    all_count = all_count_cur.fetchone()

    if request.method == 'GET':
        db.execute("update review set verified = 1 where userid = ? ",[userid])
        db.commit()
        return redirect(url_for('verifyreview', hotelid  = hoteldetails['hotelid'] ))
    return render_template('verifyreview.html',allhotels = allhotels,
        allreviews=allreviews,single_hotel = single_hotel,
        all_count = all_count,user = user)

@app.route('/viewauthenticated/<hotelid>')
def viewauthenticated(hotelid):
    user = get_current_user()
    db = get_database()
    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()
    
    review_cur = db.execute("select * from review where hotelid = ? and Real = 1",[hotelid])
    allreviews = review_cur.fetchall()

    hotel_one = db.execute("select * from hotel where hotelid = ?",[hotelid])
    single_hotel = hotel_one.fetchone()
    return render_template('viewauthenticated.html',allhotels = allhotels,
        allreviews=allreviews,single_hotel = single_hotel 
        ,user = user)

@app.route('/viewreview/<hotelid>')
def viewreview(hotelid):
    user = get_current_user()
    db = get_database()
    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()
    
    review_cur = db.execute("select * from review where hotelid = ?",[hotelid])
    allreviews = review_cur.fetchall()

    hotel_one = db.execute("select * from hotel where hotelid = ?",[hotelid])
    single_hotel = hotel_one.fetchone()
    return render_template('viewreview.html',allhotels = allhotels,
        allreviews=allreviews,single_hotel = single_hotel
        ,user = user)



@app.route('/viewverify/<hotelid>')
def viewverify(hotelid):
    user = get_current_user()
    db = get_database()
    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()
    
    review_cur = db.execute("select * from review where hotelid = ? and verified  = 1",[hotelid])
    allreviews = review_cur.fetchall()

    hotel_one = db.execute("select * from hotel where hotelid = ?",[hotelid])
    single_hotel = hotel_one.fetchone()
    return render_template('verifiedreviews.html',allhotels = allhotels,
        allreviews=allreviews,single_hotel = single_hotel,
        user = user)

@app.route('/sortbyrating/<hotelid>')
def sortbyrating(hotelid):
    user = get_current_user()
    db = get_database()
    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()
    
    review_cur = db.execute("select * from review where\
        hotelid = ? order by rating desc",[hotelid])
    allreviews = review_cur.fetchall()

    hotel_one = db.execute("select * from hotel where\
        hotelid = ?",[hotelid])
    single_hotel = hotel_one.fetchone()

    return render_template('viewreview.html',allhotels = allhotels,
        allreviews=allreviews,single_hotel = single_hotel,
        user = user)

@app.route('/verifyreview/<hotelid>')
def verifyreview(hotelid):
    user = get_current_user()
    db = get_database()
    hotel_cur = db.execute("select * from hotel")
    allhotels = hotel_cur.fetchall()
    
    review_cur = db.execute("select * from review where verified = '0'\
     and hotelid = ? and real = 1",[hotelid])
    allreviews = review_cur.fetchall()

    hotel_one = db.execute("select * from hotel where hotelid = ?",[hotelid])
    single_hotel = hotel_one.fetchone()

    all_count_cur = db.execute("select count(review) as all_count,sum(real)\
     as real_count,sum(verified) as verify_count from review,hotel on\
      hotel.hotelid = review.hotelid where hotel.hotelid = ?",[hotelid])
    all_count = all_count_cur.fetchone()
    if all_count['all_count'] == 0:
        return render_template('verifyreview.html',
            allhotels = allhotels,single_hotel = single_hotel,
            all_count = all_count,user = user,allreviews=allreviews )
    else:
        return render_template('verifyreview.html' ,
            allhotels = allhotels,single_hotel = single_hotel,
            all_count = all_count,user = user,allreviews=allreviews , auth = int((all_count['real_count'] / all_count['all_count'] )*100))


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    user = get_current_user()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits 
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('viewonehotel', name = filename))
    return render_template('upload_file.html',user = user)

@app.route('/uploads/<name>')
def download_file(name):
    user = get_current_user()
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('homepage'))

if __name__ == '__main__':
    app.run(debug = True)