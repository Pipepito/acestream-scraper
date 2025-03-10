/**
 * URL management functionality for Acestream Scraper
 */

// Toggle URL enabled/disabled status
async function toggleUrl(url, enable) {
    try {
        showLoading();
        const response = await fetch(`/api/urls/${encodeURIComponent(url)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled: enable })
        });
        
        // On dashboard we have refreshData but on config we have loadConfigData
        if (response.ok) {
            if (typeof loadConfigData === 'function') {
                await loadConfigData();
            } else if (typeof refreshData === 'function') {
                await refreshData();
            }
            return true;
        } else {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const error = await response.json();
                alert(error.message || error.error || 'An error occurred');
            } else {
                alert('An unexpected error occurred');
            }
            return false;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error while updating URL');
    } finally {
        hideLoading();
    }
}

// Delete URL
async function deleteUrl(url) {
    if (!confirm('Are you sure you want to delete this URL? This will also remove all associated channels.')) {
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/urls/${encodeURIComponent(url)}`, {
            method: 'DELETE'
        });
        
        // On dashboard we have refreshData but on config we have loadConfigData
        if (response.ok) {
            if (typeof loadConfigData === 'function') {
                await loadConfigData();
            } else if (typeof refreshData === 'function') {
                await refreshData();
            }
            return true;
        } else {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const error = await response.json();
                alert(error.message || error.error || 'An error occurred');
            } else {
                alert('An unexpected error occurred');
            }
            return false;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error while deleting URL');
    } finally {
        hideLoading();
    }
}

// Refresh all URLs
async function refreshAllUrls() {
    if (!confirm('Are you sure you want to refresh all URLs? This might take a while.')) {
        return;
    }

    showLoading();
    try {
        const response = await fetch('/api/urls/refresh', {
            method: 'POST'
        });
        
        const data = await response.json();
        if (response.ok) {
            alert(`${data.message}\nURLs being processed: ${data.urls.length}`);
            
            // Start polling for updates more frequently during refresh
            const pollInterval = setInterval(async () => {
                if (typeof loadConfigData === 'function') {
                    await loadConfigData();
                } else if (typeof refreshData === 'function') {
                    await refreshData();
                }
                
                // Check if all URLs are done processing
                const statsResponse = await fetch('/api/stats/');
                const stats = await statsResponse.json();
                const processingUrls = stats.urls.filter(u => u.status === 'processing');
                
                if (processingUrls.length === 0) {
                    clearInterval(pollInterval);
                }
            }, 5000); // Poll every 5 seconds
            
            // Stop polling after 5 minutes max
            setTimeout(() => clearInterval(pollInterval), 300000);
        } else {
            alert(data.message || data.error || 'Error refreshing URLs');
        }
    } catch (error) {
        console.error('Error refreshing URLs:', error);
        alert('Network error while refreshing URLs');
    } finally {
        hideLoading();
    }
}