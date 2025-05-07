/**
 * EPG Management functionality for Acestream Scraper
 */

// EPG page state
const epgState = {
    sources: [],
    mappings: [],
    epgChannels: [],
    currentPage: 1,
    itemsPerPage: 20,
    totalChannels: 0,
    selectedEpgChannel: null
};

// State management for EPG channels pagination
const epgChannelsState = {
    currentPage: 1,
    perPage: 20,
    searchTerm: ''
};

// Initialize when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('EPG management page initializing...');
    
    // Load data
    loadEpgData();
    
    // Set up button handlers
    document.getElementById('addEpgSourceBtn').addEventListener('click', openAddSourceModal);
    document.getElementById('saveEpgSourceBtn').addEventListener('click', saveEpgSource);
    document.getElementById('refreshEpgDataBtn').addEventListener('click', refreshEpgData);
    
    document.getElementById('addEpgMappingBtn').addEventListener('click', openAddMappingModal);
    document.getElementById('saveEpgMappingBtn').addEventListener('click', saveEpgMapping);
    document.getElementById('updateChannelsEpgBtn').addEventListener('click', updateChannelsEpg);
    
    document.getElementById('scanChannelsBtn').addEventListener('click', scanChannels);
    document.getElementById('searchEpgChannelsBtn').addEventListener('click', searchEpgChannels);
    
    // Set up event for similarity threshold slider
    const thresholdSlider = document.getElementById('similarityThreshold');
    if (thresholdSlider) {
        thresholdSlider.addEventListener('input', function() {
            document.getElementById('thresholdValue').textContent = this.value + '%';
        });
    }
    
    // Set up search input for EPG channels
    const searchInput = document.getElementById('epgChannelSearch');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchEpgChannels();
            }
        });
    }
    
    // Initialize the per page dropdown listener
    const perPageSelect = document.getElementById('epgChannelsPerPage');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            loadEpgChannels(1); // Reset to first page when changing items per page
        });
    }
    
    // Set up live search for EPG mapping pattern
    const epgSearchPattern = document.getElementById('epgSearchPattern');
    if (epgSearchPattern) {
        epgSearchPattern.addEventListener('input', debounce(previewMatchingChannels, 300));
    }
    
    // Set up exclusion checkbox to toggle EPG channel ID field
    const exclusionCheckbox = document.getElementById('epgIsExclusion');
    if (exclusionCheckbox) {
        exclusionCheckbox.addEventListener('change', function() {
            const epgChannelIdContainer = document.getElementById('epgChannelIdContainer');
            if (this.checked) {
                epgChannelIdContainer.style.display = 'none';
            } else {
                epgChannelIdContainer.style.display = 'block';
            }
        });
    }
});

/**
 * Load all EPG-related data
 */
async function loadEpgData() {
    showLoading();
    try {
        // Load EPG sources
        await loadEpgSources();
        
        // Load EPG mappings
        await loadEpgMappings();
        
        // Load EPG channels
        await loadEpgChannels();
        
        // Update statistics
        updateEpgStatistics();
    } catch (error) {
        console.error('Error loading EPG data:', error);
        showAlert('danger', 'Failed to load EPG data');
    } finally {
        hideLoading();
    }
}

/**
 * Load EPG sources
 */
