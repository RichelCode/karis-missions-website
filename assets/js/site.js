/* ==========================================================================
   Karis Missions International — site behaviour
   ==========================================================================

   FORM SET-UP (one step, ~2 minutes)
   ----------------------------------
   1. Create a free account at https://formspree.io and add a new form.
   2. Formspree gives you an endpoint like https://formspree.io/f/abcdwxyz
   3. Paste the ID (the part after /f/) into FORM_ENDPOINT below.

   Until that is done, every form on the site stays fully usable: instead of
   silently discarding the message, it tells the visitor to email us directly
   and offers a pre-filled mail link. Nothing pretends to have been sent.
   ========================================================================== */

(function () {
  'use strict';

  var FORM_ENDPOINT = '';                      // e.g. 'https://formspree.io/f/abcdwxyz'
  var FALLBACK_EMAIL = 'tackiausa@gmail.com';

  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------ navigation */

  var header = document.getElementById('siteHeader');
  var menuBtn = document.querySelector('.menu-btn');
  var nav = document.getElementById('primaryNav');
  var scrim = document.querySelector('.nav-scrim');

  function isMobileNav() {
    return window.matchMedia('(max-width: 980px)').matches;
  }

  function setDrawer(open) {
    if (!nav || !menuBtn) return;
    nav.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
    if (scrim) scrim.hidden = !open;
    // Stop the page behind the drawer from scrolling.
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) {
      var first = nav.querySelector('a, button');
      if (first) first.focus();
    }
  }

  if (menuBtn && nav) {
    menuBtn.addEventListener('click', function () {
      setDrawer(menuBtn.getAttribute('aria-expanded') !== 'true');
    });
  }
  if (scrim) scrim.addEventListener('click', function () { setDrawer(false); });

  // Close the drawer once a destination is chosen. The chevron is a <button>,
  // so opening a submenu on mobile never closes the drawer.
  if (nav) {
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a') && isMobileNav()) setDrawer(false);
    });
  }

  /* Dropdown menus — click to open, hover on pointer devices, Escape to close. */
  var toggles = Array.prototype.slice.call(document.querySelectorAll('.nav-toggle'));

  function closeMenus(except) {
    toggles.forEach(function (t) {
      if (t === except) return;
      t.setAttribute('aria-expanded', 'false');
      var menu = document.getElementById(t.getAttribute('aria-controls'));
      if (menu) menu.classList.remove('open');
    });
  }

  toggles.forEach(function (toggle) {
    var menu = document.getElementById(toggle.getAttribute('aria-controls'));
    if (!menu) return;
    var parent = toggle.parentElement;

    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      closeMenus(toggle);
      toggle.setAttribute('aria-expanded', String(!open));
      menu.classList.toggle('open', !open);
    });

    // Hover only makes sense on the desktop layout with a real pointer.
    parent.addEventListener('mouseenter', function () {
      if (isMobileNav() || !window.matchMedia('(hover: hover)').matches) return;
      closeMenus(toggle);
      toggle.setAttribute('aria-expanded', 'true');
      menu.classList.add('open');
    });
    parent.addEventListener('mouseleave', function () {
      if (isMobileNav() || !window.matchMedia('(hover: hover)').matches) return;
      toggle.setAttribute('aria-expanded', 'false');
      menu.classList.remove('open');
    });

    // Tabbing out of the group closes it.
    parent.addEventListener('focusout', function (e) {
      if (isMobileNav()) return;
      if (!parent.contains(e.relatedTarget)) {
        toggle.setAttribute('aria-expanded', 'false');
        menu.classList.remove('open');
      }
    });
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-menu')) closeMenus(null);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    closeMenus(null);
    if (nav && nav.classList.contains('open')) {
      setDrawer(false);
      if (menuBtn) menuBtn.focus();
    }
  });

  // Reset the drawer if the viewport grows past the mobile breakpoint.
  window.addEventListener('resize', function () {
    if (!isMobileNav() && nav && nav.classList.contains('open')) setDrawer(false);
  });

  /* ------------------------------------------------------- scroll affordances */

  var toTop = document.querySelector('.to-top');

  function onScroll() {
    var y = window.scrollY;
    if (header) header.classList.toggle('is-stuck', y > 8);
    if (toTop) toTop.hidden = y < 600;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (toTop) {
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
    });
  }

  /* ------------------------------------------------------------ form handling */

  function fieldWrapper(el) {
    return el.closest('.field');
  }

  function showFieldError(el, message) {
    var wrap = fieldWrapper(el);
    if (!wrap) return;
    wrap.classList.add('invalid');
    var msg = wrap.querySelector('.field-error');
    if (msg) msg.textContent = message;
    el.setAttribute('aria-invalid', 'true');
  }

  function clearFieldError(el) {
    var wrap = fieldWrapper(el);
    if (!wrap) return;
    wrap.classList.remove('invalid');
    el.removeAttribute('aria-invalid');
  }

  function validate(form) {
    var firstBad = null;
    var controls = form.querySelectorAll('input, select, textarea');

    Array.prototype.forEach.call(controls, function (el) {
      if (el.type === 'hidden' || el.closest('.hp')) return;
      clearFieldError(el);
      if (!el.checkValidity()) {
        var message = el.validity.valueMissing
          ? (el.type === 'checkbox' ? 'Please confirm this to continue.' : 'This field is required.')
          : el.validationMessage;
        showFieldError(el, message);
        if (!firstBad) firstBad = el;
      }
    });

    if (firstBad) {
      firstBad.focus();
      firstBad.scrollIntoView({ block: 'center', behavior: prefersReducedMotion ? 'auto' : 'smooth' });
    }
    return !firstBad;
  }

  function setStatus(box, type, html) {
    if (!box) return;
    box.className = 'form-status is-visible ' + type;
    box.innerHTML = html;
  }

  function mailtoFallback(form) {
    var subject = form.dataset.subject || 'Website enquiry';
    var lines = [];
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || el.closest('.hp') || el.type === 'submit' || el.type === 'hidden') return;
      if ((el.type === 'checkbox' || el.type === 'radio') && !el.checked) return;
      var label = form.querySelector('label[for="' + el.id + '"]');
      var name = label ? label.textContent.replace('*', '').trim() : el.name;
      lines.push(name + ': ' + el.value);
    });
    return 'mailto:' + FALLBACK_EMAIL +
      '?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(lines.join('\n'));
  }

  Array.prototype.forEach.call(document.querySelectorAll('form[data-form]'), function (form) {
    var status = form.querySelector('.form-status');
    var submit = form.querySelector('[type="submit"]');

    // Clear an error as soon as the visitor starts fixing it.
    form.addEventListener('input', function (e) {
      if (e.target.closest('.field.invalid')) clearFieldError(e.target);
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!validate(form)) return;

      // Honeypot: a real person never fills this in.
      var trap = form.querySelector('.hp input');
      if (trap && trap.value) return;

      if (!FORM_ENDPOINT) {
        setStatus(status, 'err',
          'This form is not connected yet. Please email us directly at ' +
          '<a href="mailto:' + FALLBACK_EMAIL + '">' + FALLBACK_EMAIL + '</a> — ' +
          '<a href="' + mailtoFallback(form) + '">open a pre-filled email</a>.');
        return;
      }

      var original = submit ? submit.textContent : '';
      if (submit) { submit.disabled = true; submit.textContent = 'Sending…'; }
      setStatus(status, 'ok', 'Sending your message…');

      fetch(FORM_ENDPOINT, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' }
      })
        .then(function (res) {
          if (!res.ok) throw new Error('Request failed');
          setStatus(status, 'ok', form.dataset.success ||
            'Thank you. We have received your message and will be in touch soon.');
          form.reset();
        })
        .catch(function () {
          setStatus(status, 'err',
            'Sorry — we could not send that. Please try again, or email us at ' +
            '<a href="mailto:' + FALLBACK_EMAIL + '">' + FALLBACK_EMAIL + '</a>.');
        })
        .finally(function () {
          if (submit) { submit.disabled = false; submit.textContent = original; }
        });
    });
  });

  /* --------------------------------------------------------- resource search */

  var dlSearch = document.getElementById('dlSearch');
  if (dlSearch) {
    var cards = Array.prototype.slice.call(document.querySelectorAll('.dl-card'));
    var groups = Array.prototype.slice.call(document.querySelectorAll('.dl-group'));
    var counter = document.getElementById('dlCount');
    var empty = document.getElementById('dlEmpty');

    var runSearch = function () {
      var q = dlSearch.value.trim().toLowerCase();
      var shown = 0;

      cards.forEach(function (card) {
        var match = !q || (card.dataset.search || '').indexOf(q) !== -1;
        card.hidden = !match;
        if (match) shown++;
      });

      // Hide a whole section when nothing in it matched.
      groups.forEach(function (group) {
        var visible = group.querySelectorAll('.dl-card:not([hidden])').length;
        group.hidden = visible === 0;
      });

      if (counter) {
        counter.textContent = q
          ? shown + (shown === 1 ? ' resource matches' : ' resources match')
          : cards.length + ' resources available';
      }
      if (empty) empty.hidden = shown !== 0;
    };

    dlSearch.addEventListener('input', runSearch);
    runSearch();
  }

  /* ------------------------------------------------------------ video player */

  /*
   * Videos are shown as a still image with a play button. Only when someone
   * presses play do we insert the YouTube player, and we use the nocookie
   * host so no tracking cookie is set for visitors who never watch anything.
   */
  Array.prototype.forEach.call(document.querySelectorAll('.video-play'), function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.dataset.video;
      if (!id) return;

      var frame = document.createElement('iframe');
      frame.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) +
                  '?autoplay=1&rel=0&modestbranding=1';
      frame.title = btn.dataset.title || 'Video player';
      frame.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; ' +
                    'gyroscope; picture-in-picture; web-share';
      frame.allowFullscreen = true;
      frame.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');

      var holder = btn.parentNode;
      holder.replaceChild(frame, btn);
      frame.focus();
    });
  });

  /* --------------------------------------------------------- content filters */

  var filterBtns = Array.prototype.slice.call(document.querySelectorAll('.filter-btn'));
  if (filterBtns.length) {
    filterBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        filterBtns.forEach(function (b) {
          b.classList.remove('active');
          b.setAttribute('aria-pressed', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-pressed', 'true');

        var tag = btn.dataset.filter;
        Array.prototype.forEach.call(document.querySelectorAll('[data-tags]'), function (card) {
          card.hidden = !(tag === 'all' || (card.dataset.tags || '').split(' ').indexOf(tag) !== -1);
        });
      });
    });
  }
})();
