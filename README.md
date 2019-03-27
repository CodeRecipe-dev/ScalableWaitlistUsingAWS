## prerequisites
npm install serverless-python-requirements

npm install serverless-pseudo-parameters

npm install serverless-iam-roles-per-function

pip install -r requirements.txt

## Deploy
serverless deploy --stage stage --twilio_account_sid='twilio_account_sid' --twilio_auth_token='twilio_auth_token' --twilio_from_number='twilio_from_number'

## get estimate API example
sls invoke -f CapacityMonitor -d '{"body":{"eventType":"getEstimate"}}' -l --stage stage

## subscribe waitlist API example
sls invoke -f CapacityMonitor -d '{"body":{"eventType":"addNewCustomer", "customerPhoneNumber":"+123456789", "customerName":"Joe"}}' -l --stage stage