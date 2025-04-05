// Articles functionality

document.addEventListener('DOMContentLoaded', function() {
    // Feedback form handling
    const feedbackForm = document.querySelector('.article-feedback-form form');
    
    if (feedbackForm) {
      const helpfulInputs = feedbackForm.querySelectorAll('input[name="helpful"]');
      const commentTextarea = feedbackForm.querySelector('textarea[name="comment"]');
      
      helpfulInputs.forEach(input => {
        input.addEventListener('change', function() {
          // Show comment textarea when user selects "Not helpful"
          if (input.value === 'False') {
            commentTextarea.closest('.form-group').style.display = 'block';
            commentTextarea.focus();
          } else {
            // Optional: hide comment textarea for "Helpful" selection
            // commentTextarea.closest('.form-group').style.display = 'none';
          }
        });
      });
    }
  
    // Handle article search in mobile view
    const searchToggle = document.getElementById('kb-search-toggle');
    const searchBox = document.querySelector('.search-box');
    
    if (searchToggle && searchBox) {
      searchToggle.addEventListener('click', function(e) {
        e.preventDefault();
        searchBox.classList.toggle('d-block');
        searchBox.querySelector('input').focus();
      });
    }
    
    // Highlight code blocks if syntax highlighting library is available
    if (typeof hljs !== 'undefined') {
      document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightBlock(block);
      });
    }
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
      const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
      tooltips.forEach(element => {
        new bootstrap.Tooltip(element);
      });
    }
    
    // Handle category collapsing in sidebar
    const categoryToggles = document.querySelectorAll('.category-toggle');
    categoryToggles.forEach(toggle => {
      toggle.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('data-target');
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
          targetElement.classList.toggle('show');
          this.querySelector('i').classList.toggle('fa-chevron-down');
          this.querySelector('i').classList.toggle('fa-chevron-right');
        }
      });
    });
});