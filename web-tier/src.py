from flask import Flask, render_template, request
import os
from aws_controller import *
import base64

app=Flask(__name__)
@app.route("/")
def indexPg():
    return render_template('index.html')

#@app.route("/uploadImg",methods=['POST'])
def upload():
    if request.method == 'POST':
        if 'img' not in request.files:
            return 'there is no file1 in form!'
        file1 = request.files['img']
        string_image = convert_image_to_string(file1)
        send_message(string_image.decode("utf-8"))
        print("---Pushing to SQS------")
        print(send_message)
    return render_template('index.html')

def convert_image_to_string(image):
    print(type(image))
    with open("/Users/srbaradi/Downloads/Test-images/test_11.JPEG", "rb") as tempImage:
        str = base64.b64encode(tempImage.read())
        print(str)
    return str

def run_classifier(path_to_file):

    return "Classifier ran successfully!"

if __name__=='__main__':
    app.run(debug=True)