async function loadEpgSources() {
    try {
        const response = await fetch('/api/epg/sources');
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        epgState.sources = await response.json();
        
        // Update UI
        const container = document.getElementById('epgSourcesContainer');
        
        if (!container || !epgState.sources || epgState.sources.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No EPG sources found. Add an EPG source to get started.
                </div>
            `;
            return;
        }
        
        container.innerHTML = epgState.sources.map(source => {
            const lastUpdated = source.last_updated ? new Date(source.last_updated).toLocaleString() : 'Never';
            const statusClass = source.error_count > 0 ? 'text-danger' : 'text-success';
            const statusIcon = source.error_count > 0 ? 'bi-x-circle' : 'bi-check-circle';
            const statusMessage = source.error_count > 0 
                ? `Error: ${source.last_error || 'Unknown error'}`
                : 'OK';
            
            return `
                <div class="card mb-2">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">${source.url}</h6>
                                <div class="small">
                                    <div class="text-muted">Last updated: ${lastUpdated}</div>
                                    <div class="${statusClass}">
                                        <i class="bi ${statusIcon} me-1"></i>
                                        Status: ${statusMessage}
                                    </div>
                                </div>
                            </div>
                            <div class="form-check form-switch me-2">
                                <input class="form-check-input" type="checkbox" id="sourceEnabled${source.id}" 
                                       ${source.enabled ? 'checked' : ''} 
                                       onchange="toggleEpgSource(${source.id}, this.checked)">
                                <label class="form-check-label" for="sourceEnabled${source.id}">
                                    ${source.enabled ? 'Enabled' : 'Disabled'}
                                </label>
                            </div>
                            <button class="btn btn-danger btn-sm" onclick="deleteEpgSource(${source.id})">
                                <i class="bi bi-trash me-1"></i>
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading EPG sources:', error);
        throw error;
    }
}

/**
 * Load EPG mappings
 */
async function loadEpgMappings() {
    try {
        const response = await fetch('/api/epg/mappings');
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        epgState.mappings = await response.json();
        
        // Update UI
        const table = document.getElementById('epgMappingsTable');
        
        if (!table || !epgState.mappings || epgState.mappings.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center">
                        <div class="alert alert-info m-0 p-2">
                            <i class="bi bi-info-circle me-2"></i>
                            No EPG mappings found. Add a mapping to assign EPG data to channels.
                        </div>
                    </td>
                </tr>
            `;
            return;
        }
        
        table.innerHTML = epgState.mappings.map(mapping => {
            const isExclusion = mapping.search_pattern.startsWith('!');
            const displayPattern = isExclusion ? 
                mapping.search_pattern.substring(1) : 
                mapping.search_pattern;
            
            return `
                <tr>
                    <td>
                        ${isExclusion ? 
                            `<span class="badge bg-warning me-1">Exclude</span> ${displayPattern}` : 
                            displayPattern}
                    </td>
                    <td>${isExclusion ? 'N/A' : mapping.epg_channel_id}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-danger" onclick="deleteEpgMapping(${mapping.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading EPG mappings:', error);
        throw error;
    }
}

/**
 * Load EPG channels with pagination and search
 */
async function loadEpgChannels(page = 1, searchTerm = '') {
    // Update state
    epgChannelsState.currentPage = page;
    if (searchTerm !== undefined) {
        epgChannelsState.searchTerm = searchTerm;
    }
    
    const tableBody = document.getElementById('epgChannelsTable');
    if (!tableBody) return;
    
    // Show loading state
    tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading EPG channels...</span>
            </td>
        </tr>
    `;
    
    try {
        // Get the per_page value from the dropdown
        const perPageSelect = document.getElementById('epgChannelsPerPage');
        if (perPageSelect) {
            epgChannelsState.perPage = parseInt(perPageSelect.value);
        }
        
        // Build URL with params
        const params = new URLSearchParams({
            page: epgChannelsState.currentPage,
            per_page: epgChannelsState.perPage
        });
        
        if (epgChannelsState.searchTerm) {
            params.append('search', epgChannelsState.searchTerm);
        }
        
        // Fetch EPG channels with search and pagination
        const response = await fetch(`/api/epg/channels?${params.toString()}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error('Failed to load EPG channels');
        }
        
        if (!data.channels || !data.channels.length) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">
                        <div class="alert alert-info mb-0">
                            No EPG channels found matching your criteria.
                        </div>
                    </td>
                </tr>
            `;
            return;
        }
        
        // Render channels
        tableBody.innerHTML = data.channels.map(channel => {
            const logoHtml = channel.icon ? 
                `<img src="${channel.icon}" alt="Channel Logo" class="img-fluid" style="max-height: 30px;">` : 
                '<span class="text-muted"><i class="bi bi-tv"></i></span>';
                
            const sourceDisplay = channel.source_url || 'Unknown Source';
            const language = channel.language || 'Unknown';
            
            return `
                <tr class="cursor-pointer" 
                    onclick="showProgramSchedule('${channel.id}')">
                    <td>${logoHtml}</td>
                    <td>${channel.id}</td>
                    <td>${channel.name}</td>
                    <td><small class="text-muted">${sourceDisplay}</small></td>
                    <td>${language}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary" 
                                    onclick="event.stopPropagation(); copyEpgId('${channel.id}')">
                                <i class="bi bi-clipboard"></i>
                            </button>
                            <button class="btn btn-outline-success create-tv-channel-btn"
                                    onclick="event.stopPropagation(); openCreateTVChannelModal('${channel.id}', '${channel.name.replace(/'/g, "\\'")}')">
                                <i class="bi bi-tv"></i> Create TV Channel
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Update pagination
        updateEpgChannelsPagination(data.page, data.total_pages);
        
    } catch (error) {
        console.error('Error loading EPG channels:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Failed to load EPG channels: ${error.message}
                </td>
            </tr>
        `;
    }
}

/**
 * Update pagination controls for EPG channels
 */
function updateEpgChannelsPagination(currentPage, totalPages) {
    const pagination = document.getElementById('epgChannelsPagination');
    if (!pagination) return;
    
    // Clear existing pagination
    pagination.innerHTML = '';
    
    if (totalPages <= 1) {
        return; // No pagination needed
    }
    
    // Previous button
    const prevItem = document.createElement('li');
    prevItem.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevItem.innerHTML = `
        <a class="page-link" href="#" aria-label="Previous" ${currentPage > 1 ? `onclick="loadEpgChannels(${currentPage - 1}); return false;"` : ''}>
            <span aria-hidden="true">&laquo;</span>
        </a>
    `;
    pagination.appendChild(prevItem);
    
    // Page numbers
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // First page
    if (startPage > 1) {
        const firstItem = document.createElement('li');
        firstItem.className = 'page-item';
        firstItem.innerHTML = `
            <a class="page-link" href="#" onclick="loadEpgChannels(1); return false;">1</a>
        `;
        pagination.appendChild(firstItem);
        
        if (startPage > 2) {
            const ellipsisItem = document.createElement('li');
            ellipsisItem.className = 'page-item disabled';
            ellipsisItem.innerHTML = '<a class="page-link" href="#">...</a>';
            pagination.appendChild(ellipsisItem);
        }
    }
    
    // Visible pages
    for (let i = startPage; i <= endPage; i++) {
        const item = document.createElement('li');
        item.className = `page-item ${i === currentPage ? 'active' : ''}`;
        item.innerHTML = `
            <a class="page-link" href="#" onclick="loadEpgChannels(${i}); return false;">${i}</a>
        `;
        pagination.appendChild(item);
    }
    
    // Last page
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsisItem = document.createElement('li');
            ellipsisItem.className = 'page-item disabled';
            ellipsisItem.innerHTML = '<a class="page-link" href="#">...</a>';
            pagination.appendChild(ellipsisItem);
        }
        
        const lastItem = document.createElement('li');
        lastItem.className = 'page-item';
        lastItem.innerHTML = `
            <a class="page-link" href="#" onclick="loadEpgChannels(${totalPages}); return false;">${totalPages}</a>
        `;
        pagination.appendChild(lastItem);
    }
    
    // Next button
    const nextItem = document.createElement('li');
    nextItem.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextItem.innerHTML = `
        <a class="page-link" href="#" aria-label="Next" ${currentPage < totalPages ? `onclick="loadEpgChannels(${currentPage + 1}); return false;"` : ''}>
            <span aria-hidden="true">&raquo;</span>
        </a>
    `;
    pagination.appendChild(nextItem);
}

/**
 * Update EPG statistics
 */
function updateEpgStatistics() {
    // Update sources count
    const sourcesCount = document.getElementById('epgSourcesCount');
    if (sourcesCount) {
        sourcesCount.textContent = epgState.sources.length;
    }
    
    // Update channels count
    const channelsCount = document.getElementById('epgChannelsCount');
    if (channelsCount) {
        channelsCount.textContent = epgState.epgChannels.length;
    }
    
    // Update mappings count
    const mappingsCount = document.getElementById('mappingRulesCount');
    if (mappingsCount) {
        mappingsCount.textContent = epgState.mappings.length;
    }
    
    // Update last update time
    const lastUpdateTime = document.getElementById('lastUpdateTime');
    if (lastUpdateTime) {
        // Find the most recent update from sources
        let latestUpdate = null;
        epgState.sources.forEach(source => {
            if (source.last_updated) {
                const updateDate = new Date(source.last_updated);
                if (!latestUpdate || updateDate > latestUpdate) {
                    latestUpdate = updateDate;
                }
            }
        });
        
        lastUpdateTime.textContent = latestUpdate ? latestUpdate.toLocaleTimeString() : 'Never';
    }
}

/**
 * Open the add source modal
 */
function openAddSourceModal() {
    // Reset form
    document.getElementById('epgSourceUrl').value = '';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addEpgSourceModal'));
    modal.show();
}

/**
 * Save a new EPG source
 */
async function saveEpgSource() {
    const url = document.getElementById('epgSourceUrl').value.trim();
    
    if (!url) {
        showAlert('warning', 'Please enter a valid URL');
        return;
    }
    
    // Validate URL format
    if (!isValidUrl(url)) {
        showAlert('warning', 'Please enter a valid URL starting with http:// or https://');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/epg/sources', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || `API returned ${response.status}: ${response.statusText}`);
        }
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('addEpgSourceModal')).hide();
        
        // Reload data
        await loadEpgSources();
        
        // Show success message
        showAlert('success', 'EPG source added successfully');
        
    } catch (error) {
        console.error('Error adding EPG source:', error);
        showAlert('danger', error.message || 'Failed to add EPG source');
    } finally {
        hideLoading();
    }
}

/**
 * Check if URL is valid
 */
function isValidUrl(url) {
    try {
        new URL(url);
        return url.startsWith('http://') || url.startsWith('https://');
    } catch (e) {
        return false;
    }
}

/**
 * Toggle EPG source enabled status
 */
async function toggleEpgSource(id, enabled) {
    try {
        showLoading();
        
        const response = await fetch(`/api/epg/sources/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled })
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        // Update label
        const label = document.querySelector(`label[for="sourceEnabled${id}"]`);
        if (label) {
            label.textContent = enabled ? 'Enabled' : 'Disabled';
        }
        
        // Update local data
        const source = epgState.sources.find(s => s.id === id);
        if (source) {
            source.enabled = enabled;
        }
        
    } catch (error) {
        console.error('Error toggling EPG source:', error);
        showAlert('danger', 'Failed to update EPG source status');
    } finally {
        hideLoading();
    }
}

