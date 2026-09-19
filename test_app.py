import json
from app import app

def test_research_endpoint():
    client = app.test_client()
    print("Testing /api/research endpoint with a mock query...")
    response = client.post('/api/research', json={"query": "Who is currently leading the United States space program?"})
    print("Status Code:", response.status_code)
    try:
        data = response.get_json()
        print("JSON Response:")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print("Failed to parse JSON response:", e)

if __name__ == "__main__":
    test_research_endpoint()
