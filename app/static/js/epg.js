/**
 * EPG (Electronic Program Guide) management functionality
 */

/**
 * Load EPG sources and display them as cards
 */
async function loadEpgSources() {
    try {
        const response = await fetch('/api/epg/sources');
        const sources = await response.json();
        
        const sourcesContainer = document.getElementById('epgSourcesContainer');
        if (!sourcesContainer) return;
        
        const hasActiveSources = sources.some(source => source.enabled);

        updateButtonsState(hasActiveSources);

        if (sources.length === 0) {
            sourcesContainer.innerHTML = `
                <div class="alert alert-info">
                    No EPG source configured. Add one to enable EPG functionality.
                </div>
            `;
            return;
        }
        
        sourcesContainer.innerHTML = '';
        
        // Display sources in a balanced format
        sources.forEach(source => {
            const lastUpdated = source.last_updated ? new Date(source.last_updated).toLocaleString() : 'Never';
            const statusClass = source.enabled ? 
                (source.error_count > 0 ? 'warning' : 'success') : 
                'secondary';
            const statusText = source.enabled ? 
                (source.error_count > 0 ? 'No EPG data' : 'Active') : 
                'Disabled';
            
            // Create balanced layout
            const sourceCard = document.createElement('div');
            sourceCard.className = 'card mb-3';
            sourceCard.innerHTML = `
                <div class="card-body py-2 px-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="me-2" style="min-width: 0; flex: 1">
                            <div class="d-flex align-items-center mb-1">
                                <span class="badge bg-${statusClass} me-2">${statusText}</span>
                                <span class="text-truncate" style="max-width: 100%;" title="${source.url}">${source.url}</span>
                            </div>
                            <small class="text-muted d-block">Last updated: ${lastUpdated}</small>
                        </div>
                        <div class="d-flex flex-nowrap">
                            <button type="button" class="btn btn-sm ${source.enabled ? 'btn-warning' : 'btn-success'} me-2 toggle-source" data-id="${source.id}" title="${source.enabled ? 'Disable' : 'Enable'}">
                                ${source.enabled ? 'Disable' : 'Enable'}
                            </button>
                            <button type="button" class="btn btn-sm btn-danger delete-source" data-id="${source.id}" title="Delete">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            `;
            sourcesContainer.appendChild(sourceCard);
        });

    } catch (error) {
        console.error('Error loading EPG sources:', error);
        const sourcesContainer = document.getElementById('epgSourcesContainer');
        if (sourcesContainer) {
            sourcesContainer.innerHTML = `
                <div class="alert alert-danger">
                    Error loading EPG sources
                </div>
            `;
        }
        updateButtonsState(false);
    }
}

/**
 * Load EPG string mappings and display in table format
 */
async function loadEpgMappings() {
    try {
        const response = await fetch('/api/epg/mappings');
        const mappings = await response.json();
        
        const mappingsTable = document.getElementById('epgMappingsTable');
        if (!mappingsTable) return;
        
        if (mappings.length === 0) {
            mappingsTable.innerHTML = '<tr><td colspan="3" class="text-center">No pattern mappings configured</td></tr>';
            return;
        }
        
        mappingsTable.innerHTML = '';
        mappings.forEach(mapping => {
            const isExclusion = mapping.search_pattern.startsWith('!');
            const displayPattern = isExclusion ? 
                mapping.search_pattern.substring(1) : 
                mapping.search_pattern;
                
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    ${isExclusion ? 
                        `<span class="badge bg-danger">EXCLUDE</span> ${displayPattern}` : 
                        displayPattern}
                </td>
                <td>${isExclusion ? '---' : mapping.epg_channel_id}</td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger delete-mapping" data-id="${mapping.id}" title="Delete">
                        Delete
                    </button>
                </td>
            `;
            mappingsTable.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading EPG mappings:', error);
        const mappingsTable = document.getElementById('epgMappingsTable');
        if (mappingsTable) {
            mappingsTable.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading pattern mappings</td></tr>';
        }
    }
}

/**
 * Toggle an EPG source's enabled status
 * @param {string|Event} sourceId - Either the source ID or the click event
 */
async function toggleEpgSource(sourceIdOrElement) {
    let sourceId, isCurrentlyEnabled;
    
    sourceId = sourceIdOrElement;
    const btn = document.querySelector(`.toggle-source[data-id="${sourceId}"]`);
    isCurrentlyEnabled = btn ? btn.textContent.trim() === 'Disable' : false;
    
    try {
        // Use PUT to update the status
        await fetch(`/api/epg/sources/${sourceId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                enabled: !isCurrentlyEnabled
            })
        });
        
        // Reload sources to show updated status
        loadEpgSources();
        
        // Show feedback to the user
        showAlert('success', `EPG source ${isCurrentlyEnabled ? 'disabled' : 'enabled'} successfully`);
        
    } catch (error) {
        console.error('Error toggling EPG source:', error);
        showAlert('danger', 'Failed to toggle EPG source status');
    }
}

