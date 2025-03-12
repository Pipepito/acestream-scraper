/**
 * Setup wizard functionality for Acestream Scraper
 */

// State management
const setupState = {
    currentStep: 1,
    totalSteps: 5,
    baseUrl: 'acestream://',
    acexyEnabled: false,
    aceEngineUrl: 'http://localhost:6878',
    rescrapeInterval: 24,
    sources: []
};

// Show loading spinner
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

// Hide loading spinner
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Switch to a specific step
function goToStep(stepNumber) {
    // Hide all steps
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => step.classList.remove('active'));
    
    // Show the target step
    document.getElementById(`step-${stepNumber}`).classList.add('active');
    
    // Update step indicators
    const indicators = document.querySelectorAll('.step-dot');
    indicators.forEach(dot => {
        const dotStep = parseInt(dot.dataset.step);
        dot.classList.remove('active', 'completed');
        
        if (dotStep === stepNumber) {
            dot.classList.add('active');
        } else if (dotStep < stepNumber) {
            dot.classList.add('completed');
        }
    });
    
    setupState.currentStep = stepNumber;
}

// Go to next step
function nextStep() {
    if (setupState.currentStep < setupState.totalSteps) {
        goToStep(setupState.currentStep + 1);
    }
}

// Go to previous step
function prevStep() {
    if (setupState.currentStep > 1) {
        goToStep(setupState.currentStep - 1);
    }
}

// Add a source URL to the list
function addSource(url) {
    if (url && !setupState.sources.includes(url)) {
        setupState.sources.push(url);
        updateSourcesList();
        return true;
    }
    return false;
}

// Remove a source URL from the list
function removeSource(url) {
    const index = setupState.sources.indexOf(url);
    if (index !== -1) {
        setupState.sources.splice(index, 1);
        updateSourcesList();
    }
}

