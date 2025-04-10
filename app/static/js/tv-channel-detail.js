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
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-tv text-muted" viewBox="0 0 16 16">
                    <path d="M2.5 13.5A.5.5 0 0 1 3 13h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zM13.991 3l.024.001a1.46 1.46 0 0 1 .538.143.757.757 0 0 1 .302.254c.067.1.145.277.145.602v5.991l-.001.024a1.464 1.464 0 0 1-.143.538.758.758 0 0 1-.254.302c-.1.067-.277.145-.602.145H2.009l-.024-.001a1.464 1.464 0 0 1-.538-.143.758.758 0 0 1-.302-.254C1.078 10.502 1 10.325 1 10V4.009l.001-.024a1.46 1.46 0 0 1 .143-.538.758.758 0 0 1 .254-.302C1.498 3.078 1.675 3 2 3h11.991zM14 2H2C0 2 0 4 0 4v6c0 2 2 2 2 2h12c2 0 2-2 2-2V4c0-2-2-2-2-2z"/>
                </svg>
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
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-shield-check" viewBox="0 0 16 16">
                                <path d="M5.338 1.59a61.44 61.44 0 0 0-2.837.856.481.481 0 0 0-.328.39c-.554 4.157.726 7.19 2.253 9.188a10.725 10.725 0 0 0 2.287 2.233c.346.244.652.42.893.533.12.057.218.095.293.118a.55.55 0 0 0 .101.025.615.615 0 0 0 .1-.025c.076-.023.174-.061.294-.118.24-.113.547-.29.893-.533a10.726 10.726 0 0 0 2.287-2.233c1.527-1.997 2.807-5.031 2.253-9.188a.48.48 0 0 0-.328-.39c-.651-.213-1.75-.56-2.837-.855C9.552 1.29 8.531 1.067 8 1.067c-.53 0-1.552.223-2.662.524zM5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887.87a1.54 1.54 0 0 1 1.044 1.262c.596 4.477-.787 7.795-2.465 9.99a11.775 11.775 0 0 1-2.517 2.453a7.159 7.159 0 0 1-1.048.625c-.28.132-.581.24-.829.24s-.548-.108-.829-.24a7.158 7.158 0 0 1-1.048-.625 11.777 11.777 0 0 1-2.517-2.453C1.928 10.487.545 7.169 1.141 2.692A1.54 1.54 0 0 1 2.185 1.43 62.456 62.456 0 0 1 5.072.56z"/>
                                <path d="M10.854 5.146a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1 .708-.708L7.5 7.793l2.646-2.647a.5.5 0 0 1 .708 0z"/>
                            </svg>
                        </button>
                        <button class="btn btn-danger" onclick="removeAcestream('${stream.id}')" title="Remove association">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                            </svg>
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
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                            <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                        </svg>
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
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus" viewBox="0 0 16 16">
                                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                            </svg>
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
