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
    selectedChannels: new Set()
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
    
    try {
        // Build query parameters from filters and pagination
        const params = new URLSearchParams();
        
        const searchInput = document.getElementById('tvChannelSearchInput');
        if (searchInput && searchInput.value.trim()) {
            params.append('search', searchInput.value.trim());
        }
        
        const filters = ['category', 'country', 'language'];
        filters.forEach(filter => {
            const element = document.getElementById(`${filter}Filter`);
            if (element && element.value) {
                params.append(filter, element.value);
            }
        });
        
        params.append('page', tvChannelsState.page.toString());
        params.append('per_page', tvChannelsState.perPage.toString());
        
        // Make API request
        const url = `/api/tv-channels?${params.toString()}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update state with returned data
        tvChannelsState.channels = data.channels || [];
        tvChannelsState.totalPages = data.total_pages || 1;
        
        // Update filter options if provided
        if (data.filters) {
            tvChannelsState.filters = data.filters;
            updateFilterDropdowns();
        }
        
        // Update UI
        updateTVChannelsTable();
        updatePagination();
        
    } catch (error) {
        console.error('Error loading TV channels:', error);
        showAlert('error', 'Failed to load TV channels');
    } finally {
        tvChannelsState.isLoading = false;
    }
}

/**
 * Update the TV channels table with current data
 */
function updateTVChannelsTable() {
    const tableBody = document.getElementById('tvChannelsTableBody');
    if (!tableBody) return;
    
    if (tvChannelsState.channels.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center">No TV channels found</td></tr>`;
        return;
    }
    
    tableBody.innerHTML = tvChannelsState.channels.map(channel => {
        // Format acestreams count
        const acestreamsCount = channel.acestream_channels_count || 0;
        const badgeClass = acestreamsCount > 0 ? 'bg-success' : 'bg-secondary';
        
        // Format country/language display
        const countryLanguage = [
            channel.country ? `<span class="badge bg-secondary">${channel.country}</span>` : '',
            channel.language ? `<span class="badge bg-info text-dark">${channel.language}</span>` : ''
        ].filter(Boolean).join(' ');
        
        // Channel name with logo if available
        const nameWithLogo = channel.logo_url ? 
            `<div class="d-flex align-items-center">
                <img src="${channel.logo_url}" alt="${channel.name}" class="me-2" style="height: 30px; max-width: 50px;">
                ${channel.name}
            </div>` : 
            channel.name;

        // Check if this channel is in the selected set
        const isSelected = tvChannelsState.selectedChannels.has(channel.id.toString());
        
        return `
            <tr>
                <td>
                    <div class="form-check">
                        <input class="form-check-input channel-select-checkbox" type="checkbox" 
                               value="${channel.id}" 
                               data-channel-id="${channel.id}" 
                               ${isSelected ? 'checked' : ''}>
                    </div>
                </td>
                <td>${nameWithLogo}</td>
                <td>${channel.category || '-'}</td>
                <td>${countryLanguage || '-'}</td>
                <td>
                    <span class="badge ${badgeClass}">${acestreamsCount}</span>
                </td>
                <td>${channel.epg_id || '-'}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/tv-channels/${channel.id}" class="btn btn-primary" title="View details">
                            <i class="bi bi-eye"></i> View
                        </a>
                        <button class="btn btn-danger" onclick="deleteTVChannel(${channel.id})" title="Delete">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    // Add event listeners to new checkboxes
    addCheckboxEventListeners();
}

/**
 * Add event listeners to channel selection checkboxes
 */
function addCheckboxEventListeners() {
    const checkboxes = document.querySelectorAll('.channel-select-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const channelId = this.value;
            
            if (this.checked) {
                tvChannelsState.selectedChannels.add(channelId);
            } else {
                tvChannelsState.selectedChannels.delete(channelId);
                
                // Uncheck "select all" if any individual checkbox is unchecked
                document.getElementById('selectAllChannels').checked = false;
            }
            
            updateBulkEditToolbar();
        });
    });
}

/**
 * Update the bulk edit toolbar visibility and count
 */
function updateBulkEditToolbar() {
    const toolbar = document.getElementById('bulkEditToolbar');
    const countSpan = document.getElementById('selectedChannelsCount');
    const selectedCount = tvChannelsState.selectedChannels.size;
    
    if (selectedCount > 0) {
        toolbar.classList.remove('d-none');
        countSpan.textContent = selectedCount;
    } else {
        toolbar.classList.add('d-none');
    }
}

/**
 * Clear all selected channels
 */
function clearSelection() {
    tvChannelsState.selectedChannels.clear();
    
    // Uncheck all checkboxes
    document.querySelectorAll('.channel-select-checkbox, #selectAllChannels').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    updateBulkEditToolbar();
}

/**
 * Open the bulk edit modal
 */
function openBulkEditModal() {
    // Update the count in the modal
    document.getElementById('bulkEditCount').textContent = tvChannelsState.selectedChannels.size;
    
    // Clear previous values
    document.getElementById('bulkEditCategory').value = '';
    document.getElementById('bulkEditCountry').value = '';
    document.getElementById('bulkEditLanguage').value = '';
    document.getElementById('bulkEditIsActive').checked = true;
    
    // Reset toggles
    document.querySelectorAll('.bulk-field-toggle').forEach(toggle => {
        toggle.checked = false;
    });
    
    // Hide all field groups
    document.querySelectorAll('.bulk-field').forEach(field => {
        field.classList.add('d-none');
    });
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('bulkEditTVChannelsModal'));
    modal.show();
}

/**
 * Save bulk edit changes
 */
async function saveBulkEdit() {
    // Get selected field toggles
    const toggles = document.querySelectorAll('.bulk-field-toggle:checked');
    
    // Build update object based on selected fields
    const updateData = {
        channel_ids: Array.from(tvChannelsState.selectedChannels)
    };
    
    // Add fields that should be updated
    toggles.forEach(toggle => {
        const field = toggle.value;
        
        switch (field) {
            case 'category':
                updateData.category = document.getElementById('bulkEditCategory').value.trim();
                break;
            case 'country':
                updateData.country = document.getElementById('bulkEditCountry').value.trim();
                break;
            case 'language':
                updateData.language = document.getElementById('bulkEditLanguage').value.trim();
                break;
            case 'is_active':
                updateData.is_active = document.getElementById('bulkEditIsActive').checked;
                break;
        }
    });
    
    // If no fields selected, show warning
    if (Object.keys(updateData).length <= 1) { // Only channel_ids
        showAlert('warning', 'Please select at least one field to update');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/bulk-update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'An error occurred during bulk update');
        }
        
        // Close the modal
        bootstrap.Modal.getInstance(document.getElementById('bulkEditTVChannelsModal')).hide();
        
        // Show success message
        showAlert('success', `Successfully updated ${data.updated_count} channels`);
        
        // Clear selection
        clearSelection();
        
        // Refresh the channels list
        loadTVChannels();
        
    } catch (error) {
        console.error('Bulk update failed:', error);
        showAlert('error', error.message || 'Failed to update channels');
    } finally {
        hideLoading();
    }
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
    
    let paginationHtml = '';
    
    // Previous button
    paginationHtml += `
        <li class="page-item ${tvChannelsState.page === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${tvChannelsState.page - 1}" aria-label="Previous">
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>
    `;
    
    // Page numbers
    const maxPages = Math.min(5, tvChannelsState.totalPages);
    let startPage = Math.max(1, tvChannelsState.page - 2);
    let endPage = Math.min(startPage + maxPages - 1, tvChannelsState.totalPages);
    
    // Adjust startPage if we're near the end
    if (endPage - startPage + 1 < maxPages) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === tvChannelsState.page ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // Next button
    paginationHtml += `
        <li class="page-item ${tvChannelsState.page === tvChannelsState.totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${tvChannelsState.page + 1}" aria-label="Next">
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>
    `;
    
    pagination.innerHTML = paginationHtml;
    
    // Add event listeners to pagination links
    const pageLinks = pagination.querySelectorAll('.page-link');
    pageLinks.forEach(link => {
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
 * Update filter dropdowns with available options
 */
function updateFilterDropdowns() {
    // Update category filter
    updateFilterDropdown('category', tvChannelsState.filters.categories);
    
    // Update country filter
    updateFilterDropdown('country', tvChannelsState.filters.countries);
    
    // Update language filter
    updateFilterDropdown('language', tvChannelsState.filters.languages);
}

/**
 * Update a specific filter dropdown with options
 */
function updateFilterDropdown(filterName, options) {
    const dropdown = document.getElementById(`${filterName}Filter`);
    if (!dropdown) return;
    
    // Save current selection
    const currentValue = dropdown.value;
    
    // Clear existing options except the first one (All)
    while (dropdown.options.length > 1) {
        dropdown.remove(1);
    }
    
    // Add new options
    if (Array.isArray(options)) {
        options.forEach(option => {
            if (option) { // Only add non-empty values
                const optionEl = document.createElement('option');
                optionEl.value = option;
                optionEl.textContent = option;
                dropdown.appendChild(optionEl);
            }
        });
    }
    
    // Restore selected value if it still exists
    if (currentValue) {
        dropdown.value = currentValue;
    }
}

/**
 * Update statistics cards with channel counts
 */
function updateStatCards() {
    // Make API call to get TV channel stats
    fetch('/api/stats/tv-channels/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('TV Channel stats loaded:', data);
            
            // Update stats cards with actual data
            document.getElementById('totalTVChannelsCard').textContent = data.total || 0;
            document.getElementById('activeChannelsCard').textContent = data.active || 0;
            document.getElementById('channelsWithEPGCard').textContent = data.with_epg || 0;
            document.getElementById('totalAcestreamsCard').textContent = data.acestreams || 0;
        })
        .catch(error => {
            console.error('Error loading TV channel stats:', error);
            
            // Set default values in case of error
            document.getElementById('totalTVChannelsCard').textContent = '0';
            document.getElementById('activeChannelsCard').textContent = '0';
            document.getElementById('channelsWithEPGCard').textContent = '0';
            document.getElementById('totalAcestreamsCard').textContent = '0';
        });
}

/**
 * Show the add TV channel modal
 */
function showAddTVChannelModal() {
    console.log('Showing Add TV Channel modal');
    // Clear form
    const form = document.getElementById('addTVChannelForm');
    if (form) form.reset();
    
    // Show the modal
    const modal = document.getElementById('addTVChannelModal');
    if (!modal) {
        console.error('Add TV Channel modal not found!');
        return;
    }
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

/**
 * Save a new TV channel
 */
async function saveNewTVChannel() {
    const form = document.getElementById('addTVChannelForm');
    if (!form) return;
    
    // Get form values
    const name = document.getElementById('newTVChannelName').value.trim();
    const description = document.getElementById('newTVChannelDescription').value.trim();
    const category = document.getElementById('newTVChannelCategory').value.trim();
    const country = document.getElementById('newTVChannelCountry').value.trim();
    const language = document.getElementById('newTVChannelLanguage').value.trim();
    const logoUrl = document.getElementById('newTVChannelLogo').value.trim();
    const website = document.getElementById('newTVChannelWebsite').value.trim();
    const epgId = document.getElementById('newTVChannelEpgId').value.trim();
    
    if (!name) {
        showAlert('warning', 'Channel name is required');
        return;
    }
    
    const channelData = {
        name: name,
        is_active: true
    };
    
    // Add optional fields
    if (description) channelData.description = description;
    if (category) channelData.category = category;
    if (country) channelData.country = country;
    if (language) channelData.language = language;
    if (logoUrl) channelData.logo_url = logoUrl;
    if (website) channelData.website = website;
    if (epgId) channelData.epg_id = epgId;
    
    try {
        showLoading();
        
        // Add trailing slash to the URL to match Flask's route definition
        const response = await fetch('/api/tv-channels/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(channelData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to create TV channel');
        }
        
        // Hide modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addTVChannelModal'));
        if (modal) modal.hide();
        
        // Show success message
        showAlert('success', 'TV channel created successfully');
        
        // Refresh data
        await loadTVChannels();
        updateStatCards();
    } catch (error) {
        console.error('Error creating TV channel:', error);
        showAlert('error', error.message || 'Error creating TV channel');
    } finally {
        hideLoading();
    }
}

/**
 * Delete a TV channel
 */
async function deleteTVChannel(id) {
    if (!confirm('Are you sure you want to delete this TV channel? This action cannot be undone.')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`/api/tv-channels/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to delete TV channel');
        }
        
        // Show success message
        showAlert('success', 'TV channel deleted successfully');
        
        // Refresh data
        await loadTVChannels();
        updateStatCards();
    } catch (error) {
        console.error('Error deleting TV channel:', error);
        showAlert('error', error.message || 'Error deleting TV channel');
    } finally {
        hideLoading();
    }
}

