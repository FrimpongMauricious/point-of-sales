/* QuickMart POS — app.js */

// Modal helpers
function openModal(id) {
    const m = document.getElementById(id);
    if (m) { m.classList.add('open'); }
}
function closeModal(id) {
    const m = document.getElementById(id);
    if (m) { m.classList.remove('open'); }
}

// Close modal on overlay click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
    }
});

// Real-time search for tables
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const q = this.value.toLowerCase();
            document.querySelectorAll('.searchable-row').forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(q) ? '' : 'none';
            });
        });
    }

    // Auto-close toasts
    document.querySelectorAll('[data-auto-close]').forEach(toast => {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity .4s';
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    });
});

// Toast helper for JS-triggered messages
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer') || createToastContainer();
    const icons = { success: '<i class="fas fa-check-circle"></i>', danger: '<i class="fas fa-times-circle"></i>', warning: '<i class="fas fa-exclamation-triangle"></i>', info: '<i class="fas fa-info-circle"></i>' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || '<i class="fas fa-info-circle"></i>'}</span>
        <span class="toast-msg">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity .4s';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

function createToastContainer() {
    const c = document.createElement('div');
    c.className = 'toast-container';
    c.id = 'toastContainer';
    document.body.appendChild(c);
    return c;
}

// Escape key closes modals
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
    }
});