// Update the sources list in the UI
function updateSourcesList() {
    const sourcesList = document.getElementById('sourcesList');
    const noSourcesMessage = document.getElementById('noSourcesMessage');
    
    if (setupState.sources.length === 0) {
        noSourcesMessage.style.display = 'block';
        sourcesList.innerHTML = '';
        sourcesList.appendChild(noSourcesMessage);
    } else {
        noSourcesMessage.style.display = 'none';
        
        // Clear existing items except the no sources message
        const existingItems = document.querySelectorAll('#sourcesList .source-item');
        existingItems.forEach(item => item.remove());
        
        // Add current sources
        setupState.sources.forEach(source => {
            const item = document.createElement('div');
            item.className = 'list-group-item source-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <span class="text-break">${source}</span>
                <button class="btn btn-sm btn-outline-danger remove-source-btn" data-url="${source}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                        <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                    </svg>
                </button>
            `;
            sourcesList.appendChild(item);
            
            // Add event listener to the remove button
            item.querySelector('.remove-source-btn').addEventListener('click', function() {
                removeSource(this.dataset.url);
            });
        });
    }
}

// Save final configuration and complete setup
async function saveConfiguration() {
    showLoading();
    try {
        // Save base URL
        await fetch('/api/config/base_url', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ base_url: setupState.baseUrl })
        });
        
        // Save Ace Engine URL
        await fetch('/api/config/ace_engine_url', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ace_engine_url: setupState.aceEngineUrl })
        });
        
        // Save rescrape interval
        await fetch('/api/config/rescrape_interval', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hours: setupState.rescrapeInterval })
        });
        
        // Mark setup as completed - IMPORTANT: This should be last
        const setupResponse = await fetch('/api/config/setup_completed', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ completed: true })
        });

        if (!setupResponse.ok) {
            throw new Error('Failed to mark setup as completed');
        }
        
        // Add source URLs only after setup is completed
        for (const url of setupState.sources) {
            const response = await fetch('/api/urls/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });
            
            if (!response.ok) {
                console.error(`Failed to add URL: ${url}`);
            }
        }
        
        return true;
    } catch (error) {
        console.error('Error saving configuration:', error);
        alert('There was an error saving your configuration. Please try again.');
        return false;
    } finally {
        hideLoading();
    }
}

// Finish setup and redirect to dashboard
async function finishSetup() {
    try {
        showLoading();
        const success = await saveConfiguration();
        if (success) {
            // Force reload to trigger server-side redirect
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error finishing setup:', error);
        alert('There was an error completing the setup. Please try again.');
    } finally {
        hideLoading();
    }
}

// Initialize the setup page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize setup
    initSetup();
    
    // Enable clicking on step indicators
    document.querySelectorAll('.step-dot').forEach(dot => {
        dot.addEventListener('click', () => {
            const stepNumber = parseInt(dot.dataset.step);
            if (stepNumber <= setupState.currentStep) {
                goToStep(stepNumber);
            }
        });
    });
    
    // Base URL form submission
    document.getElementById('baseUrlForm').addEventListener('submit', function(e) {
        e.preventDefault();
        setupState.baseUrl = document.getElementById('baseUrl').value;
        nextStep();
    });
    
    // Ace Engine form submission
    document.getElementById('aceEngineForm').addEventListener('submit', function(e) {
        e.preventDefault();
        setupState.aceEngineUrl = document.getElementById('aceEngineUrl').value;
        setupState.useAcexy = document.getElementById('useAcexy').checked;
        
        // If using Acexy, set default Ace Engine URL
        if (setupState.useAcexy && setupState.aceEngineUrl === '') {
            setupState.aceEngineUrl = 'http://localhost:8080';
        }
        
        nextStep();
    });
    
    // Add source button click
    document.getElementById('addSourceBtn').addEventListener('click', function() {
        const sourceUrl = document.getElementById('sourceUrl').value;
        if (addSource(sourceUrl)) {
            document.getElementById('sourceUrl').value = '';
        } else {
            alert('Please enter a valid URL that has not been added yet.');
        }
    });
    
    // Scraping sources form submission
    document.getElementById('scrapingSourcesForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Add any URL that might be in the input but not added yet
        const sourceUrl = document.getElementById('sourceUrl').value;
        if (sourceUrl) {
            addSource(sourceUrl);
        }
        
        // Check if at least one source is added
        if (setupState.sources.length === 0) {
            alert('Please add at least one source URL to scrape.');
            return;
        }
        
        // Save rescrape interval
        setupState.rescrapeInterval = parseInt(document.getElementById('rescrapeInterval').value) || 24;
        
        nextStep();
    });
    
    // Set default values based on common configurations
    document.getElementById('baseUrl').value = 'acestream://';
    document.getElementById('aceEngineUrl').value = 'http://localhost:8080'; // Default for Acexy
    
    // Initialize sources list
    updateSourcesList();
    
    // Focus first input on page load
    document.getElementById('baseUrl').focus();
});

// Initialize setup page
async function initSetup() {
    try {
        // Check Acexy availability first
        const acexyResponse = await fetch('/api/config/acexy_status');
        const acexyData = await acexyResponse.json();
        
        // Show/hide Acexy option based on availability
        const acexySection = document.getElementById('acexySection');
        if (acexySection) {
            if (acexyData.enabled) {
                acexySection.classList.remove('d-none');
                
                // Add event listener for Acexy checkbox
                const acexyCheckbox = document.getElementById('useAcexy');
                if (acexyCheckbox) {
                    acexyCheckbox.addEventListener('change', (e) => {
                        setupState.acexyEnabled = e.target.checked;
                        // Update Ace Engine URL based on Acexy selection
                        const aceEngineInput = document.getElementById('aceEngineUrl');
                        if (aceEngineInput) {
                            aceEngineInput.value = e.target.checked ? 
                                'http://localhost:8080' : 
                                'http://localhost:6878';
                            setupState.aceEngineUrl = aceEngineInput.value;
                        }
                    });
                }
            } else {
                acexySection.classList.add('d-none');
            }
        }
    } catch (error) {
        console.error('Error initializing setup:', error);
    }
}

// Validate setup data
function validateSetup() {
    const baseUrl = document.getElementById('baseUrl').value;
    const aceEngineUrl = document.getElementById('aceEngineUrl').value;
    const rescrapeInterval = document.getElementById('rescrapeInterval').value;
    
    if (!baseUrl || !aceEngineUrl || !rescrapeInterval) {
        showAlert('error', 'Please fill in all required fields');
        return false;
    }
    
    // URLs are optional, just collect them if they exist
    const urlsInput = document.getElementById('urlsInput');
    if (urlsInput && urlsInput.value.trim()) {
        setupState.sources = urlsInput.value
            .split('\n')
            .map(url => url.trim())
            .filter(url => url.length > 0);
    }
    
    return true;
}