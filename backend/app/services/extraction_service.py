import logging
import asyncio
import os
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse

# Import Models
from app.models.extract_request import ExtractRequest, ExtractionMode
from app.models.extract_response import JobStatus

# Import Core Modules
from app.core.url_extractor import extract_urls as core_extract_urls
from app.core.scraper import WebScraper
from app.core.parser import HTMLParser
from app.core.email_extractor import EmailExtractor
from app.core.categorizer import EmailCategorizer
from app.core.limiter import LimitEnforcer, LimitConfig
from app.core.file_generator import EmailFileGenerator
from app.core.utils import is_valid_url

# Import Services
from app.services.file_service import FileService
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)

# In-memory job store (Replace with Redis/DB in production)
JOB_STORE: Dict[str, Dict] = {}

class ExtractionService:
    """
    Orchestrates the full email extraction pipeline.
    """

    def __init__(self):
        self.file_service = FileService()
        self.encryption_service = EncryptionService()

    async def create_job(self, request: ExtractRequest) -> str:
        """
        Initializes a job record and returns the Job ID.
        """
        job_id = self.file_service.generate_file_id()
        
        # Store initial job state
        JOB_STORE[job_id] = {
            "id": job_id,
            "status": JobStatus.QUEUED,
            "created_at": datetime.now(),
            "request": request,
            "result_summary": None,
            "passphrase": None  # Will be generated upon completion
        }
        return job_id

    async def process_extraction(self, job_id: str, request: ExtractRequest):
        """
        The main worker function running in the background.
        Pipeline: Extract URLs -> Scrape -> Parse -> Extract Emails -> Generate File -> Encrypt.
        """
        logger.info(f"Starting extraction job {job_id} in mode {request.mode}")
        JOB_STORE[job_id]["status"] = JobStatus.PROCESSING
        
        temp_files = []
        final_output_path = None
        
        try:
            # 1. Extract Target URLs from Input [cite: 19]
            # Using the core/url_extractor.py module
            target_urls = core_extract_urls(request.input_data)
            
            # Filter valid URLs only
            target_urls = [u for u in target_urls if is_valid_url(u)]
            
            if not target_urls:
                raise ValueError("No valid URLs found in input data.")

            # [cite_start]Apply limits based on request config [cite: 22]
            # Using core/limiter.py
            limiter = LimitEnforcer(config=LimitConfig(
                max_pages_per_domain=request.config.max_urls_per_domain,
                max_execution_time_minutes=request.config.request_timeout / 60 * len(target_urls) # Dynamic timeout
            ))

            # [cite_start]2. Initialize Scraper [cite: 20]
            # Using core/scraper.py
            scraper = WebScraper(
                respect_robots=request.config.respect_robots_txt,
                rate_limit_delay=1.0
            )

            # [cite_start]3. Initialize Parser & Extractor [cite: 20, 21]
            # Using core/parser.py and core/email_extractor.py
            parser = HTMLParser()
            extractor = EmailExtractor(min_confidence=request.ai_settings.min_confidence)
            categorizer = EmailCategorizer()

            extracted_data = []

            # 4. Processing Loop (BFS Crawler per domain)
            MAX_EMAILS = 5
            MAX_PAGES_VISITED = 15
            
            for base_target in target_urls:
                queue = [base_target]
                visited = set()
                domain_emails_count = 0
                pages_visited = 0
                base_domain_added = False
                
                while queue and pages_visited < MAX_PAGES_VISITED and domain_emails_count < MAX_EMAILS:
                    current_url = queue.pop(0)
                    if current_url in visited:
                        continue
                        
                    visited.add(current_url)
                    pages_visited += 1
                    
                    # Ensure we don't scrape multiple manually since we use BFS here, 
                    # we just scrape one by one. User approved the increased time.
                    result = await scraper.scrape(current_url)
                    
                    parsed_url = urlparse(current_url)
                    root_domain_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    
                    if result.status_code == 200 and result.html:
                        # Parse HTML
                        parsed_content = parser.parse(result.html, base_url=result.url)
                        
                        # Extract Contacts (passing raw HTML for deep extraction)
                        contacts = extractor.extract(parsed_content.text, result.html)
                        business_label = categorizer.predict_business_type(parsed_content.text)
                        phones_str = ", ".join(contacts.phone_numbers)
                        
                        new_emails_found = 0
                        
                        if not contacts.emails and contacts.phone_numbers:
                            extracted_data.append({
                                "email": "",
                                "source_url": result.url,
                                "domain": parsed_url.netloc,
                                "confidence": 0.0,
                                "context": "",
                                "phone_numbers": phones_str,
                                "business_label": business_label,
                                "facebook": contacts.social_links.get("facebook", ""),
                                "instagram": contacts.social_links.get("instagram", ""),
                                "linkedin": contacts.social_links.get("linkedin", ""),
                                "twitter": contacts.social_links.get("twitter", ""),
                                "whatsapp": contacts.social_links.get("whatsapp", "")
                            })
                        else:
                            for email_info in contacts.emails:
                                if domain_emails_count >= MAX_EMAILS:
                                    break
                                extracted_data.append({
                                    "email": email_info.email,
                                    "source_url": result.url,
                                    "domain": email_info.domain,
                                    "confidence": email_info.confidence_score,
                                    "context": email_info.source_context[:100] if email_info.source_context else "",
                                    "phone_numbers": phones_str,
                                    "business_label": business_label,
                                    "facebook": contacts.social_links.get("facebook", ""),
                                    "instagram": contacts.social_links.get("instagram", ""),
                                    "linkedin": contacts.social_links.get("linkedin", ""),
                                    "twitter": contacts.social_links.get("twitter", ""),
                                    "whatsapp": contacts.social_links.get("whatsapp", "")
                                })
                                domain_emails_count += 1
                                new_emails_found += 1
                        
                        # Log success for limiter
                        limiter.record_success(result.url, len(result.html))
                        
                        # Base URL Fallback
                        if pages_visited == 1 and new_emails_found == 0 and not base_domain_added and root_domain_url != current_url:
                            if root_domain_url not in visited and root_domain_url not in queue:
                                queue.append(root_domain_url)
                                base_domain_added = True
                                
                        # Add links to queue if in deep mode
                        mode_str = getattr(request.mode, "value", request.mode)
                        if str(mode_str).lower() == 'deep' and domain_emails_count < MAX_EMAILS:
                            for link in parsed_content.links:
                                link_parsed = urlparse(link)
                                if link_parsed.netloc == parsed_url.netloc and link not in visited and link not in queue:
                                    queue.append(link)
                                    
                    else:
                        limiter.record_failure(result.url, result.error or "Unknown error")
                        # Fallback for failed first request
                        if pages_visited == 1 and not base_domain_added and root_domain_url != current_url:
                            if root_domain_url not in visited and root_domain_url not in queue:
                                queue.append(root_domain_url)
                                base_domain_added = True

            logger.info(f"Job {job_id}: Extracted {len(extracted_data)} contacts.")

            if not extracted_data:
                raise ValueError("No contacts could be extracted from the provided URLs.")

            # [cite_start]5. Generate Output File (CSV/Excel) [cite: 24]
            # Using core/file_generator.py
            generator = EmailFileGenerator()
            
            # Create a temporary directory for this job's artifacts
            temp_dir = self.file_service.temp_dir
            raw_filename_base = f"job_{job_id}"
            
            # Generation format before encryption
            generated_files = generator.generate_output(
                emails=extracted_data,
                output_dir=str(temp_dir),
                filename_prefix=raw_filename_base,
                formats=['xlsx'] # Generate Excel
            )
            
            raw_file_path = generated_files.get('xlsx')
            if not raw_file_path:
                raise Exception("Failed to generate output file.")
            
            temp_files.append(raw_file_path)

            # [cite_start]6. Encrypt the Output [cite: 28]
            # Using encryption_service.py
            encrypted_path = self.file_service.get_encrypted_file_path(job_id)
            
            # GENERATE A SECURE PASSPHRASE FOR THIS JOB
            # In a real app, this might be a system key or returned to the user.
            passphrase = os.urandom(16).hex()
            
            self.encryption_service.encrypt_output_file(
                input_path=raw_file_path,
                output_path=encrypted_path,
                passphrase=passphrase
            )

            # 7. Update Job Status
            JOB_STORE[job_id]["status"] = JobStatus.COMPLETED
            JOB_STORE[job_id]["result_summary"] = {
                "contacts_found": len(extracted_data),
                "encrypted_file_id": job_id
            }
            # IMPORTANT: Storing the passphrase in memory for the demo.
            # In production, this should be securely delivered to the user or stored in a Vault.
            JOB_STORE[job_id]["passphrase"] = passphrase 
            
            logger.info(f"Job {job_id} completed successfully. Encrypted file stored.")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            JOB_STORE[job_id]["status"] = JobStatus.FAILED
            JOB_STORE[job_id]["error"] = str(e)

        finally:
            # 8. Cleanup Temporary Files
            for path in temp_files:
                self.file_service.cleanup_file(path)

    def get_job_status(self, job_id: str) -> Dict:
        """Retrieves status of a job."""
        return JOB_STORE.get(job_id, None)