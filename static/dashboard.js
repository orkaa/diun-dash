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

document.addEventListener('DOMContentLoaded', () => {
	const field = document.getElementById('mobile-filter-field');
	const query = document.getElementById('mobile-filter-query');
	const sortField = document.getElementById('mobile-sort-field');
	const directionButton = document.getElementById('mobile-sort-direction');
	const inputs = Array.from(document.querySelectorAll('thead .filter-input'));
	const headers = Array.from(document.querySelectorAll('thead th.sortable'));

	function syncFilter() {
		inputs.forEach(input => {
			input.value = input.dataset.column === field.value ? query.value : '';
		});
		inputs[Number(field.value)].dispatchEvent(new Event('input', { bubbles: true }));
	}
	field.addEventListener('change', () => {
		query.value = '';
		syncFilter();
	});
	query.addEventListener('input', syncFilter);

	function refreshMobileSort() {
		const active = headers.find(h => h.hasAttribute('aria-sort'));
		if (!active) return;
		const direction = active.getAttribute('aria-sort');
		const ascending = direction === 'ascending';
		sortField.value = active.dataset.column;
		directionButton.textContent = ascending ? '↑ Asc' : '↓ Desc';
		directionButton.setAttribute('aria-label', ascending ? 'Sort ascending' : 'Sort descending');
		directionButton.setAttribute('aria-pressed', String(!ascending));
	}

	function syncSort(column, direction) {
		const header = headers.find(h => h.dataset.column === column);
		if (!header) return;
		headers.forEach(h => h.removeAttribute('aria-sort'));
		header.setAttribute('aria-sort', direction);
		sortRows(document.querySelector('tbody'), Number(column), direction);
		refreshMobileSort();
	}

	if (!headers.some(h => h.hasAttribute('aria-sort'))) {
		const createdHeader = headers.find(h => h.dataset.column === '7');
		if (createdHeader) createdHeader.setAttribute('aria-sort', 'descending');
	}
	refreshMobileSort();

	headers.forEach(header => {
		header.addEventListener('click', refreshMobileSort);
	});

	sortField.addEventListener('change', () => syncSort(sortField.value, 'ascending'));
	directionButton.addEventListener('click', () => {
		const selected = headers.find(h => h.dataset.column === sortField.value);
		const next = selected && selected.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
		syncSort(sortField.value, next);
	});
});
