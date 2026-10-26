/*
 * Cloudflare Turnstile for the free checkers (/ai-bae/, /site-checker/, /for/investors.html).
 * 2026-10-25 — founder-ops/research/AiBae_2026-10/DESIGN-ai-bae-abuse-guard-v1.md.
 *
 * The server decides: GET <api>/api/config returns turnstile_site_key (null while Turnstile is off).
 * Off → token() resolves null and the page posts exactly as before. On → an invisible widget is rendered
 * (appearance "interaction-only": nothing shows unless Cloudflare needs the visitor to click) and token()
 * returns a fresh single-use token for each scan. Plain ES5 so every page can load it.
 *
 *   KLTurnstile.init(apiBase, containerElement)  → Promise<boolean>  (true when Turnstile is on)
 *   KLTurnstile.token()                          → Promise<string|null>
 */
(function (w) {
  var SCRIPT = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=__klTurnstileLoaded';
  var TOKEN_WAIT_MS = 30000;
  var state = { ready: null, siteKey: null, widgetId: null, pending: null };

  function settle(v) {
    var p = state.pending;
    state.pending = null;
    if (p) { clearTimeout(p.timer); p.resolve(v); }
  }

  function loadScript() {
    return new Promise(function (resolve, reject) {
      if (w.turnstile) { resolve(); return; }
      w.__klTurnstileLoaded = function () { resolve(); };
      var s = document.createElement('script');
      s.src = SCRIPT; s.async = true; s.defer = true;
      s.onerror = function () { reject(new Error('turnstile script failed to load')); };
      document.head.appendChild(s);
    });
  }

  function init(apiBase, container) {
    if (state.ready) return state.ready;
    state.ready = fetch(apiBase + '/api/config', { mode: 'cors' })
      .then(function (r) { return r.ok ? r.json() : {}; })
      .then(function (cfg) {
        var key = cfg && typeof cfg.turnstile_site_key === 'string' ? cfg.turnstile_site_key : '';
        if (!key || !container) return false;
        state.siteKey = key;
        return loadScript().then(function () {
          state.widgetId = w.turnstile.render(container, {
            sitekey: key,
            execution: 'execute',
            appearance: 'interaction-only',
            callback: function (t) { settle(t); },
            'error-callback': function () { settle(''); return true; },
            'expired-callback': function () { /* a new token is fetched per scan */ }
          });
          return true;
        });
      })
      .catch(function () { return false; });
    return state.ready;
  }

  function token() {
    if (!state.ready) return Promise.resolve(null);
    return state.ready.then(function (on) {
      if (!on || state.widgetId === null) return null;
      settle(''); // drop any earlier wait
      return new Promise(function (resolve) {
        state.pending = { resolve: resolve, timer: setTimeout(function () { settle(''); }, TOKEN_WAIT_MS) };
        try {
          w.turnstile.reset(state.widgetId);
          w.turnstile.execute(state.widgetId);
        } catch (e) { settle(''); }
      });
    });
  }

  w.KLTurnstile = { init: init, token: token };
})(window);
