- **uvicorn** is the ASGI(Asynchronous server gateway interface) and it supports asynchronous operations as well as
- HTTPX is a Python HTTP client library used to send HTTP requests from your Python application to other servers or APIs
- pydantic_settings is a library that helpful for manage the settings of your python application like (database urls,secret keys)
- Python cannot talk to PostgreSQL by itself; it needs a translator (a database driver). For SQLAlchemy and PostgreSQL, the industry standard driver is psycopg2-binary

### session.py in short:

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

### Database Engine, Connection Pool, and Sessions works for multiple users

- **Shared Engine and Pool:** A single database engine and connection pool are shared across all users and requests.
- **Separate Session per Request:** Every incoming request gets its own database session through `get_db()`.
- **Connection Borrowing:** Each session borrows a database connection from the connection pool when needed.
- **Connection Return:** When `session.close()` is called, the borrowed connection is returned to the pool for reuse.
- **Transaction Isolation:** Uncommitted changes remain within that session's transaction and are not visible to other sessions.
- **Pool Exhaustion:** If all connections in the pool are in use, new requests wait until a connection becomes available (or the configured timeout is reached).


### Repository Table

When a user wants our AI to review a project, the first thing they do is connect a GitHub repository. So, we need a `repositories` table to store information about each connected repository.

**Columns**

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


### IndexedChunk Table

Once a repository is connected, our AI assistant needs to understand its source code. Since reading the entire codebase at once is not practical, the system processes source files and divides them into smaller, meaningful code blocks, such as individual functions and classes.

We store these code blocks in an `indexed_chunks` table, along with their file locations, line numbers, source code, and vector embeddings. These embeddings allow the AI assistant to find relevant code snippets through similarity searches.

**Columns**

1. **id**: Unique primary key number for each code chunk (1, 2, 3...).

2. **repo_id**: Foreign key referencing `repositories.id`, linking each code chunk to the repository it belongs to.

3. **file_path**: Relative path of the source file inside the repository (e.g., `"src/auth/service.py"`).

4. **start_line**: The line number where the code block begins (e.g., `20`).

5. **end_line**: The line number where the code block ends (e.g., `45`).

6. **symbol_name**: Name of the function or class contained in the code block (e.g., `verify_password` or `UserService`).

7. **language**: Programming language of the source file (e.g., `"python"`, `"javascript"`, or `"plaintext"`).

8. **content**: The actual source code contained within the specified line range.

9. **embedding_json**: A list of numerical values (vector embedding) representing the semantic meaning of the code block. These embeddings are used by the AI assistant to perform similarity searches and retrieve relevant code snippets.


### PRReview Table

When a developer opens a Pull Request (PR) on GitHub or requests a manual code review, our AI assistant analyzes the changed code (diff) against the repository's existing codebase.

We use a `pr_reviews` table to store the high-level report generated during each review run. This includes the review summary, overall risk assessment, and details identifying the Pull Request or commit being reviewed.

**Columns**

1. **id**: Unique primary key number for each review run (1, 2, 3...).

2. **repo_id**: Foreign key referencing `repositories.id`, linking the review to the repository being analyzed.

3. **pr_number**: GitHub Pull Request number (e.g., `42`). This can be `None` when reviewing a local Git commit that is not associated with a Pull Request.

4. **commit_sha**: The exact Git commit hash being reviewed (e.g., `"a1b2c3d4e5"`). It identifies the specific version of the code being analyzed.

5. **summary**: An overall executive summary generated by the AI, describing the Pull Request, its changes, and the main takeaways from the review.

6. **risk_level**: Overall risk assessment of the Pull Request, indicating the potential impact of the changes.

   - `LOW` – Routine changes, clean refactoring, or simple documentation updates.
   - `MEDIUM` – New logic or changes involving moderate complexity.
   - `HIGH` – Changes affecting critical business logic, database queries, or authentication.
   - `CRITICAL` – A probable security vulnerability or breaking change has been detected.

7. **created_at**: Timestamp indicating when the review was performed.


### ReviewFinding Table

A single Pull Request review can identify multiple issues or areas for improvement across different files. For example, a PR might contain an SQL injection vulnerability in one file, a missing null-check in another, and a function that lacks sufficient unit tests.

We use a `review_findings` table to store each individual issue or recommendation identified by the AI assistant. Each finding includes its severity, category, exact file location, explanation, supporting code evidence, and a suggested fix.

**Columns**

1. **id**: Unique primary key number for each finding (1, 2, 3...).

2. **review_id**: Foreign key referencing `pr_reviews.id`, linking each finding to the overall Pull Request review run.

