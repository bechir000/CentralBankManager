/**
 * Central Bank XML Data Processing System
 * Main JavaScript file for front-end functionality
 */

// Initialize tooltips everywhere
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Add current year to footer
    const currentYear = new Date().getFullYear();
    document.querySelectorAll('.current-year').forEach(el => {
        el.textContent = currentYear;
    });
    
    // Add active class to current nav item based on URL
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || 
            (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
    
    // Initialize any DataTables (if not already initialized on the page)
    if (typeof $.fn.dataTable !== 'undefined') {
        $('.datatable:not(.dataTable)').each(function() {
            $(this).DataTable({
                responsive: true,
                language: {
                    search: "Search:",
                    lengthMenu: "Show _MENU_ entries per page",
                    info: "Showing _START_ to _END_ of _TOTAL_ entries",
                    emptyTable: "No data available"
                }
            });
        });
    }
});

/**
 * Format a date string for display
 * @param {string} dateStr - Date string in ISO format
 * @returns {string} Formatted date string
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

/**
 * Format a number with thousands separators and decimal places
 * @param {number} number - The number to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted number string
 */
function formatNumber(number, decimals = 2) {
    if (number === null || number === undefined) return '';
    
    return Number(number).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Show a loading spinner in a container
 * @param {string} containerId - ID of the container element
 * @param {string} message - Optional message to display
 */
function showLoading(containerId, message = 'Loading...') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const spinner = document.createElement('div');
    spinner.className = 'text-center p-5';
    spinner.innerHTML = `
        <div class="spinner-border text-primary mb-3" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="lead">${message}</p>
    `;
    
    container.innerHTML = '';
    container.appendChild(spinner);
}

/**
 * Handle AJAX errors and display appropriate messages
 * @param {object} xhr - XMLHttpRequest object
 * @param {string} containerId - Optional container ID to display error in
 */
function handleAjaxError(xhr, containerId = null) {
    let errorMessage = 'An error occurred while processing your request.';
    
    if (xhr.responseJSON && xhr.responseJSON.message) {
        errorMessage = xhr.responseJSON.message;
    } else if (xhr.status === 404) {
        errorMessage = 'The requested resource was not found.';
    } else if (xhr.status === 403) {
        errorMessage = 'You do not have permission to perform this action.';
    } else if (xhr.status === 500) {
        errorMessage = 'An internal server error occurred. Please try again later.';
    }
    
    if (containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i> 
                    ${errorMessage}
                </div>
            `;
        }
    } else {
        alert(`Error: ${errorMessage}`);
    }
}