/**
 * Delete an EPG source
 */
async function deleteEpgSource(id) {
    if (!confirm('Are you sure you want to delete this EPG source?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`/api/epg/sources/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        // Reload data
        await loadEpgSources();
        
        // Show success message
        showAlert('success', 'EPG source deleted successfully');
        
    } catch (error) {
        console.error('Error deleting EPG source:', error);
        showAlert('danger', 'Failed to delete EPG source');
    } finally {
        hideLoading();
    }
}

/**
 * Refresh EPG data from all sources
 */
async function refreshEpgData() {
    try {
        showLoading();
        
        const response = await fetch('/api/epg/refresh', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Reload everything
        await loadEpgData();
        
        // Show success message
        showAlert('success', `EPG data refreshed successfully: ${data.channels_found} channels found`);
        
    } catch (error) {
        console.error('Error refreshing EPG data:', error);
        showAlert('danger', 'Failed to refresh EPG data');
    } finally {
        hideLoading();
    }
}

/**
 * Open the add mapping modal
 */
function openAddMappingModal() {
    // Reset form
    document.getElementById('epgSearchPattern').value = '';
    document.getElementById('epgChannelId').value = '';
    document.getElementById('epgIsExclusion').checked = false;
    
    // Reset preview
    document.getElementById('matchCount').textContent = '0';
    document.getElementById('matchingChannelsPreview').innerHTML = `
        <div class="p-3 text-center text-muted">
            <small>Start typing to see matching channels</small>
        </div>
    `;
    
    // Show channel ID field (hidden for exclusion rules)
    document.getElementById('epgChannelIdContainer').style.display = 'block';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addEpgMappingModal'));
    modal.show();
}

/**
 * Preview channels that match the search pattern
 */
async function previewMatchingChannels() {
    const searchPattern = document.getElementById('epgSearchPattern').value.trim();
    
    if (!searchPattern) {
        document.getElementById('matchCount').textContent = '0';
        document.getElementById('matchingChannelsPreview').innerHTML = `
            <div class="p-3 text-center text-muted">
                <small>Start typing to see matching channels</small>
            </div>
        `;
        return;
    }
    
    try {
        // Search channels containing the pattern
        const response = await fetch(`/api/channels?search=${encodeURIComponent(searchPattern)}&limit=10`);
        const channels = await response.json();
        
        // Update count
        document.getElementById('matchCount').textContent = channels.length;
        
        // Update preview
        const previewContainer = document.getElementById('matchingChannelsPreview');
        
        if (channels.length === 0) {
            previewContainer.innerHTML = `
                <div class="p-3 text-center text-muted">
                    <small>No channels match this pattern</small>
                </div>
            `;
            return;
        }
        
        previewContainer.innerHTML = channels.map(channel => `
            <div class="p-2 border-bottom">
                <strong>${channel.name}</strong>
                <div class="small text-muted">${channel.id}</div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error previewing matching channels:', error);
    }
}

/**
 * Save a new EPG mapping
 */
async function saveEpgMapping() {
    const searchPattern = document.getElementById('epgSearchPattern').value.trim();
    const isExclusion = document.getElementById('epgIsExclusion').checked;
    const epgChannelId = isExclusion ? '' : document.getElementById('epgChannelId').value.trim();
    
    if (!searchPattern) {
        showAlert('warning', 'Please enter a search pattern');
        return;
    }
    
    if (!isExclusion && !epgChannelId) {
        showAlert('warning', 'Please enter an EPG channel ID');
        return;
    }
    
    try {
        showLoading();
        
        // Format the search pattern with an exclamation mark prefix for exclusion rules
        const formattedPattern = isExclusion ? `!${searchPattern}` : searchPattern;
        
        const response = await fetch('/api/epg/mappings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                search_pattern: formattedPattern,
                epg_channel_id: epgChannelId
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || `API returned ${response.status}: ${response.statusText}`);
        }
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('addEpgMappingModal')).hide();
        
        // Reload mappings
        await loadEpgMappings();
        
        // Show success message
        showAlert('success', 'EPG mapping added successfully');
        
    } catch (error) {
        console.error('Error adding EPG mapping:', error);
        showAlert('danger', error.message || 'Failed to add EPG mapping');
    } finally {
        hideLoading();
    }
}

/**
 * Delete an EPG mapping
 */
async function deleteEpgMapping(id) {
    if (!confirm('Are you sure you want to delete this EPG mapping?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`/api/epg/mappings/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        // Reload mappings
        await loadEpgMappings();
        
        // Show success message
        showAlert('success', 'EPG mapping deleted successfully');
        
    } catch (error) {
        console.error('Error deleting EPG mapping:', error);
        showAlert('danger', 'Failed to delete EPG mapping');
    } finally {
        hideLoading();
    }
}

/**
 * Update all channels with EPG data
 */
async function updateChannelsEpg() {
    try {
        showLoading();
        
        const respectExisting = document.getElementById('updateRespectExisting').checked;
        const cleanUnmatched = document.getElementById('updateCleanUnmatched').checked;
        
        const response = await fetch('/api/epg/update-channels', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                respect_existing: respectExisting,
                clean_unmatched: cleanUnmatched
            })
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Show success message
        showAlert('success', `EPG data updated successfully: ${data.stats.updated} channels updated, ${data.stats.cleaned} channels cleaned`);
        
    } catch (error) {
        console.error('Error updating EPG data:', error);
        showAlert('danger', 'Failed to update EPG data');
    } finally {
        hideLoading();
    }
}

/**
 * Automatically scan channels and map them to EPG data
 */
async function scanChannels() {
    try {
        showLoading();
        
        const threshold = parseInt(document.getElementById('similarityThreshold').value) / 100;
        const cleanUnmatched = document.getElementById('cleanUnmatched').checked;
        const respectExisting = document.getElementById('respectExisting').checked;
        
        const response = await fetch('/api/epg/auto-scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                threshold,
                clean_unmatched: cleanUnmatched,
                respect_existing: respectExisting
            })
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Show success message
        showAlert('success', `Auto-mapping completed: ${data.matched} channels matched, ${data.cleaned} channels cleaned`);
        
    } catch (error) {
        console.error('Error auto-scanning channels:', error);
        showAlert('danger', 'Failed to auto-scan channels');
    } finally {
        hideLoading();
    }
}

/**
 * Copy EPG channel ID to clipboard
 */
function copyEpgId(id) {
    // Create temporary input
    const input = document.createElement('input');
    input.value = id;
    document.body.appendChild(input);
    
    // Select and copy
    input.select();
    document.execCommand('copy');
    
    // Remove temporary input
    document.body.removeChild(input);
    
    // Show feedback
    showAlert('info', 'EPG channel ID copied to clipboard');
}

/**
 * Search EPG channels
 */
function searchEpgChannels() {
    const searchTerm = document.getElementById('epgChannelSearch').value.trim();
    loadEpgChannels(1, searchTerm); // Reset to first page when searching
}

/**
 * Show program schedule for a selected EPG channel
 */
function showProgramSchedule(channelId) {
    // Find the channel
    const channel = epgState.epgChannels.find(c => c.id === channelId);
    if (!channel) return;
    
    // Store selected channel
    epgState.selectedEpgChannel = channel;
    
    // Update UI
    const container = document.getElementById('programScheduleContainer');
    const channelName = document.getElementById('selectedChannelName');
    const scheduleTable = document.getElementById('programScheduleTable');
    
    if (!container || !channelName || !scheduleTable) return;
    
    // Show container
    container.classList.remove('d-none');
    
    // Set channel name
    channelName.innerHTML = `
        <div class="d-flex align-items-center">
            ${channel.logo ? `<img src="${channel.logo}" class="me-2" style="max-height: 40px;">` : ''}
            <span>${channel.name} <small class="text-muted">(${channel.id})</small></span>
        </div>
    `;
    
    // Show loading
    scheduleTable.innerHTML = `
        <tr>
            <td colspan="3" class="text-center">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading program schedule...</span>
            </td>
        </tr>
    `;
    
    // Fetch program schedule
    fetch(`/api/epg/schedule/${encodeURIComponent(channel.id)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load program schedule');
            }
            return response.json();
        })
        .then(programs => {
            if (!programs || programs.length === 0) {
                scheduleTable.innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center">
                            <div class="alert alert-info m-0 p-2">
                                No program data available for this channel
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }
            
            // Format and display programs
            scheduleTable.innerHTML = programs.map(program => {
                const startTime = new Date(program.start).toLocaleTimeString();
                const endTime = new Date(program.stop).toLocaleTimeString();
                
                return `
                    <tr>
                        <td>${startTime} - ${endTime}</td>
                        <td>${program.title}</td>
                        <td>${program.desc || ''}</td>
                    </tr>
                `;
            }).join('');
        })
        .catch(error => {
            console.error('Error loading program schedule:', error);
            scheduleTable.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center">
                        <div class="alert alert-danger m-0 p-2">
                            Error loading program schedule: ${error.message}
                        </div>
                    </td>
                </tr>
            `;
        });
}

// Debounce function to prevent excessive API calls
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

// Helper functions for showing/hiding a loading indicator
function showLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'block';
    }
}

function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

// Helper function for showing alerts/notifications
function showAlert(type, message) {
    // Map type to Bootstrap alert class
    const alertClass = {
        'success': 'alert-success',
        'info': 'alert-info',
        'warning': 'alert-warning',
        'danger': 'alert-danger',
        'error': 'alert-danger'
    }[type] || 'alert-info';
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to document
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}