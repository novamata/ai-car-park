import boto3
import time
import uuid
import os

def detect_text(photo, bucket):
    client=boto3.client('rekognition')
    response=client.detect_text(Image={'S3Object':{'Bucket':bucket,'Name':photo}})
                        
    textDetections=response['TextDetections']
    for text in textDetections:
        if text['Type'] == 'LINE':
            return text['DetectedText']
    return False

def main(event, context): 
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    photo = event["Records"][0]["s3"]["object"]["key"]

    text_detected = detect_text(photo, bucket)
    
    if not text_detected:
        print("No text detected in the image")
        return {
            'statusCode': 400,
            'body': 'No registration plate detected'
        }
    
    print("Text detected: " + str(text_detected))
    
    current_time = int(time.time())
    
    dynamodb = boto3.resource('dynamodb')
    sessions_table = os.environ.get('SESSIONS_TABLE', 'ParkingSessions')
    table = dynamodb.Table(sessions_table)
    
    response = table.query(
        IndexName='CarRegistrationIndex',
        KeyConditionExpression='CarRegistration = :reg',
        FilterExpression='attribute_not_exists(ExitTime)',
        ExpressionAttributeValues={
            ':reg': text_detected
        }
    )
    
    if response['Items']:
        session = response['Items'][0]
        session_id = session['SessionID']
        entry_time = int(session['EntryTime'])
        
        duration_seconds = current_time - entry_time
        duration_hours = (duration_seconds + 3599) // 3600 
        
        payment_due = duration_hours * 2
        
        table.update_item(
            Key={
                'SessionID': session_id
            },
            UpdateExpression='SET ExitTime = :exit_time, DurationHours = :duration, PaymentDue = :payment',
            ExpressionAttributeValues={
                ':exit_time': current_time,
                ':duration': duration_hours,
                ':payment': payment_due
            }
        )
        
        print(f"Exit recorded for {text_detected}. Duration: {duration_hours} hours, Payment due: ${payment_due}")
        
        return {
            'statusCode': 200,
            'body': f"Exit recorded for {text_detected}. Payment due: ${payment_due}"
        }
    else:
        session_id = str(uuid.uuid4())
        
        table.put_item(
            Item={
                'SessionID': session_id,
                'CarRegistration': text_detected,
                'EntryTime': current_time,
                'EntryPhoto': photo
            }
        )
        
        print(f"Entry recorded for {text_detected}")
        
        return {
            'statusCode': 200,
            'body': f"Entry recorded for {text_detected}"
        }