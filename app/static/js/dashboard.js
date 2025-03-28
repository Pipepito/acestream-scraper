/**
 * Dashboard functionality for Acestream Scraper
 */

// Load and display dashboard data
async function refreshData() {
    showLoading();
    try {
        const stats = await fetchStats();
        updateStats(stats);
        
        // Populate URLs list
        const urlsList = document.getElementById('urlsList');
        if (urlsList) {
            renderUrlsList(urlsList, stats);
        }
        
        // Populate URL filter dropdown
        await populateUrlDropdown(stats);
        
        // Update channel list if exists
        if (typeof refreshChannelList === 'function') {
            // Get current URL filter if any
            const urlFilter = document.getElementById('urlFilter');
            const urlId = urlFilter ? urlFilter.value : '';
            
            // Get current search term if any
            const searchInput = document.getElementById('channelSearch');
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            
            await refreshChannelList(searchTerm, urlId);
        }
        
        // Update status info
        updateStatusInfo(stats);

        // Check services status if enabled
        await checkServicesStatus();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showAlert('danger', 'Failed to load dashboard data');
    } finally {
        hideLoading();
    }
}

// Populate URL dropdown with available sources
async function populateUrlDropdown(stats) {
    try {
        const urlDropdown = document.getElementById('urlFilter');
        
        if (!urlDropdown || !stats || !stats.urls) return;
        
        // Save current selection
        const currentSelection = urlDropdown.value;
        
        // Clear existing options except the first one (All Sources)
        while (urlDropdown.options.length > 1) {
            urlDropdown.remove(1);
        }
        
        // Sort URLs by channel count (descending) and then by URL
        const sortedUrls = [...stats.urls].sort((a, b) => {
            if (b.channel_count !== a.channel_count) {
                return b.channel_count - a.channel_count;
            }
            return a.url.localeCompare(b.url);
        });
        
        // Add options for each URL
        sortedUrls.forEach(url => {
            if (url.channel_count > 0) {
                const option = document.createElement('option');
                option.value = url.id;
                
                // Truncate the URL if it's too long
                let displayUrl = url.url;
                if (displayUrl.length > 40) {
                    displayUrl = displayUrl.substring(0, 37) + '...';
                }
                
                option.text = `${displayUrl} (${url.channel_count})`;
                option.title = url.url; // Show full URL on hover
                urlDropdown.appendChild(option);
            }
        });
        
        // Restore selection if it still exists
        if (currentSelection) {
            // Check if the option still exists
            const exists = Array.from(urlDropdown.options).some(option => option.value === currentSelection);
            if (exists) {
                urlDropdown.value = currentSelection;
            }
        }
    } catch (error) {
        console.error('Error populating URL dropdown:', error);
    }
}

