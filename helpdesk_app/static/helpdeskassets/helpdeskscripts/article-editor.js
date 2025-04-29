/**
 * TinyMCE initialization for helpdesk article editor
 * Provides WordPress-like editing experience with file upload support
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if content textarea exists (we're on the editor page)
    const contentField = document.querySelector('#id_content');
    if (!contentField) return;

    // Get CSRF token for file uploads
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Function to handle offline mode
    function isOffline() {
        return !navigator.onLine;
    }

    // Check for older browsers and adjust configuration accordingly
    const isIE = !!document.documentMode;
    const isOldBrowser = isIE || !window.fetch;

    // --- START CORRECTION ---
    // Define the base toolbar string
    let toolbarConfig = 'undo redo | styles | ' +
                        'bold italic underline | alignleft aligncenter ' +
                        'alignright alignjustify | bullist numlist outdent indent | ' +
                        'link image table | fullscreen preview';

    // Add the PDF upload button conditionally *before* initializing
    if (!isOldBrowser) {
        toolbarConfig += ' | pdfupload'; // Add it here
    }
    // --- END CORRECTION ---


    // Base TinyMCE Configuration
    const editorConfig = {
        selector: '#id_content',
        height: 500,
        menubar: true,
        branding: false,
        promotion: false,
        browser_spellcheck: true,
        contextmenu: false,
        entity_encoding: 'raw',
        // Prioritize essential plugins first, ones that work in all browsers
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'help', 'wordcount', 'autosave'
        ],
        // Use the determined toolbar configuration
        toolbar: toolbarConfig, // Use the variable here
        // Use the simplest skin for older browsers
        skin: isOldBrowser ? 'oxide' : 'oxide',
        // Add CSS class to body element
        body_class: 'article-content',
        // Disable some features on older browsers
        paste_data_images: !isOldBrowser,
        // Enable local autosave
        autosave_interval: '30s',
        autosave_prefix: 'helpdesk-article-' + (contentField.dataset.articleId || 'new'),
        // Setup draft recovery
        setup: function(editor) {
            // Add draft recovery notification
            editor.on('init', function() {
                // Check for unsaved drafts
                const draftContent = localStorage.getItem('helpdesk-article-draft-content');
                if (draftContent && draftContent !== contentField.value) {
                    // Show recovery prompt
                    if (confirm('A saved draft of this article was found. Would you like to restore it?')) {
                        editor.setContent(draftContent);
                    } else {
                        // Clear draft if user doesn't want to recover
                        localStorage.removeItem('helpdesk-article-draft-content');
                    }
                }

                // Set up manual save for older browsers or offline mode
                editor.on('change', function() {
                    // Save to localStorage as backup
                    localStorage.setItem('helpdesk-article-draft-content', editor.getContent());
                });

                // Clear localStorage on form submit
                const form = contentField.closest('form');
                if (form) {
                    form.addEventListener('submit', function() {
                        localStorage.removeItem('helpdesk-article-draft-content');
                    });
                }
            });

            // Add PDF upload button for modern browsers
            // This part is correct - you register the button in setup
            if (!isOldBrowser) {
                editor.ui.registry.addButton('pdfupload', {
                    icon: 'upload',
                    tooltip: 'Upload PDF',
                    onAction: function() {
                        // Create file input
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.accept = '.pdf';

                        input.onchange = function() {
                            if (!input.files || !input.files[0]) return;

                            const file = input.files[0];
                            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                                alert('PDF file is too large. Maximum size is 10MB.');
                                return;
                            }

                            // Show loading message
                            editor.setProgressState(true);

                            // Create form data
                            const formData = new FormData();
                            formData.append('file', file);
                            formData.append('csrfmiddlewaretoken', csrfToken);

                            // Send to server
                            fetch('/articles/upload-file/', {
                                method: 'POST',
                                body: formData,
                                credentials: 'same-origin'
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    // Insert link to PDF
                                    editor.insertContent('<p><a href="' + data.url + '" target="_blank">' + file.name + '</a></p>');
                                } else {
                                    alert('Upload failed: ' + data.error);
                                }
                                editor.setProgressState(false);
                            })
                            .catch(error => {
                                console.error('Upload error:', error);
                                alert('Upload failed. Please try again.');
                                editor.setProgressState(false);
                            });
                        };

                        input.click();
                    }
                });

                // --- REMOVE THE INCORRECT LINE ---
                // editor.settings.toolbar += ' | pdfupload'; // REMOVE THIS LINE
            }
        }
    };

    // If we're offline, simplify the editor further
    if (isOffline()) {
        editorConfig.plugins = 'lists link image'; // Overwrite plugins
        editorConfig.toolbar = 'undo redo | bold italic | bullist numlist | link'; // Overwrite toolbar
        // Display offline notice
        const editorContainer = contentField.parentNode;
        const offlineNotice = document.createElement('div');
        offlineNotice.className = 'alert alert-warning';
        offlineNotice.innerHTML = 'You are currently offline. The editor will work with limited functionality.';
        editorContainer.insertBefore(offlineNotice, contentField);
    }

    // Initialize TinyMCE with our configuration
    tinymce.init(editorConfig);

    // Listen for online/offline events
    window.addEventListener('online', function() {
        // Reload the editor when we come back online
        location.reload();
    });

    window.addEventListener('offline', function() {
        // Show offline notice when going offline
        alert('You are now offline. Your changes will be saved locally until you reconnect.');
    });
});