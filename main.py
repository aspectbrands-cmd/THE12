
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import time

APP_NAME = "THE12 Mod Translator"
APP_SUBTITLE = "Интеллектуальный перевод модов Skyrim / Fallout"
APP_VERSION = "v1.2 Beta"

# ---------------- Splash with 'breathing' logo ----------------
class Splash(tk.Toplevel):
    def __init__(self, master, duration_ms=2800):
        super().__init__(master)
        self.overrideredirect(True)
        self.config(bg="#0E0E0E")
        self.geometry(self._center(520, 280))
        self.canvas = tk.Canvas(self, bg="#0E0E0E", highlightthickness=0, width=520, height=280)
        self.canvas.pack(fill="both", expand=True)
        # "SVG" logo imitation with vector text (portable, no extra libs)
        self.logo = self.canvas.create_text(260, 120, text="THE12", fill="#FFFFFF", font=("Segoe UI", 44, "bold"))
        self.sub = self.canvas.create_text(260, 165, text="Основано на интеллекте", fill="#E1E1E1", font=("Segoe UI", 12))
        self._start = time.time()
        self._dur = duration_ms/1000.0
        self._animate()
        self.after(duration_ms, self.destroy)

    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        return f"{w}x{h}+{x}+{y}"

    def _animate(self):
        t = time.time() - self._start
        import math
        scale = 1.0 + 0.03 * math.sin(2*math.pi * t / 1.6)  # breathing
        self.canvas.scale("all", 260, 140, scale, scale)
        # subtle shimmer
        if int(t*6) % 2 == 0:
            self.canvas.itemconfig(self.logo, fill="#FFFFFF")
        else:
            self.canvas.itemconfig(self.logo, fill="#F5F5F5")
        if self.winfo_exists():
            self.after(120, self._animate)

# --------------- Translation helpers (placeholders safe) ---------------
PLACEHOLDER_RE = re.compile(
    r"(<[^>]+>|%s|%\d+\$s|{\d+}|&\w+;|\\n|\\r|\\t|\[pagebreak\]|"
    r"<p[^>]*>|</p>|<b>|</b>|<i>|</i>|<font[^>]*>|</font>)"
)
WORD_MAP = {
    "find":"найди","search":"поищи","listen":"послушай","talk":"поговори",
    "bring":"принеси","return":"верни","give":"дай","fetch":"забери","take":"возьми",
    "book":"книгу","key":"ключ","keys":"ключи","oil":"масло","gyro":"гироскоп",
    "dynamo":"динамо","dyno":"динамо",
    "arcanaeum":"арканеум","alftand":"алфтанд","mzinchaleft":"мзинчалефт",
    "winterhold":"винтерхолд","markarth":"маркарт","morthal":"морфал","skyrim":"скайрим",
    "please":"пожалуйста","now":"сейчас","sorry":"простите","thank":"спасибо",
    "yes":"да","no":"нет","good":"хорошо","well":"ну","what":"что","why":"почему",
    "how":"как","you":"вы","me":"меня","my":"мой","your":"ваш",
}
def has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", s or ""))

def feminine_templates(text: str) -> str | None:
    s = text.strip()
    low = s.lower()
    rules = [
        ("i found ", "Я нашла "), ("i have found ", "Я нашла "),
        ("i got ", "Я достала "), ("i have ", "У меня "),
        ("i am ", "Я "), ("i'm ", "Я "), ("i ", "Я "),
    ]
    for en, ru in rules:
        if low.startswith(en):
            return ru + s[len(en):]
    return None

def is_visible_string(src: str, rec: str, edid: str) -> bool:
    if not src: return False
    if any(ext in src for ext in (".esm",".esl",".bsa")): return False
    rec_type = (rec or "").split(":")[0]
    if rec_type in {"GMST","KYWD","WRLD","CELL","NAVM"}: return False
    if re.fullmatch(r"[A-Za-z0-9_:. -]+", src) and len(src.strip()) <= 3: return False
    return True

def translate_piecewise(text: str) -> str:
    parts = PLACEHOLDER_RE.split(text)
    out = []
    for part in parts:
        if not part: continue
        if PLACEHOLDER_RE.fullmatch(part):
            out.append(part); continue
        fem = feminine_templates(part)
        if fem:
            out.append(fem); continue
        tokens = re.split(r"(\W+)", part)
        buf = []
        for t in tokens:
            low = t.lower()
            if low in WORD_MAP:
                ru = WORD_MAP[low]
                if t.istitle():
                    ru = ru.capitalize()
                buf.append(ru)
            else:
                buf.append(t)
        out.append("".join(buf))
    return "".join(out)

