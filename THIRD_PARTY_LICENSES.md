# Third-party licenses and model provenance

Аудит выполнен **2026-08-17** по официальным model cards, API Hugging Face, репозиториям правообладателей и метаданным PyPI. Это технический license gate, а не юридическая консультация.

## Выбранная модель и неизменяемый артефакт

| Поле | Зафиксированное значение |
|---|---|
| Model ID | `ZhengPeng7/BiRefNet_dynamic` |
| Hugging Face revision | `280306042f57b7a33854319da62fd86aaa89ec4c` |
| Файл весов | `model.safetensors` |
| Размер | `444473596` байт |
| SHA-256 файла / Git LFS oid | `e3d2e4884e51ff30f0cd630edc6b1e41b06b7f23a0a2a5169f7b7cb33a711c2d` |
| Git blob oid LFS-pointer | `2744b15335ee7d7b3b5cd9a904d23932ef43e296` |

Проверяемые источники:

- [HF API для точной revision](https://huggingface.co/api/models/ZhengPeng7/BiRefNet_dynamic/revision/280306042f57b7a33854319da62fd86aaa89ec4c) возвращает тот же commit SHA и `license: mit`.
- [HF API tree с LFS metadata](https://huggingface.co/api/models/ZhengPeng7/BiRefNet_dynamic/tree/280306042f57b7a33854319da62fd86aaa89ec4c?recursive=true&expand=true) возвращает для `model.safetensors` указанные `size` и `lfs.oid`. Для LFS `oid` имеет вид SHA-256 содержимого, а не SHA Git-pointer.
- [Model card ровно на этой revision](https://huggingface.co/ZhengPeng7/BiRefNet_dynamic/blob/280306042f57b7a33854319da62fd86aaa89ec4c/README.md) содержит YAML `license: mit`.
- Дополнительно проверен уже загруженный локальный LFS-blob: размер `444473596` байт, фактический `Get-FileHash -Algorithm SHA256` вернул `E3D2E4884E51FF30F0CD630EDC6B1E41B06B7F23A0A2A5169F7B7CB33A711C2D`.

После фактической загрузки файл проверяется независимо:

```powershell
$modelPath = python -c "from huggingface_hub import hf_hub_download; print(hf_hub_download('ZhengPeng7/BiRefNet_dynamic', 'model.safetensors', revision='280306042f57b7a33854319da62fd86aaa89ec4c', local_files_only=True))"
Get-FileHash -Algorithm SHA256 -LiteralPath $modelPath
```

Результат должен в точности совпасть с SHA-256 выше. Приложение выполняет ту же проверку автоматически перед загрузкой модели. Одновременно закреплены `revision` и `code_revision`, включены `trust_remote_code=True` и `use_safetensors=True`; незакрепленный `main` или fallback на pickle-веса не допускаются.

## Лицензия кода, весов и backbone

- **Веса и файлы HF-репозитория:** MIT согласно metadata зафиксированной model card. В репозитории модели нет отдельного текста `LICENSE`, поэтому доказательство — декларация издателя в card; [документация Hugging Face](https://huggingface.co/docs/hub/repositories-licenses) описывает поле `license` как декларацию лицензии репозитория. MIT разрешает коммерческое использование при сохранении copyright/permission notice.
- **Remote model code (`birefnet.py`, `BiRefNet_config.py`):** загружается с той же revision. Card связывает его с официальным BiRefNet; [официальный исходный репозиторий BiRefNet имеет MIT на зафиксированном commit](https://github.com/ZhengPeng7/BiRefNet/blob/25cb9309bacf3dde954e4584594e16e142c51de5/LICENSE).
- **Backbone:** в зафиксированном `birefnet.py` выбран `swin_v1_l`; реализация Swin помечена MIT, как и [официальный Swin Transformer на зафиксированном commit](https://github.com/microsoft/Swin-Transformer/blob/f82860bfb5225915aca09c3227159ee9e1df874d/LICENSE). Отдельный backbone checkpoint при inference не загружается (`bb_pretrained: false`), его параметры уже входят в выбранный `model.safetensors`.

### Training-data provenance: отдельный, не закрытый лицензией весов риск

Card говорит, что модель обучена на **DIS-TR**. [Официальный DIS5K Terms of Use](https://github.com/xuebinqin/DIS/blob/main/DIS5K-Dataset-Terms-of-Use.pdf) ограничивает использование самого набора некоммерческими исследованиями и образованием. Конфигурация BiRefNet указывает на Swin-L `22kto1k`; [официальное соглашение доступа ImageNet](https://image-net.org/accessagreement) также говорит о некоммерческих исследованиях/образовании.

Это не меняет явно заявленную издателем MIT-лицензию конкретного файла весов автоматически, но означает отсутствие подтвержденной цепочки прав на training images, договорных гарантий и indemnity. Поэтому:

- **PASS:** конкретный код, опубликованные веса и прямые runtime-пакеты не содержат запрета commercial/production.
- **CONDITIONAL:** это достаточно для предусмотренного заданием demo-MVP с документированным data risk, но не является «юридически очищенной» моделью для реального коммерческого production. Для такого запуска нужны юридическая проверка и, при необходимости, письменные разрешения либо коммерческий поставщик.

## Прямые зависимости, закрепленные в `requirements.txt`

Ссылки на PyPI подтверждают конкретный релиз; ссылки на официальный source/LICENSE — условия. Все перечисленные лицензии допускают коммерческое использование при соблюдении notices и иных условий лицензии.

| Пакет | Лицензия | Официальное подтверждение |
|---|---|---|
| `fastapi==0.141.1` | MIT | [релиз](https://pypi.org/project/fastapi/0.141.1/) · [LICENSE](https://github.com/fastapi/fastapi/blob/0.141.1/LICENSE) |
| `starlette==1.3.1` | BSD-3-Clause | [релиз](https://pypi.org/project/starlette/1.3.1/) · [LICENSE](https://github.com/Kludex/starlette/blob/1.3.1/LICENSE.md) |
| `uvicorn==0.40.0` | BSD-3-Clause | [релиз](https://pypi.org/project/uvicorn/0.40.0/) · [LICENSE](https://github.com/Kludex/uvicorn/blob/0.40.0/LICENSE.md) |
| `python-multipart==0.0.32` | Apache-2.0 | [релиз](https://pypi.org/project/python-multipart/0.0.32/) · [LICENSE](https://github.com/Kludex/python-multipart/blob/0.0.32/LICENSE.txt) |
| `Pillow==12.3.0` | MIT-CMU | [релиз](https://pypi.org/project/pillow/12.3.0/) · [LICENSE](https://github.com/python-pillow/Pillow/blob/12.3.0/LICENSE) |
| `torch==2.13.0` | BSD-3-Clause (верхний уровень) + bundled third-party notices | [релиз](https://pypi.org/project/torch/2.13.0/) · [LICENSE](https://github.com/pytorch/pytorch/blob/v2.13.0/LICENSE) · [NOTICE](https://github.com/pytorch/pytorch/blob/v2.13.0/NOTICE) |
| `torchvision==0.28.0` | BSD-3-Clause | [релиз](https://pypi.org/project/torchvision/0.28.0/) · [LICENSE](https://github.com/pytorch/vision/blob/v0.28.0/LICENSE) |
| `transformers==5.15.0` | Apache-2.0 | [релиз](https://pypi.org/project/transformers/5.15.0/) · [LICENSE](https://github.com/huggingface/transformers/blob/v5.15.0/LICENSE) |
| `huggingface-hub==1.27.0` | Apache-2.0 | [релиз](https://pypi.org/project/huggingface-hub/1.27.0/) · [LICENSE](https://github.com/huggingface/huggingface_hub/blob/v1.27.0/LICENSE) |
| `safetensors==0.8.0` | Apache-2.0 | [релиз](https://pypi.org/project/safetensors/0.8.0/) · [официальная декларация](https://github.com/huggingface/safetensors/tree/v0.8.0#license) |
| `timm==1.0.23` | Apache-2.0 | [релиз](https://pypi.org/project/timm/1.0.23/) · [LICENSE](https://github.com/huggingface/pytorch-image-models/blob/v1.0.23/LICENSE) |
| `numpy==1.26.4` | BSD-3-Clause (верхний уровень) + bundled notices | [релиз](https://pypi.org/project/numpy/1.26.4/) · [LICENSE](https://github.com/numpy/numpy/blob/v1.26.4/LICENSE.txt) |
| `kornia==0.8.2` | Apache-2.0 | [релиз](https://pypi.org/project/kornia/0.8.2/) · [LICENSE](https://github.com/kornia/kornia/blob/v0.8.2/LICENSE) |
| `einops==0.8.1` | MIT | [релиз](https://pypi.org/project/einops/0.8.1/) · [LICENSE](https://github.com/arogozhnikov/einops/blob/v0.8.1/LICENSE) |
| `accelerate==1.12.0` | Apache-2.0 | [релиз](https://pypi.org/project/accelerate/1.12.0/) · [LICENSE](https://github.com/huggingface/accelerate/blob/v1.12.0/LICENSE) |
| `pytest==9.0.3` (test only) | MIT | [релиз](https://pypi.org/project/pytest/9.0.3/) · [LICENSE](https://github.com/pytest-dev/pytest/blob/9.0.3/LICENSE) |
| `httpx==0.28.1` (test only) | BSD-3-Clause | [релиз](https://pypi.org/project/httpx/0.28.1/) · [LICENSE](https://github.com/encode/httpx/blob/0.28.1/LICENSE.md) |

На дату аудита `pip-audit -r requirements.txt` не обнаружил известных OSV-advisories для итоговых прямых pins и их разрешенного набора зависимостей. Это временный security snapshot, а не свойство лицензии: перед развертыванием аудит нужно повторить.

При распространении контейнера/сборки нужно сохранить license/NOTICE из самих установленных distributions; особенно это относится к бинарным wheels PyTorch, NumPy, Pillow и их bundled libraries. Таблица покрывает прямые pins, но не заменяет SBOM/аудит полного транзитивного lock для production. Отдельно не проверялись CUDA, cuDNN и системные драйверы: GPU-сборка добавляет условия NVIDIA; текущий gate относится к Python-зависимостям проекта и CPU-compatible запуску.

## Не включенные модели

- **BEN2 Base:** [зафиксированная card, MIT](https://huggingface.co/PramaLLC/BEN2/blob/e48a20765fb421d19dcdb0bf3cc61e802ca5ec8f/README.md). Для исследования проверен только `BEN2_Base.pth`: `1134584206` байт, SHA-256 `926144a876bda06f125555b4f5a239ece89dc6eb838a863700ca9bf192161a1c`. В приложение не входит; Base нельзя смешивать с закрытым full-вариантом.
- **FeyNoBg:** [зафиксированная card, Apache-2.0](https://huggingface.co/feyninc/FeyNobg/blob/c1fd67fbefe3efeb78fe2a003270fb5350a0bb1c/README.md) и [NoBg Apache-2.0 на проверенном commit](https://github.com/feyninc/nobg/blob/335b5dd0b9c4610c80efc9f28f78a26016dc350b/LICENSE). Для исследования проверен `model.safetensors`: `1051353168` байт, SHA-256 `7ee181389acf07c6dcf3d72caba2d169224caacdde8bb837ecf7aa3e22e0c3aa`. В приложение не входит; provenance training datasets раскрыта не полностью.
- **RMBG-2.0:** [зафиксированная card](https://huggingface.co/briaai/RMBG-2.0/blob/5df4c9c76d8170882c34f6986e848ee07fd0ba43/README.md) и [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en). Публичные веса **запрещены** этим проектом; коммерческое использование возможно только по отдельному договору/API.

## Обязательства при передаче MVP третьим лицам

1. Не менять Model ID/revision/hash без повторного аудита и обновления этого файла.
2. Не заменять `model.safetensors` на `pytorch_model.bin` и не разрешать непроверенный fallback.
3. Передавать MIT/BSD/Apache/MIT-CMU license notices вместе с распространяемой сборкой; для Apache-2.0 отмечать изменения и сохранять NOTICE, если он присутствует.
4. Не включать публичные веса RMBG-2.0 и другие `Non-Commercial`, `Research Only` или неясно лицензированные артефакты.
5. Для реального коммерческого production закрыть документированные риски DIS5K/ImageNet и выполнить полный юридический и транзитивный dependency audit.
