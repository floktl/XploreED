import os
import requests

class LessonTaskGeneratorClient:
    def __init__(self, api_key, workspace_id, agent_name='LessonTaskGenerator'):
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.agent_name = agent_name
        self.base_url = f"https://dust.tt/api/v1/w/{self.workspace_id}/assistant/conversations"

    def generate_lesson(self, topic, level='intermediate'):
        prompt = (
            f"Create a complete German lesson on {topic} for {level} level learners. "
            "Output in HTML format as specified in your instructions."
        )
        payload = {
            "message": prompt,
            "assistant": self.agent_name,
            "blocking": True
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Extract lesson HTML
        try:
            html_content = data['content'][0]['content']
            return html_content
        except Exception as e:
            raise RuntimeError(f"Unexpected API response: {e}\nFull response: {data}")

if __name__ == "__main__":
    # Load credentials from environment variables or .env file
    api_key = os.getenv('DUST_API_KEY')
    workspace_id = os.getenv('DUST_WORKSPACE_ID')

    if not api_key or not workspace_id:
        print("Please set DUST_API_KEY and DUST_WORKSPACE_ID environment variables.")
        exit(1)

    client = LessonTaskGeneratorClient(api_key, workspace_id)
    topic = "Modal Verbs"
    level = "intermediate"

    print(f"Generating lesson for topic: {topic}, level: {level} ...")
    try:
        html_lesson = client.generate_lesson(topic, level)
        print("Lesson HTML received:\n")
        print(html_lesson)
    except Exception as e:
        print(f"Error: {e}")
