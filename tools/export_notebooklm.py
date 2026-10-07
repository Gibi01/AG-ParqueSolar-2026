"""Exportar las fuentes vigentes para estudiar y presentar el proyecto."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'NotebookLM_Proyecto_Actual.zip'


def export_sources():
    files = {ROOT / name for name in ['README.md', 'config.yaml', 'config.test.yaml', 'requirements.txt']}
    for folder, extensions in {
        'docs': {'.md'}, 'src': {'.py'}, 'tests': {'.py'},
        'tasks': {'.py', '.md'}, 'tools/reporting': {'.py'},
        'Informes': {'.pdf', '.docx'},
    }.items():
        files.update(p for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in extensions)
    files.add(Path(__file__).resolve())
    for run in (ROOT / 'results/spatial').glob('run-*'):
        files.update(p for p in run.iterdir() if p.is_file() and p.suffix in {'.json', '.csv', '.geojson', '.html'})
    experiment = ROOT / 'results/experiments/search-quality-compactness-20261006'
    files.update(p for p in experiment.iterdir() if p.is_file() and p.suffix in {'.json', '.md', '.csv', '.html', '.png'})
    files.update(p for p in (experiment / 'audit_archive').glob('*') if p.is_file() and p.suffix in {'.json', '.md', '.csv'})
    with ZipFile(DESTINATION, 'w', compression=ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f'{len(files)} fuentes vigentes: {DESTINATION}')


if __name__ == '__main__':
    export_sources()
