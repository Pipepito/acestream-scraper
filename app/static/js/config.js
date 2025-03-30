/**
 * Configuration page functionality for Acestream Scraper
 */

// Load and display configuration data
async function loadConfigData() {
    showLoading();
    try {
        // Get stats from API
        const stats = await fetchStats();
        
        // Update system info table - only elements that exist on the config page
        if (document.getElementById('configBaseUrl')) 
            document.getElementById('configBaseUrl').textContent = stats.base_url || 'Not configured';
        if (document.getElementById('configAddPid'))
            document.getElementById('configAddPid').textContent = stats.addpid === true ? 'Yes' : 'No';
        if (document.getElementById('configAceEngineUrl'))
            document.getElementById('configAceEngineUrl').textContent = stats.ace_engine_url || 'Not configured';
        if (document.getElementById('configRescrapeInterval'))
            document.getElementById('configRescrapeInterval').textContent = (stats.rescrape_interval || 'N/A') + ' hours';
        if (document.getElementById('configTotalUrls'))
            document.getElementById('configTotalUrls').textContent = stats.urls?.length || 0;
        if (document.getElementById('configTotalChannels'))
            document.getElementById('configTotalChannels').textContent = stats.total_channels || 0;
        
        // Set the addPid checkbox value
        const addPidCheckbox = document.getElementById('addPidCheckbox');
        if (addPidCheckbox) {
            addPidCheckbox.checked = stats.addpid === true;
        }
        
        // Update Acexy status and Acestream Engine status
        initializeServiceStatusControls();
        
        // Update WARP status
        await updateWarpUI();
        
        // Load URLs list
        await loadUrlsList();
        
        // Update footer statistics
        updateStats(stats);
    } catch (error) {
        console.error('Error loading configuration data:', error);
    } finally {
        hideLoading();
    }
}

