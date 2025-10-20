// History page JavaScript

let currentPage = 0;
const pageSize = 50;
let autoRefreshInterval = null;

// Initialize history page
document.addEventListener('DOMContentLoaded', function() {
    loadHistory();
    
    // Set up auto-refresh every 3 seconds
    autoRefreshInterval = setInterval(() => {
        loadHistory();
    }, 3000);
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});

// Load transfer history
async function loadHistory() {
    try {
        const status = document.getElementById('filter-status').value;
        const params = new URLSearchParams({
            limit: pageSize,
            offset: currentPage * pageSize
        });
        
        if (status) {
            params.append('status', status);
        }
        
        const data = await apiGet(`/api/transfers?${params}`);
        const tbody = document.getElementById('history-table-body');
        
        if (data.transfers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">No transfers found</td></tr>';
            updatePagination(0);
            return;
        }
        
        tbody.innerHTML = data.transfers.map(transfer => `
            <tr>
                <td>${transfer.device_name}</td>
                <td>${getStatusBadge(transfer.status)}</td>
                <td>${transfer.files_transferred || 0}</td>
                <td>${transfer.files_failed || 0}</td>
                <td>${transfer.files_skipped || 0}</td>
                <td>${formatTimestamp(transfer.started_at)}</td>
                <td>${formatDuration(transfer.duration_seconds)}</td>
                <td><small>${transfer.drop_location || 'N/A'}</small></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteTransfer('${transfer.transfer_id}')" title="Delete record">🗑</button>
                </td>
            </tr>
        `).join('');
        
        updatePagination(data.transfers.length);
    } catch (error) {
        console.error('Error loading history:', error);
        document.getElementById('history-table-body').innerHTML = 
            '<tr><td colspan="9" class="text-center">Error loading history</td></tr>';
    }
}

// Update pagination controls
function updatePagination(count) {
    const info = document.getElementById('pagination-info');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    
    const start = currentPage * pageSize + 1;
    const end = start + count - 1;
    
    info.textContent = count > 0 ? `Showing ${start}-${end}` : 'No transfers';
    
    prevBtn.disabled = currentPage === 0;
    nextBtn.disabled = count < pageSize;
}

// Previous page
function previousPage() {
    if (currentPage > 0) {
        currentPage--;
        loadHistory();
    }
}

// Next page
function nextPage() {
    currentPage++;
    loadHistory();
}

// Delete a transfer record
async function deleteTransfer(transferId) {
    if (!confirm('Are you sure you want to delete this transfer record?')) {
        return;
    }
    
    try {
        await apiDelete(`/api/transfers/${transferId}`);
        showToast('Transfer record deleted', 'success');
        loadHistory();
    } catch (error) {
        console.error('Error deleting transfer:', error);
        showToast('Error deleting transfer', 'error');
    }
}

// WebSocket handlers for real-time updates
window.handleTransferUpdate = function(transfer) {
    loadHistory();
};

window.handleTransferComplete = function(transfer) {
    loadHistory();
};

