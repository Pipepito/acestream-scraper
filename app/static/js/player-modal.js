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

// Open the player options modal for a stream
async function showPlayerOptions(streamId) {
    if (!streamId) {
        console.error('No stream ID provided to showPlayerOptions');
        return;
    }
    
    // Get the base engine URL
    const aceEngineUrl = await getAceEngineUrl();
    
    // Create the modal HTML
    const modalHTML = `
    <div class="player-options-modal" id="playerOptionsModal">
        <div class="modal-content">
            <h3 style="margin-top: 0; text-align: center;">Stream Options</h3>
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
