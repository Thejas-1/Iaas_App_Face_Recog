import boto3

access_key = "AKIAVYKKVOJBR65QHN4D"
secret_key = "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"
region_name = "us-east-1"
class HelperAPI:
    def __init__(self):
        self.input_queue_url = "https://sqs.us-east-1.amazonaws.com/395830456899/pushing"
        self.output_queue_url = "https://sqs.us-east-1.amazonaws.com/395830456899/reading"
        self.input_bucket = 'cse546-project-input'
        self.output_bucket = 'cse546-project-output'
        self.sqs = boto3.client('sqs', aws_access_key_id= access_key, aws_secret_access_key= secret_key, region_name=region_name)
        self.s3 = boto3.client('s3', aws_access_key_id= access_key, aws_secret_access_key= secret_key, region_name=region_name)
        self.ec2 = boto3.client('ec2', aws_access_key_id= access_key, aws_secret_access_key= secret_key, region_name=region_name)

    def push_to_input_queue(self, message):
        return self.sqs.send_message(QueueUrl=self.input_queue_url, MessageBody= message), # MessageGroupId = "MessageGroup1")

    def push_to_output_queue(self, message):
        return self.sqs.send_message(QueueUrl=self.output_queue_url, MessageBody= message), # MessageGroupId = "MessageGroup1")

    def dump_to_inputbucket(self, message):
        self.s3.upload_file(message[0], self.input_bucket, message[1])

    def dump_to_outputbucket(self, message):
        self.s3.put_object(Bucket = self.output_bucket, Key = str(message[0]), Body = str(message[1]), Metadata = {"string": 'string'})

    def delete_from_input_queue(self, receipt_handle, file_name):
        return self.delete_from_queue(self.input_queue_url, receipt_handle, file_name)

    def delete_from_output_queue(self, receipt_handle, file_name):
        return self.delete_from_queue(self.output_queue_url, receipt_handle, file_name)

    def delete_from_queue(self, url, receipt_handle, file_name):
        if url == self.input_queue_url:
            print("Deleting item from Input SQS: " + file_name)
        else:
            print("Deleting item from Output SQS: " + file_name)
        try:
            response = self.sqs.delete_message(QueueUrl = url, ReceiptHandle = receipt_handle)
            print("Message Deleted")
        except:
            print("Could not delete Message!")
        return response
    
    def get_queue_attributes(self, url, attribute_name):
        return self.sqs.get_queue_attributes(QueueUrl=url,AttributeNames=[attribute_name])

    def get_output_queue_attributes(self, attribute_name):
        return self.get_queue_attributes(self.output_queue_url, attribute_name)

    def get_input_queue_attributes(self, attribute_name):
        return self.get_queue_attributes(self.input_queue_url, attribute_name)

    def get_message_from_input_queue(self):
        return self.sqs.receive_message(QueueUrl=self.input_queue_url, MaxNumberOfMessages=1, MessageAttributeNames=['ALL'])

    def get_message_from_output_queue(self):
        return self.sqs.receive_message(QueueUrl=self.output_queue_url, MaxNumberOfMessages=1, MessageAttributeNames=['ALL'])