/**
 * Batch assign acestreams based on name patterns
 */
async function batchAssignAcestreams() {
    if (!confirm('This will attempt to match acestreams to TV channels based on name patterns. Continue?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/batch-assign', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ patterns: {} }) // The backend will handle the matching
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to batch assign acestreams');
        }
        
        // Show success message
        showAlert('success', `Batch assignment complete. ${Object.keys(result.results || {}).length} TV channels updated.`);
        
        // Refresh data
        await loadTVChannels();
        updateStatCards();
    } catch (error) {
        console.error('Error batch assigning acestreams:', error);
        showAlert('error', error.message || 'Error batch assigning acestreams');
    } finally {
        hideLoading();
    }
}

/**
 * Associate acestreams with TV channels based on EPG IDs
 */
async function associateByEPG() {
    if (!confirm('This will associate acestreams with TV channels based on matching EPG IDs. Continue?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/associate-by-epg', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to associate by EPG');
        }
        
        // Show success message
        showAlert('success', 'EPG association complete');
        
        // Refresh data
        await loadTVChannels();
        updateStatCards();
    } catch (error) {
        console.error('Error associating by EPG:', error);
        showAlert('error', error.message || 'Error associating by EPG');
    } finally {
        hideLoading();
    }
}

/**
 * Bulk update EPG data for all TV channels
 */
