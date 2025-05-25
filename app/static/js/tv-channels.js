/**
 * TV Channels Management JavaScript
 * Handles interactions for the TV channels management page
 */

// Page state
const tvChannelsState = {
    channels: [],
    filters: {
        categories: [],
        countries: [],
        languages: []
    },
    page: 1,
    perPage: 20,
    totalPages: 1,
    isLoading: false,
    selectedChannels: new Set(),
    favoritesOnly: false
};

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('TV Channels page initialized');
    
    // Initialize the page
    loadInitialData();
    
    // Set up event listeners
    setupEventListeners();

    // Initialize bulk edit handlers
    initBulkEditHandlers();

    // Initialize bulk actions
    initializeBulkActions();
    
    // Initialize playlist functionality
    initializePlaylistFunctions();
    
    // Initialize playlist URL (set the initial URL state)
    updatePlaylistUrl();
    
    // Initialize the global favorites checkbox state on page load
    const favoritesFilter = document.getElementById('favoritesOnlyFilter');
    if (favoritesFilter && favoritesFilter.checked) {
      document.getElementById('globalFavoritesOnly').checked = true;
    }
});

/**
 * Load initial data for the page
 */
async function loadInitialData() {
    showLoading();
    try {
        // Load TV channels with filters and pagination
        await loadTVChannels();
        
        // Update the stats cards
        updateStatCards();
    } catch (error) {
        console.error('Error initializing page:', error);
        showAlert('error', 'Failed to load TV channels data');
    } finally {
        hideLoading();
    }
}

/**
 * Set up event listeners for the page elements
 */
function setupEventListeners() {
    // Add TV Channel button
    const addTVChannelBtn = document.getElementById('addTVChannelBtn');
    if (addTVChannelBtn) {
        addTVChannelBtn.addEventListener('click', showAddTVChannelModal);
    } else {
        console.error('Add TV Channel button not found');
    }
    
    // Save new TV channel button
    const saveTVChannelBtn = document.getElementById('saveTVChannelBtn');
    if (saveTVChannelBtn) {
        saveTVChannelBtn.addEventListener('click', saveNewTVChannel);
    }
    
    // Search input
    const searchInput = document.getElementById('tvChannelSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            tvChannelsState.page = 1; // Reset to first page
            loadTVChannels();
        }, 300));
    }
    
    // Filter dropdowns
    const filters = ['category', 'country', 'language'];
    filters.forEach(filter => {
        const element = document.getElementById(`${filter}Filter`);
        if (element) {
            element.addEventListener('change', function() {
                tvChannelsState.page = 1; // Reset to first page
                loadTVChannels();
            });
        }
    });
    
    // Favorites filter
    const favoritesFilter = document.getElementById('favoritesOnlyFilter');
    if (favoritesFilter) {
        favoritesFilter.addEventListener('change', function() {
            tvChannelsState.favoritesOnly = this.checked;
            tvChannelsState.page = 1; // Reset to first page
            loadTVChannels();
        });
    }
    
    // Per page dropdown
    const perPageSelect = document.getElementById('channelsPerPage');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            tvChannelsState.perPage = parseInt(this.value);
            tvChannelsState.page = 1; // Reset to first page
            loadTVChannels();
        });
    }
    
    // Batch actions
    document.getElementById('batchAssignBtn')?.addEventListener('click', batchAssignAcestreams);
    document.getElementById('associateByEPGBtn')?.addEventListener('click', associateByEPG);
    document.getElementById('bulkUpdateEPGBtn')?.addEventListener('click', bulkUpdateEPG);
    document.getElementById('generateTVChannelsBtn')?.addEventListener('click', generateTVChannelsFromAcestreams);

    // Add listener for batch assign save button
    document.getElementById('saveBatchAssignBtn')?.addEventListener('click', processBatchAssignment);
    
    // Add listener for add pattern row button
    document.getElementById('addPatternRowBtn')?.addEventListener('click', addAssignmentPatternRow);
}

/**
 * Show the modal for adding a new TV channel
 */
function showAddTVChannelModal() {
    // Reset the form
    const form = document.getElementById('addTVChannelForm');
    if (form) {
        form.reset();
    }
    
    // Clear any previous selected acestreams
    const selectedAcestreamsContainer = document.getElementById('selectedAcestreams');
    if (selectedAcestreamsContainer) {
        selectedAcestreamsContainer.innerHTML = '';
    }
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('addTVChannelModal'));
    modal.show();
    
    // Load unassigned acestreams for the selection area
    loadUnassignedAcestreams();
}

/**
 * Save a new TV channel
 */
