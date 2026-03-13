async function markAsFixed(id) {
    const response = await fetch(`/updates/${id}`, {
        method: 'DELETE',
    });
    if (response.ok) {
        location.reload();
    } else {
        alert('Failed to mark as fixed.');
    }
}

async function fixAll() {
    if (!confirm('Are you sure you want to fix all entries? This will remove all current updates from the dashboard.')) {
        return;
    }

    const response = await fetch('/updates', {
        method: 'DELETE',
    });
    if (response.ok) {
        location.reload();
    } else {
        alert('Failed to fix all entries.');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-fix-id]').forEach(button => {
        button.addEventListener('click', () => markAsFixed(button.dataset.fixId));
    });

    const fixAllBtn = document.getElementById('fix-all-btn');
    if (fixAllBtn) {
        fixAllBtn.addEventListener('click', fixAll);
    }
});
