- uvicorn is the ASGI(Asynchronous server gateway interface) and it supports asynchronous operations as well as
- HTTPX is a Python HTTP client library used to send HTTP requests from your Python application to other servers or APIs
- pydantic_settings is a library that helpful for manage the settings of your python application like (database urls,secret keys)
- Python cannot talk to PostgreSQL by itself; it needs a translator (a database driver). For SQLAlchemy and PostgreSQL, the industry standard driver is psycopg2-binary

- session.py in short:

**engine**
- Connects Python to the database
- Keeps a pool of open connections so it doesn’t reconnect every time

**SessionLocal**
- A factory that creates a new database session
- A session = one conversation with the database (add, read, update, delete)

**Base**
- Parent class for all tables
- Any class that inherits from it becomes a table

**get_db()**
- Gives each API request its own session
- Closes the session when the request ends
Prevents connection leaks


### Repository Table

When a user wants our AI to review a project, the first thing they do is connect a GitHub repository. So, we need a `repositories` table to store information about each connected repository.

#### Columns

1. **`id`**: Unique primary key number (1, 2, 3...).
2. **`name`**: Name of the repository (e.g., `"fastapi/fastapi"` or `"my-project"`).
3. **`clone_url`**: URL used to clone the repository (e.g., `"https://github.com/..."`).
4. **`default_branch`**: Default branch of the repository, usually `"main"` or `"master"`.
5. **`status`**: Current state of the repository:
   - `UNINDEXED` – Newly added, not processed yet.
   - `INDEXING` – Currently reading and parsing files.
   - `READY` – Ready for AI code reviews and questions.
   - `FAILED` – Something went wrong during indexing.
6. **`created_at`**: Timestamp indicating when the repository was added.

- Note: In PostgreSQL, before SQLAlchemy can create tables inside database, that database must exist