function saveNewTVChannel() {
    // Get form data
    const form = document.getElementById('addTVChannelForm');
    if (!form) return;
      // Collect form data
    const formData = {
        name: form.querySelector('[name="name"]').value.trim(),
        description: form.querySelector('[name="description"]').value.trim() || null,
        logo_url: form.querySelector('[name="logo_url"]').value.trim() || null,
        category: form.querySelector('[name="category"]').value.trim() || null,
        country: form.querySelector('[name="country"]').value.trim() || null,
        language: form.querySelector('[name="language"]').value.trim() || null,
        website: form.querySelector('[name="website"]').value.trim() || null,
        epg_id: form.querySelector('[name="epg_id"]').value.trim() || null,        epg_source_id: form.querySelector('[name="epg_source_id"]').value ? parseInt(form.querySelector('[name="epg_source_id"]').value) : null,
        channel_number: form.querySelector('[name="channel_number"]').value ? parseInt(form.querySelector('[name="channel_number"]').value) : null,
        is_active: form.querySelector('[name="is_active"]').checked,
        is_favorite: form.querySelector('[name="is_favorite"]').checked,
        selected_acestreams: []
    };
    
    // Validate required fields
    if (!formData.name) {
        showAlert('error', 'Channel name is required');
        return;
    }
    
    // Collect selected acestreams
    const selectedContainer = document.getElementById('selectedAcestreams');
    if (selectedContainer) {
        const acestreams = selectedContainer.querySelectorAll('.selected-acestream');
        acestreams.forEach(item => {
            const id = item.getAttribute('data-acestream-id');
            if (id) {
                formData.selected_acestreams.push(id);
            }
        });
    }
    
    // Show loading
    showLoading();
    
    // Send API request
    fetch('/api/tv-channels/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to create TV channel');
            });
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        showAlert('success', 'TV channel created successfully');
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addTVChannelModal'));
        if (modal) {
            modal.hide();
        }
        
        // Refresh channel list
        loadTVChannels();
    })
    .catch(error => {
        console.error('Error creating TV channel:', error);
        showAlert('error', error.message || 'Failed to create TV channel');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Load unassigned acestreams for selection in the add channel modal
 */
function loadUnassignedAcestreams(searchTerm = '') {
    const container = document.getElementById('unassignedAcestreamsContainer');
    if (!container) return;
    
    // Show loading indicator
    container.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Loading acestreams...</span>
            </div>
            <span class="ms-2">Loading unassigned acestreams...</span>
        </div>
    `;
    
    // Build query parameters
    let url = '/api/tv-channels/unassigned-acestreams';
    if (searchTerm) {
        url += `?search=${encodeURIComponent(searchTerm)}`;
    }
    
    // Fetch unassigned acestreams
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load unassigned acestreams');
            }
            return response.json();
        })
        .then(data => {
            if (!data.acestreams || data.acestreams.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-info">
                        No unassigned acestreams found
                    </div>
                `;
                return;
            }
            
            // Create search box and list container
            let html = `
                <div class="mb-3">
                    <input type="text" 
                           class="form-control form-control-sm" 
                           id="acestreamsSearchInput" 
                           placeholder="Search acestreams...">
                </div>
                <div class="list-group acestreams-list" style="max-height: 300px; overflow-y: auto;">
            `;
            
            // Add each acestream as a list item
            data.acestreams.forEach(acestream => {
                html += `
                    <div class="list-group-item list-group-item-action">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                ${acestream.name || 'Unnamed Stream'}
                                <small class="d-block text-muted">${acestream.id}</small>
                            </div>
                            <button type="button" 
                                    class="btn btn-sm btn-outline-primary select-acestream-btn"
                                    data-acestream-id="${acestream.id}" 
                                    data-acestream-name="${acestream.name || 'Unnamed Stream'}">
                                Select
                            </button>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
            
            // Add event listener to search input
            const searchInput = document.getElementById('acestreamsSearchInput');
            if (searchInput) {
                searchInput.addEventListener('input', debounce(function() {
                    loadUnassignedAcestreams(this.value);
                }, 300));
            }
            
            // Add event listeners to select buttons
            document.querySelectorAll('.select-acestream-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const id = this.getAttribute('data-acestream-id');
                    const name = this.getAttribute('data-acestream-name');
                    addSelectedAcestream(id, name);
                });
            });
        })
        .catch(error => {
            console.error('Error loading unassigned acestreams:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Failed to load unassigned acestreams: ${error.message}
                </div>
            `;
        });
}

/**
 * Add a selected acestream to the list of acestreams to associate with the new TV channel
 * @param {string} id - Acestream ID
 * @param {string} name - Acestream name
 */
function addSelectedAcestream(id, name) {
    const container = document.getElementById('selectedAcestreams');
    if (!container) return;
    
    // Check if this acestream is already selected
    if (container.querySelector(`.selected-acestream[data-acestream-id="${id}"]`)) {
        // Already selected, don't add again
        return;
    }
    
    // Create a new element for this selected acestream
    const acestream = document.createElement('div');
    acestream.className = 'selected-acestream alert alert-info alert-dismissible fade show';
    acestream.setAttribute('data-acestream-id', id);
    
    acestream.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <strong>${name}</strong>
                <small class="d-block">${id}</small>
            </div>
            <button type="button" class="btn-close" aria-label="Remove"></button>
        </div>
    `;
    
    // Add event listener to remove button
    acestream.querySelector('.btn-close').addEventListener('click', function() {
        acestream.remove();
    });
    
    // Add to container
    container.appendChild(acestream);
}

/**
 * Initialize playlist functionality for TV channels
 */
function initializePlaylistFunctions() {
    // Update button references to match HTML elements
    
    // Download playlist button
    const downloadPlaylistBtn = document.getElementById('downloadPlaylistBtn');
    if (downloadPlaylistBtn) {
        downloadPlaylistBtn.addEventListener('click', function() {
            downloadTVChannelsPlaylist(false);
        });
    }
    
    // Initialize copy to clipboard functionality for playlist URL
    const playlistUrlElement = document.getElementById('tvChannelsPlaylistUrl');
    const copyPlaylistUrlBtn = document.getElementById('copyPlaylistUrlBtn');
    
    if (playlistUrlElement && copyPlaylistUrlBtn) {
        copyPlaylistUrlBtn.addEventListener('click', function() {
            copyToClipboard('#tvChannelsPlaylistUrl');
        });
    }
    
    // Add event listener for playlist favorites only checkbox
    const playlistFavoritesCheckbox = document.getElementById('playlistFavoritesOnly');
    if (playlistFavoritesCheckbox) {
        playlistFavoritesCheckbox.addEventListener('change', updatePlaylistUrl);
    }
    
    // Add event listener for EPG XML favorites only checkbox
    const epgFavoritesCheckbox = document.getElementById('epgFavoritesOnly');
    if (epgFavoritesCheckbox) {
        epgFavoritesCheckbox.addEventListener('change', updateEpgXmlUrl);
    }
}

/**
 * Update the playlist URL based on current filters and favorites selection
 */
function updatePlaylistUrl() {
    const urlInput = document.getElementById('tvChannelsPlaylistUrl');
    if (!urlInput) return;
    
    // Get base URL
    const baseUrl = urlInput.getAttribute('data-base-url');
    if (!baseUrl) return;
    
    // Check if favorites only is selected
    const favoritesOnly = document.getElementById('playlistFavoritesOnly')?.checked || false;
    
    // Build URL with proper parameters
    let url = baseUrl;
    if (favoritesOnly) {
        url += (url.includes('?') ? '&' : '?') + 'favorites_only=true';
    }
    
    // Update URL in input field
    urlInput.value = url;
}

/**
 * Update the EPG XML URL based on current filters and favorites selection
 */
function updateEpgXmlUrl() {
    const urlInput = document.getElementById('epgXmlUrl');
    if (!urlInput) return;
    
    // Get base URL
    const baseUrl = urlInput.getAttribute('data-base-url');
    if (!baseUrl) return;
    
    // Check if favorites only is selected
    const favoritesOnly = document.getElementById('epgFavoritesOnly')?.checked || false;
    
    // Build URL with proper parameters
    let url = baseUrl;
    if (favoritesOnly) {
        url += (url.includes('?') ? '&' : '?') + 'favorites_only=true';
    }
    
    // Update URL in input field
    urlInput.value = url;
}

/**
 * Download EPG XML file with current filters
 */
function downloadEpgXml() {
    // Get URL from input field (already formatted with correct parameters)
    const urlInput = document.getElementById('epgXmlUrl');
    if (!urlInput) return;
    
    // Navigate to the URL to download the EPG XML
    window.location.href = urlInput.value;
}

/**
 * Copy content to clipboard
 * @param {string} elementSelector - CSS selector for the element to copy from
 */
function copyToClipboard(elementSelector) {
    const element = document.querySelector(elementSelector);
    if (!element) return;
    
    // Select the text
    element.select();
    element.setSelectionRange(0, 99999); // For mobile devices
    
    // Copy the text
    document.execCommand('copy');
    
    // Deselect the text
    window.getSelection().removeAllRanges();
    
    // Find the button that was clicked (assuming it's the next sibling or parent)
    const button = document.querySelector(`button[onclick*="copyToClipboard('${elementSelector}')"]`);
    if (button) {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 1500);
    }
}

/**
 * Download TV channels playlist
 * 
 * @param {boolean} refresh - Whether to refresh the playlist before downloading
 */
function downloadTVChannelsPlaylist(refresh = false) {
    // Build base URL
    const urlInput = document.getElementById('tvChannelsPlaylistUrl');
    if (!urlInput) return;
    
    let url = urlInput.value;
    if (refresh) {
        url += (url.includes('?') ? '&' : '?') + 'refresh=true';
    }
    
    // Trigger download
    window.location.href = url;
}

/**
 * Download all streams playlist (TV channels + unassigned streams)
 */
function downloadAllStreamsPlaylist() {
    const urlInput = document.getElementById('allStreamsPlaylistUrl');
    if (!urlInput) return;
    
    // Trigger download
    window.location.href = urlInput.value;
}

/**
 * Toggle favorites across all filters and playlist options
 * 
 * @param {boolean} checked - Whether favorites only should be enabled or disabled
 */
function toggleAllFavorites(checked) {
    // Update all hidden favorites checkboxes
    document.getElementById('favoritesOnlyFilter').checked = checked;
    document.getElementById('playlistFavoritesOnly').checked = checked;
    document.getElementById('epgFavoritesOnly').checked = checked;
    
    // Manually trigger the change events to update URLs and filter the table
    if (document.getElementById('playlistFavoritesOnly').onchange) {
      document.getElementById('playlistFavoritesOnly').onchange();
    }
    
    if (document.getElementById('epgFavoritesOnly').onchange) {
      document.getElementById('epgFavoritesOnly').onchange();
    }
    
    // If favoritesOnlyFilter has event listeners in the JS file, this will trigger them
    const favoritesFilter = document.getElementById('favoritesOnlyFilter');
    if (favoritesFilter) {
      const event = new Event('change', { bubbles: true });
      favoritesFilter.dispatchEvent(event);
    }
}

/**
 * Initialize bulk edit functionality
 */
function initBulkEditHandlers() {
    // Set up select all checkbox
    const selectAllCheckbox = document.getElementById('selectAllChannels');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const checkboxes = document.querySelectorAll('.channel-select-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
                const channelId = checkbox.value;
                
                if (isChecked) {
                    tvChannelsState.selectedChannels.add(channelId);
                } else {
                    tvChannelsState.selectedChannels.delete(channelId);
                }
            });
            
            updateBulkEditToolbar();
        });
    }
    
    // Set up bulk edit buttons
    document.getElementById('bulkEditBtn')?.addEventListener('click', openBulkEditModal);
    document.getElementById('clearSelectionBtn')?.addEventListener('click', clearSelection);
    document.getElementById('saveBulkEditBtn')?.addEventListener('click', saveBulkEdit);
    
    // Set up bulk field toggles
    const toggles = document.querySelectorAll('.bulk-field-toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const fieldName = this.value;
            const fieldGroup = document.getElementById(`${fieldName}FieldGroup`);
            
            if (this.checked) {
                fieldGroup.classList.remove('d-none');
            } else {
                fieldGroup.classList.add('d-none');
            }
        });
    });
}

/**
 * Open the bulk edit modal with the selected TV channels
 */
function openBulkEditModal() {
    const selectedCount = tvChannelsState.selectedChannels.size;
    if (selectedCount === 0) {
        showAlert('warning', 'No channels selected');
        return;
    }
    
    // Get the modal element
    const modal = document.getElementById('bulkEditModal');
    if (!modal) return;
    
    // Reset the form
    const form = document.getElementById('bulkEditForm');
    if (form) {
        form.reset();
    }
    
    // Reset all field toggles to unchecked and hide field groups
    document.querySelectorAll('.bulk-field-toggle').forEach(toggle => {
        toggle.checked = false;
    });
    
    document.querySelectorAll('.bulk-field-group').forEach(group => {
        group.classList.add('d-none');
    });
    
    // Update the selection count in the modal
    const selectionCountElement = document.getElementById('selectedChannelCount');
    if (selectionCountElement) {
        selectionCountElement.textContent = selectedCount;
    }
    
    // Show the modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Clear the current channel selection
 */
function clearSelection() {
    // Clear the selected channels set
    tvChannelsState.selectedChannels.clear();
    
    // Uncheck all checkboxes
    document.querySelectorAll('.channel-select-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Also uncheck the "select all" checkbox
    const selectAllCheckbox = document.getElementById('selectAllChannels');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
    }
    
    // Update the bulk edit toolbar visibility
    updateBulkEditToolbar();
}

/**
 * Update the visibility and count of the bulk edit toolbar based on selection
 */
function updateBulkEditToolbar() {
    const toolbar = document.getElementById('bulkEditToolbar');
    if (!toolbar) return;
    
    const selectedCount = tvChannelsState.selectedChannels.size;
    
    if (selectedCount > 0) {
        toolbar.classList.remove('d-none');
        
        // Update selected count badge
        const countBadge = document.getElementById('selectedChannelsCount');
        if (countBadge) {
            countBadge.textContent = selectedCount;
        }
    } else {
        toolbar.classList.add('d-none');
    }
}

/**
 * Save bulk edit changes to selected TV channels
 */
function saveBulkEdit() {
    // Get selected channel IDs
    const selectedIds = Array.from(tvChannelsState.selectedChannels);
    if (selectedIds.length === 0) return;
    
    // Collect form data
    const form = document.getElementById('bulkEditForm');
    if (!form) return;
    
    const changes = {};
    let hasChanges = false;
    
    // Check which fields are enabled and collect their values
    document.querySelectorAll('.bulk-field-toggle:checked').forEach(toggle => {
        const fieldName = toggle.value;
        let fieldValue;
        
        // Handle different types of fields
        switch (fieldName) {
            case 'is_active':
                fieldValue = form.querySelector(`[name="${fieldName}"]`).checked;
                break;
            default:
                const input = form.querySelector(`[name="${fieldName}"]`);
                if (input) {
                    fieldValue = input.value.trim() || null;
                }
        }
        
        // Add to changes if value is not undefined
        if (fieldValue !== undefined) {
            changes[fieldName] = fieldValue;
            hasChanges = true;
        }
    });
    
    if (!hasChanges) {
        showAlert('warning', 'No changes selected');
        return;
    }
    
    // Show loading
    showLoading();
    
    // Send API request
    fetch('/api/tv-channels/bulk-update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            channel_ids: selectedIds,
            changes: changes
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to update TV channels');
            });
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        showAlert('success', `Successfully updated ${data.updated_count} channels`);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('bulkEditModal'));
        if (modal) {
            modal.hide();
        }
        
        // Refresh channel list to reflect changes
        loadTVChannels();
        
        // Clear selection
        clearSelection();
    })
    .catch(error => {
        console.error('Error during bulk update:', error);
        showAlert('error', error.message || 'Failed to update TV channels');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Initialize event handlers for bulk actions
 */
function initializeBulkActions() {
    // Select all channels checkbox
    const selectAllCheckbox = document.getElementById('selectAllChannels');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const checkboxes = document.querySelectorAll('.channel-select-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
                const channelId = parseInt(checkbox.getAttribute('data-channel-id'));
                
                if (isChecked) {
                    tvChannelsState.selectedChannels.add(channelId);
                } else {
                    tvChannelsState.selectedChannels.delete(channelId);
                }
            });
            
            updateBulkEditToolbar();
        });
    }
    
    // Bulk edit button
    const bulkEditBtn = document.getElementById('bulkEditBtn');
    if (bulkEditBtn) {
        bulkEditBtn.addEventListener('click', openBulkEditModal);
    }
    
    // Bulk delete button
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', confirmBulkDelete);
    }
    
    // Clear selection button
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', clearSelection);
    }
    
    // Update bulk edit toolbar initially
    updateBulkEditToolbar();
}

/**
 * Process batch assigning of acestreams to TV channels based on EPG ID
 */
async function associateByEPG() {
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/associate-by-epg', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to associate acestreams by EPG ID');
        }
          const result = await response.json();
        console.log('Associate by EPG response:', result);
        
        // Extract stats from the result, ensuring we have default values if properties are missing
        const matched = result.stats?.matched || result.matched || 0;
        const unmatched = result.stats?.unmatched || result.unmatched || 0;
        const created = result.stats?.created || result.created || 0;
        const existingAssociations = result.stats?.existing_associations || result.existing_associations || 0;
        
        // Build a comprehensive success message
        let message = 'EPG Association complete: ';
        const parts = [];
        
        if (created > 0) {
            parts.push(`${created} new TV channels created`);
        }
        if (matched > 0) {
            parts.push(`${matched} acestreams matched`);
        }
        if (existingAssociations > 0) {
            parts.push(`${existingAssociations} existing associations`);
        }
        if (unmatched > 0) {
            parts.push(`${unmatched} unmatched`);
        }
        
        if (parts.length > 0) {
            message += parts.join(', ');
        } else {
            message += 'No changes made';
        }
        
        // Show success message with statistics
        showAlert('success', message);
        
        // Reload TV channels to reflect changes
        loadTVChannels();
    } catch (error) {
        console.error('Error associating by EPG:', error);
        showAlert('error', error.message || 'Failed to associate acestreams by EPG ID');
    } finally {
        hideLoading();
    }
}

/**
 * Process bulk update of EPG data for all TV channels
 */
async function bulkUpdateEPG() {
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/bulk-update-epg', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update EPG data');
        }
        
        const result = await response.json();
        console.log('Bulk update EPG response:', result);
        
        // Extract stats from the result with fallbacks for different response structures
        const updated = result.stats?.updated || result.updated || 0;
        const skipped = result.stats?.skipped || result.skipped || 0;
        const errors = result.stats?.errors || result.errors || 0;
        
        // Show success message with statistics
        const message = `EPG update complete: ${updated} channels updated, ${skipped} skipped, ${errors} errors`;
        showAlert('success', message);
        
        // Reload TV channels to reflect changes
        loadTVChannels();
    } catch (error) {
        console.error('Error updating EPG data:', error);
        showAlert('error', error.message || 'Failed to update EPG data');
    } finally {
        hideLoading();
    }
}

/**
 * Generate TV channels from existing acestreams
 */
async function generateTVChannelsFromAcestreams() {
    if (!confirm('This will create new TV channels based on unassigned acestreams. Continue?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/generate-from-acestreams', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to generate TV channels');
        }
        
        const result = await response.json();
        console.log('Generate TV channels response:', result);
        
        // Extract stats from the result with fallbacks for different response structures
        const created = result.stats?.created || result.created || 0;
        const matched = result.stats?.matched || result.matched || 0;
        const skipped = result.stats?.skipped || result.skipped || 0;
        const errors = result.stats?.errors || result.errors || 0;
        
        // Show success message with statistics
        const message = `TV channels generated: ${created} channels created, ${matched} acestreams matched` +
                       (skipped > 0 ? `, ${skipped} skipped` : '') +
                       (errors > 0 ? `, ${errors} errors` : '');
        showAlert('success', message);
        
        // Reload TV channels to reflect changes
        loadTVChannels();
    } catch (error) {
        console.error('Error generating TV channels:', error);
        showAlert('error', error.message || 'Failed to generate TV channels');
    } finally {
        hideLoading();
    }
}

/**
 * Show the modal for batch assigning acestreams to TV channels
 */
function batchAssignAcestreams() {
    // Get the modal element
    const modal = document.getElementById('batchAssignModal');
    if (!modal) return;
    
    // Clear any previous patterns
    const patternsContainer = document.getElementById('assignmentPatternsContainer');
    if (patternsContainer) {
        patternsContainer.innerHTML = '<div class="pattern-row"></div>';
    }
    
    // Add the first empty row
    addAssignmentPatternRow();
    
    // Populate TV channel dropdown with current TV channels
    populateTVChannelDropdowns();
    
    // Show the modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

/**
 * Populate TV channel dropdowns for the batch assign modal
 */
function populateTVChannelDropdowns() {
    // Fetch TV channels if we don't have them yet
    if (!tvChannelsState.channels || tvChannelsState.channels.length === 0) {
        fetch('/api/tv-channels/?per_page=100')
            .then(response => response.json())
            .then(data => {
                tvChannelsState.channels = data.channels;
                updateTVChannelDropdowns();
            })
            .catch(error => {
                console.error('Error fetching TV channels:', error);
                showAlert('error', 'Failed to load TV channels');
            });
    } else {
        updateTVChannelDropdowns();
    }
}

/**
 * Update all TV channel dropdowns with the current channel list
 */
function updateTVChannelDropdowns() {
    // Find all TV channel dropdowns in the batch assign modal
    const dropdowns = document.querySelectorAll('.tv-channel-dropdown');
    
    dropdowns.forEach(dropdown => {
        // Save current selection
        const currentValue = dropdown.value;
        
        // Clear dropdown except for the first placeholder option
        while (dropdown.options.length > 1) {
            dropdown.remove(1);
        }
        
        // Add options for all TV channels
        tvChannelsState.channels.forEach(channel => {
            const option = document.createElement('option');
            option.value = channel.id;
            option.textContent = channel.name;
            dropdown.appendChild(option);
        });
        
        // Restore previous selection if it exists
        if (currentValue && dropdown.querySelector(`option[value="${currentValue}"]`)) {
            dropdown.value = currentValue;
        }
    });
}

/**
 * Add a new pattern row to the batch assign modal
 */
function addAssignmentPatternRow() {
    const container = document.getElementById('assignmentPatternsContainer');
    if (!container) return;
    
    const row = document.createElement('div');
    row.className = 'pattern-row mb-3';
    
    row.innerHTML = `
        <div class="row g-3 align-items-center">
            <div class="col-md-5">
                <input type="text" class="form-control pattern-input" placeholder="Channel name contains...">
            </div>
            <div class="col-md-5">
                <select class="form-select tv-channel-dropdown">
                    <option value="">Select a TV channel...</option>
                    <!-- Will be populated by JavaScript -->
                </select>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger btn-sm remove-pattern-btn">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;
    
    // Add event listener to the remove button
    const removeBtn = row.querySelector('.remove-pattern-btn');
    removeBtn.addEventListener('click', function() {
        row.remove();
    });
    
    // Add to container
    container.appendChild(row);
    
    // Update TV channel dropdowns
    updateTVChannelDropdowns();
}

/**
 * Process the batch assignment of acestreams to TV channels
 */
function processBatchAssignment() {
    // Collect patterns and TV channel IDs
    const patterns = {};
    let hasErrors = false;
    
    // Check each pattern row
    document.querySelectorAll('.pattern-row').forEach(row => {
        const patternInput = row.querySelector('.pattern-input');
        const channelSelect = row.querySelector('.tv-channel-dropdown');
        
        if (!patternInput || !channelSelect) return;
        
        const pattern = patternInput.value.trim();
        const channelId = channelSelect.value;
        
        // Validate input
        if (!pattern) {
            patternInput.classList.add('is-invalid');
            hasErrors = true;
            return;
        }
        
        if (!channelId) {
            channelSelect.classList.add('is-invalid');
            hasErrors = true;
            return;
        }
        
        // Add to patterns object
        patterns[pattern] = parseInt(channelId);
        
        // Clear validation errors
        patternInput.classList.remove('is-invalid');
        channelSelect.classList.remove('is-invalid');
    });
    
    if (hasErrors || Object.keys(patterns).length === 0) {
        showAlert('error', 'Please fill in all pattern fields and select TV channels');
        return;
    }
    
    // Show loading
    showLoading();
    
    // Send API request
    fetch('/api/tv-channels/batch-assign', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            patterns: patterns
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => { throw new Error(data.message || 'Failed to assign acestreams'); });
        }
        return response.json();
    })
    .then(data => {
        // Show success message
        let message = 'Assignment complete. ';
        let totalAssigned = 0;
        
        // Create result summary
        Object.keys(data.assigned).forEach(channelId => {
            const count = data.assigned[channelId];
            totalAssigned += count;
            const channel = tvChannelsState.channels.find(c => c.id.toString() === channelId);
            if (channel && count > 0) {
                message += `${count} acestreams assigned to "${channel.name}". `;
            }
        });
        
        if (totalAssigned === 0) {
            message = 'No acestreams matched the provided patterns.';
        }
        
        showAlert('success', message);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('batchAssignModal'));
        if (modal) {
            modal.hide();
        }
        
        // Refresh channel list
        loadTVChannels();
    })
    .catch(error => {
        console.error('Error during batch assignment:', error);
        showAlert('error', error.message || 'Failed to assign acestreams');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Show confirmation dialog for bulk deletion
 */
function confirmBulkDelete() {
    const selectedCount = tvChannelsState.selectedChannels.size;
    if (selectedCount === 0) {
        showAlert('warning', 'No channels selected');
        return;
    }
    
    if (confirm(`Are you sure you want to delete ${selectedCount} selected channels? This action cannot be undone.`)) {
        bulkDeleteChannels();
    }
}

/**
 * Delete multiple channels at once
 */
async function bulkDeleteChannels() {
    const selectedIds = Array.from(tvChannelsState.selectedChannels);
    if (selectedIds.length === 0) return;
    
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/bulk-delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                channel_ids: selectedIds
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showAlert('success', result.message || `Successfully deleted ${result.deleted_count} channels`);
            
            // Clear selection and refresh the list
            clearSelection();
            await loadTVChannels();
        } else {
            const error = await response.json();
            throw new Error(error.message || `Failed to delete channels: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error deleting channels:', error);
        showAlert('error', error.message || 'An error occurred during bulk deletion');
    } finally {
        hideLoading();
    }
}

/**
 * Load TV channels with current filters and pagination
 */
async function loadTVChannels() {
    if (tvChannelsState.isLoading) return;
    
    tvChannelsState.isLoading = true;
    showLoading();
    
    try {
        // Get filter values
        const category = document.getElementById('categoryFilter').value;
        const country = document.getElementById('countryFilter').value;
        const language = document.getElementById('languageFilter').value;
        const search = document.getElementById('tvChannelSearchInput').value;
        const favoritesOnly = document.getElementById('favoritesOnlyFilter').checked;
        
        // Build query parameters
        const params = new URLSearchParams({
            page: tvChannelsState.page,
            per_page: tvChannelsState.perPage
        });
        
        if (category) params.append('category', category);
        if (country) params.append('country', country);
        if (language) params.append('language', language);
        if (search) params.append('search', search);
        if (favoritesOnly) params.append('favorites_only', 'true');
        
        // Store favorites state in the state object
        tvChannelsState.favoritesOnly = favoritesOnly;
        
        // Fetch TV channels
        const response = await fetch(`/api/tv-channels/?${params.toString()}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to load TV channels');
        }
        
        // Update state
        tvChannelsState.channels = data.channels;
        tvChannelsState.totalPages = data.total_pages;
        tvChannelsState.filters.categories = data.filters.categories;
        tvChannelsState.filters.countries = data.filters.countries;
        tvChannelsState.filters.languages = data.filters.languages;
        
        // Update UI
        updateTVChannelsTable();
        updateFilterDropdowns();
        updatePagination();
        
    } catch (error) {
        console.error('Error loading TV channels:', error);
        showAlert('error', 'Failed to load TV channels data');
    } finally {
        hideLoading();
        tvChannelsState.isLoading = false;
    }
}

/**
 * Update the TV channels table with current data
 */
function updateTVChannelsTable() {
    const tableBody = document.getElementById('tvChannelsTableBody');
    
    if (!tableBody) {
        console.error('TV channels table body not found');
        return;
    }
    
    if (tvChannelsState.channels.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted">
                    No channels found matching your criteria
                </td>
            </tr>
        `;
        return;
    }
    
    // Note: We don't need to sort here as the API now returns channels 
    // already ordered by channel_number first, then name
    tableBody.innerHTML = tvChannelsState.channels.map(channel => {
        // Prepare favorite status indicator
        let favoriteIcon = '';
        if (channel.is_favorite) {
            favoriteIcon = '<i class="bi bi-star-fill text-warning me-2" title="Favorite"></i>';
        }
        
        return `
            <tr>
                <td>
                    <div class="form-check">
                        <input class="form-check-input channel-select-checkbox" 
                               type="checkbox" 
                               value="${channel.id}"
                               data-channel-id="${channel.id}"
                               ${tvChannelsState.selectedChannels.has(channel.id.toString()) ? 'checked' : ''}>
                    </div>
                </td>
                <td>
                    <div class="input-group input-group-sm">
                        <input type="number" 
                               class="form-control form-control-sm channel-number-input" 
                               value="${channel.channel_number || ''}" 
                               min="1"
                               data-channel-id="${channel.id}"
                               placeholder="#"
                               aria-label="Channel number">
                        <button class="btn btn-outline-secondary save-channel-number-btn" 
                                type="button" 
                                data-channel-id="${channel.id}"
                                title="Save channel number">
                            <i class="bi bi-check"></i>
                        </button>
                    </div>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        ${favoriteIcon}
                        <div>
                            <a href="/tv-channels/${channel.id}" class="text-decoration-none">
                                ${channel.name}
                            </a>
                        </div>
                    </div>
                </td>
                <td>${channel.category || '-'}</td>
                <td>
                    ${channel.country ? `<div>${channel.country}</div>` : ''}
                    ${channel.language ? `<small class="text-muted">${channel.language}</small>` : ''}
                </td>
                <td>
                    <span class="badge bg-primary">${channel.acestream_channels_count}</span>
                </td>
                <td>${channel.epg_id || '-'}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary toggle-favorite-btn" 
                                onclick="toggleChannelFavorite(${channel.id})" 
                                title="${channel.is_favorite ? 'Remove from favorites' : 'Add to favorites'}">
                            <i class="bi ${channel.is_favorite ? 'bi-star-fill' : 'bi-star'}"></i>
                        </button>
                        <button class="btn btn-success" onclick="showPlayerOptions('${channel.id}')" title="Play stream">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-play-fill" viewBox="0 0 16 16">
                                <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z"/>
                            </svg>
                        </button>
                        <a href="/tv-channels/${channel.id}" class="btn btn-primary" title="View details">
                            <i class="bi bi-eye"></i>
                        </a>
                        <button class="btn btn-danger" onclick="deleteChannel(${channel.id})" title="Delete channel">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Add event listeners to channel number inputs
    document.querySelectorAll('.save-channel-number-btn').forEach(button => {
        button.addEventListener('click', function() {
            const channelId = parseInt(this.getAttribute('data-channel-id'));
            const input = document.querySelector(`.channel-number-input[data-channel-id="${channelId}"]`);
            
            if (input) {
                const value = parseInt(input.value);
                // Only save if the value is a valid number
                if (!isNaN(value) && value > 0) {
                    setChannelNumber(channelId, value);
                } else if (input.value === '') {
                    // Clear channel number (set to null)
                    setChannelNumber(channelId, null);
                }
            }
        });
    });
    
    // Also save on Enter key
    document.querySelectorAll('.channel-number-input').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const channelId = parseInt(this.getAttribute('data-channel-id'));
                const value = parseInt(this.value);
                
                // Only save if the value is a valid number
                if (!isNaN(value) && value > 0) {
                    setChannelNumber(channelId, value);
                } else if (this.value === '') {
                    // Clear channel number (set to null)
                    setChannelNumber(channelId, null);
                }
            }
        });
    });
    
    // Add event listeners to checkboxes
    document.querySelectorAll('.channel-select-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const channelId = this.value;
            
            if (this.checked) {
                tvChannelsState.selectedChannels.add(channelId);
            } else {
                tvChannelsState.selectedChannels.delete(channelId);
            }
            
            updateBulkEditToolbar();
        });
    });
}

