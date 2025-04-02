/**
 * Channel management functionality for Acestream Scraper
 */

// Handle form submission for adding a channel
async function handleAddChannel(e) {
    e.preventDefault();
    
    const channelId = document.getElementById('channelId').value.trim();
    const channelName = document.getElementById('channelName').value.trim();
    const channelGroup = document.getElementById('channelGroup').value.trim();
    
    // Advanced fields
    const channelLogo = document.getElementById('channelLogo').value.trim();
    const channelTvgId = document.getElementById('channelTvgId').value.trim();
    const channelTvgName = document.getElementById('channelTvgName').value.trim();
    const channelOriginalUrl = document.getElementById('channelOriginalUrl').value.trim();
    const channelM3uSource = document.getElementById('channelM3uSource').value.trim();
    
    if (!channelId) {
        showAlert('warning', 'Please enter a channel ID');
        return;
    }
    
    try {
        showLoading();
        
        // Create the channel data object with all fields
        const channelData = {
            id: channelId,
            name: channelName || `Channel ${channelId}`,
            manual_add: true, // Flag indicating this is a manually added channel
            group: channelGroup || '',
            current_url: window.location.href // Send the current browser URL
        };
        
        // Only add the advanced fields if they are provided
        if (channelLogo) channelData.logo = channelLogo;
        if (channelTvgId) channelData.tvg_id = channelTvgId;
        if (channelTvgName) channelData.tvg_name = channelTvgName;
        if (channelOriginalUrl) channelData.original_url = channelOriginalUrl;
        if (channelM3uSource) channelData.m3u_source = channelM3uSource;
        
        const response = await fetch('/api/channels/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(channelData)
        });
        
        if (response.ok) {
            showAlert('success', 'Channel added successfully');
            document.getElementById('addChannelForm').reset();
            
            // Refresh the channels list
            if (typeof refreshChannelList === 'function') {
                await refreshChannelList();
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to add channel');
        }
    } catch (error) {
        console.error('Error adding channel:', error);
        showAlert('danger', error.message || 'Error adding channel');
    } finally {
        hideLoading();
    }
}

// Add event listener for form submission
document.addEventListener('DOMContentLoaded', function() {
    // Set up the form submission handler for adding channels
    const addChannelForm = document.getElementById('addChannelForm');
    if (addChannelForm) {
        addChannelForm.addEventListener('submit', handleAddChannel);
        console.log('Add channel form handler set up');
    }
    
    // Set up event listener for the save button in the edit modal
    const saveButton = document.getElementById('saveEditChannelBtn');
    if (saveButton) {
        saveButton.addEventListener('click', saveChannelChanges);
    }
});

// Delete a channel
async function deleteChannel(channelId) {
    if (!confirm('Are you sure you want to delete this channel?')) {
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/channels/${encodeURIComponent(channelId)}`, {
            method: 'DELETE'
        });
        
        if (await handleApiResponse(response, 'Channel deleted successfully')) {
            // Refresh data after successful deletion
            if (typeof refreshData === 'function') {
                await refreshData();
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('error', 'Network error while deleting channel');
    } finally {
        hideLoading();
    }
}

// Check status for all channels
async function checkChannelsStatus() {
    if (!confirm('Check status of all channels? This might take a while.')) {
        return;
    }
    
    showLoading();
    try {
        const response = await fetch('/api/channels/check-status', {
            method: 'POST'
        });
        
        const data = await response.json();
        if (response.ok) {
            if (typeof refreshData === 'function') {
                await refreshData();
            }
        } else {
            alert(data.message || data.error || 'Error checking channel status');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error while checking channel status');
    } finally {
        hideLoading();
    }
}

// Refresh channels list with optional search term and URL filter
async function refreshChannelList(searchTerm = '', urlId = '') {
    try {
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
        
        const channelsList = document.getElementById('channelsList');
        if (channelsList) {
            channelsList.innerHTML = channels.map(channel => `
                <tr>
                    <td>${channel.name}</td>
                    <td>
                            <a href="acestream://${channel.id}" class="text-decoration-none" title="Open in Acestream player">
                                ${channel.id}
                            </a>
                    </td>
                    <td>
                        ${formatLocalDate(channel.last_processed)}
                        ${channel.last_checked ? `
                            <br>
                            <small class="text-muted">
                                Status: <span class="badge ${channel.is_online ? 'bg-success' : 'bg-danger'}">
                                    ${channel.is_online ? 'Online' : 'Offline'}
                                </span>
                                ${channel.check_error ? `<br>Error: ${channel.check_error}` : ''}
                                <br>
                                Last checked: ${formatLocalDate(channel.last_checked)}
                            </small>
                        ` : ''}
                    </td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-info" onclick="checkChannelStatus('${channel.id}')" title="Check status">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-shield-check" viewBox="0 0 16 16">
                                    <path d="M5.338 1.59a61.44 61.44 0 0 0-2.837.856.481.481 0 0 0-.328.39c-.554 4.157.726 7.19 2.253 9.188a10.725 10.725 0 0 0 2.287 2.233c.346.244.652.42.893.533.12.057.218.095.293.118a.55.55 0 0 0 .101.025.615.615 0 0 0 .1-.025c.076-.023.174-.061.294-.118.24-.113.547-.29.893-.533a10.726 10.726 0 0 0 2.287-2.233c1.527-1.997 2.807-5.031 2.253-9.188a.48.48 0 0 0-.328-.39c-.651-.213-1.75-.56-2.837-.855C9.552 1.29 8.531 1.067 8 1.067c-.53 0-1.552.223-2.662.524zM5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887.87a1.54 1.54 0 0 1 1.044 1.262c.596 4.477-.787 7.795-2.465 9.99a11.775 11.775 0 0 1-2.517 2.453 7.159 7.159 0 0 1-1.048.625c-.28.132-.581.24-.829.24s-.548-.108-.829-.24a7.158 7.158 0 0 1-1.048-.625 11.777 11.777 0 0 1-2.517-2.453C1.928 10.487.545 7.169 1.141 2.692A1.54 1.54 0 0 1 2.185 1.43 62.456 62.456 0 0 1 5.072.56z"/>
                                    <path d="M10.854 5.146a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1 .708-.708L7.5 7.793l2.646-2.647a.5.5 0 0 1 .708 0z"/>
                                </svg>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteChannel('${channel.id}')" title="Delete channel">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                    <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                                </svg>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
        
        // Update total and filtered channel counts in stats
        const displayedChannels = document.getElementById('displayedChannels');
        if (displayedChannels) {
            displayedChannels.textContent = channels.length;
        }
    } catch (error) {
        console.error('Error refreshing channels list:', error);
    }
}

