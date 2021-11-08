from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#kullanıcı kayıt formu 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek için lütfen giriş yapın...", "danger")
            return redirect(url_for("login"))
    return decorated_function


class RegisterForm(Form):
    name = StringField("Ad Soyad", validators=[validators.length(min=4, max=25)])
    username = StringField("Kullanıcı Adı", validators=[validators.length(min=4, max=35)])
    email = StringField("Email", validators=[validators.Email(message="Lütfen geçerli email adresi giriniz")])
    password = PasswordField("Şifre", validators=[
        validators.DataRequired(message="lütfen bir parola belirleyiniz..."),
        validators.EqualTo(fieldname="confirm", message="parolanız uyuşmuyor...")
    ])
    confirm = PasswordField("Şifre Tekrar")
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")
class ContactForm(Form):
    name = StringField("Name")
    email = StringField("Email", validators=[validators.Email(message="Lütfen geçerli email adresi giriniz")])
    message = TextAreaField("Message", validators=[validators.length(min=4, max=50)])
class ProfileForm(Form):
    name = StringField("Ad Soyad", validators=[validators.length(min=4, max=25)])
    username = StringField("Kullanıcı Adı", validators=[validators.length(min=4, max=35)])
    email = StringField("Email", validators=[validators.Email(message="Lütfen geçerli email adresi giriniz")])


app = Flask(__name__)
app.secret_key="ybblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
 #kullanıcı giriş decorator
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0 :
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")


@app.route("/")
def index():
   
   
    return render_template("index.html", articles = articles)
@app.route("/about")
def about():
    return render_template("about.html")
#kayıt olma
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu, (name, email, username, password))
        mysql.connection.commit()
        # veritabanında işlem yapılacağı zaman bu işlem yapılmalı
        cursor.close()
        flash("Başarıyla Kayıt Gerçekleşti", "success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

#login işlemi
@app.route("/login", methods =["GET","POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Giriş Başarılı..","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz...", "danger")
                return redirect(url_for("login"))
        else:
            flash("Kullanıcı adı bulunamadı..", "danger")
            return redirect(url_for("login"))


    return render_template("login.html", form=form)
#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#makale ekleme
@app.route("/addarticle", methods =["GET","POST"])
def addArticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()

        cursor.close()

        flash("Makale Başarı İle Eklendi", "success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form=form)
#makale form
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.length(min=5,max=100)])
    content = TextAreaField("Makale İçeriği", validators=[validators.length(min = 10)])

#makale sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT*FROM articles"
    result = cursor.execute(sorgu)

    if result > 0 :
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")

#detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0 :
        article = cursor.fetchone()
        return render_template("article.html", article = article)

    else:
        return render_template("article.html")
#makale silme 
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"], id))
    if result > 0:
        sorgu2 = "DELETE FROM articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işlem için yetkiniz yok.", "danger")
        return redirect(url_for("index"))
#makale güncelleme

@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles where id = %s and author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle Bir Makale yok veya bu işleme yetkiniz yok..", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)

    else:
        #Post request kısmı
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "UPDATE articles SET title = %s, content= %s where id = %s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale başarıyla güncellendi", "success")
        return redirect(url_for("dashboard"))

#arama url
@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles where title LIKE '%" + keyword +"%'"
        result = cursor.execute(sorgu)
        if result == 0 :
            flash("aranan kelimeye uygun makale bulunamadı", "warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)


@app.route("/profile",methods = ["GET", "POST"])
@login_required
def profile():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT*FROM users where username = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0 :
        users = cursor.fetchone
        return render_template("profile.html", users = users)
    else:
        return render_template("profile.html")


@app.route("/contact", methods = ["GET", "POST"])
def contact():
    form = ContactForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        message =form.message.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO contact(name,email,message) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(name, email, message))
        mysql.connection.commit()
        # veritabanında işlem yapılacağı zaman bu işlem yapılmalı
        cursor.close()
        flash("Başarıyla Mesajınız Gönderildi", "success")

        return redirect(url_for("contact"))
    else:
        return render_template("contact.html", form=form)

    return render_template("contact.html") 
if __name__ == "__main__":
    app.run(debug=True)
      