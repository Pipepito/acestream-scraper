/**
 * JavaScript for creating TV Channels from EPG data
 */

document.addEventListener('DOMContentLoaded', function() {
    // Override the original loadEpgChannels function to add TV Channel creation buttons
    const originalLoadEpgChannels = window.loadEpgChannels;
    if (originalLoadEpgChannels) {
        window.loadEpgChannels = function(page = 1, searchTerm = '') {
            return originalLoadEpgChannels(page, searchTerm).then(() => {
                // After the EPG channels are loaded, add our create TV channel buttons
                addCreateTVChannelButtons();
                return Promise.resolve(); // Maintain the promise chain
            });
        };
    }
    
    // Initialize the modal functionality
    initTVChannelModal();
});

/**
 * Add "Create TV Channel" buttons to the EPG channels table
 */
function addCreateTVChannelButtons() {
    const actionCells = document.querySelectorAll('#epgChannelsTable tr td:last-child');
    
    actionCells.forEach(cell => {
        // Skip rows that don't have proper data (like loading or empty states)
        if (cell.closest('tr').cells.length <= 2) return;
        
        // Get the EPG channel data from the row
        const row = cell.closest('tr');
        const epgId = row.cells[1].textContent.trim();
        const channelName = row.cells[2].textContent.trim();
        
        // Check if the button already exists to avoid duplicates
        if (!cell.querySelector('.create-tv-channel-btn')) {
            // Create the button
            const createBtn = document.createElement('button');
            createBtn.className = 'btn btn-outline-success btn-sm ms-1 create-tv-channel-btn';
            createBtn.innerHTML = '<i class="bi bi-tv"></i> Create TV Channel';
            createBtn.onclick = function(e) {
                e.stopPropagation(); // Prevent row click event
                openCreateTVChannelModal(epgId, channelName);
            };
            
            // Add the button to the cell
            cell.appendChild(createBtn);
        }
    });
}

/**
 * Initialize the TV Channel creation modal
 */
function initTVChannelModal() {
    // Logo preview button
    const previewLogoBtn = document.getElementById('createPreviewLogoBtn');
    if (previewLogoBtn) {
        previewLogoBtn.addEventListener('click', function() {
            const logoUrl = document.getElementById('createTVChannelLogo').value;
            if (logoUrl) {
                const previewContainer = document.getElementById('createLogoPreview');
                const previewImg = previewContainer.querySelector('img');
                previewImg.src = logoUrl;
                previewContainer.classList.remove('d-none');
            }
        });
    }
    
    // Match confidence threshold slider
    const confidenceSlider = document.getElementById('matchConfidenceThreshold');
    if (confidenceSlider) {
        confidenceSlider.addEventListener('input', function() {
            document.getElementById('matchThresholdValue').textContent = this.value + '%';
        });
    }
    
    // Find matching streams button
    const findMatchesBtn = document.getElementById('findMatchingStreamsBtn');
    if (findMatchesBtn) {
        findMatchesBtn.addEventListener('click', function() {
            findMatchingStreams();
        });
    }
    
    // Select all streams checkbox
    const selectAllStreams = document.getElementById('selectAllStreams');
    if (selectAllStreams) {
        selectAllStreams.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('#matchingStreamsList input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedStreamsCount();
        });
    }
    
    // Create TV Channel button
    const createTVChannelBtn = document.getElementById('createTVChannelBtn');
    if (createTVChannelBtn) {
        createTVChannelBtn.addEventListener('click', function() {
            createTVChannel();
        });
    }
}

/**
 * Open the Create TV Channel modal with EPG data
 */