/**
 * Set channel number for a TV channel
 */
async function setChannelNumber(channelId, channelNumber) {
    try {
        showLoading();
        
        const payload = { 
            channel_number: channelNumber 
        };
        
        const response = await fetch(`/api/tv-channels/${channelId}/channel-number`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Update channel in state
            const channelIndex = tvChannelsState.channels.findIndex(c => c.id === channelId);
            if (channelIndex >= 0) {
                tvChannelsState.channels[channelIndex].channel_number = channelNumber;
                showAlert('success', `Channel number updated`);
            }
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update channel number');
        }
    } catch (error) {
        console.error('Error setting channel number:', error);
        showAlert('error', error.message || 'Error updating channel number');
    } finally {
        hideLoading();
    }
}

/**
 * Update filter dropdowns with available options from data
 */
function updateFilterDropdowns() {
    // Update categories dropdown
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        // Store current value
        const currentValue = categoryFilter.value;
        
        // Clear existing options except the first "All Categories" option
        while (categoryFilter.options.length > 1) {
            categoryFilter.remove(1);
        }
        
        // Add new options
        if (tvChannelsState.filters.categories) {
            tvChannelsState.filters.categories.forEach(category => {
                if (category) {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    categoryFilter.appendChild(option);
                }
            });
        }
        
        // Restore selected value if it exists in the new options
        if (currentValue) {
            categoryFilter.value = currentValue;
        }
    }
    
    // Update countries dropdown
    const countryFilter = document.getElementById('countryFilter');
    if (countryFilter) {
        // Store current value
        const currentValue = countryFilter.value;
        
        // Clear existing options except the first "All Countries" option
        while (countryFilter.options.length > 1) {
            countryFilter.remove(1);
        }
        
        // Add new options
        if (tvChannelsState.filters.countries) {
            tvChannelsState.filters.countries.forEach(country => {
                if (country) {
                    const option = document.createElement('option');
                    option.value = country;
                    option.textContent = country;
                    countryFilter.appendChild(option);
                }
            });
        }
        
        // Restore selected value if it exists in the new options
        if (currentValue) {
            countryFilter.value = currentValue;
        }
    }
    
    // Update languages dropdown
    const languageFilter = document.getElementById('languageFilter');
    if (languageFilter) {
        // Store current value
        const currentValue = languageFilter.value;
        
        // Clear existing options except the first "All Languages" option
        while (languageFilter.options.length > 1) {
            languageFilter.remove(1);
        }
        
        // Add new options
        if (tvChannelsState.filters.languages) {
            tvChannelsState.filters.languages.forEach(language => {
                if (language) {
                    const option = document.createElement('option');
                    option.value = language;
                    option.textContent = language;
                    languageFilter.appendChild(option);
                }
            });
        }
        
        // Restore selected value if it exists in the new options
        if (currentValue) {
            languageFilter.value = currentValue;
        }
    }
}

