import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

USERS_TABLE = os.environ.get('USERS_TABLE')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def handle_cognito_trigger(event, context):
    if event['triggerSource'] == 'PostConfirmation_ConfirmSignUp':
        try:
            user_attributes = event['request']['userAttributes']
            
            user_item = {
                'UserID': user_attributes['sub'],  
                'Email': user_attributes['email'],
                'Name': '',  
                'RegPlates': [], 
                'CreatedAt': datetime.now().isoformat(),
                'UpdatedAt': datetime.now().isoformat()
            }
            
            table = dynamodb.Table(USERS_TABLE)
            table.put_item(Item=user_item)
            
            if user_attributes['email']:
                sns.subscribe(
                    TopicArn=SNS_TOPIC_ARN,
                    Protocol='email',
                    Endpoint=user_attributes['email']
                )
            
        except Exception as e:
            print(f"Error creating user record: {str(e)}")
        
        return event
    
    return event

def create_user_profile(event, context):
    try:
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        email = event['requestContext']['authorizer']['claims']['email']
        
        name = body.get('name', '')
        reg_plates = body.get('regPlates', [])
        
        user_item = {
            'UserID': user_id,
            'Email': email,
            'Name': name,
            'RegPlates': reg_plates,
            'UpdatedAt': datetime.now().isoformat()
        }
        
        table = dynamodb.Table(USERS_TABLE)
        table.put_item(Item=user_item)
        
        if email:
            sns.subscribe(
                TopicArn=SNS_TOPIC_ARN,
                Protocol='email',
                Endpoint=email
            )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({'message': 'Profile created successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_user_profile(event, context):
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'UserID': user_id})
        
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                'body': json.dumps(response['Item'], default=decimal_default)
            }
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                'body': json.dumps({'message': 'User not found'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({'error': str(e)})
        }

def update_user_profile(event, context):
    try:
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        name = body.get('name')
        reg_plates = body.get('regPlates')
        
        update_expression = "SET "
        expression_values = {}
        
        if name:
            update_expression += "Name = :name, "
            expression_values[':name'] = name
            
        if reg_plates:
            update_expression += "RegPlates = :plates, "
            expression_values[':plates'] = reg_plates
            
        update_expression = update_expression[:-2]
        
        table = dynamodb.Table(USERS_TABLE)
        table.update_item(
            Key={'UserID': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({'message': 'Profile updated successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({'error': str(e)})
        }

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def main(event, context):
    if 'triggerSource' in event:
        return handle_cognito_trigger(event, context)
    
    route_key = event.get('routeKey', '')
    
    if route_key == 'POST /profile':
        return create_user_profile(event, context)
    elif route_key == 'GET /profile':
        return get_user_profile(event, context)
    elif route_key == 'PUT /profile':
        return update_user_profile(event, context)
    else:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({'error': 'Invalid route'})
        } 