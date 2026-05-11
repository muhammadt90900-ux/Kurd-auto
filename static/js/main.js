// ========== TOGGLE FAVORITE ==========
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.fav-btn');
    if (!btn) return;
    e.preventDefault();
    const partId = btn.dataset.partId;
    const icon = btn.querySelector('i');
    btn.disabled = true;
    fetch('/favorite/toggle/' + partId, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content,
            'Accept': 'application/json',
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'added') {
            icon.classList.replace('far', 'fas');
            btn.classList.add('active');
        } else if (data.status === 'removed') {
            icon.classList.replace('fas', 'far');
            btn.classList.remove('active');
        }
        document.getElementById('fav-count').textContent = data.count || 0;
    })
    .finally(() => btn.disabled = false);
});

// ========== COMPARE (Add) ==========
document.querySelectorAll('.compare-check').forEach(cb => {
    cb.addEventListener('change', function() {
        const partId = this.value;
        const action = this.checked ? 'add' : 'remove';
        const url = `/compare/${action}/${partId}`;
        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
        })
        .then(r => r.json())
        .then(data => {
            document.getElementById('comp-count').textContent = data.count || 0;
            if (action === 'add' && data.status === 'limit') {
                alert('تەنها دەتوانیت 3 ئۆتۆمبێل بەراورد بکەیت!');
                this.checked = false;
            }
        });
    });
});

// ========== SCROLL TO TOP ==========
const scrollBtn = document.getElementById('scrollTopBtn');
window.addEventListener('scroll', () => {
    scrollBtn.style.display = window.pageYOffset > 300 ? 'block' : 'none';
});
scrollBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ========== UPDATE COUNTERS ON PAGE LOAD ==========
window.addEventListener('load', function() {
    fetch('/api/counters')
        .then(r => r.json())
        .then(d => {
            const favEl = document.getElementById('fav-count');
            const compEl = document.getElementById('comp-count');
            if (favEl) favEl.textContent = d.favorites || 0;
            if (compEl) compEl.textContent = d.compare || 0;
        });
});
