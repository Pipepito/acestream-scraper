/**
 * Acexy integration functionality for Acestream Scraper
 */

// Check Acexy status
async function checkAcexyStatus(showLoadingIndicator = false) {
    // Check if status checks are enabled
    const acexyCheckEnabled = localStorage.getItem('enableAcexyCheck') !== 'false';
    if (!acexyCheckEnabled) {
        const acexyStatus = document.getElementById('acexyStatus');
        if (acexyStatus) {
            acexyStatus.className = 'badge bg-secondary';
            acexyStatus.textContent = 'Check disabled';
        }
        const acexyStreams = document.getElementById('acexyStreams');
        if (acexyStreams) {
            acexyStreams.classList.add('d-none');
        }
        return;
    }

    try {
        if (showLoadingIndicator) showLoading();
        
        const response = await fetch('/api/config/acexy_status');
        const data = await response.json();
        
        // Update Acexy status badge and streams info
        const acexyStatusElement = document.getElementById('acexyStatus');
        const acexyStreamsElement = document.getElementById('acexyStreams');
        
        if (acexyStatusElement) {
            if (data.enabled) {
                if (data.available) {
                    acexyStatusElement.innerHTML = '<span class="badge bg-success">Online</span>';
                    if (acexyStreamsElement) {
                        acexyStreamsElement.classList.remove('d-none');
                        acexyStreamsElement.querySelector('.fw-bold').textContent = data.active_streams;
                    }
                } else {
                    acexyStatusElement.innerHTML = '<span class="badge bg-danger">Offline</span>';
                    if (acexyStreamsElement) {
                        acexyStreamsElement.classList.add('d-none');
                    }
                }
            } else {
                acexyStatusElement.innerHTML = '<span class="badge bg-secondary">Disabled</span>';
                if (acexyStreamsElement) {
                    acexyStreamsElement.classList.add('d-none');
                }
            }
        }
        
        // Show/hide Acexy features
        const acexyElements = document.querySelectorAll('.acexy-feature');
        if (data.enabled) {
            acexyElements.forEach(el => el.classList.remove('d-none'));
        } else {
            acexyElements.forEach(el => el.classList.add('d-none'));
        }
        
        return data;
    } catch (error) {
        console.error('Error checking Acexy status:', error);
        const acexyStatusElement = document.getElementById('acexyStatus');
        if (acexyStatusElement) {
            acexyStatusElement.innerHTML = '<span class="badge bg-warning">Error</span>';
        }
        const acexyStreamsElement = document.getElementById('acexyStreams');
        if (acexyStreamsElement) {
            acexyStreamsElement.classList.add('d-none');
        }
        return { enabled: false, available: false };
    } finally {
        if (showLoadingIndicator) hideLoading();
    }
}

// Update Acexy status on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with Acexy info
    if (document.getElementById('acexyStatus') || document.getElementById('acexyStatusConfig')) {
        checkAcexyStatus();
    }
});