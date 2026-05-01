/**
 * Status Color Coding System
 * Applies color-coding to projects and tasks based on their status
 */

(function() {
    'use strict';

    // Color mapping for different statuses
    const STATUS_CONFIG = {
        // Task statuses
        'completed': { color: 'success', class: 'status-completed', symbol: '✓' },
        'finished': { color: 'success', class: 'status-finished', symbol: '✓' },
        'done': { color: 'success', class: 'status-done', symbol: '✓' },
        
        'in-progress': { color: 'warning', class: 'status-progress', symbol: '●' },
        'current': { color: 'warning', class: 'status-current', symbol: '●' },
        'pending': { color: 'warning', class: 'status-pending', symbol: '●' },
        'active': { color: 'warning', class: 'status-active', symbol: '●' },
        
        'blocked': { color: 'danger', class: 'status-blocked', symbol: '⚠' },
        'failed': { color: 'danger', class: 'status-failed', symbol: '⚠' },
        'urgent': { color: 'danger', class: 'status-urgent', symbol: '⚠' },
        'overdue': { color: 'danger', class: 'status-overdue', symbol: '⚠' },
        
        'on-hold': { color: 'info', class: 'status-hold', symbol: '⏸' },
        'waiting': { color: 'info', class: 'status-waiting', symbol: '⏸' },
    };

    // Priority mapping
    const PRIORITY_CONFIG = {
        'high': { class: 'priority-high', color: '#E74C3C' },
        'critical': { class: 'priority-critical', color: '#E74C3C' },
        'medium': { class: 'priority-medium', color: '#F39C12' },
        'normal': { class: 'priority-normal', color: '#F39C12' },
        'low': { class: 'priority-low', color: '#27AE60' },
    };

    /**
     * Apply status styling to elements
     */
    function applyStatusStyling() {
        // Apply to task/project status badges
        document.querySelectorAll('[data-status], [class*="status-"]').forEach(element => {
            const status = element.getAttribute('data-status') || 
                          Array.from(element.classList).find(cls => cls.includes('status'));
            
            if (status && STATUS_CONFIG[status]) {
                element.classList.add(STATUS_CONFIG[status].class);
            }
        });

        // Apply to priority indicators
        document.querySelectorAll('[data-priority], [class*="priority-"]').forEach(element => {
            const priority = element.getAttribute('data-priority') || 
                           Array.from(element.classList).find(cls => cls.includes('priority'));
            
            if (priority && PRIORITY_CONFIG[priority]) {
                element.classList.add(PRIORITY_CONFIG[priority].class);
            }
        });
    }

    /**
     * Create status indicator dots
     */
    function createStatusIndicator(status) {
        const config = STATUS_CONFIG[status];
        if (!config) return '';

        const indicator = document.createElement('span');
        indicator.className = `status-indicator ${config.color}`;
        indicator.setAttribute('data-status', status);
        indicator.setAttribute('title', status);
        
        return indicator;
    }

    /**
     * Apply category styling based on project status
     */
    function applyCategoryColoring() {
        // Current projects
        document.querySelectorAll('[id*="current"], [class*="current"]').forEach(el => {
            if (el.textContent.toLowerCase().includes('current')) {
                el.closest('[class*="column"]')?.classList.add('project-category', 'current');
            }
        });

        // Planning projects
        document.querySelectorAll('[id*="planning"], [class*="planning"]').forEach(el => {
            if (el.textContent.toLowerCase().includes('planning')) {
                el.closest('[class*="column"]')?.classList.add('project-category', 'planning');
            }
        });

        // Finished projects
        document.querySelectorAll('[id*="finished"], [class*="finished"]').forEach(el => {
            if (el.textContent.toLowerCase().includes('finished')) {
                el.closest('[class*="column"]')?.classList.add('project-category', 'finished');
            }
        });
    }

    /**
     * Add visual feedback on status change
     */
    function setupStatusObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-status') {
                    const element = mutation.target;
                    const newStatus = element.getAttribute('data-status');
                    
                    // Remove old status classes
                    Object.values(STATUS_CONFIG).forEach(config => {
                        element.classList.remove(config.class);
                    });
                    
                    // Add new status class
                    if (newStatus && STATUS_CONFIG[newStatus]) {
                        element.classList.add(STATUS_CONFIG[newStatus].class);
                    }
                }
            });
        });

        // Observe all elements with data-status attribute
        document.querySelectorAll('[data-status]').forEach(el => {
            observer.observe(el, { attributes: true, attributeFilter: ['data-status'] });
        });
    }

    /**
     * Initialize status color system
     */
    function init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                applyStatusStyling();
                applyCategoryColoring();
                setupStatusObserver();
            });
        } else {
            applyStatusStyling();
            applyCategoryColoring();
            setupStatusObserver();
        }

        // Reapply when new content is dynamically added
        if (window.MutationObserver) {
            const bodyObserver = new MutationObserver(() => {
                applyStatusStyling();
            });
            
            bodyObserver.observe(document.body, {
                childList: true,
                subtree: true,
            });
        }
    }

    // Initialize when DOM is ready
    init();

    // Export for external use if needed
    window.StatusColorSystem = {
        applyStatusStyling,
        applyCategoryColoring,
        createStatusIndicator,
        STATUS_CONFIG,
        PRIORITY_CONFIG,
    };
})();