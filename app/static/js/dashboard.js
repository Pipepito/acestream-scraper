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
        
        // Populate URL filter dropdown - use the dedicated endpoint
        await populateUrlDropdown();
        
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

// Populate URL dropdown with channel sources from the dedicated endpoint
async function populateUrlDropdown() {
    try {
        // Fetch channel sources from API using the dedicated endpoint
        const response = await fetch('/api/channels/sources');
        const sources = await response.json();
        
        const urlDropdown = document.getElementById('urlFilter');
        
        if (!urlDropdown || !sources) return;
        
        // Clear existing options except the first one (All Sources)
        while (urlDropdown.options.length > 1) {
            urlDropdown.remove(1);
        }
        
        // Sort sources by channel count (descending) and then by URL
        const sortedSources = [...sources].sort((a, b) => {
            if (b.channel_count !== a.channel_count) {
                return b.channel_count - a.channel_count;
            }
            return a.url.localeCompare(b.url);
        });
        
        // Add options for each source
        sortedSources.forEach(source => {
            if (source.channel_count > 0) {
                const option = document.createElement('option');
                // Use url_id as the value - this is what the API expects for filtering
                option.value = source.url_id || '';
                
                // Truncate the URL if it's too long
                let displayUrl = source.url;
                if (displayUrl.length > 40) {
                    displayUrl = displayUrl.substring(0, 37) + '...';
                }
                
                option.text = `${displayUrl} (${source.channel_count})`;
                option.title = source.url; // Show full URL on hover
                urlDropdown.appendChild(option);
            }
        });
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
    console.log('Dashboard initializing...');
    
    // Initialize data
    refreshData();
    
    // Debug form existence
    const addChannelForm = document.getElementById('addChannelForm');
    if (addChannelForm) {
        console.log('Found add channel form in dashboard');
    } else {
        console.warn('Add channel form not found in dashboard');
    }
    
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
            const urlId = this.value;
            
            // Use the selected URL ID to filter channels
            filterByUrl(urlId);
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

// Filter channels by URL - updated to use url_id
async function filterByUrl(urlId) {
    try {
        showLoading();
        
        // Get current search term
        const searchInput = document.getElementById('channelSearch');
        const searchTerm = searchInput ? searchInput.value.trim() : '';
        
        // Build query parameters
        const params = new URLSearchParams();
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        if (urlId) {
            // Use url_id parameter which is what the API expects
            params.append('url_id', urlId);
        }
        
        console.log('Filtering channels with params:', params.toString());
        
        // Fetch filtered channels
        const queryString = params.toString() ? `?${params.toString()}` : '';
        const response = await fetch(`/api/channels${queryString}`);
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        const channels = await response.json();
        console.log(`Received ${channels.length} channels from API`);
        
        // Update channel list UI
        updateChannelList(channels);
    } catch (error) {
        console.error('Error filtering channels:', error);
        showAlert('danger', 'Failed to filter channels');
    } finally {
        hideLoading();
    }
}

// Update the channel list with received data
function updateChannelList(channels) {
    const channelsList = document.getElementById('channelListContent');
    if (!channelsList) {
        console.error('Channel list element not found. Looking for #channelListContent');
        return;
    }
    
    if (channels.length === 0) {
        channelsList.innerHTML = '<tr><td colspan="4" class="text-center">No channels found matching your filter criteria</td></tr>';
        return;
    }
    
    channelsList.innerHTML = channels.map(channel => {
        // Determine metadata styling based on EPG data completeness
        let metadataClass = 'primary'; // Default blue (no metadata)
        let tooltipText = 'Edit channel - No EPG data'; // Default tooltip
        
        // If locked, purple has priority
        if (channel.epg_update_protected) {
            metadataClass = 'purple';
            tooltipText = 'Edit channel - EPG locked (protected from automatic updates)';
        }
        // Otherwise evaluate metadata state
        else if (channel.tvg_id && channel.tvg_name && channel.logo) {
            metadataClass = 'success';  // Green - complete
            tooltipText = 'Edit channel - Complete EPG data';
        } 
        else if (channel.tvg_id || channel.tvg_name || channel.logo) {
            metadataClass = 'warning';  // Amber - partial
            tooltipText = 'Edit channel - Partial EPG data';
        }
        
        // Logo display
        const logoHtml = channel.logo ? 
            `<img src="${channel.logo}" alt="Logo" class="channel-logo me-2" style="max-height:60px; max-width:60px;">` : 
            '';
            
        return `
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    ${logoHtml}
                    ${channel.name}
                </div>
            </td>
            <td><code>${channel.id}</code></td>
            <td>
                ${formatLocalDate(channel.last_processed)}
                ${channel.last_checked ? `
                    <br>
                    <small class="text-muted">
                        Status: <span class="badge ${channel.is_online ? 'bg-success' : 'bg-danger'}">
                            ${channel.is_online ? 'Online' : 'Offline'}
                        </span>
                        ${channel.check_error ? `<br>Error: ${channel.check_error}` : ''}
                    </small>
                ` : ''}
            </td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-info" onclick="checkChannelStatus('${channel.id}')" title="Check status">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-shield-check" viewBox="0 0 16 16">
                            <path d="M5.338 1.59a61.44 61.44 0 0 0-2.837.856.481.481 0 0 0-.328.39c-.554 4.157.726 7.19 2.253 9.188a10.725 10.725 0 0 0 2.287 2.233c.346.244.652.42.893.533.12.057.218.095.293.118a.55.55 0 0 0 .101.025.615.615 0 0 0 .1-.025c.076-.023.174-.061.294-.118.24-.113.547-.29.893-.533a10.726 10.726 0 0 0 2.287-2.233c1.527-1.997 2.807-5.031 2.253-9.188a.48.48 0 0 0-.328-.39c-.651-.213-1.75-.56-2.837-.855C9.552 1.29 8.531 1.067 8 1.067c-.53 0-1.552.223-2.662.524zM5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887.87a1.54 1.54 0 0 1 1.044 1.262c.596 4.477-.787 7.795-2.465 9.99a11.775 11.775 0 0 1-2.517 2.453a7.159 7.159 0 0 1-1.048.625c-.28.132-.581.24-.829.24s-.548-.108-.829-.24a7.158 7.158 0 0 1-1.048-.625 11.777 11.777 0 0 1-2.517-2.453C1.928 10.487.545 7.169 1.141 2.692A1.54 1.54 0 0 1 2.185 1.43 62.456 62.456 0 0 1 5.072.56z"/>
                            <path d="M10.854 5.146a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1 .708-.708L7.5 7.793l2.646-2.647a.5.5 0 0 1 .708 0z"/>
                        </svg>
                    </button>
                    <button class="btn btn-sm btn-${metadataClass}" onclick="editChannel('${channel.id}')" title="${tooltipText}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
                            <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                            <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
                        </svg>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteChannel('${channel.id}')" title="Delete channel">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5Zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5Zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6Z"/>
                            <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1ZM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118ZM2.5 3h11V2h-11v1Z"/>
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `}).join('');
    
    // Update displayed channels count in stats
    const displayedChannels = document.getElementById('displayedChannels');
    if (displayedChannels) {
        displayedChannels.textContent = channels.length;
    }
}

// Function to combine all update functions
async function refreshChannelList(searchTerm, urlId) {
    try {
        showLoading();
        
        // Build query parameters
        const params = new URLSearchParams();
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        if (urlId) {
            params.append('url_id', urlId);
        }
        
        // Fetch filtered channels
        const queryString = params.toString() ? `?${params.toString()}` : '';
        const response = await fetch(`/api/channels${queryString}`);
        const channels = await response.json();
        
        // Update the channel list - make sure to use the main update function
        updateChannelList(channels);
    } catch (error) {
        console.error('Error refreshing channel list:', error);
    } finally {
        hideLoading();
    }
}

// Make sure updateChannelListUI calls our main function
function updateChannelListUI(channels) {
    updateChannelList(channels);
}