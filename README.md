# calculateDistance

POST REST API (using AWS API Gateway) that take a graph and store it inside the DynamoDB database.

Parse the graph inside the lambda, compute the shortest distance using BFS (Breadth First Search) between each of the vertices and store this state inside DynamoDb.

This lambda function can be connected with AWS Lex.