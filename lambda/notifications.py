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

def get_user_by_car_reg(car_reg):    
    users_table = dynamodb.Table(USERS_TABLE)
    
    car_reg = car_reg.strip() if car_reg else car_reg
    
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

def main(event, context):
    for record in event['Records']:
        if record['eventName'] == 'MODIFY':
            new_image = record['dynamodb']['NewImage']
            
            if 'ExitTime' in new_image:
                car_reg = new_image['CarRegistration']['S']
                session_id = new_image['SessionID']['S']
                entry_time = int(new_image['EntryTime']['N'])
                exit_time = int(new_image['ExitTime']['N'])
                payment_due = float(new_image.get('PaymentDue', {}).get('N', 0))
                
                user = get_user_by_car_reg(car_reg)
                
                if user and 'Email' in user:
                    message = {
                        'sessionId': session_id,
                        'carRegistration': car_reg,
                        'entryTime': entry_time,
                        'exitTime': exit_time,
                        'paymentDue': payment_due,
                        'message': f"Your parking session for {car_reg} has ended. Payment due: ${payment_due}"
                    }
                    
                    sns.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Message=json.dumps(message, cls=DecimalEncoder),
                        Subject=f"Parking Payment Due for {car_reg}"
                    )
                    
                    print(f"Notification sent for {car_reg}")
                else:
                    print(f"No user found for car registration {car_reg}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Notifications processed successfully')
    }