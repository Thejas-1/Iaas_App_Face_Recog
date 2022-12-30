import os
from urllib import response
import boto3
import time
from datetime import datetime,timezone
import base64
from PIL import Image
from image_classification import run_app
from AWS_helpers import HelperAPI

api = HelperAPI()

def available_messages():
	""" Returns the number of messages in the queue """
	response = api.queue_attributes_input('ApproximateNumberOfMessages')
	messages_available = int(response['Attributes']['ApproximateNumberOfMessages'])
	print(messages_available)
	return messages_available

def visible_messages():
	""" Returns the number of messages visible in the queue """
	response = api.queue_attributes_input('ApproximateNumberOfMessagesNotVisible')
	messages_available = response['Attributes']['ApproximateNumberOfMessagesNotVisible']
	return int(messages_available)

def new_message():
	print("Getting New Messages")
	""" Gets the first available message in queue """
	response = api.get_message_from_input_queue()
	receipt = response['Messages'][0]['ReceiptHandle']
	body_string = response['Messages'][0]['Body']
	body,file_name = body_string.split(',')
	body = body.encode('utf-8')
	imgdata = base64.decodebytes(body)
	filename = file_name#temp_file_name[0] + '.'+ temp_file_name[1].split('.')[1]
	path= os.getcwd()+'/'+filename
	with open(filename,'wb') as f:
		f.write(imgdata)
	f.close()
	api.push_to_inputbucket([path, filename])
	api.remove_from_in_queue(receipt, filename)
	return(receipt,path,filename,file_name)

def get_result(file_name,receipt,initial_file_name):
	result = run_app(file_name)
	try:
		fileName_noExt=file_name.split('.')
		file_name=fileName_noExt[0]
		api.dump_to_outputbucket([file_name, str(result[0])])
		message = initial_file_name+','+ result
		print(message)
		try:
			response = api.push_to_output_queue(message)
		except Exception as e:
			print("Error while placing in output queue",e)
	except:
		print("Error while placing in output bucket")
	return(result)

def run_task():
	try:
		receipt,path,filename,initial_file_name = new_message()
		result = get_result(filename,receipt,initial_file_name)
		os.remove(path)
		#time.sleep(5)
	except:
		print("No more messages available")

while(available_messages()>0):
	run_task()
#if run_cont: #Run forever
#while True:
	#run_task()
#		time.sleep(5) #poll every 5 seconds


#if shutdown_after:
#	print("Job Complete. Shutting Down")
#else:
#	print("Job Comlete. Quitting...")