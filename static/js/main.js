// Job Search Form Handling
document.addEventListener('DOMContentLoaded', function() {
    // Job Search Form
    const jobSearchForm = document.getElementById('job-search-form');
    if (jobSearchForm) {
        jobSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const searchParams = {
                keywords: formData.get('keywords'),
                location: formData.get('location'),
                jobType: formData.get('job-type')
            };

            // Show loading state
            document.getElementById('job-listings').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

            // Refresh job listings
            fetch('/search-jobs?' + new URLSearchParams(searchParams))
                .then(response => response.text())
                .then(html => {
                    document.getElementById('job-listings').innerHTML = html;
                    initializeJobButtons(); // Initialize buttons after content update
                });
        });
    }

    // Apply for Job
    function initializeJobButtons() {
        const viewDetailsButtons = document.querySelectorAll('[data-bs-target^="#jobModal"]');
        viewDetailsButtons.forEach(button => {
            const modalId = button.getAttribute('data-bs-target');
            const modal = document.querySelector(modalId);
            const applyButton = modal.querySelector('.apply-btn');

            applyButton.addEventListener('click', function() {
                const jobId = this.getAttribute('data-job-id');
                window.location.href = `/optimize-resume/${jobId}`;
            });
        });

        const applyButtons = document.querySelectorAll('.apply-btn:not([data-initialized])');
        applyButtons.forEach(button => {
            button.setAttribute('data-initialized', 'true');
            button.addEventListener('click', function() {
                const jobId = this.getAttribute('data-job-id');
                window.location.href = `/optimize-resume/${jobId}`;
            });
        });
    }

    // Initialize buttons on page load
    initializeJobButtons();

    // Application Status Updates
    const updateButtons = document.querySelectorAll('.update-application');
    updateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const applicationId = this.dataset.applicationId;
            const form = document.getElementById(`update-form-${applicationId}`);
            const formData = new FormData(form);

            fetch(`/update-application/${applicationId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    showAlert('Failed to update application status.', 'danger');
                }
            });
        });
    });

    // Resume Optimization
    const optimizeButton = document.getElementById('optimize-resume');
    if (optimizeButton) {
        optimizeButton.addEventListener('click', function() {
            const jobDescription = document.getElementById('job-description').value;
            const resumeText = document.getElementById('resume-text').value;
            
            if (!jobDescription || !resumeText) {
                showAlert('Please provide both job description and resume.', 'warning');
                return;
            }
            
            fetch('/optimize-resume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    job_description: jobDescription,
                    resume_text: resumeText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update optimization preview modal
                    document.getElementById('changes-list').innerHTML = data.changes.map(
                        change => `<li class="list-group-item">${change}</li>`
                    ).join('');
                    document.getElementById('optimized-resume').textContent = data.optimized_resume;
                    
                    // Show modal
                    new bootstrap.Modal(document.getElementById('optimizationModal')).show();
                }
            });
        });
    }

    // Apply Optimization Changes
    const applyOptimization = document.getElementById('apply-optimization');
    if (applyOptimization) {
        applyOptimization.addEventListener('click', function() {
            const optimizedResume = document.getElementById('optimized-resume').textContent;
            document.getElementById('resume-text').value = optimizedResume;
            bootstrap.Modal.getInstance(document.getElementById('optimizationModal')).hide();
            showAlert('Resume optimization applied!', 'success');
        });
    }


});

// Utility Functions
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('main.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}