import boto3


queue = boto3.client(
    'sqs',
    aws_access_key_id= "AKIAVYKKVOJBR65QHN4D",
    aws_secret_access_key= "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", region_name="us-east-1")
def send_message(message):
    confirm = queue.send_message(QueueUrl='https://sqs.us-east-1.amazonaws.com/395830456899/pushing', MessageBody = message)
    print(confirm)
