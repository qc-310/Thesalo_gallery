document.addEventListener('DOMContentLoaded', () => {
    initLightbox();
    initMenus();
    initAutoResizeTextarea();
    initUploadPreview();
    initAjaxUpload();
});

/* =========================================
   Upload Preview & AJAX Logic
   ========================================= */
function initUploadPreview() {
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('file-preview-container');
    const labelSpan = document.querySelector('.file-input-wrapper span');
    const cancelBtn = document.getElementById('cancel-btn');

    if (!fileInput) return;

    // Use DataTransfer to manage the file list (allows adding/removing)
    const dt = new DataTransfer();

    // Expose reset function for external use (e.g. after upload success)
    fileInput.resetUploader = () => {
        dt.items.clear();
        fileInput.value = '';
        renderPreviews();
        labelSpan.textContent = '📁 ファイルを選択...';
        previewContainer.style.display = 'none';
    };

    fileInput.addEventListener('change', function (e) {
        // If files were selected (not cancel pressed in dialog resulting in 0 files if that happens)
        if (this.files && this.files.length > 0) {
            // Check for duplicates if needed, or just append
            // For simplicity, we just append all new files
            Array.from(this.files).forEach(file => {
                // simple duplicate check by name+size
                const exists = Array.from(dt.files).some(f => f.name === file.name && f.size === file.size);
                if (!exists) {
                    dt.items.add(file);
                }
            });

            // Sync back to input
            this.files = dt.files;
        }

        // Always re-render
        renderPreviews();
    });

    function renderPreviews() {
        const files = Array.from(dt.files);

        // Clear previous previews
        previewContainer.innerHTML = '';

        if (files.length === 0) {
            previewContainer.style.display = 'none';
            labelSpan.textContent = '📁 ファイルを選択...';
            return;
        }

        labelSpan.textContent = `📁 ${files.length}個のファイル`;
        previewContainer.style.display = 'flex';
        previewContainer.style.flexWrap = 'wrap';
        previewContainer.style.justifyContent = 'center';
        previewContainer.style.gap = '16px';

        // Scrollable container
        previewContainer.style.maxHeight = '65vh';
        previewContainer.style.overflowY = 'auto';
        previewContainer.style.paddingRight = '8px';

        files.forEach((file, index) => {
            const fileURL = URL.createObjectURL(file);
            const wrapper = document.createElement('div');
            wrapper.style.position = 'relative';
            wrapper.style.display = 'flex';
            wrapper.style.flexDirection = 'column';
            wrapper.style.gap = '4px';
            wrapper.style.width = '160px'; // Fixed width for flex items

            // Delete Button
            const delBtn = document.createElement('button');
            delBtn.innerHTML = '×';
            delBtn.style.position = 'absolute';
            delBtn.style.top = '-8px';
            delBtn.style.right = '-8px';
            delBtn.style.width = '24px';
            delBtn.style.height = '24px';
            delBtn.style.borderRadius = '50%';
            delBtn.style.background = '#ef4444';
            delBtn.style.color = 'white';
            delBtn.style.border = '2px solid white';
            delBtn.style.cursor = 'pointer';
            delBtn.style.zIndex = '10';
            delBtn.style.display = 'flex';
            delBtn.style.alignItems = 'center';
            delBtn.style.justifyContent = 'center';
            delBtn.style.fontWeight = 'bold';
            delBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';

            delBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                // Remove from DataTransfer
                dt.items.remove(index);
                // Sync back
                fileInput.files = dt.files;
                // Re-render
                renderPreviews();
            };
            wrapper.appendChild(delBtn);

            let mediaEl;
            if (file.type.startsWith('image/')) {
                mediaEl = document.createElement('img');
            } else if (file.type.startsWith('video/')) {
                mediaEl = document.createElement('video');
            }

            if (mediaEl) {
                mediaEl.src = fileURL;
                mediaEl.style.width = '100%';
                mediaEl.style.aspectRatio = '16/9';
                mediaEl.style.objectFit = 'cover';
                mediaEl.style.borderRadius = '4px';
                wrapper.appendChild(mediaEl);
            }

            const name = document.createElement('div');
            name.textContent = file.name;
            name.style.fontSize = '10px';
            name.style.overflow = 'hidden';
            name.style.textOverflow = 'ellipsis';
            name.style.whiteSpace = 'nowrap';
            name.style.color = '#ccc';
            wrapper.appendChild(name);

            // Per-file comment input (Textarea)
            const commentInput = document.createElement('textarea');
            commentInput.name = 'comments';
            commentInput.placeholder = 'コメント...';
            commentInput.style.width = '100%';
            commentInput.style.marginTop = '4px';
            commentInput.style.fontSize = '13px';
            commentInput.style.padding = '8px';
            commentInput.style.border = '1px solid #ccc';
            commentInput.style.borderRadius = '4px';
            commentInput.style.resize = 'vertical';
            commentInput.style.minHeight = '60px';

            // Prevent clicks from bubbling
            commentInput.onclick = (e) => e.stopPropagation();

            wrapper.appendChild(commentInput);

            previewContainer.appendChild(wrapper);
        });
    }
}

