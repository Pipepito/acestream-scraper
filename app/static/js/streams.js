/**
 * Streams page functionality for Acestream Scraper
 */

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

// Fetch application statistics
async function fetchStats() {
    try {
        const response = await fetch('/api/stats/');
        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching stats:', error);
        return null;
    }
}

// Update stats in the UI
function updateStats(stats) {
    // This can be an empty function since we're using updateStreamStats for our specific cards
    // The function is called in refreshData() so we need it to exist
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

// Load and display streams data
async function refreshData() {
    showLoading();
    try {
        const stats = await fetchStats();
        updateStats(stats);
        
        // Populate URL filter dropdown
        await populateUrlDropdown();
        
        // Update channel list
        const searchInput = document.getElementById('channelSearch');
        const searchTerm = searchInput ? searchInput.value.trim() : '';
        
        const urlFilter = document.getElementById('urlFilter');
        const urlId = urlFilter ? urlFilter.value : '';
        
        await refreshChannelList(searchTerm, urlId);
        
        // Update stream statistics
        updateStreamStats(stats);
    } catch (error) {
        console.error('Error loading streams data:', error);
        showAlert('danger', 'Failed to load streams data');
    } finally {
        hideLoading();
    }
}

// Update stream statistics cards
function updateStreamStats(stats) {
    // Total streams
    const totalStreamsCard = document.getElementById('totalStreamsCard');
    if (totalStreamsCard) {
        totalStreamsCard.textContent = stats.total_channels || '0';
    }
    
    // Online streams
    const onlineStreamsCard = document.getElementById('onlineStreamsCard');
    if (onlineStreamsCard) {
        onlineStreamsCard.textContent = stats.channels_online || '0';
    }
    
    // Streams with EPG data
    const withEpgStreamsCard = document.getElementById('withEpgStreamsCard');
    if (withEpgStreamsCard) {
        // We need to fetch this from a different endpoint since it's not in the stats
        fetch('/api/channels?with_epg=true&count_only=true')
            .then(response => response.json())
            .then(data => {
                withEpgStreamsCard.textContent = data.total || '0';
            })
            .catch(err => {
                console.error('Error fetching EPG stats:', err);
                withEpgStreamsCard.textContent = '?';
            });
    }
    
    // Streams assigned to TV channels
    const assignedStreamsCard = document.getElementById('assignedStreamsCard');
    if (assignedStreamsCard) {
        // We need to fetch this from TV channels stats
        fetch('/api/stats/tv-channels/')
            .then(response => response.json())
            .then(data => {
                assignedStreamsCard.textContent = data.acestreams || '0';
            })
            .catch(err => {
                console.error('Error fetching TV channel stats:', err);
                assignedStreamsCard.textContent = '?';
            });
    }
    
    // Update channel count badge
    const channelCount = document.getElementById('channelCount');
    if (channelCount) {
        channelCount.textContent = stats.total_channels || '0';
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
        
        // Update the channel list - make sure to use our own update function
        updateChannelList(channels);
        
        return channels;
    } catch (error) {
        console.error('Error refreshing channel list:', error);
        return [];
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
    
    if (!channels || channels.length === 0) {
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
            </td>            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-success" onclick="showPlayerOptions('${channel.id}')" title="Play stream">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-play-fill" viewBox="0 0 16 16">
                            <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/>
                        </svg>
                    </button>
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
    const channelCount = document.getElementById('channelCount');
    if (channelCount) {
        channelCount.textContent = channels.length;
    }
}

// Format date for display (helper function needed for updateChannelList)
function formatLocalDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Search channels function
async function searchChannels(searchTerm) {
    try {
        showLoading();
        
        // Get current URL filter
        const urlFilter = document.getElementById('urlFilter');
        const urlId = urlFilter ? urlFilter.value : '';
        
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
        
        // Update the channel list UI
        updateChannelList(channels);
        
    } catch (error) {
        console.error('Error searching channels:', error);
    } finally {
        hideLoading();
    }
}

// Filter channels by URL
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
            params.append('url_id', urlId);
        }
        
        // Fetch filtered channels
        const queryString = params.toString() ? `?${params.toString()}` : '';
        const response = await fetch(`/api/channels${queryString}`);
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        const channels = await response.json();
        
        // Update channel list UI
        updateChannelList(channels);
    } catch (error) {
        console.error('Error filtering channels:', error);
        showAlert('danger', 'Failed to filter channels');
    } finally {
        hideLoading();
    }
}

// Initialize the page when loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Streams page initializing...');
    
    // Initialize data
    refreshData();
    
    // Set up form submit handler if present
    const addChannelForm = document.getElementById('addChannelForm');
    if (addChannelForm) {
        addChannelForm.addEventListener('submit', handleAddChannel);
    }
    
    // Set up filter change handler
    const urlFilter = document.getElementById('urlFilter');
    if (urlFilter) {
        urlFilter.addEventListener('change', function() {
            filterByUrl(this.value);
        });
    }
    
    // Refresh periodically
    setInterval(refreshData, 60000); // Every minute
});
