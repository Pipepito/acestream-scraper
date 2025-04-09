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
    isLoading: false
};

// Document ready handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('TV Channels page initialized');
    
    // Initialize the page
    loadInitialData();
    
    // Set up event listeners
    setupEventListeners();
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
        
        return `
            <tr>
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