def auto_translate_xml(input_xml: Path):
    tree = ET.parse(input_xml)
    root = tree.getroot()
    changed = 0
    total_visible = 0

    for s in root.findall(".//String"):
        src = (s.findtext("Source") or "")
        dst_el = s.find("Dest")
        if dst_el is None:
            dst_el = ET.SubElement(s, "Dest")
        dst = dst_el.text or ""
        rec = s.findtext("REC") or ""
        edid = s.findtext("EDID") or ""

        if not is_visible_string(src, rec, edid):
            continue
        total_visible += 1

        if not has_cyrillic(dst):
            ru = translate_piecewise(src)
            if has_cyrillic(ru):
                dst_el.text = ru
                changed += 1

    out_formid = input_xml.with_name(input_xml.stem + "_translated_formid.xml")
    ET.indent(tree, space="  ", level=0)
    tree.write(out_formid, encoding="utf-8", xml_declaration=True)

    root2 = ET.Element("SSTXMLRessources")
    params2 = ET.SubElement(root2, "Params")
    ET.SubElement(params2, "Addon").text = "AUTO"
    ET.SubElement(params2, "Source").text = "english"
    ET.SubElement(params2, "Dest").text = "russian"
    ET.SubElement(params2, "Version").text = "2"
    content2 = ET.SubElement(root2, "Content")
    for s in root.findall(".//String"):
        el = ET.SubElement(content2, "String")
        ET.SubElement(el, "Source").text = s.findtext("Source") or ""
        ET.SubElement(el, "Dest").text = s.findtext("Dest") or ""

    out_strings = input_xml.with_name(input_xml.stem + "_translated_strings_only.xml")
    ET.indent(root2, space="  ", level=0)
    ET.ElementTree(root2).write(out_strings, encoding="utf-8", xml_declaration=True)

    return out_formid, out_strings, changed, total_visible

# ---------------- Themes ----------------
THEMES = {
    "white": {
        "bg":"#0E0E0E", "fg":"#FFFFFF", "muted":"#E1E1E1", "entry_bg":"#111", "entry_fg":"#EEE",
        "btn_bg":"#1A1A1A", "btn_fg":"#FFFFFF", "btn_bg_active":"#2A2A2A",
        "log_fg":"#DDDDDD", "footer":"#CFCFCF",
    },
    "dark": {
        "bg":"#111111", "fg":"#EDEDED", "muted":"#CCCCCC", "entry_bg":"#161616", "entry_fg":"#EDEDED",
        "btn_bg":"#202020", "btn_fg":"#FFFFFF", "btn_bg_active":"#2A2A2A",
        "log_fg":"#D6D6D6", "footer":"#BFBFBF",
    }
}

