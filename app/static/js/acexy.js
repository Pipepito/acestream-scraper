/**
 * Acexy-specific functionality for Acestream Scraper
 */

// Check Acexy status
async function checkAcexyStatus(showLoadingIndicator = false) {
    try {
        if (showLoadingIndicator) showLoading();
        
        const response = await fetch('/api/config/acexy_status');
        const data = await response.json();
        
        // Update Acexy status badge in different views
        const dashboardStatusElement = document.getElementById('acexyStatus');
        const configStatusElement = document.getElementById('acexyStatusConfig');
        
        if (data.enabled) {
            const statusHTML = data.available ? 
                '<span class="badge bg-success">Online</span>' : 
                '<span class="badge bg-danger">Offline</span>';
                
            if (dashboardStatusElement) {
                dashboardStatusElement.innerHTML = statusHTML;
            }
            if (configStatusElement) {
                configStatusElement.innerHTML = statusHTML;
            }
            
            // Show Acexy features
            document.querySelectorAll('.acexy-feature').forEach(el => {
                el.classList.remove('d-none');
            });
        } else {
            const statusHTML = '<span class="badge bg-secondary">Disabled</span>';
            
            if (dashboardStatusElement) {
                dashboardStatusElement.innerHTML = statusHTML;
            }
            if (configStatusElement) {
                configStatusElement.innerHTML = statusHTML;
            }
            
            // Hide Acexy features
            document.querySelectorAll('.acexy-feature').forEach(el => {
                el.classList.add('d-none');
            });
        }
        
        return data;
    } catch (error) {
        console.error('Error checking Acexy status:', error);
        const errorHTML = '<span class="badge bg-warning">Error</span>';
        
        const dashboardStatusElement = document.getElementById('acexyStatus');
        if (dashboardStatusElement) {
            dashboardStatusElement.innerHTML = errorHTML;
        }
        
        const configStatusElement = document.getElementById('acexyStatusConfig');
        if (configStatusElement) {
            configStatusElement.innerHTML = errorHTML;
        }
        
        return { enabled: false, available: false };
    } finally {
        if (showLoadingIndicator) hideLoading();
    }
}

// Update Acexy status on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page with Acexy info
    if (document.getElementById('acexyStatus') || document.getElementById('acexyStatusConfig')) {
        checkAcexyStatus();
    }
});