/**
 * Delete an EPG source from the system
 * @param {string} sourceId - The ID of the source to delete
 */
async function deleteEpgSource(sourceId) {
    const confirmed = window.confirm("Are you sure you want to delete this EPG source?");
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/epg/sources/${sourceId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete EPG source');
        }
        
        console.log('EPG source deleted successfully');
        
        // Reload sources list
        loadEpgSources();
    } catch (error) {
        console.error('Error deleting EPG source:', error);
    }
}

/**
 * Add a new EPG source with validation and duplicate checking
 */
async function addEpgSource() {
    const urlInput = document.getElementById('epgSourceUrl');
    const url = urlInput.value.trim();
    
    // Basic URL validation
    if (!url) {
        showInputError(urlInput, 'URL is required');
        return;
    }
    
    // Validate it's a proper URL
    try {
        const urlObj = new URL(url);
        if (urlObj.protocol !== 'http:' && urlObj.protocol !== 'https:') {
            showInputError(urlInput, 'URL must start with http:// or https://');
            return;
        }
    } catch (e) {
        showInputError(urlInput, 'Please enter a valid URL');
        return;
    }
    
    try {
        // Check if this URL already exists
        const existingSourcesResponse = await fetch('/api/epg/sources');
        const existingSources = await existingSourcesResponse.json();
        
        const isDuplicate = existingSources.some(source => 
            source.url.toLowerCase() === url.toLowerCase()
        );
        
        if (isDuplicate) {
            showInputError(urlInput, 'This EPG source URL already exists');
            return;
        }
        
        // If not a duplicate, proceed with adding
        const response = await fetch('/api/epg/sources', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                enabled: true
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to add EPG source');
        }
        
        // Close modal and reset form
        const modal = bootstrap.Modal.getInstance(document.getElementById('addEpgSourceModal'));
        modal.hide();
        urlInput.value = '';
        clearInputError(urlInput);
        
        // Reload sources list
        loadEpgSources();
        
        console.log('EPG source added successfully');
    } catch (error) {
        console.error('Error adding EPG source:', error);
        showInputError(urlInput, error.message || 'Error adding EPG source');
    }
}

/**
 * Helper functions for handling input validation errors
 */
function showInputError(inputElement, message) {
    // Remove previous error message if exists
    clearInputError(inputElement);
    
    // Add error class
    inputElement.classList.add('is-invalid');
    
    // Create and add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    inputElement.parentNode.appendChild(errorDiv);
}

function clearInputError(inputElement) {
    inputElement.classList.remove('is-invalid');
    
    // Remove previous error messages
    const existingError = inputElement.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Add a new EPG mapping with validation
 */
async function addEpgMapping() {
    try {
        const pattern = document.getElementById('epgSearchPattern').value;
        const isExclusion = document.getElementById('epgIsExclusion').checked;
        const channelId = isExclusion ? '' : document.getElementById('epgChannelId').value;
        
        // Validate data
        if (!pattern || (pattern.trim() === '')) {
            showAlert('danger', 'Search pattern is required');
            return;
        }
        
        if (!isExclusion && (!channelId || channelId.trim() === '')) {
            showAlert('danger', 'EPG channel ID is required for non-exclusion rules');
            return;
        }
        
        // Format data
        const formattedPattern = isExclusion ? '!' + pattern : pattern;
        
        const response = await fetch('/api/epg/mappings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                search_pattern: formattedPattern,
                epg_channel_id: channelId
            })
        });
        
        // Prevent duplicates
        if (response.status === 409) {
            showAlert('warning', 'This pattern already exists');
            return;
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to add EPG mapping');
        }
        
        // Close modal and refresh data
        const modal = bootstrap.Modal.getInstance(document.getElementById('addEpgMappingModal'));
        if (modal) {
            modal.hide();
        }
        
        // Refresh data
        loadEpgMappings();
        showAlert('success', 'EPG mapping added successfully');
    } catch (error) {
        console.error('Error adding EPG mapping:', error);
        showAlert('danger', 'Error adding EPG mapping: ' + error.message);
    }
}