3. **file_path**: Relative path of the file where the issue was identified (e.g., `"src/auth/service.py"`).

4. **line_number**: Specific line number in the changed code where the issue was identified (e.g., `45`).

5. **severity**: Indicates how dangerous or urgent the finding is.

   - `CRITICAL` – Direct security exploit or fatal application crash.
   - `HIGH` – Severe logic bug or risk of data corruption.
   - `MEDIUM` – Performance issue, edge-case bug, or unhandled exception.
   - `LOW` – Code smell, style deviation, or minor inefficiency.
   - `INFO` – Helpful tip or non-breaking improvement suggestion.

6. **category**: Identifies the type of issue detected.

   - `BUG_RISK` – Potential bugs such as off-by-one errors, null pointer dereferences, or race conditions.
   - `SECURITY` – Security vulnerabilities such as SQL injection, hardcoded secrets, or unsafe deserialization.
   - `MISSING_TESTS` – New logic or complex code branches without sufficient test coverage.
   - `ARCHITECTURE` – Architectural issues such as breaking API changes or tight coupling.

7. **title**: Short, descriptive summary of the identified issue (e.g., `"Unsanitized SQL Input"`).

8. **description**: Detailed explanation generated by the AI describing the issue, the potential risk, and why it matters.

9. **suggested_diff**: Suggested code patch showing the proposed changes needed to fix the issue.

10. **evidence_snippet**: Relevant surrounding source code retrieved from the codebase that provides evidence supporting the finding.


# WriteAction Table

A core requirement of our system is **Human-in-the-Loop Safeguards**: the AI must **never** modify repository files, push commits, or post comments to GitHub autonomously without developer approval.

Whenever the AI suggests an automated fix (such as a code patch, a generated unit test file, or a PR review comment), it saves that suggestion in the `write_actions` table with `status = "PENDING_APPROVAL"`.

Only when a human developer reviews and approves the action does the system execute it.

**Columns**

1. **`id`**: Unique primary key number for each action (1, 2, 3...).

2. **`finding_id`**: Foreign key referencing `review_findings.id`, linking the suggested action to the specific finding it solves.

3. **`action_type`**: The kind of write action being requested:
   - `PR_COMMENT` – Post a review comment to the GitHub PR.
   - `APPLY_PATCH` – Apply a suggested code diff to the codebase.
   - `CREATE_TEST` – Generate and write a new unit test file.

4. **`payload`**: The actual content to execute (e.g., the code diff text, the generated Python test file, or the Markdown comment).

5. **`status`**: The approval state of this action:
   - `PENDING_APPROVAL` – Staged and waiting for a human developer to review.
   - `APPROVED` – Developer confirmed the action is safe and correct.
   - `REJECTED` – Developer dismissed the suggestion.
   - `EXECUTED` – Action was successfully performed (e.g., committed or posted).

6. **`resolved_by`**: Username of the developer who approved or rejected the action (e.g., `"durgaprasad"`).

7. **`resolved_at`**: Timestamp indicating when the decision was made.

8. **`created_at`**: Timestamp indicating when the AI proposed this action.


# indexing_service.py

## Why Is This Filter Essential?

1. **Third-Party Folders:** If a project contains folders like `venv/` or `node_modules/`, there could be thousands of files belonging to external libraries. We only want to index the developer's actual source code.

2. **Binary Files:** Trying to read images (`.png`), PDFs, or compiled files (`.pyc`) as text can cause errors. We should exclude these files from text processing.

3. **Huge Files:** A 5 MB minified JavaScript bundle or auto-generated data file can consume excessive memory and exceed AI token limits. We set a safe file-size limit (e.g., 500 KB).

## How Does the Filter Work?

- **`file_path.parts`**: Returns all the individual components of a file path as a tuple.

  Example:

  ```python
  file_path = Path("my_project/node_modules/express/index.js")

  file_path.parts
  # ('my_project', 'node_modules', 'express', 'index.js')
  ```

  Because `"node_modules"` is present in `IGNORE_DIRS`, the file is excluded immediately.

- **`file_path.suffix`**: Returns the file extension, such as `.png`, `.lock`, or `.py`.

- **`file_path.stat().st_size`**: Returns the file size in bytes. We can convert it into KB to check whether it exceeds the configured size limit.

1. **chunk_by_lines()**

Splits the given source code into smaller chunks based on a fixed number of lines.

Uses splitlines() to convert the source code into individual lines.

Calculates the step size using chunk_size - overlap.

Extracts chunks containing up to the specified number of lines.

Maintains overlapping lines between consecutive chunks to preserve context.

Stores each chunk along with its metadata:

