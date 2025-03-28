/**
 * URL management functionality for Acestream Scraper
 */

// Toggle URL enabled/disabled status
async function toggleUrl(id, enable) {
    return await makeApiRequest(
        `/api/urls/${id}`,
        {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: enable })
        },
        enable ? 'URL enabled successfully' : 'URL disabled successfully'
    );
}

// Delete URL
async function deleteUrl(id) {
    if (!confirm('Are you sure you want to delete this URL? This will also remove all associated channels.')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`/api/urls/${id}`, {
            method: 'DELETE'
        });
        
        if (response.status === 204) {
            showAlert('success', 'URL deleted successfully');
            // Refresh the data if needed
            if (typeof refreshData === 'function') {
                await refreshData();
            }
            return true;
        }
        
        const data = await response.text();
        throw new Error(data || 'Failed to delete URL');
        
    } catch (error) {
        console.error('Error deleting URL:', error);
        showAlert('error', 'Failed to delete URL: ' + error.message);
        return false;
    } finally {
        hideLoading();
    }
}

// Refresh a single URL
async function refreshUrl(id) {
    try {
        showLoading();
        const response = await fetch(`/api/urls/${id}/refresh`, {
            method: 'POST'
        });
        
        await handleApiResponse(response, 'URL refreshed successfully');
        
        // Refresh dashboard data
        await refreshData();
    } catch (error) {
        console.error('Error refreshing URL:', error);
        showAlert('danger', 'Failed to refresh URL: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Add new URL 
async function addUrl(url, urlType = 'regular') {
    try {
        showLoading();
        const response = await fetch('/api/urls/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: url,
                url_type: urlType
            })
        });
        
        await handleApiResponse(response, 'URL added successfully');
        
        // Refresh dashboard data
        await refreshData();
        return true;
    } catch (error) {
        console.error('Error adding URL:', error);
        showAlert('danger', 'Failed to add URL: ' + error.message);
        return false;
    } finally {
        hideLoading();
    }
}

// Refresh all URLs
async function refreshAllUrls() {
    if (!confirm('Are you sure you want to refresh all URLs? This might take a while.')) {
        return { success: false };
    }

    const { success, data } = await makeApiRequest(
        '/api/urls/refresh',
        { method: 'POST' },
        `URLs refresh started`
    );
    
    if (success) {
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
                showAlert('success', 'All URLs have been processed');
            }
        }, 5000); // Poll every 5 seconds
        
        // Stop polling after 5 minutes max
        setTimeout(() => clearInterval(pollInterval), 300000);
    }
    
    return { success, data };
}