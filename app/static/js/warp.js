/**
 * WARP management functionality for Acestream Scraper
 */

// Get WARP status from API
async function fetchWarpStatus() {
    try {
        const response = await fetch('/api/warp/status');
        if (!response.ok) throw new Error('Failed to fetch WARP status');
        return await response.json();
    } catch (error) {
        console.error('Error fetching WARP status:', error);
        return {
            running: false,
            connected: false,
            mode: null,
            account_type: 'unknown',
            ip: null,
            enabled: false
        };
    }
}

// Update WARP UI based on status
async function updateWarpUI(forceRefresh = false) {
    try {
        const warpSection = document.getElementById('warpConfig');
        const warpLicenseSection = document.getElementById('warpLicenseConfig');
        
        if (!warpSection || !warpLicenseSection) {
            return; // Sections not found, likely not on config page
        }
        
        const status = forceRefresh ? await fetchWarpStatus() : cachedStatus || await fetchWarpStatus();
        cachedStatus = status;
        
        // Check if WARP is enabled in the container
        if (!status.enabled) {
            warpSection.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">Cloudflare WARP Status</h5>
                    <div class="alert alert-warning mb-0">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        WARP is not enabled in this container. To enable WARP, restart the container with the environment variable ENABLE_WARP=true and add required capabilities.
                    </div>
                </div>`;
            
            warpLicenseSection.style.display = 'none';
            return;
        }
        
        // If WARP is enabled, show the normal UI
        warpLicenseSection.style.display = 'block';
        
        // Update status badge
        const statusBadge = document.getElementById('warpStatusBadge');
        if (statusBadge) {
            if (status.running) {
                if (status.connected) {
                    statusBadge.className = 'badge bg-success';
                    statusBadge.textContent = 'Connected';
                } else {
                    statusBadge.className = 'badge bg-warning text-dark';
                    statusBadge.textContent = 'Running but Not Connected';
                }
            } else {
                statusBadge.className = 'badge bg-danger';
                statusBadge.textContent = 'Not Running';
            }
        }
        
        // Update mode
        const modeBadge = document.getElementById('warpMode');
        if (modeBadge) {
            modeBadge.textContent = status.mode || 'Unknown';
            modeBadge.className = 'badge ' + (status.mode ? 'bg-info' : 'bg-secondary');
        }
        
        // Update account type and IP
        document.getElementById('warpAccountType').textContent = status.account_type || '-';
        document.getElementById('warpIpAddress').textContent = status.ip || '-';
        
        // Update Cloudflare trace information
        const traceContainer = document.getElementById('warpTraceInfo');
        const traceDataContainer = document.getElementById('warpTraceData');
        
        if (traceContainer && traceDataContainer && status.cf_trace && Object.keys(status.cf_trace).length > 0) {
            traceContainer.classList.remove('d-none');
            
            // Format the trace data as a nice table
            let tableHtml = '<table class="table table-sm table-striped">';
            tableHtml += '<thead><tr><th>Property</th><th>Value</th><th>Description</th></tr></thead>';
            tableHtml += '<tbody>';
            
            // Define the order of important properties we want to show first
            const keyOrder = ['warp', 'ip', 'loc', 'colo', 'http', 'tls', 'sni'];
            const shownKeys = new Set();
            
            // Add ordered keys first
            for (const key of keyOrder) {
                if (status.cf_trace[key]) {
                    tableHtml += createTraceTableRow(key, status.cf_trace[key]);
                    shownKeys.add(key);
                }
            }
            
            // Add remaining keys
            for (const key in status.cf_trace) {
                if (!shownKeys.has(key)) {
                    tableHtml += createTraceTableRow(key, status.cf_trace[key]);
                }
            }
            
            tableHtml += '</tbody></table>';
            traceDataContainer.innerHTML = tableHtml;
        } else if (traceContainer) {
            traceContainer.classList.add('d-none');
        }
        
    } catch (error) {
        console.error('Error updating WARP UI:', error);
    }
}

// Helper function to create a table row for trace data
function createTraceTableRow(key, value) {
    const label = getTracePropertyLabel(key);
    const description = getTracePropertyDescription(key);
    const formattedValue = formatTraceValue(key, value);
    
    return `<tr>
        <td><strong>${label}</strong></td>
        <td>${formattedValue}</td>
        <td><small class="text-muted">${description}</small></td>
    </tr>`;
}

// Get human-readable label for trace property
function getTracePropertyLabel(key) {
    const labels = {
        'warp': 'WARP Status',
        'ip': 'IP Address',
        'loc': 'Location',
        'colo': 'Cloudflare Datacenter',
        'http': 'HTTP Protocol',
        'tls': 'TLS Version',
        'ts': 'Timestamp',
        'visit_scheme': 'Visit Scheme',
        'uag': 'User Agent',
        'sni': 'SNI',
        'gateway': 'Gateway',
        'rbi': 'Remote Browser',
        'kex': 'Key Exchange',
        'fl': 'Feature Flags',
        'h': 'Host',
        'sliver': 'Sliver'
    };
    
    return labels[key] || key.toUpperCase();
}

// Get description for trace property
function getTracePropertyDescription(key) {
    const descriptions = {
        'warp': 'Whether the request is using WARP',
        'ip': 'Your public IP address as seen by Cloudflare',
        'loc': 'Your country or region code',
        'colo': 'Cloudflare data center handling your request',
        'http': 'HTTP protocol version used for the request',
        'tls': 'TLS protocol version used for the connection',
        'ts': 'Timestamp when the request was processed',
        'visit_scheme': 'Protocol used for the request (HTTP/HTTPS)',
        'uag': 'User agent string of your client',
        'sni': 'Server Name Indication status',
        'gateway': 'Whether Cloudflare Gateway is being used',
        'rbi': 'Whether Remote Browser Isolation is active',
        'kex': 'Key exchange algorithm used for the TLS connection',
        'fl': 'Feature flag identifier',
        'h': 'The hostname requested',
        'sliver': 'Cloudflare infrastructure information'
    };
    
    return descriptions[key] || 'Additional connection information';
}

// Format trace values nicely
function formatTraceValue(key, value) {
    if (key === 'warp') {
        return value === 'on' 
            ? '<span class="badge bg-success">ON</span>' 
            : '<span class="badge bg-danger">OFF</span>';
    }
    
    if (key === 'ts' && !isNaN(parseFloat(value))) {
        const date = new Date(parseFloat(value) * 1000);
        return date.toLocaleString();
    }
    
    if (key === 'loc') {
        // Add flag emoji for country code
        return getCountryFlag(value) + ' ' + value;
    }
    
    return value;
}

// Get country flag emoji from country code
function getCountryFlag(countryCode) {
    // Convert country code to flag emoji (uses regional indicator symbols)
    if (countryCode && countryCode.length === 2) {
        const codePoints = [...countryCode.toUpperCase()].map(char => 
            127397 + char.charCodeAt(0)
        );
        return String.fromCodePoint(...codePoints);
    }
    return '';
}

// Connect to WARP
async function connectWarp() {
    try {
        showLoading();
        const response = await fetch('/api/warp/connect', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('success', data.message || 'Connected to WARP');
            await updateWarpUI(true);
        } else {
            showAlert('error', data.message || 'Failed to connect to WARP');
        }
    } catch (error) {
        console.error('Error connecting to WARP:', error);
        showAlert('error', 'Network error while connecting to WARP');
    } finally {
        hideLoading();
    }
}

// Disconnect from WARP
async function disconnectWarp() {
    try {
        showLoading();
        const response = await fetch('/api/warp/disconnect', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('success', data.message || 'Disconnected from WARP');
            await updateWarpUI(true);
        } else {
            showAlert('error', data.message || 'Failed to disconnect from WARP');
        }
    } catch (error) {
        console.error('Error disconnecting from WARP:', error);
        showAlert('error', 'Network error while disconnecting from WARP');
    } finally {
        hideLoading();
    }
}

// Set WARP mode
async function setWarpMode(mode) {
    try {
        showLoading();
        const response = await fetch('/api/warp/mode', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mode: mode })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('success', data.message || `WARP mode set to ${mode}`);
            await updateWarpUI(true);
        } else {
            showAlert('error', data.message || 'Failed to set WARP mode');
        }
    } catch (error) {
        console.error('Error setting WARP mode:', error);
        showAlert('error', 'Network error while setting WARP mode');
    } finally {
        hideLoading();
    }
}

// Register WARP license
async function registerWarpLicense(licenseKey) {
    try {
        showLoading();
        const response = await fetch('/api/warp/license', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ license_key: licenseKey })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('success', data.message || 'License registered successfully');
            await updateWarpUI(true);
            return true;
        } else {
            showAlert('error', data.message || 'Failed to register license');
            return false;
        }
    } catch (error) {
        console.error('Error registering WARP license:', error);
        showAlert('error', 'Network error while registering license');
        return false;
    } finally {
        hideLoading();
    }
}

// Initialize WARP UI
let cachedStatus = null;

document.addEventListener('DOMContentLoaded', function() {
    // Only run if we're on the config page
    if (document.getElementById('warpConfig')) {
        // Initial update
        updateWarpUI();
        
        // Set up event listeners
        document.getElementById('btnCheckWarpStatus').addEventListener('click', () => updateWarpUI(true));
        document.getElementById('btnConnectWarp').addEventListener('click', connectWarp);
        document.getElementById('btnDisconnectWarp').addEventListener('click', disconnectWarp);
        
        // Set up mode selection
        document.querySelectorAll('.warp-mode-option').forEach(option => {
            option.addEventListener('click', function(e) {
                e.preventDefault();
                setWarpMode(this.dataset.mode);
            });
        });
        
        // Set up license registration
        document.getElementById('warpLicenseForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const licenseKey = document.getElementById('warpLicenseInput').value.trim();
            if (licenseKey) {
                registerWarpLicense(licenseKey).then(success => {
                    if (success) {
                        document.getElementById('warpLicenseInput').value = '';
                    }
                });
            }
        });
    }
});

// Helper functions for UI feedback
function showLoading() {
    // Implement loading indicator if needed
    // For example, show a spinner or disable buttons
}

function hideLoading() {
    // Hide loading indicator
}

function showAlert(type, message) {
    // You can implement this based on your UI pattern
    // For example, display a toast notification
    console.log(`[${type}] ${message}`);
    
    // Example implementation using Bootstrap toast
    if (window.showToast) {
        window.showToast(message, type);
    }
}
