#!usr/bin/python

import boto3
import json
import paramiko
import threading
import time
import sys
from time import sleep
import os
'''
Reference for aws boto3 :
https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
All boto3 comands usage was reffered from above reference site.
'''
sqs = boto3.client(
    'sqs',
    aws_access_key_id= "AKIAVYKKVOJBR65QHN4D",
    aws_secret_access_key= "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", region_name="us-east-1")
ec2 = boto3.resource(
    'ec2',
    aws_access_key_id= "AKIAVYKKVOJBR65QHN4D",
    aws_secret_access_key= "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", region_name="us-east-1")
# input and output queue urls
input_queue_url= "https://sqs.us-east-1.amazonaws.com/395830456899/pushing"
output_queue_url= "https://sqs.us-east-1.amazonaws.com/395830456899/reading"


def create_instance( app_number):
	try:
		instance = ec2.create_instances(
				ImageId='ami-007d1c2088637c3c8',
				InstanceType='t2.micro',
				MaxCount=1,
				MinCount=1,
				KeyName='cloud',
				Monitoring={
					'Enabled': True
				},
				TagSpecifications=[
					{
						'ResourceType': 'instance',
						'Tags': [
							{
								'Key': 'Name',
								'Value': 'app-tier'+ str(app_number).zfill(2)
							},
							{
								'Key': 'Type',
								'Value': 'app-tier'

							}
						]
					},
				],
				NetworkInterfaces=[
					{
						'AssociatePublicIpAddress': True,
						'DeleteOnTermination': True,
						'DeviceIndex': 0,
						'Groups': [
							'sg-0c4f8b29bc432144e'
						]
					}
				],
				InstanceInitiatedShutdownBehavior='stop',
			)
	except Exception as e:
		print(e)


# No of Messages in the Queue
def get_no_of_messages(sqsQueueUrl):
	response = sqs.get_queue_attributes(QueueUrl=sqsQueueUrl,AttributeNames=['ApproximateNumberOfMessages',])
	response = int(response['Attributes']['ApproximateNumberOfMessages'])
	return response

# Get number of Running and Stopped Instances
def get_no_of_running_instances():
	running_count = 0
	for instance in ec2.instances.all():
		if(instance.state['Name']=='running' or instance.state['Name']=='pending'):
			running_count+=1
	return running_count

def get_no_of_stopped_instances():
	stopped_count = 0
	for instance in ec2.instances.all():
		if(instance.state['Name']=='stopped' or instance.state['Name']=='stopping'):
			stopped_count+=1
	return stopped_count


# Getting Running Ids
def get_running_ids():
	ids = []
	for instance in ec2.instances.all():
		if(instance.state['Name']=='running' or instance.state['Name']=='pending'):
			ids.append(instance.id)
	return ids

# Getting Stopped Ids
def get_stopped_ids():
	ids = []
	for instance in ec2.instances.all():
		if(instance.state['Name']=='stopped' or instance.state['Name']=='stopping'):
			ids.append(instance.id)
	return ids

def image_recognition(instance_id):
	'''
		Connecting to EC2 instance and executing apptier code via paramiko
		Reference:https://stackoverflow.com/questions/57849262/how-to-run-a-python-script-present-in-an-aws-ec2-whenever-a-lambda-is-triggered?rq=1
	'''
	path= os.getcwd()
	print("path of current working directory",path)
	key = paramiko.RSAKey.from_private_key_file("/home/ec2-user/app-tier/cloud.pem")
	client = paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	print("In Image image_recognition func")
	instance = [i for i in ec2.instances.filter(InstanceIds=[instance_id])][0]
	print("instance connecting",instance)
	while(1):
		try:
			print("in while loop trying to connect to ec2-instance")
			client.connect(hostname=instance.public_ip_address, username='ec2-user',pkey=key, timeout=30)
			print("Connected to ec2-instance")
			sin ,sout ,serr = client.exec_command('python3 /home/ec2-user/app-tier/main.py')
			exit_status = sout.channel.recv_exit_status()
			print(exit_status)
			print(sout.read())
			print("Exiting apptier")
			print("Executed Code in app tier")
			print(serr.read())
			print("Executed sudo command")
			print(client.close())
			print("Exiting image_recognition func")
			break
			print("came out of image recognition function")
		except Exception as e:
			print("Reattempting to connect "+str(e))
			sleep(5)


def autoscaling():
	threads = []
	instances_in_progress = []
	while(True):
		print("Entered while loop in autoscaling")
		input_queue_length =get_no_of_messages(input_queue_url)
		# number_of_ec2_instances = len([instance for instance in ec2.instances.all()])
		# print("No of EC2 instances:")
		# print(number_of_ec2_instances)	
		
		for i in range(1, 5):
			print("Creating Instances: ",i)
			create_instance(i)
		sleep(5)
		no_of_running_instances =get_no_of_running_instances()
		print("Non of running instances", no_of_running_instances)
		no_of_stopped_instances = get_no_of_stopped_instances()
		print("no_of_stopped_instances", no_of_stopped_instances)
		print("----------*****************------------------- \n")
		print("input_queue_length,no_of_running_instances,no_of_stopped_instances :" +' ' + str(input_queue_length)+' '+str(no_of_running_instances)+' '+str(no_of_stopped_instances))
		print("----------*****************------------------- \n")
		if(input_queue_length>no_of_running_instances-len(instances_in_progress)):
			print("----------*****************------------------- \n")
			print("Entered first IF condition \n")
			stoppedIds = get_stopped_ids()
			no_of_instances_to_start = min(no_of_stopped_instances, input_queue_length-(no_of_running_instances-len(instances_in_progress)))
			print("no_of_stopped_instances,no_of_running_instances,len(instances_in_progress)")
			print(no_of_stopped_instances,(input_queue_length-(no_of_running_instances-len(instances_in_progress))))
			try:
				ec2.instances.filter(InstanceIds = stoppedIds[:no_of_instances_to_start]).start()
			except Exception as e:
				print(e)
				continue
			time.sleep(30)
		elif input_queue_length<no_of_running_instances-len(instances_in_progress):
			print("----------*****************------------------- \n")
			print("Entered the ELIF condition")
			running_ids = get_running_ids()
			instances_completed_app_execution = [i for i in running_ids if i not in instances_in_progress]
			try:
				ec2.instances.filter(InstanceIds = instances_completed_app_execution[:len(instances_completed_app_execution)-input_queue_length]).stop()
			except Exception as e:
				print(e)
			time.sleep(30)
		for running_id in get_running_ids():
			if running_id not in instances_in_progress:
				print("running_id: "+str(running_id))
				t = threading.Thread(name=running_id, target = image_recognition, args=(running_id,))
				threads.append(t)
				instances_in_progress.append(running_id)
				t.start()
				print("Started Thread", t)
		updated_threads = []
		for t in threads:
			print("status: ",t.is_alive())
			if not t.is_alive():
				# print(instances_in_progress)
				instances_in_progress.remove(t.getName())
				print(len(instances_in_progress))
			else:
				updated_threads.append(t)
		threads = updated_threads
		print(threads)
		# sleep(15)

if __name__ == '__main__':
	while(1):
		autoscaling()
