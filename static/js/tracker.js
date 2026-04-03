/**
 * Shaw P4 Action Tracker - Client-side interactivity
 */

document.addEventListener('DOMContentLoaded', () => {
    initStatusToggles();
    initAutoFadeFlash();
});

/**
 * AJAX status toggle for action items.
 * Cycles: open -> in_progress -> completed -> open
 */
function initStatusToggles() {
    const statusCycle = {
        'open': 'in_progress',
        'in_progress': 'completed',
        'completed': 'open',
        'blocked': 'open'
    };

    const statusIcons = {
        'open': '\u25CB',        // empty circle
        'in_progress': '\u25D4', // half circle
        'completed': '\u25CF',   // filled circle
        'blocked': '\u25A0'      // square
    };

    document.querySelectorAll('.status-toggle').forEach(btn => {
        btn.addEventListener('click', async () => {
            const itemId = btn.dataset.itemId;
            const currentStatus = btn.dataset.status;
            const newStatus = statusCycle[currentStatus];

            // Get CSRF token from any form on the page
            const csrfInput = document.querySelector('input[name="csrf_token"]');
            const csrfToken = csrfInput ? csrfInput.value : '';

            try {
                const resp = await fetch(`/tracker/action-items/${itemId}/status`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ status: newStatus })
                });

                if (resp.ok) {
                    const data = await resp.json();
                    btn.dataset.status = data.status;
                    btn.textContent = statusIcons[data.status];

                    // Update CSS classes
                    btn.className = `status-toggle status-${data.status}`;

                    // Update title text
                    const titleEl = btn.closest('.action-item').querySelector('.item-title');
                    if (titleEl) {
                        titleEl.classList.toggle('completed', data.status === 'completed');
                    }
                }
            } catch (err) {
                console.error('Failed to update status:', err);
            }
        });
    });
}

/**
 * Auto-fade flash messages after 4 seconds.
 */
function initAutoFadeFlash() {
    document.querySelectorAll('.flash').forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity 0.5s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 4000);
    });
}
