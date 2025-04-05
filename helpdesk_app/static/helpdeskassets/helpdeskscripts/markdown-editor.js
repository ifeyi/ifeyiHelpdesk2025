// Example for EasyMDE initialization
function initMarkdownEditor(selector) {
    const textareas = document.querySelectorAll(selector);
    
    textareas.forEach(textarea => {

      if (!textarea.classList.contains('easymde-initialized')) {
        const easyMDE = new EasyMDE({
          element: textarea,
          spellChecker: false,
          autosave: {
            enabled: true,
            uniqueId: 'article-editor-' + textarea.id,
            delay: 1000,
          },
          toolbar: [
            'bold', 'italic', 'heading', '|',
            'quote', 'unordered-list', 'ordered-list', '|',
            'link', 'image', 'table', '|',
            'preview', 'side-by-side', 'fullscreen'
          ]
        });

        const form = textarea.closest('form');
        if (form) {
          form.addEventListener('submit', function() {
            // This ensures the textarea has the content from the editor before submit
            easyMDE.codemirror.save();
          });
        }
        
        // Mark this textarea as initialized
        textarea.classList.add('easymde-initialized');
      }
    });
  }
  
  // Initialize when document is ready
  document.addEventListener('DOMContentLoaded', function() {
    if (typeof EasyMDE !== 'undefined') {
      initMarkdownEditor('.rich-text-editor');
    }
  });