/**
 * UI/UX Enhancements for TaskDocuManagement
 * Vanilla JS - No HTML structure changes
 */

// Initialize all enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scroll behavior
    enableSmoothScroll();
    
    // Enhance form inputs with focus effects
    enhanceFormInputs();
    
    // Add ripple effect to buttons
    addRippleEffect();
    
    // Enhanced navigation highlighting
    enhanceNavigation();
    
    // Add card animations
    addCardAnimations();
    
    // Improve form validation feedback
    improveFormValidation();
    
    // Add loading states to buttons
    addLoadingStates();
    
    // Enhance modals with better transitions
    enhanceModals();
});

/**
 * Enable smooth scroll behavior across the application
 */
function enableSmoothScroll() {
    document.documentElement.style.scrollBehavior = 'smooth';
}

/**
 * Enhance form inputs with visual feedback
 */
function enhanceFormInputs() {
    const inputs = document.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        // Add focus event listener
        input.addEventListener('focus', function() {
            this.parentElement.style.position = 'relative';
            if (this.parentElement.querySelector('.input-underline')) return;
            
            const underline = document.createElement('div');
            underline.className = 'input-underline';
            underline.style.cssText = `
                position: absolute;
                bottom: 0;
                left: 0;
                height: 2px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                width: 100%;
                transform: scaleX(0);
                transform-origin: left;
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            `;
            
            this.parentElement.style.position = 'relative';
            this.parentElement.appendChild(underline);
            
            const existingUnderline = this.parentElement.querySelector('.input-underline');
            if (existingUnderline) {
                existingUnderline.style.transform = 'scaleX(1)';
            }
        });
        
        input.addEventListener('blur', function() {
            const underline = this.parentElement.querySelector('.input-underline');
            if (underline) {
                underline.style.transform = 'scaleX(0)';
            }
        });
    });
}

/**
 * Add ripple effect to buttons on click
 */
function addRippleEffect() {
    const buttons = document.querySelectorAll('button:not(.modal-close)');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            const ripple = document.createElement('div');
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
                animation: rippleEffect 0.6s ease-out forwards;
                z-index: 1;
            `;
            
            // Inject keyframes if not present
            if (!document.querySelector('style[data-ripple]')) {
                const style = document.createElement('style');
                style.setAttribute('data-ripple', 'true');
                style.textContent = `
                    @keyframes rippleEffect {
                        0% {
                            transform: scale(0);
                            opacity: 1;
                        }
                        100% {
                            transform: scale(1);
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
            
            if (this.style.position === 'static') {
                this.style.position = 'relative';
            }
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
}

/**
 * Enhance navigation with active state highlighting
 */
function enhanceNavigation() {
    const navLinks = document.querySelectorAll('.side-bar a, .buttons a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

/**
 * Add card animations on scroll
 */
function addCardAnimations() {
    const cards = document.querySelectorAll('.card, .project-card, .member-card, .task-card');
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease-out forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Inject keyframes if not present
    if (!document.querySelector('style[data-fade-in]')) {
        const style = document.createElement('style');
        style.setAttribute('data-fade-in', 'true');
        style.textContent = `
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    cards.forEach(card => observer.observe(card));
}

/**
 * Improve form validation feedback
 */
function improveFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[required], textarea[required], select[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    addValidationError(input);
                } else {
                    removeValidationError(input);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Add validation error styling
 */
function addValidationError(input) {
    input.style.borderColor = '#f8d7da';
    input.style.backgroundColor = '#fff5f7';
    
    if (!input.parentElement.querySelector('.error-message')) {
        const error = document.createElement('div');
        error.className = 'error-message';
        error.textContent = 'This field is required';
        error.style.cssText = `
            color: #c82333;
            font-size: 0.85rem;
            margin-top: 0.25rem;
            animation: fadeInUp 0.3s ease-out;
        `;
        input.parentElement.appendChild(error);
    }
}

/**
 * Remove validation error styling
 */
function removeValidationError(input) {
    input.style.borderColor = '';
    input.style.backgroundColor = '';
    
    const error = input.parentElement.querySelector('.error-message');
    if (error) {
        error.remove();
    }
}

/**
 * Add loading states to submit buttons
 */
function addLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.textContent;
            
            form.addEventListener('submit', function() {
                if (this.checkValidity()) {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.7';
                    submitBtn.innerHTML = '⏳ Processing...';
                    
                    setTimeout(() => {
                        submitBtn.disabled = false;
                        submitBtn.style.opacity = '1';
                        submitBtn.innerHTML = originalText;
                    }, 2000);
                }
            });
        }
    });
}

/**
 * Enhance modals with better transitions
 */
function enhanceModals() {
    const modals = document.querySelectorAll('.modal, .create-project');
    
    modals.forEach(modal => {
        const closeButton = modal.querySelector('.modal-close, #close-create-project');
        
        if (closeButton) {
            closeButton.addEventListener('click', function(e) {
                e.preventDefault();
                closeModal(modal);
            });
        }
    });
}

/**
 * Smoothly close modal with animation
 */
function closeModal(modal) {
    modal.style.animation = 'fadeOut 0.3s ease-out forwards';
    
    if (!document.querySelector('style[data-fade-out]')) {
        const style = document.createElement('style');
        style.setAttribute('data-fade-out', 'true');
        style.textContent = `
            @keyframes fadeOut {
                from {
                    opacity: 1;
                }
                to {
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

/**
 * Utility: Add hover effects to interactive elements
 */
document.addEventListener('DOMContentLoaded', function() {
    const interactiveElements = document.querySelectorAll('a[href], button, input[type="checkbox"], input[type="radio"]');
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        });
    });
});

/**
 * Add keyboard shortcuts for better UX
 */
document.addEventListener('keydown', function(e) {
    // Escape key closes modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show, .create-project:visible');
        if (openModal) {
            closeModal(openModal);
        }
    }
    
    // Ctrl/Cmd + K for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-bar input');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

/**
 * Add scroll-to-top button functionality
 */
window.addEventListener('scroll', function() {
    if (window.scrollY > 300) {
        if (!document.querySelector('#scroll-to-top')) {
            const button = document.createElement('button');
            button.id = 'scroll-to-top';
            button.innerHTML = '↑';
            button.style.cssText = `
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                cursor: pointer;
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                z-index: 999;
            `;
            
            button.addEventListener('click', function() {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
            
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
                this.style.boxShadow = '0 8px 25px rgba(102, 126, 234, 0.4)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)';
            });
            
            document.body.appendChild(button);
        }
    } else {
        const button = document.querySelector('#scroll-to-top');
        if (button) button.remove();
    }
});
