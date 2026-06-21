# ShieldX Web Backend

This is the FastAPI backend for the ShieldX web platform. It provides APIs for agent heartbeats, malware alerts, and whitelisted domain management.

## Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd ShieldX_web/backend
    ```

2.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

3.  **Install dependencies (if you haven't already):**
    ```bash
    pip install -r requirements.txt
    ```
    (Note: `requirements.txt` will be created below, but for now, the dependencies were installed directly via `pip install` in Step 3.)

4.  **Database Setup (MySQL):**
    -   Ensure you have a MySQL server running.
    -   Create a database, e.g., `shieldx_db`.
    -   Create a user and grant privileges to this database.

5.  **Environment Variables:**
    -   Create a `.env` file in the `ShieldX_web/backend/` directory (you can copy `.env.example`).
    -   Set your database connection string:
        ```
        DATABASE_URL="mysql+mysqlconnector://user:password@host:port/database_name"
        ```
        Example: `DATABASE_URL="mysql+mysqlconnector://root:mysecretpassword@localhost:3306/shieldx_db"`

## Running the Application

1.  **Activate your virtual environment** (if not already active):
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the FastAPI application:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    The API documentation (Swagger UI) will be available at `http://localhost:8000/docs`.

## API Endpoints

-   `POST /heartbeat/`
-   `POST /report-malware/`
-   `GET /domain/whitelist/`
-   `POST /domain/whitelist/`
-   `PUT /domain/whitelist/{domain_id}`
-   `DELETE /domain/whitelist/{domain_id}`
