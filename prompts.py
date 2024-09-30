JSON_prompt="""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are provided with natural language descriptions of failed login attempts. Your task is to:
- Parse the Natural Language Input: Understand the details such as the session ID, database name, application/user details, time of the attempt, action description, and reason for failure.
- Populate the JSON Structure: Extract the relevant information to fill in the predefined JSON schema for failed login attempts.
- Generate the JSON Object: Output the JSON object with all the required fields appropriately filled within <JSON> and </JSON> tags
The JSON Schema for failed login attempts:
{{
  "dbName": "string",
  "userDetails": {{
    "username": "string",
    "userId": "string",
    "accessLevel": "string"
  }},
  "time": {{
    "timestamp": int,
    "formattedTime": "string"
  }},
  "action": {{
    "attemptType": "string",
    "targetDatabase": "string",
    "reasonForFailure": "string"
  }},
  "attempts": int,
  "source": "string"
}}

Guidelines:
- dbName:
The name of the database the login attempt was made to.
- userDetails:
username: The username of the individual or application.
userId: The unique identifier associated with the user or application.
accessLevel: The access level of the user Standard if nothing is provided. (e.g., standard, elevated).
- time:
timestamp: Unix timestamp in milliseconds corresponding to the time of the attempt.
formattedTime: Human-readable formatted time string.
- action:
attemptType: Type of action attempted (e.g., login, access).
targetDatabase: The database targeted for the action.
reasonForFailure: Reason why the action failed.
- attempts:
Number of failed attempts.
- source:
Indicates whether the attempt was made by a user or an application.


Example:
Input: The application 'OrderProcessingApp' with App ID APP-7890 generated over 5,000 failed login attempts to the 'OrdersDB' database between 1:00 AM and 2:00 AM on September 25, 2024, due to configuration errors.
JSON object:
<JSON>
{{
    "dbName": "OrdersDB",
    "userDetails": {{
        "username": "OrderProcessingApp",
        "userId": "APP-7890",
        "accessLevel": "NONE"
    }},
    "time": {{
        "timestamp": 1732518000000,
        "formattedTime": "September 25, 2024, 1:00 AM  to September 25, 2024, 2:00 AM "
    }},
    "action": {{
        "attemptType": "login",
        "targetDatabase": "OrdersDB",
        "reasonForFailure": "configuration errors"
    }},
    "attempts": 5000,
    "source": "application"
}}
</JSON>
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
input:{input}
<|begin_of_text|><|start_header_id|>assistant<|end_header_id|>
"""
corrector_prompt="""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an assistant tasked with correcting JSON objects based on identified issues and provided recommendations. Follow these steps:
1. Analyze the Issues: Review the content within the <issues>` and `</issues>` tags to understand the discrepancies or errors in the JSON.
2. Consider the Recommendations: Read the suggestions within the `<recommendation>` and `</recommendation>` tags to know how to address each issue.
3. Modify the JSON: Adjust the provided JSON object to resolve all identified issues, ensuring that all changes comply with the predefined JSON schema for failed login attempts.
4. Maintain Schema Integrity: Ensure that the corrected JSON strictly follows the given schema, preserving the structure and data types.
5. Output the Corrected JSON: Provide only the corrected JSON object enclosed within `<JSON>` and `</JSON>` tags.
JSON SCHEMA:
{{
  "dbName": "string",
  "userDetails": {{
    "username": "string",
    "userId": "string",
    "accessLevel": "string"
  }},
  "time": {{
    "timestamp": int,
    "formattedTime": "string"
  }},
  "action": {{
    "attemptType": "string",
    "targetDatabase": "string",
    "reasonForFailure": "string"
  }},
  "attempts": int,
  "source": "string"
}}

<|begin_of_text|><|start_header_id|>user<|end_header_id|>
<issues>
{issues}
</issues>
<recommendation>
{recommendations}
</recommendation>
JSON:{JSON}
<|begin_of_text|><|start_header_id|>assistant<|end_header_id|>
"""
validation_prompt="""
[INST]
Task Overview:
You are provided with two pieces of information:
- Natural Language Description: A textual description of a failed login attempt.
- JSON Output: A JSON object(s) that is intended to represent the information from the natural language description.

Your task is to:
1. Verify that all the information from the natural language description is accurately captured in the JSON(s).
2. Ensure that the JSON(s) structure matches the provided schema.
3. Identify any discrepancies or missing information.

The JSON Schema:
{{
  "dbName": "string",
  "userDetails": {{
    "username": "string",
    "userId": "string",
    "accessLevel": "string"
  }},
  "time": {{
    "timestamp": int,
    "formattedTime": "string"
  }},
  "action": {{
    "attemptType": "string",
    "targetDatabase": "string",
    "reasonForFailure": "string"
  }},
  "attempts": int,
  "source": "string"
}}

Guidelines:
- Do not assume any information not provided in the description.
- If a field is not mentioned in the description, it is acceptable to leave it empty or as "NONE".
- Do not Recommend to add any additional fields not defined in the schema.
- Ensure that the data types and formats in the JSON adhere to the schema (e.g., timestamp should be an integer representing Unix time in milliseconds).

Feedback Structure:
- Issues Identified: List any discrepancies or missing information within `<issues>` and `</issues>` tags.
- Recommendations: Provide guidance on how to fix each issue within `<recommendation>` and `</recommendation>` tags.
- Status: Indicate "Correct" if the JSON accurately captures all the information and adheres to the schema, or "Incorrect" if there are issues, within `<status>` and `</status>` tags.

Natural Language Description:
{input}
JSON Output:
{JSON}
[/INST]
"""
