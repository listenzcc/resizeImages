# %%
import os
import cv2
import logging
import argparse

import numpy as np
import pandas as pd

from pathlib import Path

# %%
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# %%
methods = dict(linear=cv2.INTER_LINEAR,
               area=cv2.INTER_AREA,
               cubic=cv2.INTER_CUBIC,
               lanc=cv2.INTER_LANCZOS4)

extents = ['png', 'jpg', 'jpeg', 'tif', 'tiff']
folder = Path(os.environ['HOMEPATH'], 'Pictures', 'snipaste')

# %%


def _ext(e):
    return e.name.split('.')[-1]


def _putText(text, mat):
    font = cv2.FONT_HERSHEY_SIMPLEX
    org = [int(e) for e in (mat.shape[1]/2, mat.shape[0]/2)]
    fontScale = 0.5
    color = 255 - np.mean(np.mean(mat, axis=0), axis=0)
    thickness = 1

    img = cv2.putText(mat, text, org, font, fontScale,
                      color, thickness, cv2.LINE_AA)

    img[:2, :, :] = 100
    img[-2:, :, :] = 100

    return img


class Data(object):
    def __init__(self, folder=folder):
        self.folder = folder
        pass

    def read_folder(self, filter=''):
        '''Read image file from the folders'''
        if filter is None:
            filter = ''

        found = [(e, _ext(e), e.name) for e in self.folder.iterdir()
                 if all([
                     e.is_file(),
                     _ext(e) in extents,
                     not e.name.startswith('_'),
                     filter in e.name
                 ])]

        df = pd.DataFrame(found, columns=['path', 'ext', 'name'])

        n = len(df)
        logger.debug('Found {} images in folder {}'.format(
            n, self.folder))
        if n == 0:
            logger.warning('Found no image.')

        self.df = df
        return self.df

    def resize(self, id, width, compare, method):
        '''
        Resize the selected image

        Args:
            - id: The id of the image;
            - width: The width of the resized image;
            - compare: Whether to compare several interpolation methods;
            - method: Which method is used to interpolate (invalid if compare is True).
        '''

        if not id in self.df.index:
            logger.error('Can not work with {}'.format(id))
            return

        path = data.df.loc[id, 'path']
        new_path = Path(path.parent, '_resize-{}-{}'.format(width, path.name))

        mat = cv2.imread(path.as_posix())
        logger.debug('Working with {}, {}, {}'.format(id, mat.shape, path))

        height = int(width / mat.shape[1] * mat.shape[0])
        dsize = (width, height)

        if compare:
            mats = [_putText(k, cv2.resize(mat, dsize=dsize, interpolation=m))
                    for k, m in methods.items()]

            new_mat = np.concatenate(mats, axis=0)
        else:
            new_mat = cv2.resize(
                mat,
                dsize=dsize,
                interpolation=methods[method]
            )

        cv2.imwrite(new_path.as_posix(), new_mat)
        logger.debug('Resize: {}, {}'.format(new_mat.shape, new_path))

        logger.info('New file is saved to {}'.format(new_path))

        return new_path


# %%


# %%
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filter", help='Filter file name')
    parser.add_argument("-d", "--dir", help='Directory to find images')
    parser.add_argument(
        "-c", "--compare", help='Whether to compare interpolation methods', action='store_true')
    parser.add_argument(
        '-m', '--method', help='Use what method to interpolate, options are {}, only available when compare is unset'.format([e for e in methods]))
    parser.add_argument("-w", "--width", help='Width of the resized image')
    parser.add_argument("-v", "--verbose", help='Verbose', action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose is on')

    #
    if args.width is None:
        width = 300
    else:
        width = int(args.width)

    #
    filter = args.filter

    #
    folder = folder
    if not args.dir is None:
        folder = Path(args.dir)

    #
    compare = args.compare

    #
    method = args.method
    if method is None:
        method = 'area'
    if not method in methods:
        method = 'area'
        logger.warning('Method is not available, using "area" as default')

    logger.debug('Args are {}'.format(args))

    data = Data(folder)
    data.read_folder(filter)

    while True:
        if len(data.df) == 0:
            break

        print('-' * 60)
        for id in data.df.index:
            print(id, data.df.loc[id, 'name'])

        prompt = ' '.join(['Enter',
                           '"Id" to resize the image,',
                           '"a" to resize all the images,',
                           '"c" to clear the output,',
                           '"q" to escape,',
                           '\n>> '])
        inp = input(prompt)

        if inp == '':
            continue

        if inp == 'c':
            os.system('clear')
            continue

        if inp == 'q':
            break

        if inp == 'a':
            for id in data.df.index:
                data.resize(id, width, compare, method)
            continue

        id = int(inp)
        if id in data.df.index:
            data.resize(id, width, compare, method)
        else:
            logger.info('Can not find id {}'.format(id))
            continue

        pass

    print('Job done.')


# %%