// Search channels by name with optional URL filter
async function searchChannels(searchTerm, urlId = '') {
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
        
        // Get current URL filter if not provided
        if (!urlId) {
            const urlFilter = document.getElementById('urlFilter');
            if (urlFilter && urlFilter.value) {
                params.append('url_id', urlFilter.value);
            }
        }
        
        // Fetch filtered channels
        const queryString = params.toString() ? `?${params.toString()}` : '';
        const response = await fetch(`/api/channels${queryString}`);
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Failed to search channels');
        }
        
        const channels = await response.json();
        
        // Update the channel list with the same styling as refreshChannelList
        const channelsList = document.getElementById('channelsList');
        if (channelsList) {
            channelsList.innerHTML = channels.map(channel => {
                // Asegurarse de que channel.id y channel.name nunca sean null
                const channelId = channel.id || 'unknown';
                const channelName = channel.name || 'Unnamed Channel';
                
                // Determinar clase de estilo según metadatos
                let metadataClass = 'primary'; // Por defecto azul (sin metadatos)
                let metadataText = 'Basic';
                let metadataBadge = '';
                let tooltipText = 'Edit channel - No EPG data';
                
                // Si está bloqueado, tiene prioridad en el color
                if (channel.epg_update_protected) {
                    metadataClass = 'purple';
                    metadataText = 'Locked EPG';
                    metadataBadge = '<span class="badge bg-purple ms-1"><i class="bi bi-lock-fill"></i></span>';
                    tooltipText = 'Edit channel - EPG locked (protected from automatic updates)';
                }
                // Sino evaluamos el estado de los metadatos
                else if (channel.tvg_id && channel.tvg_name && channel.logo) {
                    metadataClass = 'success';  // Verde - completo
                    metadataText = 'Complete EPG';
                    tooltipText = 'Edit channel - Complete EPG data';
                } 
                else if (channel.tvg_id || channel.tvg_name || channel.logo) {
                    metadataClass = 'warning';  // Ámbar - parcial
                    metadataText = 'Partial EPG';
                    tooltipText = 'Edit channel - Partial EPG data';
                }
                
                // Logo display
                const logoHtml = channel.logo ? 
                    `<img src="${channel.logo}" alt="Logo" class="channel-logo me-2" style="max-height:24px; max-width:50px;">` : 
                    '';
                
                // Usar exactamente el mismo HTML que en refreshChannelList
                return `
                <tr class="border-${metadataClass}">
                    <td>
                        <div class="d-flex align-items-center">
                            ${logoHtml}
                            <div>
                                ${channelName}
                                <span class="badge bg-${metadataClass} ms-1">${metadataText}</span>
                                ${metadataBadge}
                            </div>
                        </div>
                    </td>
                    <td>
                        <a href="acestream://${channelId}" class="text-decoration-none" title="Open in Acestream player">
                            ${channelId}
                        </a>
                    </td>
                    <td>
                        ${formatLocalDate(channel.last_processed)}
                        ${channel.last_checked ? `
                            <br>
                            <small class="text-muted">
                                Status: <span class="badge ${channel.is_online ? 'bg-success' : 'bg-danger'}">
                                    ${channel.is_online ? 'Online' : 'Offline'}
                                </span>
                                ${channel.check_error ? `<br><small class="text-danger">Error: ${channel.check_error}</small>` : ''}
                                <br>
                                Last checked: ${formatLocalDate(channel.last_checked)}
                            </small>
                        ` : ''}
                    </td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-${channel.epg_update_protected ? 'purple' : 'outline-secondary'} toggle-epg-lock" 
                                data-id="${channelId}" title="${channel.epg_update_protected ? 'Allow automatic EPG updates' : 'Prevent automatic EPG updates'}">
                                ${channel.epg_update_protected ? '<i class="bi bi-lock-fill"></i>' : '<i class="bi bi-unlock"></i>'} EPG
                            </button>
                            <button class="btn btn-sm btn-info check-status" 
                                onclick="checkChannelStatus('${encodeURIComponent(channelId)}')" title="Check status">
                                <i class="bi bi-shield-check"></i>
                            </button>
                            <button class="btn btn-sm btn-${metadataClass} edit-channel" 
                                onclick="editChannel('${encodeURIComponent(channelId)}')" title="${tooltipText}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" 
                                onclick="deleteChannel('${encodeURIComponent(channelId)}')" title="Delete channel">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
                `;
            }).join('');
        }
        
        return channels;
    } catch (error) {
        console.error('Error searching channels:', error);
        showAlert('danger', 'Error searching channels');
        return [];
    } finally {
        hideLoading();
    }
}

