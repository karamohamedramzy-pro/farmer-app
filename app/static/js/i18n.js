const DICT = {
  ar: {
    app_name: "🌾 مزرعتي",
    username: "الاسم",
    password: "كلمة السر",
    login: "دخول",
    logout: "تسجيل خروج",
    wrong_password: "كلمة السر غير صحيحة",
    guide_title: "📖 كيف تستعمل الموقع؟",
    g1: "اكتب اسمك وكلمة سر. <b>أول مرة</b> سيُنشأ لك حساب تلقائياً.",
    g2: "اختر المنتج من القائمة (بطاطا، تفاح...).",
    g3: "<b>في بداية اليوم:</b> اكتب الكمية التي أحضرتها والمبلغ الذي دفعته.",
    g4: "<b>في نهاية اليوم:</b> اكتب الكمية التي بعتها والمبلغ الذي قبضته.",
    g5: "سيحسب الجدول الفرق لك: <span class='plus'>+5 ربح (أخضر)</span> أو <span class='minus'>-5 خسارة (أحمر)</span>.",
    g_example: "مثال: أحضرت 30 كغ بطاطا ودفعت 1000$، وبعت 25 كغ بـ 1500$ ← الكمية المتبقية <span class='plus'>+5</span> والربح <span class='plus'>+500$</span>",
    welcome: "أهلاً وسهلاً",
    choose_product: "اختر المنتج:",
    qty_start: "الكمية الأولى (بداية اليوم)",
    qty_sold: "الكمية المباعة (نهاية اليوم)",
    money_paid: "المبلغ المدفوع $",
    money_received: "المبلغ المقبوض $",
    save: "حفظ",
    date: "التاريخ",
    qty: "الكمية",
    sold: "المباعة",
    remaining: "المتبقي",
    paid: "المدفوع",
    received: "المقبوض",
    profit: "الربح",
    lang_btn: "English"
  },
  en: {
    app_name: "🌾 My Farm",
    username: "Name",
    password: "Password",
    login: "Login",
    logout: "Log out",
    wrong_password: "Wrong password",
    guide_title: "📖 How to use this site",
    g1: "Enter your name and a password. <b>First time</b>, an account is created for you automatically.",
    g2: "Choose a product from the list (potato, apple...).",
    g3: "<b>Start of day:</b> enter the quantity you brought and the money you paid.",
    g4: "<b>End of day:</b> enter the quantity you sold and the money you received.",
    g5: "The table calculates the difference: <span class='plus'>+5 profit (green)</span> or <span class='minus'>-5 loss (red)</span>.",
    g_example: "Example: you brought 30 kg of potatoes and paid $1000, then sold 25 kg for $1500 → remaining <span class='plus'>+5</span>, profit <span class='plus'>+$500</span>",
    welcome: "Welcome",
    choose_product: "Choose a product:",
    qty_start: "Starting quantity (start of day)",
    qty_sold: "Quantity sold (end of day)",
    money_paid: "Money paid $",
    money_received: "Money received $",
    save: "Save",
    date: "Date",
    qty: "Quantity",
    sold: "Sold",
    remaining: "Remaining",
    paid: "Paid",
    received: "Received",
    profit: "Profit",
    lang_btn: "العربية"
  }
};

function getLang() {
  try { return localStorage.getItem("lang") || "ar"; } catch (e) { return "ar"; }
}

function applyLang(lang) {
  const d = DICT[lang];
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const v = d[el.dataset.i18n];
    if (v) el.innerHTML = v;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    el.placeholder = d[el.dataset.i18nPlaceholder] || "";
  });
  // أسماء المنتجات القادمة من قاعدة البيانات
  document.querySelectorAll("[data-ar][data-en]").forEach(el => {
    el.textContent = lang === "ar" ? el.dataset.ar : el.dataset.en;
  });
  const btn = document.getElementById("langBtn");
  if (btn) btn.textContent = d.lang_btn;
  document.title = d.app_name.replace("🌾 ", "");
}

// ضبط الاتجاه مبكراً لتقليل الوميض
document.documentElement.dir = getLang() === "ar" ? "rtl" : "ltr";

document.addEventListener("DOMContentLoaded", () => {
  applyLang(getLang());
  const btn = document.getElementById("langBtn");
  if (btn) btn.addEventListener("click", () => {
    const next = getLang() === "ar" ? "en" : "ar";
    try { localStorage.setItem("lang", next); } catch (e) {}
    applyLang(next);
  });
});
