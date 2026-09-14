/* 세금맛집 — GA4 상호작용 추적.
   index.html 은 지도/게시글 전환이 URL을 바꾸지 않아 페이지뷰만으로는 안에서 뭘 봤는지 알 수 없다.
   기존 코드에 손대지 않도록 document 레벨 위임 리스너만 쓴다. gtag 이 없으면 전부 무동작. */
(function () {
  function send(name, params) {
    try { if (typeof window.gtag === 'function') window.gtag('event', name, params || {}); } catch (e) {}
  }
  function txt(el) { return (el.textContent || '').trim().split('\n')[0].slice(0, 60); }

  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (!t || !t.closest) return;
    try {
      if (t.closest('#vmap')) { send('view_mode', { mode: '지도' }); return; }
      if (t.closest('#vart')) { send('view_mode', { mode: '게시글' }); return; }

      var y = t.closest('#years button');
      if (y) { send('select_year', { year: txt(y) }); return; }

      var r = t.closest('.rg') || t.closest('.gcell');
      if (r) { send('select_region', { region: txt(r) }); return; }

      var a = t.closest('a[href]');
      if (a && /^https?:/i.test(a.getAttribute('href') || '') && a.hostname !== location.hostname) {
        send('outbound_click', {
          link_domain: a.hostname,
          link_url: (a.href || '').slice(0, 100),
          link_text: txt(a)
        });
      }
    } catch (e) {}
  }, true);

  var box = document.getElementById('hq'), timer;
  if (box) {
    box.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        var v = (box.value || '').trim();
        if (v.length >= 2) send('search', { search_term: v.slice(0, 40) });
      }, 1200);
    });
  }
})();