/**
 * Update statistics cards with current data
 */
function updateStatCards() {
    // Instead of using a dedicated stats endpoint that doesn't exist,
    // we'll fetch the main TV channels list with minimal data
    const params = new URLSearchParams({
        page: 1,
        per_page: 1  // We just need the total count, not actual items
    });
    
    fetch(`/api/tv-channels/?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load TV channels statistics');
            }
            return response.json();
        })
        .then(data => {
            // Extract stats from the main API response
            const stats = {
                total: data.total || 0,
                active: 0,
                with_epg: 0,
                total_acestreams: 0
            };
            
            // Update total TV channels card
            const totalChannelsCard = document.getElementById('totalTVChannelsCard');
            if (totalChannelsCard) {
                totalChannelsCard.textContent = stats.total;
            }
            
            // For the other stats, we'll make a separate call to count specific categories
            // Active channels (filter by is_active=true)
            fetch('/api/tv-channels/?is_active=true&per_page=1')
                .then(response => response.json())
                .then(data => {
                    const activeChannelsCard = document.getElementById('activeChannelsCard');
                    if (activeChannelsCard) {
                        activeChannelsCard.textContent = data.total || 0;
                    }
                })
                .catch(() => {
                    // Handle errors silently for this secondary stat
                    const activeChannelsCard = document.getElementById('activeChannelsCard');
                    if (activeChannelsCard) {
                        activeChannelsCard.textContent = 'N/A';
                    }
                });
            
            // Channels with EPG data - we'll count these from the main list
            let withEpgCount = 0;
            if (data.channels && Array.isArray(data.channels)) {
                withEpgCount = data.channels.filter(channel => channel.epg_id).length;
                
                // If we have all channels, calculate directly
                if (data.channels.length >= data.total) {
                    withEpgCount = data.channels.filter(channel => channel.epg_id).length;
                } else {
                    // Otherwise, make an estimate based on the sampling
                    const ratio = data.channels.filter(channel => channel.epg_id).length / data.channels.length;
                    withEpgCount = Math.round(ratio * data.total);
                }
            }
            
            const withEpgCard = document.getElementById('channelsWithEPGCard');
            if (withEpgCard) {
                withEpgCard.textContent = withEpgCount || '...';
            }
            
            // Total acestreams - use a reasonable default
            const totalAcestreamsCard = document.getElementById('totalAcestreamsCard');
            if (totalAcestreamsCard) {
                // This is an approximation as we don't have the exact count
                fetch('/api/tv-channels/unassigned-acestreams')
                    .then(response => response.json())
                    .then(unassignedData => {
                        // Add total unassigned plus a rough estimate of assigned (2 per channel)
                        const totalEstimate = (unassignedData.total || 0) + (stats.total * 2);
                        totalAcestreamsCard.textContent = totalEstimate;
                    })
                    .catch(() => {
                        totalAcestreamsCard.textContent = 'N/A';
                    });
            }
        })
        .catch(error => {
            console.error('Error updating stat cards:', error);
            // Set default values for cards in case of error
            const cards = ['totalTVChannelsCard', 'activeChannelsCard', 'channelsWithEPGCard', 'totalAcestreamsCard'];
            cards.forEach(id => {
                const card = document.getElementById(id);
                if (card) {
                    card.textContent = 'N/A';
                }
            });
        });
}

/**
 * Update pagination controls
 */
function updatePagination() {
    const pagination = document.getElementById('tvChannelsPagination');
    if (!pagination) return;
    
    // Don't show pagination if there's only one page
    if (tvChannelsState.totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let pagination_html = '';
    
    // Previous button
    pagination_html += `
        <li class="page-item ${tvChannelsState.page === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${tvChannelsState.page - 1}" aria-label="Previous">
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>
    `;
    
    // Page numbers
    const max_pages = Math.min(5, tvChannelsState.totalPages);
    let start_page = Math.max(1, tvChannelsState.page - 2);
    let end_page = Math.min(start_page + max_pages - 1, tvChannelsState.totalPages);
    
    // Adjust start_page if we're near the end
    if (end_page - start_page + 1 < max_pages) {
        start_page = Math.max(1, end_page - max_pages + 1);
    }
    
    for (let i = start_page; i <= end_page; i++) {
        pagination_html += `
            <li class="page-item ${i === tvChannelsState.page ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // Next button
    pagination_html += `
        <li class="page-item ${tvChannelsState.page === tvChannelsState.totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${tvChannelsState.page + 1}" aria-label="Next">
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>
    `;
    
    pagination.innerHTML = pagination_html;
    
    // Add event listeners to pagination links
    const page_links = pagination.querySelectorAll('.page-link');
    page_links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = parseInt(this.getAttribute('data-page'));
            if (page && page !== tvChannelsState.page) {
                tvChannelsState.page = page;
                loadTVChannels();
            }
        });
    });
}