function openCreateTVChannelModal(epgId, channelName) {
    // Reset the form
    document.getElementById('createTVChannelForm').reset();
    document.getElementById('createLogoPreview').classList.add('d-none');
    
    // Reset the matching streams list
    document.getElementById('matchingStreamsList').innerHTML = `
        <div class="list-group-item text-center text-muted p-4">
            <i class="bi bi-info-circle me-2"></i>
            Click "Find Matches" to search for acestreams that match this EPG channel
        </div>
    `;
    document.getElementById('selectedStreamsCount').textContent = '0';
    
    // Reset match confidence slider to 50%
    const confidenceSlider = document.getElementById('matchConfidenceThreshold');
    if (confidenceSlider) {
        confidenceSlider.value = '50';
        document.getElementById('matchThresholdValue').textContent = '50%';
    }
    
    // Fetch EPG channel details
    fetch('/api/epg/channels')
        .then(response => response.json())
        .then(channels => {
            // Find the channel with the matching EPG ID
            const channel = channels.find(ch => ch.id === epgId);
            
            if (channel) {
                // Populate the form with EPG data
                document.getElementById('createTVChannelName').value = channel.name || channelName;
                document.getElementById('createTVChannelEpgId').value = channel.id;
                document.getElementById('createTVChannelEpgSourceId').value = channel.source_id || '';
                
                // Set language if available
                if (channel.language) {
                    document.getElementById('createTVChannelLanguage').value = channel.language;
                }
                
                // Set logo if available
                if (channel.icon) {
                    document.getElementById('createTVChannelLogo').value = channel.icon;
                    
                    // Show logo preview
                    const previewContainer = document.getElementById('createLogoPreview');
                    const previewImg = previewContainer.querySelector('img');
                    previewImg.src = channel.icon;
                    previewContainer.classList.remove('d-none');
                }
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('createTVChannelFromEPGModal'));
                modal.show();
            } else {
                showAlert('warning', `Could not find EPG channel details for ID: ${epgId}`);
            }
        })
        .catch(error => {
            console.error('Error fetching EPG channel details:', error);
            showAlert('danger', 'Failed to load EPG channel details');
        });
}

/**
 * Find Acestream channels that match the current EPG channel
 */
