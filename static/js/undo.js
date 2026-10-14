/**
 * E-CÜZDAN v15.0 - Undo JavaScript
 * Undo functionality for destructive actions
 */

// Undo Queue
let undoQueue = [];
const MAX_UNDO_ITEMS = 10;

// Add Action to Undo Queue
export function addToUndoQueue(action) {
    undoQueue.push({
        ...action,
        timestamp: Date.now()
    });
    
    // Keep only max items
    if (undoQueue.length > MAX_UNDO_ITEMS) {
        undoQueue.shift();
    }
    
    // Save to localStorage
    saveToLocalStorage('undo_queue', undoQueue);
}

// Get Undo Queue
export function getUndoQueue() {
    return undoQueue;
}

// Undo Last Action
export function undoLastAction() {
    if (undoQueue.length === 0) {
        showToast('Geri alınacak işlem yok', 'warning');
        return;
    }
    
    const action = undoQueue.pop();
    saveToLocalStorage('undo_queue', undoQueue);
    
    // Execute undo callback
    if (action.undoCallback && typeof action.undoCallback === 'function') {
        try {
            action.undoCallback(action.data);
            showToast(`${action.description} geri alındı`, 'success');
        } catch (error) {
            console.error('Undo failed:', error);
            showToast('Geri alma başarısız', 'error');
        }
    }
}

// Show Undo Toast
export function showUndoToast(message, undoCallback, data = null, duration = 6000) {
    if (typeof window.showToast === 'function') {
        window.showToast(message, 'info', duration, {
            text: 'Geri Al',
            onClick: () => {
                if (typeof undoCallback === 'function') {
                    try {
                        undoCallback(data);
                        window.showToast('İşlem geri alındı', 'success');
                    } catch (error) {
                        console.error('Undo failed:', error);
                        window.showToast('Geri alma başarısız', 'error');
                    }
                }
            }
        });
        return;
    }

    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast-item bg-slate-800 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3';
    toast.innerHTML = `
        <span class="text-sm font-semibold">${message}</span>
        <button type="button" class="undo-btn text-emerald-400 font-bold text-xs hover:underline cursor-pointer">
            Geri Al
        </button>
    `;
    
    const btn = toast.querySelector('.undo-btn');
    if (btn) {
        btn.addEventListener('click', () => {
            if (typeof undoCallback === 'function') {
                try {
                    undoCallback(data);
                    if (typeof window.showToast === 'function') {
                        window.showToast('İşlem geri alındı', 'success');
                    }
                } catch (error) {
                    console.error('Undo failed:', error);
                }
            }
            toast.remove();
        });
    }
    
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) toast.remove();
    }, duration);
}

// Execute Undo from Toast
export function executeUndo(button) {
    const toast = button.closest('.toast-item');
    if (toast && toast.undoCallback) {
        try {
            toast.undoCallback(toast.undoData);
            if (typeof window.showToast === 'function') {
                window.showToast('İşlem geri alındı', 'success');
            }
        } catch (error) {
            console.error('Undo failed:', error);
            if (typeof window.showToast === 'function') {
                window.showToast('Geri alma başarısız', 'error');
            }
        }
        toast.remove();
    }
}

// Recently Deleted Items
export function addToRecentlyDeleted(item, type) {
    const recent = getFromLocalStorage('recently_deleted', []);
    
    recent.unshift({
        ...item,
        type: type,
        timestamp: Date.now()
    });
    
    // Keep only max items
    const trimmed = recent.slice(0, 20);
    saveToLocalStorage('recently_deleted', trimmed);
}

export function getRecentlyDeleted() {
    return getFromLocalStorage('recently_deleted', []);
}

export function restoreFromRecentlyDeleted(id) {
    const recent = getRecentlyDeleted();
    const item = recent.find(item => item.id === id);
    
    if (item) {
        // Remove from recently deleted
        const filtered = recent.filter(i => i.id !== id);
        saveToLocalStorage('recently_deleted', filtered);
        
        return item;
    }
    
    return null;
}

// Render Recently Deleted Panel
export function renderRecentlyDeletedPanel(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const recent = getRecentlyDeleted();
    
    if (recent.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-400">Son silinen öğe yok</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="space-y-2">
            ${recent.map(item => `
                <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200">
                    <div class="flex items-center gap-2">
                        <span class="text-lg">${item.icon || '📄'}</span>
                        <div>
                            <p class="text-xs font-semibold text-slate-700">${item.name || item.title || 'Öğe'}</p>
                            <p class="text-[10px] text-slate-400">${item.type || 'Genel'}</p>
                        </div>
                    </div>
                    <button onclick="restoreItem('${item.id}')" class="text-emerald-600 font-bold text-[10px] hover:underline">
                        Geri Yükle
                    </button>
                </div>
            `).join('')}
        </div>
    `;
}

// Restore Item
function restoreItem(id) {
    const item = restoreFromRecentlyDeleted(id);
    
    if (item) {
        // Trigger restore callback (would be implemented per use case)
        console.log('Restoring item:', item);
        showToast('Öğe geri yüklendi', 'success');
        
        // Refresh panel
        renderRecentlyDeletedPanel('recently-deleted-panel');
    }
}

// Clear Undo Queue
export function clearUndoQueue() {
    undoQueue = [];
    saveToLocalStorage('undo_queue', []);
}

// Clear Recently Deleted
export function clearRecentlyDeleted() {
    saveToLocalStorage('recently_deleted', []);
}

// Export for global access
window.showUndoToast = showUndoToast;
window.executeUndo = executeUndo;
window.restoreItem = restoreItem;

window.ECuzdanUndo = {
    addToUndoQueue,
    getUndoQueue,
    undoLastAction,
    showUndoToast,
    addToRecentlyDeleted,
    getRecentlyDeleted,
    restoreFromRecentlyDeleted,
    renderRecentlyDeletedPanel,
    clearUndoQueue,
    clearRecentlyDeleted
};
