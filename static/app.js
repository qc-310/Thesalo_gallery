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
    const imagePreview = document.getElementById('image-preview');
    const videoPreview = document.getElementById('video-preview');
    const fileNameDisplay = document.getElementById('file-name');
    const labelSpan = document.querySelector('.file-input-wrapper span');

    if (!fileInput) return;

    fileInput.addEventListener('change', function () {
        const files = Array.from(this.files);

        // Clear previous previews
        previewContainer.innerHTML = '';
        previewContainer.style.display = 'none';

        if (files.length === 0) {
            labelSpan.textContent = '📁 ファイルを選択...';
            return;
        }

        labelSpan.textContent = `📁 ${files.length}個のファイル`;
        previewContainer.style.display = 'grid';
        previewContainer.style.gridTemplateColumns = 'repeat(auto-fill, minmax(100px, 1fr))';
        previewContainer.style.gap = '10px';

        files.forEach(file => {
            const fileURL = URL.createObjectURL(file);
            const wrapper = document.createElement('div');
            wrapper.style.position = 'relative';

            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = fileURL;
                img.style.width = '100%';
                img.style.height = '100px';
                img.style.objectFit = 'cover';
                img.style.borderRadius = '4px';
                wrapper.appendChild(img);
            } else if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = fileURL;
                video.style.width = '100%';
                video.style.height = '100px';
                video.style.objectFit = 'cover';
                video.style.borderRadius = '4px';
                wrapper.appendChild(video);
            }

            const name = document.createElement('div');
            name.textContent = file.name;
            name.style.fontSize = '10px';
            name.style.overflow = 'hidden';
            name.style.textOverflow = 'ellipsis';
            name.style.whiteSpace = 'nowrap';
            wrapper.appendChild(name);

            // Per-file comment input
            const commentInput = document.createElement('input');
            commentInput.type = 'text';
            commentInput.name = 'comments'; // Changed to plural/list
            commentInput.placeholder = 'コメント...';
            commentInput.style.width = '100%';
            commentInput.style.marginTop = '4px';
            commentInput.style.fontSize = '12px';
            commentInput.style.padding = '4px';
            commentInput.style.border = '1px solid #ccc';
            commentInput.style.borderRadius = '3px';

            // Prevent Enter key from submitting form abruptly, maybe just let it be
            commentInput.onclick = (e) => e.stopPropagation();

            wrapper.appendChild(commentInput);

            previewContainer.appendChild(wrapper);
        });
    });
}

function initAjaxUpload() {
    const form = document.getElementById('upload-form');
    const btn = document.getElementById('upload-btn');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const originalBtnText = btn.textContent;

        btn.textContent = 'アップロード中...';
        btn.disabled = true;
        btn.style.opacity = '0.7';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.redirected) {
                window.location.href = response.url;
            } else if (response.ok) {
                // Manually reload if no redirect logic in fetch (though Flask usually redirects)
                window.location.reload();
            } else {
                alert('アップロードに失敗しました。');
                btn.textContent = originalBtnText;
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('エラーが発生しました。');
            btn.textContent = originalBtnText;
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    });
}


/* =========================================
   Lightbox Logic
   ========================================= */
function initLightbox() {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxVideo = document.getElementById('lightbox-video');
    const closeBtn = document.querySelector('.lightbox-close');
    const prevBtn = document.querySelector('.lightbox-prev');
    const nextBtn = document.querySelector('.lightbox-next');

    let currentIndex = -1;
    let mediaItems = [];

    // Collect all media items from the grid
    const triggers = document.querySelectorAll('.media-trigger');
    mediaItems = Array.from(triggers).map(trigger => ({
        type: trigger.dataset.type,
        src: trigger.dataset.src,
        id: trigger.closest('.grid-item').dataset.id
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