function initAjaxUpload() {
    const form = document.getElementById('upload-form');
    const btn = document.getElementById('upload-btn');
    const notification = document.getElementById('upload-notification');
    // We need the cancel logic to reset preview
    const cancelBtn = document.getElementById('cancel-btn');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const originalBtnText = btn.textContent;

        btn.textContent = 'アップロード中...';
        btn.disabled = true;
        btn.style.opacity = '0.7';

        // Hide previous notification
        if (notification) {
            notification.style.display = 'none';
        }

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                // Success

                // Reset form first
                const fileInput = document.getElementById('file-input');
                if (fileInput && fileInput.resetUploader) {
                    fileInput.resetUploader();
                } else {
                    form.reset();
                }

                // Show Success Modal
                const successModal = document.getElementById('success-modal');
                if (successModal) {
                    successModal.classList.add('active');
                    successModal.style.opacity = '1';
                    successModal.style.visibility = 'visible';
                } else {
                    // Fallback if modal missing
                    alert('アップロードしました！');
                }

            } else {
                // Error
                if (notification) {
                    notification.textContent = 'アップロードに失敗しました: ' + (result.error || 'Unknown error');
                    notification.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                    notification.style.color = '#ef4444';
                    notification.style.border = '1px solid #ef4444';
                    notification.style.display = 'block';
                } else {
                    alert('アップロードに失敗しました。');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            if (notification) {
                notification.textContent = 'エラーが発生しました。';
                notification.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                notification.style.color = '#ef4444';
                notification.style.border = '1px solid #ef4444';
                notification.style.display = 'block';
            } else {
                alert('エラーが発生しました。');
            }
        } finally {
            btn.textContent = originalBtnText;
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    });

    // Global function for modal close
    window.closeSuccessModal = function () {
        const successModal = document.getElementById('success-modal');
        if (successModal) {
            successModal.classList.remove('active');
            successModal.style.opacity = '0';
            successModal.style.visibility = 'hidden';
        }
    };
}


/* =========================================
   Lightbox Logic
   ========================================= */
function initLightbox() {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxVideo = document.getElementById('lightbox-video');
    const closeBtn = lightbox.querySelector('.lightbox-close');
    const prevBtn = lightbox.querySelector('.lightbox-prev');
    const nextBtn = lightbox.querySelector('.lightbox-next');

    let currentIndex = -1;
    let mediaItems = [];

    // Collect all media items from the grid
    const triggers = document.querySelectorAll('.media-trigger');
    mediaItems = Array.from(triggers).map(trigger => ({
        type: trigger.dataset.type,
        src: trigger.dataset.src,
        id: trigger.closest('.grid-item').dataset.id,
        description: trigger.dataset.description,
        uploader: trigger.dataset.uploader,
        date: trigger.dataset.date
    }));

    // Open Lightbox
    window.openLightbox = (index) => {
        if (index < 0 || index >= mediaItems.length) return;
        currentIndex = index;
        updateLightboxContent();
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    };

    // Close Lightbox
    const closeLightbox = () => {
        lightbox.classList.remove('active');
        lightboxVideo.pause();
        lightboxVideo.src = ""; // Stop buffering
        document.body.style.overflow = '';
    };

    closeBtn.addEventListener('click', closeLightbox);

    // Close on background click
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (!lightbox.classList.contains('active')) return;
        if (e.key === 'Escape') closeLightbox();
        if (e.key === 'ArrowLeft') showPrev();
        if (e.key === 'ArrowRight') showNext();
    });

    // Navigation
    const showPrev = () => {
        currentIndex = (currentIndex - 1 + mediaItems.length) % mediaItems.length;
        updateLightboxContent();
    };

    const showNext = () => {
        currentIndex = (currentIndex + 1) % mediaItems.length;
        updateLightboxContent();
    };

    prevBtn.addEventListener('click', showPrev);
    nextBtn.addEventListener('click', showNext);

    // Update Content
    function updateLightboxContent() {
        const item = mediaItems[currentIndex];

        if (item.type === 'video') {
            lightboxImg.style.display = 'none';
            lightboxVideo.style.display = 'block';
            lightboxVideo.src = item.src;
            // lightboxVideo.play(); // Optional: Autoplay
        } else {
            lightboxVideo.style.display = 'none';
            lightboxVideo.pause();
            lightboxImg.style.display = 'block';
            lightboxImg.src = item.src;
        }

        // Update Info
        const descEl = document.getElementById('lightbox-desc');
        const metaEl = document.getElementById('lightbox-meta');

        if (descEl) descEl.textContent = item.description || '';
        if (metaEl) {
            let meta = '';
            if (item.uploader) meta += item.uploader;
            if (item.date) meta += (meta ? ' • ' : '') + item.date;
            metaEl.textContent = meta;
        }
    }

    // Swipe Support for Mobile
    let touchStartX = 0;
    let touchEndX = 0;

    lightbox.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    });

    lightbox.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });

    function handleSwipe() {
        if (touchEndX < touchStartX - 50) showNext();
        if (touchEndX > touchStartX + 50) showPrev();
    }
}

