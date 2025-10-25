
THE12 Mod Translator — v1.2 Beta (Portable, Windows 10 x64)
Интеллектуальный перевод модов Skyrim / Fallout

Разработано агентством THE12. Основано на интеллекте.

Что это:
- Portable-приложение для перевода XML/SST из xTranslator.
- Работает офлайн; итог — *_translated_formid.xml и *_translated_strings_only.xml.
- Темы: THE12 White / THE12 Dark (переключение кнопкой 🌓).
- Splash-анимация с логотипом (SVG-стиль) и эффектом «дыхания».

Как получить .exe БЕЗ установки Python:
1) Создайте репозиторий на GitHub и загрузите туда содержимое этой папки.
2) Вкладка Actions активируется автоматически.
3) Откройте «Actions» → дождитесь завершения «Build Portable EXE».
4) Перейдите в «Artifacts» и скачайте THE12_ModTranslator.exe.

Локальная сборка (если нужно):
- pip install pyinstaller
- pyinstaller --noconfirm --onefile --windowed --name THE12_ModTranslator main.py

