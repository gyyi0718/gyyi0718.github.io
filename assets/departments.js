"use strict";
(async () => {
  const select = document.getElementById('distribution-place');
  if (!select) return;
  const status = document.getElementById('distribution-status');
  const body = document.getElementById('distribution-rows');
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  try {
    const response = await fetch('/data/seoul-departments.json');
    if (!response.ok) throw new Error('HTTP '+response.status);
    const data = await response.json();
    const render = () => {
      const place = data.places.find(p => p.id === select.value);
      status.textContent = `${place.merchant} · ${place.address}: ${place.records}행, 부서명 ${place.department_labels}개 · 상위 5개 비중 ${place.top5_share}% · 6개월 이상 기록된 부서명 ${place.repeat_thresholds['6']}개`;
      body.innerHTML = place.departments.map(d => `<tr><th scope="row"><a href="${esc(d.explorer_url)}">${esc(d.department)}</a></th><td class="num">${d.records}</td><td class="num">${d.active_months}</td>${d.months.map(n=>`<td class="num ${n?'month-observed':''}">${n}</td>`).join('')}</tr>`).join('');
    };
    select.addEventListener('change',render);
    render();
  } catch(error) {
    select.disabled = true;
    status.textContent = '부서별 탐색 자료를 불러오지 못했습니다. 아래 정적 집계표와 CSV에서 같은 결과를 확인할 수 있습니다.';
  }
})();
