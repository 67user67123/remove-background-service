# MVP удаления фона

Демонстрационный сервис принимает JPG/PNG, удаляет фон моделью
`ZhengPeng7/BiRefNet_dynamic` и возвращает прозрачный PNG. Исходник и
результат обрабатываются только в памяти: базы данных и постоянного хранилища
в приложении нет.

## Требования

- Python 3.11;
- около 2 ГБ свободного места для окружения, кэша модели и весов;
- CPU с достаточным объёмом RAM либо CUDA-совместимая GPU.

При первом запуске Hugging Face скачает зафиксированные веса размером около
424 MiB. Устройство выбирается автоматически: CUDA при её доступности, иначе
CPU.

## Установка

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux/macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Для CPU-only окружения PyTorch можно заранее установить из официального
индекса, после чего выполнить обычную установку requirements:

```powershell
python -m pip install torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
```

## Запуск

```powershell
uvicorn app:create_app --factory --reload
```

Откройте <http://127.0.0.1:8000>. Проверка состояния доступна по адресу
<http://127.0.0.1:8000/health>.

Пример API-запроса:

```powershell
curl.exe -X POST -F "file=@photo.jpg" http://127.0.0.1:8000/remove-background --output result.png
```

## Тесты

```powershell
python -m pytest -q
```

Три smoke-теста проверяют health-check, выдачу фронтенда и основной PNG API.
Они подменяют тяжёлую модель тестовой реализацией, поэтому не скачивают веса
и не требуют GPU.

## Модель и ограничения

Используется только `ZhengPeng7/BiRefNet_dynamic` на immutable revision
`280306042f57b7a33854319da62fd86aaa89ec4c`. Загружаются и веса, и удалённый
код именно этой revision; при старте SHA-256 safetensors сверяется с
зафиксированным значением. Публичные веса RMBG-2.0 в приложение не входят.
Подробности о выборе — в [research.md](research.md), сведения о лицензиях и
SHA-256 весов — в [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

Ограничения MVP:

- запрос остаётся открытым до окончания inference; внешних очередей,
  фоновых задач и пакетной обработки нет;
- MVP допускает только одну загрузку одновременно; следующий POST ждёт, но
  `/health` и страница продолжают отвечать;
- CPU-обработка может занимать заметное время;
- вход ограничен 20 MiB, а длинная сторона для inference уменьшается до
  2048 px; итоговый PNG сохраняет размер декодированного исходника;
- волосы, полупрозрачные предметы, размытие, тени и слабый контраст могут
  давать артефакты маски;
- открытая лицензия checkpoint не является гарантией происхождения всех
  обучающих данных.

Сервис рассчитан на локальную демонстрацию. При публикации в интернет нужны
как минимум TLS, ограничения частоты запросов и таймауты загрузки/ответа на
reverse proxy; они сознательно не входят в этот MVP.
