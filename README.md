Githubh Repo Link: https://github.com/mi7hra-shubham/Kuvaka-Tech

API Base URL
You can test the API by making requests to the live base URL.

Live URL for Testing:
https://b5a5217674f6.ngrok-free.app/

You should append the specific API endpoints to this base URL. For example, to get a list of available models, you would use:

https://b5a5217674f6.ngrok-free.app/api/tags

Note: This is a temporary ngrok URL and is subject to change. For a persistent solution, you would deploy the API to a production server with a stable domain.

API Examples: You can test the following APIs from any API tester ( using Postman/ThunderClient/cURL )
1. https://kuvaka-tech-8lup.onrender.com/offer with 
JSON Body as: {
  "name": "AI Outreach Automation",
  "value_props": ["24/7 outreach", "6x more meetings"],
  "ideal_use_cases": ["B2B SaaS mid-market"]
}

2. https://kuvaka-tech-8lup.onrender.com/leads/upload ( use Postman since thunderClient doesnt offer free fileUploading  )
Create a .csv file with the format specified and pass it into the form-data of body: 
.csv file content: 
name,role,company,industry,location,linkedin_bio
Ava Patel,Head of Growth,FlowMetrics,B2B SaaS mid-market,NY,"10 years in SaaS"
John Doe,Engineer,DataCorp,Analytics,Boston,"Building data pipelines"


3. https://kuvaka-tech-8lup.onrender.com/score
This calculates the score and stores it in result locally.

4. https://kuvaka-tech-8lup.onrender.com/results
Testing output: [
  {
    "name": "Ava Patel",
    "role": "Head of Growth",
    "company": "FlowMetrics",
    "industry": "B2B SaaS mid-market",
    "score": 50,
    "rule_breakdown": {
      "role": 20,
      "industry": 20,
      "completeness": 10
    },
    "ai_intent": "High",
    "ai_reasoning": "Lead is Head of Growth at a B2B SaaS mid-market company (exact ICP), with 10 years in SaaS experience, strongly indicating active buyer intent for AI outreach automation."
  },
  {
    "name": "John Doe",
    "role": "Engineer",
    "company": "DataCorp",
    "industry": "Analytics",
    "score": 20,
    "rule_breakdown": {
      "role": 10,
      "industry": 0,
      "completeness": 10
    },
    "ai_intent": "Low",
    "ai_reasoning": "Lead is an engineer in a B2B SaaS mid-market analytics company, but the product targets sales outreach automation (requiring sales roles), creating a role mismatch. Rule-based score of 20/50 further confirms weak fit."
  }
]

NOTE:
The setup steps can easily be read in the commit history.
Since I am running Ollama locally and using my PC as a server, I request you to evaluate as early as possible from your end.