# ---------------- Main GUI ----------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        Splash(self).wait_window()
        self.deiconify()

        self.title(f"{APP_NAME} — {APP_SUBTITLE}")
        self.geometry("960x540")
        self.minsize(960, 540)

        self.theme_name = "white"
        self.styles = THEMES[self.theme_name]

        self.configure(bg=self.styles["bg"])

        top = tk.Frame(self, bg=self.styles["bg"])
        top.pack(fill="x", padx=16, pady=(14,0))

        self.title_lbl = tk.Label(top, text=APP_NAME, fg=self.styles["fg"], bg=self.styles["bg"], font=("Segoe UI", 18, "bold"))
        self.subtitle_lbl = tk.Label(top, text=APP_SUBTITLE, fg=self.styles["muted"], bg=self.styles["bg"], font=("Segoe UI", 11))
        self.title_lbl.pack(anchor="w"); self.subtitle_lbl.pack(anchor="w")

        hdr = tk.Frame(top, bg=self.styles["bg"]); hdr.pack(fill="x")
        self.ver_lbl = tk.Label(hdr, text=APP_VERSION+"  •  Portable Edition", fg="#BFBFBF", bg=self.styles["bg"], font=("Segoe UI", 10))
        self.ver_lbl.pack(side="right")

        ctr = tk.Frame(self, bg=self.styles["bg"]); ctr.pack(fill="x", padx=16, pady=12)

        self.path_var = tk.StringVar()
        self.entry = tk.Entry(ctr, textvariable=self.path_var, bg=self.styles["entry_bg"], fg=self.styles["entry_fg"],
                              insertbackground=self.styles["entry_fg"], relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=6)

        self.btn_open = tk.Button(ctr, text="📂 Открыть XML / SST", command=self.pick,
                                  bg=self.styles["btn_bg"], fg=self.styles["btn_fg"],
                                  activebackground=self.styles["btn_bg_active"], activeforeground=self.styles["btn_fg"],
                                  relief="flat", padx=14, pady=8, cursor="hand2")
        self.btn_open.pack(side="left", padx=(8,4))

        self.btn_translate = tk.Button(ctr, text="⚙ Перевести", command=self.translate,
                                  bg=self.styles["btn_bg"], fg=self.styles["btn_fg"],
                                  activebackground=self.styles["btn_bg_active"], activeforeground=self.styles["btn_fg"],
                                  relief="flat", padx=14, pady=8, cursor="hand2")
        self.btn_translate.pack(side="left", padx=4)

        self.btn_save = tk.Button(ctr, text="💾 Сохранить", command=self.save_hint,
                                  bg=self.styles["btn_bg"], fg=self.styles["btn_fg"],
                                  activebackground=self.styles["btn_bg_active"], activeforeground=self.styles["btn_fg"],
                                  relief="flat", padx=14, pady=8, cursor="hand2")
        self.btn_save.pack(side="left", padx=4)

        self.btn_esp = tk.Button(ctr, text="🧩 Создать .esp (в разработке)", command=lambda: None,
                                  state="disabled", disabledforeground="#888",
                                  bg=self.styles["btn_bg"], fg=self.styles["btn_fg"], relief="flat", padx=14, pady=8)
        self.btn_esp.pack(side="left", padx=4)

        self.theme_btn = tk.Button(ctr, text="🌓", command=self.toggle_theme,
                                  bg=self.styles["btn_bg"], fg=self.styles["btn_fg"],
                                  activebackground=self.styles["btn_bg_active"], activeforeground=self.styles["btn_fg"],
                                  relief="flat", padx=10, pady=8, cursor="hand2")
        self.theme_btn.pack(side="left", padx=(8,0))

        self.log = tk.Text(self, bg=self.styles["bg"], fg=self.styles["log_fg"],
                           insertbackground=self.styles["entry_fg"], relief="flat", height=16)
        self.log.pack(fill="both", expand=True, padx=16, pady=(4,8))

        self.footer = tk.Label(self, text="Разработано агентством THE12. Основано на интеллекте.",
                               fg=self.styles["footer"], bg=self.styles["bg"], font=("Segoe UI", 10))
        self.footer.pack(side="bottom", pady=(0,8))

        self.log_write("Готово к работе. Выберите XML/SST и нажмите «Перевести».")

    def apply_theme(self):
        s = self.styles
        self.configure(bg=s["bg"])
        for w in (self.title_lbl, self.subtitle_lbl, self.ver_lbl, self.footer, self.log):
            w.config(bg=s["bg"], fg=(s["fg"] if w is self.title_lbl else (s["muted"] if w is self.subtitle_lbl else (s["footer"] if w is self.footer else s["log_fg"]))))
        self.entry.config(bg=s["entry_bg"], fg=s["entry_fg"], insertbackground=s["entry_fg"])
        for b in (self.btn_open, self.btn_translate, self.btn_save, self.btn_esp, self.theme_btn):
            b.config(bg=s["btn_bg"], fg=s["btn_fg"], activebackground=s["btn_bg_active"], activeforeground=s["btn_fg"])
        self.log.config(bg=s["bg"], fg=s["log_fg"], insertbackground=s["entry_fg"])

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "white" else "white"
        self.styles = THEMES[self.theme_name]
        self.apply_theme()

    def log_write(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.update_idletasks()

    def pick(self):
        fp = filedialog.askopenfilename(title="Выбор XML/SST",
                                        filetypes=[("xTranslator/XML/SST","*.xml *.sst *.SST"),("Все файлы","*.*")])
        if fp:
            self.path_var.set(fp)
            self.log_write(f"Выбран файл: {fp}")

    def translate(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Ошибка", "Выберите файл XML или SST.")
            return
        p = Path(path)
        if not p.exists():
            messagebox.showerror("Ошибка", "Файл не найден.")
            return
        try:
            self.log_write("Перевод начат…")
            out_formid, out_strings, changed, total = auto_translate_xml(p)
            self.log_write(f"Создано: {out_formid.name}, {out_strings.name}")
            self.log_write(f"Автоперевод применён к {changed} из {total} видимых строк.")
            messagebox.showinfo("Готово",
                                f"Создано:\n- {out_formid}\n- {out_strings}\n\n"
                                f"Автоперевод: {changed} из {total}.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            self.log_write(f"[Ошибка] {e}")

    def save_hint(self):
        messagebox.showinfo("Сохранение",
                            "Файлы уже сохранены рядом с исходным XML/SST:\n"
                            "* *_translated_formid.xml\n* *_translated_strings_only.xml\n\n"
                            "Импортируйте в xTranslator: Use FormID references → при необходимости Strings Only.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