/* =========================================
   Menu Dropdown Logic
   ========================================= */
function initMenus() {
    document.addEventListener('click', (e) => {
        const toggle = e.target.closest('.menu-btn');

        // Close all open menus first
        const allMenus = document.querySelectorAll('.menu-dropdown');
        const allBtns = document.querySelectorAll('.menu-btn');

        if (!toggle) {
            // Clicked outside, close all
            allMenus.forEach(m => m.classList.remove('show'));
            allBtns.forEach(b => b.classList.remove('active'));
            return;
        }

        e.stopPropagation(); // Prevent immediate closing
        const currentMenu = toggle.nextElementSibling;
        const isCurrentOpen = currentMenu.classList.contains('show');

        // Close all
        allMenus.forEach(m => m.classList.remove('show'));
        allBtns.forEach(b => b.classList.remove('active'));

        // Toggle current
        if (!isCurrentOpen) {
            currentMenu.classList.add('show');
            toggle.classList.add('active');
        }
    });
}

/* =========================================
   Auto Resize Textarea
   ========================================= */
function initAutoResizeTextarea() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}

/* =========================================
   Global Modal Helpers
   ========================================= */
window.showMessageModal = function (title, text, onCloseCallback) {
    const modal = document.getElementById('message-modal');
    if (!modal) return;

    const titleEl = document.getElementById('message-modal-title');
    const textEl = document.getElementById('message-modal-text');

    if (titleEl) titleEl.textContent = title;
    if (textEl) textEl.textContent = text;

    modal.classList.add('active');
    modal.style.opacity = '1';
    modal.style.visibility = 'visible';

    // Cleanup previous event listeners to avoid stacking
    const btn = modal.querySelector('button');
    if (btn) {
        // Clone button to remove listeners
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.onclick = function () {
            closeMessageModal();
            if (onCloseCallback) onCloseCallback();
        };
    }
};

window.closeMessageModal = function () {
    const modal = document.getElementById('message-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.opacity = '0';
        modal.style.visibility = 'hidden';
    }
};

window.showErrorModal = function (text) {
    const modal = document.getElementById('error-modal');
    if (!modal) {
        alert(text);
        return;
    }

    const textEl = document.getElementById('error-modal-text');
    if (textEl) textEl.textContent = text;

    modal.classList.add('active');
    modal.style.opacity = '1';
    modal.style.visibility = 'visible';
};

window.closeErrorModal = function () {
    const modal = document.getElementById('error-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.opacity = '0';
        modal.style.visibility = 'hidden';
    }
};

window.currentConfirmCallback = null;

window.showConfirmModal = function (message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    if (!modal) {
        if (confirm(message)) {
            onConfirm();
        }
        return;
    }

    const msgEl = document.getElementById('confirm-message');
    if (msgEl) msgEl.textContent = message;

    window.currentConfirmCallback = onConfirm;

    modal.classList.add('active');
    modal.style.opacity = '1';
    modal.style.visibility = 'visible';

    // Setup OK button
    const okBtn = document.getElementById('confirm-ok-btn');
    if (okBtn) {
        // Remove old listeners
        const newOkBtn = okBtn.cloneNode(true);
        okBtn.parentNode.replaceChild(newOkBtn, okBtn);

        newOkBtn.onclick = function () {
            if (window.currentConfirmCallback) {
                window.currentConfirmCallback();
            }
            closeConfirmModal();
        };
    }
};

window.closeConfirmModal = function () {
    const modal = document.getElementById('confirm-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.opacity = '0';
        modal.style.visibility = 'hidden';
    }
};
