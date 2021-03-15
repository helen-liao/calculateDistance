import json
import boto3
import base64

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response
    
def calculate_distance(intent_request):
    sourceCity = intent_request['currentIntent']['slots']['source']
    destinationCity = intent_request['currentIntent']['slots']['destination']
    
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    dynamodb = boto3.resource('dynamodb')
    graphTable = dynamodb.Table('Graph')
    
    response = graphTable.get_item(Key={'Source': sourceCity, 'Destination': destinationCity})
    
    if ('Item' in response and response['Item']['Distance']):
        distance = response['Item']['Distance']
        return close(
            output_session_attributes,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': '{}'.format(distance)
            }
        )
    else:
        return close(
            output_session_attributes,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': '0'
            }
        )

def dispatch(intent_request):
    intent_name ='CalculateDistance'
    
    if intent_name == 'CalculateDistance':
        return calculate_distance(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')

def find_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if not start in graph:
        return None
    for node in graph[start]:
        if node not in path:
            newpath = find_path(graph, node, end, path)
            if newpath: return newpath
    return None
    
def parse(event):
    dynamodb = boto3.resource('dynamodb')
    graphTable = dynamodb.Table('Graph')
    
    graphEvent = event["body"]
    graphData = base64.b64decode(graphEvent)
    graphJson = json.loads(graphData)
    graph = graphJson['graph']
    pairs = graph.split(',')
    
    parsedGraph = {}
    sourceCities = set()
    destinationCities = set()
    
    for pair in pairs:
        cities = pair.split('->')
        source = cities[0]
        destination = cities[1]
        
        sourceCities.add(source)
        destinationCities.add(destination)
            
        if (source in parsedGraph):
            parsedGraph[source].append(destination)
        else:
            parsedGraph[source] = [destination]
    
    for start in sourceCities:
        for end in destinationCities:
            if start==end:
                continue
            path = find_path(parsedGraph, start, end)
            if path:
                dis = len(path)-1
                graphTable.put_item(
                    Item={
                        'Source': start,
                        'Destination': end,
                        'Distance': dis
                    }
                )
        
    return {
        'statusCode': 200,
        'body': json.dumps('Processed data.')
    }

def lambda_handler(event, context):
    if ("body" in event):
        return parse(event)
    elif(not "body" in event):
        return dispatch(event)