async function bulkUpdateEPG() {
    if (!confirm('This will update EPG data for all TV channels and their acestreams. Continue?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/bulk-update-epg', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to bulk update EPG');
        }
        
        // Show success message
        showAlert('success', 'Bulk EPG update complete');
        
        // Refresh data
        await loadTVChannels();
        updateStatCards();
    } catch (error) {
        console.error('Error bulk updating EPG:', error);
        showAlert('error', error.message || 'Error bulk updating EPG');
    } finally {
        hideLoading();
    }
}

/**
 * Generate TV channels from existing acestreams based on metadata
 */
async function generateTVChannelsFromAcestreams() {
    if (!confirm('This will analyze your acestreams and create TV channels based on their EPG data and other metadata. Continue?')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/tv-channels/generate-from-acestreams', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to generate TV channels');
        }
        
        // Show success message
        showAlert('success', `TV channels generation complete. Created: ${result.stats.created}, Matched: ${result.stats.matched}, Skipped: ${result.stats.skipped}`);
        
        // Refresh data
        await loadTVChannels();
        updateStatCards();
    } catch (error) {
        console.error('Error generating TV channels:', error);
        showAlert('error', error.message || 'Error generating TV channels');
    } finally {
        hideLoading();
    }
}

// Initialize debounce function if not already defined
if (typeof debounce !== 'function') {
    window.debounce = function(func, wait) {
        let timeout;
        return function(...args) {
            const later = () => {
                timeout = null;
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };
}
