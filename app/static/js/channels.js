/**
 * Channel management functionality for Acestream Scraper
 */

// Handle form submission for adding a channel
async function handleAddChannel(e) {
    e.preventDefault();
    const channelIdInput = document.getElementById('channelId');
    const channelNameInput = document.getElementById('channelName');
    
    let channelId = channelIdInput.value.trim();
    let channelName = channelNameInput.value.trim();
     
    // Reset previous validation state
    channelIdInput.classList.remove('is-invalid');
    channelNameInput.classList.remove('is-invalid');
    
    // Clear previous error messages
    document.getElementById('channelIdError')?.remove();
    document.getElementById('channelNameError')?.remove();
    
    let isValid = true;
    
    // Validate channel name
    if (!channelName) {
        channelNameInput.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.id = 'channelNameError';
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = 'Channel name is required';
        channelNameInput.parentNode.appendChild(errorDiv);
        isValid = false;
    }
    
    // Validate Acestream ID
    if (!channelId) {
        channelIdInput.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.id = 'channelIdError';
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = 'Channel ID is required';
        channelIdInput.parentNode.appendChild(errorDiv);
        isValid = false;
    } else {
        // Search for any 40-character hexadecimal sequence in the text
        const aceStreamIdMatch = channelId.match(/[a-fA-F0-9]{40}/);

        if (aceStreamIdMatch) {
            const extractedId = aceStreamIdMatch[0];
            channelIdInput.value = extractedId;
            channelId = extractedId;
        } else {
            channelIdInput.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.id = 'channelIdError';
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = 'Channel ID not valid';
            channelIdInput.parentNode.appendChild(errorDiv);
            isValid = false;
        }   
    }
    
    if (!isValid) {
        return;
    }

    try {
        showLoading();
        const response = await fetch('/api/channels/', {  // Note: no trailing slash
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                id: channelId,
                name: channelName
            })
        });

        if (await handleApiResponse(response, 'Channel added successfully')) {
            channelIdInput.value = '';
            channelNameInput.value = '';
            channelIdInput.classList.remove('is-valid');
            channelNameInput.classList.remove('is-valid');
            // Refresh data after successful addition
            if (typeof refreshData === 'function') {
                await refreshData();
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('error', 'Network error while adding channel');
    } finally {
        hideLoading();
    }
}

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
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to search channels');
        }
        
        return data;
    } catch (error) {
        console.error('Error searching channels:', error);
        showAlert('error', 'Error searching channels');
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