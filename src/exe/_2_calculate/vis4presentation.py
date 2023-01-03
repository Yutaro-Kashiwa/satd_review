import pandas
import scipy.stats
import math
import seaborn as sns

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
if __name__ == '__main__':

    tp = "acceptances"
    sns.barplot(x=["Without", "With"], y=[74.9, 68.0])
    plt.ylim([0,100])
    plt.savefig(f'openstack_{tp}.png')
    plt.close()

    sns.barplot(x=["Without", "With"], y=[86.2, 79.9])
    plt.ylim([0,100])
    plt.savefig(f'qt_{tp}.png')
    plt.close()