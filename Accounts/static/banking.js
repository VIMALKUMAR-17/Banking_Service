/* VK Banking System - small UI helpers (mobile menu, dismissible alerts, focus on first error). */
(function () {
    'use strict';

    var toggle = document.querySelector('.nav-toggle');
    var nav = document.getElementById('site-nav');

    function setOpen(open) {
        if (!toggle || !nav) { return; }
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        nav.classList.toggle('is-open', open);
    }

    if (toggle && nav) {
        toggle.addEventListener('click', function () {
            setOpen(toggle.getAttribute('aria-expanded') !== 'true');
        });

        nav.addEventListener('click', function (e) {
            if (e.target.closest('a')) { setOpen(false); }
        });

        document.addEventListener('click', function (e) {
            if (!e.target.closest('.site-header')) { setOpen(false); }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
                setOpen(false);
                toggle.focus();
            }
        });

        window.addEventListener('resize', function () {
            if (window.innerWidth > 900) { setOpen(false); }
        });
    }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-dismiss="alert"]');
        if (btn && btn.parentElement) { btn.parentElement.remove(); }
    });

    var firstInvalid = document.querySelector('[aria-invalid="true"]');
    if (firstInvalid) { firstInvalid.focus(); }
})();
