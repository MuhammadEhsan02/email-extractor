# API Specifications

**Base URL:** `/api/v1`

## 1. System Health

### `GET /health/`

Checks the operational status of the API and storage systems.

* **Response (200 OK):**

    ```json
    {
      "status": "healthy",
      "service": "Email Extraction System",
      "timestamp": "2023-10-27T10:00:00",
      "uptime": "0:05:23",
      "system_info": { ... },
      "components": {
        "api": "operational",
        "storage": "writable"
      }
    }
    ```

## 2. Extraction

### `POST /extract/`

Initiates a new email extraction job.

* **Request Body (`application/json`):**

    ```json
    {
      "input_data": "[https://example.com](https://example.com), [https://test.org](https://test.org)",
      "mode": "quick", // "quick", "deep", "custom"
      "output_formats": ["csv"],
      "config": {
        "max_urls_per_domain": 10,
        "respect_robots_txt": true
      },
      "ai_settings": {
        "enabled": false
      }
    }
    ```

* **Response (202 Accepted):**

    ```json
    {
      "job_id": "uuid-string-1234",
      "status": "queued",
      "message": "Extraction started in the background.",
      "created_at": "2023-10-27T10:01:00"
    }
    ```

### `GET /extract/{job_id}`

Retrieves the current status of a specific job.

* **Response (200 OK):**

    ```json
    {
      "id": "uuid-string-1234",
      "status": "completed", // "queued", "processing", "completed", "failed"
      "result_summary": {
        "emails_found": 15,
        "encrypted_file_id": "uuid-string-1234"
      },
      "passphrase": "generated-secure-key" // Only shown once upon completion
    }
    ```

## 3. Decryption

### `POST /decrypt/`

Decrypts and streams the requested file.

* **Request Body (`application/json`):**

    ```json
    {
      "file_id": "uuid-string-1234",
      "passphrase": "generated-secure-key"
    }
    ```

* **Response (200 OK):**
  * **Content-Type:** `application/octet-stream` (Binary File)
  * **Content-Disposition:** `attachment; filename="job_uuid_1234.csv"`

* **Errors:**
  * `401 Unauthorized`: Invalid passphrase.
  * `404 Not Found`: File ID does not exist.
