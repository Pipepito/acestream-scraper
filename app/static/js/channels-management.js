/**
 * Channels management functionality for Acestream Scraper
 */

// State management for channels page
const channelsState = {
    currentPage: 1,
    channelsPerPage: 25,
    totalPages: 1,
    searchTerm: '',
    statusFilter: 'all',
    channels: [],
    isLoading: false
};

// Debounced search function to limit API calls
const debouncedSearch = debounce(() => {
    channelsState.currentPage = 1;
    loadChannelsData();
}, 500);

// Load channels data with pagination, filtering and searching
async function loadChannelsData() {
    if (channelsState.isLoading) return;
    
    channelsState.isLoading = true;
    showLoading();
    
    try {
        // Get filters and pagination values
        channelsState.searchTerm = document.getElementById('channelSearchInput').value.trim();
        channelsState.statusFilter = document.getElementById('statusFilter').value;
        channelsState.channelsPerPage = parseInt(document.getElementById('channelsPerPage').value);
        
        // Build query parameters
        const params = new URLSearchParams({
            page: channelsState.currentPage,
            per_page: channelsState.channelsPerPage,
            status: channelsState.statusFilter !== 'all' ? channelsState.statusFilter : '',
            search: channelsState.searchTerm
        });
        
        // Fetch channels data from API
        const response = await fetch(`/api/channels?${params.toString()}`);
        const data = await response.json();
        
        if (response.ok) {
            // Update state
            channelsState.channels = data.channels || [];
            channelsState.totalPages = data.total_pages || 1;
            
            // Update channels table
            updateChannelsTable();
            
            // Update pagination
            updatePagination();
            
            // Update statistics
            updateStatsFromData(data);
        } else {
            showAlert('error', data.message || data.error || 'Failed to load channels');
        }
    } catch (error) {
        console.error('Error loading channels data:', error);
        showAlert('error', 'Network error while loading channels');
    } finally {
        hideLoading();
        channelsState.isLoading = false;
    }
}

// Update channel statistics cards
function updateStatsFromData(data) {
    if (data.stats) {
        document.getElementById('totalChannelsCard').textContent = data.stats.total_channels || 0;
        document.getElementById('channelsCheckedCard').textContent = data.stats.channels_checked || 0;
        document.getElementById('channelsOnlineCard').textContent = data.stats.channels_online || 0;
        document.getElementById('channelsOfflineCard').textContent = data.stats.channels_offline || 0;
    }
}

