# AI Car Park Management System

A serverless car park management system that uses AWS services and AI to automate license plate recognition, parking session management, and payment notifications.

## Overview

This project implements a complete car park management solution that:

1. Automatically detects vehicle license plates using AWS Rekognition
2. Tracks parking sessions (entry and exit times)
3. Calculates parking fees based on duration
4. Sends payment notifications to registered users
5. Provides a user-friendly web interface for registration and profile management

The system is built using a serverless architecture on AWS, making it scalable, cost-effective, and easy to maintain.

## Architecture

The system consists of the following components:

### Frontend
- Vue.js single-page application
- Hosted on AWS S3 and delivered via CloudFront
- User authentication via Amazon Cognito
- Responsive design using Bootstrap Vue

### Backend
- AWS Lambda functions for serverless processing
- Amazon DynamoDB for data storage
- Amazon S3 for image storage
- Amazon Rekognition for license plate detection
- Amazon SNS for notifications
- API Gateway for RESTful API endpoints
- AWS Cognito for user authentication and management

### Data Flow
1. When a car enters/exits the car park, a camera captures an image of the license plate
2. The image is uploaded to an S3 bucket
3. An S3 event triggers a Lambda function that:
   - Uses Rekognition to detect the license plate text
   - Records entry/exit in DynamoDB
   - Calculates parking duration and fees on exit
4. When a parking session ends, a DynamoDB stream triggers a notification Lambda
5. The notification Lambda finds the user associated with the license plate and sends a payment notification via SNS

## Technologies Used

### AWS Services
- **Lambda**: Serverless compute for processing images and events
- **S3**: Storage for frontend assets and license plate images
- **DynamoDB**: NoSQL database for user profiles and parking sessions
- **Rekognition**: AI service for license plate text detection
- **SNS**: Notification service for payment alerts
- **API Gateway**: RESTful API management
- **Cognito**: User authentication and management
- **CloudFront**: Content delivery network for the frontend

### Frontend
- **Vue.js**: Progressive JavaScript framework
- **Bootstrap Vue**: UI component library
- **AWS Amplify**: Authentication and API integration

### Infrastructure as Code
- **Terraform**: Infrastructure provisioning and management

### Programming Languages
- **Python**: Backend Lambda functions
- **JavaScript**: Frontend application

## Features

- **Automated License Plate Recognition**: Uses AWS Rekognition to detect license plates from images
- **Parking Session Management**: Tracks entry and exit times, calculates duration and fees
- **User Registration and Authentication**: Secure user accounts with email verification
- **Profile Management**: Users can register multiple vehicles
- **Payment Notifications**: Automated email notifications when parking sessions end
- **Serverless Architecture**: Scalable and cost-effective infrastructure

## Deployment

### Prerequisites
- AWS Account
- Terraform installed
- AWS CLI configured
- Node.js and npm installed

### Deployment Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-car-park.git
   cd ai-car-park
   ```

2. Create a `terraform.tfvars` file in the terraform directory:
   ```
   aws_region = "eu-west-2"  # or your preferred region
   frontend_bucket_prefix = "car-park-frontend"
   car_images_bucket_prefix = "car-park-images"
   users_table_name = "CarParkUsers"
   sessions_table_name = "ParkingSessions"
   notification_email = "your-email@example.com"  # for admin notifications
   ```

3. Deploy the backend infrastructure:
   ```bash
   cd terraform
   terraform init
   terraform apply -var-file="terraform.tfvars"
   ```

4. Note the outputs from Terraform, particularly the API Gateway URL and Cognito User Pool details.

5. Create a `.env` file in the car-park-frontend directory:
   ```
   VUE_APP_API_URL=<API_GATEWAY_URL>
   VUE_APP_REGION=<AWS_REGION>
   VUE_APP_USER_POOL_ID=<COGNITO_USER_POOL_ID>
   VUE_APP_USER_POOL_CLIENT_ID=<COGNITO_USER_POOL_CLIENT_ID>
   ```

6. Build and deploy the frontend:
   ```bash
   cd ../car-park-frontend
   npm install
   npm run build
   
   # Upload the dist folder to the S3 bucket
   aws s3 sync dist/ s3://<FRONTEND_BUCKET_NAME>/ --delete
   ```

7. Access your application via the CloudFront URL provided in the Terraform outputs.

## Usage

### User Registration and Profile Management
1. Navigate to the application URL
2. Click "Register" to create a new account
3. Verify your email address with the code sent to your inbox
4. Log in with your credentials
5. Add your vehicle registration plates in your profile

### Car Park Operation
1. When a car enters the car park, capture an image of the license plate
2. Upload the image to the S3 bucket in the `uploads/` folder
3. The system will automatically:
   - Detect the license plate
   - Record the entry time
   - Create a new parking session

4. When the car exits, capture another image of the license plate
5. Upload the image to the S3 bucket
6. The system will automatically:
   - Detect the license plate
   - Find the active parking session
   - Record the exit time
   - Calculate the parking duration and fee
   - Send a payment notification to the registered user

## Development

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-car-park.git
   cd ai-car-park
   ```

2. Set up the frontend for local development:
   ```bash
   cd car-park-frontend
   npm install
   npm run serve
   ```

3. For Lambda function development, you can use AWS SAM or test locally with mock events.

### Project Structure

```
ai-car-park/
├── car-park-frontend/       # Vue.js frontend application
│   ├── public/              # Static assets
│   ├── src/                 # Source code
│   │   ├── components/      # Vue components
│   │   ├── views/           # Vue views/pages
│   │   ├── router/          # Vue Router configuration
│   │   ├── App.vue          # Main application component
│   │   └── main.js          # Application entry point
│   └── package.json         # Frontend dependencies
│   └── .env                 # Environment variables
├── lambda/                  # Lambda functions
│   ├── notifications.py     # Payment notification function
│   ├── regplateapi.py       # Registration plate API function
│   ├── s3getpassrek.py      # License plate recognition function
│   └── userprofile.py       # User profile management function
└── terraform/               # Infrastructure as code
    ├── main.tf              # Main Terraform configuration
    ├── variables.tf         # Input variables
    ├── outputs.tf           # Output values
    └── data.tf              # Data sources
    └── terraform.tfvars     # Terraform variables
```

## Troubleshooting

### Common Issues

1. **License Plate Not Detected**
   - Ensure the image is clear and well-lit
   - Check the S3 bucket permissions
   - Verify the Lambda function logs in CloudWatch

2. **Notifications Not Received**
   - Confirm the email address is verified in SNS
   - Check that the license plate is registered in the user's profile
   - Verify the CarRegistrationIndex in DynamoDB is properly populated

3. **Frontend Authentication Issues**
   - Ensure Cognito User Pool and Client settings are correct
   - Check CORS configuration in API Gateway
   - Verify the environment variables in the frontend application