File path

Starting and ending line numbers

Symbol name

Programming language

Actual code content

Returns a list of dictionaries containing the generated chunks.

2. **chunk_file()**

Reads a source code file from the filesystem and generates chunks using chunk_by_lines().

Opens the file in read mode using UTF-8 encoding.

Reads the complete file content.

Handles file-reading errors and returns an empty list if an error occurs.

Passes the file path and source code to chunk_by_lines().

Returns the generated chunks.

### Indexing Service – Code Parsing Update

The Indexing Service uses language-aware code parsing to divide source files into meaningful code blocks instead of relying on simple line-based splitting.

**How It Works**

1. **Python:** Splits code based on structures such as `class` and `def` (functions).
2. **Java and TypeScript:** Splits code based on structures such as `class`, `interface`, and `function`.
3. **Accurate Line Tracking:** Maintains the exact `start_line` and `end_line` for each code block, allowing the AI assistant to provide precise file and line references in review findings.
4. **No Manual Parsing Logic:** Uses a code parser instead of manually writing regular expressions or brace counters to identify code boundaries.


# Repository Indexing Service

### The Function: `index_repository_files()`

#### What this function does step-by-step:

1. Sets the repository status to `"INDEXING"` in the database.
2. Walks through every file and folder in the repository.
3. Calls `should_index_file()` to skip unwanted files and folders such as `.git`, `node_modules`, and images.
4. Calls `chunk_file()` on every valid source code file to split it into smaller chunks.
5. Creates `IndexedChunk` database objects and saves them into PostgreSQL.
6. Sets the repository status to `"READY"` to indicate that indexing is complete.


# Building the FastAPI REST API Layer

The FastAPI REST API layer consists of three main components:

### 1. Schemas (`schemas/`)

- Defines the structure of incoming request data and outgoing response data.
- Validates the data received from clients.
- Similar to Zod or Joi in Node.js.

### 2. Routers / Controllers (`api/v1/`)

- Handles incoming HTTP requests such as `POST` and `GET`.
- Calls the appropriate service functions to perform business logic.
- Returns the response to the client.

### 3. Main Application (`main.py`)

- Acts as the main entry point of the FastAPI application.
- Registers all API routers.
- Starts the application using an ASGI server such as Uvicorn.

### Why Do We Need Schemas?

- Schemas define the expected structure of incoming request data and outgoing response data.
- When a user sends a `POST /repositories` request with JSON data:
  `{"name": "my-project", "clone_url": "https://github.com/..."}`
- Pydantic validates the incoming data, ensuring that `name` is a string and is not empty.
- It also helps structure and format the response JSON before sending it back to the client.

### Why Do We Need `from_attributes = True`?
- Database returns SQLAlchemy object not a dictionary
- **`Optional[str] = None`**: The field can contain a string or `None`. By default, its value is `None`.
- **`from_attributes = True`**: Allows Pydantic to read data directly from SQLAlchemy model objects, instead of only reading from dictionaries.



# Repository API(repositories.py) – Important Points

## General

- **Database Session:** `Depends(get_db)` provides a database session for each request, ensuring requests use separate sessions.
- **SQLite Thread Safety:** Add `connect_args={"check_same_thread": False}` to `create_engine` because FastAPI may handle requests across different threads.
- **Refresh Database Object:** `db.refresh(new_repo)` reloads the object from the database to retrieve the latest values, including database-generated fields such as `id` and `created_at`.

## 1. `POST /repositories/` – Create a Repository

- Checks whether a repository with the same `name` already exists. Returns `400` if it does.
- Every new repository starts with the status `UNINDEXED`.
- Uses `db.add()`, `db.commit()`, and `db.refresh()` to save the repository and retrieve generated values such as `id` and `created_at`.
- `clone_url` is optional.

## 2. `GET /repositories/` – List All Repositories

- Retrieves all repositories from the database.
- Uses `@router.get(...)` with `response_model=List[RepositoryResponse]` because the endpoint returns a list.
- Pagination using `skip` and `limit` can be added later when the repository list grows.

## 3. `GET /repositories/{repo_id}` – Get a Single Repository

- `repo_id` is extracted from the URL and validated as an integer.
- Returns `404 Not Found` if the repository does not exist.
- Uses `.first()`, which returns the matching record or `None` if no record is found.
- Use `404` instead of `400` for a repository that does not exist.

## 4. `POST /repositories/{repo_id}/index` – Index Repository Code