// Initialize service status controls and check status if enabled
function initializeServiceStatusControls() {
    // Setup Acexy status check control
    const enableAcexyCheck = document.getElementById('enableAcexyCheck');
    if (enableAcexyCheck) {
        // Set checkbox state from localStorage
        const acexyCheckEnabled = localStorage.getItem('enableAcexyCheck') !== 'false';
        enableAcexyCheck.checked = acexyCheckEnabled;
        
        // Add event listener to save preference
        enableAcexyCheck.addEventListener('change', function() {
            localStorage.setItem('enableAcexyCheck', this.checked);
            if (this.checked) {
                // If re-enabled, immediately check status
                updateAcexyStatus();
            } else {
                // If disabled, update UI to reflect disabled state
                const acexyStatus = document.getElementById('acexyStatusConfig');
                if (acexyStatus) {
                    acexyStatus.className = 'badge bg-secondary';
                    acexyStatus.textContent = 'Check disabled';
                }
            }
        });
        
        // Check status if enabled
        if (acexyCheckEnabled) {
            updateAcexyStatus();
        } else {
            const acexyStatus = document.getElementById('acexyStatusConfig');
            if (acexyStatus) {
                acexyStatus.className = 'badge bg-secondary';
                acexyStatus.textContent = 'Check disabled';
            }
        }
    }
    
    // Setup Acestream Engine status check control
    const enableAcestreamCheck = document.getElementById('enableAcestreamCheck');
    if (enableAcestreamCheck) {
        // Set checkbox state from localStorage
        const acestreamCheckEnabled = localStorage.getItem('enableAcestreamCheck') !== 'false';
        enableAcestreamCheck.checked = acestreamCheckEnabled;
        
        // Add event listener to save preference
        enableAcestreamCheck.addEventListener('change', function() {
            localStorage.setItem('enableAcestreamCheck', this.checked);
            if (this.checked) {
                // If re-enabled, immediately check status
                updateAcestreamStatus();
            } else {
                // If disabled, update UI to reflect disabled state
                const acestreamStatus = document.getElementById('acestreamStatusConfig');
                if (acestreamStatus) {
                    acestreamStatus.className = 'badge bg-secondary';
                    acestreamStatus.textContent = 'Check disabled';
                }
                // Hide details
                const acestreamDetails = document.getElementById('acestreamDetailsConfig');
                if (acestreamDetails) {
                    acestreamDetails.classList.add('d-none');
                }
            }
        });
        
        // Check status if enabled
        if (acestreamCheckEnabled) {
            updateAcestreamStatus();
        } else {
            const acestreamStatus = document.getElementById('acestreamStatusConfig');
            if (acestreamStatus) {
                acestreamStatus.className = 'badge bg-secondary';
                acestreamStatus.textContent = 'Check disabled';
            }
        }
    }
    
    // Setup Acexy check interval control
    const acexyCheckInterval = document.getElementById('acexyCheckInterval');
    const saveAcexyIntervalBtn = document.getElementById('saveAcexyIntervalBtn');
    
    if (acexyCheckInterval) {
        // Load saved interval from localStorage or use default
        const savedInterval = localStorage.getItem('acexyCheckInterval');
        if (savedInterval) {
            acexyCheckInterval.value = savedInterval;
        }
        
        // Add event listener to save button
        if (saveAcexyIntervalBtn) {
            saveAcexyIntervalBtn.addEventListener('click', function() {
                const interval = parseInt(acexyCheckInterval.value);
                if (isNaN(interval) || interval < 5) {
                    showAlert('warning', 'Check interval must be at least 5 seconds');
                    return;
                }
                
                // Save to localStorage
                localStorage.setItem('acexyCheckInterval', interval);
                
                // Show confirmation
                showAlert('success', 'Acexy check interval updated');
                
                // Update backend configuration
                updateAcexyCheckIntervalSetting(interval);
            });
        }
    }
    
    // Setup Acestream Engine check interval control
    const acestreamCheckInterval = document.getElementById('acestreamCheckInterval');
    const saveAcestreamIntervalBtn = document.getElementById('saveAcestreamIntervalBtn');
    
    if (acestreamCheckInterval) {
        // Load saved interval from localStorage or use default
        const savedInterval = localStorage.getItem('acestreamCheckInterval');
        if (savedInterval) {
            acestreamCheckInterval.value = savedInterval;
        }
        
        // Add event listener to save button
        if (saveAcestreamIntervalBtn) {
            saveAcestreamIntervalBtn.addEventListener('click', function() {
                const interval = parseInt(acestreamCheckInterval.value);
                if (isNaN(interval) || interval < 5) {
                    showAlert('warning', 'Check interval must be at least 5 seconds');
                    return;
                }
                
                // Save to localStorage
                localStorage.setItem('acestreamCheckInterval', interval);
                
                // Show confirmation
                showAlert('success', 'Acestream Engine check interval updated');
                
                // Update backend configuration
                updateAcestreamCheckIntervalSetting(interval);
            });
        }
    }
}

// Update Acexy status in the config page
async function updateAcexyStatus() {
    // Check if status checks are enabled
    const acexyCheckEnabled = localStorage.getItem('enableAcexyCheck') !== 'false';
    if (!acexyCheckEnabled) {
        const acexyStatus = document.getElementById('acexyStatusConfig');
        if (acexyStatus) {
            acexyStatus.className = 'badge bg-secondary';
            acexyStatus.textContent = 'Check disabled';
        }
        return;
    }

    try {
        const response = await fetch('/api/config/acexy_status');
        const data = await response.json();
        
        const acexyStatusElement = document.getElementById('acexyStatusConfig');
        const configAcexyStatus = document.getElementById('configAcexyStatus');
        
        if (acexyStatusElement) {
            if (data.enabled) {
                if (data.available) {
                    acexyStatusElement.className = 'badge bg-success';
                    acexyStatusElement.textContent = 'Online';
                    if (configAcexyStatus) configAcexyStatus.textContent = 'Enabled and Online';
                } else {
                    acexyStatusElement.className = 'badge bg-danger';
                    acexyStatusElement.textContent = 'Offline';
                    if (configAcexyStatus) configAcexyStatus.textContent = 'Enabled but Offline';
                }
            } else {
                acexyStatusElement.className = 'badge bg-secondary';
                acexyStatusElement.textContent = 'Disabled';
                if (configAcexyStatus) configAcexyStatus.textContent = 'Disabled';
            }
        }
        
        // Show/hide Acexy features
        const acexyElements = document.querySelectorAll('.acexy-feature');
        if (data.enabled) {
            acexyElements.forEach(el => el.classList.remove('d-none'));
        } else {
            acexyElements.forEach(el => el.classList.add('d-none'));
        }
    } catch (error) {
        console.error('Error checking Acexy status:', error);
        const acexyStatusElement = document.getElementById('acexyStatusConfig');
        if (acexyStatusElement) {
            acexyStatusElement.className = 'badge bg-warning';
            acexyStatusElement.textContent = 'Error';
        }
    }
}

