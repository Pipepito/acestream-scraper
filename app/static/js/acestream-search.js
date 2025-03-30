/**
 * Acestream search functionality for Acestream Scraper
 */

// State for search page
const searchState = {
    currentPage: 1,
    pageSize: 10,
    totalPages: 0,
    query: '',
    results: [],
    isLoading: false
};

// DOM Elements
let searchForm;
let searchQuery;
let searchButton;
let categoryFilter; // Add category filter element
let resultsContainer;
let searchResults;
let noResultsMessage;
let searchLoading;
let pagination;
let errorContainer;
let errorMessage;
let selectAllCheckbox;
let addSelectedButton;

// Initialize page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM elements
    searchForm = document.getElementById('searchForm');
    searchQuery = document.getElementById('searchQuery');
    searchButton = document.getElementById('searchButton');
    categoryFilter = document.getElementById('categoryFilter'); // Initialize category filter
    resultsContainer = document.getElementById('resultsContainer');
    searchResults = document.getElementById('searchResults');
    noResultsMessage = document.getElementById('noResultsMessage');
    searchLoading = document.getElementById('searchLoading');
    pagination = document.getElementById('pagination');
    errorContainer = document.getElementById('errorContainer');
    errorMessage = document.getElementById('errorMessage');
    selectAllCheckbox = document.getElementById('selectAllCheckbox');
    addSelectedButton = document.getElementById('addSelectedButton');
    
    // Add event listeners
    searchForm.addEventListener('submit', handleSearch);
    selectAllCheckbox.addEventListener('change', handleSelectAll);
    addSelectedButton.addEventListener('click', handleAddSelected);
    
    // Check Acestream engine status on page load
    checkAcestreamStatus();
});

// Handle search form submission
async function handleSearch(e) {
    e.preventDefault();
    
    const query = searchQuery.value.trim();
    // Allow empty queries - remove validation that was preventing empty searches
    
    // Reset state
    searchState.query = query;
    searchState.currentPage = 1;
    
    // Perform search
    await performSearch();
}

// Perform search API call
async function performSearch() {
    // Show loading state
    showLoading(true);
    hideError();
    searchState.isLoading = true;
    
    try {
        // Get category value if selected
        const category = categoryFilter ? categoryFilter.value : '';
        
        // Build search URL with query parameters
        let searchUrl = `/api/search?query=${encodeURIComponent(searchState.query)}&page=${searchState.currentPage}&page_size=${searchState.pageSize}`;
        
        // Add category parameter if selected
        if (category) {
            searchUrl += `&category=${encodeURIComponent(category)}`;
        }
        
        // Make API request
        const response = await fetch(searchUrl);
        const data = await response.json();
        
        if (data.success) {
            // Update state
            searchState.results = data.results;
            searchState.totalPages = data.pagination.total_pages;
            searchState.currentPage = data.pagination.page;
            
            // Display results
            displayResults();
            updatePagination();
        } else {
            // Show error message
            showError(data.message || 'Search failed');
        }
    } catch (error) {
        console.error('Error performing search:', error);
        showError('Error connecting to search service');
    } finally {
        // Hide loading state
        showLoading(false);
        searchState.isLoading = false;
    }
}

// Display search results
function displayResults() {
    // Clear previous results
    searchResults.innerHTML = '';
    
    // Show/hide appropriate containers
    resultsContainer.classList.remove('d-none');
    
    if (searchState.results.length === 0) {
        noResultsMessage.classList.remove('d-none');
        return;
    }
    
    noResultsMessage.classList.add('d-none');
    
    // Create table rows for each result
    searchState.results.forEach(result => {
        const row = document.createElement('tr');
        
        // Format categories
        const categories = result.categories && result.categories.length > 0
            ? result.categories.join(', ')
            : '-';
        
        // Format bitrate
        const bitrate = result.bitrate 
            ? `${Math.round(result.bitrate / 1000)} Kbps`
            : '-';
        
        row.innerHTML = `
            <td>
                <div class="form-check">
                    <input class="form-check-input result-checkbox" type="checkbox" value="${result.id}" data-name="${result.name}">
                </div>
            </td>
            <td>${result.name || 'Unnamed Channel'}</td>
            <td><code>${result.id}</code></td>
            <td>${categories}</td>
            <td>${bitrate}</td>
            <td>
                <button class="btn btn-sm btn-primary add-channel-btn" data-id="${result.id}" data-name="${result.name}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-lg" viewBox="0 0 16 16">
                        <path d="M8 0a1 1 0 0 1 1 1v6h6a1 1 0 1 1 0 2H9v6a1 1 0 1 1-2 0V9H1a1 1 0 0 1 0-2h6V1a1 1 0 0 1 1-1z"/>
                    </svg>
                    Add
                </button>
            </td>
        `;
        
        // Add event listener to the add button
        const addButton = row.querySelector('.add-channel-btn');
        addButton.addEventListener('click', () => {
            addChannel(result.id, result.name);
        });
        
        searchResults.appendChild(row);
    });
}

