/**
 * TV Channel Detail Page JavaScript
 * Handles the display and interactions for a single TV channel's detail page
 */

// State for the TV channel detail page
const channelState = {
    channelId: null,
    channelData: null,
    acestreams: [],
    isLoading: false
};

// Define debounce function at the top of the file so it's available globally
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const later = () => {
            timeout = null;
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Initialize the page
 */
function initializeDetailPage() {
    // Extract channel ID from URL
    const pathParts = window.location.pathname.split('/');
    channelState.channelId = pathParts[pathParts.length - 1];
    
    if (!channelState.channelId) {
        showAlert('error', 'Invalid TV channel ID');
        return;
    }
    
    // Load channel data
    loadChannelData();
    
    // Set up event listeners
    document.getElementById('editChannelBtn').addEventListener('click', editChannel);
    document.getElementById('deleteChannelBtn').addEventListener('click', deleteChannel);
    document.getElementById('assignAcestreamsBtn').addEventListener('click', showAssignModal);
    document.getElementById('findAcestreamsBtn')?.addEventListener('click', showAssignModal);
    document.getElementById('syncEpgBtn').addEventListener('click', syncEpgData);
    document.getElementById('updateTVChannelBtn').addEventListener('click', updateChannel);
    document.getElementById('previewLogoBtn').addEventListener('click', previewLogo);
}

/**
 * Load the TV channel data
 */
async function loadChannelData() {
    if (channelState.isLoading) return;
    
    channelState.isLoading = true;
    showLoading();
    
    try {
        const response = await fetch(`/api/tv-channels/${channelState.channelId}`);
        
        // Check response status explicitly
        if (response.status === 404) {
            throw new Error('TV channel not found. It may have been deleted.');
        } else if (!response.ok) {
            throw new Error(`Failed to load TV channel data: ${response.statusText}`);
        }
        
        channelState.channelData = await response.json();
        channelState.acestreams = channelState.channelData.acestream_channels || [];
        
        // Update UI with channel data
        updateChannelUI();
        updateAcestreamsTable();
        
    } catch (error) {
        console.error('Error loading channel data:', error);
        showAlert('error', error.message || 'Failed to load channel data');
        
        // If channel not found, redirect back to listing after a delay
        if (error.message && error.message.includes('not found')) {
            setTimeout(() => {
                window.location.href = '/tv-channels';
            }, 3000);
        }
    } finally {
        hideLoading();
        channelState.isLoading = false;
    }
}

/**
 * Update the UI with channel data
 */
function updateChannelUI() {
    const channel = channelState.channelData;
    if (!channel) return;
    
    // Update breadcrumb
    document.getElementById('channelBreadcrumb').textContent = channel.name;
    
    // Update header
    document.getElementById('channelName').textContent = channel.name;
    
    // Update logo
    const logoContainer = document.getElementById('channelLogoContainer');
    if (channel.logo_url) {
        logoContainer.innerHTML = `<img src="${channel.logo_url}" alt="${channel.name} logo" class="img-fluid rounded" style="max-height: 150px;">`;
    } else {
        logoContainer.innerHTML = `
            <div class="placeholder-logo bg-light rounded d-flex align-items-center justify-content-center" style="width: 150px; height: 150px;">
                <i class="bi bi-tv fs-1 text-muted"></i>
            </div>
        `;
    }
    
    // Update metadata badges
    document.getElementById('channelCategory').textContent = channel.category || 'No category';
    document.getElementById('channelCountry').textContent = channel.country || 'Unknown country';
    document.getElementById('channelLanguage').textContent = channel.language || 'Unknown language';
    
    // Update description
    document.getElementById('channelDescription').textContent = channel.description || 'No description available.';
    
    // Update EPG tab
    document.getElementById('epgIdDisplay').value = channel.epg_id || '';
    document.getElementById('epgSourceDisplay').value = channel.epg_source_id ? `Source #${channel.epg_source_id}` : 'None';
    
    // Update details tab
    document.getElementById('detailChannelId').textContent = channel.id;
    document.getElementById('detailCreatedAt').textContent = formatDate(channel.created_at);
    document.getElementById('detailUpdatedAt').textContent = formatDate(channel.updated_at);
    document.getElementById('detailStatus').innerHTML = channel.is_active ? 
        '<span class="badge bg-success">Active</span>' : 
        '<span class="badge bg-danger">Inactive</span>';
    
    // Update website link
    if (channel.website) {
        document.getElementById('detailWebsite').innerHTML = `<a href="${channel.website}" target="_blank">${channel.website}</a>`;
    } else {
        document.getElementById('detailWebsite').textContent = 'Not specified';
    }
    
    // Update stream information
    document.getElementById('detailTotalStreams').textContent = channelState.acestreams.length;
    document.getElementById('detailOnlineStreams').textContent = channelState.acestreams.filter(stream => stream.is_online).length;
    
    // Update best stream info
    const bestStream = channelState.acestreams.find(stream => stream.is_online);
    if (bestStream) {
        document.getElementById('detailBestStream').innerHTML = `
            <a href="acestream://${bestStream.id}" class="text-decoration-none">
                <span class="badge bg-success">Online</span> ${bestStream.id.substring(0, 8)}...
            </a>
        `;
    } else if (channelState.acestreams.length > 0) {
        document.getElementById('detailBestStream').innerHTML = `
            <a href="acestream://${channelState.acestreams[0].id}" class="text-decoration-none">
                <span class="badge bg-danger">Offline</span> ${channelState.acestreams[0].id.substring(0, 8)}...
            </a>
        `;
    } else {
        document.getElementById('detailBestStream').textContent = 'No streams available';
    }
}

/**
 * Update the acestreams table
 */
function updateAcestreamsTable() {
    const tableBody = document.getElementById('acestreamsTableBody');
    if (!tableBody) return;
    
    if (channelState.acestreams.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">No acestream channels associated with this TV channel.</td>
            </tr>
        `;
        
        // Show the "no acestreams" message
        document.getElementById('noAcestreamsMessage').style.display = 'block';
        return;
    }
    
    // Hide the "no acestreams" message
    document.getElementById('noAcestreamsMessage').style.display = 'none';
    
    // Update the table
    tableBody.innerHTML = channelState.acestreams.map(stream => {
        const statusClass = stream.is_online ? 'bg-success' : 'bg-danger';
        const statusText = stream.is_online ? 'Online' : 'Offline';
        
        return `
            <tr>
                <td>${stream.name || 'Unnamed channel'}</td>
                <td>
                    <a href="acestream://${stream.id}" class="text-decoration-none" title="Open in Acestream player">
                        ${stream.id}
                    </a>
                </td>
                <td>
                    <span class="badge ${statusClass}">${statusText}</span>
                    <small class="d-block text-muted">Last checked: ${formatLocalDate(stream.last_checked)}</small>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-info" onclick="checkAcestreamStatus('${stream.id}')" title="Check status">
                            <i class="bi bi-shield-check"></i>
                        </button>
                        <button class="btn btn-danger" onclick="removeAcestream('${stream.id}')" title="Remove association">
                            <i class="bi bi-unlink"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Show the edit channel modal
 */
function editChannel() {
    const channel = channelState.channelData;
    if (!channel) return;
    
    // Populate form fields
    document.getElementById('editTVChannelId').value = channel.id;
    document.getElementById('editTVChannelName').value = channel.name || '';
    document.getElementById('editTVChannelDescription').value = channel.description || '';
    document.getElementById('editTVChannelCategory').value = channel.category || '';
    document.getElementById('editTVChannelCountry').value = channel.country || '';
    document.getElementById('editTVChannelLanguage').value = channel.language || '';
    document.getElementById('editTVChannelLogo').value = channel.logo_url || '';
    document.getElementById('editTVChannelWebsite').value = channel.website || '';
    document.getElementById('editTVChannelEpgId').value = channel.epg_id || '';
    document.getElementById('editTVChannelEpgSourceId').value = channel.epg_source_id || '';
    document.getElementById('editTVChannelIsActive').checked = Boolean(channel.is_active);
    
    // Clear logo preview
    const logoPreview = document.getElementById('logoPreview');
    if (logoPreview) {
        logoPreview.style.display = 'none';
        logoPreview.querySelector('img').src = '';
    }
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('editTVChannelModal'));
    modal.show();
}

/**
 * Update the channel
 */
async function updateChannel() {
    const channelId = document.getElementById('editTVChannelId').value;
    const channelName = document.getElementById('editTVChannelName').value.trim();
    const channelDescription = document.getElementById('editTVChannelDescription').value.trim();
    const channelCategory = document.getElementById('editTVChannelCategory').value.trim();
    const channelCountry = document.getElementById('editTVChannelCountry').value.trim();
    const channelLanguage = document.getElementById('editTVChannelLanguage').value.trim();
    const channelLogo = document.getElementById('editTVChannelLogo').value.trim();
    const channelWebsite = document.getElementById('editTVChannelWebsite').value.trim();
    const channelEpgId = document.getElementById('editTVChannelEpgId').value.trim();
    const channelEpgSourceId = document.getElementById('editTVChannelEpgSourceId').value;
    const channelIsActive = document.getElementById('editTVChannelIsActive').checked;
    
    if (!channelName) {
        showAlert('warning', 'Channel name is required');
        return;
    }
    
    try {
        showLoading();
        
        const channelData = {
            name: channelName,
            is_active: channelIsActive
        };
        
        // Add optional fields if they have values
        if (channelDescription) channelData.description = channelDescription;
        if (channelCategory) channelData.category = channelCategory;
        if (channelCountry) channelData.country = channelCountry;
        if (channelLanguage) channelData.language = channelLanguage;
        if (channelLogo) channelData.logo_url = channelLogo;
        if (channelWebsite) channelData.website = channelWebsite;
        if (channelEpgId) channelData.epg_id = channelEpgId;
        if (channelEpgSourceId) channelData.epg_source_id = parseInt(channelEpgSourceId);
        
        const response = await fetch(`/api/tv-channels/${channelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(channelData)
        });
        
        if (response.ok) {
            showAlert('success', 'TV channel updated successfully');
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editTVChannelModal'));
            modal.hide();
            
            // Reload channel data
            loadChannelData();
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update TV channel');
        }
    } catch (error) {
        console.error('Error updating TV channel:', error);
        showAlert('error', error.message || 'Error updating TV channel');
    } finally {
        hideLoading();
    }
}

/**
 * Delete the channel
 */
async function deleteChannel() {
    if (!confirm('Are you sure you want to delete this TV channel? This will remove all associations with acestream channels but will not delete the acestreams.')) {
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/tv-channels/${channelState.channelId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('success', 'TV channel deleted successfully');
            // Redirect to TV channels list page
            window.location.href = '/tv-channels';
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Failed to delete TV channel');
        }
    } catch (error) {
        console.error('Error deleting TV channel:', error);
        showAlert('error', error.message || 'Error deleting TV channel');
    } finally {
        hideLoading();
    }
}

/**
 * Update the list of assigned acestreams in the modal
 */
function updateAssignedAcestreams() {
    const container = document.getElementById('assignedAcestreams');
    if (!container) return;
    
    if (channelState.acestreams.length === 0) {
        container.innerHTML = `
            <div class="list-group-item text-center text-muted">
                <small>No acestreams assigned to this channel</small>
            </div>
        `;
        return;
    }
    
    container.innerHTML = channelState.acestreams.map(stream => {
        const statusClass = stream.is_online ? 'bg-success' : 'bg-danger';
        const statusText = stream.is_online ? 'Online' : 'Offline';
        
        return `
            <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                <div>
                    <div class="fw-bold">${stream.name || 'Unnamed channel'}</div>
                    <small class="text-muted">${stream.id}</small>
                </div>
                <div>
                    <span class="badge ${statusClass}">${statusText}</span>
                    <button class="btn btn-sm btn-danger ms-2" onclick="removeAcestream('${stream.id}')" title="Remove association">
                        <i class="bi bi-x"></i> Remove
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Load available acestreams for assignment
 */
async function loadAvailableAcestreams(searchTerm = '') {
    const container = document.getElementById('availableAcestreams');
    if (!container) return;
    
    container.innerHTML = `
        <div class="list-group-item text-center">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">Loading available acestreams...</span>
        </div>
    `;
    
    try {
        // Build query parameters
        const params = new URLSearchParams();
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        
        console.log('Fetching unassigned acestreams with search term:', searchTerm);
        const response = await fetch(`/api/tv-channels/unassigned-acestreams?${params.toString()}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to load available acestreams');
        }
        
        const acestreams = data.acestreams || [];
        console.log(`Found ${acestreams.length} unassigned acestreams`);
        
        if (acestreams.length === 0) {
            container.innerHTML = `
                <div class="list-group-item text-center text-muted">
                    <small>No unassigned acestreams available</small>
                </div>
            `;
            return;
        }
        
        container.innerHTML = acestreams.map(stream => {
            const statusClass = stream.is_online ? 'bg-success' : 'bg-danger';
            const statusText = stream.is_online ? 'Online' : 'Offline';
            
            return `
                <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                    <div>
                        <div class="fw-bold">${stream.name || 'Unnamed channel'}</div>
                        <small class="text-muted">${stream.id}</small>
                    </div>
                    <div>
                        <span class="badge ${statusClass}">${statusText}</span>
                        <button class="btn btn-sm btn-success ms-2" onclick="assignAcestream('${stream.id}')" title="Assign to this TV channel">
                            <i class="bi bi-plus"></i> Add
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading available acestreams:', error);
        container.innerHTML = `
            <div class="list-group-item text-center text-danger">
                <small>Error loading acestreams: ${error.message}</small>
            </div>
        `;
    }
}

/**
 * Assign an acestream to this TV channel
 */
async function assignAcestream(acestream_id) {
    try {
        showLoading();
        
        const response = await fetch(`/api/tv-channels/${channelState.channelId}/acestreams`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ acestream_id })
        });
        
        if (response.ok) {
            // Reload data
            await loadChannelData();
            
            // Update modal UI
            updateAssignedAcestreams();
            await loadAvailableAcestreams(document.getElementById('searchAcestreamsInput').value);
            
            showAlert('success', 'Acestream assigned to TV channel');
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Failed to assign acestream');
        }
    } catch (error) {
        console.error('Error assigning acestream:', error);
        showAlert('error', error.message || 'Error assigning acestream');
    } finally {
        hideLoading();
    }
}

/**
 * Remove an acestream from this TV channel
 */
async function removeAcestream(acestream_id) {
    if (!confirm('Are you sure you want to remove this acestream from the TV channel?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`/api/tv-channels/${channelState.channelId}/acestreams/${acestream_id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Reload data
            await loadChannelData();
            
            // Update modal UI if it's open
            const modal = document.getElementById('assignAcestreamsModal');
            if (modal.classList.contains('show')) {
                updateAssignedAcestreams();
                await loadAvailableAcestreams(document.getElementById('searchAcestreamsInput').value);
            }
            
            showAlert('success', 'Acestream removed from TV channel');
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Failed to remove acestream');
        }
    } catch (error) {
        console.error('Error removing acestream:', error);
        showAlert('error', error.message || 'Error removing acestream');
    } finally {
        hideLoading();
    }
}

/**
 * Check the status of an acestream
 */
async function checkAcestreamStatus(acestream_id) {
    try {
        showLoading();
        
        const response = await fetch(`/api/channels/${acestream_id}/status`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Reload data to show updated status
            await loadChannelData();
            
            // Show status message
            const statusText = result.is_online ? 'online' : 'offline';
            showAlert('info', `Channel status checked: ${statusText}`);
        } else {
            throw new Error(result.message || 'Failed to check acestream status');
        }
    } catch (error) {
        console.error('Error checking acestream status:', error);
        showAlert('error', error.message || 'Error checking acestream status');
    } finally {
        hideLoading();
    }
}

/**
 * Synchronize EPG data between TV channel and acestreams
 */
async function syncEpgData() {
    try {
        showLoading();
        
        const response = await fetch(`/api/tv-channels/${channelState.channelId}/sync-epg`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Reload data
            await loadChannelData();
            
            const message = result.changes_made ? 
                'EPG data synchronized successfully - changes were made' : 
                'EPG data synchronized - no changes needed';
            
            showAlert('success', message);
        } else {
            throw new Error(result.message || 'Failed to synchronize EPG data');
        }
    } catch (error) {
        console.error('Error syncing EPG data:', error);
        showAlert('error', error.message || 'Error synchronizing EPG data');
    } finally {
        hideLoading();
    }
}

/**
 * Preview the logo in the edit form
 */
function previewLogo() {
    const logoUrl = document.getElementById('editTVChannelLogo').value.trim();
    const logoPreview = document.getElementById('logoPreview');
    const logoImg = logoPreview.querySelector('img');
    
    if (logoUrl) {
        logoImg.src = logoUrl;
        logoImg.onload = () => {
            logoPreview.style.display = 'block';
        };
        logoImg.onerror = () => {
            logoPreview.style.display = 'none';
            showAlert('warning', 'Cannot load logo image from URL');
        };
    } else {
        logoPreview.style.display = 'none';
    }
}

/**
 * Show the assign acestreams modal with search functionality
 */
function showAssignModal() {
    const modal = document.getElementById('assignAcestreamsModal');
    
    // Set channel name in modal
    document.getElementById('tvChannelNameDisplay').textContent = `TV Channel: ${channelState.channelData.name}`;
    
    // Clear search input
    const searchInput = document.getElementById('searchAcestreamsInput');
    if (searchInput) {
        searchInput.value = '';
        
        // Ensure event listener is properly attached
        searchInput.removeEventListener('input', searchHandler); // Remove old handler if exists
        searchInput.addEventListener('input', searchHandler);
    }
    
    // Display assigned acestreams
    updateAssignedAcestreams();
    
    // Load available acestreams
    loadAvailableAcestreams();
    
    // Show the modal
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

// Debounced search handler
const searchHandler = debounce(function() {
    console.log('Search input changed:', this.value);
    const searchTerm = this.value.trim();
    loadAvailableAcestreams(searchTerm);
}, 300);

// Format date for display
function formatLocalDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeDetailPage);
