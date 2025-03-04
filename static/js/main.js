// Job Search Form Handling
document.addEventListener('DOMContentLoaded', function() {
    // Job Search Form
    const jobSearchForm = document.getElementById('job-search-form');
    if (jobSearchForm) {
        // Add event listeners for real-time search
        const keywordsInput = document.getElementById('keywords');
        const locationInput = document.getElementById('location');
        const jobTypeSelect = document.getElementById('job-type');
        let searchTimeout;
        
        // Function to handle real-time search
        function performRealTimeSearch() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const searchParams = {
                    keywords: keywordsInput.value,
                    location: locationInput.value,
                    'job-type': jobTypeSelect.value
                };
                
                // Only search if at least one field has content
                if (searchParams.keywords || searchParams.location) {
                    // Show loading state
                    document.getElementById('job-listings').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
                    
                    // Perform the search
                    window.location.href = '/jobs?' + new URLSearchParams(searchParams);
                }
            }, 600); // Delay for typing
        }
        
        // Setup real-time search on input
        keywordsInput.addEventListener('input', performRealTimeSearch);
        locationInput.addEventListener('input', performRealTimeSearch);
        jobTypeSelect.addEventListener('change', performRealTimeSearch);
        
        // Still handle the form submission directly
        jobSearchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const searchParams = {
                keywords: formData.get('keywords'),
                location: formData.get('location'),
                'job-type': formData.get('job-type')
            };

            // Show loading state
            document.getElementById('job-listings').innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';

            // Perform the search by redirecting to the URL with search parameters
            window.location.href = '/jobs?' + new URLSearchParams(searchParams);
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