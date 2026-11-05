"""Rebuild the read-only dashboard from the current repository documents."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import re
import subprocess
import shutil

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent.parent


def section(text, heading):
    match = re.search(r'^## ' + re.escape(heading) + r'\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1).strip() if match else ''


def plain(text):
    return re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text).replace('`', '').replace('**', '')


meta = [
    ('Весовая ABCD-классификация', 'Печатная форма · EPF', 'Логистика', 'Масса упаковок и правила классов', ['Техпроверка', 'Правило', 'Правило'], 'Проверить источник брутто и контракт печати комплекта.', ['В формуле веса G12 есть необъяснённый коэффициент ×1,1.', 'Не хватает обязательной характеристики.', 'После уточнений доля включает текущую позицию. Прежний пример A,A,B,C,D больше не действующий эталон.']),
    ('Остаточный срок годности', 'Контроль проведения · CFE', 'Закупки', 'Две складские схемы, один контроль', ['Техпроверка', 'Правило', 'Данные'], 'Уточнить ордерный маршрут и правила отсутствующей серии.', []),
    ('Внеплановая приёмка', 'Документ и отчёт · CFE', 'Склад', 'Очередь бухгалтеру на прошлую дату', ['Техпроверка', 'Правило', 'Правило', 'Правило'], 'Проверить распоряжение без товаров и определить события исторической очереди.', ['Прежний макет исключает ордер целиком; актуальная очередь учитывает связанное количество.', 'Формулы дней G14:G19 содержат необъяснённое +7.', 'Исходный пример и лист сценариев расходятся по ПО-10570 и ПО-10624. После новых правил числовой эталон нужно пересобрать.']),
    ('Лимиты закупок филиалов', 'Документ и аналитика · CFE', 'Финансы', 'План и факт без НДС', ['Правило', 'Правило', 'Данные', 'Правило'], 'Определить участвующие строки и пересчитать эталоны без НДС.', ['В отчёте отсутствует дата отгрузок 27.11.', 'Возвраты уже отрицательные в источнике, формулы меняют знак ещё раз.', 'При нулевом плане D13 возвращает 0 вместо «н/д».', 'Прежний итог 6 110 000 — арифметическая сверка исходной книги. Для нового режима без НДС он не подтверждён.']),
    ('Контрольная цена заказа', 'Документ и цены · CFE', 'Продажи', 'Маржа 9% и пересчёт при проведении', ['Правило', 'Техпроверка', 'Данные', 'Правило'], 'Уточнить смысл даты проведения и источник закупочной цены.', []),
    ('Корректировка плана продаж', 'Права и аудит · CFE', 'Планирование', 'Выборочный доступ с проверкой зависимостей', ['Техпроверка', 'Техпроверка', 'Правило', 'Техпроверка'], 'Проверить аудит после отката и узкий перехват типовой защиты.', []),
]
paths = sorted((ROOT / 'openspec/changes').glob('dev-*'))
assert len(paths) == 6, 'Expected six DEV-1C changes'
documents = {}
# Keep the embedded reader scoped to these six changes and their wiki context.
# Never recursively import future OpenSpec changes, archives, logs or local files.
document_paths = [ROOT / 'openspec/inbox-development-index.md', ROOT / 'openspec/wiki-reconciliation.md', ROOT / 'llm-wiki/wiki/index.md']
for change in paths:
    document_paths.extend(change / name for name in ['proposal.md', 'design.md', 'explore.md', 'tasks.md'])
    document_paths.extend((change / 'specs').glob('*/spec.md'))
for branch in ['sources', 'concepts', 'entities', 'questions']:
    document_paths.extend((ROOT / 'llm-wiki/wiki' / branch).glob('*.md'))
for path in sorted(set(document_paths)):
    resolved = path.resolve()
    relative = path.relative_to(ROOT).as_posix()
    if resolved != ROOT.resolve() / path.relative_to(ROOT) or any(part.startswith('.') for part in path.relative_to(ROOT).parts):
        raise ValueError('Embedded document is outside the allowed project context')
    documents[relative] = path.read_text()
reconciliation = (ROOT / 'openspec/wiki-reconciliation.md').read_text()
answers = {}
for line in reconciliation.splitlines():
    if not line.startswith('| DEV-1C-'):
        continue
    cells = [x.strip() for x in line.strip('|').split('|')]
    number = int(re.search(r'DEV-1C-(\d+)', cells[0]).group(1))
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', cells[2])
    source = next((url for label, url in links if label == 'Конспект'), '')
    from urllib.parse import unquote
    source = (ROOT / 'openspec' / unquote(source)).resolve().relative_to(ROOT).as_posix() if source else ''
    answers.setdefault(number, []).append({'before': plain(cells[0].split('·', 1)[-1].strip()), 'answer': plain(cells[1]), 'source': source})
items = []
for i, path in enumerate(paths):
    proposal = (path / 'proposal.md').read_text()
    design = (path / 'design.md').read_text()
    specpath = next((path / 'specs').glob('*/spec.md'))
    spec = specpath.read_text()
    tasktext = (path / 'tasks.md').read_text()
    tasks = [{'done': state.lower() == 'x', 'text': text} for state, text in re.findall(r'^- \[([ xX])\] (.+)$', tasktext, re.M)]
    questions = re.findall(r'^- (.+)$', section(design, 'Open Questions'), re.M)
    title, kind, area, subtitle, cats, action, issues = meta[i]
    assert len(questions) == len(cats)
    docs = {name.replace('.md', ''): p.relative_to(ROOT).as_posix() for name in ['proposal.md', 'design.md', 'explore.md', 'tasks.md'] if (p := path / name).exists()}
    docs['spec'] = specpath.relative_to(ROOT).as_posix()
    items.append({'id': f'DEV-1C-{i+1:02}', 'num': i+1, 'change': path.name, 'title': title, 'kind': kind, 'area': area, 'subtitle': subtitle, 'action': action, 'issues': issues, 'docs': docs, 'questions': [{'text': q, 'type': cat} for q, cat in zip(questions, cats)], 'answers': answers.get(i+1, []), 'tasks': tasks, 'requirements': spec.count('### Requirement:'), 'scenarios': spec.count('#### Scenario:'), 'artifacts': sum(bool((path/n).exists()) for n in ['proposal.md', 'design.md', 'tasks.md']) + int(specpath.exists()), 'summary': re.findall(r'^- (.+)$', section(proposal, 'What Changes'), re.M)})
validation = json.loads(subprocess.check_output(['openspec', 'validate', '--changes', '--strict', '--json', '--no-interactive'], cwd=ROOT))
revision = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()
data = {'generatedAt': datetime.now(ZoneInfo('Europe/Moscow')).isoformat(timespec='seconds'), 'revision': revision, 'items': items, 'documents': documents, 'validation': validation, 'sourceDigest': hashlib.sha256(json.dumps(documents, ensure_ascii=False, sort_keys=True).encode()).hexdigest(), 'sourceCount': len(list((ROOT/'llm-wiki/wiki/sources').glob('*.md')))}
out = SITE / 'dist'
out.mkdir(exist_ok=True)
for name in ['index.html', 'app.js', 'styles.css']:
    shutil.copyfile(SITE / 'web' / name, out / name)
(out/'data.js').write_text('window.DASHBOARD_DATA = ' + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + ';\n')
(out/'snapshot.json').write_text(json.dumps({k:v for k,v in data.items() if k != 'documents'}, ensure_ascii=False, indent=2)+'\n')
standalone = (out/'index.html').read_text()
standalone = standalone.replace('<link rel="stylesheet" href="styles.css">', '<style>'+(out/'styles.css').read_text()+'</style>')
standalone = standalone.replace('<script src="data.js"></script><script src="app.js"></script>', '<script>'+(out/'data.js').read_text()+'</script><script>'+(out/'app.js').read_text().replace('</script', '<\\/script')+'</script>')
(SITE/'dashboard.html').write_text(standalone)
print(json.dumps({'changes': len(items), 'questionGroups': sum(len(x['questions']) for x in items), 'tasks': sum(len(x['tasks']) for x in items), 'complete': sum(t['done'] for x in items for t in x['tasks']), 'validationPassed': validation['summary']['totals']['passed']}, ensure_ascii=False))
