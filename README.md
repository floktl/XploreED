# german_class_tool
This project provides a small learning platform for German classes. It is composed of a Vue frontend and a Flask backend. Development is done with Docker Compose. The backend exposes REST APIs for authentication, a small game, lessons and spaced repetition vocabulary review.

Database
--------
The backend stores data in a SQLite file referenced by `DB_FILE` in the `.env` file. The database schema is created on startup by `backend/utils/setup/migration_script.py`. The migration script creates and updates these tables:
- **users** – stores registered usernames and hashed passwords
- **results** – records user answers for the sentence ordering game and lesson completions
- **vocab_log** – vocabulary items tracked for spaced repetition
- **lesson_content** – HTML lesson content plus metadata like `target_user`, `published`, `num_blocks` and `ai_enabled`
- **lesson_blocks** – mapping of lesson IDs to block IDs
- **lesson_progress** – progress per lesson block for each user
- **support_feedback** – user feedback messages
- **exercise_submissions** – submissions of lesson exercises
 - **topic_memory** – spaced repetition data for grammar and topics
- **ai_user_data** – caches AI exercises, the next exercise block and weakness lesson per user
 
The schema creation queries can be found around lines 33‑258 of the migration script.

## Development

To run the project locally with Docker Compose use:

```bash
docker compose -f docker-compose.dev.yml up
```

Once the stack is running, open <http://localhost:5173> in your browser to see
the frontend. The Flask API is served on <http://localhost:5050>.

The backend service runs a small migration script on start to ensure the
database schema has all required columns.


