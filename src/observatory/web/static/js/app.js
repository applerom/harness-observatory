/*
FILE: src/observatory/web/static/js/app.js
VERSION: 2026-04-26
START_MODULE_CONTRACT:
PURPOSE: Tiny browser helpers for HTMX-enhanced observatory UI.
PRD_REF: docs/PRD.md §11.2
WHY_REF: docs/why-graph.xml#MOD-WEB-APP
SCOPE: matrix scroll synchronization; matrix detail reveal after HTMX swaps
INVARIANTS:
- Helpers stay framework-free and do not own product state.
:END_MODULE_CONTRACT
*/

window.observatorySyncScroll = function observatorySyncScroll(sourceId, targetId) {
  const source = document.getElementById(sourceId);
  const target = document.getElementById(targetId);
  if (!source || !target || target.scrollLeft === source.scrollLeft) {
    return;
  }
  target.scrollLeft = source.scrollLeft;
};

window.observatoryScrollToMatrixDetail = function observatoryScrollToMatrixDetail() {
  const detail = document.getElementById("matrix-cell-detail");
  if (!detail) {
    return;
  }
  if (window.matchMedia("(min-width: 1101px)").matches) {
    return;
  }
  detail.scrollIntoView({ block: "start", behavior: "smooth" });
};

document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.detail && event.detail.target && event.detail.target.id === "matrix-cell-detail") {
    window.observatoryScrollToMatrixDetail();
  }
});
