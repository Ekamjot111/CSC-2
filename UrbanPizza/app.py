from flask import Flask, render_templete

app = Flask(_name_)

@app.route("/")
def home():
    return render_templete('index.html')

@app.route("/menu")
def menu():
    return render_templete('menu.html')

@app.route("/order")
def order():
    return render_templete('order.html')

@app.route("/reciept")
def menu():
    return render_templete('reciept.html')

if __name__ == "__main__":
    app.run(debug=True)