// Update Acestream Engine status in the config page
async function updateAcestreamStatus() {
    // Check if status checks are enabled
    const acestreamCheckEnabled = localStorage.getItem('enableAcestreamCheck') !== 'false';
    if (!acestreamCheckEnabled) {
        const acestreamStatus = document.getElementById('acestreamStatusConfig');
        if (acestreamStatus) {
            acestreamStatus.className = 'badge bg-secondary';
            acestreamStatus.textContent = 'Check disabled';
        }
        return;
    }

    try {
        const response = await fetch('/api/config/acestream_status');
        const data = await response.json();
        
        const acestreamStatusElement = document.getElementById('acestreamStatusConfig');
        const configAcestreamStatus = document.getElementById('configAcexyStatus');
        const acestreamDetailsElement = document.getElementById('acestreamDetailsConfig');
        const versionElement = document.getElementById('acestreamVersionConfig');
        const platformElement = document.getElementById('acestreamPlatformConfig');
        const networkElement = document.getElementById('acestreamNetworkConfig');
        const engineUrlElement = document.getElementById('acestreamUrlConfig');
        
        if (acestreamStatusElement) {
            if (data.available) {
                acestreamStatusElement.className = 'badge bg-success';
                acestreamStatusElement.textContent = data.is_internal ? 'Online' : 'External Online';
                
                if (acestreamDetailsElement) {
                    acestreamDetailsElement.classList.remove('d-none');
                    if (versionElement) versionElement.textContent = data.version || 'Unknown';
                    if (platformElement) platformElement.textContent = data.platform || 'Unknown';
                    if (networkElement) networkElement.textContent = data.connected ? 'Connected' : 'Disconnected';
                    if (engineUrlElement) {
                        if (data.is_internal) {
                            engineUrlElement.parentElement.classList.add('d-none');
                        } else {
                            engineUrlElement.parentElement.classList.remove('d-none');
                            engineUrlElement.textContent = data.engine_url || 'Unknown';
                        }
                    }
                }
                
                if (configAcestreamStatus) {
                    configAcestreamStatus.textContent = data.is_internal ? 
                        'Enabled and Online' : 'External Engine Online';
                }
            } else {
                if (data.is_internal === false && data.engine_url) {
                    // External engine is configured but not available
                    acestreamStatusElement.className = 'badge bg-danger';
                    acestreamStatusElement.textContent = 'External Offline';
                    
                    if (acestreamDetailsElement) {
                        acestreamDetailsElement.classList.remove('d-none');
                        if (engineUrlElement) {
                            engineUrlElement.parentElement.classList.remove('d-none');
                            engineUrlElement.textContent = data.engine_url || 'Unknown';
                        }
                        if (versionElement) versionElement.parentElement.classList.add('d-none');
                        if (platformElement) platformElement.parentElement.classList.add('d-none');
                        if (networkElement) networkElement.parentElement.classList.add('d-none');
                    }
                    
                    if (configAcestreamStatus) {
                        configAcestreamStatus.textContent = 'External Engine Offline';
                    }
                } else if (data.enabled) {
                    acestreamStatusElement.className = 'badge bg-danger';
                    acestreamStatusElement.textContent = 'Offline';
                    if (acestreamDetailsElement) acestreamDetailsElement.classList.add('d-none');
                    if (configAcestreamStatus) configAcestreamStatus.textContent = 'Enabled but Offline';
                } else {
                    acestreamStatusElement.className = 'badge bg-secondary';
                    acestreamStatusElement.textContent = 'Disabled';
                    if (acestreamDetailsElement) acestreamDetailsElement.classList.add('d-none');
                    if (configAcestreamStatus) configAcestreamStatus.textContent = 'Disabled';
                }
            }
        }
    } catch (error) {
        console.error('Error checking Acestream Engine status:', error);
        const acestreamStatusElement = document.getElementById('acestreamStatusConfig');
        if (acestreamStatusElement) {
            acestreamStatusElement.className = 'badge bg-warning';
            acestreamStatusElement.textContent = 'Error';
        }
    }
}