// Update pagination controls
function updatePagination() {
    pagination.innerHTML = '';
    
    if (searchState.totalPages <= 1) {
        return;
    }
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.classList.add('page-item');
    if (searchState.currentPage === 1) {
        prevLi.classList.add('disabled');
    }
    prevLi.innerHTML = `
        <a class="page-link" href="#" aria-label="Previous">
            <span aria-hidden="true">&laquo;</span>
        </a>
    `;
    prevLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (searchState.currentPage > 1) {
            goToPage(searchState.currentPage - 1);
        }
    });
    pagination.appendChild(prevLi);
    
    // Page numbers
    const startPage = Math.max(1, searchState.currentPage - 2);
    const endPage = Math.min(searchState.totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        pageLi.classList.add('page-item');
        if (i === searchState.currentPage) {
            pageLi.classList.add('active');
        }
        pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageLi.addEventListener('click', (e) => {
            e.preventDefault();
            goToPage(i);
        });
        pagination.appendChild(pageLi);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.classList.add('page-item');
    if (searchState.currentPage === searchState.totalPages) {
        nextLi.classList.add('disabled');
    }
    nextLi.innerHTML = `
        <a class="page-link" href="#" aria-label="Next">
            <span aria-hidden="true">&raquo;</span>
        </a>
    `;
    nextLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (searchState.currentPage < searchState.totalPages) {
            goToPage(searchState.currentPage + 1);
        }
    });
    pagination.appendChild(nextLi);
}

// Go to a specific page
function goToPage(page) {
    if (page === searchState.currentPage) {
        return;
    }
    
    searchState.currentPage = page;
    performSearch();
    
    // Scroll back to top of results
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

// Show loading state
function showLoading(isLoading) {
    if (isLoading) {
        searchLoading.classList.remove('d-none');
        searchResults.classList.add('d-none');
    } else {
        searchLoading.classList.add('d-none');
        searchResults.classList.remove('d-none');
    }
}

// Show error message
function showError(message) {
    errorContainer.classList.remove('d-none');
    errorMessage.textContent = message;
}

// Hide error message
function hideError() {
    errorContainer.classList.add('d-none');
}

// Handle select all checkbox
function handleSelectAll() {
    const checkboxes = document.querySelectorAll('.result-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

// Get selected channels
function getSelectedChannels() {
    const checkboxes = document.querySelectorAll('.result-checkbox:checked');
    const channels = [];
    
    checkboxes.forEach(checkbox => {
        channels.push({
            id: checkbox.value,
            name: checkbox.dataset.name
        });
    });
    
    return channels;
}

// Handle add selected button
async function handleAddSelected() {
    const selectedChannels = getSelectedChannels();
    
    if (selectedChannels.length === 0) {
        showAlert('warning', 'Please select at least one channel');
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch('/api/search/add_multiple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                channels: selectedChannels
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('success', data.message);
            
            // Update UI to reflect added channels
            updateAddedChannelsUI(data.added_channels, data.existing_channels);
        } else {
            showAlert('danger', data.message || 'Failed to add channels');
        }
    } catch (error) {
        console.error('Error adding channels:', error);
        showAlert('danger', 'Error adding channels');
    } finally {
        showLoading(false);
    }
}

// Add a single channel
async function addChannel(id, name) {
    try {
        const response = await fetch('/api/search/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: id,
                name: name
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('success', `Channel "${name}" added successfully`);
            
            // Disable the add button for this channel
            const button = document.querySelector(`.add-channel-btn[data-id="${id}"]`);
            if (button) {
                button.disabled = true;
                button.classList.remove('btn-primary');
                button.classList.add('btn-success');
                button.innerHTML = 'Added';
            }
            
            // Also uncheck this channel if it was checked
            const checkbox = document.querySelector(`.result-checkbox[value="${id}"]`);
            if (checkbox) {
                checkbox.checked = false;
                checkbox.disabled = true;
            }
        } else {
            if (data.message.includes('already exists')) {
                showAlert('info', `Channel "${name}" already exists`);
                
                // Disable the add button for this channel
                const button = document.querySelector(`.add-channel-btn[data-id="${id}"]`);
                if (button) {
                    button.disabled = true;
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-secondary');
                    button.innerHTML = 'Exists';
                }
                
                // Also uncheck this channel if it was checked
                const checkbox = document.querySelector(`.result-checkbox[value="${id}"]`);
                if (checkbox) {
                    checkbox.checked = false;
                    checkbox.disabled = true;
                }
            } else {
                showAlert('danger', data.message || 'Failed to add channel');
            }
        }
    } catch (error) {
        console.error('Error adding channel:', error);
        showAlert('danger', 'Error adding channel');
    }
}

// Update UI after adding multiple channels
function updateAddedChannelsUI(addedChannels, existingChannels) {
    // Combine both lists to update UI
    const allIds = [...addedChannels.map(c => c.id), ...existingChannels.map(c => c.id)];
    
    allIds.forEach(id => {
        // Disable the add button for this channel
        const button = document.querySelector(`.add-channel-btn[data-id="${id}"]`);
        if (button) {
            button.disabled = true;
            
            // Different styling based on whether it was added or already existed
            if (addedChannels.some(c => c.id === id)) {
                button.classList.remove('btn-primary');
                button.classList.add('btn-success');
                button.innerHTML = 'Added';
            } else {
                button.classList.remove('btn-primary');
                button.classList.add('btn-secondary');
                button.innerHTML = 'Exists';
            }
        }
        
        // Disable checkbox
        const checkbox = document.querySelector(`.result-checkbox[value="${id}"]`);
        if (checkbox) {
            checkbox.checked = false;
            checkbox.disabled = true;
        }
    });
    
    // Uncheck "select all" if it was checked
    selectAllCheckbox.checked = false;
}