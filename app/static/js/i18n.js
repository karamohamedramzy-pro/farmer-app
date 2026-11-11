const DICT = {
  ar: {
    app_name: "🌾 مزرعتي",
    lang_btn: "English",
    brand_name: "مزرعتي", tagline: "سجّل يومك. اعرف ربحك.",
    lbl_name: "الاسم الكامل", lbl_phone: "رقم واتساب", lbl_pass: "كلمة السر",
    start_day: "بداية اليوم", end_day: "نهاية اليوم",
    lbl_qty_in: "الكمية التي أحضرتها", lbl_money_out: "المبلغ الذي دفعته $",
    lbl_qty_sold: "الكمية التي بعتها", lbl_money_in: "المبلغ الذي قبضته $",
    last_entry: "آخر إدخال", total_profit: "إجمالي الربح", no_entries: "لا توجد سجلات لهذا المنتج بعد. سجّل بداية يومك من النموذج أعلاه.",
    status_on: "مفعّل", status_off: "غير مفعّل",
    // عام
    nav_home: "الرئيسية", nav_products: "منتجاتي", nav_sources: "مصادري",
    logout: "تسجيل خروج", welcome: "أهلاً وسهلاً", save: "حفظ", cancel: "إلغاء", edit: "تعديل", close: "إغلاق",
    // دخول / تسجيل
    email: "البريد الإلكتروني", ph_email: "البريد الإلكتروني", ph_name: "الاسم الكامل",
    ph_phone: "رقم واتساب مع رمز الدولة، مثال: +9665xxxxxxxx", ph_pass: "كلمة السر (6 أحرف على الأقل)",
    login_hint: "اكتب بريدك الإلكتروني وسنرسل لك رابط الدخول.",
    login_btn: "أرسل لي رابط الدخول", create_account: "إنشاء حساب جديد",
    reg_title: "إنشاء حساب", reg_btn: "إنشاء الحساب", back_login: "لدي حساب — تسجيل الدخول",
    phone_hint: "يجب أن يكون رقم واتساب: سيصلك عليه كود التأكيد عند كل دخول.",
    ce_title: "تحقق من بريدك", ce_text: "أرسلنا رابط الدخول إلى:", ce_note: "الرابط صالح 15 دقيقة. افتحه من أي جهاز.", ce_back: "رجوع",
    vp_title: "كود واتساب", vp_text: "أرسلنا كوداً من 6 أرقام إلى رقم واتساب:", vp_code: "الكود",
    vp_btn: "تأكيد ودخول", vp_resend: "إعادة إرسال الكود",
    dev_note: "⚠️ وضع تجريبي: لم يُرسل شيء فعلياً. هذا للتجربة فقط:", dev_link: "رابط الدخول", dev_code: "الكود",
    // دليل الاستعمال
    guide_title: "📖 كيف تستعمل الموقع؟",
    g1: "<b>أول مرة:</b> اضغط «إنشاء حساب جديد» واكتب اسمك وبريدك ورقم واتساب وكلمة سر.",
    g2: "<b>للدخول:</b> اكتب بريدك فيصلك رابط، افتحه ثم اكتب الكود الذي يصلك على واتساب.",
    g3: "من «منتجاتي» اختر المنتج (بطاطا، تفاح...).",
    g4: "<b>في بداية اليوم:</b> اكتب الكمية التي أحضرتها والمبلغ الذي دفعته. <b>في نهاية اليوم:</b> الكمية التي بعتها والمبلغ الذي قبضته.",
    g5: "سيحسب الجدول الفرق لك: <span class='plus'>+5 ربح (أخضر)</span> أو <span class='minus'>-5 خسارة (أحمر)</span>.",
    g6: "من «مصادري» احفظ بيانات من تشتري منهم (الاسم، الهاتف، الموقع، صور).",
    g_example: "مثال: أحضرت 30 كغ بطاطا ودفعت 1000$، وبعت 25 كغ بـ 1500$ ← الكمية المتبقية <span class='plus'>+5</span> والربح <span class='plus'>+500$</span>",
    // أخطاء
    err_no_account: "لا يوجد حساب بهذا البريد. أنشئ حساباً أولاً.",
    err_link_invalid: "الرابط غير صالح أو انتهت صلاحيته. اطلب رابطاً جديداً.",
    err_too_many: "محاولات كثيرة. حاول لاحقاً.",
    err_bad_code: "الكود غير صحيح.", err_code_expired: "انتهت صلاحية الكود. اضغط «إعادة إرسال الكود».",
    err_email_invalid: "البريد الإلكتروني غير صالح.", err_email_exists: "هذا البريد مسجّل مسبقاً. سجّل الدخول.",
    err_phone_invalid: "رقم الهاتف غير صالح (8–15 رقماً، ويمكن أن يبدأ بـ +).",
    err_name_required: "الاسم مطلوب.", err_pass_short: "كلمة السر قصيرة (6 أحرف على الأقل).",
    err_sub_code: "كود الاشتراك غير صحيح أو مستعمل.", err_url_invalid: "رابط غير صالح (يجب أن يبدأ بـ http:// أو https://).",
    err_url_required: "اكتب رابطاً واحداً على الأقل.", err_src_name: "اسم المصدر مطلوب.", err_too_long: "أحد الحقول أطول من المسموح.",
    // الرئيسية
    home_text: "ماذا تريد أن تفعل اليوم؟",
    card_products_t: "📦 منتجاتي", card_products_d: "سجّل مشترياتك ومبيعاتك واعرف ربحك.",
    card_sources_t: "🤝 مصادري", card_sources_d: "دليل الموردين والمزارع التي تتعامل معها.",
    // المنتجات
    choose_product: "اختر المنتج:", qty_start: "الكمية الأولى (بداية اليوم)", qty_sold: "الكمية المباعة (نهاية اليوم)",
    money_paid: "المبلغ المدفوع $", money_received: "المبلغ المقبوض $",
    date: "التاريخ", qty: "الكمية", sold: "المباعة", remaining: "المتبقي", paid: "المدفوع", received: "المقبوض", profit: "الربح",
    // المصادر
    add_source: "➕ إضافة مصدر", no_sources: "لا توجد مصادر بعد. أضف أول مصدر.",
    src_new: "مصدر جديد", src_edit: "تعديل المصدر", src_name: "الاسم (مطلوب)", src_field: "المجال",
    src_desc: "الوصف", src_phone: "رقم الهاتف", src_location: "الموقع (عنوان أو رابط خريطة)",
    src_images: "روابط الصور (من 1 إلى 4، اختيارية)", open_map: "فتح الخريطة", src_hint: "الاسم وحده إجباري، ويمكنك إكمال الباقي لاحقاً بزر «تعديل».",
    // الـ footer والروبوتات
    f_rights: "جميع الحقوق محفوظة", f_beta: "نسخة تجريبية",
    r1_label: "اشتراك", r2_label: "تخزين محلي", r3_label: "تخزين سحابي",
    contact_a: "تواصلوا مع المبرمج من خلال", telegram: "تلغرام", contact_b: "ويمكنكم زيارة صفحة", docs_name: "Document TB-farm",
    d_sub_title: "كود الاشتراك", d_sub_hint: "أدخل كود الاشتراك الذي أعطاك إياه المبرمج.", sub_code_ph: "مثال: FARM-XXXX-30",
    activate: "تفعيل", days_left: "الأيام المتبقية", day_unit: "يوم", sub_expired: "انتهى الاشتراك",
    usage_products: "مساحة المنتجات", usage_sources: "مساحة المصادر", disconnect: "فصل",
    d_local_title: "تخزين محلي على جهازك", d_local_hint: "للذين يخزنون بياناتهم على جهازهم: أدخل رابطي مكان التحميل.",
    local_products_url: "رابط تحميل بيانات المنتجات", local_sources_url: "رابط تحميل بيانات المصادر",
    d_cloud_title: "تخزين سحابي خاص بك", d_cloud_hint: "أدخل رابطي API الخاصين بك لتخزين البيانات.",
    cloud_sql: "رابط API لقاعدة SQL", cloud_nosql: "رابط API لقاعدة NoSQL", save_conn: "حفظ وتفعيل", connected: "متصل ✅"
  },
  en: {
    app_name: "🌾 My Farm",
    lang_btn: "العربية",
    brand_name: "My Farm", tagline: "Log your day. Know your profit.",
    lbl_name: "Full name", lbl_phone: "WhatsApp number", lbl_pass: "Password",
    start_day: "Start of day", end_day: "End of day",
    lbl_qty_in: "Quantity you brought", lbl_money_out: "Money you paid $",
    lbl_qty_sold: "Quantity you sold", lbl_money_in: "Money you received $",
    last_entry: "Latest entry", total_profit: "Total profit", no_entries: "No records for this product yet. Log your start of day in the form above.",
    status_on: "Active", status_off: "Inactive",
    nav_home: "Home", nav_products: "My Products", nav_sources: "My Sources",
    logout: "Log out", welcome: "Welcome", save: "Save", cancel: "Cancel", edit: "Edit", close: "Close",
    email: "Email", ph_email: "Email address", ph_name: "Full name",
    ph_phone: "WhatsApp number with country code, e.g. +9665xxxxxxxx", ph_pass: "Password (at least 6 characters)",
    login_hint: "Enter your email and we will send you a login link.",
    login_btn: "Send me a login link", create_account: "Create a new account",
    reg_title: "Create account", reg_btn: "Create account", back_login: "I have an account — log in",
    phone_hint: "Must be a WhatsApp number: your confirmation code is sent there at every login.",
    ce_title: "Check your email", ce_text: "We sent the login link to:", ce_note: "The link is valid for 15 minutes. Open it from any device.", ce_back: "Back",
    vp_title: "WhatsApp code", vp_text: "We sent a 6-digit code to the WhatsApp number:", vp_code: "Code",
    vp_btn: "Confirm and log in", vp_resend: "Resend code",
    dev_note: "⚠️ Test mode: nothing was actually sent. For testing only:", dev_link: "Login link", dev_code: "Code",
    guide_title: "📖 How to use this site",
    g1: "<b>First time:</b> press “Create a new account” and enter your name, email, WhatsApp number and a password.",
    g2: "<b>To log in:</b> enter your email, open the link we send, then type the code you receive on WhatsApp.",
    g3: "From “My Products” choose a product (potato, apple...).",
    g4: "<b>Start of day:</b> enter the quantity you brought and the money you paid. <b>End of day:</b> the quantity you sold and the money you received.",
    g5: "The table calculates the difference: <span class='plus'>+5 profit (green)</span> or <span class='minus'>-5 loss (red)</span>.",
    g6: "From “My Sources” save the details of your suppliers (name, phone, location, photos).",
    g_example: "Example: you brought 30 kg of potatoes and paid $1000, then sold 25 kg for $1500 → remaining <span class='plus'>+5</span>, profit <span class='plus'>+$500</span>",
    err_no_account: "No account with this email. Please create one first.",
    err_link_invalid: "The link is invalid or has expired. Request a new one.",
    err_too_many: "Too many attempts. Try again later.",
    err_bad_code: "Wrong code.", err_code_expired: "The code has expired. Press “Resend code”.",
    err_email_invalid: "Invalid email address.", err_email_exists: "This email is already registered. Please log in.",
    err_phone_invalid: "Invalid phone number (8–15 digits, may start with +).",
    err_name_required: "Name is required.", err_pass_short: "Password too short (at least 6 characters).",
    err_sub_code: "Wrong or already used subscription code.", err_url_invalid: "Invalid URL (must start with http:// or https://).",
    err_url_required: "Enter at least one URL.", err_src_name: "Source name is required.", err_too_long: "One of the fields is too long.",
    home_text: "What would you like to do today?",
    card_products_t: "📦 My Products", card_products_d: "Record your purchases and sales and see your profit.",
    card_sources_t: "🤝 My Sources", card_sources_d: "A directory of the suppliers and farms you deal with.",
    choose_product: "Choose a product:", qty_start: "Starting quantity (start of day)", qty_sold: "Quantity sold (end of day)",
    money_paid: "Money paid $", money_received: "Money received $",
    date: "Date", qty: "Quantity", sold: "Sold", remaining: "Remaining", paid: "Paid", received: "Received", profit: "Profit",
    add_source: "➕ Add a source", no_sources: "No sources yet. Add your first one.",
    src_new: "New source", src_edit: "Edit source", src_name: "Name (required)", src_field: "Field",
    src_desc: "Description", src_phone: "Phone number", src_location: "Location (address or map link)",
    src_images: "Image URLs (1 to 4, optional)", open_map: "Open map", src_hint: "Only the name is required; complete the rest later with the “Edit” button.",
    f_rights: "All rights reserved", f_beta: "Beta",
    r1_label: "Subscription", r2_label: "Local storage", r3_label: "Cloud storage",
    contact_a: "Contact the developer via", telegram: "Telegram", contact_b: "and you can visit the page", docs_name: "Document TB-farm",
    d_sub_title: "Subscription code", d_sub_hint: "Enter the subscription code the developer gave you.", sub_code_ph: "e.g. FARM-XXXX-30",
    activate: "Activate", days_left: "Days left", day_unit: "days", sub_expired: "Subscription expired",
    usage_products: "Products storage", usage_sources: "Sources storage", disconnect: "Disconnect",
    d_local_title: "Local storage on your device", d_local_hint: "For those who keep their data on their own device: enter the two download-location URLs.",
    local_products_url: "Products data download URL", local_sources_url: "Sources data download URL",
    d_cloud_title: "Your own cloud storage", d_cloud_hint: "Enter your own API URLs used to store the data.",
    cloud_sql: "SQL database API URL", cloud_nosql: "NoSQL database API URL", save_conn: "Save and activate", connected: "Connected ✅"
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
