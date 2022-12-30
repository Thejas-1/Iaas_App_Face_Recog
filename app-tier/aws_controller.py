import boto3


push_queue = "https://sqs.us-east-1.amazonaws.com/395830456899/pushing"
read_queue = "https://sqs.us-east-1.amazonaws.com/395830456899/reading"

input_bucket = "cse546-project-input"
output_bucket = "cse546-project-output"

def read_messages_from_queue():
    return "Dummy Return"

def push_image_to_input_bucket(image):
    return "Dummy Return"

def push_recognition_result_to_output_bucket(output: tuple):
    return "Dummy Return"

