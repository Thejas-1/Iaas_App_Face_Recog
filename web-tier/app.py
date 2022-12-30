from logging import exception
import os
from flask import Flask,render_template,request,redirect,url_for,abort
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError
import base64
from datetime import datetime
from time import sleep
import threading
from random import randint
from autoscaling import autoscaling
from AWS_helpers import HelperAPI

api = HelperAPI()
app = Flask(__name__)
toll = 0
result_data_from_image_queue = []
request_count = 0
low_range = 0
high_range = 1000000000

def populate_global_variables():
		global result_data_from_image_queue
		global request_count
		global toll
		while(1):
			response = api.get_output_queue_attributes('ApproximateNumberOfMessages')
			messages_in_output_queue = int(response['Attributes']['ApproximateNumberOfMessages'])
			if(messages_in_output_queue > 0):
				try:
					response = api.get_message_from_output_queue()
					if 'Messages' in response:
						message = response['Messages'][0]['Body']
						receipt_handle=response['Messages'][0]['ReceiptHandle']
						message = message.split(',')
						result_data_from_image_queue.append(message)
						api.delete_from_output_queue(receipt_handle, '')
				except Exception as e:
					print("Error Occured: in Get Result to GLobal",e)
			elif(messages_in_output_queue == 0 and request_count == 0):
				toll = 0
				break


class process_images:
	def __init__(self):
		global request_count
		self.results = []
		self.files_names = {}
		now =datetime.now()
		self.date_time = now.strftime("%m%d%Y%H%M%S")
		self.result =[]
		self.request_number = request_count
	#def queue_length(self,queue_url):
	#	response = api.get_output_queue_attributes('ApproximateNumberOfMessages')
	#	messages_in_queue = int(response['Attributes']['ApproximateNumberOfMessages'])
	#	return(messages_in_queue)
	def uploaded_images(self,data):
		try:
			for uploaded_file in data:
				if uploaded_file.filename != '':
					filename = str(randint(low_range, high_range))
					new_file_name = filename
					print(new_file_name)
					self.files_names[new_file_name] = uploaded_file.filename
				if filename != '':
					uploaded = self.populate_file_in_sqs(uploaded_file,new_file_name)
		except exception as e:
			print("Error Occured in Uploaded Files Method",e)
		self.get_result_from_output_queue()
	
	#def get_file_names(self):
	#	return(self.files_names)

	def populate_file_in_sqs(self,file,filename):
		converted_string = base64.b64encode(file.read()).decode('utf-8')
		try:
			message = converted_string + ',' +str(filename)
			response = api.push_to_input_queue(message)
		except Exception as e:
			print("Some exception is there: ", e)
			return e

	def get_result_from_output_queue(self):
		global result_data_from_image_queue
		print("Retriving output messages")
		while(1):
			for message in result_data_from_image_queue:
				if message[0] in self.files_names.keys():
					result_data_from_image_queue.remove(message)
					message[0]=self.files_names[message[0]]
					self.result.append(message)
					print(message)
			if(len(self.result) == len(self.files_names)):
				break
		self.results=sorted(self.result)
		print("Finished")
	
	def get_results(self):
		return self.results

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_files():
	global request_count
	global toll
	request_count =request_count + 1
	#in_count = request_count
	out = process_images()
	images = request.files.getlist('myfile')
	if(toll == 0):
		toll = 1
		t = threading.Thread(name="generate_output" , target = populate_global_variables)
		t.start()
		t = threading.Thread(name="autoscaling" , target = autoscaling)
		t.start() 
	out.uploaded_images(images)
	request_count = request_count - 1
	return render_template('result.html', results=out.get_results())

if __name__ == '__main__':
	app.run(
		threaded=True,
		host=os.getenv('LISTEN', '0.0.0.0'),
		port=int(os.getenv('PORT', '5000')),
		use_reloader=True
		)
		