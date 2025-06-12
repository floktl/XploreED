# german_class_tool

## Development

To run the project locally with Docker Compose use:

```bash
docker compose -f docker-compose.dev.yml up
```

Once the stack is running, open <http://localhost:5173> in your browser to see
the frontend. The Flask API is served on <http://localhost:5050>.

## AI Exercise Workflow

1. **Admin**
   - Log in and open the lesson editor in the admin panel.
   - Use the "🤖 AI Exercise" button in the toolbar to insert an AI exercise block.
   - Save and publish the lesson.

2. **Student**
   - Open the lesson from the Lessons page.
   - Complete the five AI exercises shown in the block and submit the answers.
   - If any answers are incorrect you will see feedback and can click **Continue** to get a new set of exercises.
   - Repeat until all answers are correct, then mark the lesson as completed.

