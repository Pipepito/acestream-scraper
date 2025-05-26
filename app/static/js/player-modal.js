/**
 * Stream Player Options Modal Implementation
 */

// Function to get the base URL from config
async function getAceEngineUrl() {
    try {
        const response = await fetch('/api/config/ace-engine-url');
        const data = await response.json();
        return data.value || 'http://127.0.0.1:6878'; // Default to localhost if not set
    } catch (error) {
        console.error('Error fetching Ace Engine URL:', error);
        return 'http://127.0.0.1:6878'; // Default to localhost on error
    }
}

// Function to get the base URL from config
async function getBaseUrl() {
    try {
        const response = await fetch('/api/config/base_url');
        const data = await response.json();
        return data.value || 'acestream://'; // Default to acestream:// if not set
    } catch (error) {
        console.error('Error fetching base URL:', error);
        return 'acestream://'; // Default to acestream:// on error
    }
}

// Open the player options modal for a stream
async function showPlayerOptions(streamId) {
    if (!streamId) {
        console.error('No stream ID provided to showPlayerOptions');
        return;
    }
    
    // Get the base URLs
    const aceEngineUrl = await getAceEngineUrl();
    const baseUrl = await getBaseUrl();
    const fullStreamUrl = `${baseUrl}${streamId}`;
    
    // Create the modal HTML
    const modalHTML = `
    <div class="player-options-modal" id="playerOptionsModal">
        <div class="modal-content">
            <h3 style="margin-top: 0; text-align: center;">Stream Options</h3>
            <div style="margin-bottom: 20px;">
                <div class="input-group mb-2">
                    <input type="text" class="form-control" id="streamUrlInput" value="${fullStreamUrl}" readonly>
                    <button class="button modal-button" onclick="copyStreamUrl()" style="border-radius: 0 4px 4px 0;">
                        Copy URL
                    </button>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <button class="button modal-button" onclick="window.open('acestream://${streamId}', '_blank')">
                    Open in Acestream (PC/Android)
                </button>
                <button class="button modal-button" onclick="window.open('${aceEngineUrl}/server/api?method=open_in_player&player_id=&content_id=${streamId}', '_blank')">
                    Open stream HTTP (PC)
                </button>
                <button class="button modal-button" onclick="window.open('${aceEngineUrl}/ace/manifest.m3u8?id=${streamId}', '_blank')">
                    Multiplatform M3U8
                </button>
                <button class="button modal-button" onclick="window.open('vlc://${aceEngineUrl}/ace/manifest.m3u8?id=${streamId}', '_blank')">
                    Open in VLC
                </button>
                <button class="button modal-button cancel-button" onclick="document.getElementById('playerOptionsModal').remove()">
                    Cancel
                </button>
            </div>
        </div>
    </div>`;
    
    // Add the modal to the page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add escape key listener to close modal
    document.addEventListener('keydown', function closeOnEscape(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById('playerOptionsModal');
            if (modal) {
                modal.remove();
                document.removeEventListener('keydown', closeOnEscape);
            }
        }
    });
    
    // Add click outside to close
    document.getElementById('playerOptionsModal').addEventListener('click', function(event) {
        if (event.target === this) {
            this.remove();
        }
    });
}

// Function to copy the stream URL to clipboard
function copyStreamUrl() {
    const input = document.getElementById('streamUrlInput');
    input.select();
    document.execCommand('copy');
    
    // Show feedback
    const originalValue = input.value;
    input.value = 'Copied!';
    setTimeout(() => {
        input.value = originalValue;
    }, 1000);
}