// Update the channels table with current data
function updateChannelsTable() {
    const tableBody = document.getElementById('channelsTableBody');
    
    if (channelsState.channels.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No channels found matching your criteria</td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = channelsState.channels.map(channel => `
        <tr>
            <td>${channel.name || 'Unknown'}</td>
            <td><code>${channel.id}</code></td>
            <td>${channel.group || 'None'}</td>
            <td>
                <span class="badge bg-${getStatusBadgeClass(channel.status)}">
                    ${channel.status || 'Unknown'}
                </span>
            </td>
            <td>${channel.last_checked ? formatLocalDate(channel.last_checked) : 'Never'}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-primary" onclick="checkChannelStatus('${channel.id}')" title="Check status">
                        <i class="bi bi-check-circle"></i>
                    </button>
                    <button class="btn btn-danger" onclick="deleteChannel('${channel.id}')" title="Delete channel">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Get appropriate badge class for channel status
function getStatusBadgeClass(status) {
    if (!status) return 'secondary';
    
    switch(status.toLowerCase()) {
        case 'online':
            return 'success';
        case 'offline':
            return 'danger';
        default:
            return 'secondary';
    }
}

// Update pagination controls
function updatePagination() {
    const pagination = document.getElementById('channelsPagination');
    
    let paginationHTML = '';
    
    // Previous button
    paginationHTML += `
        <li class="page-item ${channelsState.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="handlePageChange(${channelsState.currentPage - 1}); return false;">
                Previous
            </a>
        </li>
    `;
    
    // Page numbers
    const startPage = Math.max(1, channelsState.currentPage - 2);
    const endPage = Math.min(channelsState.totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === channelsState.currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="handlePageChange(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    // Next button
    paginationHTML += `
        <li class="page-item ${channelsState.currentPage === channelsState.totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="handlePageChange(${channelsState.currentPage + 1}); return false;">
                Next
            </a>
        </li>
    `;
    
    pagination.innerHTML = paginationHTML;
}

// Handle page change
function handlePageChange(page) {
    if (page < 1 || page > channelsState.totalPages || page === channelsState.currentPage) {
        return;
    }
    
    channelsState.currentPage = page;
    loadChannelsData();
}

// Handle filter change
function handleFilterChange() {
    channelsState.currentPage = 1;
    loadChannelsData();
}

// Check status for a single channel
async function checkChannelStatus(channelId) {
    try {
        showLoading();
        const response = await fetch(`/api/channels/${channelId}/check-status`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('success', `Status check completed: ${data.status}`);
            loadChannelsData();
        } else {
            showAlert('error', data.message || data.error || 'Error checking channel status');
        }
    } catch (error) {
        console.error('Error checking channel status:', error);
        showAlert('error', 'Network error while checking channel status');
    } finally {
        hideLoading();
    }
}

// Check status for all channels
async function checkAllChannelsStatus() {
    if (!confirm('Check status of all channels? This might take a while.')) {
        return;
    }
    
    try {
        showLoading();
        const response = await fetch('/api/channels/check-status', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('info', `Status check started for ${data.total_channels} channels. Results will update automatically.`);
            // Start periodic refresh of channel list
            startAutoRefresh();
        } else {
            showAlert('error', data.message || data.error || 'Error starting status check');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('error', 'Network error while initiating status check');
    } finally {
        hideLoading();
    }
}

// Auto-refresh functionality
let refreshInterval = null;

function startAutoRefresh() {
    // Stop any existing refresh
    stopAutoRefresh();
    
    // Refresh every 10 seconds for 2 minutes
    let refreshCount = 0;
    const maxRefreshes = 12;  // 2 minutes total
    
    refreshInterval = setInterval(async () => {
        await loadChannelsData();
        refreshCount++;
        
        if (refreshCount >= maxRefreshes) {
            stopAutoRefresh();
        }
    }, 10000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Remove offline channels
async function removeOfflineChannels() {
    if (!confirm('Are you sure you want to remove all offline channels? This action cannot be undone.')) {
        return;
    }
    
    try {
        showLoading();
        const response = await fetch('/api/channels/remove-offline', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('success', `Removed ${data.removed_count} offline channels`);
            loadChannelsData();
        } else {
            showAlert('error', data.message || data.error || 'Error removing offline channels');
        }
    } catch (error) {
        console.error('Error removing offline channels:', error);
        showAlert('error', 'Network error while removing offline channels');
    } finally {
        hideLoading();
    }
}

// Delete a specific channel
async function deleteChannel(channelId) {
    if (!confirm('Are you sure you want to delete this channel?')) {
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/channels/${channelId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('success', 'Channel deleted successfully');
            loadChannelsData();
        } else {
            const data = await response.json();
            showAlert('error', data.message || data.error || 'Error deleting channel');
        }
    } catch (error) {
        console.error('Error deleting channel:', error);
        showAlert('error', 'Network error while deleting channel');
    } finally {
        hideLoading();
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadChannelsData();
    
    // Set up event listeners
    document.getElementById('channelSearchInput').addEventListener('input', debouncedSearch);
    document.getElementById('statusFilter').addEventListener('change', handleFilterChange);
    document.getElementById('channelsPerPage').addEventListener('change', handleFilterChange);
    document.getElementById('checkAllChannelsBtn').addEventListener('click', checkAllChannelsStatus);
    document.getElementById('removeOfflineChannelsBtn').addEventListener('click', removeOfflineChannels);
    
    // Refresh data periodically
    setInterval(loadChannelsData, 60000); // Every minute
});
