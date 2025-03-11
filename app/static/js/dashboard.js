/**
 * Dashboard-specific functionality for Acestream Scraper
 */

// Refresh all dashboard data
async function refreshData() {
    showLoading();
    try {
        const searchTerm = document.getElementById('channelSearch')?.value || '';

        // Fetch stats
        const stats = await fetchStats();
        
        // Update URL list
        const urlsList = document.getElementById('urlsList');
        if (urlsList && stats.urls) {
            urlsList.innerHTML = stats.urls.map(url => `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="row w-100">
                        <div class="col-12 col-md-6 text-break">
                            <span class="status-${url.status.toLowerCase()}">${url.status}</span>
                            <span class="ms-2">${url.url}</span>
                        </div>
                        <div class="col-6 col-md-3 text-md-end">
                            <span class="badge bg-primary">${url.channel_count} channels</span>
                        </div>
                        <div class="col-6 col-md-3 text-end">
                            <button class="btn btn-sm ${url.enabled ? 'btn-warning' : 'btn-success'}" 
                                    onclick="toggleUrl('${url.url}', ${!url.enabled})">
                                ${url.enabled ? 'Disable' : 'Enable'}
                            </button>
                            <button class="btn btn-sm btn-danger" 
                                    onclick="deleteUrl('${url.url}')">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        // Update base URL info
        if (stats.base_url) {
            const currentBaseUrlDisplay = document.getElementById('currentBaseUrlDisplay');
            const sampleUrlDisplay = document.getElementById('sampleUrlDisplay');
            if (currentBaseUrlDisplay) currentBaseUrlDisplay.textContent = `Current: ${stats.base_url}`;
            if (sampleUrlDisplay) sampleUrlDisplay.innerHTML = `Sample: <code>${stats.base_url}${'1'.repeat(40)}</code>`;
        }

        // Update Ace Engine URL info
        if (stats.ace_engine_url) {
            const aceEngineUrlDisplay = document.getElementById('currentAceEngineUrlDisplay');
            if (aceEngineUrlDisplay) {
                aceEngineUrlDisplay.textContent = `Current: ${stats.ace_engine_url}`;
                
                // Add Acexy information if not already there
                if (!document.getElementById('acexyInfoSection')) {
                    const acexyInfoDiv = document.createElement('div');
                    acexyInfoDiv.id = 'acexyInfoSection';
                    acexyInfoDiv.innerHTML = `
                        <h5 class="card-title mt-3">Acexy</h5>
                        <p class="mb-1 text-muted small">
                            <a href="https://github.com/Javinator9889/acexy" target="_blank" class="acexy-feature">
                                Integrated Acexy
                            </a>
                        </p>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>
                                Status: <span id="acexyStatus" class="badge bg-secondary">Checking...</span>
                            </span>
                            <button onclick="checkAcexyStatus(true)" class="btn btn-sm btn-info" title="Check Acexy status">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-repeat" viewBox="0 0 16 16">
                                    <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                                    <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
                                </svg>
                            </button>
                        </div>
                    `;
                    
                    const acexyInfoContainer = document.getElementById('acexyInfoContainer');
                    if (acexyInfoContainer) {
                        acexyInfoContainer.innerHTML = '';
                        acexyInfoContainer.appendChild(acexyInfoDiv);
                    }
                }
            }
        }

        // Update rescrape interval info
        if (stats.rescrape_interval) {
            const rescrapeInfoContainer = document.getElementById('rescrapeInfoContainer');
            if (rescrapeInfoContainer) {
                rescrapeInfoContainer.innerHTML = `
                    <h5 class="card-title">Rescrape Interval</h5>
                    <p id="currentRescrapeInterval" class="mb-1 text-muted small">
                        Current: ${stats.rescrape_interval} hours
                    </p>
                `;
            }
        }

        // Update channels list
        await refreshChannelsList(searchTerm);
        
        // Check Acexy status 
        await checkAcexyStatus();
        
    } catch (error) {
        console.error('Error refreshing dashboard data:', error);
    } finally {
        hideLoading();
    }
}

// Function to download playlist
function downloadPlaylist(refresh = false) {
    const searchTerm = document.getElementById('channelSearch')?.value.trim();
    let url = '/playlist.m3u'; // Use original URL for backward compatibility
    const params = new URLSearchParams();
    
    if (refresh) {
        params.append('refresh', 'true');
    }
    if (searchTerm) {
        params.append('search', searchTerm);
    }
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    window.location.href = url;
}

// Check Acexy status
async function checkAcexyStatus(showLoadingIndicator = false) {
    try {
        if (showLoadingIndicator) showLoading();
        
        const response = await fetch('/api/config/acexy_status');
        const data = await response.json();
        
        // Update Acexy status badge
        const acexyStatusElement = document.getElementById('acexyStatus');
        if (acexyStatusElement) {
            if (data.enabled) {
                if (data.available) {
                    acexyStatusElement.innerHTML = '<span class="badge bg-success">Online</span>';
                } else {
                    acexyStatusElement.innerHTML = '<span class="badge bg-danger">Offline</span>';
                }
            } else {
                acexyStatusElement.innerHTML = '<span class="badge bg-secondary">Disabled</span>';
            }
        }
        
        // Show/hide Acexy features
        const acexyElements = document.querySelectorAll('.acexy-feature');
        if (data.enabled) {
            acexyElements.forEach(el => el.classList.remove('d-none'));
        } else {
            acexyElements.forEach(el => el.classList.add('d-none'));
        }
    } catch (error) {
        console.error('Error checking Acexy status:', error);
        const acexyStatusElement = document.getElementById('acexyStatus');
        if (acexyStatusElement) {
            acexyStatusElement.innerHTML = '<span class="badge bg-warning">Error</span>';
        }
    } finally {
        if (showLoadingIndicator) hideLoading();
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    refreshData();
    
    // Set up event listeners for dashboard-specific elements
    const addChannelForm = document.getElementById('addChannelForm');
    if (addChannelForm) {
        addChannelForm.addEventListener('submit', handleAddChannel);
    }
    
    // Refresh periodically
    setInterval(refreshData, 60000); // Every minute
});

async function handleAddUrl(e) {
    e.preventDefault();
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    
    if (!url) {
        showAlert('error', 'Please enter a URL');
        return;
    }
    
    try {
        showLoading();
        const response = await fetch('/api/urls/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        if (await handleApiResponse(response, 'URL added successfully')) {
            urlInput.value = '';
            // Refresh data after successful addition
            if (typeof refreshData === 'function') {
                await refreshData();
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('error', 'Network error while adding URL');
    } finally {
        hideLoading();
    }
}

// Add event listener to the form
document.addEventListener('DOMContentLoaded', () => {
    const addUrlForm = document.getElementById('addUrlForm');
    if (addUrlForm) {
        addUrlForm.addEventListener('submit', handleAddUrl);
    }
});