// Check status of a specific channel
async function checkChannelStatus(channelId) {
    try {
        showLoading();
        const response = await fetch(`/api/channels/${encodeURIComponent(channelId)}/check-status`, {
            method: 'POST'
        });
        
        await handleApiResponse(response);
    } catch (error) {
        console.error('Error:', error);
        alert('Network error while checking channel status');
    } finally {
        hideLoading();
    }
}

// Edit a channel - load data and show modal
async function editChannel(channelId) {
    try {
        showLoading();
        const response = await fetch(`/api/channels/${channelId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch channel data');
        }
        
        const channel = await response.json();
        
        // Populate form fields
        document.getElementById('editChannelId').value = channel.id;
        document.getElementById('editChannelName').value = channel.name || '';
        document.getElementById('editChannelGroup').value = channel.group || '';
        document.getElementById('editChannelLogo').value = channel.logo || '';
        document.getElementById('editChannelTvgId').value = channel.tvg_id || '';
        document.getElementById('editChannelTvgName').value = channel.tvg_name || '';
        document.getElementById('editChannelOriginalUrl').value = channel.original_url || '';
        document.getElementById('editChannelM3uSource').value = channel.m3u_source || '';
        const epgLockedField = document.getElementById('editChannelEpgLocked');
        if (epgLockedField) {
            epgLockedField.checked = Boolean(channel.epg_update_protected || false);
        }
        
        // Show the modal
        const editModal = new bootstrap.Modal(document.getElementById('editChannelModal'));
        editModal.show();
        
    } catch (error) {
        console.error('Error loading channel data:', error);
        showAlert('danger', 'Failed to load channel data');
    } finally {
        hideLoading();
    }
}

// Initialize the edit channel functionality
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listener for the save button in the edit modal
    const saveButton = document.getElementById('saveEditChannelBtn');
    if (saveButton) {
        saveButton.addEventListener('click', saveChannelChanges);
    }
});

// Save changes to an edited channel
async function saveChannelChanges() {
    try {
        showLoading();
        
        const channelId = document.getElementById('editChannelId').value;
        const channelName = document.getElementById('editChannelName').value;
        const channelGroup = document.getElementById('editChannelGroup').value;
        const channelLogo = document.getElementById('editChannelLogo').value;
        const channelTvgId = document.getElementById('editChannelTvgId').value;
        const channelTvgName = document.getElementById('editChannelTvgName').value;
        const channelOriginalUrl = document.getElementById('editChannelOriginalUrl').value;
        const channelM3uSource = document.getElementById('editChannelM3uSource').value;
        const epgLocked = document.getElementById('editChannelEpgLocked').checked;
        
        // Create channel data object
        const channelData = {
            name: channelName,
            group: channelGroup,
            epg_update_protected: epgLocked  
        };
        
        // Only include fields that have values
        if (channelLogo) channelData.logo = channelLogo;
        if (channelTvgId) channelData.tvg_id = channelTvgId;
        if (channelTvgName) channelData.tvg_name = channelTvgName;
        if (channelOriginalUrl) channelData.original_url = channelOriginalUrl;
        if (channelM3uSource) channelData.m3u_source = channelM3uSource;
        
        // Send update request
        const response = await fetch(`/api/channels/${channelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(channelData)
        });
        
        if (response.ok) {
            // Close the modal
            const editModal = bootstrap.Modal.getInstance(document.getElementById('editChannelModal'));
            editModal.hide();
            
            showAlert('success', 'Channel updated successfully');
            
            // Refresh channel list
            if (typeof refreshChannelList === 'function') {
                await refreshChannelList();
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update channel');
        }
    } catch (error) {
        console.error('Error updating channel:', error);
        showAlert('danger', error.message || 'Error updating channel');
    } finally {
        hideLoading();
    }
}