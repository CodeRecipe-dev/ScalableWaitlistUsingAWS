# How I build a scalable waitlist feature in AWS

More info here: https://coderecipe.ai/architectures/96083665

Many popular restaurants require you to wait in line to get seated. This simple design creates a scalable waitlist feature similar to [Yelp’s NoWait feature](https://www.yelp.nowait.com/) that allows you to get in a line without physically being there.  

I assume that each additional table takes 2 mins, and there is a global queue for any table size.

**Prerequisites**  
```  
npm install serverless  
  
export AWS_ACCESS_KEY_ID=<your-key-here>  
  
export AWS_SECRET_ACCESS_KEY=<your-secret-key-here>  
```  

**Deploy**  
  

```  
serverless create --template-url https://github.com/CodeRecipe-dev/ScalableWaitlistUsingAWS --path coderecipe-scalable-waitlist  
  
cd coderecipe-scalable-waitlist
  
npm install  
  
serverless deploy --stage stage --twilio_account_sid='twilio_account_sid' --twilio_auth_token='twilio_auth_token' --twilio_from_number='twilio_from_number'
```  
