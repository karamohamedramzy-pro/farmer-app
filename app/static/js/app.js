// نوافذ الروبوتات في الـ footer (عنصر <dialog>)
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-dialog]").forEach(btn => {
    btn.addEventListener("click", () => {
      const d = document.getElementById(btn.dataset.dialog);
      if (d && d.showModal) d.showModal();
    });
  });
  document.querySelectorAll("dialog").forEach(d => {
    d.addEventListener("click", e => { if (e.target === d) d.close(); });   // الضغط على الخلفية
    d.querySelectorAll("[data-close]").forEach(b => b.addEventListener("click", () => d.close()));
  });

  // إعادة فتح النافذة عند وجود خطأ من الخادم (?dlg=dlg-sub&msg=...) ثم تنظيف الرابط
  const params = new URLSearchParams(location.search);
  const id = params.get("dlg");
  if (id) {
    const d = document.getElementById(id);
    if (d && d.tagName === "DIALOG" && d.showModal) d.showModal();
    params.delete("dlg"); params.delete("msg");
    const qs = params.toString();
    history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
  }
});
