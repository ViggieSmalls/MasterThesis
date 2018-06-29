import mrcfile
from scipy import misc
from skimage import exposure
import numpy as np
import math

##### Create screenshots of area

def save_image(image_ary, fname, equalize_hist=True):
    if equalize_hist == True:
        image_ary = exposure.equalize_hist(image_ary)
    misc.imsave(fname, image_ary)

def main(input_mrc, output, x, y, boxsize, scale_bar, equalize_hist=False):
    img = mrcfile.open(input_mrc, permissive=True).data
    area = img[round(y - boxsize / 2):round(y + boxsize / 2),
           round(x - boxsize / 2):round(x + boxsize / 2)]
    ary = np.copy(area)
    if equalize_hist == True:
        ary = exposure.equalize_hist(ary)

    if scale_bar is not None:
        x = scale_bar
        y = math.ceil(boxsize/100)
        if y < 10:
            y = 10
        d = math.ceil(boxsize/50)
        ary[-d-y:-d, -d-x:-d] = 0

    misc.imsave(output, ary)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create a screenshot of an area in an mrc file.')
    parser.add_argument('input_file', type=str,
                        help='Input mrc file')
    parser.add_argument('output_file', type=str,
                        help='Output area file')
    parser.add_argument('-x', type=int, default=3838/2,
                        help='x coordinate')
    parser.add_argument('-y', type=int, default=3710/2,
                        help='y coordinate')
    parser.add_argument('--boxsize', type=int, default=200,
                        help='y coordinate')
    parser.add_argument('--equalize_hist',  action='store_true', default=False,
                        help='equalize histogram for higher contrast')
    parser.add_argument('--scalebar', type=int, help='Scale bar in pixel at the bottom right corner')

    args = parser.parse_args()

    main(args.input_file, args.output_file, args.x, args.y, args.boxsize, args.scalebar, args.equalize_hist)

