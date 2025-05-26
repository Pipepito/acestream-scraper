/**
 * Core functionality for the Acestream Scraper application
 */

// Show alert message to the user
function showAlert(type, message, duration = 5000) {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(alertContainer);
    }
    
    // Generate a unique ID for this alert
    const alertId = 'alert-' + Date.now();
    
    // Create the alert element
    const alertHTML = `
        <div id="${alertId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Add the alert to the container
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // Initialize and show the toast
    const toastElement = document.getElementById(alertId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });
    toast.show();
    
    // Remove the toast from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Show loading spinner
function showLoading() {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.style.display = 'inline-block';
    }
}

// Hide loading spinner
function hideLoading() {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Format date with local timezone
function formatLocalDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Handle API response and show appropriate message
 * @param {Response} response - Fetch API response object
 * @param {string} successMessage - Message to show on success
 * @param {Function} refreshCallback - Optional callback function to refresh data
 * @returns {Promise<Object>} - The parsed response data and success status
 */
async function handleApiResponse(response, successMessage = 'Operation successful', refreshCallback = null) {
    try {
        const data = await response.json();
        
        if (response.ok) {
            showAlert('success', data.message || successMessage);
            
            // Refresh data if callback provided
            if (typeof refreshCallback === 'function') {
                setTimeout(() => refreshCallback(), 1000);
            // If no specific callback is provided, try to use common refresh functions
            } else if (typeof refreshData === 'function') {
                setTimeout(() => refreshData(), 1000);
            } else if (typeof loadConfigData === 'function') {
                setTimeout(() => loadConfigData(), 1000);
            }
            
            return { success: true, data };
        } else {
            showAlert('error', data.message || data.error || 'Operation failed');
            return { success: false, data };
        }
    } catch (error) {
        console.error('Error processing response:', error);
        showAlert('error', 'Error processing response');
        return { success: false, error };
    }
}

/**
 * Make an API request with standardized handling
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch API options
 * @param {string} successMessage - Message to show on success 
 * @param {Function} refreshCallback - Optional callback function to refresh data
 * @returns {Promise<Object>} - The result of handleApiResponse
 */
async function makeApiRequest(url, options, successMessage, refreshCallback = null) {
    showLoading();
    try {
        console.log('Making API request to:', url, options); // Add debugging
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        console.log('Response:', response); // Add debugging
        
        if (!response.ok) {
            // Log more details about error responses
            console.error('API error:', response.status, await response.text());
        }
        
        return await handleApiResponse(response, successMessage, refreshCallback);
    } catch (error) {
        console.error('API request error:', error);
        showAlert('error', 'Network error while making request');
        return { success: false, error };
    } finally {
        hideLoading();
    }
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Update statistics in the footer
function updateStats(stats) {
    // Check if elements exist before updating them
    const totalChannelsEl = document.getElementById('totalChannels');
    const channelsCheckedEl = document.getElementById('channelsChecked');
    const channelsOnlineEl = document.getElementById('channelsOnline');
    const channelsOfflineEl = document.getElementById('channelsOffline');
    
    if (totalChannelsEl) totalChannelsEl.textContent = stats.total_channels || 0;
    if (channelsCheckedEl) channelsCheckedEl.textContent = stats.channels_checked || 0;
    if (channelsOnlineEl) channelsOnlineEl.textContent = stats.channels_online || 0;
    if (channelsOfflineEl) channelsOfflineEl.textContent = stats.channels_offline || 0;
}

// Fetch stats and update UI elements
async function fetchStats() {
    try {
        const statsResponse = await fetch('/api/stats/');
        return await statsResponse.json();
    } catch (error) {
        console.error('Error fetching stats:', error);
        return {};
    }
}

// Check Acestream Engine status
async function checkAcestreamStatus() {
    // Check if status checks are enabled
    const acestreamCheckEnabled = localStorage.getItem('enableAcestreamCheck') !== 'false';
    if (!acestreamCheckEnabled) {
        const acestreamStatus = document.getElementById('acestreamStatus');
        if (acestreamStatus) {
            acestreamStatus.className = 'badge bg-secondary';
            acestreamStatus.textContent = 'Check disabled';
        }
        const acestreamDetails = document.getElementById('acestreamDetails');
        if (acestreamDetails) {
            acestreamDetails.classList.add('d-none');
        }
        return;
    }

    try {
        const response = await fetch('/api/config/acestream_status');
        const data = await response.json();
        
        const acestreamStatus = document.getElementById('acestreamStatus');
        const acestreamDetails = document.getElementById('acestreamDetails');
        
        if (acestreamStatus) {
            if (data.available) {
                acestreamStatus.className = 'badge bg-success';
                acestreamStatus.textContent = data.is_internal ? 'Online' : 'External Online';
                
                if (acestreamDetails) {
                    acestreamDetails.classList.remove('d-none');
                    acestreamDetails.innerHTML = `
                        <div class="small">
                            <div>Version: ${data.version || 'Unknown'}</div>
                            <div>Platform: ${data.platform || 'Unknown'}</div>
                            <div>Network: ${data.connected ? 'Connected' : 'Disconnected'}</div>
                            ${!data.is_internal ? `<div>URL: ${data.engine_url || 'Unknown'}</div>` : ''}
                        </div>
                    `;
                }
            } else {
                if (data.is_internal === false && data.engine_url) {
                    // External engine is configured but not available
                    acestreamStatus.className = 'badge bg-danger';
                    acestreamStatus.textContent = 'External Offline';
                    
                    if (acestreamDetails) {
                        acestreamDetails.classList.remove('d-none');
                        acestreamDetails.innerHTML = `
                            <div class="small">
                                <div>URL: ${data.engine_url || 'Unknown'}</div>
                                <div class="text-danger">Cannot connect to external engine</div>
                            </div>
                        `;
                    }
                } else if (data.enabled) {
                    acestreamStatus.className = 'badge bg-danger';
                    acestreamStatus.textContent = 'Offline';
                    if (acestreamDetails) acestreamDetails.classList.add('d-none');
                } else {
                    acestreamStatus.className = 'badge bg-secondary';
                    acestreamStatus.textContent = 'Disabled';
                    if (acestreamDetails) acestreamDetails.classList.add('d-none');
                }
            }
        }
    } catch (error) {
        console.error('Error checking Acestream Engine status:', error);
        const acestreamStatus = document.getElementById('acestreamStatus');
        if (acestreamStatus) {
            acestreamStatus.className = 'badge bg-warning';
            acestreamStatus.textContent = 'Error';
        }
    }
}

// Check Acexy status
async function checkAcexyStatus() {
    // Check if status checks are enabled
    const acexyCheckEnabled = localStorage.getItem('enableAcexyCheck') !== 'false';
    if (!acexyCheckEnabled) {
        const acexyStatus = document.getElementById('acexyStatus');
        if (acexyStatus) {
            acexyStatus.className = 'badge bg-secondary';
            acexyStatus.textContent = 'Check disabled';
        }
        const acexyDetails = document.getElementById('acexyDetails');
        if (acexyDetails) {
            acexyDetails.classList.add('d-none');
        }
        return;
    }

    try {
        const response = await fetch('/api/config/acexy_status');
        const data = await response.json();
        
        const acexyStatus = document.getElementById('acexyStatus');
        const acexyDetails = document.getElementById('acexyDetails');
        
        if (acexyStatus) {
            if (data.enabled) {
                if (data.available) {
                    acexyStatus.className = 'badge bg-success';
                    acexyStatus.textContent = 'Online';
                    
                    if (acexyDetails) {
                        acexyDetails.classList.remove('d-none');
                        acexyDetails.innerHTML = `
                            <div class="small">
                                <div>Acexy version: ${data.version || 'Unknown'}</div>
                            </div>
                        `;
                    }
                } else {
                    acexyStatus.className = 'badge bg-danger';
                    acexyStatus.textContent = 'Offline';
                    if (acexyDetails) acexyDetails.classList.add('d-none');
                }
            } else {
                acexyStatus.className = 'badge bg-secondary';
                acexyStatus.textContent = 'Disabled';
                if (acexyDetails) acexyDetails.classList.add('d-none');
            }
        }
    } catch (error) {
        console.error('Error checking Acexy status:', error);
        const acexyStatus = document.getElementById('acexyStatus');
        if (acexyStatus) {
            acexyStatus.className = 'badge bg-warning';
            acexyStatus.textContent = 'Error';
        }
    }
}

// Initialize automatic status checks
function initStatusAutoRefresh() {
    // Set up Acestream Engine status auto-refresh
    let acestreamInterval;
    
    function setupAcestreamAutoRefresh() {
        // Clear existing interval if any
        if (acestreamInterval) {
            clearInterval(acestreamInterval);
        }
        
        // Only set up auto-refresh if status checks are enabled
        const checkEnabled = localStorage.getItem('enableAcestreamCheck') !== 'false';
        if (!checkEnabled) {
            return;
        }
        
        // Get the configured interval or use default
        const intervalSeconds = parseInt(localStorage.getItem('acestreamCheckInterval'), 10) || 120;
        
        // Set up new interval
        acestreamInterval = setInterval(checkAcestreamStatus, intervalSeconds * 1000);
        console.log(`Auto-refresh for Acestream Engine status set to ${intervalSeconds} seconds`);
    }
    
    // Set up Acexy status auto-refresh
    let acexyInterval;
    
    function setupAcexyAutoRefresh() {
        // Clear existing interval if any
        if (acexyInterval) {
            clearInterval(acexyInterval);
        }
        
        // Only set up auto-refresh if status checks are enabled
        const checkEnabled = localStorage.getItem('enableAcexyCheck') !== 'false';
        if (!checkEnabled) {
            return;
        }
        
        // Get the configured interval or use default
        const intervalSeconds = parseInt(localStorage.getItem('acexyCheckInterval'), 10) || 60;
        
        // Set up new interval
        acexyInterval = setInterval(checkAcexyStatus, intervalSeconds * 1000);
        console.log(`Auto-refresh for Acexy status set to ${intervalSeconds} seconds`);
    }
    
    // Initial setup for both
    setupAcestreamAutoRefresh();
    setupAcexyAutoRefresh();
    
    // Watch for changes to the localStorage settings
    window.addEventListener('storage', function(e) {
        if (e.key === 'enableAcestreamCheck' || e.key === 'acestreamCheckInterval') {
            setupAcestreamAutoRefresh();
        }
        if (e.key === 'enableAcexyCheck' || e.key === 'acexyCheckInterval') {
            setupAcexyAutoRefresh();
        }
    });
    
    // Do initial checks
    const acestreamCheckEnabled = localStorage.getItem('enableAcestreamCheck') !== 'false';
    if (acestreamCheckEnabled) {
        checkAcestreamStatus();
    }
    
    const acexyCheckEnabled = localStorage.getItem('enableAcexyCheck') !== 'false';
    if (acexyCheckEnabled) {
        checkAcexyStatus();
    }
}

// Document ready function
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips on all elements with data-bs-toggle="tooltip"
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
    
    // Update stats on page load - only if we're on a page with stats elements
    fetchStats().then(stats => {
        // Only call updateStats if at least one of the elements exists
        if (document.getElementById('totalChannels') || 
            document.getElementById('channelsChecked') || 
            document.getElementById('channelsOnline') || 
            document.getElementById('channelsOffline')) {
            updateStats(stats);
        }
    });
    
    // Initialize automatic status checks
    initStatusAutoRefresh();
});