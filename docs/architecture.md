# System Architecture

## Overview

The Email Extraction System is a secure, internal web-based tool designed to extract business email addresses from publicly available websites. It prioritizes security, scalability, and controlled automation to prevent abuse and ensure data ownership through encryption.

## High-Level Architecture

The system follows a modular, service-oriented architecture, containerized with Docker.

### Core Components

1. **Frontend (UI Layer)**
    * **Technology:** HTML5, CSS3, Vanilla JavaScript.
    * **Function:** Provides a dashboard for users to input URLs, configure extraction settings, monitor job progress, and decrypt/download results.
    * **Communication:** Interacts with the Backend API via RESTful endpoints.

2. **Backend (API & Logic Layer)**
    * **Technology:** Python, FastAPI, Uvicorn.
    * **Role:** Handles request validation, orchestration, and core business logic.
    * **Key Modules:**
        * **Routes:** API endpoints (`/extract`, `/decrypt`, `/health`).
        * **Services:** `ExtractionService` (Orchestrator), `EncryptionService` (Security), `FileService` (Storage).
        * **Core:**
            * `Scraper`: Async web scraper with rate limiting and robot compliance.
            * `Parser`: HTML parser using BeautifulSoup4.
            * `EmailExtractor`: Regex-based extractor with validation heuristics.
            * `Limiter`: Enforces safety constraints (timeouts, max pages).
            * `Encryptor`: AES-256-GCM encryption module.

3. **Storage (Data Persistence)**
    * **Ephemeral Storage:** `storage/temp_html/` for intermediate processing artifacts.
    * **Secure Storage:** `storage/encrypted_files/` for final output files (AES-256 encrypted).
    * **Logs:** `logs/app.log` for system auditing and debugging.

## Security Architecture

* **Encryption at Rest:** All extracted data is encrypted immediately upon generation using AES-256-GCM. The backend does not permanently store plaintext files.
* **Key Management:** Decryption keys (passphrases) are generated per job and provided *only* to the user. The system does not persist these keys long-term.
* **Access Control:** The tool is designed for internal network use only.

## Data Flow Pipeline

1. **Input:** User submits raw text/URLs via Frontend.
2. **Validation:** Backend validates input and creates a Job ID.
3. **Extraction (Async Task):**
    * `UrlExtractor` cleans and validates target URLs.
    * `Scraper` fetches HTML content (respecting `robots.txt` and rate limits).
    * `Parser` extracts visible text from HTML.
    * `EmailExtractor` identifies and validates email addresses.
4. **File Generation:** Extracted data is compiled into a CSV/Excel file.
5. **Encryption:** The file is encrypted using a unique session key.
6. **Cleanup:** Temporary plaintext files are securely deleted.
7. **Delivery:** User requests decryption using the File ID and Session Key to download the result.

## Scalability & Performance

* **Asynchronous I/O:** Uses Python's `asyncio` and `aiohttp` for non-blocking network operations, allowing concurrent scraping of multiple pages.
* **Background Tasks:** FastAPI `BackgroundTasks` offload long-running extraction jobs, keeping the API responsive.
* **Containerization:** Docker ensures consistent environments and easy horizontal scaling if moved to an orchestration platform (e.g., Kubernetes).