/**
 * Delete an EPG mapping
 * @param {string} mappingId - The ID of the mapping to delete
 */
async function deleteEpgMapping(mappingId) {
    if (!confirm('Are you sure you want to delete this pattern mapping?')) {
        return;
    }
    
    try {
        await fetch(`/api/epg/mappings/${mappingId}`, {
            method: 'DELETE'
        });
        
        // Reload mappings list
        loadEpgMappings();
        
        console.log('Pattern mapping deleted successfully');
    } catch (error) {
        console.error('Error deleting pattern mapping:', error);
    }
}

/**
 * Refresh EPG data from all configured sources
 */
async function refreshEpgData() {
    try {
        const btn = document.getElementById('refreshEpgDataBtn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Refreshing...';
        }
        
        const response = await fetch('/api/epg/refresh', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to refresh EPG data');
        }
        
        const result = await response.json();
        
        console.log(`EPG data refreshed: ${result.channels_found} channels found`);
        
        // Reload sources list to update last_updated info
        loadEpgSources();
    } catch (error) {
        console.error('Error refreshing EPG data:', error);
    } finally {
        const btn = document.getElementById('refreshEpgDataBtn');
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Refresh EPG Channels';
        }
    }
}

/**
 * Update channel EPG data using the configured mapping rules
 * Includes options for respecting existing data and cleaning unmatched channels
 */
async function updateChannelsEpg() {
    try {
        showLoading();
        
        // Disable the button and change text to show progress
        const btn = document.getElementById('updateChannelsEpgBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Updating...';
        }

        // Read state from both checkboxes
        const respectExisting = document.getElementById('updateRespectExisting')?.checked || false;
        const cleanUnmatched = document.getElementById('updateCleanUnmatched')?.checked || false;
        
        console.log('Update channels options:', {
            respect_existing: respectExisting,
            clean_unmatched: cleanUnmatched
        });
        
        const response = await fetch('/api/epg/update-channels', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                respect_existing: respectExisting,
                clean_unmatched: cleanUnmatched
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update channels with EPG data');
        }
        
        const result = await response.json();
        
        // Use the new stats format
        const stats = result.stats;
        
        // Display message with the new format
        showAlert('success', `EPG update completed. 
            Updated: ${stats.updated || 0}, 
            Cleaned: ${stats.cleaned || 0}, 
            Locked: ${stats.locked || 0}, 
            Excluded: ${stats.excluded || 0}`);
        
        // Update UI if needed
        if (typeof refreshData === 'function') {
            await refreshData();
        }
        
        return result;
    } catch (error) {
        console.error('Error updating channels with EPG data:', error);
        showAlert('danger', 'Error updating channels with EPG data: ' + error.message);
        throw error;
    } finally {
        hideLoading();

        // Restore button state
        const btn = document.getElementById('updateChannelsEpgBtn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Update EPG Mappings';
        }
    }
}

/**
 * Load EPG channel options for datalist
 * Caches results to avoid unnecessary API calls
 */
