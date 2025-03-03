import boto3
import time
import json

def main(event, context): 
    jsonBody = json.loads(event['body'])
    reg_plate = jsonBody['regPlate']
    if not reg_plate:
        exit()
    
    table_name = 'Customer_Reg_DB'
    
    dynamodbresource = boto3.resource('dynamodb')
    tableToScan = dynamodbresource.Table(table_name)
    responseQuery = tableToScan.scan()
    
    data = responseQuery['Items']
    
    returnDataReg = ''
    mostRecentEntryTime = 0
    exitTime = 0
    
    for entry in data:
        if reg_plate in entry["reg_plate"]:
            if (entry["entry_time"] > mostRecentEntryTime):
                mostRecentEntryTime = entry["entry_time"]
                returnDataReg = entry["reg_plate"]
                exitTime = entry["exit_time"]
    
    
    if mostRecentEntryTime == 0:
        returnData = {}
        statusCode = 400
    else:
        returnData = { 'reg_plate': reg_plate, 'entry_time': str(mostRecentEntryTime), 'exit_time': str(exitTime) }
        statusCode = 200
        
    response = {
        'statusCode': statusCode,
        'headers': {
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Credentials' : 'true',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(returnData)
    }

    return response    