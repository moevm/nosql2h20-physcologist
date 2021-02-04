import matplotlib.pyplot as plt
from scipy import interpolate
import numpy as np
from io import BytesIO
import base64


def image_from_plt(fig):
    tmpfile = BytesIO()
    fig.savefig(tmpfile, format='png', transparent=True)
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    return "data:image/png;base64," + encoded


def get_week_stats(y):
    y = np.array(y)

    x = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    fig, ax = plt.subplots()
    ax.bar(x, y, width=0.7, label='Количество встреч')
    ax.legend(prop={'size': 20})

    ax.set_facecolor('seashell')
    fig.set_figwidth(12)  # ширина Figure
    fig.set_figheight(6)  # высота Figure
    fig.set_facecolor('floralwhite')

    return image_from_plt(fig)


def get_meets_for_every_doc(x, y):
    y = np.array(y)

    fig, ax = plt.subplots()
    ax.bar(x, y, width=0.7, label='Количество встреч')
    ax.legend(prop={'size': 20})

    ax.set_facecolor('seashell')
    fig.set_figwidth(12)  # ширина Figure
    fig.set_figheight(6)  # высота Figure
    fig.set_facecolor('floralwhite')

    return image_from_plt(fig)
