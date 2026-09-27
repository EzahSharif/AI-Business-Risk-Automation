import requests
import os
import json
import csv
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

print("AI Business Risk Automation")

companies = []

with open("companies.csv", "r", encoding="utf-8-sig") as file:

    reader = csv.DictReader(file)

    print(reader.fieldnames)

    for company in reader:

        companies.append({
            "company_name": company["Company Name"],
            "country": company["Country"],
            "industry": company["Industry"],
            "website": company["Website"],
            "description": company["Description"]
        })

print("Total companies:", len(companies))

print(companies[0])


def validate_company(company):

    required_fields = [
        "company_name",
        "country",
        "industry",
        "website",
        "description"
    ]

    missing_fields = []

    for field in required_fields:

        if not company.get(field):
            missing_fields.append(field)

    if missing_fields:

        return {
            "valid": False,
            "missing_fields": missing_fields
        }

    return {
        "valid": True,
        "missing_fields": []
    }


# Load previous results

if os.path.exists("results.json"):

    with open("results.json", "r", encoding="utf-8") as file:

        previous_results = json.load(file)

    previous_results_dict = {
        item["company_name"]: item
        for item in previous_results
    }

    for i, company in enumerate(companies):

        if company["company_name"] in previous_results_dict:

            companies[i] = previous_results_dict[
                company["company_name"]
            ]

    print("\nPrevious results loaded.")

else:

    previous_results = []

    print("\nNo previous results found.")


# Process companies

for company in companies:

    if "decision_agent" in company:

        print(
            "\nSkipping already processed:",
            company["company_name"]
        )

        continue

    result = validate_company(company)

    print("\nProcessing:", company["company_name"])

    print(result)

    company["validation"] = result

    if not result["valid"]:

        print("Company data is incomplete.")

        continue

    print("Ready for AI Analysis")


    # AI Analysis

    prompt = f"""
    
Analyse the following company information:

Identify potential business risk indicators.

Identify information that should be verified.

Identify useful business intelligence.

Do not make unsupported accusations.

Do not assume that a company is fraudulent based only on missing or limited information.

Clearly distinguish between facts, missing information, and potential risk indicators.

Return the analysis in the following structure:

Company Name:

Risk Indicators:

Information to Verify:

Business Intelligence:

Overall Risk Level:

Company Information:

Company Name: {company["company_name"]}

Country: {company["country"]}

Industry: {company["industry"]}

Website: {company["website"]}

Description: {company["description"]}
"""

    try:

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        print("\n--- AI ANALYSIS ---")

        print(response.output_text)

        company["ai_analysis"] = response.output_text

    except Exception as e:

        print("\nAI Analysis Error:")
        print(e)

        continue


    # Verify Agent

    verify_prompt = f"""
You are a Verify Agent.

Review the following company information:

Company Name: {company["company_name"]}

Country: {company["country"]}

Industry: {company["industry"]}

Website: {company["website"]}

Description: {company["description"]}

Identify information that should be verified.

Return:

1. Website Verification

2. Business Identity Verification

3. Industry Verification

4. Missing Information

Do not make unsupported accusations.

Do not claim that information is true or false without evidence.
"""

    try:

        verify_response = client.responses.create(
            model="gpt-5.6-luna",
            input=verify_prompt
        )

        print("\n--- VERIFY AGENT ---")

        print(verify_response.output_text)

        company["verify_agent"] = verify_response.output_text

    except Exception as e:

        print("\nVerify Agent Error:")
        print(e)

        continue


    # Risk Agent

    risk_prompt = f"""
You are a Risk Agent.

Review the following company information:

Company Name: {company["company_name"]}

Country: {company["country"]}

Industry: {company["industry"]}

Website: {company["website"]}

Description: {company["description"]}

Identify potential business risk indicators.

Focus on:

1. Information Gaps
2. Website-related Concerns
3. Business Identity Concerns
4. Industry-related Concerns
5. Data Inconsistencies

Do not make unsupported accusations.

Do not assume that the company is fraudulent.

Clearly distinguish between confirmed facts, missing information, and potential risk indicators.

Return ONLY valid JSON.

Do not include:

- Markdown
- ```json
- Explanations
- Headings
- Any text before or after the JSON

Use exactly this JSON structure:

{{
    "information_gap": true,
    "website_concern": false,
    "identity_concern": false,
    "industry_concern": false,
    "data_inconsistency": false
}}

Set each value to true if the concern is present.

Otherwise set it to false.
"""

    try:

        risk_response = client.responses.create(
            model="gpt-5.6-luna",
            input=risk_prompt
        )

        print("\n--- RISK AGENT ---")

        print(risk_response.output_text)

        company["risk_agent"] = risk_response.output_text

        risk_data = json.loads(
            risk_response.output_text
        )

        print("\n--- RISK DATA ---")

        print(risk_data)

        company["risk_data"] = risk_data

    except Exception as e:

        print("\nRisk Agent Error:")
        print(e)

        continue


    # Intelligence Agent

    intelligence_prompt = f"""
You are a Business Intelligence Agent.

Review the following company information:

Company Name: {company["company_name"]}

Country: {company["country"]}

Industry: {company["industry"]}

Website: {company["website"]}

Description: {company["description"]}

Identify useful business intelligence about the company.

Focus on:

1. Business Model

2. Target Customers

3. Industry Context

4. Potential Business Opportunities

5. Important Business Information

Clearly distinguish between information provided in the data
and insights inferred from that information.

Do not invent facts that are not supported by the provided information.
"""

    try:

        intelligence_response = client.responses.create(
            model="gpt-5.6-luna",
            input=intelligence_prompt
        )

        print("\n--- INTELLIGENCE AGENT ---")

        print(intelligence_response.output_text)

        company["intelligence_agent"] = intelligence_response.output_text

    except Exception as e:

        print("\nIntelligence Agent Error:")
        print(e)

        continue


    # Decision Agent

    decision_prompt = f"""
You are a Decision Agent.

Review the following company information and risk analysis:

Company Name: {company["company_name"]}

Risk Data:
{risk_data}

Based on the risk indicators, make a simple processing decision.

Use only these decisions:

- Continue Processing
- Additional Verification
- Human Review Required

Rules:

If multiple serious risk indicators are present:
Human Review Required

If some risk indicators are present:
Additional Verification

If there are no significant risk indicators:
Continue Processing

Do not make unsupported accusations.
Do not assume that the company is fraudulent.

Return:

Risk Level:
Decision:
Reason:
"""

    try:

        decision_response = client.responses.create(
            model="gpt-5.6-luna",
            input=decision_prompt
        )

        print("\n--- DECISION AGENT ---")

        print(decision_response.output_text)

        company["decision_agent"] = decision_response.output_text

    except Exception as e:

        print("\nDecision Agent Error:")
        print(e)

        continue


    # Save result

    with open("results.json", "w", encoding="utf-8") as file:

        json.dump(
            companies,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\nResult saved:",
        company["company_name"]
    )


print("\nAll companies processed.")

print("Results saved successfully!")