- `repo_path` represents the local folder path of the repository and is passed as a query parameter.
- Checks whether the repository exists before starting the indexing process. Returns `404` if it does not.
- Calls `index_repository_files()` to process source files, divide them into chunks, and save the chunks in the database.
- Returns a `500 Internal Server Error` if the indexing process fails.
- The indexing service should update the repository status (for example, to `INDEXED`) so the response reflects the latest status.
- **Security:** A user-supplied `repo_path` could point to any folder on the server. Restrict access to an allowed directory, such as `DATA_DIR/repos`, before deploying.

## 5. `GET /repositories/{repo_id}/chunks` – View Repository Chunks

- Retrieves all `IndexedChunk` records associated with the specified repository.
- Uses `response_model=List[ChunkResponse]` because the endpoint returns a list of chunks.
- Returns an empty list if the repository has not been indexed yet.
- Add pagination later because source-code chunks can produce large responses.

### main.py

#### `Base.metadata.create_all(bind=engine)`

Creates all database tables based on the SQLAlchemy model classes, if they do not already exist.

**What Each Part Means**

- **`Base`**: The parent class inherited by all SQLAlchemy models, such as `Repository` and `IndexedChunk`.
- **`Base.metadata`**: Stores information about all models that inherit from `Base`, including table names, columns, and data types.
- **`create_all()`**: Reads the metadata and executes the required `CREATE TABLE` statements for tables that do not already exist.
- **`bind=engine`**: Specifies which database engine should be used to create the tables.



### Embedding Service

The Embedding Service converts text and source code into numerical vectors (lists of numbers) so the AI assistant can search for relevant information based on meaning rather than exact keyword matches.

**How It Works**

- Uses the `all-MiniLM-L6-v2` model from the `sentence-transformers` library.
- Runs locally on the machine. The model is downloaded once and can then work offline.
- Does not require an API key or paid embedding API.
- The model is loaded once when the module is imported, avoiding repeated loading for every request.
- Converts each input text into a vector containing **384 numerical values**.

**Functions**

| Function | Input | Output | Purpose |
|---|---|---|---|
| `embed_documents(texts)` | List of texts | List of vectors | Generates embeddings for multiple code chunks during indexing. |
| `embed_text(text)` | Single string | One vector | Generates an embedding for a user's question or a single text. |
| `cosine_similarity(a, b)` | Two vectors | Score between -1.0 and 1.0 | Measures the similarity between two vectors. |

**Important Points**

- `embed_documents()` processes 32 texts at a time using `batch_size=32` for efficient batch processing.
- Returns an empty list (`[]`) when the input list is empty.
- `convert_to_numpy=True` returns NumPy arrays, while `.tolist()` converts them into regular Python lists that can be stored in the database or serialized as JSON.
- **Cosine Similarity:**
  - `1.0` – Vectors point in the same direction.
  - `0.0` – Vectors are perpendicular (no cosine similarity).
  - `-1.0` – Vectors point in opposite directions.
- Returns `0.0` if either vector contains only zeros, avoiding division by zero.
- Always use the same embedding model for indexing and searching. Vectors generated by different models are not directly comparable. If the model changes, all existing code chunks must be re-embedded.

**Typical Workflow**

1. **Indexing:** Code chunks are passed to `embed_documents()` to generate embeddings.
2. **Storage:** Generated vectors are stored alongside their corresponding code chunks in the database.
3. **Query:** The user's question is passed to `embed_text()` to generate a query embedding.
4. **Similarity Search:** The query embedding is compared with stored embeddings using `cosine_similarity()`.
5. **Retrieval:** The code chunks with the highest similarity scores are selected as the most relevant context for the AI assistant.


### Connecting Embeddings to PostgreSQL & Searching

Currently, the Embedding Service can generate numerical vectors in memory. To complete the AI-powered code search layer, we need two main functions to connect embeddings with PostgreSQL.

**Functions**

1. **`save_chunk_embeddings()`**
   - Retrieves code chunks from PostgreSQL that do not have embeddings yet.
   - Generates vector embeddings for the retrieved code chunks.
   - Saves the generated embeddings into the `embedding_json` column.
   - Ensures existing embeddings are not unnecessarily regenerated.

2. **`search_codebase()`**
   - Accepts a developer's natural-language question (e.g., `"Where is the database session created?"`).
   - Converts the question into a numerical vector using the Embedding Service.
   - Compares the query vector against the stored code chunk embeddings in PostgreSQL.
   - Retrieves the top matching code snippets based on similarity scores.
   - Returns the relevant code along with exact file paths and line numbers (`start_line` and `end_line`) for accurate citations.

**Important Concept**

- **`json.dumps()`**: Converts a Python object, such as a dictionary or list, into a JSON-formatted string. This allows Python data to be stored or transferred in JSON format.