// Render the URLs list with ID and type information
function renderUrlsList(urlsList, stats) {
    if (!stats || !stats.urls || stats.urls.length === 0) {
        urlsList.innerHTML = `
            <div class="list-group-item text-center">
                <span class="text-muted">No URLs found. Add a URL to start scraping for channels.</span>
            </div>
        `;
        return;
    }
    
    const urlItems = stats.urls.map(url => `
        <div class="list-group-item">
            <div class="row align-items-center">
                <div class="col-md-7">
                    <div>
                        <strong>${url.url}</strong>
                        <span class="badge bg-info ms-2">${url.url_type || 'regular'}</span>
                    </div>
                    <div class="small text-muted">
                        <span class="status-badge">Status: <span class="badge ${getStatusBadgeClass(url.status)}">${url.status}</span></span>
                        <span class="ms-2">Channels: ${url.channel_count}</span>
                        ${url.last_processed ? `<span class="ms-2">Last scraped: ${formatLocalDate(url.last_processed)}</span>` : ''}
                    </div>
                </div>
                <div class="col-md-5 text-end">
                    <button class="btn btn-sm ${url.enabled ? 'btn-warning' : 'btn-success'}" 
                            onclick="toggleUrl('${url.id}', ${!url.enabled})">
                        ${url.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button class="btn btn-sm btn-info" 
                            onclick="refreshUrl('${url.id}')">
                        Refresh
                    </button>
                    <button class="btn btn-sm btn-danger" 
                            onclick="deleteUrl('${url.id}')">
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    urlsList.innerHTML = urlItems;
}

// Get appropriate badge class for status
function getStatusBadgeClass(status) {
    switch(status.toLowerCase()) {
        case 'pending': return 'bg-warning';
        case 'processing': return 'bg-primary';
        case 'success': case 'ok': return 'bg-success';
        case 'failed': case 'error': return 'bg-danger';
        case 'disabled': return 'bg-secondary';
        default: return 'bg-info';
    }
}

// Update status information
function updateStatusInfo(stats) {
    // Update base URL display
    const baseUrlDisplay = document.getElementById('currentBaseUrlDisplay');
    if (baseUrlDisplay) {
        baseUrlDisplay.textContent = `Base URL: ${stats.base_url || 'Not configured'}`;
    }
    
    // Update PID parameter display
    const pidParamDisplay = document.getElementById('pidParameterDisplay');
    if (pidParamDisplay) {
        pidParamDisplay.textContent = `Add PID Parameter: ${stats.addpid ? 'Yes' : 'No'}`;
    }
    
    // Update sample URL display
    const sampleUrlDisplay = document.getElementById('sampleUrlDisplay');
    if (sampleUrlDisplay) {
        const sampleId = '1a2b3c4d5e6f7g8h9i0j';
        let sampleUrl = (stats.base_url || 'acestream://') + sampleId;
        if (stats.addpid) {
            sampleUrl += '&pid=player_id';
        }
        sampleUrlDisplay.textContent = `Example: ${sampleUrl}`;
    }
    
    // Update Ace Engine URL display
    const aceEngineUrlDisplay = document.getElementById('currentAceEngineUrlDisplay');
    if (aceEngineUrlDisplay) {
        aceEngineUrlDisplay.textContent = `Ace Engine URL: ${stats.ace_engine_url || 'Not configured'}`;
    }
    
    // Update rescrape interval info
    const rescrapeInfo = document.getElementById('rescrapeInfoContainer');
    if (rescrapeInfo) {
        rescrapeInfo.innerHTML = `
            <h6 class="card-subtitle mb-2">Rescrape Interval</h6>
            <p class="mb-1 text-muted small">URLs are automatically refreshed every ${stats.rescrape_interval || 'N/A'} hours</p>
        `;
    }
}

// Format date for display
function formatLocalDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Add URL form submission handler
async function handleAddUrl(e) {
    e.preventDefault();
    const urlInput = document.getElementById('urlInput');
    const urlTypeSelect = document.getElementById('urlTypeSelect');
    const url = urlInput.value.trim();
    const urlType = urlTypeSelect.value;
    
    if (!url) {
        showAlert('warning', 'Please enter a URL');
        return;
    }
    
    try {
        showLoading();
        const success = await addUrl(url, urlType);
        if (success) {
            urlInput.value = '';
            await refreshData();
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('error', 'Network error while adding URL');
    } finally {
        hideLoading();
    }
}

// Download playlist function
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

// Initialize the page when loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize data
    refreshData();
    
    // Add event listeners
    const addUrlForm = document.getElementById('addUrlForm');
    if (addUrlForm) {
        addUrlForm.addEventListener('submit', handleAddUrl);
    }
    
    // Set up filter change handler
    const urlFilter = document.getElementById('urlFilter');
    if (urlFilter) {
        urlFilter.addEventListener('change', function() {
            const searchInput = document.getElementById('channelSearch');
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            refreshChannelList(searchTerm, this.value);
        });
    }
    
    // Refresh periodically
    setInterval(refreshData, 60000); // Every minute
});

// Check services status based on user preferences
async function checkServicesStatus() {
    // Check Acexy status if enabled
    const enableAcexyCheck = document.getElementById('enableAcexyCheck');
    if (enableAcexyCheck) {
        // Set checkbox state from localStorage
        const acexyCheckEnabled = localStorage.getItem('enableAcexyCheck') !== 'false';
        enableAcexyCheck.checked = acexyCheckEnabled;
        
        // Add event listener to save preference
        enableAcexyCheck.addEventListener('change', function() {
            localStorage.setItem('enableAcexyCheck', this.checked);
            if (this.checked) {
                // If re-enabled, immediately check status
                checkAcexyStatus();
            } else {
                // If disabled, update UI to reflect disabled state
                const acexyStatus = document.getElementById('acexyStatus');
                if (acexyStatus) {
                    acexyStatus.className = 'badge bg-secondary';
                    acexyStatus.textContent = 'Check disabled';
                }
                // Hide acexy streams info
                const acexyStreams = document.getElementById('acexyStreams');
                if (acexyStreams) {
                    acexyStreams.classList.add('d-none');
                }
            }
        });
        
        // Check status if enabled
        if (acexyCheckEnabled) {
            checkAcexyStatus();
        } else {
            const acexyStatus = document.getElementById('acexyStatus');
            if (acexyStatus) {
                acexyStatus.className = 'badge bg-secondary';
                acexyStatus.textContent = 'Check disabled';
            }
        }
    }
    
    // Check Acestream Engine status if enabled
    const enableAcestreamCheck = document.getElementById('enableAcestreamCheck');
    if (enableAcestreamCheck) {
        // Set checkbox state from localStorage
        const acestreamCheckEnabled = localStorage.getItem('enableAcestreamCheck') !== 'false';
        enableAcestreamCheck.checked = acestreamCheckEnabled;
        
        // Add event listener to save preference
        enableAcestreamCheck.addEventListener('change', function() {
            localStorage.setItem('enableAcestreamCheck', this.checked);
            if (this.checked) {
                // If re-enabled, immediately check status
                checkAcestreamStatus();
            } else {
                // If disabled, update UI to reflect disabled state
                const acestreamStatus = document.getElementById('acestreamStatus');
                if (acestreamStatus) {
                    acestreamStatus.className = 'badge bg-secondary';
                    acestreamStatus.textContent = 'Check disabled';
                }
                // Hide details
                const acestreamDetails = document.getElementById('acestreamDetails');
                if (acestreamDetails) {
                    acestreamDetails.classList.add('d-none');
                }
            }
        });
        
        // Check status if enabled
        if (acestreamCheckEnabled) {
            checkAcestreamStatus();
        } else {
            const acestreamStatus = document.getElementById('acestreamStatus');
            if (acestreamStatus) {
                acestreamStatus.className = 'badge bg-secondary';
                acestreamStatus.textContent = 'Check disabled';
            }
        }
    }
}