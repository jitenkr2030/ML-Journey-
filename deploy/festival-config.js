// =============================================
// ReconcileAI - Festival Auto-Theme Config v1.0
// =============================================
// HOW TO ADD A FESTIVAL:
// 1. Add entry below with dates
// 2. Add CSS theme in festival-themes.css
// 3. Done! Engine auto-detects and applies.
//
// DATE FORMAT: "MM-DD" (month-day)
// fixed = same date every year
// dates = { "year": "MM-DD" } for lunar festivals
// duration = days theme stays active
// priority = 1-10 (higher wins if 2 festivals match)

window.FESTIVALS = {

  // ===== JANUARY =====
  "makar-sankranti": {
    name: "Makar Sankranti",
    emoji: "\u{1FA81}",
    banner: "Happy Makar Sankranti, Pongal & Lohri! Fly high with joy!",
    colors: { primary: "#f97316", secondary: "#0ea5e9", accent: "#eab308" },
    particles: "float",
    fixed: "01-14",
    duration: 1,
    priority: 5
  },

  "republic-day": {
    name: "Republic Day",
    emoji: "\u{1F1EE}\u{1F1F3}",
    banner: "Happy Republic Day! Jai Hind!",
    colors: { primary: "#FF9933", secondary: "#f8f7f4", accent: "#138808" },
    particles: "confetti",
    fixed: "01-26",
    duration: 1,
    priority: 7
  },

  // ===== FEBRUARY =====
  "maha-shivaratri": {
    name: "Maha Shivaratri",
    emoji: "\u{1F549}\uFE0F",
    banner: "Maha Shivaratri! Har Har Mahadev!",
    colors: { primary: "#1e3a5f", secondary: "#60a5fa", accent: "#93c5fd" },
    particles: "star",
    dates: { "2025": "02-26", "2026": "02-15", "2027": "02-06" },
    duration: 1,
    priority: 6
  },

  // ===== MARCH =====
  "holi": {
    name: "Holi",
    emoji: "\u{1F3A8}",
    banner: "Happy Holi! Spread colors of joy!",
    colors: { primary: "#ec4899", secondary: "#eab308", accent: "#22c55e" },
    particles: "float",
    dates: { "2025": "03-14", "2026": "03-03", "2027": "03-22" },
    duration: 2,
    priority: 9
  },

  "eid-fitr": {
    name: "Eid al-Fitr",
    emoji: "\u{1F319}",
    banner: "Eid Mubarak! Peace, blessings & joy!",
    colors: { primary: "#059669", secondary: "#d4a017", accent: "#34d399" },
    particles: "star",
    dates: { "2025": "03-31", "2026": "03-20", "2027": "03-10" },
    duration: 3,
    priority: 8
  },

  // ===== APRIL =====
  "ram-navami": {
    name: "Ram Navami",
    emoji: "\u{1F64F}",
    banner: "Happy Ram Navami! Jai Shri Ram!",
    colors: { primary: "#f97316", secondary: "#d4a017", accent: "#fbbf24" },
    particles: "petal",
    dates: { "2025": "04-06", "2026": "03-26", "2027": "04-15" },
    duration: 1,
    priority: 6
  },

  "ambedkar-jayanti": {
    name: "Ambedkar Jayanti",
    emoji: "\u{1F4DC}",
    banner: "Happy Ambedkar Jayanti! Jai Bhim!",
    colors: { primary: "#1e40af", secondary: "#d4a017", accent: "#3b82f6" },
    particles: "star",
    fixed: "04-14",
    duration: 1,
    priority: 5
  },

  "good-friday": {
    name: "Good Friday",
    emoji: "\u271D\uFE0F",
    banner: "Good Friday. Reflection, peace & hope.",
    colors: { primary: "#581c87", secondary: "#a78bfa", accent: "#d4a017" },
    particles: "glow",
    dates: { "2025": "04-18", "2026": "04-03", "2027": "03-26" },
    duration: 1,
    priority: 5
  },

  // ===== MAY =====
  "buddha-purnima": {
    name: "Buddha Purnima",
    emoji: "\u{1FAB7}",
    banner: "Buddha Purnima! Peace & enlightenment!",
    colors: { primary: "#d97706", secondary: "#fbbf24", accent: "#d4a017" },
    particles: "petal",
    dates: { "2025": "05-12", "2026": "05-01", "2027": "04-30" },
    duration: 1,
    priority: 5
  },

  // ===== JUNE =====
  "eid-adha": {
    name: "Eid al-Adha",
    emoji: "\u{1F410}",
    banner: "Eid al-Adha Mubarak! Sacrifice & generosity!",
    colors: { primary: "#059669", secondary: "#d4a017", accent: "#34d399" },
    particles: "star",
    dates: { "2025": "06-07", "2026": "05-27", "2027": "05-17" },
    duration: 3,
    priority: 8
  },

  "rath-yatra": {
    name: "Rath Yatra",
    emoji: "\u{1F6D5}",
    banner: "Happy Rath Yatra! Jai Jagannath!",
    colors: { primary: "#eab308", secondary: "#dc2626", accent: "#f97316" },
    particles: "petal",
    dates: { "2025": "06-27", "2026": "06-29", "2027": "07-18" },
    duration: 1,
    priority: 5
  },

  // ===== JULY =====
  "guru-purnima": {
    name: "Guru Purnima",
    emoji: "\u{1F4FF}",
    banner: "Happy Guru Purnima! Gratitude to all teachers!",
    colors: { primary: "#1e40af", secondary: "#d4a017", accent: "#60a5fa" },
    particles: "star",
    dates: { "2025": "07-10", "2026": "07-29", "2027": "07-17" },
    duration: 1,
    priority: 5
  },

  // ===== AUGUST =====
  "raksha-bandhan": {
    name: "Raksha Bandhan",
    emoji: "\u{1F4AB}",
    banner: "Happy Raksha Bandhan! Celebrate the bond of love!",
    colors: { primary: "#dc2626", secondary: "#d4a017", accent: "#ec4899" },
    particles: "sparkle",
    dates: { "2025": "08-09", "2026": "08-28", "2027": "08-17" },
    duration: 1,
    priority: 7
  },

  "independence-day": {
    name: "Independence Day",
    emoji: "\u{1F1EE}\u{1F1F3}",
    banner: "Happy Independence Day! Jai Hind!",
    colors: { primary: "#FF9933", secondary: "#f8f7f4", accent: "#138808" },
    particles: "confetti",
    fixed: "08-15",
    duration: 1,
    priority: 8
  },

  "janmashtami": {
    name: "Janmashtami",
    emoji: "\u{1F99A}",
    banner: "Happy Janmashtami! Hare Krishna!",
    colors: { primary: "#3b82f6", secondary: "#eab308", accent: "#818cf8" },
    particles: "float",
    dates: { "2025": "08-16", "2026": "09-04", "2027": "08-25" },
    duration: 2,
    priority: 7
  },

  // ===== SEPTEMBER =====
  "ganesh-chaturthi": {
    name: "Ganesh Chaturthi",
    emoji: "\u{1F418}",
    banner: "Ganpati Bappa Morya!",
    colors: { primary: "#f97316", secondary: "#eab308", accent: "#dc2626" },
    particles: "petal",
    dates: { "2025": "08-27", "2026": "09-14", "2027": "09-03" },
    duration: 3,
    priority: 8
  },

  "onam": {
    name: "Onam",
    emoji: "\u{1F33A}",
    banner: "Happy Onam! Prosperity & happiness!",
    colors: { primary: "#d4a017", secondary: "#22c55e", accent: "#fbbf24" },
    particles: "petal",
    fixed: "09-05",
    duration: 1,
    priority: 6
  },

  "teachers-day": {
    name: "Teacher's Day",
    emoji: "\u{1F468}\u200D\u{1F3EB}",
    banner: "Happy Teacher's Day! Thank you for shaping minds!",
    colors: { primary: "#d4a017", secondary: "#1e3a5f", accent: "#fbbf24" },
    particles: "sparkle",
    fixed: "09-05",
    duration: 1,
    priority: 4
  },

  // ===== OCTOBER =====
  "navratri": {
    name: "Navratri",
    emoji: "\u{1F64F}",
    banner: "Happy Navratri! Nine nights of divine energy!",
    colors: { primary: "#dc2626", secondary: "#f97316", accent: "#7c3aed" },
    particles: "glow",
    dates: { "2025": "09-22", "2026": "10-11", "2027": "10-01" },
    duration: 9,
    priority: 7
  },

  "gandhi-jayanti": {
    name: "Gandhi Jayanti",
    emoji: "\u{1F54A}\uFE0F",
    banner: "Gandhi Jayanti! Truth & non-violence!",
    colors: { primary: "#FF9933", secondary: "#f8f7f4", accent: "#138808" },
    particles: "petal",
    fixed: "10-02",
    duration: 1,
    priority: 6
  },

  "durga-puja": {
    name: "Durga Puja",
    emoji: "\u{1F409}",
    banner: "Durga Puja! Maa Durga ki Jai!",
    colors: { primary: "#dc2626", secondary: "#d4a017", accent: "#f97316" },
    particles: "glow",
    dates: { "2025": "10-01", "2026": "10-20", "2027": "10-08" },
    duration: 5,
    priority: 8
  },

  "dussehra": {
    name: "Dussehra",
    emoji: "\u{1F3F9}",
    banner: "Happy Dussehra! Victory of good over evil!",
    colors: { primary: "#dc2626", secondary: "#d4a017", accent: "#f97316" },
    particles: "sparkle",
    dates: { "2025": "10-12", "2026": "10-20", "2027": "10-08" },
    duration: 1,
    priority: 9
  },

  "karva-chauth": {
    name: "Karva Chauth",
    emoji: "\u{1F319}",
    banner: "Karva Chauth! Love & togetherness!",
    colors: { primary: "#991b1b", secondary: "#d4a017", accent: "#f87171" },
    particles: "star",
    dates: { "2025": "10-20", "2026": "11-08", "2027": "10-28" },
    duration: 1,
    priority: 5
  },

  "diwali": {
    name: "Diwali",
    emoji: "\u{1FA94}",
    banner: "Happy Diwali! May light conquer darkness!",
    colors: { primary: "#d4a017", secondary: "#f97316", accent: "#fbbf24" },
    particles: "sparkle",
    dates: { "2025": "10-20", "2026": "11-08", "2027": "10-28" },
    duration: 5,
    priority: 10
  },

  "chhath-puja": {
    name: "Chhath Puja",
    emoji: "\u{1F33E}",
    banner: "Happy Chhath Puja! Jai Surya Dev!",
    colors: { primary: "#f97316", secondary: "#eab308", accent: "#fbbf24" },
    particles: "sparkle",
    dates: { "2025": "10-27", "2026": "11-15", "2027": "11-04" },
    duration: 2,
    priority: 6
  },

  // ===== NOVEMBER =====
  "guru-nanak-jayanti": {
    name: "Guru Nanak Jayanti",
    emoji: "\u{1F64F}",
    banner: "Happy Guru Nanak Jayanti! Waheguru!",
    colors: { primary: "#1e40af", secondary: "#d4a017", accent: "#60a5fa" },
    particles: "star",
    dates: { "2025": "11-05", "2026": "11-24", "2027": "11-14" },
    duration: 1,
    priority: 6
  },

  // ===== DECEMBER =====
  "christmas": {
    name: "Christmas",
    emoji: "\u{1F384}",
    banner: "Merry Christmas! Joy, peace & love!",
    colors: { primary: "#dc2626", secondary: "#22c55e", accent: "#d4a017" },
    particles: "snow",
    fixed: "12-25",
    duration: 3,
    priority: 9
  },

  "new-year": {
    name: "New Year",
    emoji: "\u{1F386}",
    banner: "Happy New Year! New beginnings & fresh hopes!",
    colors: { primary: "#d4a017", secondary: "#c0c0c0", accent: "#fbbf24" },
    particles: "confetti",
    fixed: "01-01",
    duration: 2,
    priority: 9
  }

};
