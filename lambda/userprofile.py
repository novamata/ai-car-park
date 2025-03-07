import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

USERS_TABLE = os.environ.get('USERS_TABLE', 'CarParkUsers')
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
            
            update_car_registration_index(user_attributes['sub'], [])
            
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
        user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']
        email = event['requestContext']['authorizer']['jwt']['claims']['email']
        
        name = body.get('name', '')
        reg_plates = body.get('regPlates', [])
        
        reg_plates = [plate.strip() for plate in reg_plates if plate]
        
        user_item = {
            'UserID': user_id,
            'Email': email,
            'Name': name,
            'RegPlates': reg_plates,
            'UpdatedAt': datetime.now().isoformat()
        }
        
        table = dynamodb.Table(USERS_TABLE)
        table.put_item(Item=user_item)
        
        if reg_plates:
            update_car_registration_index(user_id, reg_plates)
        
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
                'Access-Control-Allow-Credentials': 'true',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': 'Profile created successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

def get_user_profile(event, context):
    try:
        print("Event:", json.dumps(event))
        user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']
        print("User ID:", user_id)
        
        table = dynamodb.Table(USERS_TABLE)
        print("Getting item from table:", USERS_TABLE)
        response = table.get_item(Key={'UserID': user_id})
        print("DynamoDB Response:", json.dumps(response))
        
        if 'Item' in response:
            item = response['Item']
            print("User item found:", json.dumps(item))
            
            if 'RegPlates' in item:
                print("RegPlates found:", json.dumps(item['RegPlates']))
            else:
                print("RegPlates not found in user item")
                
                if 'CarRegistration' in item:
                    car_reg = item['CarRegistration']
                    print(f"Found CarRegistration directly in user record: {car_reg}")
                    
                    reg_plates = [car_reg]
                    item['RegPlates'] = reg_plates
                    
                    try:
                        table.update_item(
                            Key={'UserID': user_id},
                            UpdateExpression='SET RegPlates = :plates',
                            ExpressionAttributeValues={
                                ':plates': reg_plates
                            }
                        )
                        print(f"Updated user record with RegPlates: {reg_plates}")
                    except Exception as e:
                        print(f"Error updating user record with RegPlates: {str(e)}")
                else:
                    try:
                        scan_response = table.scan(
                            FilterExpression='UserID = :user_id',
                            ExpressionAttributeValues={
                                ':user_id': user_id
                            }
                        )
                        
                        reg_plates = []
                        for scan_item in scan_response.get('Items', []):
                            if 'CarRegistration' in scan_item and scan_item['CarRegistration'] != user_id:
                                reg_plates.append(scan_item['CarRegistration'])
                        
                        if reg_plates:
                            print(f"Found registration plates in scan: {reg_plates}")
                            
                            item['RegPlates'] = reg_plates
                            
                            table.update_item(
                                Key={'UserID': user_id},
                                UpdateExpression='SET RegPlates = :plates',
                                ExpressionAttributeValues={
                                    ':plates': reg_plates
                                }
                            )
                            print("Updated user record with RegPlates")
                        else:
                            print("No registration plates found in scan")
                            item['RegPlates'] = []
                    except Exception as e:
                        print(f"Error scanning for registration plates: {str(e)}")
                        item['RegPlates'] = []
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': 'true',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(item, default=decimal_default)
            }
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': 'true',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'message': 'User not found'})
            }
    except Exception as e:
        import traceback
        print("Error:", str(e))
        print("Traceback:", traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'trace': traceback.format_exc()
            })
        }

def update_car_registration_index(user_id, reg_plates):
    table = dynamodb.Table(USERS_TABLE)
    
    response = table.get_item(Key={'UserID': user_id})
    if 'Item' not in response:
        print(f"User {user_id} not found")
        return
    
    user = response['Item']
    email = user.get('Email', '')
    name = user.get('Name', '')
    
    update_expression = 'SET RegPlates = :plates'
    expression_values = {
        ':plates': reg_plates
    }
    
    if reg_plates and len(reg_plates) > 0:
        update_expression += ', CarRegistration = :car_reg'
        expression_values[':car_reg'] = reg_plates[0]
    
    table.update_item(
        Key={'UserID': user_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )
    print(f"Updated main user record with RegPlates: {reg_plates}")
    
    for plate in reg_plates:
        if plate:  
            table.put_item(Item={
                'UserID': user_id,
                'CarRegistration': plate,
                'Email': email,
                'Name': name
            })
            print(f"Added plate to CarRegistrationIndex: {plate}")
    
    print(f"Updated CarRegistrationIndex for user {user_id} with plates: {reg_plates}")

def update_user_profile(event, context):
    try:
        print("Event:", json.dumps(event))
        body = json.loads(event['body'])
        print("Request body:", json.dumps(body))
        user_id = event['requestContext']['authorizer']['jwt']['claims']['sub']
        print("User ID:", user_id)
        
        name = body.get('name')
        reg_plates = body.get('regPlates')
        print("Name:", name)
        print("Reg Plates:", reg_plates)
        
        if reg_plates is not None:
            reg_plates = [plate.strip() for plate in reg_plates if plate]
        
        update_expression = "SET "
        expression_values = {}
        expression_names = {}
        
        if name is not None:
            update_expression += "#n = :name, "
            expression_values[':name'] = name
            expression_names['#n'] = 'Name'
            
        if reg_plates is not None:
            update_expression += "RegPlates = :plates, "
            expression_values[':plates'] = reg_plates
            
        update_expression += "UpdatedAt = :updated"
        expression_values[':updated'] = datetime.now().isoformat()
        
        if len(expression_values) == 1: 
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': 'true',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'No fields to update'})
            }
        
        print("Update expression:", update_expression)
        print("Expression values:", json.dumps(expression_values))
        print("Expression names:", json.dumps(expression_names))
        
        table = dynamodb.Table(USERS_TABLE)
        print("Updating item in table:", USERS_TABLE)
        
        update_params = {
            'Key': {'UserID': user_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': "ALL_NEW"
        }
        
        if expression_names:
            update_params['ExpressionAttributeNames'] = expression_names
            
        response = table.update_item(**update_params)
        print("DynamoDB Response:", json.dumps(response))
        
        if reg_plates is not None:
            update_car_registration_index(user_id, reg_plates)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Profile updated successfully',
                'profile': response.get('Attributes', {})
            }, default=decimal_default)
        }
    except Exception as e:
        import traceback
        print("Error:", str(e))
        print("Traceback:", traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'trace': traceback.format_exc()
            })
        }

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def main(event, context):
    if 'triggerSource' in event:
        return handle_cognito_trigger(event, context)
    
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')
    
    if http_method == 'POST' and path == '/profile':
        return create_user_profile(event, context)
    elif http_method == 'GET' and path == '/profile':
        return get_user_profile(event, context)
    elif http_method == 'PUT' and path == '/profile':
        return update_user_profile(event, context)
    elif http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': ''
        }
    else:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({'error': f'Invalid route: {http_method} {path}'})
        }