function findMatchingStreams() {
    const epgId = document.getElementById('createTVChannelEpgId').value;
    const channelName = document.getElementById('createTVChannelName').value;
    
    if (!epgId && !channelName) {
        showAlert('warning', 'EPG ID or channel name is required to find matches');
        return;
    }
    
    // Get the threshold value from the slider
    const threshold = document.getElementById('matchConfidenceThreshold').value / 100;
    
    // Show loading state
    document.getElementById('matchingStreamsList').innerHTML = `
        <div class="list-group-item text-center p-3">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">Searching for matching acestreams...</span>
        </div>
    `;
    
    // Build the query parameters
    const params = new URLSearchParams();
    if (epgId) params.append('epg_id', epgId);
    if (channelName) params.append('name', channelName);
    params.append('threshold', threshold); // Add the threshold parameter
    
    // Call the API to find matches
    fetch(`/api/tv-channels/find-matches?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to find matching streams');
            }
            return response.json();
        })
        .then(data => {
            const matches = data.matches || [];
            const streamsList = document.getElementById('matchingStreamsList');
            
            if (matches.length === 0) {
                streamsList.innerHTML = `
                    <div class="list-group-item text-center text-muted p-3">
                        <i class="bi bi-exclamation-circle me-2"></i>
                        No matching acestreams found
                    </div>
                `;
                return;
            }
            
            // Render the matches
            streamsList.innerHTML = matches.map((match, index) => {
                const channel = match.channel;
                const score = match.score || 0;
                const scorePercent = Math.round(score * 100);
                
                // Determine badge color based on match score
                let badgeClass = 'bg-danger';
                if (scorePercent >= 90) {
                    badgeClass = 'bg-success';
                } else if (scorePercent >= 70) {
                    badgeClass = 'bg-primary';
                } else if (scorePercent >= 50) {
                    badgeClass = 'bg-warning text-dark';
                }
                
                return `
                    <div class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="form-check">
                                <input class="form-check-input stream-checkbox" type="checkbox" value="${channel.id}" 
                                       id="stream_${index}" onchange="updateSelectedStreamsCount()">
                                <label class="form-check-label" for="stream_${index}">
                                    <strong>${channel.name || channel.id}</strong>
                                </label>
                            </div>
                            <span class="badge ${badgeClass}">${scorePercent}% match</span>
                        </div>
                        <div class="small text-muted mt-1">
                            ID: ${channel.id}
                        </div>
                        ${channel.is_online ? 
                            '<div class="small text-success"><i class="bi bi-broadcast"></i> Online</div>' : 
                            '<div class="small text-secondary"><i class="bi bi-broadcast"></i> Offline</div>'}
                    </div>
                `;
            }).join('');
            
            // Update the selected count
            updateSelectedStreamsCount();
        })
        .catch(error => {
            console.error('Error finding matching streams:', error);
            document.getElementById('matchingStreamsList').innerHTML = `
                <div class="list-group-item text-center text-danger p-3">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error: ${error.message}
                </div>
            `;
        });
}

/**
 * Update the count of selected streams
 */
function updateSelectedStreamsCount() {
    const selectedCount = document.querySelectorAll('#matchingStreamsList input[type="checkbox"]:checked').length;
    document.getElementById('selectedStreamsCount').textContent = selectedCount.toString();
}

/**
 * Create a TV Channel with selected acestreams
 */
function createTVChannel() {
    // Validate required field
    const name = document.getElementById('createTVChannelName').value.trim();
    if (!name) {
        showAlert('warning', 'Channel name is required');
        return;
    }
    
    // Get selected acestreams
    const selectedStreams = [];
    document.querySelectorAll('#matchingStreamsList input[type="checkbox"]:checked').forEach(checkbox => {
        selectedStreams.push(checkbox.value);
    });
    
    // Prepare the request data
    const channelData = {
        name: name,
        description: document.getElementById('createTVChannelDescription').value,
        logo_url: document.getElementById('createTVChannelLogo').value,
        category: document.getElementById('createTVChannelCategory').value,
        country: document.getElementById('createTVChannelCountry').value,
        language: document.getElementById('createTVChannelLanguage').value,
        website: document.getElementById('createTVChannelWebsite').value,
        epg_id: document.getElementById('createTVChannelEpgId').value,
        epg_source_id: document.getElementById('createTVChannelEpgSourceId').value || null,
        is_active: document.getElementById('createTVChannelIsActive').checked,
        selected_acestreams: selectedStreams
    };
    
    // Show loading state
    const createBtn = document.getElementById('createTVChannelBtn');
    const originalBtnText = createBtn.innerHTML;
    createBtn.disabled = true;
    createBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Creating...
    `;
    
    // Call the API to create the TV channel
    fetch('/api/tv-channels/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(channelData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(error => {
                throw new Error(error.message || 'Failed to create TV channel');
            });
        }
        return response.json();
    })
    .then(data => {
        // Close the modal
        bootstrap.Modal.getInstance(document.getElementById('createTVChannelFromEPGModal')).hide();
        
        // Show success message
        showAlert('success', `TV channel "${name}" created successfully with ${data.associated_acestreams || 0} acestreams`);
        
        // Optionally, redirect to the new TV channel's detail page
        if (data.id) {
            setTimeout(() => {
                window.location.href = `/tv-channels/${data.id}`;
            }, 1500);
        }
    })
    .catch(error => {
        console.error('Error creating TV channel:', error);
        showAlert('danger', error.message || 'Failed to create TV channel');
    })
    .finally(() => {
        // Reset button state
        createBtn.disabled = false;
        createBtn.innerHTML = originalBtnText;
    });
}

/**
 * Show alert/notification
 * (Check if global showAlert exists, otherwise define our own)
 */
if (typeof window.showAlert !== 'function') {
    window.showAlert = function(type, message, duration = 5000) {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertContainer.style.zIndex = '9999';
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.body.appendChild(alertContainer);
        
        // Auto-dismiss after duration
        setTimeout(() => {
            alertContainer.classList.remove('show');
            setTimeout(() => alertContainer.remove(), 150);
        }, duration);
    };
}
