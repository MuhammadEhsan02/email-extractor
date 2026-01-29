# Email Extraction System

A secure, internal-only tool for extracting business email addresses from websites.
Designed with a focus on privacy (AES-256 encryption), scalability (Docker), and safety (Rate limiting).

## Quick Start

### Prerequisites

* Docker & Docker Compose
* Python 3.9+ (if running locally without Docker)

### Running with Docker (Recommended)

1. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd email-extraction-system
    ```

2. **Start the application:**

    ```bash
    docker-compose up --build
    ```

3. **Access the tool:**
    * **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
    * **Backend API Docs:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

### Running Locally (Development)

1. **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment:**
    Copy `.env.example` to `.env` and adjust settings if needed.

4. **Run the backend:**

    ```bash
    # Run from the root directory
    uvicorn backend.app.main:app --reload --port 8000
    ```

5. **Run the frontend:**
    Open `frontend/index.html` in your browser (or use a simple server like Live Server).

## Project Structure

* `backend/` - FastAPI application logic.
  * `app/core/` - Core extraction logic (Scraper, Parser, Encryptor).
  * `app/services/` - Orchestration and business logic.
  * `app/routes/` - API endpoints.
  * `app/storage/` - Runtime data (Encrypted files, logs).
* `frontend/` - Lightweight HTML/JS Dashboard.
* `docs/` - Architecture and API documentation.

## Security Features

* **Encryption at Rest:** All output files are encrypted using AES-256-GCM.
* **Decryption on Demand:** Files can only be decrypted using the unique passphrase generated per job.
* **Data Cleanup:** Temporary HTML files are deleted immediately after processing.

## Internal Use Only

This tool is designed for authorized internal operations. Ensure you have permission to scrape target websites and respect `robots.txt` policies.
