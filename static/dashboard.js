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

function applyFilters(rows, filters) {
    rows.forEach(row => {
        const visible = filters.every(({ column, value }) =>
            row.cells[column].textContent.toLowerCase().includes(value));
        row.hidden = !visible;
    });
}

function sortRows(tbody, column, direction) {
    const factor = direction === 'ascending' ? 1 : -1;
    const rows = Array.from(tbody.rows).sort((a, b) =>
        factor * a.cells[column].textContent.trim().localeCompare(
            b.cells[column].textContent.trim(), undefined, { numeric: true }));
    rows.forEach(row => tbody.appendChild(row));
}

document.addEventListener('DOMContentLoaded', () => {
    const tbody = document.querySelector('tbody');
    const filterInputs = document.querySelectorAll('.filter-input');
    const headers = document.querySelectorAll('th.sortable');

    filterInputs.forEach(input => {
        input.addEventListener('input', () => {
            const filters = Array.from(filterInputs)
                .filter(i => i.value)
                .map(i => ({ column: Number(i.dataset.column), value: i.value.toLowerCase() }));
            applyFilters(Array.from(tbody.rows), filters);
        });
    });

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const direction = header.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
            headers.forEach(h => h.removeAttribute('aria-sort'));
            header.setAttribute('aria-sort', direction);
            sortRows(tbody, Number(header.dataset.column), direction);
        });
    });
});
