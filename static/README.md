# Структура фронтенда

Фронтенд остаётся без сборщика и стороннего JavaScript-фреймворка.

```text
static/
├── index.html          # Семантическая разметка страницы
├── css/
│   ├── base.css        # Tokens, reset, accessibility, header и hero
│   ├── workspace.css   # Загрузка, validation states, progress и инструкция
│   ├── result.css      # Результат, before/after, slider, actions и footer
│   └── responsive.css  # Breakpoints, reduced motion и forced colors
└── js/
    └── app.js          # Валидация, API-запрос, UI state и event handlers
```

CSS подключён в указанном порядке: `responsive.css` должен оставаться
последним, чтобы исходный cascade не менялся. `app.js` подключён classic-script
в конце `body`; он намеренно не переведён на `async`, `defer` или ES modules,
поскольку использует общий жизненный цикл состояния и выполняется после готовой
DOM-разметки.

