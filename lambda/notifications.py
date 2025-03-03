import json
import boto3
import os
from decimal import Decimal

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
USERS_TABLE = os.environ.get('USERS_TABLE', 'CarParkUsers')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):    
    for record in event['Records']:
        if record['eventName'] not in ['MODIFY', 'INSERT']:
            continue
            
        if 'NewImage' not in record['dynamodb']:
            continue
            
        new_image = record['dynamodb']['NewImage']
        
        if 'ExitTime' in new_image and 'PaymentDue' in new_image:
            if record['eventName'] == 'MODIFY' and 'OldImage' in record['dynamodb']:
                old_image = record['dynamodb']['OldImage']
                if 'ExitTime' not in old_image or 'PaymentDue' not in old_image:
                    send_payment_notification(new_image)
            elif record['eventName'] == 'INSERT':
                send_payment_notification(new_image)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Notifications processed successfully')
    }

def send_payment_notification(session_data):
    car_reg = session_data.get('CarRegistration', {}).get('S', 'Unknown')
    payment_due = float(session_data.get('PaymentDue', {}).get('N', '0'))
    session_id = session_data.get('SessionID', {}).get('S', 'Unknown')
    
    user_info = get_user_by_car_reg(car_reg)
    
    if payment_due > 0:
        message = {
            'type': 'PAYMENT_DUE',
            'sessionId': session_id,
            'carRegistration': car_reg,
            'paymentDue': payment_due,
            'userName': user_info.get('Name', 'Car Owner'),
            'userContact': user_info.get('Contact', 'Unknown')
        }
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message, cls=DecimalEncoder),
            Subject=f"Parking Payment Due: {car_reg}"
        )
        
        print(f"Payment notification sent for car {car_reg}, amount: ${payment_due}")
    
def get_user_by_car_reg(car_reg):    
    users_table = dynamodb.Table(USERS_TABLE)
    
    response = users_table.query(
        IndexName='CarRegistrationIndex',
        KeyConditionExpression='CarRegistration = :car_reg',
        ExpressionAttributeValues={
            ':car_reg': car_reg
        }
    )
    
    if response['Items']:
        return response['Items'][0]
    return {}