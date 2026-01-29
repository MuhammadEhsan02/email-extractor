# Project Requirements

## Business Requirements

1. **Goal:** Automate the collection of business email addresses for internal lead generation.
2. **Privacy:** The tool must be for internal use only. Extracted data must not be accessible to unauthorized users or external entities.
3. **Efficiency:** Replaces manual copy-pasting from search results with an automated bulk process.
4. **Ownership:** Output data must be securely owned by the user who initiated the job (enforced via encryption keys).

## Technical Requirements

### Functional

* **Input:** Accept raw text, lists of URLs, or messy copy-pastes.
* **Extraction:** Identify and validate email addresses from HTML content.
* **Output:** Generate structured CSV or Excel files.
* **Encryption:** All output files must be AES-256 encrypted at rest. Decryption is on-demand only.

### Non-Functional

* **Security:** No storage of plaintext emails on disk. Minimal retention of temporary files.
* **Scalability:** Must handle multiple concurrent URL requests without blocking the server (AsyncIO).
* **Reliability:** Robust error handling for network failures (timeouts, 404s) and messy HTML.
* **Compliance:** Respect `robots.txt` and implement rate limiting to be a "polite" scraper.

### Constraints

* **Tech Stack:** Python (FastAPI), Docker.
* **Deployment:** Containerized for easy internal deployment.
* **AI:** Optional integration for categorization, but core logic must function deterministically without it.
