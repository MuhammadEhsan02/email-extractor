/**
 * Email Extraction System - Frontend Logic
 * Handles API communication for Job Submission, Status Polling, and File Decryption.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

// DOM Elements
const elements = {
    extractForm: document.getElementById('extractForm'),
    decryptForm: document.getElementById('decryptForm'),
    inputData: document.getElementById('inputData'),
    startBtn: document.getElementById('startBtn'),
    decryptBtn: document.getElementById('decryptBtn'),
    
    // Status Elements
    jobStatusContainer: document.getElementById('jobStatusContainer'),
    currentJobId: document.getElementById('currentJobId'),
    statusBadge: document.getElementById('statusBadge'),
    progressBar: document.getElementById('progressBar'),
    statusMessage: document.getElementById('statusMessage'),
    secureCredentials: document.getElementById('secureCredentials'),
    
    // Result Elements
    resultFileId: document.getElementById('resultFileId'),
    resultPassphrase: document.getElementById('resultPassphrase'),
    
    // Health Element
    healthIndicator: document.getElementById('health-indicator')
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    checkSystemHealth();
});

// --- Event Listeners ---

// 1. Handle Extraction Submission
elements.extractForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // UI Reset
    resetExtractionUI();
    setLoading(true);

    const payload = {
        input_data: elements.inputData.value,
        mode: document.getElementById('scanMode').value,
        config: {
            respect_robots_txt: document.getElementById('respectRobots').checked
        },
        ai_settings: {
            enabled: document.getElementById('aiEnable').checked
        }
    };

    try {
        const response = await fetch(`${API_BASE_URL}/extract/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('Failed to start job');

        const data = await response.json();
        
        // Job Started Successfully
        startPolling(data.job_id);

    } catch (error) {
        showError(error.message);
        setLoading(false);
    }
});

// 2. Handle Decryption & Download
elements.decryptForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileId = document.getElementById('decryptFileId').value.trim();
    const passphrase = document.getElementById('decryptPassphrase').value.trim();
    const btn = elements.decryptBtn;
    const msg = document.getElementById('downloadMessage');

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Decrypting...';
    msg.textContent = '';

    try {
        const response = await fetch(`${API_BASE_URL}/decrypt/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: fileId, passphrase: passphrase })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Decryption failed');
        }

        // Handle Binary File Download
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        // Extract filename from headers if possible, else default
        const contentDisp = response.headers.get('Content-Disposition');
        let fileName = 'extracted_emails.csv';
        if (contentDisp && contentDisp.includes('filename=')) {
            fileName = contentDisp.split('filename=')[1].replace(/"/g, '');
        }

        a.href = downloadUrl;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);

        msg.textContent = 'Download started successfully.';
        msg.style.color = 'var(--accent-green)';

    } catch (error) {
        msg.textContent = `Error: ${error.message}`;
        msg.style.color = 'var(--accent-red)';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-unlock"></i> Decrypt & Download';
    }
});

// --- Logic Functions ---

let pollInterval;

function startPolling(jobId) {
    elements.jobStatusContainer.classList.remove('hidden');
    elements.currentJobId.textContent = jobId;
    elements.statusMessage.textContent = "Job queued on server...";
    
    // Poll every 2 seconds
    pollInterval = setInterval(async () => {
        try {
            // NOTE: This assumes a GET endpoint exists at /extract/{job_id}
            // If strictly following previous code blocks, this endpoint needs 
            // to be added to routes/extract.py to support this frontend feature.
            const response = await fetch(`${API_BASE_URL}/extract/${jobId}`);
            
            if (response.ok) {
                const job = await response.json();
                updateStatusUI(job);

                if (job.status === 'completed' || job.status === 'failed') {
                    clearInterval(pollInterval);
                    setLoading(false);
                }
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 2000);
}

function updateStatusUI(job) {
    elements.statusBadge.textContent = job.status;
    elements.statusBadge.className = `badge-status ${job.status}`;

    if (job.status === 'processing') {
        elements.progressBar.style.width = '50%';
        elements.statusMessage.textContent = "Scraping and analyzing websites...";
    } else if (job.status === 'completed') {
        elements.progressBar.style.width = '100%';
        elements.statusMessage.textContent = "Extraction finished successfully.";
        
        // Show Credentials
        elements.secureCredentials.classList.remove('hidden');
        elements.resultFileId.value = job.result_summary.encrypted_file_id;
        elements.resultPassphrase.value = job.passphrase; // Only available once
        
    } else if (job.status === 'failed') {
        elements.progressBar.style.width = '100%';
        elements.progressBar.style.backgroundColor = 'var(--accent-red)';
        elements.statusMessage.textContent = `Error: ${job.error || 'Unknown failure'}`;
    }
}

function resetExtractionUI() {
    elements.jobStatusContainer.classList.add('hidden');
    elements.secureCredentials.classList.add('hidden');
    elements.progressBar.style.width = '0%';
    elements.progressBar.style.backgroundColor = 'var(--accent-blue)';
}

function setLoading(isLoading) {
    elements.startBtn.disabled = isLoading;
    if (isLoading) {
        elements.startBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Processing...';
    } else {
        elements.startBtn.innerHTML = '<i class="fas fa-play"></i> Start Extraction';
    }
}

async function checkSystemHealth() {
    try {
        const res = await fetch(`${API_BASE_URL}/health/`);
        if (res.ok) {
            elements.healthIndicator.textContent = "Operational";
            elements.healthIndicator.style.color = "var(--accent-green)";
        } else {
            throw new Error();
        }
    } catch {
        elements.healthIndicator.textContent = "Offline";
        elements.healthIndicator.style.color = "var(--accent-red)";
    }
}

function showError(msg) {
    alert(msg); // Simple alert for MVP
}

// Global utility for HTML onclick
window.copyToClipboard = (elementId) => {
    const copyText = document.getElementById(elementId);
    copyText.select();
    document.execCommand("copy");
    
    // Visual feedback
    const btn = copyText.nextElementSibling;
    const originalIcon = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check"></i>';
    setTimeout(() => {
        btn.innerHTML = originalIcon;
    }, 1000);
};