async function loadEpgChannelOptions() {
    try {
        // If we haven't cached the data yet, fetch it
        if (!window.epgChannelsList || window.epgChannelsList.length === 0) {
            // Get the available channel IDs
            const channelResponse = await fetch('/api/epg/channels');
            if (!channelResponse.ok) {
                throw new Error('Failed to fetch EPG channel IDs');
            }
            
            const channelData = await channelResponse.json();
            window.epgChannelsList = channelData;
        }
        
        // Populate the datalist with options
        const datalist = document.getElementById('epgChannelOptions');
        if (datalist) {
            datalist.innerHTML = '';
            window.epgChannelsList.forEach(channel => {
                const option = document.createElement('option');
                option.value = channel.id;
                option.text = channel.name || channel.id;
                datalist.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading EPG channel options:', error);
    }
}

/**
 * Automatically scan and match channels with EPG data based on similarity
 * Configurable with threshold and options for handling existing data
 */
async function autoScanChannels() {
    try {
        showLoading();
        
        // Get slider value, converted to decimal (0.5-0.95)
        const thresholdSlider = document.getElementById('similarityThreshold');
        const threshold = thresholdSlider ? (parseInt(thresholdSlider.value) / 100) : 0.8;
        
        // Read checkbox states
        const cleanUnmatched = document.getElementById('cleanUnmatched')?.checked || false;
        const respectExisting = document.getElementById('respectExisting')?.checked || false;
        
        console.log('Auto-scan options:', {
            threshold: threshold,
            cleanUnmatched: cleanUnmatched,
            respectExisting: respectExisting
        });
        
        const response = await fetch('/api/epg/auto-scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                threshold: threshold,
                clean_unmatched: cleanUnmatched,
                respect_existing: respectExisting
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to perform auto-scan');
        }
        
        const result = await response.json();
        
        // Display results
        showAlert('success', `Auto-scan completed successfully. 
            Processed: ${result.total} channels, 
            Matched: ${result.matched}, 
            Cleaned: ${result.cleaned || 0},
            Skipped: ${result.skipped || 0} (already had EPG data)`
        );
        
        // Update channel list if the function exists
        if (typeof refreshData === 'function') {
            await refreshData();
        }
    } catch (error) {
        console.error('Error during auto-scan:', error);
        showAlert('danger', 'Error during auto-scan: ' + error.message);
    } finally {
        hideLoading();
        
        // Restore button state
        const btn = document.getElementById('scanChannelsBtn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-search"></i> Scan Channels';
        }
    }
}

/**
 * Initialize all EPG components and event handlers
 */
function initializeEpgComponents() {
    // Load initial data
    loadEpgSources();
    loadEpgMappings();
    
    // Configure threshold slider
    const thresholdSlider = document.getElementById('similarityThreshold');
    const thresholdValue = document.getElementById('thresholdValue');
    if (thresholdSlider && thresholdValue) {
        // Initial configuration
        thresholdValue.textContent = `${thresholdSlider.value}%`;
        
        // Change listener
        thresholdSlider.addEventListener('input', function() {
            thresholdValue.textContent = `${this.value}%`;
        });
    }
    
    // Configure exclusion checkbox
    const exclusionCheckbox = document.getElementById('epgIsExclusion');
    const channelIdContainer = document.getElementById('epgChannelIdContainer');
    if (exclusionCheckbox && channelIdContainer) {
        exclusionCheckbox.addEventListener('change', function() {
            const channelIdField = document.getElementById('epgChannelId');
            if (this.checked) {
                channelIdContainer.style.display = 'none';
                if (channelIdField) channelIdField.removeAttribute('required');
            } else {
                channelIdContainer.style.display = 'block';
                if (channelIdField) channelIdField.setAttribute('required', 'required');
            }
        });
    }
    
    // Add event listener for the search pattern input
    const searchPatternInput = document.getElementById('epgSearchPattern');
    if (searchPatternInput) {
        searchPatternInput.addEventListener('input', debounce(previewMatchingChannels, 300));
    }
    
    // Add event listener for the exclusion checkbox to update preview when changed
    if (exclusionCheckbox) {
        exclusionCheckbox.addEventListener('change', () => {
            const searchPattern = document.getElementById('epgSearchPattern');
            if (searchPattern && searchPattern.value) {
                previewMatchingChannels();
            }
        });
    }
    
    // Configure global event delegation (once)
    document.addEventListener('click', function(event) {
        // EPG source events
        if (event.target.closest('.toggle-source')) {
            const btn = event.target.closest('.toggle-source');
            toggleEpgSource(btn.dataset.id);
            event.preventDefault();
        }
        else if (event.target.closest('.delete-source')) {
            const btn = event.target.closest('.delete-source');
            deleteEpgSource(btn.dataset.id);
            event.preventDefault();
        }
        
        // EPG mapping events
        else if (event.target.closest('.delete-mapping')) {
            const btn = event.target.closest('.delete-mapping');
            deleteEpgMapping(btn.dataset.id);
            event.preventDefault();
        }
        
        // Action buttons
        else if (event.target.id === 'addEpgSourceBtn') {
            const modal = new bootstrap.Modal(document.getElementById('addEpgSourceModal'));
            modal.show();
        }
        else if (event.target.id === 'saveEpgSourceBtn') {
            addEpgSource();
        }
        else if (event.target.id === 'addEpgMappingBtn') {
            // Reset form when opening
            const mappingForm = document.getElementById('epgMappingForm');
            if (mappingForm) mappingForm.reset();
            
            // Show channel ID container by default
            const channelIdContainer = document.getElementById('epgChannelIdContainer');
            if (channelIdContainer) channelIdContainer.style.display = 'block';
            
            // Reset required attribute
            const channelIdField = document.getElementById('epgChannelId');
            if (channelIdField) channelIdField.setAttribute('required', 'required');
            
            // Reset preview container to default state
            const previewContainer = document.getElementById('matchingChannelsPreview');
            const matchCount = document.getElementById('matchCount');
            if (previewContainer) {
                previewContainer.innerHTML = `
                    <div class="p-3 text-center text-muted">
                        <small>Start typing to see matching channels</small>
                    </div>
                `;
            }
            if (matchCount) {
                matchCount.textContent = '0';
            }
            
            const modal = new bootstrap.Modal(document.getElementById('addEpgMappingModal'));
            modal.show();
            
            // Load channel options
            loadEpgChannelOptions();
        }
        else if (event.target.id === 'saveEpgMappingBtn') {
            addEpgMapping();
        }
        else if (event.target.id === 'refreshEpgDataBtn') {
            refreshEpgData(event.target);
        }
        else if (event.target.id === 'updateChannelsEpgBtn') {
            updateChannelsEpg();
        }
        else if (event.target.id === 'scanChannelsBtn') {
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Scanning...';
            autoScanChannels();
        }
    });
}

/**
 * Preview channels that match the current search pattern
 * Considers existing exclusion rules and protected status
 */
async function previewMatchingChannels() {
    const searchPattern = document.getElementById('epgSearchPattern').value.trim();
    const isExclusion = document.getElementById('epgIsExclusion')?.checked || false;
    const previewContainer = document.getElementById('matchingChannelsPreview');
    const matchCount = document.getElementById('matchCount');
    
    if (!previewContainer) return;
    
    // If no pattern, show default message
    if (!searchPattern) {
        previewContainer.innerHTML = `
            <div class="p-3 text-center text-muted">
                <small>Start typing to see matching channels</small>
            </div>
        `;
        matchCount.textContent = '0';
        return;
    }
    
    // Show loading indicator
    previewContainer.innerHTML = `
        <div class="p-3 text-center">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">Searching channels...</span>
        </div>
    `;
    
    try {
        // Get existing exclusion rules
        const mappingsResponse = await fetch('/api/epg/mappings');
        const mappings = await mappingsResponse.json();
        const exclusionPatterns = mappings
            .filter(m => m.search_pattern.startsWith('!'))
            .map(m => m.search_pattern.substring(1).toLowerCase());
        
        // Get all channels
        const response = await fetch('/api/channels');
        const channels = await response.json();
        
        // Filter channels based on pattern and existing exclusion rules
        const pattern = new RegExp(escapeRegExp(searchPattern), 'i');
        const matchingChannels = channels.filter(channel => {
            // Skip if channel name is missing
            if (!channel.name) return false;
            
            // Check if this channel matches the current pattern
            const matchesPattern = pattern.test(channel.name);
            if (!matchesPattern) return false;
            
            // If this is not an exclusion rule, check if channel is already excluded
            if (!isExclusion) {
                // Check if any existing exclusion patterns match this channel
                const isAlreadyExcluded = exclusionPatterns.some(exPattern => 
                    channel.name.toLowerCase().includes(exPattern)
                );
                
                if (isAlreadyExcluded) {
                    return false; // Skip channels already excluded
                }
            }
            
            return true;
        });
        
        // Update counter
        matchCount.textContent = matchingChannels.length.toString();
        
        // Limit to 15 results for performance
        const limitedResults = matchingChannels.slice(0, 15);
        
        // If no matches
        if (limitedResults.length === 0) {
            previewContainer.innerHTML = `
                <div class="p-3 text-center text-muted">
                    <small>No channels match this pattern</small>
                </div>
            `;
            return;
        }
        
        // Generate HTML for each channel
        const listItems = limitedResults.map(channel => {
            // Highlight matching part
            const highlightedName = (channel.name || '').replace(
                new RegExp(`(${escapeRegExp(searchPattern)})`, 'gi'),
                '<span class="bg-warning text-dark">$1</span>'
            );
            
            // Determine EPG status with better visual indication
            let epgStatus = '';
            
            if (channel.epg_update_protected) {
                epgStatus = '<span class="ms-2 badge bg-purple">Protected</span>';
            } else if (channel.tvg_id && channel.tvg_name) {
                epgStatus = '<span class="ms-2 badge bg-success">EPG</span>';
            }
            
            return `
                <div class="list-group-item list-group-item-action py-2 px-3 border-start-0 border-end-0">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <div class="text-truncate" style="max-width: 350px;">${highlightedName}</div>
                            <small class="text-muted">${channel.id}</small>
                        </div>
                        ${epgStatus}
                    </div>
                </div>
            `;
        });
        
        // Show more indicator if there are more results
        const moreResults = matchingChannels.length > limitedResults.length ? 
            `<div class="list-group-item text-center text-muted py-2"><small>+ ${matchingChannels.length - limitedResults.length} more channels</small></div>` : '';
        
        // Update container
        previewContainer.innerHTML = `
            <div class="list-group list-group-flush">
                ${listItems.join('')}
                ${moreResults}
            </div>
        `;
        
    } catch (error) {
        console.error('Error previewing matching channels:', error);
        previewContainer.innerHTML = `
            <div class="p-3 text-center text-danger">
                <small>Error loading channel preview</small>
            </div>
        `;
    }
}

/**
 * Escape special characters in a string for use in RegExp
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Debounce function to limit how often a function runs
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Initialize everything when the DOM is ready
document.addEventListener('DOMContentLoaded', initializeEpgComponents);

/**
 * Update buttons state and show alerts when no active sources
 * @param {boolean} hasActiveSources - Whether there are any active EPG sources
 */
function updateButtonsState(hasActiveSources) {
    // Buttons to disable
    const scanChannelsBtn = document.getElementById('scanChannelsBtn');
    const updateChannelsEpgBtn = document.getElementById('updateChannelsEpgBtn');
    const addEpgMappingBtn = document.getElementById('addEpgMappingBtn'); // Added

    // Alert containers
    const mappingsTabContent = document.getElementById('mappings');
    const autoScanTabContent = document.getElementById('automapping');
    
    if (!hasActiveSources) {
        // Disable buttons
        if (scanChannelsBtn) {
            scanChannelsBtn.disabled = true;
            scanChannelsBtn.title = 'Requires active EPG sources';
        }
        
        if (updateChannelsEpgBtn) {
            updateChannelsEpgBtn.disabled = true;
            updateChannelsEpgBtn.title = 'Requires active EPG sources';
        }

        if (addEpgMappingBtn) {
            addEpgMappingBtn.disabled = true;
            addEpgMappingBtn.title = 'Requires active EPG sources';
        }
        
        // Add alert if not exists
        if (mappingsTabContent) {
            const existingAlert = mappingsTabContent.querySelector('.epg-no-sources-alert');
            if (!existingAlert) {
                const alert = document.createElement('div');
                alert.className = 'alert alert-warning mt-3 epg-no-sources-alert';
                alert.innerHTML = '<strong>No active EPG sources!</strong> You need to add and enable at least one EPG source to use mapping functions.';
                mappingsTabContent.insertBefore(alert, mappingsTabContent.firstChild);
            }
        }
        
        if (autoScanTabContent) {
            const existingAlert = autoScanTabContent.querySelector('.epg-no-sources-alert');
            if (!existingAlert) {
                const alert = document.createElement('div');
                alert.className = 'alert alert-warning mt-3 epg-no-sources-alert';
                alert.innerHTML = '<strong>No active EPG sources!</strong> You need to add and enable at least one EPG source to use auto-scan functionality.';
                autoScanTabContent.insertBefore(alert, autoScanTabContent.firstChild);
            }
        }
    } else {
        // Enable buttons
        if (scanChannelsBtn) {
            scanChannelsBtn.disabled = false;
            scanChannelsBtn.title = '';
        }
        
        if (updateChannelsEpgBtn) {
            updateChannelsEpgBtn.disabled = false;
            updateChannelsEpgBtn.title = '';
        }

        if (addEpgMappingBtn) {
            addEpgMappingBtn.disabled = false;
            addEpgMappingBtn.title = '';
        }
        
        // Remove alerts if exists
        document.querySelectorAll('.epg-no-sources-alert').forEach(alert => {
            alert.remove();
        });
    }
}
// From core.js
/**
 * Core functionality for the Acestream Scraper application
 */

// Show alert message to the user
function showAlert(type, message, duration = 5000) {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(alertContainer);
    }
    
    // Generate a unique ID for this alert
    const alertId = 'alert-' + Date.now();
    
    // Create the alert element
    const alertHTML = `
        <div id="${alertId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Add the alert to the container
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // Initialize and show the toast
    const toastElement = document.getElementById(alertId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });
    toast.show();
    
    // Remove the toast from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Show loading spinner
function showLoading() {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.style.display = 'inline-block';
    }
}

// Hide loading spinner
function hideLoading() {
    const loadingElement = document.getElementById('loading');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}