/**
 * Delete a TV channel from the listing page
 * @param {number} channelId - The ID of the channel to delete
 */
function deleteChannel(channelId) {
    if (!confirm('Are you sure you want to delete this TV channel? This will remove all associations with acestream channels but will not delete the acestreams.')) {
        return;
    }
    
    // Show loading
    showLoading();
    
    // Call API to delete the channel
    fetch(`/api/tv-channels/${channelId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to delete TV channel');
            });
        }
        return response.json();
    })
    .then(data => {
        showAlert('success', 'TV channel deleted successfully');
        
        // Reload the channels list to reflect the deletion
        loadTVChannels();
    })
    .catch(error => {
        console.error('Error deleting TV channel:', error);
        showAlert('error', error.message || 'Error deleting TV channel');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Toggle the favorite status of a TV channel
 * @param {number} channelId - The ID of the channel to toggle favorite status
 */
function toggleChannelFavorite(channelId) {
    // Show loading
    showLoading();
    
    // Call API to toggle favorite status
    fetch(`/api/tv-channels/${channelId}/favorite`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to toggle favorite status');
            });
        }
        return response.json();
    })
    .then(result => {
        // Update local state - find the channel in the state and toggle its favorite status
        const channelIndex = tvChannelsState.channels.findIndex(c => c.id === channelId);
        if (channelIndex >= 0) {
            tvChannelsState.channels[channelIndex].is_favorite = result.is_favorite;
            
            // Update the UI without reloading the entire table
            const row = document.querySelector(`tr .channel-select-checkbox[data-channel-id="${channelId}"]`)?.closest('tr');
            if (row) {
                // Update favorite icon
                const favoriteBtn = row.querySelector('.toggle-favorite-btn');
                const favoriteIcon = favoriteBtn?.querySelector('i');
                
                if (favoriteIcon) {
                    if (result.is_favorite) {
                        favoriteIcon.className = 'bi bi-star-fill';
                        favoriteBtn.setAttribute('title', 'Remove from favorites');
                        
                        // Add favorite star to the channel name column if not present
                        let nameCell = row.cells[2];
                        let nameContent = nameCell.querySelector('div');
                        if (nameContent && !nameContent.querySelector('.bi-star-fill')) {
                            const favoriteIndicator = document.createElement('i');
                            favoriteIndicator.className = 'bi bi-star-fill text-warning me-2';
                            favoriteIndicator.title = 'Favorite';
                            nameContent.insertBefore(favoriteIndicator, nameContent.firstChild);
                        }
                    } else {
                        favoriteIcon.className = 'bi bi-star';
                        favoriteBtn.setAttribute('title', 'Add to favorites');
                        
                        // Remove favorite star from the channel name column
                        let nameCell = row.cells[2];
                        let favoriteIndicator = nameCell.querySelector('.bi-star-fill');
                        if (favoriteIndicator) {
                            favoriteIndicator.remove();
                        }
                    }
                }
            }
            
            // If we're filtering by favorites, we might need to reload the list
            if (tvChannelsState.favoritesOnly && !result.is_favorite) {
                loadTVChannels();
            }
        }
        
        showAlert('success', result.message);
    })
    .catch(error => {
        console.error('Error toggling favorite status:', error);
        showAlert('error', error.message || 'Error toggling favorite status');
    })
    .finally(() => {
        hideLoading();
    });
}