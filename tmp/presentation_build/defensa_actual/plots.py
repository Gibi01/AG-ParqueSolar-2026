"""Evidence plots only: coordinates and attributes from the recorded run."""
import os,json
from pathlib import Path
OUT=Path(__file__).parent
os.environ['MPLCONFIGDIR']=str(OUT/'mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geopandas as gpd
import shapely
import numpy as np
d=json.loads((OUT/'evidence.json').read_text(encoding='utf-8'))
cells=gpd.read_file(OUT/'cells.geojson').set_index('cell_id')
region=gpd.read_file(OUT/'region.geojson')
navy='#123442';teal='#13877C';gold='#E5AE41';pale='#E8F2EF'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':navy,'axes.labelcolor':navy,'xtick.color':navy,'ytick.color':navy,'font.size':13})
def save(fig,name):
    fig.savefig(OUT/name,dpi=170,bbox_inches='tight',facecolor='white');plt.close(fig)
def park(p,name,highlight=None,bounds=None):
    g=cells.loc[p['cells']]
    fig,ax=plt.subplots(figsize=(5,4.2));g.plot(ax=ax,color=teal,edgecolor='white',linewidth=2)
    if highlight:
        cells.loc[highlight].plot(ax=ax,color=gold,edgecolor='white',linewidth=2)
    b=g.total_bounds if bounds is None else bounds
    cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2;r=max(b[2]-b[0],b[3]-b[1],1500)*.7
    ax.set(xlim=(cx-r,cx+r),ylim=(cy-r,cy+r));ax.set_aspect('equal');ax.axis('off')
    save(fig,name)
park(d['first'],'winner.png')
for g in [0,50,200]:park(next(p for p in d['leaders'] if p['generation']==g),f'leader-{g}.png')
for i,p in enumerate(d['prefixes']):park(p,f'prefix-{i}.png',bounds=cells.loc[d['example']['cells']].total_bounds)
for k in ['a','b','child']:park(d['crossover'][k],f'cross-{k}.png')
m=d['mutation'];b=cells.loc[m['child']['cells']].total_bounds
park(m['parent'],'mutation-before.png',bounds=b)
park(m['child'],'mutation-after.png',highlight=list(set(m['child']['cells'])-set(m['parent']['cells'])),bounds=b)
for mode in ['initial','location','grid']:
    fig,ax=plt.subplots(figsize=(5,6.3));region.plot(ax=ax,color=pale,edgecolor=navy,linewidth=1.4)
    if mode=='initial':
        ax.scatter([p['centroid_x_m'] for p in d['initial']],[p['centroid_y_m'] for p in d['initial']],s=24,color=teal,edgecolors='white',linewidth=.4)
    else:
        p=d['first'];ax.scatter([p['centroid_x_m']],[p['centroid_y_m']],s=75,color=gold,edgecolors=navy,zorder=4)
        if mode=='location':ax.annotate('Candidato',xy=(p['centroid_x_m'],p['centroid_y_m']),xytext=(p['centroid_x_m']+90000,p['centroid_y_m']-20000),arrowprops={'arrowstyle':'->','color':navy},fontsize=13)
    ax.axis('off');save(fig,mode+'.png')
# The winning geometry and all recorded examples must reproduce reported metrics.
for p in d['leaders']+d['prefixes']+[d['first'],d['crossover']['a'],d['crossover']['b'],d['crossover']['child'],m['parent'],m['child']]:
    geom=shapely.union_all(cells.loc[p['cells']].geometry.to_numpy())
    assert np.isclose(geom.area/1e6,p['park_area_km2'])
    assert np.isclose(geom.length,p['park_perimeter_m'])
    assert np.isclose(4*np.pi*geom.area/geom.length**2,p['compactness_score'])
    assert p['installed_power_mw']<=80
assert d['crossover']['raw_child']['genes']==d['crossover']['a']['genes'][:d['crossover']['cut']]+d['crossover']['b']['genes'][d['crossover']['cut']:]
print('All recorded geometry metrics and crossover provenance verified.')
