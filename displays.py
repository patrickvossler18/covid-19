import matplotlib.pyplot as pl
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.transforms import blended_transform_factory as blend
from imageio import imwrite
import pandas as pd
import numpy as np
import datetime
import mpld3
    
# Aesthetic parameters
fig_size = (16, 9)
ax_box = [0.25, 0.1, 0.65, 0.8]

tfs = 25 # title font size
lfs = 20 # label font size
tkfs = 15 # tick font size

title_pos = (0.05, 0.94)
ylab_pos = (-0.2, 0.5)

ylims = (0.0, None)
n_yticks = 8

cmap = pl.cm.cubehelix

data_line_kw = dict(
                    linewidth = 4,
                    color = 'darkslateblue',
                    )

ref_line_kw = dict(color = 'black',
                   linewidth = 1.5,
                   dashes = [4, 2],
                  )

def choose_y(pos, priors, min_dist=0.3, inc=0.01):
    priors = np.array(priors)

    if len(priors) == 0:
        return pos
    
    dif = pos - priors
    closest = np.min(np.abs(dif))
    closest_i = np.argmin(np.abs(dif))
    while closest < min_dist:
        inc_ = inc * np.sign(dif[closest_i])
        pos += inc_
        closest = np.min(np.abs(pos - priors))

    return pos

def generate_plot(filename, columns, title='', ylabel='', log=False):
    """Returns numpy array with image of full figure
    """

    # process params
    if not isinstance(columns, (list, np.ndarray)):
        columns = [columns]
    if not title and len(columns) == 1:
        title = columns[0]

    # load data
    data = pd.read_csv(filename, index_col=0)

    # setup axes
    fig = pl.figure(figsize=fig_size)
    canvas = FigureCanvas(fig)
    ax = fig.add_axes(ax_box) 

    # plot data
    colors = cmap(np.linspace(0.05, 0.76, len(columns)))
    for column, color in zip(columns, colors):
        # specify data
        ydata = data[column].values
        ydata[np.isinf(ydata)] = np.nan
        xdata = np.arange(len(ydata))

        # aesthetic prep
        if len(columns) > 1:
            data_line_kw['color'] = color

        # plot line
        ax.plot(xdata, ydata, **data_line_kw)

    # plot reference data
    #ax.axhline(3, zorder=101, **ref_line_kw)
    pct90 = np.nanpercentile(data[columns].values, 90) # global 90th percentile values
    ax.axhspan(0, pct90, color='lightgrey', alpha=0.35, lw=0)

    # axes/spines aesthetics
    ax.set_ylim(ylims)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(True)
    ax.spines['bottom'].set_visible(True)
    
    # y scale
    if log:
        ax.set_yscale('log')

    # xticks
    xtl = [pd.to_datetime(s).strftime('%-m/%d') for s in data.index.values]
    ax.set_xticks(np.arange(len(xdata)))
    ax.set_xticklabels(xtl, rotation=90)
    ax.tick_params(pad=11, length=10, labelsize=tkfs)

    # x limit
    subdata = data[columns].values
    allnan = np.all(np.isnan(subdata), axis=1)
    first_nonnan = np.argwhere(allnan == False)[0][0]
    ax.set_xlim([first_nonnan - 0.5, None])

    # yticks
    yticks = ax.get_yticks()
    maxx = np.ceil(np.max(yticks))
    minn = 0
    if maxx < 10:
        step = 2
    else:
        step = 5
    int_range = np.arange(minn, maxx, step).astype(int)
    if not log:
        ax.set_yticks(int_range)

    # labels for data lines
    prior_ys = []
    min_dist = 0.05 * np.abs(np.diff(ax.get_ylim()))
    for column, color in zip(columns, colors):
        # specify data
        ydata = data[column].values
        ydata[np.isinf(ydata)] = np.nan
        xdata = np.arange(len(ydata))

        if len(columns) > 1:
            ypos = choose_y(ydata[-1], prior_ys, min_dist=min_dist)
            prior_ys.append(ypos)
            ax.text(xdata[-1] + 0.1, ypos, column, ha='left', va='center', color=color, fontsize=lfs)

    # labels for axes
    if title:
        ax.text(title_pos[0], title_pos[1], title, fontsize=tfs, weight='bold', ha='left', va='center', transform=ax.transAxes)
    ax.text(ylab_pos[0], ylab_pos[1], ylabel, fontsize=lfs, ha='center', va='center', transform=ax.transAxes)

    # convert to image, html
    canvas.draw()
    s, (width, height) = canvas.print_to_buffer()
    img = np.fromstring(s, np.uint8).reshape((height, width, 4))
    #html = mpld3.fig_to_html(fig) # Quite buggy so on hold
    pl.close(fig)

    return img#, html

def create_html(imgs, htmls=None):

    if not isinstance(imgs, list):
        imgs = [imgs]
        htmls = [htmls]

    # Option 1: generate pngs from image data
    img_tags = []
    for idx, img in enumerate(imgs):
        fname = f'images/{idx}.png'
        imwrite(fname, img)
        width = fig_size[0] * 40
        height = fig_size[1] * 40
        img_tag = f'<div><img src="{fname}" width="{width}" height="{height}"></div>'
        img_tags.append(img_tag)
    with open('test_webpage.html', 'w') as f:
        f.write('<html><body>\n{}\n</body></html>'.format('\n'.join(img_tags)))

    # Option 2: use htmls wth interactive matplotlib; quite buggy
    #with open('test_webpage.html', 'w') as f:
    #    f.write('<html><body>\n{}\n</body></html>'.format('\n\n'.join(htmls)))

