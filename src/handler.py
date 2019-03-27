import json
import os
import boto3
from twilio.rest import Client


def handle_capacity_request(event, context):
    request_body = event['body']
    event_type = request_body['eventType']
    estimateMin = _get_estimate()
    if "getEstimate" == event_type:
        return {"estimateMin": estimateMin}

    if "addNewCustomer" == event_type:
        if 'customerPhoneNumber' not in request_body:
            raise Exception("customerInfo is missing, event is:{}".format(event))
        _add_to_queue(request_body)
        _handle_add_new_customer(request_body)
        return {"response": estimateMin}

    if "getCurrentCustomer" == event_type:
        return {"response": _retreive_from_queue(False)}

    if "fetchNextCustomer" == event_type:
        _handle_table_ready_notification(request_body)
        return {"response": request_body}


def _handle_add_new_customer(request_body):
    lambda_client = boto3.client('lambda')

    notifier_request = _build_notifier_request('confirmReservationNotification',
                                               request_body['customerPhoneNumber'])
    notifier_function_name = "{}-{}".format(os.environ["Stage"], "Notifier")
    lambda_client.invoke(FunctionName=notifier_function_name,
                         InvocationType='Event',
                         Payload=json.dumps(notifier_request))


def _handle_table_ready_notification(request_body):
    lambda_client = boto3.client('lambda')

    notifier_request = _build_notifier_request('tableReadyNotification',
                                               request_body['customerPhoneNumber'])
    notifier_function_name = "{}-{}".format(os.environ["Stage"], "Notifier")
    lambda_client.invoke(FunctionName=notifier_function_name,
                         InvocationType='Event',
                         Payload=json.dumps(notifier_request))


def _build_notifier_request(event_type, customer_phone_number):
    return {"body": {"eventType": event_type, "customerPhoneNumber": customer_phone_number}}

def _build_capacity_monitor_request(event_type, customer_phone_number):
    return {"body": {"eventType": event_type, "customerPhoneNumber": customer_phone_number}}

def _get_estimate():
    return 2*int(_get_queue_length())

def _get_queue_length():
    sqs = boto3.resource('sqs')
    sqsClient = boto3.client('sqs')
    queue_length = sqsClient.get_queue_attributes(
        QueueUrl=os.environ['QueueUrl'],
        AttributeNames=['ApproximateNumberOfMessages'])['Attributes']['ApproximateNumberOfMessages']
    return queue_length

def _add_to_queue(request_body):
    customer_name = request_body["customerName"]
    customer_phone_number = request_body["customerPhoneNumber"]
    sqs = boto3.resource('sqs')
    sqsClient = boto3.client('sqs')
    response = sqsClient.send_message(
        QueueUrl=os.environ['QueueUrl'],
        MessageAttributes={
            'CustomerName': {
                'DataType': 'String',
                'StringValue': customer_name
            },
            'CustomerPhoneNumber': {
                'DataType': 'String',
                'StringValue': customer_phone_number
            }
        },
        MessageBody=customer_name+customer_phone_number,
        MessageGroupId='CustomersGroup1'
    )
    return response

def _retreive_from_queue(delete=False):
    sqsR = boto3.resource('sqs')
    queue = sqsR.get_queue_by_name(QueueName=os.environ['QueueName'])
    customerInfo = {}
    message = queue.receive_messages(MessageAttributeNames=['CustomerPhoneNumber', 'CustomerName'])[0]
    customerInfo['customerName'] = message.message_attributes['CustomerName']['StringValue']
    customerInfo['customerPhoneNumber'] = message.message_attributes['CustomerPhoneNumber']['StringValue']
    if delete:
        print("Removing Customer:")
        print(message.message_attributes)
        message.delete()
    return customerInfo

def handle_notification(event, context):
    request_body = event['body']
    event_type = request_body['eventType']

    account_sid = os.environ["twilio_account_sid"]
    auth_token = os.environ["twilio_auth_token"]
    client = Client(account_sid, auth_token)

    if event_type == 'confirmReservationNotification':
        message = client.messages \
                        .create(
                             body="Thank you for reserving a table, we will notify you once it's ready",
                             from_=os.environ["twilio_from_number"],
                             to=request_body["customerPhoneNumber"]
                         )
    elif event_type == 'tableReadyNotification':
        message = client.messages \
                        .create(
                             body="Your table is ready!",
                             from_=os.environ["twilio_from_number"],
                             to=request_body["customerPhoneNumber"]
                         )
    return {"response": "handle_notification completed"}


def handle_fetch_next_customer(event, context):
    request_body = event['body']

    lambda_client = boto3.client('lambda')

    estimateMin = _get_estimate()
    if estimateMin > 0:
        _retreive_from_queue(True)
        next_customer = _retreive_from_queue()
        capacity_monitor_request = _build_capacity_monitor_request('fetchNextCustomer',
                                                                   next_customer['customerPhoneNumber'])
        capacity_monitor_function_name = "{}-{}".format(os.environ["Stage"], "CapacityMonitor")
        lambda_client.invoke(FunctionName=capacity_monitor_function_name,
                         InvocationType='Event',
                         Payload=json.dumps(capacity_monitor_request))

    return {"response": "handle_fetch_next_customer completed"}
