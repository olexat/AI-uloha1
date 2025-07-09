import os
import json
from pprint import pprint

from dotenv import load_dotenv
load_dotenv()

import anthropic

import openmeteo_requests
import requests

# curl -v 'https://api.open-meteo.com/v1/forecast?latitude=48.15&longitude=17.15&hourly=temperature_2m'
# curl -v 'https://api.open-meteo.com/v1/forecast?latitude=48.15&longitude=17.15&hourly=temperature_2m,precipitation,precipitation_probability'

CLIENT = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)


def get_weather(latitude: str, longitude: str):
#    openmeteo = openmeteo_requests.Client()
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation,precipitation_probability"
    }
#    responses = openmeteo.weather_api(url, params=params)
#    print(responses[0].Hourly().Variables(0))
#    return(responses[0])
    response = requests.get(url, params=params)
#    print(response.json())
    return response.json()

TOOLS = [
    {
        "name": "get_weather",
        "description": "Use this function to get the weather forecast.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "string",
                    "description": "latitude",
                },
                "longitude": {
                    "type": "string",
                    "description": "longitude",
                },
            },
#            "required": ["ticker"],
        },
    },
]

AVAILABLE_FUNCTIONS = {"get_weather": get_weather}


def lets_talk(messages, model="claude-sonnet-4-20250514"):
    response = CLIENT.messages.create(
        model=model,
        max_tokens=1024,
        system="You are an AI assistant.",
        messages=messages,
        tools=TOOLS,  # CUSTOM TOOLS
        tool_choice={"type": "auto"} # Allow AI to decide if a tool should be called
    )

    print("--- Full response: ---")
    pprint(response)
    print("\n--- Response text: ---")
    print(response.content[0].text)
    has_tool_call = any(item.type == "tool_use" for item in response.content)
    if has_tool_call:
        print("--- Response Tool call: ---")
        print(response.content[1])
        
          # Find the tool call content
        tool_call = next(item for item in response.content if item.type == "tool_use")
        
        # Extract tool name and arguments
        function_name = tool_call.name
        function_args = tool_call.input
        tool_id = tool_call.id
        
        # Call the function
        function_to_call = AVAILABLE_FUNCTIONS[function_name]
        function_response = function_to_call(**function_args)

        # Append the assistant message with the tool call
        messages.append({
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": tool_id,
                    "name": function_name,
                    "input": function_args
                }
            ]
        })
        
        # Append the tool result - using tool_use_id instead of tool_call_id
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,  # Using tool_use_id as per the error message
                    "content": json.dumps(function_response)
                }
            ]
        })

        print(messages)

        second_response = CLIENT.messages.create(
            model=model,
            max_tokens=1024,
            system="You are a helpful AI assistant.",
            messages=messages,
        )
        
        return second_response
        


response = lets_talk(
        messages=[
            {"role": "user", "content": "What weather will it be tomorrow in Trencin? Find the coordinates and use these. And add some romantic poetry."},
        ]
)


pprint(response)
print("\n--- Response text: ---")
if response.content and hasattr(response.content[0], 'text'):
    print(response.content[0].text)
else:
    print("No text content in the response")

