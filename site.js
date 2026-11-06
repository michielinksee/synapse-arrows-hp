/* synapsearrows.com — static port of the Codex prototype (2026-10-27): menu, request form, analytics events */
(function () {
  var en = document.documentElement.lang === 'en';
  var t = document.querySelector('.menu-toggle'), m = document.getElementById('mobile-menu');
  if (t && m) t.addEventListener('click', function () { var open = m.hidden; m.hidden = !open; t.setAttribute('aria-expanded', open ? 'true' : 'false'); t.setAttribute('aria-label', open ? (en ? 'Close menu' : 'メニューを閉じる') : (en ? 'Open menu' : 'メニューを開く')); });
  // どこから進んだかを数える（Vercel Web Analytics・Cookie なし）。名前・メール・自由文・URL は送らない
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-va]'); if (!a || !window.va) return;
    var d = {}; if (a.dataset.vaFrom) d.from = a.dataset.vaFrom; if (a.dataset.plan) d.plan = a.dataset.plan;
    window.va('event', { name: a.dataset.va, data: d });
  });
  var rf = document.getElementById('request-form');
  if (rf) {
    var count = document.getElementById('selection-count'), err = document.getElementById('request-error');
    function n() { return rf.querySelectorAll('input[name=service]:checked').length; }
    rf.addEventListener('change', function () { var k = n(); count.textContent = k ? (en ? k + ' selected' : k + '件のサービスを選択中') : ''; if (k) err.hidden = true; });
    rf.addEventListener('submit', function (e) { if (!n()) { e.preventDefault(); err.hidden = false; err.scrollIntoView({ block: 'center' }); } });
  }
})();
