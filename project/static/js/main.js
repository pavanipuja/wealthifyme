// WealthifyMe - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (mobileMenuToggle && navbarMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
        });
    }
    
    // Flash Messages Auto-close
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000);
    });
    
    // Initialize Chart.js charts if they exist on the page
    initializeCharts();
    
    // Initialize Expense Form
    initExpenseForm();
    
    // Initialize Budget Form
    initBudgetForm();
    
    // Initialize Goal Form
    initGoalForm();
    
    // Add animation to cards
    animateOnScroll();
});

// Chart initialization
function initializeCharts() {
    // Monthly Spending Trend Chart
    const monthlySpendingCtx = document.getElementById('monthlySpendingChart');
    if (monthlySpendingCtx) {
        const monthlySpendingData = JSON.parse(monthlySpendingCtx.dataset.spending || '[]');
        
        new Chart(monthlySpendingCtx, {
            type: 'line',
            data: {
                labels: monthlySpendingData.map(item => item.month),
                datasets: [{
                    label: 'Monthly Spending',
                    data: monthlySpendingData.map(item => item.total),
                    borderColor: '#4ade80',
                    backgroundColor: 'rgba(74, 222, 128, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#4ade80',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '$' + context.raw.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Spending by Category Chart
    const categorySpendingCtx = document.getElementById('categorySpendingChart');
    if (categorySpendingCtx) {
        const categoryData = JSON.parse(categorySpendingCtx.dataset.categories || '[]');
        
        new Chart(categorySpendingCtx, {
            type: 'doughnut',
            data: {
                labels: categoryData.map(item => item.name),
                datasets: [{
                    data: categoryData.map(item => item.total),
                    backgroundColor: categoryData.map(item => item.color),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }
    
    // Budget Progress Charts
    const budgetCharts = document.querySelectorAll('.budget-chart');
    budgetCharts.forEach(chartCanvas => {
        const spent = parseFloat(chartCanvas.dataset.spent);
        const budget = parseFloat(chartCanvas.dataset.budget);
        const percentage = Math.min((spent / budget) * 100, 100);
        const isOverBudget = spent > budget;
        
        new Chart(chartCanvas, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [spent, Math.max(budget - spent, 0)],
                    backgroundColor: [
                        isOverBudget ? '#ef4444' : '#4ade80',
                        '#e2e8f0'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '80%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            }
        });
        
        // Add percentage text in center
        const chartParent = chartCanvas.parentElement;
        const percentText = document.createElement('div');
        percentText.className = 'chart-percent';
        percentText.innerHTML = `${Math.round(percentage)}%`;
        percentText.style.position = 'absolute';
        percentText.style.top = '50%';
        percentText.style.left = '50%';
        percentText.style.transform = 'translate(-50%, -50%)';
        percentText.style.fontSize = '1rem';
        percentText.style.fontWeight = '600';
        percentText.style.color = isOverBudget ? '#ef4444' : '#1e293b';
        chartParent.style.position = 'relative';
        chartParent.appendChild(percentText);
    });
    
    // Goal Progress Charts
    const goalCharts = document.querySelectorAll('.goal-chart');
    goalCharts.forEach(chartCanvas => {
        const current = parseFloat(chartCanvas.dataset.current);
        const target = parseFloat(chartCanvas.dataset.target);
        const percentage = Math.min((current / target) * 100, 100);
        
        new Chart(chartCanvas, {
            type: 'bar',
            data: {
                labels: ['Progress'],
                datasets: [{
                    data: [percentage],
                    backgroundColor: ['#3b82f6'],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function() {
                                return `$${current.toFixed(2)} of $${target.toFixed(2)} (${Math.round(percentage)}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: 100,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
    });
}

// Expense Form Handling
function initExpenseForm() {
    const expenseForm = document.getElementById('expenseForm');
    if (!expenseForm) return;
    
    const amountInput = document.getElementById('amount');
    const descriptionInput = document.getElementById('description');
    const dateInput = document.getElementById('date');
    const categorySelect = document.getElementById('category');
    
    // Set default date to today
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
    
    // Format amount as currency
    if (amountInput) {
        amountInput.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    }
    
    // Form submission
    expenseForm.addEventListener('submit', function(e) {
        let valid = true;
        
        if (amountInput && (isNaN(amountInput.value) || amountInput.value <= 0)) {
            showInputError(amountInput, 'Please enter a valid amount');
            valid = false;
        }
        
        if (descriptionInput && !descriptionInput.value.trim()) {
            showInputError(descriptionInput, 'Please enter a description');
            valid = false;
        }
        
        if (dateInput && !dateInput.value) {
            showInputError(dateInput, 'Please select a date');
            valid = false;
        }
        
        if (categorySelect && !categorySelect.value) {
            showInputError(categorySelect, 'Please select a category');
            valid = false;
        }
        
        if (!valid) {
            e.preventDefault();
        }
    });
}

// Budget Form Handling
function initBudgetForm() {
    const budgetForm = document.getElementById('budgetForm');
    if (!budgetForm) return;
    
    const amountInput = document.getElementById('budget_amount');
    const categorySelect = document.getElementById('budget_category');
    const monthInput = document.getElementById('budget_month');
    const yearInput = document.getElementById('budget_year');
    
    // Set default month and year to current
    if (monthInput && !monthInput.value) {
        const currentMonth = new Date().getMonth() + 1;
        monthInput.value = currentMonth;
    }
    
    if (yearInput && !yearInput.value) {
        const currentYear = new Date().getFullYear();
        yearInput.value = currentYear;
    }
    
    // Format amount as currency
    if (amountInput) {
        amountInput.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    }
    
    // Form submission
    budgetForm.addEventListener('submit', function(e) {
        let valid = true;
        
        if (amountInput && (isNaN(amountInput.value) || amountInput.value <= 0)) {
            showInputError(amountInput, 'Please enter a valid amount');
            valid = false;
        }
        
        if (categorySelect && !categorySelect.value) {
            showInputError(categorySelect, 'Please select a category');
            valid = false;
        }
        
        if (!valid) {
            e.preventDefault();
        }
    });
}

// Goal Form Handling
function initGoalForm() {
    const goalForm = document.getElementById('goalForm');
    if (!goalForm) return;
    
    const nameInput = document.getElementById('goal_name');
    const targetInput = document.getElementById('goal_target');
    const currentInput = document.getElementById('goal_current');
    const deadlineInput = document.getElementById('goal_deadline');
    
    // Format amount as currency
    if (targetInput) {
        targetInput.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    }
    
    if (currentInput) {
        currentInput.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    }
    
    // Form submission
    goalForm.addEventListener('submit', function(e) {
        let valid = true;
        
        if (nameInput && !nameInput.value.trim()) {
            showInputError(nameInput, 'Please enter a goal name');
            valid = false;
        }
        
        if (targetInput && (isNaN(targetInput.value) || targetInput.value <= 0)) {
            showInputError(targetInput, 'Please enter a valid target amount');
            valid = false;
        }
        
        if (!valid) {
            e.preventDefault();
        }
    });
}

// Helper function to show input error
function showInputError(inputElement, message) {
    inputElement.classList.add('is-invalid');
    
    let errorElement = inputElement.nextElementSibling;
    if (!errorElement || !errorElement.classList.contains('error-message')) {
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.style.color = 'var(--error-500)';
        errorElement.style.fontSize = '0.875rem';
        errorElement.style.marginTop = '0.25rem';
        inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling);
    }
    
    errorElement.textContent = message;
    
    inputElement.addEventListener('input', function() {
        this.classList.remove('is-invalid');
        if (errorElement) {
            errorElement.textContent = '';
        }
    }, { once: true });
}

// Animation on scroll
function animateOnScroll() {
    const animatedElements = document.querySelectorAll('.card, .stat-card, .budget-card, .goal-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeIn');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// Currency formatter
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Date formatter
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}