// Check Acestream Engine status with optional loading indicator
async function checkAcestreamStatus(showLoadingIndicator = false) {
    try {
        if (showLoadingIndicator) showLoading();
        await updateAcestreamStatus();
    } finally {
        if (showLoadingIndicator) hideLoading();
    }
}

// Load URLs list for management
async function loadUrlsList() {
    try {
        const stats = await fetchStats();
        const urlsManagementList = document.getElementById('urlsManagementList');
        
        if (urlsManagementList && stats.urls && stats.urls.length > 0) {
            urlsManagementList.innerHTML = stats.urls.map(url => `
                <div class="list-group-item">
                    <div class="row align-items-center">
                        <div class="col-md-7">
                            <div>
                                <strong>${url.url}</strong>
                                <span class="badge bg-info ms-2">${url.url_type}</span>
                            </div>
                            <div class="small text-muted">
                                <span>ID: ${url.id}</span>
                                <span class="ms-2">Status: <span class="status-${url.status.toLowerCase()}">${url.status}</span></span>
                                <span class="ms-2">Channels: ${url.channel_count}</span>
                                ${url.last_processed ? `<span class="ms-2">Last scraped: ${formatLocalDate(url.last_processed)}</span>` : ''}
                            </div>
                        </div>
                        <div class="col-md-5 text-end">
                            <button class="btn btn-sm ${url.enabled ? 'btn-warning' : 'btn-success'}" 
                                    onclick="toggleUrl('${url.id}', ${!url.enabled})">
                                ${url.enabled ? 'Disable' : 'Enable'}
                            </button>
                            <button class="btn btn-sm btn-info" 
                                    onclick="refreshUrl('${url.id}')">
                                Refresh
                            </button>
                            <button class="btn btn-sm btn-danger" 
                                    onclick="deleteUrl('${url.id}')">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            urlsManagementList.innerHTML = '<div class="list-group-item text-center text-muted">No URLs found</div>';
        }
    } catch (error) {
        console.error('Error loading URLs list:', error);
    }
}

// Refresh a single URL
async function refreshUrl(url) {
    try {
        showLoading();
        const response = await fetch(`/api/urls/${encodeURIComponent(url)}/refresh`, {
            method: 'POST'
        });
        
        await handleApiResponse(response, 'URL refresh started');
    } catch (error) {
        console.error('Error refreshing URL:', error);
        alert('Network error while refreshing URL');
    } finally {
        hideLoading();
    }
}

// Migrate configuration from file to database
async function migrateConfigToDatabase() {
    if (!confirm('This will migrate settings from config.json to the database. Continue?')) {
        return;
    }
    
    try {
        showLoading();
        const response = await fetch('/api/config/migrate_config', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            showAlert('success', data.message);
            await loadConfigData();
        } else {
            showAlert('error', data.message || 'Failed to migrate configuration');
        }
    } catch (error) {
        console.error('Error migrating config:', error);
        showAlert('error', 'Network error while migrating configuration');
    } finally {
        hideLoading();
    }
}

// Setup event listeners for the configuration page
function setupConfigEvents() {
    // Base URL form
    const baseUrlForm = document.getElementById('baseUrlForm');
    if (baseUrlForm) {
        baseUrlForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const baseUrlInput = document.getElementById('baseUrlInput');
            const baseUrl = baseUrlInput.value;
            const addpid = document.getElementById('addPidCheckbox').checked;

            try {
                showLoading();
                
                // Update base URL
                const responseBaseUrl = await fetch('/api/config/base_url', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ base_url: baseUrl })
                });

                // Update addpid setting
                const responseAddPid = await fetch('/api/config/addpid', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ addpid: addpid })
                });

                if (await handleApiResponse(responseBaseUrl, 'Base URL updated successfully') && 
                    await handleApiResponse(responseAddPid, 'PID parameter setting updated successfully')) {
                    baseUrlInput.value = '';
                    await loadConfigData();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Network error while updating base URL configuration');
            } finally {
                hideLoading();
            }
        });
    }

    // Save addpid when checkbox is changed (separately)
    const addPidCheckbox = document.getElementById('addPidCheckbox');
    if (addPidCheckbox) {
        addPidCheckbox.addEventListener('change', async () => {
            try {
                showLoading();
                const response = await fetch('/api/config/addpid', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ addpid: addPidCheckbox.checked })
                });

                await handleApiResponse(response, 'PID parameter setting updated successfully');
                await loadConfigData();
            } catch (error) {
                console.error('Error:', error);
                alert('Network error while updating PID parameter setting');
            } finally {
                hideLoading();
            }
        });
    }

    // Ace Engine form
    const aceEngineForm = document.getElementById('aceEngineForm');
    if (aceEngineForm) {
        aceEngineForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const aceEngineInput = document.getElementById('aceEngineInput');
            const aceEngineUrl = aceEngineInput.value;

            try {
                showLoading();
                const response = await fetch('/api/config/ace_engine_url', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ ace_engine_url: aceEngineUrl })
                });

                if (await handleApiResponse(response, 'Ace Engine URL updated successfully')) {
                    aceEngineInput.value = '';
                    await loadConfigData();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Network error while updating Ace Engine URL');
            } finally {
                hideLoading();
            }
        });
    }

    // Rescrape interval form
    const rescrapeIntervalForm = document.getElementById('rescrapeIntervalForm');
    if (rescrapeIntervalForm) {
        rescrapeIntervalForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const hoursInput = document.getElementById('rescrapeIntervalInput');
            const hours = parseInt(hoursInput.value, 10);

            if (isNaN(hours) || hours < 1) {
                alert('Please enter a valid number of hours (minimum 1)');
                return;
            }

            try {
                showLoading();
                const response = await fetch('/api/config/rescrape_interval', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ hours: hours })
                });

                if (await handleApiResponse(response, 'Rescrape interval updated successfully')) {
                    hoursInput.value = '';
                    await loadConfigData();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Network error while updating rescrape interval');
            } finally {
                hideLoading();
            }
        });
    }

    // Add URL form
    const addUrlForm = document.getElementById('addUrlForm');
    if (addUrlForm) {
        addUrlForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const urlInput = document.getElementById('urlInput');
            const urlTypeSelect = document.getElementById('urlTypeSelect');
            const url = urlInput.value.trim();
            const urlType = urlTypeSelect.value;

            if (!url) {
                showAlert('warning', 'Please enter a URL');
                return;
            }

            try {
                showLoading();
                const success = await addUrl(url, urlType);
                if (success) {
                    urlInput.value = '';
                    await loadUrlsList();
                }
            } finally {
                hideLoading();
            }
        });
    }

    // Migration button
    const migrateConfigBtn = document.getElementById('migrateConfigBtn');
    if (migrateConfigBtn) {
        migrateConfigBtn.addEventListener('click', migrateConfigToDatabase);
    }
}

// Update Acexy check interval setting on server
async function updateAcexyCheckIntervalSetting(interval) {
    try {
        const response = await fetch('/api/config/acexy_check_interval', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interval: interval })
        });
        
        await handleApiResponse(response, 'Acexy check interval saved');
    } catch (error) {
        console.error('Error updating Acexy check interval:', error);
        showAlert('error', 'Error saving Acexy check interval');
    }
}

// Update Acestream Engine check interval setting on server
async function updateAcestreamCheckIntervalSetting(interval) {
    try {
        const response = await fetch('/api/config/acestream_check_interval', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interval: interval })
        });
        
        await handleApiResponse(response, 'Acestream Engine check interval saved');
    } catch (error) {
        console.error('Error updating Acestream Engine check interval:', error);
        showAlert('error', 'Error saving Acestream Engine check interval');
    }
}

// Initialize configuration page
document.addEventListener('DOMContentLoaded', function() {
    // Load configuration data
    loadConfigData();
    
    // Set up event handlers
    setupConfigEvents();
    
    // Refresh periodically
    setInterval(loadConfigData, 60000); // Every minute
});